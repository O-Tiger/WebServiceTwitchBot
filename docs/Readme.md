# 🎮 Twitch Bot Dashboard - Premium v3.0

Bot avançado para Twitch com **dashboard web moderno** usando Flask, substituindo completamente a interface Tkinter.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![TwitchIO](https://img.shields.io/badge/TwitchIO-2.9-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Funcionalidades

### 🎯 Core
- ✅ **Múltiplos canais simultâneos** - Conecte a vários streamers ao mesmo tempo
- ✅ **Sistema de pontos automático** - Usuários ganham pontos por participação
- ✅ **Respostas automáticas** - Configure gatilhos personalizados
- ✅ **Comandos customizáveis** - !dados, !pontos, !top, !piada, etc.
- ✅ **Moderação básica** - Filtro de palavras e logs de atividades

### 🌐 Dashboard Web
- ✅ **Interface moderna** - Design responsivo com Tailwind CSS
- ✅ **WebSocket em tempo real** - Chat e logs ao vivo
- ✅ **Controle START/STOP** - Inicie/pare bots por API ou interface
- ✅ **Estatísticas agregadas** - Visualize dados de todos os canais
- ✅ **Editor JSON visual** - Edite configurações pela web
- ✅ **Autenticação segura** - Sistema de login

### 🔧 Avançado
- ✅ **API REST completa** - Controle programático via HTTP
- ✅ **Integração Discord** - Notificações e comandos
- ✅ **Integração Minecraft** - Comandos RCON
- ✅ **Reconhecimento de voz** - Controle por comandos falados
- ✅ **Importação de dados** - StreamElements, Nightbot

---

## 📁 Estrutura do Projeto

```
Projeto/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── bot_manager.py          # Gerenciador central de bots
│   │   └── twitch_bot.py           # Classe do bot (do projeto antigo)
│   ├── web/
│   │   ├── __init__.py
│   │   ├── app.py                  # Aplicação Flask principal
│   │   ├── auth.py                 # Autenticação
│   │   ├── templates/
│   │   │   ├── base.html
│   │   │   ├── login.html
│   │   │   ├── dashboard.html
│   │   │   ├── chat.html
│   │   │   ├── settings.html
│   │   │   └── integrations.html
│   │   └── static/
│   │       ├── css/style.css
│   │       └── js/
│   │           ├── dashboard.js
│   │           └── websocket.js
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py               # Rotas da API
│   │   └── bot_control.py          # Controle dos bots
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   └── services/
│       ├── __init__.py
│       ├── twitch_api.py
│       └── oauth_service.py
├── migrations/
│   └── migrate_from_old.py         # Script de migração automática
├── data/
│   ├── config.json
│   ├── oauth_config.json
│   ├── streamers.json
│   ├── bot_data.json
│   └── token_data.json
├── run.py                           # Arquivo principal de execução
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Instalação

### 1️⃣ Clone ou baixe o projeto

```bash
git clone https://github.com/seu-usuario/twitch-bot-dashboard.git
cd twitch-bot-dashboard
```

### 2️⃣ Crie ambiente virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Instale dependências

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure OAuth da Twitch

Crie um aplicativo em: https://dev.twitch.tv/console

Edite `data/oauth_config.json`:

```json
{
  "client_id": "SEU_CLIENT_ID",
  "client_secret": "SEU_CLIENT_SECRET",
  "refresh_token": "SEU_REFRESH_TOKEN"
}
```

### 5️⃣ Execute o servidor

```bash
python run.py
```

### 6️⃣ Acesse o dashboard

Abra no navegador: **http://localhost:5000**

**Login padrão:**
- Usuário: `admin`
- Senha: `admin`

---

## 🔄 Migração do Tkinter

Se você já tem o bot Tkinter funcionando:

```bash
python migrations/migrate_from_old.py
```

O script irá:
1. ✅ Criar backup dos dados atuais
2. ✅ Converter configurações para Flask
3. ✅ Migrar todos os dados de pontos
4. ✅ Migrar streamers salvos
5. ✅ Migrar auto-respostas
6. ✅ Preservar logs históricos

---

## 📖 Como Usar

### 🎮 Conectar a um Canal

1. Acesse o dashboard
2. Digite o username do streamer
3. Clique em **▶️ START**
4. O bot conecta automaticamente

### 💬 Enviar Mensagens

1. Vá para a aba **Chat**
2. Selecione o canal
3. Digite a mensagem
4. Clique em **📤 Enviar**

### 🤖 Adicionar Resposta Automática

1. Vá para a aba **Auto Respostas**
2. Digite o gatilho (ex: "oi")
3. Digite a resposta (ex: "tchau")
4. Clique em **➕ Adicionar**

### 📊 Ver Estatísticas

- Dashboard mostra estatísticas em tempo real
- Total de usuários, mensagens, pontos
- Top usuários por canal
- Logs de todas as atividades

---

## 🔌 API REST

### Endpoints Disponíveis

#### **Iniciar Bot**
```http
POST /api/bot/start
Content-Type: application/json

{
  "channel": "nome_do_canal"
}
```

#### **Parar Bot**
```http
POST /api/bot/stop
Content-Type: application/json

{
  "channel": "nome_do_canal"
}
```

#### **Enviar Mensagem**
```http
POST /api/bot/send
Content-Type: application/json

{
  "channel": "nome_do_canal",
  "message": "Olá, chat!"
}
```

#### **Obter Estatísticas**
```http
GET /api/stats
```

#### **Adicionar Resposta Automática**
```http
POST /api/auto-response/add
Content-Type: application/json

{
  "trigger": "oi",
  "response": "tchau"
}
```

---

## 🎨 Personalização

### Mudar Tema/Cores

Edite `app/web/templates/dashboard.html` e modifique as classes Tailwind:

```html
<!-- Alterar cor primária de roxo para azul -->
<div class="bg-purple-600">  <!-- Antes -->
<div class="bg-blue-600">    <!-- Depois -->
```

### Adicionar Novos Comandos

Edite `twitch_bot_class.py`:

```python
@commands.command(name='meucomando')
async def my_command(self, ctx):
    """Descrição do comando"""
    await ctx.send("Resposta do comando!")
```

### Customizar Autenticação

Edite `app/web/app.py`:

```python
# Trocar credenciais padrão
if username == 'admin' and password == 'admin':
    # Usar banco de dados, OAuth, etc.
```

---

## 🐛 Troubleshooting

### Erro: "Token inválido"
- ✅ Verifique `oauth_config.json`
- ✅ Gere novo token em https://twitchtokengenerator.com
- ✅ Execute o script de renovação

### Erro: "Porta 5000 em uso"
```bash
# Mude a porta em run.py
socketio.run(app, port=8080)  # Use outra porta
```

### WebSocket não conecta
- ✅ Verifique firewall
- ✅ Teste em http://localhost:5000 (não HTTPS localmente)
- ✅ Limpe cache do navegador

---

## 📦 Dependências Opcionais

### Reconhecimento de Voz
```bash
pip install SpeechRecognition pyaudio pyttsx3
```

### Integração Discord
```bash
pip install discord.py
```

### Integração Minecraft
```bash
pip install mcrcon
```

---

## 🚀 Deploy (Produção)

### Usando Gunicorn

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app.web.app:app
```

### Docker (recomendado)

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

---

## 📝 Changelog

### v3.0 (2025-11-30)
- ✅ Migração completa Tkinter → Flask
- ✅ Dashboard web moderno
- ✅ WebSocket em tempo real
- ✅ API REST completa
- ✅ Múltiplos canais simultâneos
- ✅ Sistema de autenticação

### v2.0 (Anterior)
- Interface Tkinter
- Bot básico com comandos
- Sistema de pontos

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

## 💬 Suporte

- **Issues:** https://github.com/seu-usuario/twitch-bot-dashboard/issues
- **Documentação:** Este README
- **Email:** seu-email@exemplo.com

---

## ⭐ Agradecimentos

- TwitchIO - Biblioteca Python para Twitch
- Flask - Framework web
- Tailwind CSS - Framework CSS
- Socket.IO - WebSocket em tempo real

---

**Desenvolvido com ❤️ para a comunidade Twitch**

🎮 **Boas lives e bom código!**
