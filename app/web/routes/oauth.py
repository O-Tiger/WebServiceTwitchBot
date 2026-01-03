from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    session,
    jsonify,
    url_for,
)
from app.core.oauth_manager import OAuthConfig, OAuthManager, OAUTH_TUTORIALS
import secrets


oauth_bp = Blueprint("oauth", __name__)
oauth_config = OAuthConfig()
oauth_manager = OAuthManager(oauth_config)

# ===== OAUTH ROUTES =====


@oauth_bp.route("/oauth/<provider>")
def oauth_login(provider):
    """Inicia fluxo OAuth para um provedor"""

    # Verificar se provedor é válido
    if provider not in ["google", "twitch", "github", "discord"]:
        return jsonify({"error": "Provedor inválido"}), 400

    # Verificar se está configurado
    if not oauth_config.is_configured(provider):
        return render_template(
            "oauth_setup.html",
            provider=provider,
            tutorial=OAUTH_TUTORIALS.get(provider),
            config=oauth_config.get_provider_config(provider),
        )

    # Gerar state para segurança
    state = secrets.token_urlsafe(32)
    session[f"oauth_state_{provider}"] = state

    # Obter URL de autorização
    success, auth_url = oauth_manager.get_authorization_url(provider, state)

    if success:
        return redirect(auth_url)
    else:
        return jsonify({"error": auth_url}), 500


@oauth_bp.route("/oauth/<provider>/callback")
def oauth_callback(provider):
    """Callback OAuth"""

    # Verificar se há erro
    error = request.args.get("error")
    if error:
        return render_template("oauth_error.html", error=error, provider=provider)

    # Obter código
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Código não recebido"}), 400

    # Verificar state (CSRF protection)
    state = request.args.get("state")
    expected_state = session.get(f"oauth_state_{provider}")

    if state and expected_state and state != expected_state:
        return jsonify({"error": "State inválido"}), 400

    # Trocar código por token
    success, token_data = oauth_manager.exchange_code_for_token(provider, code)

    if not success:
        return jsonify({"error": "Falha ao obter token"}), 500

    # Obter informações do usuário
    access_token = token_data.get("access_token")
    success, user_data = oauth_manager.get_user_info(provider, access_token)

    if not success:
        return jsonify({"error": "Falha ao obter dados do usuário"}), 500

    # Criar sessão
    session["logged_in"] = True
    session["username"] = user_data.get("name") or user_data.get("username")
    session["email"] = user_data.get("email")
    session["provider"] = provider
    session["user_id"] = user_data.get("id")
    session["picture"] = user_data.get("picture")

    # Limpar state
    session.pop(f"oauth_state_{provider}", None)

    return redirect(url_for("dashboard.index"))
