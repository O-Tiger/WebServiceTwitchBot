// Integrations Manager - Full Implementation
// Conecta o frontend com as rotas de API

let voiceEnabled = false;
let voiceRecognition = null;

// ===== INICIALIZAÇÃO =====

document.addEventListener("DOMContentLoaded", () => {
  loadIntegrationsStatus();
  setupEventListeners();
  initVoiceRecognition();
});

function setupEventListeners() {
  // Discord
  document
    .getElementById("btn-save-discord")
    ?.addEventListener("click", saveDiscord);
  document
    .getElementById("btn-test-discord")
    ?.addEventListener("click", testDiscord);

  // Minecraft
  document
    .getElementById("btn-save-minecraft")
    ?.addEventListener("click", saveMinecraft);
  document
    .getElementById("btn-test-minecraft")
    ?.addEventListener("click", testMinecraft);

  // Email
  document
    .getElementById("btn-save-email")
    ?.addEventListener("click", saveEmail);
  document
    .getElementById("btn-test-email")
    ?.addEventListener("click", testEmail);

  // Twitch API
  document
    .getElementById("btn-save-twitch-api")
    ?.addEventListener("click", saveTwitchAPI);

  // Import
  document
    .getElementById("btn-import-streamelements")
    ?.addEventListener("click", () => importFile("streamelements"));
  document
    .getElementById("btn-import-nightbot")
    ?.addEventListener("click", () => importFile("nightbot"));
}

// ===== CARREGAR STATUS =====

async function loadIntegrationsStatus() {
  try {
    const res = await fetch("/api/integrations/status");
    const data = await res.json();

    console.log("📊 Status das integrações:", data);

    // Atualizar badges de status
    updateStatusBadge("discord", data.discord);
    updateStatusBadge("minecraft", data.minecraft);
    updateStatusBadge("email", data.email);
    updateStatusBadge("twitch-api", data.twitch_api);
  } catch (err) {
    console.error("Erro ao carregar status:", err);
    showToast("Erro ao carregar status das integrações", "error");
  }
}

function updateStatusBadge(name, status) {
  const badge = document.getElementById(`status-${name}`);
  if (!badge) return;

  if (status.enabled) {
    badge.textContent = "🟢 Ativado";
    badge.className = "bg-green-600 text-xs px-3 py-1 rounded-full";
  } else {
    badge.textContent = "🔴 Desativado";
    badge.className = "bg-red-600 text-xs px-3 py-1 rounded-full";
  }

  // Atualizar disponibilidade
  if (!status.available) {
    const card = document.getElementById(`card-${name}`);
    if (card) {
      const warning = document.createElement("div");
      warning.className =
        "bg-yellow-600/20 border border-yellow-600 rounded-lg p-2 mt-2 text-xs";
      warning.textContent = "⚠️ Biblioteca não instalada";
      card.querySelector(".space-y-3")?.after(warning);
    }
  }
}

// ===== DISCORD =====

async function saveDiscord() {
  const token = document.getElementById("discord-token").value.trim();
  const channelId = document.getElementById("discord-channel").value.trim();

  if (!token || !channelId) {
    showToast("Preencha o Token e o Channel ID", "warning");
    return;
  }

  try {
    const res = await fetch("/api/integrations/discord/setup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, channel_id: channelId }),
    });

    const data = await res.json();

    if (res.ok) {
      showToast("✅ Discord configurado com sucesso!", "success");
      loadIntegrationsStatus();
    } else {
      showToast(`❌ ${data.error}`, "error");
    }
  } catch (err) {
    console.error("Erro ao salvar Discord:", err);
    showToast("Erro de conexão", "error");
  }
}

async function testDiscord() {
  try {
    const res = await fetch("/api/integrations/discord/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: "🎮 Teste de integração do Twitch Bot!",
      }),
    });

    const data = await res.json();
    showToast(
      res.ok ? `✅ ${data.message}` : `❌ ${data.error}`,
      res.ok ? "success" : "error"
    );
  } catch (err) {
    showToast("Erro ao testar Discord", "error");
  }
}

async function disableDiscord() {
  try {
    const res = await fetch("/api/integrations/discord/disable", {
      method: "POST",
    });
    const data = await res.json();

    if (res.ok) {
      showToast("Discord desabilitado", "info");
      loadIntegrationsStatus();
    }
  } catch (err) {
    showToast("Erro ao desabilitar", "error");
  }
}

// ===== MINECRAFT =====

async function saveMinecraft() {
  const host = document.getElementById("minecraft-host").value.trim();
  const port = parseInt(document.getElementById("minecraft-port").value);
  const password = document.getElementById("minecraft-password").value.trim();

  if (!host || !password) {
    showToast("Preencha o Host e a Senha RCON", "warning");
    return;
  }

  try {
    const res = await fetch("/api/integrations/minecraft/setup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ host, port, password }),
    });

    const data = await res.json();

    if (res.ok) {
      showToast("✅ Minecraft configurado com sucesso!", "success");
      loadIntegrationsStatus();
    } else {
      showToast(`❌ ${data.error}`, "error");
    }
  } catch (err) {
    console.error("Erro ao salvar Minecraft:", err);
    showToast("Erro de conexão", "error");
  }
}

async function testMinecraft() {
  try {
    const res = await fetch("/api/integrations/minecraft/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        command: "say Teste de integração com a Twitch!",
      }),
    });

    const data = await res.json();
    showToast(
      res.ok ? `✅ ${data.message}` : `❌ ${data.error}`,
      res.ok ? "success" : "error"
    );
  } catch (err) {
    showToast("Erro ao testar Minecraft", "error");
  }
}

// ===== EMAIL =====

async function saveEmail() {
  const smtpServer = document.getElementById("email-smtp").value.trim();
  const port = parseInt(document.getElementById("email-port").value);
  const email = document.getElementById("email-address").value.trim();
  const password = document.getElementById("email-password").value.trim();

  if (!email || !password) {
    showToast("Preencha o Email e a Senha", "warning");
    return;
  }

  try {
    const res = await fetch("/api/integrations/email/setup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ smtp_server: smtpServer, port, email, password }),
    });

    const data = await res.json();

    if (res.ok) {
      showToast("✅ Email configurado com sucesso!", "success");
      loadIntegrationsStatus();
    } else {
      showToast(`❌ ${data.error}`, "error");
    }
  } catch (err) {
    console.error("Erro ao salvar Email:", err);
    showToast("Erro de conexão", "error");
  }
}

async function testEmail() {
  try {
    const res = await fetch("/api/integrations/email/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        subject: "Teste de Integração - Twitch Bot",
        body: "Este é um email de teste da integração com o Twitch Bot! 🎮",
      }),
    });

    const data = await res.json();
    showToast(
      res.ok ? `✅ ${data.message}` : `❌ ${data.error}`,
      res.ok ? "success" : "error"
    );
  } catch (err) {
    showToast("Erro ao testar Email", "error");
  }
}

// ===== TWITCH API =====

async function saveTwitchAPI() {
  const clientId = document.getElementById("twitch-client-id").value.trim();
  const clientSecret = document
    .getElementById("twitch-client-secret")
    .value.trim();

  if (!clientId || !clientSecret) {
    showToast("Preencha o Client ID e Client Secret", "warning");
    return;
  }

  try {
    const res = await fetch("/api/integrations/twitch-api/setup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client_id: clientId,
        client_secret: clientSecret,
      }),
    });

    const data = await res.json();

    if (res.ok) {
      showToast("✅ Twitch API configurada com sucesso!", "success");
      loadIntegrationsStatus();
    } else {
      showToast(`❌ ${data.error}`, "error");
    }
  } catch (err) {
    console.error("Erro ao salvar Twitch API:", err);
    showToast("Erro de conexão", "error");
  }
}

// ===== RECONHECIMENTO DE VOZ =====

function initVoiceRecognition() {
  if (
    !("webkitSpeechRecognition" in window) &&
    !("SpeechRecognition" in window)
  ) {
    console.warn("⚠️ Navegador não suporta reconhecimento de voz");
    return;
  }

  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;
  voiceRecognition = new SpeechRecognition();

  voiceRecognition.continuous = true;
  voiceRecognition.interimResults = false;
  voiceRecognition.lang = "pt-BR";

  voiceRecognition.onresult = (event) => {
    const last = event.results.length - 1;
    const text = event.results[last][0].transcript.toLowerCase();
    console.log("🎤 Reconhecido:", text);

    if (text.includes("bot")) {
      processVoiceCommand(text);
    }
  };

  voiceRecognition.onerror = (event) => {
    console.error("Erro no reconhecimento:", event.error);
  };
}

function toggleVoice() {
  voiceEnabled = !voiceEnabled;
  const btn = document.getElementById("toggle-voice");
  const status = document.getElementById("voice-status");

  if (voiceEnabled) {
    if (voiceRecognition) {
      voiceRecognition.start();
      btn.textContent = "🔴 Desativar Reconhecimento";
      btn.className =
        "w-full bg-green-600 hover:bg-green-700 py-2 rounded-lg transition";
      status.textContent = "🟢 Escutando";
      status.className = "bg-green-600 text-xs px-3 py-1 rounded-full";
      showToast("Reconhecimento de voz ativado!", "success");
    } else {
      showToast("Reconhecimento de voz não disponível", "error");
      voiceEnabled = false;
    }
  } else {
    if (voiceRecognition) {
      voiceRecognition.stop();
    }
    btn.textContent = "🎤 Ativar Reconhecimento";
    btn.className =
      "w-full bg-red-600 hover:bg-red-700 py-2 rounded-lg transition";
    status.textContent = "🔴 Desativado";
    status.className = "bg-red-600 text-xs px-3 py-1 rounded-full";
    showToast("Reconhecimento de voz desativado", "info");
  }
}

function processVoiceCommand(text) {
  console.log("🎯 Processando comando:", text);
  // Comandos já implementados no dashboard.js
  showToast(`Comando reconhecido: ${text}`, "info");
}

// ===== IMPORTAÇÃO DE ARQUIVOS =====

function importFile(type) {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = type === "streamelements" ? ".csv" : ".json";

  input.onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const endpoint =
      type === "streamelements"
        ? "/api/import/streamelements"
        : "/api/import/nightbot";

    try {
      showToast("⏳ Importando...", "info");

      const res = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        showToast(
          `✅ ${data.imported} itens importados com sucesso!`,
          "success"
        );
      } else {
        showToast(`❌ ${data.error}`, "error");
      }
    } catch (err) {
      console.error("Erro ao importar:", err);
      showToast("Erro ao importar arquivo", "error");
    }
  };

  input.click();
}

// ===== TOAST NOTIFICATIONS =====

function showToast(message, type = "info") {
  const colors = {
    success: "bg-green-600",
    error: "bg-red-600",
    warning: "bg-yellow-600",
    info: "bg-blue-600",
  };

  const toast = document.createElement("div");
  toast.className = `fixed bottom-8 right-8 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50`;
  toast.textContent = message;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = "opacity 0.3s";
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Exportar funções globais
window.toggleVoice = toggleVoice;
window.saveDiscord = saveDiscord;
window.testDiscord = testDiscord;
window.saveMinecraft = saveMinecraft;
window.testMinecraft = testMinecraft;
window.saveEmail = saveEmail;
window.testEmail = testEmail;
window.saveTwitchAPI = saveTwitchAPI;
