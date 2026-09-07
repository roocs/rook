"""Public service identification from PyWPS metadata."""

from pywps import configuration as pywps_configuration


def get_service_identification():
    """Return provider and contact metadata shared by status representations."""
    return {
        "provider": {
            "name": _metadata_value("provider_name"),
            "url": _metadata_value("provider_url"),
        },
        "contact": {
            "name": _metadata_value("contact_name"),
            "city": _metadata_value("contact_city"),
            "country": _metadata_value("contact_country"),
            "url": _metadata_value("contact_url"),
        },
    }


def _metadata_value(option):
    try:
        value = pywps_configuration.get_config_value("metadata:main", option)
    except Exception:  # status metadata must not prevent the report
        return None
    if not isinstance(value, str):
        return None
    return value.strip() or None
