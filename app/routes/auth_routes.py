import json
from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from app.utils.address_service import AddressValidationError, validate_address
from app.utils.decorators import login_required
from app.utils.helpers import (
    create_notification,
    execute_db,
    flag_client_account,
    looks_suspicious_client_submission,
    query_db,
)
from app.utils.security import hash_password
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# -------------------------------------------------------------
# CORRECT ROLE → DASHBOARD MAPPING (PERMANENT FIX)
# -------------------------------------------------------------
ROLE_REDIRECTS = {
    "admin": "admin.dashboard",
    "client": "client.client_dashboard",
    "volunteer": "volunteer.volunteer_dashboard",
}

# -------------------------------------------------------------
# LOGIN ROUTE
# -------------------------------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    requested_role = request.args.get("role")
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]
        requested_role = request.form.get("requested_role") or requested_role

        # Fetch user
        user = query_db("SELECT * FROM users WHERE email=%s", (email,), one=True)

        if not user:
            flash("Invalid credentials.", "danger")
            return redirect(url_for("auth.login"))

        # Validate password
        if not check_password_hash(user["password_hash"], password):
            flash("Invalid credentials.", "danger")
            return redirect(url_for("auth.login"))

        # Store session
        session["user_id"] = user["user_id"]
        session["role"] = user["role"]

        # Redirect based on correct mapping
        target = ROLE_REDIRECTS.get(user["role"], "index")
        return redirect(url_for(target))

    return render_template("auth/login.html", requested_role=requested_role)


# -------------------------------------------------------------
# LOGOUT
# -------------------------------------------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("index"))


# -------------------------------------------------------------
# USER REGISTRATION (CLIENT SIGNUP)
# -------------------------------------------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        address = request.form["address"].strip()
        try:
            family_size = int(request.form.get("family_size", 1))
            if family_size <= 0:
                raise ValueError()
        except ValueError:
            flash("Family size must be a positive whole number.", "danger")
            return redirect(url_for("auth.register"))
        allergies = request.form.get("allergies", "")
        food_pref = request.form.get("food_preferences", "")

        try:
            validation = validate_address(
                address,
                selection_id=request.form.get("address_selection_id"),
                require_selection=True,
            )
        except AddressValidationError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("auth.register"))

        standardized_address = validation["formatted"]
        standardized_components = json.dumps(validation.get("components", {}))
        validation_source = validation.get("source")

        hashed = hash_password(password)

        # Create user account
        execute_db("""
            INSERT INTO users (email, password_hash, full_name, role, is_active)
            VALUES (%s, %s, %s, 'client', 1)
        """, (email, hashed, full_name))

        # Fetch new user_id
        new_user = query_db(
            "SELECT user_id FROM users WHERE email=%s",
            (email,),
            one=True
        )
        user_id = new_user["user_id"]

        # Create client profile
        execute_db("""
            INSERT INTO clients (
                user_id,
                address,
                address_original,
                address_standardized,
                address_validation_source,
                address_validated_at,
                family_size,
                allergies,
                food_preferences
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            standardized_address,
            address,
            standardized_components,
            validation_source,
            datetime.utcnow(),
            family_size,
            allergies,
            food_pref,
        ))

        client_row = query_db(
            "SELECT client_id FROM clients WHERE user_id=%s",
            (user_id,),
            one=True,
        )

        if client_row and looks_suspicious_client_submission(full_name, address, email):
            flag_client_account(client_row["client_id"], "Submission auto-flagged for admin review.")
            admin_user = query_db(
                "SELECT user_id FROM users WHERE role='admin' ORDER BY user_id ASC LIMIT 1",
                one=True,
            )
            if admin_user:
                create_notification(
                    admin_user["user_id"],
                    f"Client {full_name} ({email}) was auto-flagged for review.",
                    "warning",
                )

        flash("Registration submitted. Awaiting admin verification.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# -------------------------------------------------------------
# VOLUNTEER REGISTRATION
# -------------------------------------------------------------
@auth_bp.route("/register/volunteer", methods=["GET", "POST"])
def register_volunteer():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        phone = request.form.get("phone", "").strip()

        # Check if email exists
        existing = query_db("SELECT user_id FROM users WHERE email=%s", (email,), one=True)
        if existing:
            flash("Email already registered.", "warning")
            return redirect(url_for("auth.login"))

        hashed = hash_password(password)

        # Create user account (is_active=0 for admin approval)
        execute_db("""
            INSERT INTO users (email, password_hash, full_name, phone, role, is_active)
            VALUES (%s, %s, %s, %s, 'volunteer', 0)
        """, (email, hashed, full_name, phone))

        # Notify admins (optional, but good practice)
        admin_user = query_db(
            "SELECT user_id FROM users WHERE role='admin' ORDER BY user_id ASC LIMIT 1",
            one=True,
        )
        if admin_user:
            create_notification(
                admin_user["user_id"],
                f"New volunteer registration: {full_name} ({email}). Pending approval.",
                "info",
            )

        flash("Registration submitted. Please wait for admin approval.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_volunteer.html")



# -------------------------------------------------------------
# PASSWORD RESET (CLIENT SELF-SERVE)
# -------------------------------------------------------------
@auth_bp.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        client_number = request.form.get("client_number", "").strip().upper()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not email or not client_number:
            flash("Email and client number are required.", "danger")
            return redirect(url_for("auth.reset_password"))

        if len(new_password) < 8:
            flash("New password must be at least 8 characters.", "danger")
            return redirect(url_for("auth.reset_password"))

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.reset_password"))

        client = query_db(
            """
            SELECT users.user_id
            FROM users
            JOIN clients ON clients.user_id = users.user_id
            WHERE users.email=%s AND clients.client_number=%s
            """,
            (email, client_number),
            one=True,
        )

        if not client:
            flash("No matching verified client found.", "danger")
            return redirect(url_for("auth.reset_password"))

        execute_db(
            "UPDATE users SET password_hash=%s WHERE user_id=%s",
            (hash_password(new_password), client["user_id"]),
        )

        flash("Password reset successful. You can log in now.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html")


# -------------------------------------------------------------
# CHANGE PASSWORD (LOGGED-IN USERS)
# -------------------------------------------------------------
@auth_bp.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    user_id = session.get("user_id")
    user = query_db("SELECT user_id, password_hash FROM users WHERE user_id=%s", (user_id,), one=True)
    target_endpoint = ROLE_REDIRECTS.get(session.get("role"), "index")

    if not user:
        flash("Account not found.", "danger")
        return redirect(url_for("auth.logout"))

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not check_password_hash(user["password_hash"], current_password):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("auth.change_password"))

        if len(new_password) < 8:
            flash("New password must be at least 8 characters.", "danger")
            return redirect(url_for("auth.change_password"))

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.change_password"))

        execute_db(
            "UPDATE users SET password_hash=%s WHERE user_id=%s",
            (hash_password(new_password), user_id),
        )

        flash("Password updated successfully.", "success")
        return redirect(url_for("auth.change_password"))

    return render_template("auth/change_password.html", return_url=url_for(target_endpoint))
