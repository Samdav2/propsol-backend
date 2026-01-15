import os
from typing import Any, Dict, List, Optional
from jinja2 import Environment, FileSystemLoader
from mailjet_rest import Client

from app.config import settings

# Setup Jinja2 environment
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
env = Environment(loader=FileSystemLoader(template_dir))

def render_template(template_name: str, context: Dict[str, Any]) -> str:
    template = env.get_template(template_name)
    return template.render(**context)

def send_email(
    email_to: str,
    subject: str,
    template_name: str,
    context: Dict[str, Any] = {},
) -> None:
    if not settings.MAILJET_API_KEY or not settings.MAILJET_SECRET_KEY:
        print(f"Mailjet not configured, skipping email to {email_to}. Subject: {subject}")
        return

    html_content = render_template(template_name, context)

    mailjet = Client(auth=(settings.MAILJET_API_KEY, settings.MAILJET_SECRET_KEY), version='v3.1')
    data = {
        'Messages': [
            {
                "From": {
                    "Email": settings.MAILJET_SENDER_EMAIL,
                    "Name": "PropSol Support"
                },
                "To": [
                    {
                        "Email": email_to,
                        "Name": "User"
                    }
                ],
                "Subject": subject,
                "HTMLPart": html_content,
            }
        ]
    }
    result = mailjet.send.create(data=data)
    if result.status_code != 200:
        print(f"Failed to send email: {result.status_code} {result.json()}")
    else:
        print(f"Email sent to {email_to}")
