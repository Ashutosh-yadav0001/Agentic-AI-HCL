import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("BGV_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def api_get(path: str):
    response = requests.get(f"{API_BASE_URL}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: dict):
    response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def status_label(status: str) -> str:
    return status.replace("_", " ").title()


st.set_page_config(page_title="Agentic BGV Console", layout="wide", page_icon="🛡️")
st.title("🛡️ Agentic AI BGV System")
st.caption("Enterprise HR workflow console: Multi-track verification, AI compliance reasoning, Integrity Scoring, and Automated Audit Dossiers.")

with st.sidebar:
    st.subheader("⚡ System Connection")
    st.write(f"API: `{API_BASE_URL}`")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    st.divider()
    st.subheader("📊 Pipeline Summary")
    try:
        all_cases = api_get("/agentic-bgv/cases")
        total_cases = len(all_cases)
        completed = sum(1 for c in all_cases if c["status"] == "completed")
        discrepancies = sum(1 for c in all_cases if (c["risk_level"] or "").lower() in ["medium", "high", "critical"])
        avg_score = (
            int(sum(c.get("integrity_score") or 100 for c in all_cases) / total_cases)
            if total_cases > 0
            else 100
        )
        st.metric("Total Cases", total_cases)
        st.metric("Completed Clean", completed)
        st.metric("Active Discrepancies", discrepancies)
        st.metric("Avg Integrity Score", f"{avg_score}/100")
    except Exception:
        st.info("Pipeline stats available once backend is running.")

try:
    health = api_get("/")
except requests.RequestException as exc:
    st.error(f"FastAPI backend is not reachable at {API_BASE_URL}. Start it with: uvicorn bgv_app.main:app --reload")
    st.exception(exc)
    st.stop()

left, right = st.columns([0.32, 0.68])

with left:
    st.subheader("👤 Create Candidate")
    with st.form("candidate_form", clear_on_submit=True):
        name = st.text_input("Full Name", value="Anita Sharma")
        email = st.text_input("Email Address", value="anita.sharma@example.com")
        phone = st.text_input("Phone Number", value="+91 98765 43210")
        submitted = st.form_submit_button("Add Candidate", use_container_width=True)
        if submitted:
            try:
                api_post("/candidates", {"name": name, "email": email, "phone": phone or None})
                st.success("Candidate added successfully!")
                st.rerun()
            except requests.HTTPError as exc:
                st.error(exc.response.text)

    candidates = api_get("/candidates")
    st.subheader("🚀 Initiate BGV Workflow")
    if not candidates:
        st.info("Add a candidate to begin.")
    else:
        labels = {f"{c['name']} <{c['email']}>": c["id"] for c in candidates}
        selected_candidate = st.selectbox("Select Candidate", list(labels.keys()))
        vendor = st.text_input("Verification Vendor", value="Demo Verify")
        if st.button("Send Offer Email & Init 5 Tracks", use_container_width=True):
            api_post("/agentic-bgv/cases", {"candidate_id": labels[selected_candidate], "vendor_name": vendor})
            st.success("Offer workflow started with 5 tracks initialized!")
            st.rerun()

with right:
    cases = api_get("/agentic-bgv/cases")
    st.subheader("📋 Verification Cases")
    if not cases:
        st.info("No BGV cases initiated yet.")
    else:
        case_options = {
            f"#{case['id']} - {case['candidate']['name']} [{status_label(case['status'])}] - Score: {case.get('integrity_score', 100)}": case
            for case in cases
        }
        selected_label = st.selectbox("Active Case", list(case_options.keys()))
        case = case_options[selected_label]

        # Top KPI Metrics bar
        score = case.get("integrity_score") or 100
        risk = case.get("risk_level") or "Pending"
        metrics = st.columns(5)
        metrics[0].metric("Status", status_label(case["status"]))
        metrics[1].metric("Integrity Score", f"{score}/100", delta=f"{score - 100}" if score < 100 else "Clear")
        metrics[2].metric("Risk Level", risk)
        metrics[3].metric("Documents", len(case.get("documents", [])))
        metrics[4].metric("Vendor Checks", len(case.get("vendor_checks", [])))

        tabs = st.tabs([
            "🛠️ Actions",
            "🧩 Verification Matrix",
            "🤖 AI Compliance & Review",
            "📜 Audit Dossier",
            "⏱️ Timeline",
        ])

        # TAB 1: WORKFLOW ACTIONS
        with tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### 1. Offer Response")
                offer_choice = st.radio("Candidate Decision", ["Accepted", "Declined"], horizontal=True)
                if st.button("Record Offer Response", use_container_width=True):
                    api_post(
                        f"/agentic-bgv/cases/{case['id']}/offer-response",
                        {"accepted": offer_choice == "Accepted"},
                    )
                    st.rerun()

                st.markdown("##### 2. Upload Candidate Document")
                doc_type = st.selectbox("Document Type", ["Identity Proof (Aadhaar/PAN)", "Employment Proof (Relieving/Experience)", "Education Degree", "Address Proof"])
                file_name = st.text_input("File Name", value="document.pdf")
                file_url = st.text_input("Document URL", value="https://secure-docs.example.com/doc.pdf")
                if st.button("Submit Document to Vendor", use_container_width=True):
                    api_post(
                        f"/agentic-bgv/cases/{case['id']}/documents",
                        {"document_type": doc_type, "file_name": file_name, "file_url": file_url},
                    )
                    st.rerun()

            with col2:
                st.markdown("##### 3. Vendor Outcome Submission")
                outcome = st.selectbox("Vendor Result", ["Clear", "Missing Document", "Discrepancy", "Red Flag"])
                remarks = st.text_area("Vendor Findings / Remarks", value="Address proof mismatch: utility bill does not match current address.")
                if st.button("Submit Vendor Result", use_container_width=True):
                    api_post(
                        f"/agentic-bgv/cases/{case['id']}/vendor-status",
                        {"vendor_outcome": outcome, "vendor_remarks": remarks},
                    )
                    st.rerun()

                st.markdown("##### 4. Candidate Clarification Upload")
                correction = st.text_area(
                    "Candidate Response & Corrected Evidence",
                    value="I have attached my registered rental agreement confirming my current residence.",
                )
                if st.button("Send Clarification for Re-verification", use_container_width=True):
                    api_post(
                        f"/agentic-bgv/cases/{case['id']}/candidate-response",
                        {"candidate_response": correction},
                    )
                    st.rerun()

            st.divider()
            st.markdown("##### ⚡ Quick Vendor Simulation (Demo Mode)")
            sim_cols = st.columns(3)
            with sim_cols[0]:
                if st.button("✅ Simulate All Clear", use_container_width=True):
                    requests.post(f"{API_BASE_URL}/agentic-bgv/cases/{case['id']}/simulate-checks?scenario=clear")
                    st.rerun()
            with sim_cols[1]:
                if st.button("⚠️ Simulate Discrepancy", use_container_width=True):
                    requests.post(f"{API_BASE_URL}/agentic-bgv/cases/{case['id']}/simulate-checks?scenario=discrepancy")
                    st.rerun()
            with sim_cols[2]:
                if st.button("🚨 Simulate Critical Red Flag", use_container_width=True):
                    requests.post(f"{API_BASE_URL}/agentic-bgv/cases/{case['id']}/simulate-checks?scenario=red_flag")
                    st.rerun()

        # TAB 2: COMPONENT VERIFICATION MATRIX
        with tabs[1]:
            st.markdown("##### 5-Pillar Verification Tracks")
            components = case.get("components", [])
            if not components:
                st.info("No components initialized for this case.")
            else:
                for comp in components:
                    comp_box = st.container()
                    c_status = comp.get("status", "Pending")
                    status_badge = "🟢" if "Clear" in c_status else ("🔴" if "Flag" in c_status else "🟡")
                    with comp_box:
                        c_col1, c_col2, c_col3 = st.columns([0.4, 0.4, 0.2])
                        c_col1.markdown(f"**{status_badge} {comp['component_type']}**")
                        c_col1.caption(f"Status: **{comp['status']}** | Severity: **{comp.get('severity', 'Low')}**")
                        c_col2.write(f"Findings: {comp.get('remarks') or 'In progress / No remarks.'}")
                        with c_col3:
                            with st.popover("✏️ Edit Track"):
                                new_st = st.selectbox(f"Status for {comp['id']}", ["Verified Clear", "In Progress", "Discrepancy Found", "Critical Flag"], key=f"st_{comp['id']}")
                                new_sev = st.selectbox(f"Severity for {comp['id']}", ["None", "Low", "Medium", "High", "Critical"], key=f"sev_{comp['id']}")
                                new_rem = st.text_input(f"Remarks for {comp['id']}", value=comp.get("remarks") or "", key=f"rem_{comp['id']}")
                                if st.button("Save", key=f"btn_{comp['id']}"):
                                    api_post(
                                        f"/agentic-bgv/cases/{case['id']}/components/{comp['id']}",
                                        {"status": new_st, "severity": new_sev, "remarks": new_rem},
                                    )
                                    st.rerun()
                    st.markdown("---")

        # TAB 3: AI COMPLIANCE & REVIEW
        with tabs[2]:
            st.markdown("##### 🧠 AI Risk Assessment & Findings")
            st.info(case.get("ai_summary") or "All checks clear or awaiting initial vendor assessment.")

            st.markdown("##### ✉️ AI-Drafted Candidate Clarification Pack")
            st.text_area("Draft Communication", value=case.get("ai_draft_email") or "", height=200)

            rev_col1, rev_col2 = st.columns(2)
            with rev_col1:
                st.markdown("**HR Review of Draft**")
                hr_notes = st.text_area("HR Reviewer Notes", value="Approved for dispatch to candidate.")
                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    if st.button("✅ Approve AI Draft", use_container_width=True):
                        api_post(f"/agentic-bgv/cases/{case['id']}/hr-review", {"approved": True, "reviewer_notes": hr_notes})
                        st.success("Draft approved and dispatched!")
                        st.rerun()
                with bcol2:
                    if st.button("✏️ Request Re-Draft", use_container_width=True):
                        api_post(f"/agentic-bgv/cases/{case['id']}/hr-review", {"approved": False, "reviewer_notes": hr_notes})
                        st.rerun()

            with rev_col2:
                st.markdown("**Final HR Decision**")
                decision = st.selectbox("Decision Verdict", ["Proceed", "Reject", "Hold"])
                decision_notes = st.text_area("Final Disposition Rationale", value="Candidate passed all enterprise criteria.")
                if st.button("🔒 Finalize Decision", use_container_width=True):
                    api_post(
                        f"/agentic-bgv/cases/{case['id']}/hr-review",
                        {"approved": True, "reviewer_notes": decision_notes, "final_decision": decision},
                    )
                    st.success(f"Case closed with decision: {decision}")
                    st.rerun()

        # TAB 4: AUDIT DOSSIER & EXPORT
        with tabs[3]:
            st.markdown("##### 📄 Formal Background Verification Audit Dossier")
            st.caption("Official compliance documentation suitable for internal audit, SOX compliance, and ISO 27001 records.")
            
            report_url = f"{API_BASE_URL}/agentic-bgv/cases/{case['id']}/report/html"
            st.link_button("🌐 Open Printable Audit Dossier (HTML)", report_url, use_container_width=True)

            with st.expander("👁️ Preview Dossier Data (JSON)", expanded=False):
                try:
                    report_json = api_get(f"/agentic-bgv/cases/{case['id']}/report")
                    st.json(report_json)
                except Exception as ex:
                    st.error(f"Could not load report: {ex}")

        # TAB 5: TIMELINE
        with tabs[4]:
            events = case.get("events", [])
            if events:
                for event in reversed(events):
                    st.write(f"**🕒 {event['created_at']} — {status_label(event['event_type'])}**")
                    st.caption(event["detail"])
                    st.markdown("---")
            else:
                st.info("No audit events recorded yet.")
