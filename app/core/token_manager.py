"""
Gerenciador de tokens OAuth da Twitch com renovação automática
Corrigido para carregar o token de /data/bot_oauth.json
"""

import json
import os
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    requests = None


class TokenManager:
    """Gerencia tokens OAuth com renovação automática"""

    def __init__(self, client_id="", client_secret="", refresh_token="", access_token=""):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.token_expiry = None

        # Caminhos de arquivos
        core_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(core_dir, "../../"))

        self.data_dir = os.path.join(core_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.token_file = os.path.join(self.data_dir, "token_data.json")
        self.legacy_oauth_file = os.path.join(root_dir, "data/bot_oauth.json")

        # Carregar token
        self.load_token()

    # =============================================================
    #  CARREGAR TOKEN DE AMBOS OS ARQUIVOS (PRIORIDADE LEGADO)
    # =============================================================
    def load_token(self):
        """Carrega token do bot_oauth.json (legado) ou token_data.json"""

        # 1️⃣ Verificar arquivo legado primeiro: /data/bot_oauth.json
        if os.path.exists(self.legacy_oauth_file):
            print("📥 Carregando token de bot_oauth.json (arquivo legado)...")

            try:
                with open(self.legacy_oauth_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Popular campos

                self.client_id = data.get("client_id", self.client_id)
                self.client_secret = data.get("client_secret", self.client_secret)
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
               
                print("🔄 Renovando token inicial...")

                self.refresh_access_token()

                print("⬆ Migrando token para token_data.json...")
                self.save_token()

                return True
            except Exception as e:
                print(f"❌ Erro ao carregar bot_oauth.json: {e}")

        # 2️⃣ Segundo: token_data.json padrão
        if os.path.exists(self.token_file):
            print("📥 Carregando token de token_data.json...")

            try:
                with open(self.token_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token", self.refresh_token)

                expiry_str = data.get("expiry")
                if expiry_str:
                    try:
                        self.token_expiry = datetime.fromisoformat(expiry_str)
                    except:
                        self.token_expiry = None

                # Se ainda estiver válido
                if self.token_expiry and datetime.now() < self.token_expiry:
                    print("✅ Token válido carregado")
                    return True

                # Senão tenta renovar
                print("⚠️ Token expirado ou sem expiry, renovando...")
                return self.refresh_access_token()

            except Exception as e:
                print(f"❌ Erro ao carregar token_data.json: {e}")

        # 3️⃣ Nenhum token encontrado
        print("⚠️ Nenhum token encontrado.")
        return False

    # =============================================================
    # SALVAR TOKEN PADRONIZADO
    # =============================================================
    def save_token(self):
        """Salva token no arquivo padrão token_data.json"""
        try:
            data = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expiry": self.token_expiry.isoformat() if self.token_expiry else None,
            }

            with open(self.token_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            print("💾 Token salvo com sucesso em token_data.json")

        except Exception as e:
            print(f"❌ Erro ao salvar token: {e}")

    # =============================================================
    #   REFRESH TOKEN USANDO API EXTERNA + FALLBACK TWITCH
    # =============================================================
    def refresh_access_token(self):
        """Renova o Access Token usando API externa + fallback oficial."""
        if requests is None:
            print("❌ Biblioteca 'requests' não disponível")
            return False

        if not self.refresh_token:
            print("⚠️ Nenhum Refresh Token disponível")
            return False

        # ---------- 1️⃣ API externa ----------
        print("🔄 Renovando Token via twitchtokengenerator.com...")

        try:
            url = f"https://twitchtokengenerator.com/api/refresh/{self.refresh_token}"
            response = requests.get(url, timeout=15)
            
            print(f"🔍 Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                
                print(f"🔍 JSON recebido: {data}")
            
                if not data.get("success"):
                    print("❌ API retornou success=false")
                    return False
                
                self.access_token = data.get("token")  # ← Era "access_token", agora é "token"
                self.refresh_token = data.get("refresh") or self.refresh_token  # ← Era "refresh_token", agora é "refresh"
                expires_in = data.get("expires_in", 14400)
                
                
                if not self.access_token:
                    print("❌ Token não foi obtido da API")
                    return False
                    
                print(f"✅ access_token obtido: {self.access_token[:20]}...")
                print(f"✅ refresh_token obtido: {self.refresh_token[:20]}...")
        

                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                self.save_token()
                print("✅ Token renovado pela API externa")
                return True
            else:
                print(f"⚠️ API externa falhou: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Erro API externa: {e}")
            import traceback
            traceback.print_exc()

        # ---------- 2️⃣ Fallback Twitch ----------
        print("🔁 Tentando renovar via API oficial da Twitch...")

        try:
            url = "https://id.twitch.tv/oauth2/token"
            params = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            }

            response = requests.post(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()

                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token", self.refresh_token)

                expires_in = data.get("expires_in", 14400)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

                self.save_token()
                print("✅ Token renovado pela API Twitch")
                return True

            print(f"❌ Erro Twitch: {response.status_code}")
            print(response.json())
        except Exception as e:
            print(f"❌ Erro no fallback Twitch: {e}")

        return False

    # =============================================================
    #   GET VALID TOKEN (NORMAL)
    # =============================================================
    def get_valid_token(self):
        """Retorna token válido, renovando se necessário"""

        if not self.access_token:
            print("⚠️ Sem Access Token, tentando renovar...")
            if not self.refresh_access_token():
                return None

        # Sem data de expiração -> validar
        if not self.token_expiry:
            if not self.validate_token():
                print("⚠️ Token inválido, tentando renovar...")
                if not self.refresh_access_token():
                    return None

        # Renova preventivamente
        if datetime.now() >= self.token_expiry - timedelta(minutes=5):
            print("⏰ Token perto de expirar, renovando...")
            self.refresh_access_token()

        return self.access_token

    # =============================================================
    #   VALIDAR TOKEN
    # =============================================================
    def validate_token(self):
        """Valida o token atual usando a API oficial da Twitch"""

        if requests is None or not self.access_token:
            return False

        url = "https://id.twitch.tv/oauth2/validate"
        headers = {"Authorization": f"OAuth {self.access_token}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                expires_in = data.get("expires_in", 0)

                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                self.save_token()

                print(f"✅ Token válido (expira em {expires_in}s)")
                return True

            print(f"❌ Token inválido: {response.status_code}")
            return False

        except Exception as e:
            print(f"❌ Erro ao validar token: {e}")
            return False
