"""
Script de migração: JSON → SQLite
Converte todos os arquivos JSON em /data para bancos de dados SQLite
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.crud import BotDatabase


def backup_file(filepath: str) -> bool:
    """Faz backup de um arquivo JSON"""
    if not os.path.exists(filepath):
        return False

    backup_path = filepath + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            with open(backup_path, "w", encoding="utf-8") as b:
                b.write(f.read())
        print(f"📦 Backup criado: {backup_path}")
        return True
    except Exception as e:
        print(f"⚠️  Erro ao fazer backup de {filepath}: {e}")
        return False


def migrate_auto_responses(db: BotDatabase) -> bool:
    """Migra auto_responses.json para banco de dados"""
    filepath = "data/auto_responses.json"

    if not os.path.exists(filepath):
        print(f"⏭️  {filepath} não encontrado, pulando...")
        return True

    print(f"\n🔄 Migrando {filepath}...")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        responses = data.get("responses", {})
        migrated = 0

        for trigger, response in responses.items():
            # Verificar se já existe
            existing = db.auto_responses.get_by_trigger(trigger, channel_id=None)

            if not existing:
                db.auto_responses.create(
                    trigger=trigger, response=response, channel_id=None, enabled=True
                )
                migrated += 1

        print(f"✅ {migrated} auto-respostas migradas")

        # Fazer backup
        if backup_file(filepath):
            os.remove(filepath)
            print(f"🗑️  Arquivo original removido")

        return True

    except Exception as e:
        print(f"❌ Erro ao migrar {filepath}: {e}")
        return False


def migrate_streamers(db: BotDatabase) -> bool:
    """Migra streamers.json para banco de dados"""
    filepath = "data/streamers.json"

    if not os.path.exists(filepath):
        print(f"⏭️  {filepath} não encontrado, pulando...")
        return True

    print(f"\n🔄 Migrando {filepath}...")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        streamers_list = data.get("streamers", [])
        migrated = 0

        for streamer in streamers_list:
            username = streamer.get("username", "").lower()
            if username and not db.streamers.exists(username):
                db.streamers.create(
                    username=username,
                    display_name=streamer.get("display_name", username),
                    auto_connect=streamer.get("auto_connect", False),
                )
                migrated += 1

        print(f"✅ {migrated} streamers migrados")

        # Fazer backup
        if backup_file(filepath):
            os.remove(filepath)
            print(f"🗑️  Arquivo original removido")

        return True

    except Exception as e:
        print(f"❌ Erro ao migrar {filepath}: {e}")
        return False


def migrate_oauth_config(db: BotDatabase) -> bool:
    """oauth_config.json é mantido como JSON para credenciais sensíveis"""
    filepath = "data/oauth_config.json"

    if os.path.exists(filepath):
        print(f"⏭️  {filepath} será mantido como JSON (credenciais sensíveis)")
    else:
        print(f"⏭️  {filepath} não encontrado, pulando...")

    return True


def migrate_oauth_tokens(db: BotDatabase) -> bool:
    """Migra token_data.json para banco de dados"""
    filepath = "data/token_data.json"

    if not os.path.exists(filepath):
        print(f"⏭️  {filepath} não encontrado, pulando...")
        return True

    print(f"\n🔄 Migrando {filepath}...")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        migrated = 0

        # Estrutura esperada: {"provider": {"user_id": {...token_data...}}}
        for provider, users in data.items():
            if isinstance(users, dict):
                for user_id, token_data in users.items():
                    if isinstance(token_data, dict):
                        db.oauth_tokens.save_token(
                            provider=provider,
                            user_id=user_id,
                            access_token=token_data.get("access_token", ""),
                            refresh_token=token_data.get("refresh_token"),
                            expires_at=token_data.get("expires_at"),
                            scope=token_data.get("scope"),
                        )
                        migrated += 1

        print(f"✅ {migrated} tokens OAuth migrados")

        # Fazer backup
        if backup_file(filepath):
            os.remove(filepath)
            print(f"🗑️  Arquivo original removido")

        return True

    except Exception as e:
        print(f"❌ Erro ao migrar {filepath}: {e}")
        return False


def main():
    """Executa migração completa"""
    print(
        """
    ╔════════════════════════════════════════════════════╗
    ║                                                    ║
    ║         📦 MIGRAÇÃO JSON → SQLITE                 ║
    ║                                                    ║
    ║     Convertendo arquivos JSON para banco de dados  ║
    ║                                                    ║
    ╚════════════════════════════════════════════════════╝
    """
    )

    try:
        db = BotDatabase()
        print("✅ Banco de dados conectado")

        # Executar migrações
        migrations = [
            ("Auto-respostas", migrate_auto_responses),
            ("Streamers", migrate_streamers),
            ("Tokens OAuth", migrate_oauth_tokens),
        ]

        results = {}
        for name, migration_func in migrations:
            results[name] = migration_func(db)

        # Resumo
        print("\n" + "=" * 50)
        print("📊 RESUMO DA MIGRAÇÃO")
        print("=" * 50)

        for name, success in results.items():
            status = "✅ Sucesso" if success else "❌ Falha"
            print(f"{status}: {name}")

        if all(results.values()):
            print("\n🎉 Migração concluída com sucesso!")
            return 0
        else:
            print("\n⚠️  Migração concluída com erros")
            return 1

    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
