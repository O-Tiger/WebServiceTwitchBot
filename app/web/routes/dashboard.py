from flask import Blueprint, render_template, session, redirect, url_for
from app.web.app_state import streamer_manager, bot_manager

dashboard_bp = Blueprint("dashboard", __name__)

# ===== ROTAS WEB =====


@dashboard_bp.route("/")
def index():
    """Dashboard principal"""
    if "logged_in" not in session:
        return redirect(url_for("auth.login"))

    return render_template(
        "dashboard.html",
        streamers=streamer_manager.get_streamers(),
        connected=list(bot_manager.connected_channels),
    )


@dashboard_bp.route("/help")
def help_page():
    """Página de ajuda"""
    if "logged_in" not in session:
        return redirect(url_for("auth.login"))

    return render_template("help.html")


@dashboard_bp.route("/integrations")
def integrations():
    """Página de integrações"""
    if "logged_in" not in session:
        return redirect(url_for("auth.login"))

    return render_template("integrations.html")
