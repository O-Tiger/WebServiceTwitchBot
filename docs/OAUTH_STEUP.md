# 🔐 Guia Completo de Configuração OAuth

## 📋 Visão Geral

O sistema OAuth permite que usuários façam login usando suas contas de:
- 🔵 **Google**
- 🟣 **Twitch**
- ⚫ **GitHub**
- 🔵 **Discord**

---

## 🚀 Como Funciona

1. Usuário clica em "Continuar com [Provedor]"
2. Sistema verifica se o provedor está configurado
3. Se não estiver, mostra página de configuração com tutorial
4. Se estiver, redireciona para autenticação OAuth
5. Após aprovação, usuário é autenticado automaticamente

---

## 📱 Configuração por Provedor

### 1️⃣ Google OAuth

#### Passo a Passo:

1. **Acesse**: https://console.cloud.google.com
2. **Crie um projeto** (ou selecione existente)
3. **Vá em**: APIs & Services → Credentials
4. **Clique em**: Create Credentials → OAuth client ID
5. **Configure**:
   - Application type: `Web application`
   - Name: `Twitch Bot Dashboard`
   - Authorized redirect URIs: `http://127.0.0.1:5000/oauth/google/callback`
6. **Copie**: Client ID e Client Secret

#### Informações Importantes:
- **Redirect URI**: `http://127.0.0.1:5000/oauth/google/callback`
- **Scopes**: openid, email, profile
- **Docs**: https://developers.google.com/identity/protocols/oauth2

---

### 2️⃣ Twitch OAuth

#### Passo a Passo:

1. **Acesse**: https://dev.twitch.tv/console/apps
2. **Clique em**: Register Your Application
3. **Preencha**:
   - Name: `Twitch Bot Dashboard`
   - OAuth Redirect URLs: `http://127.0.0.1:5000/oauth/twitch/callback`
   - Category: `Application Integration`
4. **Clique em**: Create
5. **Copie**: Client ID
6. **Gere Secret**: New Secret → Copie o Client Secret

#### Informações Importantes:
- **Redirect URI**: `http://127.0.0.1:5000/oauth/twitch/callback`
- **Scopes**: user:read:email
- **Docs**: https://dev.twitch.tv/docs/authentication

---

### 3️⃣ GitHub OAuth

#### Passo a Passo:

1. **Acesse**: https://github.com/settings/developers
2. **Clique em**: OAuth Apps → New OAuth App
3. **Preencha**:
   - Application name: `Twitch Bot Dashboard`
   - Homepage URL: `http://127.0.0.1:5000`
   - Authorization callback URL: `http://127.0.0.1:5000/oauth/github/callback`
4. **Clique em**: Register application
5. **Copie**: Client ID
6. **Gere Secret**: Generate a new client secret → Copie (aparece só uma vez!)

#### Informações Importantes:
- **Redirect URI**: `http://127.0.0.1:5000/oauth/github/callback`
- **Scopes**: read:user, user:email
- **Docs**: https://docs.github.com/en/developers/apps/building-oauth-apps

---

### 4️⃣ Discord OAuth

#### Passo a Passo:

1. **Acesse**: https://discord.com/developers/applications
2. **Clique em**: New Application
3. **Dê um nome**: `Twitch Bot Dashboard`
4. **Vá em**: OAuth2
5. **Adicione Redirect**: `http://127.0.0.1:5000/oauth/discord/callback`
6. **Copie**: Client ID
7. **Reset Secret**: Para ver o Client Secret → Copie

#### Informações Importantes:
- **Redirect URI**: `http://127.0.0.1:5000/oauth/discord/callback`
- **Scopes**: identify, email
- **Docs**: https://discord.com/developers/docs/topics/oauth2

---

## 🔧 Instalação

### 1. Instalar Dependências

```bash
pip install requests
```

### 2. Criar Arquivo oauth_manager.py

Coloque o arquivo `oauth_manager.py` na mesma pasta do `app.py`

### 3. Atualizar app.py

O código já foi atualizado com as rotas OAuth

---

## 📁 Estrutura de Arquivos

```
app/
├── web/
│   ├── app.py                 # Flask app com rotas OAuth
│   ├── oauth_manager.py       # Gerenciador OAuth
│   ├── templates/
│   │   ├── login.html         # Login com botões OAuth
│   │   ├── oauth_setup.html   # Configuração OAuth
│   │   └── oauth_error.html   # Página de erro
│   └── ...
└── data/
    └── oauth_providers.json   # Credenciais OAuth (criado automaticamente)
```

---

## 🎯 Fluxo de Uso

### Primeira Vez (Configuração):

1. Usuário clica em "Continuar com Google"
2. Sistema detecta que Google não está configurado
3. Mostra página com tutorial passo a passo
4. Usuário preenche Client ID e Secret
5. Sistema salva e redireciona para OAuth

### Próximas Vezes (Já Configurado):

1. Usuário clica em "Continuar com Google"
2. Sistema redireciona direto para Google OAuth
3. Usuário aprova permissões
4. Sistema recebe callback e cria sessão
5. Usuário é redirecionado para dashboard

---

## 🔒 Segurança

### State Parameter (CSRF Protection):
- Cada requisição OAuth gera um `state` aleatório
- Armazenado na sessão
- Verificado no callback para prevenir ataques CSRF

### Client Secret:
- **NUNCA** exponha o Client Secret publicamente
- Armazenado em arquivo local `data/oauth_providers.json`
- Adicione ao `.gitignore` para não commitá-lo

---

## ⚙️ Configuração Manual

### Editar Manualmente as Credenciais:

```json
// data/oauth_providers.json
{
  "google": {
    "client_id": "SEU_CLIENT_ID_AQUI",
    "client_secret": "SEU_CLIENT_SECRET_AQUI",
    "redirect_uri": "http://127.0.0.1:5000/oauth/google/callback",
    // ... outras configurações
  }
}
```

---

## 🌐 Produção (HTTPS)

Ao colocar em produção:

1. **Atualize os Redirect URIs** para usar HTTPS:
   ```
   https://seudominio.com/oauth/google/callback
   ```

2. **Reconfigure nos Provedores**:
   - Adicione os novos URIs HTTPS
   - Remova URIs de desenvolvimento

3. **Use Variáveis de Ambiente**:
   ```python
   import os
   client_id = os.getenv('GOOGLE_CLIENT_ID')
   ```

---

## 🐛 Troubleshooting

### Erro: "Redirect URI mismatch"
**Solução**: Certifique-se de que o URI está exatamente igual em ambos os lugares

### Erro: "Invalid client"
**Solução**: Verifique se copiou Client ID e Secret corretamente

### Erro: "State mismatch"
**Solução**: Limpe os cookies/sessão e tente novamente

### Usuário cancela autenticação
**Resultado**: Redireciona para página de erro com opções de tentar novamente

---

## 📊 Status API

Verificar quais provedores estão configurados:

```bash
curl http://127.0.0.1:5000/api/oauth/status
```

Resposta:
```json
{
  "google": true,
  "twitch": false,
  "github": true,
  "discord": false
}
```

---

## ✅ Checklist de Configuração

- [ ] Criar aplicação OAuth no provedor
- [ ] Copiar Client ID
- [ ] Copiar Client Secret
- [ ] Adicionar Redirect URI correto
- [ ] Testar fluxo de login
- [ ] Verificar que dados do usuário são recebidos
- [ ] Adicionar `oauth_providers.json` ao `.gitignore`

---

## 💡 Dicas

1. **Teste localmente primeiro** antes de colocar em produção
2. **Use HTTPS em produção** sempre
3. **Mantenha secrets seguros** - nunca commite no Git
4. **Monitore logs** para detectar problemas
5. **Implemente rate limiting** para prevenir abuso

---

## 📞 Suporte

Em caso de dúvidas:
- Consulte a documentação oficial de cada provedor
- Verifique os logs do Flask para erros detalhados
- Use a página de ajuda do dashboard

---

## 🎉 Pronto!

Seu sistema OAuth está configurado e funcionando! Usuários agora podem fazer login com suas contas favoritas de forma rápida e segura.