# 🚀 INSTRUÇÕES DE CONFIGURAÇÃO

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
