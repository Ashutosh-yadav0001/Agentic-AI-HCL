from dataclasses import dataclass

import requests
from msal import ConfidentialClientApplication

from bgv_app.config import get_settings


@dataclass
class EmailPayload:
    to: str
    subject: str
    body: str
    demo_mode: bool


def send_email(to: str, subject: str, body: str) -> EmailPayload:
    settings = get_settings()
    payload = EmailPayload(to=to, subject=subject, body=body, demo_mode=settings.gmail_demo_mode)
    if settings.gmail_demo_mode:
        return payload

    missing = [
        name
        for name, value in {
            "MS_TENANT_ID": settings.ms_tenant_id,
            "MS_CLIENT_ID": settings.ms_client_id,
            "MS_CLIENT_SECRET": settings.ms_client_secret,
            "MS_SENDER_EMAIL": settings.ms_sender_email,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Microsoft Graph mail is enabled, but these settings are missing: {', '.join(missing)}")

    authority = f"https://login.microsoftonline.com/{settings.ms_tenant_id}"
    app = ConfidentialClientApplication(
        client_id=settings.ms_client_id,
        client_credential=settings.ms_client_secret,
        authority=authority,
    )
    token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in token:
        raise RuntimeError(f"Could not acquire Microsoft Graph token: {token.get('error_description', token)}")

    message = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": to}}],
            "from": {"emailAddress": {"address": settings.ms_sender_email}},
        },
        "saveToSentItems": True,
    }
    response = requests.post(
        f"https://graph.microsoft.com/v1.0/users/{settings.ms_sender_email}/sendMail",
        headers={"Authorization": f"Bearer {token['access_token']}", "Content-Type": "application/json"},
        json=message,
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(f"Microsoft Graph sendMail failed: {response.status_code} {response.text}")
    return payload
