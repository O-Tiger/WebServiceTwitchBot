"""
Aplicação Flask Principal - Twitch Bot Dashboard
Versão corrigida com logs funcionando e mensagens aparecendo
"""

from flask import Flask
from app.web.socket import socketio
from app.web.app_state import bot_manager
from datetime import datetime
import threading
import time
import os
import secrets

app = Flask(__name__)

# Carregar SECRET_KEY de variável de ambiente (OBRIGATÓRIO em produção)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)

# Avisar se usando chave gerada automaticamente
if not os.getenv("FLASK_SECRET_KEY"):
    print("⚠️  ATENÇÃO: Usando SECRET_KEY gerada automaticamente!")
    print("⚠️  Defina FLASK_SECRET_KEY no .env para produção!")

socketio.init_app(app)

# ----------------------------
# REGISTRAR BLUEPRINTS
# ----------------------------

from app.web.routes.api import api_bp
from app.web.routes.auth import auth_bp
from app.web.routes.oauth import oauth_bp
from app.web.routes.dashboard import dashboard_bp
from app.web.routes.integrations import integrations_bp

app.register_blueprint(api_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(oauth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(integrations_bp)

# ----------------------------
# CALLBACKS DO BOT MANAGER
# ----------------------------

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
    
    # 🆕 Emitir stats atualizadas após cada mensagem
    emit_stats_update()


def on_status_change(channel, status):
    """Callback quando status muda"""
    socketio.emit("status_change", {"channel": channel, "status": status})
    
    # 🆕 Emitir stats atualizadas após mudança de status
    emit_stats_update()


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
    on_log("event", f"🎉 RAID de {raider} com {viewers} viewers no canal {channel}!")
    
    # 🆕 Emitir stats atualizadas após raid
    emit_stats_update()


bot_manager.set_callbacks(
    on_message=on_message, 
    on_status=on_status_change, 
    on_log=on_log, 
    on_raid=on_raid
)

# 🆕 NOVA FUNÇÃO: Emitir stats via WebSocket
def emit_stats_update():
    """Emite stats atualizadas via WebSocket"""
    try:
        stats = bot_manager.get_aggregated_stats()
        socketio.emit("stats_update", stats)
    except Exception as e:
        print(f"❌ Erro ao emitir stats: {e}")

# ----------------------------
# WEBSOCKET EVENTS
# ----------------------------

@socketio.on("connect")
def handle_connect():
    """Cliente conectou via WebSocket"""
    print(f"✅ Cliente conectado via WebSocket")
    socketio.emit("connected", {"status": "ok"})
    
    # 🆕 Enviar stats imediatamente quando cliente conecta
    emit_stats_update()


@socketio.on("disconnect")
def handle_disconnect():
    """Cliente desconectou"""
    print("👋 Cliente desconectou")


@socketio.on("request_stats")
def handle_stats_request():
    """Cliente solicitou estatísticas"""
    emit_stats_update()


@socketio.on_error_default
def default_error_handler(e):
    """Handler global de erros do Socket.IO"""
    print(f"❌ Socket.IO Error: {e}")
    import traceback
    traceback.print_exc()

# 🆕 THREAD DE BACKGROUND: Emitir stats periodicamente (fallback)
def background_stats_emitter():
    """Thread que emite stats a cada 15 segundos como fallback"""
    while True:
        try:
            time.sleep(15)  # A cada 15 segundos
            emit_stats_update()
        except Exception as e:
            print(f"❌ Erro no background stats emitter: {e}")

# 🆕 Iniciar thread de background quando o app rodar
def start_background_tasks():
    """Inicia tasks em background"""
    stats_thread = threading.Thread(target=background_stats_emitter, daemon=True)
    stats_thread.start()
    print("✅ Background stats emitter iniciado")


# Iniciar background tasks quando o módulo for importado
# Isso garante que funciona tanto quando rodado diretamente quanto via gunicorn
start_background_tasks()