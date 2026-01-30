import sys
import os
import asyncio

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.service.mail import send_email

def send_test_emails(target_email):
    templates = {
        "admin_new_user.html": {
            "name": "Test User",
            "email": "test@propsol.com",
            "created_at": "2023-01-01 12:00:00"
        },
        "referral_signup.html": {
            "referrer_name": "Referrer",
            "new_user_name": "New User"
        },
        "reset_password.html": {
            "name": "Test User",
            "reset_link": "https://propfirmsol.com/reset-password?token=dummy_token"
        },
        "password_changed.html": {
            "name": "Test User"
        },
        "verify_email.html": {
            "name": "Test User",
            "verification_link": "https://propfirmsol.com/verify-email?token=dummy_token"
        },
        "admin_payment_received.html": {
            "user_email": "user@propsol.com",
            "amount": 100.00,
            "reference": "REF123",
            "created_at": "2023-01-01"
        },
        "admin_account_passed.html": {
            "user_email": "user@propsol.com",
            "propfirm_name": "PropFirm X",
            "login_id": "12345"
        },
        "admin_account_failed.html": {
            "user_email": "user@propsol.com",
            "propfirm_name": "PropFirm X",
            "login_id": "12345"
        },
        "user_account_passed.html": {
            "name": "Test User",
            "propfirm_name": "PropFirm X",
            "login_id": "12345"
        },
        "user_account_failed.html": {
            "name": "Test User",
            "propfirm_name": "PropFirm X",
            "login_id": "12345"
        },
        "support_receipt.html": {
            "name": "Test User",
            "message": "I need help!"
        },
        "user_package_purchased.html": {
            "name": "Test User",
            "package_name": "Gold Package",
            "price": 5000,
            "date": "2023-01-01"
        },
        "welcome.html": {
            "name": "Test User"
        }
    }

    print(f"Sending test emails to {target_email}...\n")

    for template_name, context in templates.items():
        print(f"Sending {template_name}...", end=" ")
        try:
            send_email(
                email_to=target_email,
                subject=f"Test: {template_name}",
                template_name=template_name,
                context=context
            )
            # The send_email function prints its own success/failure message,
            # but we catch exceptions just in case.
        except Exception as e:
            print(f"FAILED ({e})")

    print("\nDone.")

if __name__ == "__main__":
    target = "adoxop1@gmail.com"
    if len(sys.argv) > 1:
        target = sys.argv[1]
    send_test_emails(target)
