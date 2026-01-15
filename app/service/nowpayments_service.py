import json
import hmac
import hashlib
from typing import List, Dict, Any
from uuid import UUID
import httpx
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.models.crypto_payment import CryptoPayment
from app.schema.crypto_payment import (
    CryptoPaymentCreate,
    CryptoPaymentUpdate,
    NOWPaymentsInvoiceRequest,
    NOWPaymentsPaymentRequest,
    NOWPaymentsIPNPayload,
)
from app.repository.crypto_payment_repo import CryptoPaymentRepository


class NOWPaymentsService:
    """Service for NOWPayments API integration"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CryptoPaymentRepository(CryptoPayment, session)
        self.api_url = settings.NOWPAYMENTS_API_URL
        self.api_key = settings.NOWPAYMENTS_API_KEY
        self.ipn_secret = settings.NOWPAYMENTS_IPN_SECRET

    def _get_headers(self) -> Dict[str, str]:
        """Get default headers for NOWPayments API requests"""
        return {
            "x-api-key": self.api_key or "",
            "Content-Type": "application/json"
        }

    async def get_api_status(self) -> Dict[str, Any]:
        """Check NOWPayments API status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_url}/status")
            response.raise_for_status()
            return response.json()

    async def get_available_currencies(self) -> List[str]:
        """Get list of available cryptocurrencies"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/currencies",
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            return data.get("currencies", [])

    async def get_minimum_amount(
        self,
        currency_from: str,
        currency_to: str | None = None,
        is_fixed_rate: bool = False,
        is_fee_paid_by_user: bool = False
    ) -> Dict[str, Any]:
        """Get minimum payment amount for currency pair"""
        params = {
            "currency_from": currency_from,
            "is_fixed_rate": str(is_fixed_rate).lower(),
            "is_fee_paid_by_user": str(is_fee_paid_by_user).lower()
        }
        if currency_to:
            params["currency_to"] = currency_to

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/min-amount",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def get_estimated_price(
        self,
        amount: float,
        currency_from: str,
        currency_to: str
    ) -> Dict[str, Any]:
        """Get estimated price for conversion"""
        params = {
            "amount": amount,
            "currency_from": currency_from,
            "currency_to": currency_to
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/estimate",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def create_invoice(
        self,
        invoice_data: NOWPaymentsInvoiceRequest,
        user_id: UUID
    ) -> CryptoPayment:
        """Create a payment invoice (redirect flow)"""
        payload = invoice_data.dict(exclude_none=True)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/invoice",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            invoice_response = response.json()

        # Store in database
        crypto_payment_data = {
            "user_id": user_id,
            "invoice_id": str(invoice_response.get("id")),
            "order_id": invoice_response.get("order_id"),
            "order_description": invoice_response.get("order_description"),
            "price_amount": float(invoice_response.get("price_amount")),
            "price_currency": invoice_response.get("price_currency"),
            "pay_currency": invoice_response.get("pay_currency") or invoice_data.pay_currency,
            "ipn_callback_url": invoice_response.get("ipn_callback_url"),
            "invoice_url": invoice_response.get("invoice_url"),
            "payment_status": "waiting",
            "is_fixed_rate": invoice_response.get("is_fixed_rate", False),
            "is_fee_paid_by_user": invoice_response.get("is_fee_paid_by_user", False)
        }

        return await self.repo.create(crypto_payment_data)

    async def create_payment(
        self,
        payment_data: NOWPaymentsPaymentRequest,
        user_id: UUID
    ) -> CryptoPayment:
        """Create a direct payment (white-label flow)"""
        payload = payment_data.dict(exclude_none=True)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/payment",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            payment_response = response.json()

        # Store in database
        crypto_payment_data = {
            "user_id": user_id,
            "payment_id": str(payment_response.get("payment_id")),
            "order_id": payment_response.get("order_id"),
            "order_description": payment_response.get("order_description"),
            "price_amount": float(payment_response.get("price_amount")),
            "price_currency": payment_response.get("price_currency"),
            "pay_amount": payment_response.get("pay_amount"),
            "pay_currency": payment_response.get("pay_currency"),
            "pay_address": payment_response.get("pay_address"),
            "payin_extra_id": payment_response.get("payin_extra_id"),
            "purchase_id": payment_response.get("purchase_id"),
            "payment_status": payment_response.get("payment_status", "waiting"),
            "ipn_callback_url": payment_response.get("ipn_callback_url"),
            "is_fixed_rate": payment_response.get("is_fixed_rate", False),
            "is_fee_paid_by_user": payment_response.get("is_fee_paid_by_user", False)
        }

        return await self.repo.create(crypto_payment_data)

    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get payment status from NOWPayments API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/payment/{payment_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_user_payments(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get all crypto payments for a user with propfirm registration data"""
        payments = await self.repo.get_by_user(user_id)
        result = []
        for payment in payments:
            payment_dict = payment.dict() if hasattr(payment, 'dict') else payment.__dict__
            # Fetch propfirm registration if order_id exists
            if payment.order_id:
                propfirm_registration = await self._get_propfirm_registration(payment.order_id)
                payment_dict['propfirm_registration'] = propfirm_registration
            else:
                payment_dict['propfirm_registration'] = None
            result.append(payment_dict)
        return result

    async def get_payment_by_id(self, payment_db_id: UUID) -> Dict[str, Any] | None:
        """Get payment by database ID with propfirm registration data"""
        payment = await self.repo.get(payment_db_id)
        if not payment:
            return None

        payment_dict = payment.dict() if hasattr(payment, 'dict') else payment.__dict__
        # Fetch propfirm registration if order_id exists
        if payment.order_id:
            propfirm_registration = await self._get_propfirm_registration(payment.order_id)
            payment_dict['propfirm_registration'] = propfirm_registration
        else:
            payment_dict['propfirm_registration'] = None

        return payment_dict

    async def _get_propfirm_registration(self, order_id: str) -> Dict[str, Any] | None:
        """Helper method to fetch propfirm registration by order_id"""
        from app.repository.propfirm_registration_repo import PropFirmRegistrationRepository
        from app.models.propfirm_registration import PropFirmRegistration

        propfirm_repo = PropFirmRegistrationRepository(PropFirmRegistration, self.session)
        registration = await propfirm_repo.get_by_order_id(order_id)

        if registration:
            return registration.dict() if hasattr(registration, 'dict') else registration.__dict__
        return None

    def verify_ipn_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """Verify IPN callback signature using HMAC-SHA512"""
        if not self.ipn_secret:
            raise ValueError("IPN secret key is not configured")

        # Sort the payload by keys
        def sort_dict(d):
            return {k: sort_dict(v) if isinstance(v, dict) else v for k, v in sorted(d.items())}

        sorted_payload = sort_dict(payload)

        # Convert to JSON string
        payload_str = json.dumps(sorted_payload, separators=(',', ':'))

        # Create HMAC signature
        hmac_obj = hmac.new(
            self.ipn_secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha512
        )
        calculated_signature = hmac_obj.hexdigest()

        return hmac.compare_digest(calculated_signature, signature)

    async def process_ipn_callback(
        self,
        payload: NOWPaymentsIPNPayload,
        signature: str
    ) -> CryptoPayment | None:
        """Process IPN callback and update payment status"""
        # Verify signature
        payload_dict = payload.dict(exclude_none=True)
        if not self.verify_ipn_signature(payload_dict, signature):
            raise ValueError("Invalid IPN signature")

        # Find the payment in database
        payment_id_str = str(payload.payment_id)
        crypto_payment = await self.repo.get_by_payment_id(payment_id_str)

        if not crypto_payment:
            # Try to find by invoice_id if payment_id not found
            if payload.invoice_id:
                crypto_payment = await self.repo.get_by_invoice_id(str(payload.invoice_id))

        if not crypto_payment:
            return None

        # Update payment with IPN data
        update_data = CryptoPaymentUpdate(
            payment_status=payload.payment_status,
            actually_paid=payload.actually_paid,
            pay_amount=payload.pay_amount,
            pay_address=payload.pay_address,
            payin_extra_id=payload.payin_extra_id,
            outcome_amount=payload.outcome_amount,
            outcome_currency=payload.outcome_currency
        )

        updated_payment = await self.repo.update(
            db_obj=crypto_payment,
            obj_in=update_data
        )

        return updated_payment
