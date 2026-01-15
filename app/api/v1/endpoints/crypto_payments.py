from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Header, BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schema.crypto_payment import (
    CryptoPaymentRead,
    NOWPaymentsInvoiceRequest,
    NOWPaymentsPaymentRequest,
    NOWPaymentsIPNPayload,
)
from app.service.nowpayments_service import NOWPaymentsService

router = APIRouter()


@router.get("/status")
async def get_api_status(
    session: AsyncSession = Depends(get_session),
):
    """Check NOWPayments API status"""
    service = NOWPaymentsService(session)
    return await service.get_api_status()


@router.get("/currencies")
async def get_available_currencies(
    session: AsyncSession = Depends(get_session),
):
    """Get list of available cryptocurrencies"""
    service = NOWPaymentsService(session)
    currencies = await service.get_available_currencies()
    return {"currencies": currencies}


@router.get("/min-amount")
async def get_minimum_amount(
    currency_from: str,
    currency_to: str | None = None,
    is_fixed_rate: bool = False,
    is_fee_paid_by_user: bool = False,
    session: AsyncSession = Depends(get_session),
):
    """Get minimum payment amount for currency pair"""
    service = NOWPaymentsService(session)
    return await service.get_minimum_amount(
        currency_from=currency_from,
        currency_to=currency_to,
        is_fixed_rate=is_fixed_rate,
        is_fee_paid_by_user=is_fee_paid_by_user
    )


@router.get("/estimate")
async def get_estimated_price(
    amount: float,
    currency_from: str,
    currency_to: str,
    session: AsyncSession = Depends(get_session),
):
    """Get estimated price for conversion"""
    service = NOWPaymentsService(session)
    return await service.get_estimated_price(
        amount=amount,
        currency_from=currency_from,
        currency_to=currency_to
    )


@router.post("/invoice", response_model=CryptoPaymentRead)
async def create_invoice(
    invoice_data: NOWPaymentsInvoiceRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a payment invoice (redirect flow)"""
    service = NOWPaymentsService(session)
    return await service.create_invoice(invoice_data, current_user.id)


@router.post("/payment", response_model=CryptoPaymentRead)
async def create_payment(
    payment_data: NOWPaymentsPaymentRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a direct payment (white-label flow)"""
    service = NOWPaymentsService(session)
    return await service.create_payment(payment_data, current_user.id)


@router.get("/payment/{payment_id}/status")
async def get_payment_status(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get payment status from NOWPayments API"""
    service = NOWPaymentsService(session)

    # Verify the payment belongs to the user
    crypto_payment = await service.repo.get_by_payment_id(payment_id)
    if not crypto_payment or crypto_payment.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Payment not found")

    return await service.get_payment_status(payment_id)


@router.get("", response_model=List[CryptoPaymentRead])
async def list_user_payments(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get all crypto payments for the current user"""
    service = NOWPaymentsService(session)
    return await service.get_user_payments(current_user.id)


@router.get("/{payment_db_id}", response_model=CryptoPaymentRead)
async def get_payment_by_id(
    payment_db_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a specific crypto payment by database ID"""
    service = NOWPaymentsService(session)
    payment = await service.get_payment_by_id(payment_db_id)

    if not payment or payment.get('user_id') != current_user.id:
        raise HTTPException(status_code=404, detail="Payment not found")

    return payment


@router.post("/ipn-callback")
async def ipn_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    x_nowpayments_sig: str = Header(None),
    session: AsyncSession = Depends(get_session),
):
    """
    IPN webhook endpoint for NOWPayments callbacks.
    This endpoint does not require authentication.
    Handles payment status updates and triggers background tasks for notifications.
    """
    if not x_nowpayments_sig:
        raise HTTPException(status_code=400, detail="Missing signature header")

    # Get the raw request body
    body = await request.json()

    try:
        # Parse the payload
        ipn_payload = NOWPaymentsIPNPayload(**body)

        # Process the callback
        service = NOWPaymentsService(session)
        updated_payment = await service.process_ipn_callback(
            payload=ipn_payload,
            signature=x_nowpayments_sig
        )

        if not updated_payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        # Add background task for notifications and additional processing
        background_tasks.add_task(
            process_payment_update,
            payment_id=updated_payment.id,
            payment_status=updated_payment.payment_status,
            user_id=updated_payment.user_id
        )

        return {"status": "ok", "payment_id": str(updated_payment.id)}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def process_payment_update(payment_id: UUID, payment_status: str, user_id: UUID):
    """
    Background task to process payment updates.
    Add your business logic here for:
    - Sending email notifications
    - Updating order status
    - Triggering fulfillment
    - Updating inventory
    - Notifying admins
    """
    from app.service.mail import send_email
    from app.config import settings
    from app.db.session import async_session_maker
    from app.models.user import User

    # Get user details
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if not user:
            return

        user_email = user.email
        user_name = user.name

    # Send email notification based on payment status
    if payment_status == "finished":
        # Payment successful - send confirmation
        await send_email(
            email_to=user_email,
            subject="Payment Successful - Crypto Payment Confirmed",
            template_name="crypto_payment_success.html",
            context={
                "user_name": user_name,
                "payment_id": str(payment_id),
                "status": payment_status
            }
        )

        # Notify admin
        if settings.ADMIN_EMAIL:
            await send_email(
                email_to=settings.ADMIN_EMAIL,
                subject="New Crypto Payment Received",
                template_name="admin_crypto_payment_received.html",
                context={
                    "user_email": user_email,
                    "payment_id": str(payment_id),
                    "status": payment_status
                }
            )

    elif payment_status == "partially_paid":
        # Partially paid - notify user
        await send_email(
            email_to=user_email,
            subject="Payment Partially Received",
            template_name="crypto_payment_partial.html",
            context={
                "user_name": user_name,
                "payment_id": str(payment_id),
                "status": payment_status
            }
        )

    elif payment_status == "failed":
        # Payment failed - send notification
        await send_email(
            email_to=user_email,
            subject="Payment Failed",
            template_name="crypto_payment_failed.html",
            context={
                "user_name": user_name,
                "payment_id": str(payment_id),
                "status": payment_status
            }
        )

    # Add your additional business logic here:
    # - Update related orders
    # - Trigger product delivery
    # - Update user subscriptions
    # - Log analytics events
    # etc.

    # Update propfirm registration payment status if order_id is present
    if payment_status in ["finished", "failed"]:
        async with async_session_maker() as session:
            from app.models.crypto_payment import CryptoPayment
            from app.service.propfirm_registration_service import PropFirmRegistrationService
            from app.repository.propfirm_registration_repo import PropFirmRegistrationRepository
            from app.models.propfirm_registration import PropFirmRegistration, PaymentStatus
            from app.schema.propfirm_registration import PropFirmRegistrationUpdate

            # Get the crypto payment to find the order_id
            crypto_payment = await session.get(CryptoPayment, payment_id)
            if crypto_payment and crypto_payment.order_id:
                # Find propfirm registration by order_id
                propfirm_repo = PropFirmRegistrationRepository(PropFirmRegistration, session)
                registration = await propfirm_repo.get_by_order_id(crypto_payment.order_id)

                if registration:
                    # Update payment status based on payment result
                    new_payment_status = PaymentStatus.completed if payment_status == "finished" else PaymentStatus.failed

                    update_data = PropFirmRegistrationUpdate(payment_status=new_payment_status)
                    await propfirm_repo.update(db_obj=registration, obj_in=update_data.dict(exclude_unset=True))
                    await session.commit()
