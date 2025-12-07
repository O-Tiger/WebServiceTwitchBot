import json
import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

try:
    import requests
except Exception:
    requests = None


class OAuthHandler(BaseHTTPRequestHandler):
    """Handler para receber o callback OAuth"""

    auth_code = None

    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)

        if "code" in params:
            OAuthHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            html = """<!DOCTYPE html>
<html><head><title>Autenticação Concluída</title>
<style>body{font-family:'Segoe UI',Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.container{background:#fff;padding:40px;border-radius:15px;box-shadow:0 10px 40px rgba(0,0,0,0.3);
text-align:center;max-width:500px}h1{color:#6441a5;margin-bottom:20px}
.success{font-size:60px;margin-bottom:20px}p{color:#555;font-size:16px;line-height:1.6}
.info{background:#f0f0f0;padding:15px;border-radius:8px;margin-top:20px}</style></head>
<body><div class="container"><div class="success">✅</div>
<h1>Autenticação Concluída!</h1><p>Você pode fechar esta janela e voltar para o bot.</p>
<div class="info"><strong>O bot está configurando seus tokens automaticamente...</strong></div>
</div><script>setTimeout(function(){window.close()},3000);</script></body></html>"""
            self.wfile.write(html.encode())
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Erro na autenticacao</h1>")

    def log_message(self, format, *args):
        pass


class TwitchOAuthManager:
    """Gerenciador de autenticação OAuth da Twitch"""

    def __init__(self, client_id, client_secret, redirect_uri="http://localhost:3000"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = ["chat:read", "chat:edit", "channel:moderate"]
        self.server = None

    def start_oauth_flow(self):
        if not requests:
            print("❌ Biblioteca 'requests' não disponível")
            return None, None

        print("\n🔐 Iniciando autenticação OAuth...")
        auth_url = self._build_auth_url()

        print("🌐 Iniciando servidor local na porta 3000...")
        if not self._start_local_server():
            return None, None

        print("🌍 Abrindo navegador...")
        webbrowser.open(auth_url)
        print("⏳ Aguardando autorização...\n")

        auth_code = self._wait_for_code()
        if self.server:
            self.server.shutdown()

        if not auth_code:
            print("❌ Código não recebido")
            return None, None

        print("✅ Código recebido!")
        print("🔄 Trocando por tokens...")
        return self._exchange_code_for_tokens(auth_code)

    def _build_auth_url(self):
        scopes_str = "+".join(self.scopes)
        return (
            f"https://id.twitch.tv/oauth2/authorize?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}&response_type=code&scope={scopes_str}"
        )

    def _start_local_server(self):
        try:
            self.server = HTTPServer(("localhost", 3000), OAuthHandler)
            thread = threading.Thread(target=self.server.serve_forever)
            thread.daemon = True
            thread.start()
            return True
        except Exception as e:
            print(f"Erro ao iniciar servidor: {e}")
            return False

    def _wait_for_code(self, timeout=120):
        import time

        OAuthHandler.auth_code = None
        start = time.time()
        while time.time() - start < timeout:
            if OAuthHandler.auth_code:
                return OAuthHandler.auth_code
            time.sleep(0.5)
        return None

    def _exchange_code_for_tokens(self, auth_code):
        url = "https://id.twitch.tv/oauth2/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }

        try:
            response = requests.post(url, data=data, timeout=15)
            if response.status_code == 200:
                tokens = response.json()
                access = tokens.get("access_token")
                refresh = tokens.get("refresh_token")
                print(f"✅ Tokens obtidos!")
                return access, refresh
            else:
                print(f"❌ Erro: {response.status_code} - {response.text}")
                return None, None
        except Exception as e:
            print(f"❌ Erro: {e}")
            return None, None


def authenticate_with_twitch(gui):
    """Integração com a GUI"""
    from tkinter import messagebox, simpledialog

    if not hasattr(gui, "temp_client_id"):
        client_id = simpledialog.askstring(
            "Client ID", "Digite o Client ID:", parent=gui.window
        )
        if not client_id:
            return False

        client_secret = simpledialog.askstring(
            "Client Secret", "Digite o Client Secret:", parent=gui.window, show="*"
        )
        if not client_secret:
            return False

        gui.temp_client_id = client_id
        gui.temp_client_secret = client_secret

    oauth = TwitchOAuthManager(gui.temp_client_id, gui.temp_client_secret)
    access_token, refresh_token = oauth.start_oauth_flow()

    if access_token and refresh_token:
        from app.core.token_manager import TokenManager

        gui.token_manager = TokenManager(
            gui.temp_client_id, gui.temp_client_secret, refresh_token, access_token
        )

        # Salvar com access_token incluído
        save_config_with_tokens(gui, access_token)

        gui.log("✅", "OAuth concluído!", "success")
        messagebox.showinfo("Sucesso", "Autenticação concluída!\nTokens salvos.")
        return True
    else:
        gui.log("❌", "Falha no OAuth", "error")
        return False


def save_config_with_tokens(gui, access_token):
    """Salva config incluindo access_token"""
    try:
        # Caminho correto: usa script_dir
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        oauth_file = os.path.join(data_dir, "oauth_config.json")
        oauth = {
            "client_id": gui.token_manager.client_id,
            "client_secret": gui.token_manager.client_secret,
            "refresh_token": gui.token_manager.refresh_token,
            "access_token": access_token,  # ← INCLUIR ACCESS TOKEN
        }

        with open(oauth_file, "w", encoding="utf-8") as f:
            json.dump(oauth, f, indent=2)

        print("💾 OAuth salvo com access_token")
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")
