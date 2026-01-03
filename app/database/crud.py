"""
Sistema CRUD Completo para Twitch Bot Dashboard
Operações de banco de dados usando SQLite
Localização: app/database/crud.py
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import os

# Models are now defined inline in this file
# No need to import from models.py since we use direct SQL queries


class DatabaseManager:
    """Gerenciador central do banco de dados"""

    def __init__(self, db_path: str = "database/bot_data.db"):
        self.db_path = db_path
        self._ensure_directory()
        self._initialize_db()

    def _ensure_directory(self):
        """Garante que o diretório existe"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Context manager para conexões thread-safe"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Retorna dicts
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _initialize_db(self):
        """Inicializa todas as tabelas"""
        from app.database.models import create_tables

        with self.get_connection() as conn:
            create_tables(conn)


# ===== USERS CRUD =====


class UserCRUD:
    """Operações CRUD para usuários"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(
        self, username: str, channel: str, points: int = 0, message_count: int = 0
    ) -> int:
        """Cria novo usuário"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO users (username, channel, points, message_count)
                   VALUES (?, ?, ?, ?)""",
                (username, channel, points, message_count),
            )
            return cursor.lastrowid

    def get(self, user_id: int) -> Optional[Dict]:
        """Busca usuário por ID"""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_by_username(self, username: str, channel: str) -> Optional[Dict]:
        """Busca usuário por username e canal"""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? AND channel = ?",
                (username, channel),
            ).fetchone()
            return dict(row) if row else None

    def get_or_create(self, username: str, channel: str) -> Dict:
        """Busca ou cria usuário"""
        user = self.get_by_username(username, channel)
        if not user:
            user_id = self.create(username, channel)
            user = self.get(user_id)
        return user

    def update_points(self, username: str, channel: str, points: int) -> bool:
        """Atualiza pontos do usuário"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """UPDATE users SET points = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE username = ? AND channel = ?""",
                (points, username, channel),
            )
            return cursor.rowcount > 0

    def add_points(self, username: str, channel: str, points: int) -> int:
        """Adiciona pontos ao usuário"""
        user = self.get_or_create(username, channel)
        new_points = user["points"] + points
        self.update_points(username, channel, new_points)
        return new_points

    def increment_messages(self, username: str, channel: str) -> int:
        """Incrementa contador de mensagens"""
        with self.db.get_connection() as conn:
            conn.execute(
                """UPDATE users 
                   SET message_count = message_count + 1,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE username = ? AND channel = ?""",
                (username, channel),
            )

            row = conn.execute(
                "SELECT message_count FROM users WHERE username = ? AND channel = ?",
                (username, channel),
            ).fetchone()
            return row["message_count"] if row else 0

    def get_top_users(
        self, channel: str, limit: int = 10, order_by: str = "points"
    ) -> List[Dict]:
        """Retorna top usuários por pontos ou mensagens"""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                f"""SELECT * FROM users 
                    WHERE channel = ?
                    ORDER BY {order_by} DESC
                    LIMIT ?""",
                (channel, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_all_by_channel(self, channel: str) -> List[Dict]:
        """Retorna todos usuários de um canal"""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM users WHERE channel = ?", (channel,)
            ).fetchall()
            return [dict(row) for row in rows]

    def delete(self, user_id: int) -> bool:
        """Deleta usuário"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            return cursor.rowcount > 0

    def get_stats(self, channel: str) -> Dict:
        """Retorna estatísticas agregadas do canal"""
        with self.db.get_connection() as conn:
            row = conn.execute(
                """SELECT 
                    COUNT(*) as total_users,
                    SUM(points) as total_points,
                    SUM(message_count) as total_messages,
                    AVG(points) as avg_points
                   FROM users WHERE channel = ?""",
                (channel,),
            ).fetchone()
            return dict(row) if row else {}


# ===== MESSAGES CRUD =====


class MessageCRUD:
    """Operações CRUD para mensagens"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(
        self, username: str, channel: str, message: str, user_id: Optional[int] = None
    ) -> int:
        """Cria nova mensagem"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO messages (username, channel, message, user_id)
                   VALUES (?, ?, ?, ?)""",
                (username, channel, message, user_id),
            )
            return cursor.lastrowid

    def get_recent(self, channel: str, limit: int = 100) -> List[Dict]:
        """Retorna mensagens recentes de um canal"""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM messages 
                   WHERE channel = ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (channel, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_by_user(self, username: str, channel: str, limit: int = 50) -> List[Dict]:
        """Retorna mensagens de um usuário específico"""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM messages 
                   WHERE username = ? AND channel = ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (username, channel, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def count_by_channel(self, channel: str) -> int:
        """Conta mensagens do canal"""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as count FROM messages WHERE channel = ?", (channel,)
            ).fetchone()
            return row["count"] if row else 0

    def delete_old_messages(self, days: int = 30) -> int:
        """Deleta mensagens antigas"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """DELETE FROM messages 
                   WHERE timestamp < datetime('now', '-' || ? || ' days')""",
                (days,),
            )
            return cursor.rowcount


# ===== AUTO RESPONSES CRUD =====


class AutoResponseCRUD:
    """Operações CRUD para auto respostas"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(
        self,
        trigger: str,
        response: str,
        channel: Optional[str] = None,
        enabled: bool = True,
    ) -> int:
        """Cria nova auto resposta"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO auto_responses (trigger, response, channel, enabled)
                   VALUES (?, ?, ?, ?)""",
                (trigger, response, channel, enabled),
            )
            return cursor.lastrowid

    def get(self, response_id: int) -> Optional[Dict]:
        """Busca auto resposta por ID"""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM auto_responses WHERE id = ?", (response_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_by_trigger(
        self, trigger: str, channel: Optional[str] = None
    ) -> Optional[Dict]:
        """Busca auto resposta por trigger"""
        with self.db.get_connection() as conn:
            if channel:
                row = conn.execute(
                    """SELECT * FROM auto_responses 
                       WHERE trigger = ? AND (channel = ? OR channel IS NULL)
                       AND enabled = 1
                       ORDER BY channel DESC LIMIT 1""",
                    (trigger, channel),
                ).fetchone()
            else:
                row = conn.execute(
                    """SELECT * FROM auto_responses 
                       WHERE trigger = ? AND channel IS NULL AND enabled = 1""",
                    (trigger,),
                ).fetchone()
            return dict(row) if row else None

    def get_all(
        self, channel: Optional[str] = None, enabled_only: bool = True
    ) -> List[Dict]:
        """Retorna todas auto respostas"""
        with self.db.get_connection() as conn:
            if channel:
                query = """SELECT * FROM auto_responses 
                          WHERE (channel = ? OR channel IS NULL)"""
                params = [channel]
            else:
                query = "SELECT * FROM auto_responses WHERE channel IS NULL"
                params = []

            if enabled_only:
                query += " AND enabled = 1"

            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def update(
        self, response_id: int, response: str = None, enabled: bool = None
    ) -> bool:
        """Atualiza auto resposta"""
        updates = []
        params = []

        if response is not None:
            updates.append("response = ?")
            params.append(response)

        if enabled is not None:
            updates.append("enabled = ?")
            params.append(enabled)

        if not updates:
            return False

        params.append(response_id)

        with self.db.get_connection() as conn:
            cursor = conn.execute(
                f"""UPDATE auto_responses 
                    SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                params,
            )
            return cursor.rowcount > 0

    def delete(self, response_id: int) -> bool:
        """Deleta auto resposta"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM auto_responses WHERE id = ?", (response_id,)
            )
            return cursor.rowcount > 0

    def delete_by_trigger(self, trigger: str, channel: Optional[str] = None) -> bool:
        """Deleta auto resposta por trigger"""
        with self.db.get_connection() as conn:
            if channel:
                cursor = conn.execute(
                    "DELETE FROM auto_responses WHERE trigger = ? AND channel = ?",
                    (trigger, channel),
                )
            else:
                cursor = conn.execute(
                    "DELETE FROM auto_responses WHERE trigger = ? AND channel IS NULL",
                    (trigger,),
                )
            return cursor.rowcount > 0


# ===== CLASSE PRINCIPAL =====


class BotDatabase:
    """Interface principal para todas operações de banco de dados"""

    def __init__(self, db_path: str = "database/bot_data.db"):
        self.manager = DatabaseManager(db_path)

        # Inicializar CRUDs
        self.users = UserCRUD(self.manager)
        self.messages = MessageCRUD(self.manager)
        self.auto_responses = AutoResponseCRUD(self.manager)
        self.streamers = StreamersCRUD(self.manager)
        self.oauth_config = OAuthConfigCRUD(self.manager)
        self.oauth_tokens = OAuthTokensCRUD(self.manager)

    def close(self):
        """Fecha conexões (se necessário)"""
        pass  # SQLite fecha automaticamente via context manager


# ===== STREAMERS CRUD =====


class StreamersCRUD:
    """Operações CRUD para streamers favoritos"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(
        self,
        username: str,
        display_name: str = None,
        auto_connect: bool = False,
        enabled: bool = True,
    ) -> int:
        """Cria novo streamer"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO streamers (username, display_name, auto_connect, enabled)
                   VALUES (?, ?, ?, ?)""",
                (username, display_name or username, auto_connect, enabled),
            )
            return cursor.lastrowid

    def get(self, streamer_id: int) -> Optional[Dict]:
        """Busca streamer por ID"""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM streamers WHERE id = ?", (streamer_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_by_username(self, username: str) -> Optional[Dict]:
        """Busca streamer por username"""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM streamers WHERE username = ?", (username,)
            ).fetchone()
            return dict(row) if row else None

    def get_all(self, enabled_only: bool = True) -> List[Dict]:
        """Retorna todos os streamers"""
        with self.db.get_connection() as conn:
            query = "SELECT * FROM streamers"
            if enabled_only:
                query += " WHERE enabled = 1"
            query += " ORDER BY display_name"
            rows = conn.execute(query).fetchall()
            return [dict(row) for row in rows]

    def update(self, streamer_id: int, **kwargs) -> bool:
        """Atualiza streamer"""
        allowed_fields = ["display_name", "auto_connect", "enabled"]
        updates = []
        params = []

        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                params.append(value)

        if not updates:
            return False

        params.append(streamer_id)

        with self.db.get_connection() as conn:
            cursor = conn.execute(
                f"""UPDATE streamers
                    SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                params,
            )
            return cursor.rowcount > 0

    def delete(self, username: str) -> bool:
        """Deleta streamer por username"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM streamers WHERE username = ?", (username,)
            )
            return cursor.rowcount > 0

    def delete_by_id(self, streamer_id: int) -> bool:
        """Deleta streamer por ID"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM streamers WHERE id = ?", (streamer_id,))
            return cursor.rowcount > 0

    def exists(self, username: str) -> bool:
        """Verifica se streamer existe"""
        return self.get_by_username(username) is not None


# ===== OAUTH CONFIG CRUD =====


class OAuthConfigCRUD:
    """Operações CRUD para configuração OAuth"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def set_config(
        self,
        provider: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        auth_uri: str = None,
        token_uri: str = None,
        user_info_uri: str = None,
        scopes: str = None,
    ) -> int:
        """Salva ou atualiza configuração de um provedor"""
        with self.db.get_connection() as conn:
            # Verificar se existe
            existing = conn.execute(
                "SELECT id FROM oauth_config WHERE provider = ?", (provider,)
            ).fetchone()

            if existing:
                cursor = conn.execute(
                    """UPDATE oauth_config 
                       SET client_id = ?, client_secret = ?, redirect_uri = ?,
                           auth_uri = ?, token_uri = ?, user_info_uri = ?, 
                           scopes = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE provider = ?""",
                    (
                        client_id,
                        client_secret,
                        redirect_uri,
                        auth_uri,
                        token_uri,
                        user_info_uri,
                        scopes,
                        provider,
                    ),
                )
                return existing["id"]
            else:
                cursor = conn.execute(
                    """INSERT INTO oauth_config 
                       (provider, client_id, client_secret, redirect_uri,
                        auth_uri, token_uri, user_info_uri, scopes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        provider,
                        client_id,
                        client_secret,
                        redirect_uri,
                        auth_uri,
                        token_uri,
                        user_info_uri,
                        scopes,
                    ),
                )
                return cursor.lastrowid

    def get_config(self, provider: str):
        """Busca configuração de um provedor"""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM oauth_config WHERE provider = ?", (provider,)
            ).fetchone()
            return dict(row) if row else None

    def get_all_configs(self):
        """Retorna todas as configurações"""
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM oauth_config").fetchall()
            return [dict(row) for row in rows]

    def is_configured(self, provider: str) -> bool:
        """Verifica se provedor está configurado"""
        config = self.get_config(provider)
        return config and bool(config.get("client_id") and config.get("client_secret"))


# ===== OAUTH TOKENS CRUD =====


class OAuthTokensCRUD:
    """Operações CRUD para tokens OAuth"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def save_token(
        self,
        provider: str,
        user_id: str,
        access_token: str,
        refresh_token: str = None,
        expires_at: str = None,
        scope: str = None,
    ) -> int:
        """Salva token OAuth"""
        with self.db.get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM oauth_tokens WHERE provider = ? AND user_id = ?",
                (provider, user_id),
            ).fetchone()

            if existing:
                cursor = conn.execute(
                    """UPDATE oauth_tokens 
                       SET access_token = ?, refresh_token = ?, expires_at = ?,
                           scope = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE provider = ? AND user_id = ?""",
                    (access_token, refresh_token, expires_at, scope, provider, user_id),
                )
                return existing["id"]
            else:
                cursor = conn.execute(
                    """INSERT INTO oauth_tokens
                       (provider, user_id, access_token, refresh_token, expires_at, scope)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (provider, user_id, access_token, refresh_token, expires_at, scope),
                )
                return cursor.lastrowid

    def get_token(self, provider: str, user_id: str):
        """Busca token OAuth"""
        with self.db.get_connection() as conn:
            row = conn.execute(
                """SELECT * FROM oauth_tokens 
                   WHERE provider = ? AND user_id = ?""",
                (provider, user_id),
            ).fetchone()
            return dict(row) if row else None

    def delete_token(self, provider: str, user_id: str) -> bool:
        """Deleta token OAuth"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """DELETE FROM oauth_tokens 
                   WHERE provider = ? AND user_id = ?""",
                (provider, user_id),
            )
            return cursor.rowcount > 0
