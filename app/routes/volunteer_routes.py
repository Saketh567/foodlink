import json
import os
import re
import tempfile
from datetime import datetime

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.utils.decorators import login_required, role_required
from app.utils.helpers import (
    NO_SHOW_THRESHOLD,
    create_notification,
    execute_db,
    log_no_show,
    query_db,
    validate_qr_session,
)
from app.utils.qrcode_utils import decode_qr

volunteer_bp = Blueprint("volunteer", __name__, url_prefix="/volunteer")


# ---------------------------------------------------------
# Helper: Active Sign-In Session
# ---------------------------------------------------------
def _get_active_signin(volunteer_id: int):
    return query_db(
        """
        SELECT *
        FROM volunteer_signins
        WHERE volunteer_id=%s AND status='signed_in'
        ORDER BY signin_time DESC
        LIMIT 1
        """,
        (volunteer_id,),
        one=True,
    )


def _get_next_shift(volunteer_id: int):
    return query_db(
        """
        SELECT schedule_id, schedule_date, start_time, end_time, notes
        FROM volunteer_schedules
        WHERE volunteer_id=%s
          AND status='scheduled'
          AND schedule_date >= CURDATE()
        ORDER BY schedule_date ASC, start_time ASC
        LIMIT 1
        """,
        (volunteer_id,),
        one=True,
    )


def _build_next_tasks(active_signin, stats, volunteer_id):
    tasks = []
    if not active_signin:
        tasks.append(
            {
                "title": "Begin your shift",
                "subtitle": "Sign in so QR scans and distributions are attributed to you.",
            }
        )
    if stats["today"] == 0:
        tasks.append(
            {
                "title": "Log the first pickup of the day",
                "subtitle": "Scan a client QR to open the distribution form.",
            }
        )
    recent_no_shows_row = query_db(
        """
        SELECT COUNT(*) AS c
        FROM no_show_logs
        WHERE logged_by=%s AND DATE(created_at)=CURDATE()
        """,
        (volunteer_id,),
        one=True,
    )
    recent_no_shows = recent_no_shows_row["c"] if recent_no_shows_row else 0
    if recent_no_shows:
        tasks.append(
            {
                "title": "Follow up on today's no-shows",
                "subtitle": "Ensure flagged households are contacted or rescheduled.",
            }
        )
    if not tasks:
        tasks.append(
            {
                "title": "Review recent history",
                "subtitle": "Double-check items and notes for accuracy.",
            }
        )
    return tasks


def _parse_qr_payload(raw_payload):
    if not raw_payload:
        return None
    if isinstance(raw_payload, dict):
        return raw_payload
    try:
        data = json.loads(raw_payload)
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def _validate_qr_client(decoded_payload):
    if not decoded_payload:
        return None, "Invalid or unreadable QR code."
    client_id = decoded_payload.get("client_id")
    if not client_id:
        return None, "Invalid QR data."
    session_id = decoded_payload.get("session_id")
    if session_id:
        session_record = validate_qr_session(session_id)
        if not session_record or session_record["client_id"] != client_id:
            return None, "Invalid or expired QR session."
    client = query_db(
        """
        SELECT c.*, u.full_name, u.email, u.phone
        FROM clients c
        JOIN users u ON u.user_id = c.user_id
        WHERE c.client_id=%s
        """,
        (client_id,),
        one=True,
    )
    if not client:
        return None, "Client not found."
    if client["verification_status"] != "verified":
        return None, "Client is not verified."
    return client, None


def _build_client_preview(client):
    proxies = query_db(
        """
        SELECT proxy_name, proxy_phone, proxy_email, status
        FROM client_proxies
        WHERE client_id=%s
        ORDER BY updated_at DESC
        LIMIT 3
        """,
        (client["client_id"],),
    )
    recent_pickups = query_db(
        """
        SELECT distribution_date, weight_kg, items_description
        FROM distributions
        WHERE client_id=%s
        ORDER BY distribution_date DESC
        LIMIT 3
        """,
        (client["client_id"],),
    )
    preview = {
        "client": {
            "client_id": client["client_id"],
            "client_number": client.get("client_number"),
            "full_name": client.get("full_name"),
            "family_size": client.get("family_size"),
            "verification_status": client.get("verification_status"),
        },
        "proxies": [
            {
                "name": p["proxy_name"],
                "phone": p["proxy_phone"],
                "email": p["proxy_email"],
                "status": p["status"],
            }
            for p in (proxies or [])
        ],
        "recent": [
            {
                "date": pickup["distribution_date"].strftime("%b %d, %Y")
                if pickup["distribution_date"]
                else None,
                "weight": float(pickup["weight_kg"]) if pickup["weight_kg"] is not None else None,
                "items": pickup["items_description"],
            }
            for pickup in (recent_pickups or [])
        ],
    }
    return preview


# ---------------------------------------------------------
# Volunteer Dashboard
# ---------------------------------------------------------
@volunteer_bp.route("/dashboard")
@login_required
@role_required("volunteer")
def volunteer_dashboard():

    volunteer_id = session["user_id"]

    # Basic stats
    stats = {
        "total": query_db(
            "SELECT COUNT(*) AS c FROM distributions WHERE volunteer_id=%s",
            (volunteer_id,),
            one=True,
        )["c"],
        "today": query_db(
            """
            SELECT COUNT(*) AS c
            FROM distributions
            WHERE volunteer_id=%s
              AND DATE(distribution_date)=CURDATE()
            """,
            (volunteer_id,),
            one=True,
        )["c"],
    }

    # Recent 5 distributions
    recent = query_db(
        """
        SELECT d.*, c.client_number, u.full_name AS client_name
        FROM distributions d
        JOIN clients c ON d.client_id = c.client_id
        JOIN users u ON c.user_id = u.user_id
        WHERE d.volunteer_id=%s
        ORDER BY d.distribution_date DESC
        LIMIT 5
        """,
        (volunteer_id,),
    )

    volunteer = query_db(
        "SELECT full_name, email, phone FROM users WHERE user_id=%s",
        (volunteer_id,),
        one=True,
    )

    active_signin = _get_active_signin(volunteer_id)
    upcoming_shift = _get_next_shift(volunteer_id)
    next_tasks = _build_next_tasks(active_signin, stats, volunteer_id)

    return render_template(
        "volunteer/dashboard.html",
        volunteer=volunteer,
        stats=stats,
        recent=recent,
        active_signin=active_signin,
        upcoming_shift=upcoming_shift,
        next_tasks=next_tasks,
    )


# ---------------------------------------------------------
# SIGN-IN
# ---------------------------------------------------------
@volunteer_bp.route("/signin", methods=["GET", "POST"])
@login_required
@role_required("volunteer")
def signin():

    volunteer_id = session["user_id"]
    active_signin = _get_active_signin(volunteer_id)

    if request.method == "POST":
        if active_signin:
            flash("You are already signed in.", "warning")
            return redirect(url_for("volunteer.signin"))

        method = request.form.get("method", "manual")
        notes = request.form.get("notes", "").strip() or None

        execute_db(
            """
            INSERT INTO volunteer_signins (volunteer_id, method, notes)
            VALUES (%s, %s, %s)
            """,
            (volunteer_id, method, notes),
        )

        flash("Sign-in recorded!", "success")
        return redirect(url_for("volunteer.dashboard"))

    return render_template("volunteer/signin.html", active_signin=active_signin)


# ---------------------------------------------------------
# SIGN-OUT
# ---------------------------------------------------------
@volunteer_bp.route("/signout/<int:signin_id>", methods=["POST"])
@login_required
@role_required("volunteer")
def signout(signin_id):

    volunteer_id = session["user_id"]

    signin_record = query_db(
        """
        SELECT *
        FROM volunteer_signins
        WHERE signin_id=%s AND volunteer_id=%s
        """,
        (signin_id, volunteer_id),
        one=True,
    )

    if not signin_record or signin_record["status"] != "signed_in":
        flash("Unable to sign out from that session.", "danger")
        return redirect(url_for("volunteer.dashboard"))

    execute_db(
        """
        UPDATE volunteer_signins
        SET signout_time=NOW(), status='signed_out'
        WHERE signin_id=%s
        """,
        (signin_id,),
    )

    flash("Signed out successfully!", "success")
    return redirect(url_for("volunteer.dashboard"))


# ---------------------------------------------------------
# SCAN QR
# ---------------------------------------------------------
@volunteer_bp.route("/scan", methods=["GET", "POST"])
@login_required
@role_required("volunteer")
def scan_qr():

    if request.method == "POST":
        payload_raw = request.form.get("qr_payload")
        decoded = None

        if payload_raw:
            decoded = _parse_qr_payload(payload_raw)
            if not decoded:
                flash("Camera scan produced invalid data. Please try again.", "danger")
                return redirect(url_for("volunteer.scan_qr"))
        else:
            file = request.files.get("qr_image")
            if not file or file.filename == "":
                flash("Please upload a QR code image or use the camera scanner.", "danger")
                return redirect(url_for("volunteer.scan_qr"))

            fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1])
            os.close(fd)

            try:
                file.save(temp_path)
                decoded = decode_qr(temp_path)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        client, error = _validate_qr_client(decoded)
        if error:
            flash(error, "danger")
            return redirect(url_for("volunteer.scan_qr"))

        session["last_scanned_client"] = client["client_id"]
        return redirect(url_for("volunteer.distribute", client_id=client["client_id"]))

    return render_template("volunteer/scan_qr.html")


@volunteer_bp.route("/scan/preview", methods=["POST"])
@login_required
@role_required("volunteer")
def scan_qr_preview():

    payload_raw = None
    if request.is_json:
        payload_raw = request.json.get("qr_payload")
    else:
        payload_raw = request.form.get("qr_payload")

    decoded = _parse_qr_payload(payload_raw)
    client, error = _validate_qr_client(decoded)
    if error:
        return jsonify({"error": error}), 400

    session["last_scanned_client"] = client["client_id"]
    preview = _build_client_preview(client)
    preview["distribute_url"] = url_for("volunteer.distribute", client_id=client["client_id"])
    return jsonify(preview)


# ---------------------------------------------------------
# DISTRIBUTION
# ---------------------------------------------------------
@volunteer_bp.route("/distribute/<int:client_id>", methods=["GET", "POST"])
@login_required
@role_required("volunteer")
def distribute(client_id):

    volunteer_id = session["user_id"]

    client = query_db(
        """
        SELECT c.*, u.full_name, u.user_id AS client_user_id
        FROM clients c
        JOIN users u ON u.user_id = c.user_id
        WHERE c.client_id=%s
        """,
        (client_id,),
        one=True,
    )

    if not client:
        flash("Client not found.", "danger")
        return redirect(url_for("volunteer.dashboard"))

    proxies = query_db(
        """
        SELECT proxy_name, proxy_phone, proxy_email, status, updated_at
        FROM client_proxies
        WHERE client_id=%s
        ORDER BY updated_at DESC
        """,
        (client_id,),
    )

    recent_pickups = query_db(
        """
        SELECT distribution_date, weight_kg, items_description
        FROM distributions
        WHERE client_id=%s
        ORDER BY distribution_date DESC
        LIMIT 3
        """,
        (client_id,),
    )

    total_pickups = query_db(
        "SELECT COUNT(*) AS c FROM distributions WHERE client_id=%s",
        (client_id,),
        one=True,
    )["c"]

    if request.method == "POST":

        weight_raw = request.form.get("weight_kg")

        try:
            weight = round(float(weight_raw), 2)
            if weight <= 0:
                raise ValueError()
        except Exception:
            flash("Weight must be a positive number.", "danger")
            return redirect(url_for("volunteer.distribute", client_id=client_id))

        items = request.form.get("items_description", "")
        notes = request.form.get("notes", "")
        signed = 1 if request.form.get("signature") == "on" else 0

        execute_db(
            """
            INSERT INTO distributions
            (client_id, volunteer_id, distribution_date, weight_kg, items_description, client_signature, notes)
            VALUES (%s, %s, NOW(), %s, %s, %s, %s)
            """,
            (client_id, volunteer_id, weight, items, signed, notes),
        )

        if client.get("client_user_id"):
            create_notification(
                client["client_user_id"],
                f"Your pickup on {datetime.utcnow().strftime('%b %d, %Y')} has been recorded ({weight} kg).",
                "success",
            )

        volunteer_user = query_db(
            "SELECT full_name FROM users WHERE user_id=%s",
            (volunteer_id,),
            one=True,
        )

        admin_users = query_db("SELECT user_id FROM users WHERE role='admin'")
        for admin in admin_users:
            create_notification(
                admin["user_id"],
                f"Distribution recorded for {client['client_number'] or client_id} by {volunteer_user['full_name']}",
                "info",
            )

        create_notification(
            volunteer_id,
            f"Logged distribution for {client['client_number'] or client_id}.",
            "success",
        )

        flash("Distribution recorded successfully!", "success")
        return redirect(url_for("volunteer.dashboard"))

    return render_template(
        "volunteer/distribute.html",
        client=client,
        proxies=proxies,
        recent_pickups=recent_pickups,
        total_pickups=total_pickups,
    )


# ---------------------------------------------------------
# HISTORY
# ---------------------------------------------------------
@volunteer_bp.route("/history")
@login_required
@role_required("volunteer")
def history():

    volunteer_id = session["user_id"]

    history_records = query_db(
        """
        SELECT d.*, c.client_number, u.full_name AS client_name
        FROM distributions d
        JOIN clients c ON d.client_id = c.client_id
        JOIN users u ON c.user_id = u.user_id
        WHERE d.volunteer_id=%s
        ORDER BY d.distribution_date DESC
        """,
        (volunteer_id,),
    )

    return render_template("volunteer/history.html", history=history_records)


# ---------------------------------------------------------
# ALL DISTRIBUTIONS
# ---------------------------------------------------------
@volunteer_bp.route("/distributions")
@login_required
@role_required("volunteer")
def all_distributions():
    volunteer_id = session["user_id"]

    distributions = query_db(
        """
        SELECT d.*, c.client_number, u.full_name AS client_name
        FROM distributions d
        JOIN clients c ON d.client_id = c.client_id
        JOIN users u ON c.user_id = u.user_id
        WHERE d.volunteer_id=%s
        ORDER BY d.distribution_date DESC
        """,
        (volunteer_id,),
    )

    return render_template("volunteer/all_distributions.html", distributions=distributions)


# ---------------------------------------------------------
# SHIFTS / SIGN-INS
# ---------------------------------------------------------
@volunteer_bp.route("/shifts")
@login_required
@role_required("volunteer")
def shifts():
    volunteer_id = session["user_id"]

    signins = query_db(
        """
        SELECT signin_id, signin_time, signout_time, status, method, notes
        FROM volunteer_signins
        WHERE volunteer_id=%s
        ORDER BY signin_time DESC
        """,
        (volunteer_id,),
    )

    return render_template("volunteer/shifts.html", signins=signins)


# ---------------------------------------------------------
# NO-SHOW MANAGEMENT
# ---------------------------------------------------------
@volunteer_bp.route("/no_shows", methods=["GET", "POST"])
@login_required
@role_required("volunteer")
def manage_no_shows():
    volunteer_id = session["user_id"]
    summary = None
    form_values = {}

    if request.method == "POST":
        form_values = request.form.to_dict()
        expected_raw = request.form.get("expected_clients") or "0"
        actual_raw = request.form.get("actual_clients") or "0"
        reason = request.form.get("reason", "").strip() or "Missed scheduled pickup"
        missing_raw = request.form.get("missing_clients", "")

        try:
            expected = int(expected_raw)
            actual = int(actual_raw)
        except ValueError:
            flash("Expected and actual counts must be whole numbers.", "danger")
            return redirect(url_for("volunteer.manage_no_shows"))

        tokens = [t.strip() for t in re.split(r"[\n,]+", missing_raw) if t.strip()]
        processed = []
        not_found = []

        for token in tokens:
            token_upper = token.upper()
            client = query_db(
                """
                SELECT c.client_id, c.client_number, u.full_name
                FROM clients c
                JOIN users u ON u.user_id = c.user_id
                WHERE c.client_number=%s OR UPPER(u.email)=UPPER(%s)
                """,
                (token_upper, token),
                one=True,
            )

            if not client:
                not_found.append(token)
                continue

            log_no_show(client["client_id"], logged_by=volunteer_id, reason=reason)
            processed.append(client)

        summary = {
            "expected": expected,
            "actual": actual,
            "difference": max(expected - actual, 0),
            "logged": processed,
            "not_found": not_found,
        }

        create_notification(
            volunteer_id,
            f"Attendance logged: {actual}/{expected} clients arrived.",
            "info",
        )

        if summary["difference"] > 0:
            admin_users = query_db("SELECT user_id FROM users WHERE role='admin'")
            for admin in admin_users:
                create_notification(
                    admin["user_id"],
                    f"{summary['difference']} clients missed their pickup (expected {expected}, actual {actual}).",
                    "warning",
                )

        if processed:
            flash(f"Logged {len(processed)} no-shows.", "warning")
        elif not tokens:
            flash("Provide at least one client number or email to mark as no-show.", "danger")
        else:
            flash("No matching clients found for the provided entries.", "danger")

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

    recent_logs = query_db(
        """
        SELECT l.*, c.client_number, u.full_name AS client_name
        FROM no_show_logs l
        JOIN clients c ON c.client_id = l.client_id
        JOIN users u ON u.user_id = c.user_id
        WHERE l.logged_by=%s
        ORDER BY l.created_at DESC
        LIMIT 10
        """,
        (volunteer_id,),
    )

    high_risk = query_db(
        """
        SELECT c.client_id, c.client_number, u.full_name, c.no_show_count
        FROM clients c
        JOIN users u ON u.user_id = c.user_id
        WHERE c.no_show_count >= %s
        ORDER BY c.no_show_count DESC
        LIMIT 5
        """,
        (NO_SHOW_THRESHOLD,),
    )

    return render_template(
        "volunteer/no_shows.html",
        stats=stats,
        recent_logs=recent_logs,
        high_risk=high_risk,
        threshold=NO_SHOW_THRESHOLD,
        summary=summary,
        form_values=form_values,
    )
