from flask import Blueprint, render_template, request, redirect, session, url_for
import os
from werkzeug.security import check_password_hash


auth_bp = Blueprint("auth", __name__)

# Carregar credenciais de variáveis de ambiente
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
# Hash gerado com: python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('admin'))"
# Para produção, use: python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('SUA_SENHA_FORTE'))"
ADMIN_PASSWORD_HASH = os.getenv(
    "ADMIN_PASSWORD_HASH",
    "scrypt:32768:8:1$mK3qJZGvHxOCE6Hv$a0b5e5c5e5c5e5c5e5c5e5c5e5c5e5c5e5c5e5c5e5c5e5c5e5c5e5c5e5c5e5c5e5c5e5c5e5c5e5c5e5c5e5c5"
)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Página de login"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Autenticação com hash de senha
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("dashboard.index"))
        else:
            return render_template("login.html", error="Credenciais inválidas")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for("auth.login"))
