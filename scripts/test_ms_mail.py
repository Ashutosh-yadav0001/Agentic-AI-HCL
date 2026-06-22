import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bgv_app.integrations.gmail import send_email


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a Microsoft Graph test email for the BGV demo.")
    parser.add_argument("--to", required=True, help="Recipient email address")
    args = parser.parse_args()

    payload = send_email(
        to=args.to,
        subject="Agentic BGV demo mail test",
        body=(
            "Hello,\n\n"
            "This is a test email from the Agentic AI BGV hackathon demo. "
            "Microsoft Graph mail is configured correctly.\n\n"
            "Regards,\nAgentic BGV"
        ),
    )
    mode = "demo log only" if payload.demo_mode else "sent through Microsoft Graph"
    print(f"Email {mode}: {payload.subject} -> {payload.to}")


if __name__ == "__main__":
    main()
