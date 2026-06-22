import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bgv_app.config import get_settings


def masked(value: str) -> str:
    if not value:
        return "MISSING"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def main() -> int:
    settings = get_settings()
    checks = {
        "GMAIL_DEMO_MODE": str(settings.gmail_demo_mode),
        "MS_TENANT_ID": masked(settings.ms_tenant_id),
        "MS_CLIENT_ID": masked(settings.ms_client_id),
        "MS_CLIENT_SECRET": masked(settings.ms_client_secret),
        "MS_SENDER_EMAIL": settings.ms_sender_email if settings.ms_sender_email else "MISSING",
    }
    for key, value in checks.items():
        print(f"{key}: {value}")

    missing = [
        key
        for key, value in {
            "MS_TENANT_ID": settings.ms_tenant_id,
            "MS_CLIENT_ID": settings.ms_client_id,
            "MS_CLIENT_SECRET": settings.ms_client_secret,
            "MS_SENDER_EMAIL": settings.ms_sender_email,
        }.items()
        if not value
    ]
    if settings.gmail_demo_mode:
        print("Mail mode: DEMO. Set GMAIL_DEMO_MODE=false to send real Microsoft Graph email.")
        return 1
    if missing:
        print(f"Missing required Microsoft mail settings: {', '.join(missing)}")
        return 1

    print("Microsoft Graph mail config looks ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
