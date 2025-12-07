"""
Gerenciador de tokens OAuth da Twitch com renovação automática
Gerencia access_token, refresh_token e validade
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

    def __init__(self, client_id, client_secret, refresh_token, access_token=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.token_expiry = None

        # Pasta para dados
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(script_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.token_file = os.path.join(self.data_dir, "token_data.json")

        # Tenta carregar token salvo
        self.load_token()

    def load_token(self):
        """Carrega token do arquivo"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token", self.refresh_token)
                    expiry_str = data.get("expiry")

                    if expiry_str:
                        try:
                            self.token_expiry = datetime.fromisoformat(expiry_str)
                        except Exception:
                            self.token_expiry = None

                    # Verificar validade
                    if self.token_expiry and datetime.now() < self.token_expiry:
                        print("✅ Token válido carregado")
                        return True
                    """ else:
                        print("⚠️ Token expirado, renovando...")
                        return self.refresh_access_token() """
            else:
                # Arquivo não existe, tentar gerar
                if self.refresh_token:
                    print("🔐 Gerando novo Access Token...")
                    return self.refresh_access_token()

        except Exception as e:
            print(f"❌ Erro ao carregar token: {e}")
        return False

    def save_token(self):
        """Salva token no arquivo"""
        try:
            data = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expiry": self.token_expiry.isoformat() if self.token_expiry else None,
            }
            with open(self.token_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print("💾 Token salvo com sucesso")
        except Exception as e:
            print(f"❌ Erro ao salvar token: {e}")

    def refresh_access_token(self):
        """Renova o Access Token usando Refresh Token"""
        if requests is None:
            print("❌ Biblioteca 'requests' não disponível")
            return False

        if not self.refresh_token:
            print("⚠️ Nenhum Refresh Token disponível")
            return False

        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        """ try:
            print("🔄 Renovando Access Token...")
            response = requests.post(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")

                # Atualizar refresh_token se retornar novo
                if "refresh_token" in data:
                    self.refresh_token = data.get("refresh_token")

                expires_in = data.get("expires_in", 14400)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

                self.save_token()
                print(f"✅ Token renovado! Expira em: {self.token_expiry}")
                return True
            else:
                print(f"❌ Erro ao renovar token: {response.status_code}")

                # Mensagens específicas de erro
                if response.status_code == 400:
                    print("💡 Possíveis causas:")
                    print("   • Refresh Token expirado ou inválido")
                    print("   • Client ID ou Client Secret incorretos")
                elif response.status_code == 401:
                    print("💡 Credenciais inválidas (Client ID/Secret)")

                try:
                    print(f"Detalhes: {response.json()}")
                except:
                    print(f"Resposta: {response.text}")
                return False 

        except requests.exceptions.Timeout:
            print("❌ Timeout na renovação do token")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ Erro de conexão com a API da Twitch")
            return False
        except Exception as e:
            print(f"❌ Erro na renovação: {e}")
            return False
        """

    def get_valid_token(self):
        """Retorna token válido, renovando se necessário"""
        # Sem access_token, tentar renovar
        if not self.access_token:
            if self.refresh_token:
                print("⚠️ Sem Access Token, tentando renovar...")
                if not self.refresh_access_token():
                    print("❌ Não foi possível obter token válido")
                    return None
            else:
                print("❌ Sem Access Token e sem Refresh Token")
                return None

        # Token sem expiry, validar
        if not self.token_expiry:
            print("⚠️ Token sem data de expiração, validando...")
            if self.validate_token():
                # Válido, assumir 4 horas de validade
                self.token_expiry = datetime.now() + timedelta(hours=4)
                self.save_token()
            else:
                # Inválido, tentar renovar
                if self.refresh_token:
                    print("🔄 Token inválido, renovando...")
                    if not self.refresh_access_token():
                        return None
                else:
                    print("❌ Token inválido e sem Refresh Token")
                    return None

        # Token próximo de expirar (5 min), renovar preventivamente
        elif datetime.now() >= self.token_expiry - timedelta(minutes=5):
            if self.refresh_token:
                print("⚠️ Token próximo de expirar, renovando...")
                self.refresh_access_token()
            else:
                print("⚠️ Token vai expirar em breve")

        return self.access_token

    def validate_token(self):
        """Valida o token atual"""
        if requests is None:
            print("❌ Biblioteca 'requests' não disponível")
            return False

        if not self.access_token:
            return False

        url = "https://id.twitch.tv/oauth2/validate"
        headers = {"Authorization": f"OAuth {self.access_token}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Token válido para: {data.get('login')}")
                expires_in = data.get("expires_in", 0)
                print(f"⏰ Expira em: {expires_in} segundos (~{expires_in//3600}h)")

                # Atualizar expiry
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                self.save_token()

                return True
            else:
                print(f"❌ Token inválido: {response.status_code}")
                if response.status_code == 401:
                    print("💡 O token expirou ou foi revogado")
                return False
        except Exception as e:
            print(f"❌ Erro ao validar: {e}")
            return False
