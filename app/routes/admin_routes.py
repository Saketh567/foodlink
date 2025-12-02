import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.utils.decorators import login_required, role_required
from app.utils.helpers import NO_SHOW_THRESHOLD, create_notification, execute_db, query_db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    stats = {
        "total_clients": query_db("SELECT COUNT(*) AS c FROM clients", one=True)["c"],
        "pending_clients": query_db(
            "SELECT COUNT(*) AS c FROM clients WHERE verification_status='pending'",
            one=True,
        )["c"],
        "pending_volunteers": query_db(
            "SELECT COUNT(*) AS c FROM users WHERE role='volunteer' AND is_active=0",
            one=True,
        )["c"],
        "verified_clients": query_db(
            "SELECT COUNT(*) AS c FROM clients WHERE verification_status='verified'",
            one=True,
        )["c"],
        "total_volunteers": query_db(
            "SELECT COUNT(*) AS c FROM users WHERE role='volunteer'",
            one=True,
        )["c"],
        "pending_proxies": query_db(
            "SELECT COUNT(*) AS c FROM client_proxies WHERE status='pending'",
            one=True,
        )["c"],
        "todays_distributions": query_db(
            """
            SELECT COUNT(*) AS c
            FROM distributions
            WHERE DATE(distribution_date)=CURDATE()
            """,
            one=True,
        )["c"],
        "active_signins": query_db(
            "SELECT COUNT(*) AS c FROM volunteer_signins WHERE status='signed_in'",
            one=True,
        )["c"],
        "no_show_alerts": query_db(
            "SELECT COUNT(*) AS c FROM clients WHERE no_show_count >= %s",
            (NO_SHOW_THRESHOLD,),
            one=True,
        )["c"],
    }

    pending_clients = query_db(
        """
        SELECT c.client_id, c.client_number, u.full_name, u.email, c.created_at
        FROM clients c
        JOIN users u ON u.user_id = c.user_id
        WHERE c.verification_status='pending'
        ORDER BY c.created_at ASC
        LIMIT 5
        """
    )

    pending_proxies = query_db(
        """
        SELECT p.proxy_id, p.proxy_name, c.client_number, u.full_name AS client_name
        FROM client_proxies p
        JOIN clients c ON c.client_id = p.client_id
        JOIN users u ON u.user_id = c.user_id
        WHERE p.status='pending'
        ORDER BY p.created_at DESC
        LIMIT 5
        """
    )

    recent_distributions = query_db(
        """
        SELECT d.distribution_id,
               d.distribution_date,
               c.client_number,
               u.full_name AS volunteer_name
        FROM distributions d
        JOIN clients c ON c.client_id = d.client_id
        JOIN users u ON u.user_id = d.volunteer_id
        ORDER BY d.distribution_date DESC
        LIMIT 5
        """
    )

    top_no_shows = query_db(
        """
        SELECT c.client_id, c.client_number, c.no_show_count, u.full_name
        FROM clients c
        JOIN users u ON u.user_id = c.user_id
        WHERE c.no_show_count > 0
        ORDER BY c.no_show_count DESC
        LIMIT 5
        """
    )

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        pending_clients=pending_clients,
        pending_proxies=pending_proxies,
        recent_distributions=recent_distributions,
        top_no_shows=top_no_shows,
    )


@admin_bp.route("/verify_clients")
@login_required
@role_required("admin")
def verify_clients():
    pending = query_db(
        """
        SELECT c.*, u.full_name, u.email, u.phone
        FROM clients c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.verification_status = 'pending'
        ORDER BY c.created_at ASC
        """
    )

    return render_template("admin/verify_clients.html", pending=pending)


@admin_bp.route("/clients/<int:client_id>")
@login_required
@role_required("admin")
def client_profile(client_id):
    client = query_db(
        """
        SELECT c.*, u.full_name, u.email, u.phone
        FROM clients c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.client_id=%s
        """,
        (client_id,),
        one=True,
    )

    if not client:
        flash("Client not found.", "danger")
        return redirect(url_for("admin.verify_clients"))

    proxies = query_db(
        """
        SELECT *
        FROM client_proxies
        WHERE client_id=%s
        ORDER BY created_at DESC
        """,
        (client_id,),
    )

    distributions = query_db(
        """
        SELECT d.*, u.full_name AS volunteer_name
        FROM distributions d
        JOIN users u ON u.user_id = d.volunteer_id
        WHERE d.client_id=%s
        ORDER BY d.distribution_date DESC
        LIMIT 5
        """,
        (client_id,),
    )

    return render_template(
        "admin/client_profile.html",
        client=client,
        proxies=proxies,
        distributions=distributions,
    )


@admin_bp.route("/approve_client/<int:client_id>", methods=["POST"])
@login_required
@role_required("admin")
def approve_client(client_id):
    client = query_db(
        "SELECT client_id, user_id, verification_status FROM clients WHERE client_id=%s",
        (client_id,),
        one=True,
    )
    if not client:
        flash("Client not found.", "danger")
        return redirect(url_for("admin.verify_clients"))

    if client["verification_status"] == "verified":
        flash("Client is already verified.", "info")
        return redirect(url_for("admin.client_profile", client_id=client_id))

    existing_numbers = query_db(
        "SELECT client_number FROM clients WHERE client_number IS NOT NULL"
    )

    next_sequence = 0
    for row in existing_numbers or []:
        token = row.get("client_number")
        if not token:
            continue
        match = re.search(r"(\d+)$", token)
        if not match:
            continue
        try:
            value = int(match.group(1))
        except ValueError:
            continue
        next_sequence = max(next_sequence, value)

    next_sequence += 1
    new_number = f"CL{next_sequence:04d}"
    while query_db(
        "SELECT client_id FROM clients WHERE client_number=%s",
        (new_number,),
        one=True,
    ):
        next_sequence += 1
        new_number = f"CL{next_sequence:04d}"

    admin_id = session.get("user_id")
    execute_db(
        """
        UPDATE clients
        SET verification_status = 'verified',
            client_number = %s,
            verified_by = %s,
            verified_date = NOW(),
            updated_at = NOW()
        WHERE client_id = %s
        """,
        (new_number, admin_id, client_id),
    )

    create_notification(
        client["user_id"],
        f"Your FoodLink registration has been approved. Your client number is {new_number}.",
        "success",
    )

    flash(f"Client approved and assigned number {new_number}.", "success")
    return redirect(url_for("admin.client_profile", client_id=client_id))


@admin_bp.route("/reject_client/<int:client_id>", methods=["POST"])
@login_required
@role_required("admin")
def reject_client(client_id):
    client = query_db(
        "SELECT client_id, user_id FROM clients WHERE client_id=%s",
        (client_id,),
        one=True,
    )
    if not client:
        flash("Client not found.", "danger")
        return redirect(url_for("admin.verify_clients"))

    execute_db(
        """
        UPDATE clients
        SET verification_status = 'rejected',
            verified_by = %s,
            verified_date = NULL,
            updated_at = NOW()
        WHERE client_id = %s
        """,
        (session.get("user_id"), client_id),
    )

    create_notification(
        client["user_id"],
        "Unfortunately, your FoodLink registration was not approved. Please contact support for next steps.",
        "warning",
    )

    flash("Client rejected.", "danger")
    return redirect(url_for("admin.verify_clients"))


@admin_bp.route("/clients/<int:client_id>/notes", methods=["POST"])
@login_required
@role_required("admin")
def update_client_notes(client_id):
    client = query_db(
        "SELECT client_id FROM clients WHERE client_id=%s",
        (client_id,),
        one=True,
    )
    if not client:
        flash("Client not found.", "danger")
        return redirect(url_for("admin.verify_clients"))

    notes = request.form.get("notes", "").strip()
    execute_db(
        """
        UPDATE clients
        SET notes = %s,
            updated_at = NOW()
        WHERE client_id = %s
        """,
        (notes if notes else None, client_id),
    )

    flash("Client notes updated.", "success")
    return redirect(url_for("admin.client_profile", client_id=client_id))


@admin_bp.route("/proxies")
@login_required
@role_required("admin")
def proxy_requests():
    pending = query_db(
        """
        SELECT p.*, c.client_number, u.full_name AS client_name
        FROM client_proxies p
        JOIN clients c ON p.client_id = c.client_id
        JOIN users u ON c.user_id = u.user_id
        WHERE p.status = 'pending'
        ORDER BY p.created_at DESC
        """
    )

    return render_template("admin/proxy_requests.html", proxies=pending)


@admin_bp.route("/proxies/approve/<int:proxy_id>", methods=["POST"])
@login_required
@role_required("admin")
def approve_proxy(proxy_id):
    proxy = query_db(
        """
        SELECT proxy_id, client_id
        FROM client_proxies
        WHERE proxy_id=%s
        """,
        (proxy_id,),
        one=True,
    )
    if not proxy:
        flash("Proxy not found.", "danger")
        return redirect(url_for("admin.proxy_requests"))

    execute_db(
        """
        UPDATE client_proxies
        SET status='approved',
            approved_by=%s
        WHERE proxy_id=%s
        """,
        (session.get("user_id"), proxy_id),
    )

    client_user = query_db(
        """
        SELECT users.user_id
        FROM clients
        JOIN users ON users.user_id = clients.user_id
        WHERE clients.client_id=%s
        """,
        (proxy["client_id"],),
        one=True,
    )
    if client_user:
        create_notification(
            client_user["user_id"],
            "Your proxy pickup request has been approved.",
            "success",
        )

    flash("Proxy approved.", "success")
    return redirect(url_for("admin.proxy_requests"))


@admin_bp.route("/proxies/reject/<int:proxy_id>", methods=["POST"])
@login_required
@role_required("admin")
def reject_proxy(proxy_id):
    proxy = query_db(
        """
        SELECT proxy_id, client_id
        FROM client_proxies
        WHERE proxy_id=%s
        """,
        (proxy_id,),
        one=True,
    )
    if not proxy:
        flash("Proxy not found.", "danger")
        return redirect(url_for("admin.proxy_requests"))

    execute_db(
        """
        UPDATE client_proxies
        SET status='rejected',
            approved_by=NULL
        WHERE proxy_id=%s
        """,
        (proxy_id,),
    )

    client_user = query_db(
        """
        SELECT users.user_id
        FROM clients
        JOIN users ON users.user_id = clients.user_id
        WHERE clients.client_id=%s
        """,
        (proxy["client_id"],),
        one=True,
    )
    if client_user:
        create_notification(
            client_user["user_id"],
            "Your proxy pickup request was rejected. Please review and resubmit if needed.",
            "warning",
        )

    flash("Proxy rejected.", "danger")
    return redirect(url_for("admin.proxy_requests"))


@admin_bp.route("/no_shows")
@login_required
@role_required("admin")
def no_show_report():
    stats = {
        "today": query_db(
            "SELECT COUNT(*) AS c FROM no_show_logs WHERE DATE(created_at)=CURDATE()",
            one=True,
        )["c"],
        "week": query_db(
            """
            SELECT COUNT(*) AS c
            FROM no_show_logs
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            """,
            one=True,
        )["c"],
        "total": query_db(
            "SELECT COUNT(*) AS c FROM no_show_logs",
            one=True,
        )["c"],
    }

    logs = query_db(
        """
        SELECT l.*, c.client_number, u.full_name AS client_name,
               vu.full_name AS volunteer_name
        FROM no_show_logs l
        JOIN clients c ON c.client_id = l.client_id
        JOIN users u ON u.user_id = c.user_id
        LEFT JOIN users vu ON vu.user_id = l.logged_by
        ORDER BY l.created_at DESC
        LIMIT 50
        """
    )

    high_risk = query_db(
        """
        SELECT c.client_id, c.client_number, u.full_name, c.no_show_count
        FROM clients c
        JOIN users u ON u.user_id = c.user_id
        WHERE c.no_show_count >= %s
        ORDER BY c.no_show_count DESC
        LIMIT 10
        """,
        (NO_SHOW_THRESHOLD,),
    )

    return render_template(
        "admin/no_show_report.html",
        stats=stats,
        logs=logs,
        high_risk=high_risk,
        threshold=NO_SHOW_THRESHOLD,
    )


# -------------------------------------------------------------
# VOLUNTEER VERIFICATION
# -------------------------------------------------------------
@admin_bp.route("/verify_volunteers")
@login_required
@role_required("admin")
def verify_volunteers():
    pending = query_db(
        "SELECT * FROM users WHERE role='volunteer' AND is_active=0 ORDER BY created_at ASC"
    )
    return render_template("admin/verify_volunteers.html", pending=pending)


@admin_bp.route("/approve_volunteer/<int:user_id>", methods=["POST"])
@login_required
@role_required("admin")
def approve_volunteer(user_id):
    user = query_db("SELECT * FROM users WHERE user_id=%s AND role='volunteer'", (user_id,), one=True)
    if not user:
        flash("Volunteer not found.", "danger")
        return redirect(url_for("admin.verify_volunteers"))

    execute_db("UPDATE users SET is_active=1 WHERE user_id=%s", (user_id,))
    
    # Notify (if we had email, we'd send one here)
    create_notification(user_id, "Your volunteer account has been approved! You can now log in.", "success")
    
    flash(f"Volunteer {user['full_name']} approved.", "success")
    return redirect(url_for("admin.verify_volunteers"))


@admin_bp.route("/reject_volunteer/<int:user_id>", methods=["POST"])
@login_required
@role_required("admin")
def reject_volunteer(user_id):
    user = query_db("SELECT * FROM users WHERE user_id=%s AND role='volunteer'", (user_id,), one=True)
    if not user:
        flash("Volunteer not found.", "danger")
        return redirect(url_for("admin.verify_volunteers"))

    # Hard delete for rejected registrations to keep DB clean
    execute_db("DELETE FROM users WHERE user_id=%s", (user_id,))
    
    flash(f"Volunteer request for {user['full_name']} rejected and removed.", "info")
    return redirect(url_for("admin.verify_volunteers"))
