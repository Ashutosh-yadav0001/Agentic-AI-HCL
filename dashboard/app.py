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


st.set_page_config(page_title="Agentic BGV", layout="wide")
st.title("Agentic AI BGV System")
st.caption("HR workflow console for offer acceptance, background verification, AI-assisted issue handling, and final decisioning.")

with st.sidebar:
    st.subheader("Connection")
    st.write(API_BASE_URL)
    if st.button("Refresh", use_container_width=True):
        st.rerun()

try:
    health = api_get("/")
except requests.RequestException as exc:
    st.error(f"FastAPI backend is not reachable at {API_BASE_URL}. Start it with: uvicorn bgv_app.main:app --reload")
    st.exception(exc)
    st.stop()

st.success(f"Backend connected: {health['app']}")

left, right = st.columns([0.35, 0.65])

with left:
    st.subheader("Create Candidate")
    with st.form("candidate_form", clear_on_submit=True):
        name = st.text_input("Name", value="Anita Sharma")
        email = st.text_input("Email", value="anita.sharma@example.com")
        phone = st.text_input("Phone", value="")
        submitted = st.form_submit_button("Add Candidate", use_container_width=True)
        if submitted:
            try:
                api_post("/candidates", {"name": name, "email": email, "phone": phone or None})
                st.success("Candidate added")
                st.rerun()
            except requests.HTTPError as exc:
                st.error(exc.response.text)

    candidates = api_get("/candidates")
    st.subheader("Start BGV Case")
    if not candidates:
        st.info("Add a candidate to begin.")
    else:
        labels = {f"{c['name']} <{c['email']}>": c["id"] for c in candidates}
        selected_candidate = st.selectbox("Candidate", labels.keys())
        vendor = st.text_input("Vendor", value="Demo Verify")
        if st.button("Send Offer Email", use_container_width=True):
            api_post("/agentic-bgv/cases", {"candidate_id": labels[selected_candidate], "vendor_name": vendor})
            st.success("Offer workflow started")
            st.rerun()

with right:
    cases = api_get("/agentic-bgv/cases")
    st.subheader("Cases")
    if not cases:
        st.info("No BGV cases yet.")
    else:
        case_options = {
            f"#{case['id']} - {case['candidate']['name']} - {status_label(case['status'])}": case
            for case in cases
        }
        selected_label = st.selectbox("Active case", case_options.keys())
        case = case_options[selected_label]

        metrics = st.columns(4)
        metrics[0].metric("Status", status_label(case["status"]))
        metrics[1].metric("Risk", case["risk_level"] or "Pending")
        metrics[2].metric("Documents", len(case["documents"]))
        metrics[3].metric("Vendor Checks", len(case["vendor_checks"]))

        tabs = st.tabs(["Workflow Actions", "AI Review", "Timeline"])

        with tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Offer Response**")
                offer_choice = st.radio("Candidate accepted?", ["Accepted", "Declined"], horizontal=True)
                if st.button("Record Offer Response", use_container_width=True):
                    api_post(
                        f"/agentic-bgv/cases/{case['id']}/offer-response",
                        {"accepted": offer_choice == "Accepted"},
                    )
                    st.rerun()

                st.markdown("**BGV Document**")
                doc_type = st.text_input("Document type", value="Identity Proof")
                file_name = st.text_input("File name", value="aadhaar.pdf")
                file_url = st.text_input("File URL", value="https://example.com/aadhaar.pdf")
                if st.button("Submit Document To Vendor", use_container_width=True):
                    api_post(
                        f"/agentic-bgv/cases/{case['id']}/documents",
                        {"document_type": doc_type, "file_name": file_name, "file_url": file_url},
                    )
                    st.rerun()

            with col2:
                st.markdown("**Vendor Result**")
                outcome = st.selectbox("Outcome", ["Clear", "Missing Document", "Discrepancy", "Red Flag"])
                remarks = st.text_area("Vendor remarks", value="Address proof does not match the current address.")
                if st.button("Submit Vendor Result", use_container_width=True):
                    api_post(
                        f"/agentic-bgv/cases/{case['id']}/vendor-status",
                        {"vendor_outcome": outcome, "vendor_remarks": remarks},
                    )
                    st.rerun()

                st.markdown("**Candidate Correction**")
                correction = st.text_area(
                    "Candidate response",
                    value="I have uploaded my latest rental agreement for address proof.",
                )
                if st.button("Send For Re-verification", use_container_width=True):
                    api_post(
                        f"/agentic-bgv/cases/{case['id']}/candidate-response",
                        {"candidate_response": correction},
                    )
                    st.rerun()

        with tabs[1]:
            st.markdown("**AI Summary**")
            st.write(case["ai_summary"] or "No AI summary yet. Submit a non-clear vendor result to generate one.")
            st.markdown("**Draft Candidate Email**")
            st.text_area("Draft", value=case["ai_draft_email"] or "", height=220)

            review_col, decision_col = st.columns(2)
            with review_col:
                notes = st.text_area("HR notes", value="Send to candidate")
                if st.button("Approve Draft", use_container_width=True):
                    api_post(
                        f"/agentic-bgv/cases/{case['id']}/hr-review",
                        {"approved": True, "reviewer_notes": notes},
                    )
                    st.rerun()
                if st.button("Request Draft Changes", use_container_width=True):
                    api_post(
                        f"/agentic-bgv/cases/{case['id']}/hr-review",
                        {"approved": False, "reviewer_notes": notes},
                    )
                    st.rerun()
            with decision_col:
                final_decision = st.selectbox("Final decision", ["Proceed", "Reject", "Hold"])
                final_notes = st.text_area("Final decision notes", value="Proceed with HR approval.")
                if st.button("Update Final Decision", use_container_width=True):
                    api_post(
                        f"/agentic-bgv/cases/{case['id']}/hr-review",
                        {
                            "approved": True,
                            "reviewer_notes": final_notes,
                            "final_decision": final_decision,
                        },
                    )
                    st.rerun()

        with tabs[2]:
            if case["events"]:
                for event in case["events"]:
                    st.write(f"**{event['created_at']} - {status_label(event['event_type'])}**")
                    st.caption(event["detail"])
            else:
                st.info("No timeline events yet.")
