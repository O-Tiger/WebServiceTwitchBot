"""
Script de Migração Automática
Migra dados de JSON para SQLite
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Adicionar ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import BotDataDB, LogsDB, init_databases
from crud import UserCRUD, ChannelCRUD, UserPointsCRUD, AutoResponseCRUD, RaidCRUD
from logs_crud import SystemLogCRUD, ChatMessageCRUD, EventCRUD


class DataMigration:
    """Classe para gerenciar migração de dados"""

    def __init__(self):
        self.data_dir = Path("data")
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar bancos
        print("🔧 Inicializando bancos de dados...")
        self.bot_db, self.logs_db = init_databases()

        # Inicializar CRUDs
        self.user_crud = UserCRUD(self.bot_db)
        self.channel_crud = ChannelCRUD(self.bot_db)
        self.points_crud = UserPointsCRUD(self.bot_db)
        self.response_crud = AutoResponseCRUD(self.bot_db)
        self.raid_crud = RaidCRUD(self.bot_db)
        self.log_crud = SystemLogCRUD(self.logs_db)

        self.stats = {
            "users": 0,
            "channels": 0,
            "points_records": 0,
            "auto_responses": 0,
            "logs": 0,
            "errors": 0,
        }

    def backup_file(self, filepath: Path):
        """Cria backup de um arquivo"""
        if not filepath.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{filepath.stem}_{timestamp}{filepath.suffix}"

        try:
            import shutil

            shutil.copy2(filepath, backup_path)
            print(f"✅ Backup criado: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ Erro ao criar backup de {filepath}: {e}")
            return None

    def load_json(self, filepath: Path):
        """Carrega arquivo JSON"""
        if not filepath.exists():
            print(f"⚠️  Arquivo não encontrado: {filepath}")
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erro ao carregar {filepath}: {e}")
            self.stats["errors"] += 1
            return None

    def migrate_bot_data(self):
        """Migra bot_data.json"""
        print("\n📦 Migrando bot_data.json...")

        filepath = self.data_dir / "bot_data.json"
        data = self.load_json(filepath)

        if not data:
            return

        # Fazer backup
        self.backup_file(filepath)

        # Migrar dados por canal
        for channel_name, channel_data in data.items():
            try:
                print(f"  📺 Processando canal: {channel_name}")

                # Criar canal
                channel_id = self.channel_crud.get_or_create(channel_name)
                self.stats["channels"] += 1

                # Migrar pontos
                user_points = channel_data.get("user_points", {})
                message_count = channel_data.get("message_count", {})

                for username, points in user_points.items():
                    messages = message_count.get(username, 0)

                    # Criar usuário e atualizar pontos
                    self.points_crud.update_user(
                        username=username,
                        channel_name=channel_name,
                        points=points,
                        messages=messages,
                    )

                    self.stats["users"] += 1
                    self.stats["points_records"] += 1

                print(f"    ✅ {len(user_points)} usuários migrados")

            except Exception as e:
                print(f"    ❌ Erro ao processar {channel_name}: {e}")
                self.stats["errors"] += 1

        print(f"✅ bot_data.json migrado com sucesso!")

    def migrate_auto_responses(self):
        """Migra auto_responses.json"""
        print("\n📦 Migrando auto_responses.json...")

        filepath = self.data_dir / "auto_responses.json"
        data = self.load_json(filepath)

        if not data:
            return

        # Fazer backup
        self.backup_file(filepath)

        responses = data.get("responses", {})

        for trigger, response in responses.items():
            try:
                # Criar resposta global (channel_id = None)
                self.response_crud.create(
                    trigger=trigger, response=response, channel_id=None
                )
                self.stats["auto_responses"] += 1

            except Exception as e:
                print(f"  ❌ Erro ao migrar '{trigger}': {e}")
                self.stats["errors"] += 1

        print(f"✅ {len(responses)} auto-respostas migradas!")

    def migrate_logs(self):
        """Migra logs.json"""
        print("\n📦 Migrando logs.json...")

        filepath = self.data_dir / "logs.json"
        data = self.load_json(filepath)

        if not data:
            return

        # Fazer backup
        self.backup_file(filepath)

        logs = data if isinstance(data, list) else data.get("logs", [])

        for log_entry in logs:
            try:
                self.log_crud.create(
                    level=log_entry.get("level", "info"),
                    message=log_entry.get("message", ""),
                    channel=log_entry.get("channel"),
                    username=log_entry.get("username"),
                    extra_data=log_entry.get("extra_data"),
                )
                self.stats["logs"] += 1

            except Exception as e:
                print(f"  ❌ Erro ao migrar log: {e}")
                self.stats["errors"] += 1

        print(f"✅ {len(logs)} logs migrados!")

    def migrate_streamers(self):
        """Migra streamers.json (apenas referência)"""
        print("\n📦 Verificando streamers.json...")

        filepath = self.data_dir / "streamers.json"
        if filepath.exists():
            print(f"  ℹ️  streamers.json permanece no formato JSON")
            print(f"  ℹ️  Use StreamerManager para gerenciar streamers")

    def verify_migration(self):
        """Verifica integridade da migração"""
        print("\n🔍 Verificando migração...")

        # Contar registros no banco
        user_count = self.user_crud.count()
        channel_count = len(self.channel_crud.list_all())
        response_count = len(self.response_crud.list_all())

        print(f"  👥 Usuários no banco: {user_count}")
        print(f"  📺 Canais no banco: {channel_count}")
        print(f"  🤖 Auto-respostas no banco: {response_count}")

        # Verificar consistência
        if user_count == 0 and self.stats["users"] > 0:
            print("  ⚠️  Aviso: Migração pode ter falhado")
            return False

        print("  ✅ Migração verificada com sucesso!")
        return True

    def cleanup_old_files(self):
        """Move arquivos antigos para pasta de backup"""
        print("\n🧹 Limpando arquivos antigos...")

        files_to_move = ["bot_data.json", "auto_responses.json", "logs.json"]

        for filename in files_to_move:
            filepath = self.data_dir / filename
            if filepath.exists():
                try:
                    # Mover para backup
                    new_path = self.backup_dir / f"{filename}.migrated"
                    filepath.rename(new_path)
                    print(f"  ✅ {filename} → backups/")
                except Exception as e:
                    print(f"  ❌ Erro ao mover {filename}: {e}")

    def print_summary(self):
        """Imprime resumo da migração"""
        print("\n" + "=" * 50)
        print("📊 RESUMO DA MIGRAÇÃO")
        print("=" * 50)
        print(f"👥 Usuários migrados:      {self.stats['users']}")
        print(f"📺 Canais migrados:        {self.stats['channels']}")
        print(f"📊 Registros de pontos:    {self.stats['points_records']}")
        print(f"🤖 Auto-respostas:         {self.stats['auto_responses']}")
        print(f"📋 Logs migrados:          {self.stats['logs']}")
        print(f"❌ Erros encontrados:      {self.stats['errors']}")
        print("=" * 50)

    def run(self, cleanup: bool = True, verify: bool = True):
        """Executa migração completa"""
        print("\n" + "=" * 50)
        print("🚀 INICIANDO MIGRAÇÃO JSON → SQLite")
        print("=" * 50)

        # Migrar dados
        self.migrate_bot_data()
        self.migrate_auto_responses()
        self.migrate_logs()
        self.migrate_streamers()

        # Verificar
        if verify:
            success = self.verify_migration()
            if not success:
                print("\n⚠️  Migração pode ter problemas. Verifique manualmente.")

        # Limpar arquivos antigos
        if cleanup:
            response = input("\n🧹 Mover arquivos JSON antigos para backup? (s/N): ")
            if response.lower() in ["s", "sim", "y", "yes"]:
                self.cleanup_old_files()

        # Resumo
        self.print_summary()

        print("\n✅ Migração concluída!")
        print("\n💡 Dicas:")
        print("  - Backups estão em: data/backups/")
        print("  - Banco de dados: database/bot_data.db")
        print("  - Logs: logs/logs.db")
        print("  - Use os CRUDs em app/database/ para acessar dados")


def main():
    """Função principal"""
    print(
        """
    ╔════════════════════════════════════════════════════╗
    ║                                                    ║
    ║      🔄  MIGRAÇÃO DE DADOS JSON → SQLite          ║
    ║                                                    ║
    ╚════════════════════════════════════════════════════╝
    
    Este script irá:
    ✓ Criar bancos de dados SQLite
    ✓ Migrar bot_data.json
    ✓ Migrar auto_responses.json
    ✓ Migrar logs.json
    ✓ Criar backups dos arquivos originais
    ✓ Verificar integridade da migração
    """
    )

    response = input("Deseja continuar? (S/n): ")
    if response.lower() in ["n", "no", "nao", "não"]:
        print("❌ Migração cancelada")
        return

    try:
        migration = DataMigration()
        migration.run(cleanup=True, verify=True)

    except KeyboardInterrupt:
        print("\n\n⚠️  Migração interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal durante migração: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
