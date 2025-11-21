import json
import os
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    session,
    flash,
    redirect,
    url_for,
    current_app,
    request,
)
from app.utils.address_service import AddressValidationError, validate_address
from app.utils.decorators import login_required, role_required
from app.utils.helpers import query_db, execute_db

client_bp = Blueprint("client", __name__, url_prefix="/client")


@client_bp.route("/dashboard")
@login_required
@role_required("client")
def client_dashboard():
    user_id = session["user_id"]

    # Fetch client + user data
    client = query_db(
        """
        SELECT c.*, u.full_name 
        FROM clients c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.user_id = %s
        """,
        (user_id,),
        one=True,
    )

    if not client:
        flash("Client profile not found.", "danger")
        return redirect(url_for("index"))

    client_id = client.get("client_id")
    qr_filename = None

    # Only generate QR code if verified
    if client.get("verification_status") == "verified" and client_id and client.get("client_number"):
        from app.utils.qrcode_utils import generate_client_qr

        save_dir = os.path.join(current_app.root_path, "static", "qrcodes")
        os.makedirs(save_dir, exist_ok=True)

        qr_filename = generate_client_qr(
            client_id=client_id,
            client_number=client["client_number"],
            save_dir=save_dir,
        )

    # Recent distributions for quick glance
    history_preview = query_db(
        """
        SELECT d.distribution_date,
               d.weight_kg,
               d.items_description,
               u.full_name AS volunteer_name
        FROM distributions d
        LEFT JOIN users u ON d.volunteer_id = u.user_id
        WHERE d.client_id=%s
        ORDER BY d.distribution_date DESC
        LIMIT 3
        """,
        (client_id,),
    )

    proxy_preview = query_db(
        """
        SELECT proxy_name, status, created_at
        FROM client_proxies
        WHERE client_id=%s
        ORDER BY created_at DESC
        LIMIT 3
        """,
        (client_id,),
    )

    proxy_counts_rows = query_db(
        """
        SELECT status, COUNT(*) AS total
        FROM client_proxies
        WHERE client_id=%s
        GROUP BY status
        """,
        (client_id,),
    )
    proxy_counts = {row["status"]: row["total"] for row in proxy_counts_rows} if proxy_counts_rows else {}

    return render_template(
        "client/dashboard.html",
        client=client,
        qr_filename=qr_filename,
        history_preview=history_preview,
        proxy_preview=proxy_preview,
        proxy_counts=proxy_counts,
    )


@client_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("client")
def update_profile():
    """Allow client to update address, family size, allergies, preferences."""
    user_id = session["user_id"]

    client = query_db(
        """
        SELECT c.*, u.full_name, u.email
        FROM clients c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.user_id = %s
        """,
        (user_id,),
        one=True,
    )

    if not client:
        flash("Client profile not found.", "danger")
        return redirect(url_for("client.client_dashboard"))

    if request.method == "POST":
        address = request.form.get("address", "").strip()
        selection_id = request.form.get("address_selection_id", "").strip() or None
        family_size = request.form.get("family_size", "").strip()
        allergies = request.form.get("allergies", "").strip()
        food_pref = request.form.get("food_preferences", "").strip()

        # Simple validation
        try:
            validation = validate_address(address, selection_id=selection_id, require_selection=True)
        except AddressValidationError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("client.update_profile"))

        try:
            fam_size_val = int(family_size) if family_size else 1
            if fam_size_val <= 0:
                raise ValueError()
        except ValueError:
            flash("Family size must be a positive integer.", "danger")
            return redirect(url_for("client.update_profile"))

        standardized_address = validation["formatted"]
        standardized_components = json.dumps(validation.get("components", {}))
        validation_source = validation.get("source")
        validated_at = datetime.utcnow()

        execute_db(
            """
            UPDATE clients
            SET address=%s,
                address_original=%s,
                address_standardized=%s,
                address_validation_source=%s,
                address_validated_at=%s,
                family_size=%s,
                allergies=%s,
                food_preferences=%s
            WHERE client_id=%s
            """,
            (
                standardized_address,
                address,
                standardized_components,
                validation_source,
                validated_at,
                fam_size_val,
                allergies,
                food_pref,
                client["client_id"],
            ),
        )

        flash("Profile updated successfully.", "success")
        return redirect(url_for("client.client_dashboard"))

    return render_template("client/update_profile.html", client=client)


@client_bp.route("/history")
@login_required
@role_required("client")
def pickup_history():
    """Show all distributions for this client."""
    user_id = session["user_id"]

    client = query_db(
        "SELECT client_id FROM clients WHERE user_id=%s",
        (user_id,),
        one=True,
    )

    if not client:
        flash("Client profile not found.", "danger")
        return redirect(url_for("client.client_dashboard"))

    history = query_db(
        """
        SELECT d.*, u.full_name AS volunteer_name
        FROM distributions d
        LEFT JOIN users u ON d.volunteer_id = u.user_id
        WHERE d.client_id = %s
        ORDER BY d.distribution_date DESC
        """,
        (client["client_id"],),
    )

    return render_template(
        "client/pickup_history.html",
        history=history,
    )


@client_bp.route("/proxies")
@login_required
@role_required("client")
def manage_proxies():
    user_id = session["user_id"]

    client = query_db("SELECT client_id FROM clients WHERE user_id=%s", (user_id,), one=True)
    if not client:
        flash("Client profile not found.", "danger")
        return redirect(url_for("client.client_dashboard"))

    proxies = query_db(
        """
        SELECT proxy_id, proxy_name, proxy_phone, proxy_email, status, created_at
        FROM client_proxies
        WHERE client_id=%s
        ORDER BY created_at DESC
        """,
        (client["client_id"],),
    )

    return render_template("client/manage_proxies.html", proxies=proxies)


@client_bp.route("/proxies/add", methods=["GET", "POST"])
@login_required
@role_required("client")
def add_proxy():
    user_id = session["user_id"]

    client = query_db("SELECT client_id FROM clients WHERE user_id=%s", (user_id,), one=True)
    if not client:
        flash("Client profile not found.", "danger")
        return redirect(url_for("client.client_dashboard"))

    if request.method == "POST":
        proxy_name = request.form.get("proxy_name", "").strip()
        proxy_phone = request.form.get("proxy_phone", "").strip()
        proxy_email = request.form.get("proxy_email", "").strip()

        if not proxy_name:
            flash("Proxy name is required.", "danger")
            return redirect(url_for("client.add_proxy"))

        execute_db(
            """
            INSERT INTO client_proxies (client_id, proxy_name, proxy_phone, proxy_email)
            VALUES (%s, %s, %s, %s)
            """,
            (client["client_id"], proxy_name, proxy_phone or None, proxy_email or None),
        )

        flash("Proxy request submitted. Waiting for admin approval.", "success")
        return redirect(url_for("client.manage_proxies"))

    return render_template("client/add_proxy.html")


@client_bp.route("/proxies/delete/<int:proxy_id>", methods=["POST"])
@login_required
@role_required("client")
def delete_proxy(proxy_id):
    user_id = session["user_id"]

    client = query_db("SELECT client_id FROM clients WHERE user_id=%s", (user_id,), one=True)
    if not client:
        flash("Client profile not found.", "danger")
        return redirect(url_for("client.client_dashboard"))

    execute_db(
        """
        DELETE FROM client_proxies
        WHERE proxy_id=%s AND client_id=%s AND status!='approved'
        """,
        (proxy_id, client["client_id"]),
    )

    flash("Proxy removed.", "info")
    return redirect(url_for("client.manage_proxies"))


