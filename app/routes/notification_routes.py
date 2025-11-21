from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.utils.decorators import login_required
from app.utils.helpers import execute_db, query_db

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


def _user_notifications(user_id: int, unread_only: bool = False):
    clause = "AND is_read=0" if unread_only else ""
    return query_db(
        f"""
        SELECT notification_id, message, type, is_read, created_at
        FROM notifications
        WHERE user_id=%s {clause}
        ORDER BY created_at DESC
        """,
        (user_id,),
    )


@notifications_bp.route("/")
@login_required
def list_notifications():
    user_id = session["user_id"]
    filter_state = request.args.get("filter", "all")
    unread_only = filter_state == "unread"

    notifications = _user_notifications(user_id, unread_only=unread_only)
    unread_count = query_db(
        "SELECT COUNT(*) AS c FROM notifications WHERE user_id=%s AND is_read=0",
        (user_id,),
        one=True,
    )["c"]

    return render_template(
        "notifications/list.html",
        notifications=notifications,
        filter_state=filter_state,
        unread_count=unread_count,
    )


@notifications_bp.route("/read/<int:notification_id>", methods=["POST"])
@login_required
def mark_read(notification_id):
    user_id = session["user_id"]
    execute_db(
        "UPDATE notifications SET is_read=1 WHERE notification_id=%s AND user_id=%s",
        (notification_id, user_id),
    )
    flash("Notification marked as read.", "success")
    return redirect(request.referrer or url_for("notifications.list_notifications"))


@notifications_bp.route("/read_all", methods=["POST"])
@login_required
def mark_all_read():
    user_id = session["user_id"]
    execute_db(
        "UPDATE notifications SET is_read=1 WHERE user_id=%s",
        (user_id,),
    )
    flash("All notifications cleared.", "success")
    return redirect(request.referrer or url_for("notifications.list_notifications"))
