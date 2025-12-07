"""
Setup Simples - Twitch Bot Dashboard
Configura estrutura Flask SEM migração (usa arquivos existentes)
"""

import os
import sys


def create_structure():
    """Cria estrutura de pastas necessária"""

    folders = [
        "app",
        "app/core",
        "app/web",
        "app/web/templates",
        "app/web/static",
        "app/web/static/js",
        "app/web/static/css",
        "app/api",
        "app/models",
        "app/services",
        "app/utils",
        "migrations",
        "logs",
    ]

    print("📁 Criando estrutura de pastas...\n")

    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"   ✅ {folder}/")

    # Criar __init__.py
    init_files = [
        "app/__init__.py",
        "app/core/__init__.py",
        "app/web/__init__.py",
        "app/api/__init__.py",
        "app/models/__init__.py",
        "app/services/__init__.py",
        "app/utils/__init__.py",
    ]

    print("\n📝 Criando arquivos __init__.py...\n")

    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8") as f:
                f.write('"""Package initialization"""\n')
            print(f"   ✅ {init_file}")

    print("\n" + "=" * 60)
    print("✅ ESTRUTURA CRIADA COM SUCESSO!")
    print("=" * 60)
    print("\n📋 PRÓXIMOS PASSOS:\n")
    print("1. Copie os códigos dos artefatos para os arquivos:")
    print("   • Artefato 1 → app/core/bot_manager.py")
    print("   • Artefato 2 → app/web/app.py")
    print("   • Artefato 3 → app/web/templates/dashboard.html")
    print("   • Artefato 4 → app/web/static/js/dashboard.js")
    print("   • Artefato 5 → app/web/templates/login.html")
    print("   • Artefato 6 → run.py (raiz do projeto)")
    print("   • Artefato 7 → requirements.txt (raiz do projeto)")
    print("\n2. Instale dependências:")
    print("   pip install -r requirements.txt")
    print("\n3. Execute o servidor:")
    print("   python run.py")
    print("\n4. Acesse: http://localhost:5000")
    print("   Login: admin / admin\n")

    # Criar arquivo de instruções
    create_instructions_file()


def create_instructions_file():
    """Cria arquivo com instruções detalhadas"""

    instructions = """# 🚀 INSTRUÇÕES DE CONFIGURAÇÃO

## Arquivos que você DEVE criar/copiar:

### 1. app/core/bot_manager.py
Copie o código do **Artefato 1** (BotManager)

### 2. app/web/app.py  
Copie o código do **Artefato 2** (Flask App)

### 3. app/web/templates/dashboard.html
Copie o código do **Artefato 3** (Dashboard HTML)

### 4. app/web/static/js/dashboard.js
Copie o código do **Artefato 4** (JavaScript)

### 5. app/web/templates/login.html
Copie o código do **Artefato 5** (Login HTML)

### 6. run.py (raiz do projeto)
Copie o código do **Artefato 6** (Arquivo de execução)

### 7. requirements.txt (raiz do projeto)
Copie o código do **Artefato 7** (Dependências)

---

## Arquivos que você JÁ TEM (NÃO alterar):

✅ twitch_bot_class.py
✅ token_manager.py
✅ streamer_manager.py
✅ data/config.json
✅ data/oauth_config.json
✅ data/streamers.json
✅ data/bot_data.json
✅ data/token_data.json

---

## Comandos para executar:

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar servidor
python run.py

# 3. Acessar dashboard
http://localhost:5000

# Login: admin / admin
```

---

## Estrutura final esperada:

```
Projeto/
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── bot_manager.py      ← CRIAR/COPIAR
│   └── web/
│       ├── __init__.py
│       ├── app.py               ← CRIAR/COPIAR
│       ├── templates/
│       │   ├── dashboard.html   ← CRIAR/COPIAR
│       │   └── login.html       ← CRIAR/COPIAR
│       └── static/
│           └── js/
│               └── dashboard.js ← CRIAR/COPIAR
├── data/
│   ├── config.json              ← JÁ EXISTE
│   ├── oauth_config.json        ← JÁ EXISTE
│   └── ...                      ← MANTER TUDO
├── twitch_bot_class.py          ← JÁ EXISTE
├── token_manager.py             ← JÁ EXISTE
├── streamer_manager.py          ← JÁ EXISTE
├── run.py                       ← CRIAR/COPIAR
└── requirements.txt             ← CRIAR/COPIAR
```

---

## ⚠️ Problemas Comuns:

### Erro: "No module named 'app'"
**Solução:** Certifique-se de executar `python run.py` da pasta raiz do projeto

### Erro: "Token inválido"
**Solução:** Verifique se `data/oauth_config.json` existe e tem dados válidos

### Erro: Porta 5000 em uso
**Solução:** Mude a porta em `run.py` (linha final): `port=8080`

---

## 🎉 Tudo pronto!

Após seguir essas instruções, você terá:
✅ Dashboard web funcional
✅ WebSocket em tempo real
✅ API REST completa
✅ 100% compatível com seu código antigo
"""

    with open("INSTRUCOES_SETUP.md", "w", encoding="utf-8") as f:
        f.write(instructions)

    print("📄 Arquivo criado: INSTRUCOES_SETUP.md")
    print("   (Consulte para instruções detalhadas)\n")


def check_existing_files():
    """Verifica se arquivos importantes já existem"""

    print("\n🔍 Verificando arquivos existentes...\n")

    files_to_check = {
        "twitch_bot_class.py": "Classe do bot Twitch",
        "token_manager.py": "Gerenciador de tokens",
        "streamer_manager.py": "Gerenciador de streamers",
        "data/config.json": "Configurações",
        "data/oauth_config.json": "OAuth config",
        "data/streamers.json": "Lista de streamers",
    }

    all_exist = True

    for file, desc in files_to_check.items():
        exists = os.path.exists(file)
        status = "✅" if exists else "❌"
        print(f"   {status} {file:<30} - {desc}")
        if not exists:
            all_exist = False

    print()

    if all_exist:
        print("✅ Todos os arquivos importantes encontrados!")
        print("   → Pode continuar com o setup Flask\n")
    else:
        print("⚠️  Alguns arquivos estão faltando")
        print("   → Certifique-se de estar na pasta correta do projeto\n")

    return all_exist


def main():
    """Função principal"""

    print(
        """
╔════════════════════════════════════════════════════════╗
║                                                        ║
║  🚀  SETUP SIMPLES - TWITCH BOT DASHBOARD             ║
║      Flask + WebSocket (sem migração)                 ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
"""
    )

    # Verificar arquivos existentes
    check_existing_files()

    # Perguntar confirmação
    response = input("📋 Deseja criar a estrutura de pastas? (s/n): ")

    if response.lower() in ["s", "sim", "y", "yes"]:
        create_structure()
    else:
        print("\n❌ Setup cancelado.")


if __name__ == "__main__":
    main()
