import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.service.mail import render_template

def test_email_templates():
    templates = {
        "admin_new_user.html": {
            "name": "Test User",
            "email": "test@example.com",
            "created_at": "2023-01-01 12:00:00"
        },
        "referral_signup.html": {
            "referrer_name": "Referrer",
            "new_user_name": "New User"
        },
        "reset_password.html": {
            "name": "Test User",
            "reset_link": "http://example.com/reset"
        },
        "password_changed.html": {
            "name": "Test User"
        },
        "verify_email.html": {
            "name": "Test User",
            "verification_link": "http://example.com/verify"
        },
        "admin_payment_received.html": {
            "user_email": "user@example.com",
            "amount": 100.00,
            "reference": "REF123",
            "created_at": "2023-01-01"
        },
        "admin_account_passed.html": {
            "user_email": "user@example.com",
            "propfirm_name": "PropFirm X",
            "login_id": "12345"
        },
        "admin_account_failed.html": {
            "user_email": "user@example.com",
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
            "name": "Test User" # Guessing context
        }
    }

    print("Testing email templates rendering...\n")
    failed = []
    for template_name, context in templates.items():
        try:
            print(f"Rendering {template_name}...", end=" ")
            content = render_template(template_name, context)
            if content:
                print("OK")
            else:
                print("FAILED (Empty content)")
                failed.append(template_name)
        except Exception as e:
            print(f"FAILED ({e})")
            failed.append(template_name)

    print("\n" + "="*30)
    if failed:
        print(f"Failed templates: {failed}")
    else:
        print("All templates rendered successfully!")

if __name__ == "__main__":
    test_email_templates()
