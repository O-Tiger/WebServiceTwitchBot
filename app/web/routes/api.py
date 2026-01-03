from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os, csv, json

from app.web.app_state import token_manager, bot_manager, streamer_manager
from datetime import datetime

UPLOAD_FOLDER = 'data/uploads'
ALLOWED_EXTENSIONS = {'csv', 'json', 'txt'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

api_bp = Blueprint("api", __name__, url_prefix="/api")


# MARK: API ENDPOINTS

@api_bp.route("/bot/start", methods=["POST"])
def start_bot():
    """Inicia bot em um canal"""
    data = request.json
    channel = data.get("channel")

    if not channel:
        return jsonify({"error": "Canal não especificado"}), 400

    if not token_manager:
        return jsonify({"error": "Token OAuth não configurado"}), 400

    token = token_manager.get_valid_token()
    print(token_manager)
    print(token)
    if not token:
        return jsonify({"error": "Token inválido"}), 400

    # Conectar ao canal
    success = bot_manager.connect_to_channel(channel, token)

    if success:
        return jsonify({"status": "connected", "channel": channel})
    else:
        return jsonify({"error": "Falha ao conectar"}), 500


@api_bp.route("/bot/stop", methods=["POST"])
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


@api_bp.route("/bot/send", methods=["POST"])
def send_message():
    """Envia mensagem para o chat"""
    data = request.json
    channel = data.get("channel")
    message = data.get("message")

    if not channel or not message:
        return jsonify({"error": "Canal ou mensagem não especificados"}), 400

    success = bot_manager.send_message(channel, message)

    if success:
        return jsonify({"status": "sent"})
    return jsonify({"error": "Falha ao enviar"}), 500


@api_bp.route("/stats")
def get_stats():
    """Retorna estatísticas agregadas"""
    stats = bot_manager.get_aggregated_stats()
    return jsonify(stats)


@api_bp.route("/stats/<channel>")
def get_channel_stats(channel):
    """Retorna estatísticas de um canal específico"""
    stats = bot_manager.get_channel_stats(channel)

    if stats:
        return jsonify(stats)
    else:
        return jsonify({"error": "Canal não encontrado"}), 404


@api_bp.route("/streamers", methods=["GET"])
def get_streamers():
    """Lista todos os streamers"""
    return jsonify({"streamers": streamer_manager.get_streamers()})


@api_bp.route("/streamers/add", methods=["POST"])
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


@api_bp.route("/streamers/remove", methods=["POST"])
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


@api_bp.route("/auto-response/add", methods=["POST"])
def add_auto_response():
    """Adiciona resposta automática"""
    data = request.json
    trigger = data.get("trigger")
    response = data.get("response")

    if not trigger or not response:
        return jsonify({"error": "Trigger ou resposta não especificados"}), 400

    bot_manager.add_auto_response(trigger, response)
    return jsonify({"status": "added", "trigger": trigger})


@api_bp.route("/auto-response/list", methods=["GET"])
def list_auto_responses():
    """Lista todas as respostas automáticas"""
    return jsonify({"responses": bot_manager.auto_responses})


@api_bp.route("/auto-response/remove", methods=["POST"])
def remove_auto_response():
    """Remove resposta automática"""
    data = request.json
    trigger = data.get("trigger")

    if not trigger:
        return jsonify({"error": "Trigger não especificado"}), 400

    if trigger in bot_manager.auto_responses:
        bot_manager.remove_auto_response(trigger)
        return jsonify({"status": "removed", "trigger": trigger})
    return jsonify({"error": "Trigger não encontrado"}), 404


#MARK: IMPORT FILES


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api_bp.route("/import/streamelements", methods=["POST"])
def import_streamelements():
    """Importa pontos do StreamElements (CSV)"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Nenhum arquivo enviado"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "Nome de arquivo vazio"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Tipo de arquivo não permitido"}), 400
        
        # Salvar arquivo temporariamente
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Processar CSV
        imported_users = []
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                # StreamElements CSV tem: username, points, watchtime
                username = row.get('username', row.get('user', '')).strip()
                points = int(row.get('points', row.get('balance', 0)))
                
                if username:
                    # Adicionar ao bot_manager
                    bot_manager.import_user_points(username, points)
                    imported_users.append({"username": username, "points": points})
        
        # Deletar arquivo temporário
        os.remove(filepath)
        
        return jsonify({
            "status": "success",
            "imported": len(imported_users),
            "users": imported_users[:10]  # Mostrar primeiros 10
        })
        
    except Exception as e:
        print(f"❌ Erro ao importar StreamElements: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@api_bp.route("/import/nightbot", methods=["POST"])
def import_nightbot():
    """Importa dados do Nightbot (JSON)"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Nenhum arquivo enviado"}), 400
        
        file = request.files['file']
        
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({"error": "Arquivo inválido"}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Processar JSON
        with open(filepath, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
        
        imported_commands = []
        
        # Nightbot JSON tem lista de comandos
        if 'commands' in data:
            for cmd in data['commands']:
                trigger = cmd.get('name', '').replace('!', '')
                response = cmd.get('message', '')
                
                if trigger and response:
                    bot_manager.add_auto_response(trigger, response)
                    imported_commands.append({"trigger": trigger, "response": response})
        
        os.remove(filepath)
        
        return jsonify({
            "status": "success",
            "imported": len(imported_commands),
            "commands": imported_commands[:10]
        })
        
    except Exception as e:
        print(f"❌ Erro ao importar Nightbot: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500