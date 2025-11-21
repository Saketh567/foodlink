import json
import re
from typing import Any, Dict, List, Optional

import requests
from flask import current_app


class AddressValidationError(Exception):
    """Raised when an address cannot be validated."""


def _config(key: str, default: Any = None) -> Any:
    return current_app.config.get(key, default)


def _canada_post_key() -> str:
    return _config("CANADA_POST_API_KEY", "")


def _base_url() -> str:
    return _config(
        "CANADA_POST_API_BASE",
        "https://ws1.postescanadapost.ca/AddressComplete/Interactive",
    ).rstrip("/")


def _allow_fallback() -> bool:
    return bool(_config("ADDRESS_VALIDATION_ALLOW_FALLBACK", True))


def _normalize_postal_code(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    alnum = re.sub(r"\s+", "", value).upper()
    if len(alnum) == 6:
        return f"{alnum[:3]} {alnum[3:]}"
    return value


def _format_address_string(components: Dict[str, Any]) -> str:
    parts = [
        components.get("line1"),
        components.get("line2"),
        ", ".join(
            filter(
                None,
                [
                    components.get("city"),
                    components.get("province"),
                    components.get("postal_code"),
                ],
            )
        ),
        components.get("country"),
    ]
    return ", ".join(filter(None, parts))


def search_addresses(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Proxy to Canada Post AddressComplete search endpoint.
    Returns a lightweight list of suggestions or empty list on failure.
    """
    key = _canada_post_key()
    if not key or len(query.strip()) < 3:
        return []

    url = f"{_base_url()}/Find/v2.10/json3ex.ws"
    params = {
        "Key": key,
        "SearchTerm": query.strip(),
        "Country": "CAN",
        "LanguagePreference": "EN",
        "MaxSuggestions": max_results,
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("Items") or []
        return [
            {
                "id": item.get("Id"),
                "text": item.get("Text"),
                "description": item.get("Description"),
            }
            for item in items
            if item.get("Text")
        ]
    except Exception:
        return []


def _retrieve_selection(selection_id: str) -> Optional[Dict[str, Any]]:
    key = _canada_post_key()
    if not key or not selection_id:
        return None

    url = f"{_base_url()}/Retrieve/v2.10/json3ex.ws"
    params = {"Key": key, "Id": selection_id}
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("Items") or []
        return items[0] if items else None
    except Exception:
        return None


def _components_from_item(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "line1": item.get("Line1"),
        "line2": item.get("Line2"),
        "city": item.get("City"),
        "province": item.get("ProvinceName") or item.get("Province"),
        "postal_code": _normalize_postal_code(item.get("PostalCode")),
        "country": "Canada",
        "raw": json.dumps(item),
    }


def validate_address(
    address: str,
    selection_id: Optional[str] = None,
    require_selection: bool = False,
) -> Dict[str, Any]:
    """
    Validate and standardize an address.
    - If Canada Post key is configured, uses AddressComplete search + retrieve.
    - Falls back to basic validation if allowed via config.
    """
    cleaned = (address or "").strip()
    if not cleaned:
        raise AddressValidationError("Address is required.")

    allow_fallback = _allow_fallback()
    key = _canada_post_key()

    if not key and not allow_fallback:
        raise AddressValidationError(
            "Address validation is unavailable. Please contact support to configure Canada Post."
        )

    selected = _retrieve_selection(selection_id) if selection_id else None

    if require_selection and key and not selection_id:
        raise AddressValidationError("Please select your address from the dropdown suggestions.")

    # If no explicit selection, find the top match then retrieve details.
    if not selected and key:
        suggestions = search_addresses(cleaned, max_results=1)
        if suggestions:
            selected = _retrieve_selection(suggestions[0]["id"])

    if selected:
        components = _components_from_item(selected)
        formatted = _format_address_string(components)
        return {
            "valid": True,
            "formatted": formatted or cleaned,
            "original": cleaned,
            "components": components,
            "source": "canada-post",
        }

    if not allow_fallback:
        raise AddressValidationError(
            "Could not validate the address. Please check spelling or try another address."
        )

    # Fallback: basic structure validation
    if len(cleaned.split()) < 2:
        raise AddressValidationError("Please include a full street address.")

    fallback_components = {
        "line1": cleaned,
        "city": None,
        "province": None,
        "postal_code": None,
        "country": "Canada",
    }
    return {
        "valid": True,
        "formatted": cleaned,
        "original": cleaned,
        "components": fallback_components,
        "source": "local-fallback",
    }
