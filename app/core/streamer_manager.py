"""
Gerenciador de lista de streamers favoritos
Salva e gerencia streamers em banco de dados SQLite
"""

import os


class StreamerManager:
    """Gerencia lista de streamers salvos"""

    def __init__(self):
        from app.database.crud import BotDatabase

        self.db = BotDatabase()

    def load_streamers(self):
        """Carrega lista de streamers do banco de dados"""
        try:
            streamers = self.db.streamers.get_all(enabled_only=False)
            print(f"✅ {len(streamers)} streamers carregados do banco de dados")
            return streamers
        except Exception as e:
            print(f"❌ Erro ao carregar streamers: {e}")
            return []

    def add_streamer(self, username, display_name=None):
        """Adiciona streamer à lista"""
        username = username.lstrip("@").strip().lower()

        if not username:
            return False, "Nome de usuário inválido"

        if self.db.streamers.exists(username):
            return False, "Streamer já existe na lista"

        try:
            self.db.streamers.create(
                username=username,
                display_name=display_name or username,
                auto_connect=False,
            )
            return True, f"Streamer {username} adicionado com sucesso"
        except Exception as e:
            return False, f"Erro ao adicionar streamer: {e}"

    def remove_streamer(self, username):
        """Remove streamer da lista"""
        username = username.lstrip("@").strip().lower()

        try:
            if self.db.streamers.delete(username):
                return True, f"Streamer {username} removido com sucesso"
            else:
                return False, "Streamer não encontrado"
        except Exception as e:
            return False, f"Erro ao remover streamer: {e}"

    def get_streamers(self):
        """Retorna lista completa de streamers"""
        return self.load_streamers()

    def get_streamer_names(self):
        """Retorna apenas os usernames"""
        streamers = self.get_streamers()
        return [s["username"] for s in streamers]

    def get_display_names(self):
        """Retorna lista de nomes de exibição"""
        streamers = self.get_streamers()
        return [s["display_name"] for s in streamers]

    def clear_all(self):
        """Remove todos os streamers"""
        try:
            streamers = self.get_streamers()
            for streamer in streamers:
                self.db.streamers.delete(streamer["username"])
            return True, "Todos os streamers foram removidos"
        except Exception as e:
            return False, f"Erro ao limpar streamers: {e}"

    def streamer_exists(self, username):
        """Verifica se streamer existe na lista"""
        username = username.lstrip("@").strip().lower()
        return self.db.streamers.exists(username)
