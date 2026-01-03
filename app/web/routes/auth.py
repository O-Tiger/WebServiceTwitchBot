from flask import Blueprint, render_template, request, redirect, session, url_for


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Página de login"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Autenticação simples (melhorar em produção)
        if username == "admin" and password == "admin":
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
