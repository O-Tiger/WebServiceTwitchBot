"""
Aplicação Flask Principal - Twitch Bot Dashboard
Versão corrigida com logs funcionando e mensagens aparecendo
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
import os
import sys
from datetime import datetime
import secrets

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.bot_manager import BotManager
from app.core.token_manager import TokenManager
from app.core.streamer_manager import StreamerManager
from app.core.oauth_manager import OAuthConfig, OAuthManager, OAUTH_TUTORIALS

app = Flask(__name__)
app.config["SECRET_KEY"] = "twitch-bot-secret-key-2025"

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    # ✅ TIMEOUTS AUMENTADOS
    ping_timeout=60,  # Espera 60s pela resposta do ping
    ping_interval=25,  # Envia ping a cada 25s para manter conexão viva
    # ✅ CONFIGURAÇÕES ADICIONAIS
    engineio_logger=True,  # Logs detalhados
    logger=True,  # Logs do SocketIO
    # ✅ Permitir reconexão automática
    always_connect=True,
    # ✅ Configurações de transporte
    transports=["websocket", "polling"],  # Websocket primeiro, polling como fallback
)


# Instâncias globais
bot_manager = BotManager()
token_manager = None
streamer_manager = StreamerManager()
oauth_config = OAuthConfig()
oauth_manager = OAuthManager(oauth_config)


# Configurar callbacks do BotManager
def on_message(channel, username, message, messages, points):
    """Callback quando mensagem é recebida"""
    socketio.emit(
        "chat_message",
        {
            "channel": channel,
            "username": username,
            "message": message,
            "messages": messages,
            "points": points,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        },
    )


def on_status_change(channel, status):
    """Callback quando status muda"""
    socketio.emit("status_change", {"channel": channel, "status": status})


def on_log(level, message):
    """Callback para logs"""
    socketio.emit(
        "log_message",
        {
            "level": level,
            "message": message,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        },
    )


def on_raid(channel, raider, viewers):
    """Callback quando raid é recebida"""
    socketio.emit(
        "raid_received",
        {
            "channel": channel,
            "raider": raider,
            "viewers": viewers,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        },
    )

    # Log também
    on_log("event", f"🎉 RAID de {raider} com {viewers} viewers no canal {channel}!")


bot_manager.set_callbacks(
    on_message=on_message, on_status=on_status_change, on_log=on_log, on_raid=on_raid
)


# ===== ROTAS WEB =====


@app.route("/")
def index():
    """Dashboard principal"""
    if "logged_in" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        streamers=streamer_manager.get_streamers(),
        connected=list(bot_manager.connected_channels),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Página de login"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Autenticação simples (melhorar em produção)
        if username == "admin" and password == "admin":
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Credenciais inválidas")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for("login"))


@app.route("/integrations")
def integrations():
    """Página de integrações"""
    if "logged_in" not in session:
        return redirect(url_for("login"))

    return render_template("integrations.html")


@app.route("/help")
def help_page():
    """Página de ajuda"""
    if "logged_in" not in session:
        return redirect(url_for("login"))

    return render_template("help.html")


# ===== OAUTH ROUTES =====


@app.route("/auth/<provider>")
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


@app.route("/auth/<provider>/callback")
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

    return redirect(url_for("index"))


@app.route("/oauth/setup/<provider>", methods=["GET", "POST"])
def oauth_setup(provider):
    """Página de configuração OAuth"""

    if request.method == "POST":
        client_id = request.form.get("client_id")
        client_secret = request.form.get("client_secret")

        if not client_id or not client_secret:
            return render_template(
                "oauth_setup.html",
                provider=provider,
                tutorial=OAUTH_TUTORIALS.get(provider),
                config=oauth_config.get_provider_config(provider),
                error="Preencha todos os campos",
            )

        # Salvar credenciais
        oauth_config.set_credentials(provider, client_id, client_secret)

        return redirect(url_for("oauth_login", provider=provider))

    return render_template(
        "oauth_setup.html",
        provider=provider,
        tutorial=OAUTH_TUTORIALS.get(provider),
        config=oauth_config.get_provider_config(provider),
    )


@app.route("/api/oauth/status")
def oauth_status():
    """Retorna status de configuração OAuth"""
    return jsonify(
        {
            "google": oauth_config.is_configured("google"),
            "twitch": oauth_config.is_configured("twitch"),
            "github": oauth_config.is_configured("github"),
            "discord": oauth_config.is_configured("discord"),
        }
    )


# ===== API ENDPOINTS =====


@app.route("/api/bot/start", methods=["POST"])
def start_bot():
    """Inicia bot em um canal"""
    global token_manager

    data = request.json
    channel = data.get("channel")

    if not channel:
        return jsonify({"error": "Canal não especificado"}), 400

    # Carregar token
    if not token_manager:
        token_manager = load_token_manager()

    if not token_manager:
        return jsonify({"error": "Token OAuth não configurado"}), 400

    token = token_manager.get_valid_token()
    if not token:
        return jsonify({"error": "Token inválido"}), 400

    # Conectar ao canal
    success = bot_manager.connect_to_channel(channel, token)

    if success:
        return jsonify({"status": "connected", "channel": channel})
    else:
        return jsonify({"error": "Falha ao conectar"}), 500


@app.route("/api/bot/stop", methods=["POST"])
def stop_bot():
    """Para bot em um canal"""
    data = request.json
    channel = data.get("channel")

    if not channel:
        return jsonify({"error": "Canal não especificado"}), 400

    success = bot_manager.disconnect_from_channel(channel)

    if success:
        return jsonify({"status": "disconnected", "channel": channel})
    else:
        return jsonify({"error": "Falha ao desconectar"}), 500


@app.route("/api/bot/send", methods=["POST"])
def send_message():
    """Envia mensagem para o chat"""
    data = request.json
    channel = data.get("channel")
    message = data.get("message")

    if not channel or not message:
        return jsonify({"error": "Canal ou mensagem não especificados"}), 400

    success = bot_manager.send_message(channel, message)

    if success:
        # Emitir evento para mostrar a mensagem enviada
        socketio.emit(
            "chat_message",
            {
                "channel": channel,
                "username": "Você",
                "message": message,
                "messages": 0,
                "points": 0,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "isOwn": True,
            },
        )
        return jsonify({"status": "sent"})
    else:
        return jsonify({"error": "Falha ao enviar"}), 500


@app.route("/api/stats")
def get_stats():
    """Retorna estatísticas agregadas"""
    stats = bot_manager.get_aggregated_stats()
    return jsonify(stats)


@app.route("/api/stats/<channel>")
def get_channel_stats(channel):
    """Retorna estatísticas de um canal específico"""
    stats = bot_manager.get_channel_stats(channel)

    if stats:
        return jsonify(stats)
    else:
        return jsonify({"error": "Canal não encontrado"}), 404


@app.route("/api/streamers", methods=["GET"])
def get_streamers():
    """Lista todos os streamers"""
    return jsonify({"streamers": streamer_manager.get_streamers()})


@app.route("/api/streamers/add", methods=["POST"])
def add_streamer():
    """Adiciona novo streamer"""
    data = request.json
    username = data.get("username")

    if not username:
        return jsonify({"error": "Username não especificado"}), 400

    success, message = streamer_manager.add_streamer(username)

    if success:
        return jsonify({"status": "added", "message": message})
    else:
        return jsonify({"error": message}), 400


@app.route("/api/streamers/remove", methods=["POST"])
def remove_streamer():
    """Remove streamer"""
    data = request.json
    username = data.get("username")

    if not username:
        return jsonify({"error": "Username não especificado"}), 400

    success, message = streamer_manager.remove_streamer(username)

    if success:
        return jsonify({"status": "removed", "message": message})
    else:
        return jsonify({"error": message}), 400


@app.route("/api/auto-response/add", methods=["POST"])
def add_auto_response():
    """Adiciona resposta automática"""
    data = request.json
    trigger = data.get("trigger")
    response = data.get("response")

    if not trigger or not response:
        return jsonify({"error": "Trigger ou resposta não especificados"}), 400

    bot_manager.add_auto_response(trigger, response)

    return jsonify({"status": "added", "trigger": trigger, "response": response})


@app.route("/api/auto-response/list", methods=["GET"])
def list_auto_responses():
    """Lista todas as respostas automáticas"""
    return jsonify({"responses": bot_manager.auto_responses})


@app.route("/api/auto-response/remove", methods=["POST"])
def remove_auto_response():
    """Remove resposta automática"""
    data = request.json
    trigger = data.get("trigger")

    if not trigger:
        return jsonify({"error": "Trigger não especificado"}), 400

    if trigger in bot_manager.auto_responses:
        del bot_manager.auto_responses[trigger]

        # Remover de todos os bots ativos
        for bot in bot_manager.bots.values():
            if trigger in bot.auto_responses:
                del bot.auto_responses[trigger]
                bot.save_data()

        # Salvar alterações
        bot_manager._save_auto_responses()

        return jsonify({"status": "removed", "trigger": trigger})
    else:
        return jsonify({"error": "Trigger não encontrado"}), 404


# ===== WEBSOCKET EVENTS =====


@socketio.on("connect")
def handle_connect():
    """Cliente conectou via WebSocket"""
    emit("connected", {"status": "ok"})


@socketio.on("disconnect")
def handle_disconnect():
    """Cliente desconectou"""
    print("Cliente desconectou")


@socketio.on("request_stats")
def handle_stats_request():
    """Cliente solicitou estatísticas"""
    stats = bot_manager.get_aggregated_stats()
    emit("stats_update", stats)


# ===== HELPERS =====


def load_token_manager():
    """Carrega TokenManager do arquivo"""
    try:
        import json

        script_dir = os.path.dirname(os.path.abspath(__file__))
        oauth_file = os.path.join(script_dir, "../../data/oauth_config.json")

        if os.path.exists(oauth_file):
            with open(oauth_file, "r") as f:
                oauth = json.load(f)
                return TokenManager(
                    oauth.get("client_id", ""),
                    oauth.get("client_secret", ""),
                    oauth.get("refresh_token", ""),
                )
    except Exception as e:
        print(f"Erro ao carregar token: {e}")

    return None


if __name__ == "__main__":
    # Carregar token na inicialização
    token_manager = load_token_manager()

    # Perguntar sobre modo debug
    DebugOptionBool: bool = False
    try:
        DebugOption = int(
            input("Deseja iniciar o servidor em modo de Debug? \n1 - Sim\n2 - Não: \n")
        )
        match DebugOption:
            case 1:
                DebugOptionBool = True
            case 2:
                DebugOptionBool = False
            case _:
                print("Invalid option! Using default (Debug=False)")
    except ValueError:
        print("Invalid input! Using default (Debug=False)")
    except KeyboardInterrupt:
        print("\n\n⚠️  Inicialização cancelada pelo usuário.\n")
        sys.exit(0)

    socketio.run(
        app,
        debug=DebugOptionBool,
        host="127.0.0.1",
        port=5000,
        use_reloader=False,  # ✅ Desabilitar reloader (causa problemas com threads)
        log_output=True,
    )
