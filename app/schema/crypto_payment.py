from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Any


# Base schemas
class CryptoPaymentBase(BaseModel):
    order_id: str | None = None
    order_description: str | None = None
    price_amount: float = Field(gt=0, description="Amount in fiat currency")
    price_currency: str = Field(default="usd", description="Fiat currency code (usd, eur, etc)")
    pay_currency: str = Field(description="Crypto currency code (btc, eth, trx, etc)")
    ipn_callback_url: str | None = None
    is_fixed_rate: bool = False
    is_fee_paid_by_user: bool = False


class CryptoPaymentCreate(CryptoPaymentBase):
    """Schema for creating a new crypto payment"""
    pass


class CryptoPaymentRead(BaseModel):
    """Schema for reading crypto payment data"""
    id: UUID
    user_id: UUID
    payment_id: str | None
    invoice_id: str | None
    order_id: str | None
    order_description: str | None
    price_amount: float
    price_currency: str
    pay_amount: float | None
    pay_currency: str
    pay_address: str | None
    payin_extra_id: str | None
    payment_status: str
    actually_paid: float | None
    purchase_id: str | None
    outcome_amount: float | None
    outcome_currency: str | None
    ipn_callback_url: str | None
    invoice_url: str | None
    is_fixed_rate: bool
    is_fee_paid_by_user: bool
    created_at: datetime
    updated_at: datetime
    propfirm_registration: dict[str, Any] | None = None

    class Config:
        from_attributes = True


class CryptoPaymentUpdate(BaseModel):
    """Schema for updating crypto payment status"""
    payment_id: str | None = None
    payment_status: str | None = None
    pay_address: str | None = None
    pay_amount: float | None = None
    actually_paid: float | None = None
    payin_extra_id: str | None = None
    outcome_amount: float | None = None
    outcome_currency: str | None = None


# NOWPayments API specific schemas
class NOWPaymentsInvoiceRequest(BaseModel):
    """Schema for creating a NOWPayments invoice"""
    price_amount: float
    price_currency: str = "usd"
    pay_currency: str | None = None
    order_id: str | None = None
    order_description: str | None = None
    ipn_callback_url: str | None = None
    success_url: str | None = None
    cancel_url: str | None = None
    partially_paid_url: str | None = None
    is_fixed_rate: bool = False
    is_fee_paid_by_user: bool = False


class NOWPaymentsPaymentRequest(BaseModel):
    """Schema for creating a direct NOWPayments payment"""
    price_amount: float
    price_currency: str = "usd"
    pay_amount: float | None = None
    pay_currency: str
    ipn_callback_url: str | None = None
    order_id: str | None = None
    order_description: str | None = None
    payout_address: str | None = None
    payout_currency: str | None = None
    payout_extra_id: str | None = None
    is_fixed_rate: bool = False
    is_fee_paid_by_user: bool = False


class NOWPaymentsIPNPayload(BaseModel):
    """Schema for NOWPayments IPN callback payload"""
    payment_id: int | str
    parent_payment_id: int | str | None = None
    invoice_id: int | str | None = None
    payment_status: str
    pay_address: str
    payin_extra_id: str | None = None
    price_amount: float
    price_currency: str
    pay_amount: float
    actually_paid: float
    actually_paid_at_fiat: float | None = None
    pay_currency: str
    order_id: str | None = None
    order_description: str | None = None
    purchase_id: str | None = None
    outcome_amount: float | None = None
    outcome_currency: str | None = None


class CurrencyInfo(BaseModel):
    """Schema for available currency information"""
    currency: str
    min_amount: float | None = None


class EstimateResponse(BaseModel):
    """Schema for estimated price response"""
    currency_from: str
    amount_from: float
    currency_to: str
    estimated_amount: float
