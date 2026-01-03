# 🚀 Guia de Deploy para Produção

Este guia explica como fazer deploy do Twitch Bot Dashboard em serviços de hospedagem.

---

## ⚠️ **PRÉ-REQUISITOS OBRIGATÓRIOS**

Antes de fazer deploy, você **DEVE** configurar:

### 1. **Gerar SECRET_KEY**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copie a saída e use como `FLASK_SECRET_KEY` no `.env`

### 2. **Gerar Hash de Senha**
```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('SUA_SENHA_FORTE_AQUI'))"
```
Copie a saída e use como `ADMIN_PASSWORD_HASH` no `.env`

### 3. **Criar arquivo .env**
```bash
cp .env.example .env
# Edite .env e preencha TODAS as variáveis obrigatórias
```

---

## 📦 **OPÇÃO 1: Deploy em VPS (DigitalOcean, Linode, etc.)**

### Passo 1: Preparar o Servidor
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.10+
sudo apt install python3 python3-pip python3-venv -y

# Instalar Git
sudo apt install git -y
```

### Passo 2: Clonar o Projeto
```bash
cd /var/www
sudo git clone SEU_REPOSITORIO twitch-bot
cd twitch-bot
sudo chown -R $USER:$USER /var/www/twitch-bot
```

### Passo 3: Configurar Ambiente Virtual
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Passo 4: Configurar Variáveis de Ambiente
```bash
# Copiar exemplo
cp .env.example .env

# Editar .env
nano .env

# Gerar SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Gerar hash de senha
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('SUA_SENHA_AQUI'))"

# Salvar no .env:
# FLASK_SECRET_KEY=chave_gerada_acima
# ADMIN_PASSWORD_HASH=hash_gerado_acima
# FLASK_HOST=0.0.0.0
# FLASK_PORT=5000
```

### Passo 5: Configurar Gunicorn + Systemd
```bash
# Criar arquivo de serviço
sudo nano /etc/systemd/system/twitch-bot.service
```

Conteúdo do arquivo:
```ini
[Unit]
Description=Twitch Bot Dashboard
After=network.target

[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/var/www/twitch-bot
Environment="PATH=/var/www/twitch-bot/venv/bin"
ExecStart=/var/www/twitch-bot/venv/bin/gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### Passo 6: Iniciar o Serviço
```bash
sudo systemctl daemon-reload
sudo systemctl enable twitch-bot
sudo systemctl start twitch-bot
sudo systemctl status twitch-bot
```

### Passo 7: Configurar Nginx (Reverse Proxy)
```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/twitch-bot
```

Conteúdo:
```nginx
server {
    listen 80;
    server_name SEU_DOMINIO.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:5000/socket.io;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/twitch-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Passo 8: Configurar SSL (HTTPS)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d SEU_DOMINIO.com
```

---

## 🌐 **OPÇÃO 2: Deploy no Heroku**

### Passo 1: Criar Procfile
```bash
echo "web: gunicorn --worker-class eventlet -w 1 run:app" > Procfile
```

### Passo 2: Criar runtime.txt
```bash
echo "python-3.10.12" > runtime.txt
```

### Passo 3: Login e Deploy
```bash
heroku login
heroku create seu-twitch-bot

# Configurar variáveis de ambiente
heroku config:set FLASK_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set ADMIN_PASSWORD_HASH=$(python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('SUA_SENHA'))")
heroku config:set FLASK_HOST=0.0.0.0
heroku config:set FLASK_PORT=5000

# Deploy
git push heroku main
```

---

## 🔧 **OPÇÃO 3: Deploy no Hostinger (Hospedagem Compartilhada)**

⚠️ **AVISO**: Hostinger compartilhado **NÃO suporta WebSockets** nativamente!
Para funcionar corretamente, você precisa de VPS ou Cloud Hosting.

Se você tem VPS na Hostinger, siga as instruções da **OPÇÃO 1** (VPS).

---

## 🐳 **OPÇÃO 4: Deploy com Docker**

### Criar Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "run:app"]
```

### Criar docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    volumes:
      - ./database:/app/database
      - ./logs:/app/logs
      - ./data:/app/data
    restart: always
```

### Deploy
```bash
docker-compose up -d
```

---

## 🔒 **CHECKLIST DE SEGURANÇA**

Antes de fazer deploy, verifique:

- [ ] ✅ `.env` tem `FLASK_SECRET_KEY` único e seguro
- [ ] ✅ `.env` tem `ADMIN_PASSWORD_HASH` (NÃO senha em texto!)
- [ ] ✅ `.env` está no `.gitignore` (NUNCA commitar!)
- [ ] ✅ Senha do admin é forte (mínimo 12 caracteres)
- [ ] ✅ `FLASK_DEBUG=False` em produção
- [ ] ✅ Firewall configurado (permitir apenas portas 80 e 443)
- [ ] ✅ SSL/HTTPS configurado
- [ ] ✅ Backup do banco de dados configurado

---

## 🌍 **CONFIGURAR DOMÍNIO**

### Atualizar OAuth Redirect URIs

Depois de fazer deploy, atualize os redirect URIs em:

1. **Twitch Developer Console**
   - `https://SEU_DOMINIO.com/oauth/twitch/callback`

2. **Google Cloud Console** (se usar)
   - `https://SEU_DOMINIO.com/oauth/google/callback`

3. **GitHub OAuth Apps** (se usar)
   - `https://SEU_DOMINIO.com/oauth/github/callback`

4. **Discord Developer Portal** (se usar)
   - `https://SEU_DOMINIO.com/oauth/discord/callback`

### Atualizar .env
```env
TWITCH_REDIRECT_URI=https://SEU_DOMINIO.com/oauth/twitch/callback
GOOGLE_REDIRECT_URI=https://SEU_DOMINIO.com/oauth/google/callback
GITHUB_REDIRECT_URI=https://SEU_DOMINIO.com/oauth/github/callback
DISCORD_REDIRECT_URI=https://SEU_DOMINIO.com/oauth/discord/callback
```

---

## 📊 **MONITORAMENTO**

### Ver Logs (Systemd)
```bash
sudo journalctl -u twitch-bot -f
```

### Ver Logs (Docker)
```bash
docker-compose logs -f
```

### Ver Status
```bash
sudo systemctl status twitch-bot
```

---

## 🆘 **TROUBLESHOOTING**

### Erro: "No module named 'app'"
```bash
# Verificar se está no diretório correto
pwd  # Deve estar em /var/www/twitch-bot

# Ativar venv
source venv/bin/activate
```

### Erro: "Connection refused"
```bash
# Verificar se serviço está rodando
sudo systemctl status twitch-bot

# Reiniciar serviço
sudo systemctl restart twitch-bot
```

### WebSocket não funciona
```bash
# Verificar configuração do Nginx
sudo nginx -t

# Ver logs do Nginx
sudo tail -f /var/log/nginx/error.log
```

### Erro 500
```bash
# Ver logs completos
sudo journalctl -u twitch-bot -n 100
```

---

## 🔄 **ATUALIZAR APLICAÇÃO**

```bash
cd /var/www/twitch-bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart twitch-bot
```

---

## 📧 **SUPORTE**

Se encontrar problemas:
1. Verifique os logs: `sudo journalctl -u twitch-bot -f`
2. Teste localmente primeiro
3. Verifique se todas variáveis do .env estão configuradas
4. Confirme que portas 80/443 estão abertas no firewall

---

**✅ Deployment Pronto! Acesse: `https://SEU_DOMINIO.com`**
