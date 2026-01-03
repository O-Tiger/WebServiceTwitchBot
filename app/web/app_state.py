from app.core.bot_manager import BotManager
from app.core.streamer_manager import StreamerManager
from app.core.token_manager import TokenManager
from app.integrations.integrations_manager import IntegrationManager
import json, os

bot_manager = BotManager()
streamer_manager = StreamerManager()
integration_manager = IntegrationManager()

def load_token_manager():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    oauth_file = os.path.join(script_dir, "../../data/bot_oauth.json")

    print(f"🔍 Procurando arquivo OAuth em: {oauth_file}")  # Debug
    
    if not os.path.exists(oauth_file):
        print("❌ Arquivo bot_oauth.json NÃO encontrado!")
        return None
    
    try:
        with open(oauth_file, "r") as f:
            oauth = json.load(f)
        
        client_id = oauth.get("client_id", "")
        client_secret = oauth.get("client_secret", "")
        refresh_token = oauth.get("refresh_token", "")
        access_token = oauth.get("access_token","")
       
               
        if not client_id or not client_secret or not refresh_token:
            print("⚠️ Dados OAuth incompletos no arquivo!")
            return None
        
        return TokenManager(client_id, client_secret, refresh_token, access_token)
        
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao ler JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return None


token_manager = load_token_manager()

if token_manager:
    print("✅ TokenManager inicializado com sucesso")
else:
    print("❌ TokenManager NÃO foi inicializado - bot não poderá conectar!")