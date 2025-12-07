"""
Sistema de Autenticação OAuth para múltiplos provedores
Suporta: Google, Twitch, GitHub, Discord
"""

import json
import os
from typing import Optional, Dict, Tuple
import requests
from urllib.parse import urlencode


class OAuthConfig:
    """Configurações OAuth para cada provedor"""

    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "oauth_providers.json")
        self.config = self.load_config()

    def load_config(self) -> Dict:
        """Carrega configurações OAuth"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar config OAuth: {e}")

        # Configuração padrão
        return {
            "google": {
                "client_id": "",
                "client_secret": "",
                "redirect_uri": "http://127.0.0.1:5000/auth/google/callback",
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "user_info_uri": "https://www.googleapis.com/oauth2/v2/userinfo",
                "scopes": ["openid", "email", "profile"],
            },
            "twitch": {
                "client_id": "",
                "client_secret": "",
                "redirect_uri": "http://127.0.0.1:5000/auth/twitch/callback",
                "auth_uri": "https://id.twitch.tv/oauth2/authorize",
                "token_uri": "https://id.twitch.tv/oauth2/token",
                "user_info_uri": "https://api.twitch.tv/helix/users",
                "scopes": ["user:read:email"],
            },
            "github": {
                "client_id": "",
                "client_secret": "",
                "redirect_uri": "http://127.0.0.1:5000/auth/github/callback",
                "auth_uri": "https://github.com/login/oauth/authorize",
                "token_uri": "https://github.com/login/oauth/access_token",
                "user_info_uri": "https://api.github.com/user",
                "scopes": ["read:user", "user:email"],
            },
            "discord": {
                "client_id": "",
                "client_secret": "",
                "redirect_uri": "http://127.0.0.1:5000/auth/discord/callback",
                "auth_uri": "https://discord.com/api/oauth2/authorize",
                "token_uri": "https://discord.com/api/oauth2/token",
                "user_info_uri": "https://discord.com/api/users/@me",
                "scopes": ["identify", "email"],
            },
        }

    def save_config(self):
        """Salva configurações"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print("✅ Configurações OAuth salvas")
        except Exception as e:
            print(f"❌ Erro ao salvar OAuth config: {e}")

    def set_credentials(self, provider: str, client_id: str, client_secret: str):
        """Define credenciais de um provedor"""
        if provider in self.config:
            self.config[provider]["client_id"] = client_id
            self.config[provider]["client_secret"] = client_secret
            self.save_config()
            return True
        return False

    def get_provider_config(self, provider: str) -> Optional[Dict]:
        """Retorna configuração de um provedor"""
        return self.config.get(provider)

    def is_configured(self, provider: str) -> bool:
        """Verifica se provedor está configurado"""
        config = self.config.get(provider, {})
        return bool(config.get("client_id") and config.get("client_secret"))


class OAuthManager:
    """Gerenciador OAuth"""

    def __init__(self, oauth_config: OAuthConfig):
        self.config = oauth_config

    def get_authorization_url(
        self, provider: str, state: str = None
    ) -> Tuple[bool, str]:
        """Gera URL de autorização"""
        provider_config = self.config.get_provider_config(provider)

        if not provider_config:
            return False, f"Provedor {provider} não suportado"

        if not self.config.is_configured(provider):
            return False, f"Provedor {provider} não configurado"

        params = {
            "client_id": provider_config["client_id"],
            "redirect_uri": provider_config["redirect_uri"],
            "response_type": "code",
            "scope": " ".join(provider_config["scopes"]),
        }

        if state:
            params["state"] = state

        # Parâmetros específicos por provedor
        if provider == "google":
            params["access_type"] = "offline"
            params["prompt"] = "consent"

        auth_url = f"{provider_config['auth_uri']}?{urlencode(params)}"
        return True, auth_url

    def exchange_code_for_token(
        self, provider: str, code: str
    ) -> Tuple[bool, Optional[Dict]]:
        """Troca código por access token"""
        provider_config = self.config.get_provider_config(provider)

        if not provider_config:
            return False, None

        data = {
            "client_id": provider_config["client_id"],
            "client_secret": provider_config["client_secret"],
            "code": code,
            "redirect_uri": provider_config["redirect_uri"],
            "grant_type": "authorization_code",
        }

        try:
            headers = {"Accept": "application/json"}
            response = requests.post(
                provider_config["token_uri"], data=data, headers=headers
            )

            if response.status_code == 200:
                return True, response.json()
            else:
                print(f"Erro ao trocar código: {response.text}")
                return False, None
        except Exception as e:
            print(f"Erro na requisição: {e}")
            return False, None

    def get_user_info(
        self, provider: str, access_token: str
    ) -> Tuple[bool, Optional[Dict]]:
        """Obtém informações do usuário"""
        provider_config = self.config.get_provider_config(provider)

        if not provider_config:
            return False, None

        try:
            headers = {"Authorization": f"Bearer {access_token}"}

            # Twitch precisa do Client-ID
            if provider == "twitch":
                headers["Client-Id"] = provider_config["client_id"]

            response = requests.get(provider_config["user_info_uri"], headers=headers)

            if response.status_code == 200:
                user_data = response.json()

                # Normalizar dados por provedor
                return True, self._normalize_user_data(provider, user_data)
            else:
                print(f"Erro ao obter user info: {response.text}")
                return False, None
        except Exception as e:
            print(f"Erro na requisição: {e}")
            return False, None

    def _normalize_user_data(self, provider: str, data: Dict) -> Dict:
        """Normaliza dados do usuário de diferentes provedores"""

        if provider == "google":
            return {
                "id": data.get("id"),
                "email": data.get("email"),
                "name": data.get("name"),
                "picture": data.get("picture"),
                "provider": "google",
            }

        elif provider == "twitch":
            user = data.get("data", [{}])[0]
            return {
                "id": user.get("id"),
                "email": user.get("email"),
                "name": user.get("display_name"),
                "username": user.get("login"),
                "picture": user.get("profile_image_url"),
                "provider": "twitch",
            }

        elif provider == "github":
            return {
                "id": str(data.get("id")),
                "email": data.get("email"),
                "name": data.get("name") or data.get("login"),
                "username": data.get("login"),
                "picture": data.get("avatar_url"),
                "provider": "github",
            }

        elif provider == "discord":
            return {
                "id": data.get("id"),
                "email": data.get("email"),
                "name": data.get("username"),
                "discriminator": data.get("discriminator"),
                "picture": (
                    f"https://cdn.discordapp.com/avatars/{data.get('id')}/{data.get('avatar')}.png"
                    if data.get("avatar")
                    else None
                ),
                "provider": "discord",
            }

        return data


# ===== TUTORIAIS PARA CADA PROVEDOR =====

OAUTH_TUTORIALS = {
    "google": {
        "title": "Como configurar Google OAuth",
        "steps": [
            "1. Acesse o Google Cloud Console: https://console.cloud.google.com",
            "2. Crie um novo projeto ou selecione um existente",
            "3. Vá em 'APIs & Services' > 'Credentials'",
            "4. Clique em 'Create Credentials' > 'OAuth client ID'",
            "5. Escolha 'Web application'",
            "6. Adicione o Redirect URI: http://127.0.0.1:5000/auth/google/callback",
            "7. Copie o Client ID e Client Secret",
        ],
        "redirect_uri": "http://127.0.0.1:5000/auth/google/callback",
        "docs": "https://developers.google.com/identity/protocols/oauth2",
    },
    "twitch": {
        "title": "Como configurar Twitch OAuth",
        "steps": [
            "1. Acesse: https://dev.twitch.tv/console/apps",
            "2. Clique em 'Register Your Application'",
            "3. Preencha o nome da aplicação",
            "4. Adicione o OAuth Redirect URL: http://127.0.0.1:5000/auth/twitch/callback",
            "5. Escolha categoria: 'Application Integration'",
            "6. Clique em 'Create'",
            "7. Copie o Client ID",
            "8. Clique em 'New Secret' para gerar o Client Secret",
        ],
        "redirect_uri": "http://127.0.0.1:5000/auth/twitch/callback",
        "docs": "https://dev.twitch.tv/docs/authentication",
    },
    "github": {
        "title": "Como configurar GitHub OAuth",
        "steps": [
            "1. Acesse: https://github.com/settings/developers",
            "2. Clique em 'OAuth Apps' > 'New OAuth App'",
            "3. Preencha:",
            "   - Application name: Twitch Bot Dashboard",
            "   - Homepage URL: http://127.0.0.1:5000",
            "   - Authorization callback URL: http://127.0.0.1:5000/auth/github/callback",
            "4. Clique em 'Register application'",
            "5. Copie o Client ID",
            "6. Clique em 'Generate a new client secret'",
            "7. Copie o Client Secret (só aparece uma vez!)",
        ],
        "redirect_uri": "http://127.0.0.1:5000/auth/github/callback",
        "docs": "https://docs.github.com/en/developers/apps/building-oauth-apps",
    },
    "discord": {
        "title": "Como configurar Discord OAuth",
        "steps": [
            "1. Acesse: https://discord.com/developers/applications",
            "2. Clique em 'New Application'",
            "3. Dê um nome (ex: Twitch Bot Dashboard)",
            "4. Vá na aba 'OAuth2'",
            "5. Adicione Redirect: http://127.0.0.1:5000/auth/discord/callback",
            "6. Copie o Client ID",
            "7. Clique em 'Reset Secret' para ver o Client Secret",
            "8. Copie o Client Secret",
        ],
        "redirect_uri": "http://127.0.0.1:5000/auth/discord/callback",
        "docs": "https://discord.com/developers/docs/topics/oauth2",
    },
}
