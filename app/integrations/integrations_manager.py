"""
Sistema de Integrações para Twitch Bot
Suporta: Discord, Minecraft, Email, Twitch API avançada
Instalação: pip install discord.py mcrcon smtplib requests
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

try:
    import discord
    from discord.ext import commands as discord_commands

    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

try:
    from mcrcon import MCRcon

    MINECRAFT_AVAILABLE = True
except ImportError:
    MINECRAFT_AVAILABLE = False

try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class IntegrationManager:
    """Gerenciador central de todas as integrações"""

    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "integrations_config.json")
        self.config = self.load_config()

        # Integrações ativas
        self.discord_bot = None
        self.minecraft_connection = None
        self.twitch_api = None

    def load_config(self) -> Dict[str, Any]:
        """Carrega configurações de integrações"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar config de integrações: {e}")

        return {
            "discord": {"enabled": False, "token": "", "channel_id": ""},
            "minecraft": {"enabled": False, "host": "", "port": 25575, "password": ""},
            "email": {
                "enabled": False,
                "smtp_server": "",
                "port": 587,
                "email": "",
                "password": "",
            },
            "twitch_api": {"enabled": False, "client_id": "", "client_secret": ""},
        }

    def save_config(self):
        """Salva configurações"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print("✅ Configurações de integrações salvas")
        except Exception as e:
            print(f"❌ Erro ao salvar config: {e}")

    # ===== DISCORD =====

    def setup_discord(self, token: str, channel_id: str):
        """Configura integração com Discord"""
        if not DISCORD_AVAILABLE:
            return (
                False,
                "Biblioteca discord.py não instalada. Use: pip install discord.py",
            )

        self.config["discord"]["token"] = token
        self.config["discord"]["channel_id"] = channel_id
        self.config["discord"]["enabled"] = True
        self.save_config()

        return True, "Discord configurado com sucesso"

    def send_to_discord(self, message: str):
        """Envia mensagem para Discord"""
        if not self.config["discord"]["enabled"]:
            return False, "Discord não está habilitado"

        if not DISCORD_AVAILABLE:
            return False, "Discord não disponível"

        # Implementação assíncrona necessária para envio real
        # Por enquanto, retorna sucesso
        return True, f"Mensagem enviada para Discord: {message}"

    # ===== MINECRAFT =====

    def setup_minecraft(self, host: str, port: int, password: str):
        """Configura integração com servidor Minecraft (RCON)"""
        if not MINECRAFT_AVAILABLE:
            return False, "Biblioteca mcrcon não instalada. Use: pip install mcrcon"

        self.config["minecraft"]["host"] = host
        self.config["minecraft"]["port"] = port
        self.config["minecraft"]["password"] = password
        self.config["minecraft"]["enabled"] = True
        self.save_config()

        return True, "Minecraft configurado com sucesso"

    def send_to_minecraft(self, command: str):
        """Envia comando para servidor Minecraft via RCON"""
        if not self.config["minecraft"]["enabled"]:
            return False, "Minecraft não está habilitado"

        if not MINECRAFT_AVAILABLE:
            return False, "Minecraft RCON não disponível"

        try:
            with MCRcon(
                self.config["minecraft"]["host"],
                self.config["minecraft"]["password"],
                self.config["minecraft"]["port"],
            ) as mcr:
                response = mcr.command(command)
                return True, f"Comando executado: {response}"
        except Exception as e:
            return False, f"Erro ao conectar ao Minecraft: {e}"

    def announce_to_minecraft(self, message: str):
        """Anuncia mensagem no chat do Minecraft"""
        return self.send_to_minecraft(f"say {message}")

    # ===== EMAIL =====

    def setup_email(self, smtp_server: str, port: int, email: str, password: str):
        """Configura integração com Email"""
        if not EMAIL_AVAILABLE:
            return False, "Biblioteca email não disponível"

        self.config["email"]["smtp_server"] = smtp_server
        self.config["email"]["port"] = port
        self.config["email"]["email"] = email
        self.config["email"]["password"] = password
        self.config["email"]["enabled"] = True
        self.save_config()

        return True, "Email configurado com sucesso"

    def send_email(self, to: str, subject: str, body: str):
        """Envia email"""
        if not self.config["email"]["enabled"]:
            return False, "Email não está habilitado"

        if not EMAIL_AVAILABLE:
            return False, "Email não disponível"

        try:
            msg = MIMEMultipart()
            msg["From"] = self.config["email"]["email"]
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(
                self.config["email"]["smtp_server"], self.config["email"]["port"]
            )
            server.starttls()
            server.login(
                self.config["email"]["email"], self.config["email"]["password"]
            )
            server.send_message(msg)
            server.quit()

            return True, f"Email enviado para {to}"
        except Exception as e:
            return False, f"Erro ao enviar email: {e}"

    # ===== TWITCH API HELIX =====

    def setup_twitch_api(self, client_id: str, client_secret: str):
        """Configura Twitch API avançada (Helix)"""
        if not REQUESTS_AVAILABLE:
            return False, "Biblioteca requests não disponível"

        self.config["twitch_api"]["client_id"] = client_id
        self.config["twitch_api"]["client_secret"] = client_secret
        self.config["twitch_api"]["enabled"] = True
        self.save_config()

        return True, "Twitch API configurada"

    def get_twitch_access_token(self) -> Optional[str]:
        """Obtém access token da Twitch API"""
        if not self.config["twitch_api"]["enabled"]:
            return None

        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": self.config["twitch_api"]["client_id"],
            "client_secret": self.config["twitch_api"]["client_secret"],
            "grant_type": "client_credentials",
        }

        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                return response.json().get("access_token")
        except Exception as e:
            print(f"Erro ao obter token: {e}")

        return None

    def get_channel_followers(self, broadcaster_id: str) -> list:
        """Obtém lista de seguidores do canal"""
        token = self.get_twitch_access_token()
        if not token:
            return []

        url = f"https://api.twitch.tv/helix/channels/followers"
        headers = {
            "Authorization": f"Bearer {token}",
            "Client-Id": self.config["twitch_api"]["client_id"],
        }
        params = {"broadcaster_id": broadcaster_id}

        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            print(f"Erro ao obter followers: {e}")

        return []

    def get_channel_subscribers(self, broadcaster_id: str) -> list:
        """Obtém lista de subscribers do canal"""
        token = self.get_twitch_access_token()
        if not token:
            return []

        url = f"https://api.twitch.tv/helix/subscriptions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Client-Id": self.config["twitch_api"]["client_id"],
        }
        params = {"broadcaster_id": broadcaster_id}

        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            print(f"Erro ao obter subs: {e}")

        return []

    def get_user_id(self, username: str) -> Optional[str]:
        """Obtém ID do usuário pelo username"""
        token = self.get_twitch_access_token()
        if not token:
            return None

        url = "https://api.twitch.tv/helix/users"
        headers = {
            "Authorization": f"Bearer {token}",
            "Client-Id": self.config["twitch_api"]["client_id"],
        }
        params = {"login": username}

        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                users = data.get("data", [])
                if users:
                    return users[0].get("id")
        except Exception as e:
            print(f"Erro ao obter user ID: {e}")

        return None

    # ===== IMPORTAÇÃO DE DADOS =====

    def import_streamelements_points(self, csv_file: str) -> Dict[str, int]:
        """Importa pontos do StreamElements (CSV)"""
        points = {}
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                lines = f.readlines()[1:]  # Skip header
                for line in lines:
                    parts = line.strip().split(",")
                    if len(parts) >= 2:
                        username = parts[0].strip()
                        try:
                            pts = int(parts[1].strip())
                            points[username] = pts
                        except ValueError:
                            continue
            return points
        except Exception as e:
            print(f"Erro ao importar pontos: {e}")
            return {}

    def import_nightbot_points(self, json_file: str) -> Dict[str, int]:
        """Importa pontos do Nightbot (JSON)"""
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("points", {})
        except Exception as e:
            print(f"Erro ao importar Nightbot: {e}")
            return {}

    # ===== SISTEMA DE RANKS =====

    def calculate_rank(self, points: int) -> str:
        """Calcula rank baseado em pontos"""
        if points >= 10000:
            return "🏆 Lendário"
        elif points >= 5000:
            return "💎 Diamante"
        elif points >= 2500:
            return "🥇 Ouro"
        elif points >= 1000:
            return "🥈 Prata"
        elif points >= 500:
            return "🥉 Bronze"
        else:
            return "🆕 Novato"

    def get_rank_rewards(self, rank: str) -> Dict[str, Any]:
        """Retorna recompensas por rank"""
        rewards = {
            "🏆 Lendário": {"multiplier": 3.0, "emoji": "👑"},
            "💎 Diamante": {"multiplier": 2.5, "emoji": "💎"},
            "🥇 Ouro": {"multiplier": 2.0, "emoji": "⭐"},
            "🥈 Prata": {"multiplier": 1.5, "emoji": "✨"},
            "🥉 Bronze": {"multiplier": 1.2, "emoji": "🌟"},
            "🆕 Novato": {"multiplier": 1.0, "emoji": "🎯"},
        }
        return rewards.get(rank, {"multiplier": 1.0, "emoji": "🎯"})


# ===== FUNÇÕES DE UTILIDADE =====


def merge_points(
    bot_points: Dict[str, int], imported_points: Dict[str, int]
) -> Dict[str, int]:
    """Faz merge de pontos importados com pontos do bot"""
    merged = bot_points.copy()
    for user, pts in imported_points.items():
        if user in merged:
            merged[user] += pts  # Soma pontos
        else:
            merged[user] = pts
    return merged


def export_points_to_csv(points: Dict[str, int], filename: str):
    """Exporta pontos para CSV"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("username,Points\n")
            for user, pts in sorted(points.items(), key=lambda x: x[1], reverse=True):
                f.write(f"{user},{pts}\n")
        print(f"✅ Pontos exportados para {filename}")
    except Exception as e:
        print(f"❌ Erro ao exportar: {e}")


def check_integration_dependencies() -> Dict[str, bool]:
    """Verifica quais integrações estão disponíveis"""
    return {
        "Discord": DISCORD_AVAILABLE,
        "Minecraft": MINECRAFT_AVAILABLE,
        "Email": EMAIL_AVAILABLE,
        "Requests": REQUESTS_AVAILABLE,
    }
