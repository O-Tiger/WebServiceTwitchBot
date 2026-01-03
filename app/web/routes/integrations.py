"""
Rotas de API para Integrações
Discord, Minecraft, Email, Twitch API
"""

from flask import Blueprint, request, jsonify
from app.web.app_state import integration_manager

integrations_bp = Blueprint("integrations", __name__, url_prefix="/api/integrations")

# ===== STATUS DAS INTEGRAÇÕES =====

@integrations_bp.route("/status", methods=["GET"])
def get_integrations_status():
    """Retorna status de todas as integrações"""
    try:
        config = integration_manager.config
        dependencies = integration_manager.check_integration_dependencies() if hasattr(integration_manager, 'check_integration_dependencies') else {}
        
        return jsonify({
            "discord": {
                "enabled": config.get("discord", {}).get("enabled", False),
                "configured": bool(config.get("discord", {}).get("token")),
                "available": dependencies.get("Discord", False)
            },
            "minecraft": {
                "enabled": config.get("minecraft", {}).get("enabled", False),
                "configured": bool(config.get("minecraft", {}).get("host")),
                "available": dependencies.get("Minecraft", False)
            },
            "email": {
                "enabled": config.get("email", {}).get("enabled", False),
                "configured": bool(config.get("email", {}).get("email")),
                "available": dependencies.get("Email", False)
            },
            "twitch_api": {
                "enabled": config.get("twitch_api", {}).get("enabled", False),
                "configured": bool(config.get("twitch_api", {}).get("client_id")),
                "available": dependencies.get("Requests", False)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== DISCORD =====

@integrations_bp.route("/discord/setup", methods=["POST"])
def setup_discord():
    """Configura integração com Discord"""
    try:
        data = request.json
        token = data.get("token", "").strip()
        channel_id = data.get("channel_id", "").strip()
        
        if not token or not channel_id:
            return jsonify({"error": "Token e Channel ID são obrigatórios"}), 400
        
        success, message = integration_manager.setup_discord(token, channel_id)
        
        if success:
            return jsonify({"status": "success", "message": message})
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integrations_bp.route("/discord/test", methods=["POST"])
def test_discord():
    """Testa envio de mensagem para Discord"""
    try:
        data = request.json
        message = data.get("message", "Teste de integração do Twitch Bot!")
        
        success, response = integration_manager.send_to_discord(message)
        
        if success:
            return jsonify({"status": "success", "message": response})
        else:
            return jsonify({"error": response}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integrations_bp.route("/discord/disable", methods=["POST"])
def disable_discord():
    """Desabilita integração com Discord"""
    try:
        integration_manager.config["discord"]["enabled"] = False
        integration_manager.save_config()
        return jsonify({"status": "success", "message": "Discord desabilitado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== MINECRAFT =====

@integrations_bp.route("/minecraft/setup", methods=["POST"])
def setup_minecraft():
    """Configura integração com Minecraft (RCON)"""
    try:
        data = request.json
        host = data.get("host", "localhost").strip()
        port = int(data.get("port", 25575))
        password = data.get("password", "").strip()
        
        if not host or not password:
            return jsonify({"error": "Host e senha são obrigatórios"}), 400
        
        success, message = integration_manager.setup_minecraft(host, port, password)
        
        if success:
            return jsonify({"status": "success", "message": message})
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integrations_bp.route("/minecraft/test", methods=["POST"])
def test_minecraft():
    """Testa comando no servidor Minecraft"""
    try:
        data = request.json
        command = data.get("command", "say Teste de integração!")
        
        success, response = integration_manager.send_to_minecraft(command)
        
        if success:
            return jsonify({"status": "success", "message": response})
        else:
            return jsonify({"error": response}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integrations_bp.route("/minecraft/disable", methods=["POST"])
def disable_minecraft():
    """Desabilita integração com Minecraft"""
    try:
        integration_manager.config["minecraft"]["enabled"] = False
        integration_manager.save_config()
        return jsonify({"status": "success", "message": "Minecraft desabilitado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== EMAIL =====

@integrations_bp.route("/email/setup", methods=["POST"])
def setup_email():
    """Configura integração com Email"""
    try:
        data = request.json
        smtp_server = data.get("smtp_server", "smtp.gmail.com").strip()
        port = int(data.get("port", 587))
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        
        if not email or not password:
            return jsonify({"error": "Email e senha são obrigatórios"}), 400
        
        success, message = integration_manager.setup_email(smtp_server, port, email, password)
        
        if success:
            return jsonify({"status": "success", "message": message})
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integrations_bp.route("/email/test", methods=["POST"])
def test_email():
    """Testa envio de email"""
    try:
        data = request.json
        to_email = data.get("to", integration_manager.config["email"]["email"])
        subject = data.get("subject", "Teste de Integração - Twitch Bot")
        body = data.get("body", "Este é um email de teste da integração do Twitch Bot!")
        
        success, response = integration_manager.send_email(to_email, subject, body)
        
        if success:
            return jsonify({"status": "success", "message": response})
        else:
            return jsonify({"error": response}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integrations_bp.route("/email/disable", methods=["POST"])
def disable_email():
    """Desabilita integração com Email"""
    try:
        integration_manager.config["email"]["enabled"] = False
        integration_manager.save_config()
        return jsonify({"status": "success", "message": "Email desabilitado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== TWITCH API =====

@integrations_bp.route("/twitch-api/setup", methods=["POST"])
def setup_twitch_api():
    """Configura Twitch API avançada"""
    try:
        data = request.json
        client_id = data.get("client_id", "").strip()
        client_secret = data.get("client_secret", "").strip()
        
        if not client_id or not client_secret:
            return jsonify({"error": "Client ID e Client Secret são obrigatórios"}), 400
        
        success, message = integration_manager.setup_twitch_api(client_id, client_secret)
        
        if success:
            return jsonify({"status": "success", "message": message})
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integrations_bp.route("/twitch-api/user/<username>", methods=["GET"])
def get_twitch_user_id(username):
    """Obtém ID de um usuário da Twitch"""
    try:
        user_id = integration_manager.get_user_id(username)
        
        if user_id:
            return jsonify({"user_id": user_id, "username": username})
        else:
            return jsonify({"error": "Usuário não encontrado"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integrations_bp.route("/twitch-api/followers/<broadcaster_id>", methods=["GET"])
def get_followers(broadcaster_id):
    """Obtém seguidores de um canal"""
    try:
        followers = integration_manager.get_channel_followers(broadcaster_id)
        return jsonify({"total": len(followers), "followers": followers})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integrations_bp.route("/twitch-api/disable", methods=["POST"])
def disable_twitch_api():
    """Desabilita Twitch API"""
    try:
        integration_manager.config["twitch_api"]["enabled"] = False
        integration_manager.save_config()
        return jsonify({"status": "success", "message": "Twitch API desabilitada"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500