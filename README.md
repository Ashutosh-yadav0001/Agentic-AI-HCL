# Agentic AI BGV System

A local demo for background verification after an HR offer release. It covers candidate acceptance, BGV form submission, vendor verification, AI-assisted issue handling, HR review, re-verification, and final decisioning.

## Hackathon Pitch

Agentic AI BGV turns a messy HR background verification process into a guided workflow where AI summarizes vendor issues and drafts candidate communication, while HR stays in control of every decision.

For the quickest presentation path, read [HACKATHON_DEMO.md](HACKATHON_DEMO.md).

## Tech Stack

- FastAPI backend
- Streamlit HR dashboard
- SQLite local storage
- SQLAlchemy and Pydantic
- Demo-safe email and Microsoft Forms placeholders
- Deterministic AI fallback for summaries and candidate email drafts

## Setup

```powershell
cd "C:\Users\ashutosh\Documents\BGV Proccess Automation"
Copy-Item .env.example .env
.\scripts\install_deps.ps1
.\.venv\Scripts\python.exe scripts\seed_demo.py
```

If PowerShell blocks script execution:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Run

Backend:

```powershell
.\scripts\run_api.ps1
```

Dashboard, in a second terminal:

```powershell
.\scripts\run_dashboard.ps1
```

Open:

- API health: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Dashboard: Streamlit prints the local URL, usually http://localhost:8501

## Configure Real Microsoft Email

The app can send real email through Microsoft Graph. For hackathon demos, keep `GMAIL_DEMO_MODE=true` until your app registration is ready.

1. Go to Azure Portal.
2. Open `Microsoft Entra ID` > `App registrations` > `New registration`.
3. Name it `Agentic BGV Mailer`.
4. Choose `Accounts in this organizational directory only`.
5. Register the app.
6. Copy:
   - `Application (client) ID`
   - `Directory (tenant) ID`
7. Open `Certificates & secrets` > `New client secret`.
8. Copy the secret **Value** immediately.
9. Open `API permissions` > `Add a permission` > `Microsoft Graph` > `Application permissions`.
10. Add `Mail.Send`.
11. Click `Grant admin consent`.
12. Update `.env`:

```env
GMAIL_DEMO_MODE=false
MS_TENANT_ID=your-tenant-id
MS_CLIENT_ID=your-client-id
MS_CLIENT_SECRET=your-client-secret
MS_SENDER_EMAIL=your-real-mailbox@yourdomain.com
```

`MS_SENDER_EMAIL` must be a real mailbox in your Microsoft tenant. For example, use your developer account user email if it has an Exchange Online mailbox.

Important: `MS_CLIENT_SECRET` must be the client secret **Value**, not the secret ID. If you copied the secret ID, Microsoft Graph returns `AADSTS7000215: Invalid client secret provided`.

Validate your mail settings:

```powershell
.\.venv\Scripts\python.exe scripts\check_ms_mail_config.py
```

Send a real test email:

```powershell
.\.venv\Scripts\python.exe scripts\test_ms_mail.py --to your-email@yourdomain.com
```

Then restart the API:

```powershell
.\scripts\run_api.ps1
```

When HR actions trigger email, the backend calls Microsoft Graph:

```text
POST https://graph.microsoft.com/v1.0/users/{MS_SENDER_EMAIL}/sendMail
```

## Demo Flow

Fastest judge demo:

1. Seed demo data with `.\.venv\Scripts\python.exe scripts\seed_demo.py`.
2. Open the dashboard.
3. Select the seeded discrepancy case for Rohan Mehta.
4. Show the AI risk summary and draft candidate email.
5. Approve the draft.
6. Add the candidate correction.
7. Submit final vendor result as `Clear`.
8. Show the timeline and completed status.

Manual end-to-end demo:

1. Add a candidate.
2. Click `Send Offer Email`.
3. Record the offer as accepted.
4. Add a BGV document and submit it to the vendor.
5. Submit a vendor result such as `Discrepancy`.
6. Review the AI-generated risk summary and draft email.
7. Approve the HR draft.
8. Add the candidate correction.
9. Submit a final vendor result such as `Clear`.
10. Show the final case status as completed.

## API Endpoints

- `POST /candidates`
- `GET /candidates`
- `POST /agentic-bgv/cases`
- `POST /agentic-bgv/cases/{case_id}/offer-response`
- `POST /agentic-bgv/cases/{case_id}/documents`
- `POST /agentic-bgv/cases/{case_id}/vendor-status`
- `POST /agentic-bgv/cases/{case_id}/hr-review`
- `POST /agentic-bgv/cases/{case_id}/candidate-response`
- `GET /agentic-bgv/cases`
- `GET /agentic-bgv/cases/{case_id}`

## Visuals

Generate the workflow visual:

```powershell
.\.venv\Scripts\python.exe scripts\create_workflow_visual.py
```
