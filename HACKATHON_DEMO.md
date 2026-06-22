# Hackathon Demo Guide

## One-Line Pitch

Agentic AI BGV automates the background verification journey after offer release while keeping HR in control of every candidate-facing and final decision.

## Problem

Background verification is slow because HR, candidates, and vendors exchange repeated emails, missing document requests, remarks, and final approvals across disconnected tools.

## Solution

This app gives HR one workflow console:

- release offer and collect accept/decline response
- request BGV documents
- send details to vendor
- receive vendor outcome
- use AI to summarize risk and draft clarification email
- require HR review before sending
- track candidate correction and re-verification
- close with final decision

## What To Demo

1. Open the dashboard.
2. Show seeded cases: one completed, one medium-risk discrepancy, one high-risk escalation.
3. Open the discrepancy case.
4. Show the AI summary and draft candidate email.
5. Click `Approve Draft`.
6. Add a candidate correction.
7. Submit final vendor result as `Clear`.
8. Show the case status becoming `Completed`.

## Judge-Friendly Talking Points

- The system is not replacing HR judgment. It makes HR faster and more consistent.
- AI is used only for summarization, risk explanation, and email drafting.
- Every major action is recorded in a timeline.
- The same architecture can plug into Microsoft Forms, Microsoft Graph email, vendor APIs, and Azure storage.

## Best Hackathon Scope

For a hackathon, present this as a production-shaped MVP:

- working local backend and dashboard
- real state transitions
- seeded demo data
- clear API docs
- safe fallback AI behavior
- obvious integration points for Microsoft Forms, email, and vendor systems

Avoid overpromising live production compliance. Say the next production steps are authentication, secure document storage, vendor webhooks, audit hardening, and cloud deployment.

## Setup

```powershell
cd "C:\Users\ashutosh\Documents\BGV Proccess Automation"
.\scripts\install_deps.ps1
.\.venv\Scripts\python.exe scripts\seed_demo.py
```

## Run

Terminal 1:

```powershell
.\scripts\run_api.ps1
```

Terminal 2:

```powershell
.\scripts\run_dashboard.ps1
```

Open the Streamlit URL, usually:

```text
http://localhost:8501
```
