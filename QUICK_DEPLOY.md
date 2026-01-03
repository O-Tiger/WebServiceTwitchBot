# ⚡ Guia Rápido de Deploy - Hostinger/VPS

Este é um guia resumido para fazer deploy rapidamente. Para detalhes completos, veja [DEPLOYMENT.md](DEPLOYMENT.md).

---

## 🎯 **5 PASSOS PARA DEPLOY**

### **1️⃣ Gerar Credenciais Seguras**

No seu computador local:

```bash
# Gerar SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
# Copie a saída: ex: 8a3f9c2e1d4b7a6f8e2c9d1b4a7e3f6c8d2b9e1a4c7f6b3e8d1a9c2f4e7b6a3d

# Gerar hash de senha (troque 'MinhaSenh@Forte123' pela sua senha)
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('MinhaSenh@Forte123'))"
# Copie a saída: ex: scrypt:32768:8:1$abc123def...
```

Guarde essas duas strings, você vai precisar delas!

---

### **2️⃣ Conectar no Servidor (SSH)**

```bash
ssh seu_usuario@SEU_IP_OU_DOMINIO
```

---

### **3️⃣ Instalar e Configurar**

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install python3 python3-pip python3-venv git nginx -y

# Clonar projeto
cd /var/www
sudo git clone https://github.com/SEU_USUARIO/SEU_REPO.git twitch-bot
cd twitch-bot
sudo chown -R $USER:$USER /var/www/twitch-bot

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Criar arquivo .env
cp .env.example .env
nano .env
```

**Edite o .env** e preencha:

```env
# Cole a SECRET_KEY que você gerou no passo 1
FLASK_SECRET_KEY=cole_aqui_a_chave_que_voce_gerou

# Cole o hash de senha que você gerou no passo 1
ADMIN_PASSWORD_HASH=cole_aqui_o_hash_que_voce_gerou

# Configure para aceitar conexões externas
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Seu domínio (ou IP)
TWITCH_REDIRECT_URI=http://SEU_DOMINIO/oauth/twitch/callback
```

Salve (Ctrl+O, Enter, Ctrl+X)

---

### **4️⃣ Configurar Serviço Systemd**

```bash
sudo nano /etc/systemd/system/twitch-bot.service
```

Cole isto (MODIFIQUE `seu_usuario` pelo seu usuário do servidor):

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

Salve e inicie:

```bash
sudo systemctl daemon-reload
sudo systemctl enable twitch-bot
sudo systemctl start twitch-bot
sudo systemctl status twitch-bot
```

Deve mostrar "active (running)" em verde!

---

### **5️⃣ Configurar Nginx**

```bash
sudo nano /etc/nginx/sites-available/twitch-bot
```

Cole isto (MODIFIQUE `SEU_DOMINIO.com`):

```nginx
server {
    listen 80;
    server_name SEU_DOMINIO.com www.SEU_DOMINIO.com;

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
    }
}
```

Ativar e reiniciar:

```bash
sudo ln -s /etc/nginx/sites-available/twitch-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🎉 **PRONTO!**

Acesse: `http://SEU_DOMINIO.com`

Login:
- **Username:** `admin`
- **Senha:** A senha que você usou no passo 1 (NÃO o hash!)

---

## 🔒 **OPCIONAL: Ativar HTTPS (SSL)**

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d SEU_DOMINIO.com -d www.SEU_DOMINIO.com
```

Siga as instruções e pronto! Agora acesse via `https://SEU_DOMINIO.com`

---

## 🔧 **COMANDOS ÚTEIS**

```bash
# Ver logs em tempo real
sudo journalctl -u twitch-bot -f

# Reiniciar serviço
sudo systemctl restart twitch-bot

# Parar serviço
sudo systemctl stop twitch-bot

# Ver status
sudo systemctl status twitch-bot

# Atualizar código
cd /var/www/twitch-bot
git pull origin main
sudo systemctl restart twitch-bot
```

---

## ⚠️ **TROUBLESHOOTING**

**Erro 502 Bad Gateway:**
```bash
sudo systemctl status twitch-bot
sudo journalctl -u twitch-bot -n 50
```

**Porta 5000 já em uso:**
```bash
sudo lsof -i :5000
# Matar processo: sudo kill -9 PID
```

**Permissões negadas:**
```bash
sudo chown -R $USER:$USER /var/www/twitch-bot
```

---

## 📞 **PRECISA DE AJUDA?**

Veja o guia completo: [DEPLOYMENT.md](DEPLOYMENT.md)

**✅ Boa sorte com o deploy!** 🚀
