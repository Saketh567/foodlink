from flask import Blueprint, jsonify, request

from app.utils.address_service import (
    AddressValidationError,
    search_addresses,
    validate_address,
)

address_bp = Blueprint("address", __name__, url_prefix="/address")


@address_bp.route("/search")
def address_search():
    query = (request.args.get("q") or "").strip()
    if len(query) < 3:
        return jsonify({"suggestions": []})

    suggestions = search_addresses(query, max_results=7)
    return jsonify({"suggestions": suggestions})


@address_bp.route("/validate", methods=["POST"])
def address_validate():
    payload = request.get_json(silent=True) or {}
    raw_address = (payload.get("address") or "").strip()
    selection_id = payload.get("selection_id") or payload.get("id")

    try:
        result = validate_address(raw_address, selection_id=selection_id)
    except AddressValidationError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400
    except Exception:
        return jsonify({"ok": False, "message": "Address validation failed."}), 500

    return jsonify(
        {
            "ok": True,
            "standardized": result["formatted"],
            "original": result["original"],
            "components": result["components"],
            "source": result["source"],
        }
    )
