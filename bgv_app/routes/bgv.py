from fastapi import APIRouter

router = APIRouter(prefix="/bgv", tags=["bgv"])


@router.get("/statuses")
def statuses():
    return {
        "statuses": [
            "offer_sent",
            "bgv_form_sent",
            "sent_to_vendor",
            "awaiting_hr_review",
            "awaiting_candidate_response",
            "reverification_sent",
            "completed",
            "final_decision_updated",
        ]
    }
