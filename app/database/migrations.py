"""
Script de Migração: JSON → SQLite
Migra dados de bot_data.json e logs.json para banco de dados SQLite
Localização: app/database/migrations.py

Uso:
    python -m app.database.migrations
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List

# Adicionar root ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.database.crud import BotDatabase


class DataMigration:
    """Gerenciador de migração de dados"""
    
    def __init__(self, data_dir: str = "data", backup: bool = True):
        self.data_dir = data_dir
        self.backup = backup
        self.db = BotDatabase()
        
        # Arquivos fonte
        self.bot_data_file = os.path.join(data_dir, "bot_data.json")
        self.logs_file = os.path.join(data_dir, "logs.json")
        self.auto_responses_file = os.path.join(data_dir, "auto_responses.json")
        self.streamers_file = os.path.join(data_dir, "streamers.json")
    
    def run(self):
        """Executa migração completa"""
        print("=" * 60)
        print("🔄 MIGRAÇÃO DE DADOS: JSON → SQLite")
        print("=" * 60)
        print()
        
        # Backup se solicitado
        if self.backup:
            self._create_backups()
        
        # Migrar cada tipo de dado
        stats = {
            'users': 0,
            'messages': 0,
            'auto_responses': 0,
            'streamers': 0,
            'errors': 0
        }
        
        # 1. Migrar dados de usuários (bot_data.json)
        print("\n📊 Migrando dados de usuários...")
        stats['users'] = self._migrate_bot_data()
        
        # 2. Migrar logs/mensagens (logs.json)
        print("\n💬 Migrando histórico de mensagens...")
        stats['messages'] = self._migrate_logs()
        
        # 3. Migrar auto respostas
        print("\n🤖 Migrando auto respostas...")
        stats['auto_responses'] = self._migrate_auto_responses()
        
        # 4. Migrar streamers
        print("\n📺 Migrando configuração de streamers...")
        stats['streamers'] = self._migrate_streamers()
        
        # Relatório final
        self._print_report(stats)
        
        return stats
    
    def _create_backups(self):
        """Cria backup dos arquivos JSON"""
        print("💾 Criando backups...")
        
        backup_dir = os.path.join(self.data_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        files = [
            self.bot_data_file,
            self.logs_file,
            self.auto_responses_file,
            self.streamers_file
        ]
        
        for file_path in files:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                backup_path = os.path.join(
                    backup_dir, 
                    f"{filename}.{timestamp}.backup"
                )
                
                try:
                    import shutil
                    shutil.copy2(file_path, backup_path)
                    print(f"   ✅ {filename} → {backup_path}")
                except Exception as e:
                    print(f"   ⚠️ Erro ao fazer backup de {filename}: {e}")
    
    def _migrate_bot_data(self) -> int:
        """Migra bot_data.json (pontos e mensagens por usuário)"""
        if not os.path.exists(self.bot_data_file):
            print("   ⚠️ Arquivo bot_data.json não encontrado")
            return 0
        
        try:
            with open(self.bot_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            count = 0
            
            # Estrutura: { "channel": { "username": {"points": X, "messages": Y} } }
            for channel, users in data.items():
                if not isinstance(users, dict):
                    continue
                
                for username, user_data in users.items():
                    if not isinstance(user_data, dict):
                        continue
                    
                    points = user_data.get('points', 0)
                    messages = user_data.get('messages', 0)
                    
                    try:
                        # Criar ou atualizar usuário
                        user = self.db.users.get_or_create(username, channel)
                        
                        if user:
                            self.db.users.update_points(username, channel, points)
                            
                            # Atualizar message_count manualmente
                            with self.db.manager.get_connection() as conn:
                                conn.execute(
                                    """UPDATE users 
                                       SET message_count = ?, 
                                           updated_at = CURRENT_TIMESTAMP
                                       WHERE username = ? AND channel = ?""",
                                    (messages, username, channel)
                                )
                            
                            count += 1
                            print(f"   ✅ {channel}/{username}: {points} pts, {messages} msgs")
                    
                    except Exception as e:
                        print(f"   ❌ Erro ao migrar {username}: {e}")
            
            return count
        
        except Exception as e:
            print(f"   ❌ Erro ao ler bot_data.json: {e}")
            return 0
    
    def _migrate_logs(self) -> int:
        """Migra logs.json (histórico de mensagens)"""
        if not os.path.exists(self.logs_file):
            print("   ⚠️ Arquivo logs.json não encontrado")
            return 0
        
        try:
            with open(self.logs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            count = 0
            
            # Estrutura: lista de logs
            logs = data if isinstance(data, list) else data.get('logs', [])
            
            for log_entry in logs:
                try:
                    # Extrair informações
                    timestamp = log_entry.get('timestamp', '')
                    message_text = log_entry.get('message', '')
                    level = log_entry.get('level', 'info')
                    
                    # Tentar extrair canal e usuário da mensagem
                    # Formato típico: "[canal] username: mensagem"
                    channel = None
                    username = None
                    
                    if '[' in message_text and ']' in message_text:
                        parts = message_text.split(']', 1)
                        if len(parts) == 2:
                            channel = parts[0].strip('[').strip()
                            rest = parts[1].strip()
                            
                            if ':' in rest:
                                username_part, msg = rest.split(':', 1)
                                username = username_part.strip()
                                message_text = msg.strip()
                    
                    # Se conseguiu extrair informações válidas
                    if channel and username and message_text:
                        self.db.messages.create(
                            username=username,
                            channel=channel,
                            message=message_text
                        )
                        count += 1
                
                except Exception as e:
                    # Ignorar entradas inválidas silenciosamente
                    pass
            
            print(f"   ✅ {count} mensagens migradas")
            return count
        
        except Exception as e:
            print(f"   ❌ Erro ao ler logs.json: {e}")
            return 0
    
    def _migrate_auto_responses(self) -> int:
        """Migra auto_responses.json"""
        if not os.path.exists(self.auto_responses_file):
            print("   ⚠️ Arquivo auto_responses.json não encontrado")
            return 0
        
        try:
            with open(self.auto_responses_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            responses = data.get('responses', {}) if isinstance(data, dict) else data
            
            count = 0
            for trigger, response in responses.items():
                try:
                    # Verificar se já existe
                    existing = self.db.auto_responses.get_by_trigger(trigger)
                    
                    if not existing:
                        self.db.auto_responses.create(
                            trigger=trigger,
                            response=response,
                            channel=None,  # Global
                            enabled=True
                        )
                        count += 1
                        print(f"   ✅ {trigger} → {response}")
                    else:
                        print(f"   ⏭️ {trigger} já existe, pulando")
                
                except Exception as e:
                    print(f"   ❌ Erro ao migrar {trigger}: {e}")
            
            return count
        
        except Exception as e:
            print(f"   ❌ Erro ao ler auto_responses.json: {e}")
            return 0
    
    def _migrate_streamers(self) -> int:
        """Migra streamers.json"""
        if not os.path.exists(self.streamers_file):
            print("   ⚠️ Arquivo streamers.json não encontrado")
            return 0
        
        try:
            with open(self.streamers_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            streamers = data.get('streamers', []) if isinstance(data, dict) else data
            
            count = 0
            for streamer in streamers:
                try:
                    username = streamer.get('username')
                    display_name = streamer.get('display_name', username)
                    
                    if not username:
                        continue
                    
                    # Verificar se já existe
                    if not self.db.streamers.exists(username):
                        self.db.streamers.create(
                            username=username,
                            display_name=display_name,
                            auto_connect=False,
                            enabled=True
                        )
                        count += 1
                        print(f"   ✅ {display_name} (@{username})")
                    else:
                        print(f"   ⏭️ {username} já existe, pulando")
                
                except Exception as e:
                    print(f"   ❌ Erro ao migrar streamer: {e}")
            
            return count
        
        except Exception as e:
            print(f"   ❌ Erro ao ler streamers.json: {e}")
            return 0
    
    def _print_report(self, stats: Dict):
        """Imprime relatório final"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO DE MIGRAÇÃO")
        print("=" * 60)
        print(f"\n✅ Usuários migrados:      {stats['users']}")
        print(f"✅ Mensagens migradas:     {stats['messages']}")
        print(f"✅ Auto respostas:         {stats['auto_responses']}")
        print(f"✅ Streamers:              {stats['streamers']}")
        
        if stats['errors'] > 0:
            print(f"\n⚠️ Erros encontrados:      {stats['errors']}")
        
        print("\n" + "=" * 60)
        print("✅ Migração concluída com sucesso!")
        print("=" * 60)
        print("\n💡 Os arquivos JSON originais foram mantidos como backup.")
        print("   Você pode removê-los manualmente se desejar.\n")


def main():
    """Função principal"""
    try:
        migration = DataMigration(data_dir="data", backup=True)
        migration.run()
    except KeyboardInterrupt:
        print("\n\n⚠️ Migração cancelada pelo usuário.\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal na migração: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()