"""
Modelos do Banco de Dados SQLite
Definição das tabelas e estrutura
"""

import sqlite3
from datetime import datetime
from typing import Optional
from pathlib import Path


class Database:
    """Classe base para gerenciamento de banco de dados"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Garante que o diretório do banco existe"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Retorna uma conexão com o banco de dados"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
        return conn
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Executa uma query e retorna o cursor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return cursor
    
    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Executa query e retorna uma linha"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result
    
    def fetchall(self, query: str, params: tuple = ()) -> list:
        """Executa query e retorna todas as linhas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results


class BotDataDB(Database):
    """Banco de dados para armazenar dados do bot (pontos, mensagens, etc)"""
    
    def __init__(self, db_path: str = "database/bot_data.db"):
        super().__init__(db_path)
        self.create_tables()
    
    def create_tables(self):
        """Cria as tabelas necessárias"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de canais
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de pontos (relacionamento usuário-canal)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                points INTEGER DEFAULT 0,
                messages INTEGER DEFAULT 0,
                last_message_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
                UNIQUE(user_id, channel_id)
            )
        """)
        
        # Tabela de auto-respostas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auto_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                trigger TEXT NOT NULL,
                response TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                use_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE
            )
        """)
        
        # Tabela de raids
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                raider_name TEXT NOT NULL,
                viewers INTEGER NOT NULL,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE
            )
        """)
        
        # Índices para performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_points_user 
            ON user_points(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_points_channel 
            ON user_points(channel_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_auto_responses_trigger 
            ON auto_responses(trigger)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_raids_channel 
            ON raids(channel_id)
        """)
        
        conn.commit()
        conn.close()


class LogsDB(Database):
    """Banco de dados para logs do sistema"""
    
    def __init__(self, db_path: str = "logs/logs.db"):
        super().__init__(db_path)
        self.create_tables()
    
    def create_tables(self):
        """Cria as tabelas de logs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de logs do sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                channel TEXT,
                username TEXT,
                extra_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de mensagens do chat (histórico completo)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL,
                username TEXT NOT NULL,
                message TEXT NOT NULL,
                points_at_time INTEGER DEFAULT 0,
                messages_at_time INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de eventos especiais
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                channel TEXT NOT NULL,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Índices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_logs_level 
            ON system_logs(level)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_logs_created 
            ON system_logs(created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_messages_channel 
            ON chat_messages(channel)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_messages_created 
            ON chat_messages(created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_type 
            ON events(event_type)
        """)
        
        conn.commit()
        conn.close()


# ===== FUNÇÕES AUXILIARES =====

def init_databases():
    """Inicializa todos os bancos de dados"""
    print("🔧 Inicializando bancos de dados...")
    
    bot_db = BotDataDB()
    print("✅ Banco de dados do bot criado")
    
    logs_db = LogsDB()
    print("✅ Banco de dados de logs criado")
    
    return bot_db, logs_db


def migrate_json_to_db():
    """Migra dados dos arquivos JSON antigos para SQLite"""
    import json
    import os
    
    print("📦 Iniciando migração de dados JSON para SQLite...")
    
    bot_db = BotDataDB()
    
    # Migrar bot_data.json
    bot_data_file = "data/bot_data.json"
    if os.path.exists(bot_data_file):
        try:
            with open(bot_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Migrar dados por canal
            for channel_name, channel_data in data.items():
                # Criar canal
                from crud import ChannelCRUD
                channel_crud = ChannelCRUD()
                channel_id = channel_crud.get_or_create(channel_name)
                
                # Migrar pontos
                user_points = channel_data.get('user_points', {})
                message_count = channel_data.get('message_count', {})
                
                from crud import UserPointsCRUD
                points_crud = UserPointsCRUD()
                
                for username, points in user_points.items():
                    messages = message_count.get(username, 0)
                    points_crud.update_user(
                        username=username,
                        channel_name=channel_name,
                        points=points,
                        messages=messages
                    )
            
            print(f"✅ Dados de {bot_data_file} migrados com sucesso")
            
            # Fazer backup do arquivo antigo
            backup_file = bot_data_file + ".backup"
            os.rename(bot_data_file, backup_file)
            print(f"📦 Backup criado: {backup_file}")
            
        except Exception as e:
            print(f"❌ Erro ao migrar {bot_data_file}: {e}")
    
    # Migrar auto_responses.json
    auto_resp_file = "data/auto_responses.json"
    if os.path.exists(auto_resp_file):
        try:
            with open(auto_resp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            responses = data.get('responses', {})
            
            from crud import AutoResponseCRUD
            response_crud = AutoResponseCRUD()
            
            for trigger, response in responses.items():
                response_crud.create(
                    trigger=trigger,
                    response=response,
                    channel_id=None  # Global
                )
            
            print(f"✅ Auto-respostas de {auto_resp_file} migradas com sucesso")
            
            # Fazer backup
            backup_file = auto_resp_file + ".backup"
            os.rename(auto_resp_file, backup_file)
            print(f"📦 Backup criado: {backup_file}")
            
        except Exception as e:
            print(f"❌ Erro ao migrar {auto_resp_file}: {e}")
    
    print("✅ Migração concluída!")


if __name__ == "__main__":
    # Testar criação dos bancos
    init_databases()
    print("\n✅ Bancos de dados criados com sucesso!")
    print("\n📊 Estrutura:")
    print("  - database/bot_data.db")
    print("    ├── users")
    print("    ├── channels")
    print("    ├── user_points")
    print("    ├── auto_responses")
    print("    └── raids")
    print("\n  - logs/logs.db")
    print("    ├── system_logs")
    print("    ├── chat_messages")
    print("    └── events")