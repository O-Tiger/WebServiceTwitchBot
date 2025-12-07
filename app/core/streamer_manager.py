"""
Gerenciador de lista de streamers favoritos
Salva e gerencia streamers em arquivo JSON
"""

import json
import os


class StreamerManager:
    """Gerencia lista de streamers salvos"""

    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(script_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.streamers_file = os.path.join(self.data_dir, "streamers.json")
        self.streamers = []
        self.load_streamers()

    def load_streamers(self):
        """Carrega lista de streamers do arquivo"""
        try:
            if os.path.exists(self.streamers_file):
                with open(self.streamers_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.streamers = data.get("streamers", [])
                    print(f"✅ {len(self.streamers)} streamers carregados")
            else:
                # Criar arquivo vazio
                self.save_streamers()
        except Exception as e:
            print(f"❌ Erro ao carregar streamers: {e}")
            self.streamers = []

    def save_streamers(self):
        """Salva lista de streamers no arquivo"""
        try:
            data = {"streamers": self.streamers}
            with open(self.streamers_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("💾 Lista de streamers salva")
        except Exception as e:
            print(f"❌ Erro ao salvar streamers: {e}")

    def add_streamer(self, username, display_name=None):
        """Adiciona streamer à lista"""
        # Limpar e normalizar
        username = username.lstrip("@").strip().lower()

        if not username:
            return False, "Nome de usuário inválido"

        # Verificar duplicata
        if any(s["username"] == username for s in self.streamers):
            return False, "Streamer já existe na lista"

        streamer = {
            "username": username,
            "display_name": display_name or username,
            "added_at": None,
        }

        self.streamers.append(streamer)
        self.save_streamers()
        return True, f"Streamer {username} adicionado com sucesso"

    def remove_streamer(self, username):
        """Remove streamer da lista"""
        username = username.lstrip("@").strip().lower()

        original_len = len(self.streamers)
        self.streamers = [s for s in self.streamers if s["username"] != username]

        if len(self.streamers) < original_len:
            self.save_streamers()
            return True, f"Streamer {username} removido com sucesso"
        else:
            return False, "Streamer não encontrado"

    def get_streamers(self):
        """Retorna lista completa de streamers"""
        return self.streamers

    def get_streamer_names(self):
        """Retorna apenas os usernames"""
        return [s["username"] for s in self.streamers]

    def get_display_names(self):
        """Retorna lista de nomes de exibição"""
        return [s["display_name"] for s in self.streamers]

    def clear_all(self):
        """Remove todos os streamers"""
        self.streamers = []
        self.save_streamers()
        return True, "Todos os streamers foram removidos"

    def streamer_exists(self, username):
        """Verifica se streamer existe na lista"""
        username = username.lstrip("@").strip().lower()
        return any(s["username"] == username for s in self.streamers)
