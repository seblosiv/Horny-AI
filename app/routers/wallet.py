"""
Wallet and payment routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx
import uuid as uuid_lib
from typing import List

from app.database import get_db
from app.models import User, Wallet, Payment
from app.schemas import (
    WalletResponse, TopUpRequest, TopUpResponse, PaymentResponse
)
from app.auth import get_current_user_from_token
from app.config import settings

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("", response_model=WalletResponse)
async def get_wallet(
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get wallet balance"""
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()

    if not wallet:
        # Create wallet if doesn't exist
        wallet = Wallet(user_id=current_user.id, balance_cents=0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)

    return wallet


@router.post("/topup", response_model=TopUpResponse)
async def create_topup(
    topup_data: TopUpRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a top-up payment via NOWPayments"""
    if not settings.NOWPAYMENTS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment provider not configured"
        )

    amount_cents = int(topup_data.amount_usd * 100)

    # Create payment record
    payment = Payment(
        user_id=current_user.id,
        provider="NOWPAYMENTS",
        status="pending",
        amount_cents=amount_cents,
        currency=topup_data.currency.upper()
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Create NOWPayments invoice
    try:
        nowpayments_url = "https://api-sandbox.nowpayments.io" if settings.NOWPAYMENTS_SANDBOX else "https://api.nowpayments.io"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{nowpayments_url}/v1/invoice",
                headers={
                    "x-api-key": settings.NOWPAYMENTS_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "price_amount": topup_data.amount_usd,
                    "price_currency": topup_data.currency.lower(),
                    "order_id": str(payment.id),
                    "order_description": f"Top-up wallet - ${topup_data.amount_usd}",
                    "ipn_callback_url": f"{settings.HOST}/webhooks/nowpayments",  # Update with your domain
                    "success_url": f"{settings.HOST}/console/wallet",  # Update with your domain
                    "cancel_url": f"{settings.HOST}/console/wallet"
                },
                timeout=30.0
            )
            response.raise_for_status()
            invoice_data = response.json()

            # Update payment with invoice data
            payment.provider_invoice_id = invoice_data.get("id")
            payment.payment_url = invoice_data.get("invoice_url")
            payment.raw_data = invoice_data
            db.commit()

            return TopUpResponse(
                payment_id=payment.id,
                amount_cents=amount_cents,
                payment_url=payment.payment_url,
                status=payment.status
            )

    except httpx.HTTPError as e:
        payment.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}"
        )


@router.get("/payments", response_model=List[PaymentResponse])
async def list_payments(
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """List all payments for current user"""
    payments = db.query(Payment).filter(
        Payment.user_id == current_user.id
    ).order_by(Payment.created_at.desc()).limit(50).all()

    return payments
