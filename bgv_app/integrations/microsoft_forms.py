from bgv_app.config import get_settings


def offer_form_url() -> str:
    return get_settings().offer_acceptance_form_url


def bgv_form_url() -> str:
    return get_settings().bgv_form_url
