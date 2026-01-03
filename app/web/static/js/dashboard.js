// Dashboard JavaScript - Twitch Bot (VERSÃO MELHORADA)
// Localização: app/web/static/js/dashboard.js

const socket = io({
  transports: ["websocket", "polling"],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: Infinity,
  timeout: 30000,
  autoConnect: true,
});

// ===== ESTADO GLOBAL =====

const AppState = {
  currentTab: "chat",
  debugMode: localStorage.getItem("debug_mode") === "true" || false,
  voiceEnabled: false,
  voiceRecognition: null,
  recentRaids: [],
  stats: {
    connected_channels: [],
    total_users: 0,
    total_messages: 0,
    total_points: 0,
  },
};

// ===== INICIALIZAÇÃO =====

document.addEventListener("DOMContentLoaded", () => {
  setupWebSocket();
  loadStats();
  loadAutoResponses();
  setupKeyboardShortcuts();
  initializeDebugMode();
  initializeVoiceRecognition();

  // Restaurar canal selecionado
  const chatChannel = document.getElementById("chat-channel");
  if (chatChannel) {
    chatChannel.addEventListener("change", (e) => {
      const selectedChannel = e.target.value;
      if (selectedChannel) {
        localStorage.setItem("selected_channel", selectedChannel);
        debugLog("💾 Canal salvo:", selectedChannel);
      }
    });
  }
});

// ===== DEBUG MODE =====

function initializeDebugMode() {
  // Criar botão de debug no navbar
  const navbar = document.querySelector("nav .flex.items-center.space-x-4");
  if (navbar) {
    const debugBtn = document.createElement("button");
    debugBtn.id = "debug-toggle";
    debugBtn.className = `px-4 py-2 ${
      AppState.debugMode ? "bg-green-600" : "bg-gray-700"
    } hover:bg-gray-600 rounded-lg transition flex items-center gap-2 text-sm`;
    debugBtn.innerHTML = `
      <span>🐛</span>
      <span>${AppState.debugMode ? "Debug ON" : "Debug OFF"}</span>
    `;
    debugBtn.onclick = toggleDebugMode;
    navbar.insertBefore(debugBtn, navbar.firstChild);
  }

  if (AppState.debugMode) {
    console.log("🐛 Debug mode ATIVADO");
    createDebugConsole();
  }
}

function toggleDebugMode() {
  AppState.debugMode = !AppState.debugMode;
  localStorage.setItem("debug_mode", AppState.debugMode.toString());

  const btn = document.getElementById("debug-toggle");
  if (btn) {
    btn.className = `px-4 py-2 ${
      AppState.debugMode ? "bg-green-600" : "bg-gray-700"
    } hover:bg-gray-600 rounded-lg transition flex items-center gap-2 text-sm`;
    btn.innerHTML = `
      <span>🐛</span>
      <span>${AppState.debugMode ? "Debug ON" : "Debug OFF"}</span>
    `;
  }

  if (AppState.debugMode) {
    console.log("🐛 Debug mode ATIVADO");
    createDebugConsole();
    showToast("Debug mode ativado", "success");
  } else {
    console.log("🐛 Debug mode DESATIVADO");
    removeDebugConsole();
    showToast("Debug mode desativado", "info");
  }
}

function createDebugConsole() {
  if (document.getElementById("debug-console")) return;

  const debugDiv = document.createElement("div");
  debugDiv.id = "debug-console";
  debugDiv.className =
    "fixed bottom-4 right-4 w-96 h-64 bg-gray-900 border border-purple-500 rounded-lg shadow-2xl z-50 flex flex-col";
  debugDiv.innerHTML = `
    <div class="bg-purple-600 px-4 py-2 rounded-t-lg flex justify-between items-center">
      <span class="font-bold">🐛 Debug Console</span>
      <button onclick="removeDebugConsole()" class="text-white hover:text-red-400">✕</button>
    </div>
    <div id="debug-output" class="flex-1 p-2 overflow-y-auto text-xs font-mono text-green-400"></div>
    <div class="bg-gray-800 px-2 py-1 text-xs text-gray-400">
      Stats: ${AppState.stats.total_users} users | ${AppState.stats.total_messages} msgs
    </div>
  `;
  document.body.appendChild(debugDiv);

  debugLog("Debug console inicializado");
}

function removeDebugConsole() {
  const console = document.getElementById("debug-console");
  if (console) console.remove();
}

function debugLog(...args) {
  if (!AppState.debugMode) return;

  const output = document.getElementById("debug-output");
  if (output) {
    const timestamp = new Date().toLocaleTimeString();
    const line = document.createElement("div");
    line.className = "mb-1";
    line.textContent = `[${timestamp}] ${args.join(" ")}`;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;

    // Limitar a 100 linhas
    while (output.children.length > 100) {
      output.removeChild(output.firstChild);
    }
  }

  console.log(...args);
}

// ===== RECONHECIMENTO DE VOZ =====

function initializeVoiceRecognition() {
  // Verificar se o navegador suporta
  if (
    !("webkitSpeechRecognition" in window) &&
    !("SpeechRecognition" in window)
  ) {
    debugLog("⚠️ Navegador não suporta reconhecimento de voz");
    return;
  }

  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;
  AppState.voiceRecognition = new SpeechRecognition();

  AppState.voiceRecognition.continuous = true;
  AppState.voiceRecognition.interimResults = false;
  AppState.voiceRecognition.lang = "pt-BR";

  AppState.voiceRecognition.onresult = (event) => {
    const last = event.results.length - 1;
    const text = event.results[last][0].transcript.toLowerCase();

    debugLog("🎤 Reconhecido:", text);

    // Processar comando de voz
    if (text.includes("bot")) {
      processVoiceCommand(text);
    }
  };

  AppState.voiceRecognition.onerror = (event) => {
    console.error("Erro no reconhecimento de voz:", event.error);
    debugLog("❌ Erro de voz:", event.error);

    if (event.error === "no-speech") {
      // Silencioso, tentar novamente
      if (AppState.voiceEnabled) {
        setTimeout(() => {
          if (AppState.voiceEnabled) {
            AppState.voiceRecognition.start();
          }
        }, 100);
      }
    }
  };

  AppState.voiceRecognition.onend = () => {
    debugLog("🎤 Reconhecimento parou");

    // Reiniciar se ainda estiver ativado
    if (AppState.voiceEnabled) {
      setTimeout(() => {
        if (AppState.voiceEnabled) {
          AppState.voiceRecognition.start();
        }
      }, 100);
    }
  };

  // Criar botão de voz no dashboard
  createVoiceButton();
}

function createVoiceButton() {
  const navbar = document.querySelector("nav .flex.items-center.space-x-4");
  if (!navbar) return;

  const voiceBtn = document.createElement("button");
  voiceBtn.id = "voice-toggle";
  voiceBtn.className =
    "px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition flex items-center gap-2 text-sm";
  voiceBtn.innerHTML = `
    <span>🎤</span>
    <span>Voz OFF</span>
  `;
  voiceBtn.onclick = toggleVoiceRecognition;

  // Inserir antes do botão de logout
  const logoutBtn = navbar.querySelector('a[href="/logout"]');
  if (logoutBtn) {
    navbar.insertBefore(voiceBtn, logoutBtn);
  } else {
    navbar.appendChild(voiceBtn);
  }
}

async function toggleVoiceRecognition() {
  if (!AppState.voiceRecognition) {
    showToast("Reconhecimento de voz não disponível", "error");
    return;
  }

  const btn = document.getElementById("voice-toggle");

  if (AppState.voiceEnabled) {
    // Desativar
    AppState.voiceEnabled = false;
    AppState.voiceRecognition.stop();

    btn.className =
      "px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition flex items-center gap-2 text-sm";
    btn.innerHTML = `
      <span>🎤</span>
      <span>Voz OFF</span>
    `;

    debugLog("🎤 Reconhecimento de voz DESATIVADO");
    showToast("Reconhecimento de voz desativado", "info");
  } else {
    // Ativar
    try {
      await AppState.voiceRecognition.start();
      AppState.voiceEnabled = true;

      btn.className =
        "px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition flex items-center gap-2 text-sm animate-pulse";
      btn.innerHTML = `
        <span>🎤</span>
        <span>Voz ON</span>
      `;

      debugLog("🎤 Reconhecimento de voz ATIVADO");
      showToast(
        "Reconhecimento de voz ativado! Diga 'bot' + comando",
        "success"
      );
    } catch (error) {
      console.error("Erro ao ativar reconhecimento de voz:", error);
      showToast("Erro ao ativar reconhecimento de voz", "error");
    }
  }
}

function processVoiceCommand(text) {
  debugLog("🎯 Processando comando:", text);

  // Comandos disponíveis
  if (text.includes("ler chat")) {
    readLastMessages();
    speak("Lendo últimas mensagens");
  } else if (
    text.includes("quantos viewers") ||
    text.includes("quantos usuários")
  ) {
    announceViewers();
  } else if (text.includes("obrigado")) {
    sendThankYouMessage();
    speak("Obrigado a todos!");
  } else if (text.includes("limpar chat")) {
    clearChat();
    speak("Chat limpo");
  } else if (text.includes("enviar mensagem")) {
    const message = text.split("enviar mensagem")[1]?.trim();
    if (message) {
      sendVoiceMessage(message);
    }
  } else {
    debugLog("⚠️ Comando não reconhecido");
  }
}

function speak(text) {
  if ("speechSynthesis" in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "pt-BR";
    utterance.rate = 1.0;
    window.speechSynthesis.speak(utterance);
  }
}

function readLastMessages() {
  const chatDiv = document.getElementById("chat-messages");
  const messages = Array.from(chatDiv.children).slice(-3);

  messages.forEach((msg) => {
    const text = msg.textContent;
    speak(text);
  });
}

function announceViewers() {
  const count = AppState.stats.total_users;
  speak(`Temos ${count} usuários ativos no chat`);
  showToast(`${count} usuários ativos`, "info");
}

function sendThankYouMessage() {
  const channel = document.getElementById("chat-channel").value;
  if (!channel) {
    showToast("Selecione um canal primeiro", "warning");
    return;
  }

  fetch("/api/bot/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      channel: channel,
      message: "Muito obrigado a todos por assistirem! ❤️",
    }),
  });
}

function sendVoiceMessage(message) {
  const channel = document.getElementById("chat-channel").value;
  if (!channel) {
    showToast("Selecione um canal primeiro", "warning");
    return;
  }

  fetch("/api/bot/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ channel: channel, message: message }),
  });

  speak("Mensagem enviada");
}

function clearChat() {
  const chatDiv = document.getElementById("chat-messages");
  chatDiv.innerHTML =
    '<div class="text-gray-500 text-center py-8">Chat limpo</div>';
}

// ===== WEBSOCKET =====

function setupWebSocket() {
  debugLog("✅ Conectado ao servidor WebSocket");
  updateStatus("online");
  addLogMessage({
    level: "success",
    message: "Conectado ao servidor WebSocket",
    timestamp: new Date().toLocaleTimeString(),
  });

  socket.on("disconnect", (reason) => {
    debugLog("❌ Desconectado do servidor:", reason);
    updateStatus("offline");
    addLogMessage({
      level: "error",
      message: `Desconectado: ${reason}`,
      timestamp: new Date().toLocaleTimeString(),
    });
  });
  socket.emit("request_stats");
  
  socket.on("reconnect", (attemptNumber) => {
    debugLog("🔄 Reconectado após", attemptNumber, "tentativas");
    addLogMessage({
      level: "success",
      message: `Reconectado ao servidor (tentativa ${attemptNumber})`,
      timestamp: new Date().toLocaleTimeString(),
    });
    loadStats();
  });

  socket.on("chat_message", (data) => {
    debugLog("📨 Mensagem recebida:", data);
    addChatMessage(data);
  });

  socket.on("log_message", (data) => {
    debugLog("📋 Log recebido:", data);
    addLogMessage(data);
  });

  socket.on("status_change", (data) => {
    handleStatusChange(data);
  });

  socket.on("stats_update", (data) => {
    updateStatsDisplay(data);
  });

  socket.on("raid_received", (data) => {
    handleRaidNotification(data);
  });
}

function updateStatus(status) {
  const indicator = document.getElementById("status-indicator");
  const dot = indicator.querySelector("div");
  const text = indicator.querySelector("span");

  if (status === "online") {
    dot.className = "w-3 h-3 bg-green-500 rounded-full animate-pulse";
    text.textContent = "Online";
  } else {
    dot.className = "w-3 h-3 bg-red-500 rounded-full animate-pulse";
    text.textContent = "Offline";
  }
}

// ===== CHAT =====

async function sendMessage() {
  const channelSelect = document.getElementById("chat-channel");
  const input = document.getElementById("chat-input");

  const channel = channelSelect.value;
  const message = input.value.trim();

  if (!channel || !message) {
    showToast("Selecione um canal e digite uma mensagem", "warning");
    return;
  }

  try {
    const res = await fetch("/api/bot/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel, message }),
    });

    if (res.ok) {
      input.value = "";
      debugLog("✅ Mensagem enviada:", message);
    } else {
      showToast("Erro ao enviar mensagem", "error");
    }
  } catch (err) {
    console.error("Erro ao enviar mensagem:", err);
    showToast("Erro de conexão", "error");
  }
}

function addChatMessage(data) {
  const container = document.getElementById("chat-messages");

  const placeholder = container.querySelector(".text-gray-500.text-center");
  if (placeholder) {
    container.innerHTML = "";
  }

  const { channel, username, message, timestamp, isOwn } = data;

  const msgEl = document.createElement("div");
  msgEl.className = `mb-2 ${isOwn ? "text-purple-400" : "text-gray-300"}`;
  msgEl.innerHTML = `
    <span class="text-gray-500">[${timestamp}]</span>
    <span class="text-blue-400">[${channel}]</span>
    <span class="font-bold">${username}:</span>
    <span>${message || ""}</span>
  `;

  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;

  debugLog(`📨 [${channel}] ${username}: ${message}`);
}

// ===== STATS =====

async function loadStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    updateStatsDisplay(data);
  } catch (err) {
    console.error("Erro ao carregar stats:", err);
  }
}

function updateStatsDisplay(data) {
  AppState.stats = data;

  document.getElementById("active-channels").textContent =
    data.connected_channels.length;
  document.getElementById("total-users").textContent = data.total_users;
  document.getElementById("total-messages").textContent = data.total_messages;

  const summary = document.getElementById("stats-summary");
  if (summary) {
    summary.innerHTML = `
      <div>👥 Usuários: <span class="text-white">${data.total_users}</span></div>
      <div>💬 Mensagens: <span class="text-white">${data.total_messages}</span></div>
      <div>💰 Pontos: <span class="text-white">${data.total_points}</span></div>
    `;
  }

  updateChannelSelect(data.connected_channels);

  // Atualizar debug console
  const debugStats = document.querySelector("#debug-console .bg-gray-800");
  if (debugStats) {
    debugStats.textContent = `Stats: ${data.total_users} users | ${data.total_messages} msgs`;
  }
}

function updateChannelSelect(connectedChannels) {
  const select = document.getElementById("chat-channel");
  const currentValue = select.value;

  const existingChannels = Array.from(select.options)
    .map((opt) => opt.value)
    .filter((val) => val !== "");

  const channelsChanged =
    connectedChannels.length !== existingChannels.length ||
    !connectedChannels.every((ch) => existingChannels.includes(ch));

  if (channelsChanged) {
    debugLog("🔄 Atualizando lista de canais...");

    select.innerHTML = '<option value="">Selecione canal...</option>';
    connectedChannels.forEach((channel) => {
      const option = document.createElement("option");
      option.value = channel;
      option.textContent = `📺 ${channel}`;
      select.appendChild(option);
    });

    if (currentValue && connectedChannels.includes(currentValue)) {
      select.value = currentValue;
    } else {
      const savedChannel = localStorage.getItem("selected_channel");
      if (savedChannel && connectedChannels.includes(savedChannel)) {
        select.value = savedChannel;
      } else if (connectedChannels.length === 1) {
        select.value = connectedChannels[0];
        localStorage.setItem("selected_channel", connectedChannels[0]);
      }
    }
  }
}

// ===== LOGS =====

function addLogMessage(data) {
  const container = document.getElementById("log-messages");
  const { level, message, timestamp } = data;

  const colors = {
    success: "text-green-400",
    error: "text-red-400",
    warning: "text-yellow-400",
    info: "text-blue-400",
    bot: "text-purple-400",
    event: "text-pink-400",
    debug: "text-cyan-400",
  };

  const logEl = document.createElement("div");
  logEl.className = `mb-1 ${colors[level] || "text-gray-400"}`;
  logEl.textContent = `[${timestamp}] ${message}`;

  container.appendChild(logEl);
  container.scrollTop = container.scrollHeight;

  while (container.children.length > 1000) {
    container.removeChild(container.firstChild);
  }
}

function clearLogs() {
  document.getElementById("log-messages").innerHTML = "";
  addLogMessage({
    level: "info",
    message: "Logs limpos",
    timestamp: new Date().toLocaleTimeString(),
  });
}

// ===== AUTO RESPONSES =====

async function addAutoResponse() {
  const trigger = document.getElementById("trigger-input").value.trim();
  const response = document.getElementById("response-input").value.trim();

  if (!trigger || !response) {
    showToast("Preencha ambos os campos", "warning");
    return;
  }

  try {
    const res = await fetch("/api/auto-response/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trigger, response }),
    });

    if (res.ok) {
      document.getElementById("trigger-input").value = "";
      document.getElementById("response-input").value = "";

      showToast("Resposta adicionada com sucesso!", "success");
      loadAutoResponses();
    }
  } catch (err) {
    console.error("Erro ao adicionar resposta:", err);
    showToast("Erro ao adicionar resposta", "error");
  }
}

async function loadAutoResponses() {
  try {
    const res = await fetch("/api/auto-response/list");
    const data = await res.json();

    const container = document.getElementById("responses-list");
    container.innerHTML = "";

    const responses = data.responses || {};

    if (Object.keys(responses).length === 0) {
      container.innerHTML =
        '<div class="text-gray-500 text-center py-8">Nenhuma resposta automática configurada</div>';
      return;
    }

    for (const [trigger, response] of Object.entries(responses)) {
      const itemEl = document.createElement("div");
      itemEl.className =
        "bg-gray-800 rounded-lg p-4 mb-2 flex items-center justify-between hover:bg-gray-700 transition";
      itemEl.innerHTML = `
        <div class="flex-1">
          <div class="text-sm text-gray-400 mb-1">Gatilho:</div>
          <div class="font-mono text-purple-400 mb-2">"${trigger}"</div>
          <div class="text-sm text-gray-400 mb-1">Resposta:</div>
          <div class="font-mono text-green-400">"${response}"</div>
        </div>
        <button 
          onclick="removeAutoResponse('${trigger.replace(/'/g, "\\'")}')"
          class="bg-red-600 hover:bg-red-700 px-4 py-2 rounded transition text-sm"
        >
          🗑️ Remover
        </button>
      `;
      container.appendChild(itemEl);
    }
  } catch (err) {
    console.error("Erro ao carregar respostas:", err);
  }
}

async function removeAutoResponse(trigger) {
  if (!confirm(`Remover resposta automática para "${trigger}"?`)) return;

  try {
    const res = await fetch("/api/auto-response/remove", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trigger }),
    });

    if (res.ok) {
      showToast("Resposta removida com sucesso!", "success");
      loadAutoResponses();
    } else {
      showToast("Erro ao remover resposta", "error");
    }
  } catch (err) {
    console.error("Erro ao remover resposta:", err);
    showToast("Erro ao remover resposta", "error");
  }
}

// ===== STREAMERS =====

async function addStreamer() {
  const input = document.getElementById("new-streamer");
  const username = input.value.trim();

  if (!username) return;

  try {
    const res = await fetch("/api/streamers/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username }),
    });

    const data = await res.json();

    if (res.ok) {
      input.value = "";
      showToast(`Streamer ${username} adicionado!`, "success");
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast(data.error, "error");
    }
  } catch (err) {
    console.error("Erro ao adicionar streamer:", err);
    showToast("Erro de conexão", "error");
  }
}

async function removeStreamer(username) {
  if (!confirm(`Remover ${username}?`)) return;

  try {
    const res = await fetch("/api/streamers/remove", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username }),
    });

    if (res.ok) {
      showToast(`Streamer ${username} removido!`, "success");
      setTimeout(() => location.reload(), 1000);
    }
  } catch (err) {
    console.error("Erro ao remover streamer:", err);
  }
}

async function toggleBot(channel) {
  const isConnected = AppState.stats.connected_channels.includes(channel);

  // 🔍 DEBUG: Verificar o valor do channel
  console.log("🔍 toggleBot chamado com channel:", channel);
  console.log("🔍 isConnected:", isConnected);
  console.log("🔍 AppState.stats:", AppState.stats);

  try {
    const endpoint = isConnected ? "/api/bot/stop" : "/api/bot/start";
    const payload = { channel };

    // 🔍 DEBUG: Ver o que está sendo enviado
    console.log("🔍 Endpoint:", endpoint);
    console.log("🔍 Payload:", payload);

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel }),
    });

    const data = await res.json();

    // 🔍 DEBUG: Ver a resposta
    console.log("🔍 Response status:", res.status);
    console.log("🔍 Response data:", data);

    if (res.ok) {
      const action = isConnected ? "Desconectado" : "Conectado";
      showToast(`${action} de ${channel}`, "success");
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast(data.error, "error");
    }
  } catch (err) {
    console.error("Erro ao controlar bot:", err);
    showToast("Erro de conexão", "error");
  }
}

function handleStatusChange(data) {
  const { channel, status } = data;

  const channelEl = document.querySelector(`[data-channel="${channel}"]`);
  if (channelEl) {
    const dot = channelEl.querySelector(".w-2");
    if (status === "online") {
      dot.className = "w-2 h-2 bg-green-500 rounded-full";
    } else {
      dot.className = "w-2 h-2 bg-gray-500 rounded-full";
    }
  }

  loadStats();
}

// ===== RAIDS =====

function handleRaidNotification(data) {
  const { channel, raider, viewers, timestamp } = data;

  AppState.recentRaids.unshift({ channel, raider, viewers, timestamp });
  if (AppState.recentRaids.length > 5) AppState.recentRaids.pop();

  showRaidNotification(raider, viewers, channel);

  addLogMessage({
    level: "event",
    message: `🎉 RAID de ${raider} com ${viewers} viewers no canal ${channel}!`,
    timestamp: timestamp,
  });

  addChatMessage({
    channel: channel,
    username: "🎉 RAID",
    message: `${raider} chegou com ${viewers} viewers!`,
    timestamp: timestamp,
    isRaid: true,
  });

  loadStats();
}

function showRaidNotification(raider, viewers, channel) {
  const notification = document.createElement("div");
  notification.className =
    "fixed top-20 right-8 bg-gradient-to-r from-purple-600 to-pink-600 text-white px-8 py-6 rounded-xl shadow-2xl z-50 animate-bounce";
  notification.innerHTML = `
    <div class="flex items-center gap-4">
      <div class="text-5xl">🎉</div>
      <div>
        <div class="text-2xl font-bold">RAID INCOMING!</div>
        <div class="text-lg">${raider} trouxe ${viewers} viewers!</div>
        <div class="text-sm opacity-75">Canal: ${channel}</div>
      </div>
    </div>
  `;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.transition = "opacity 0.5s";
    notification.style.opacity = "0";
    setTimeout(() => notification.remove(), 500);
  }, 10000);
}

// ===== TABS =====

function switchTab(tab) {
  AppState.currentTab = tab;

  document.querySelectorAll('[id^="content-"]').forEach((el) => {
    el.classList.add("hidden");
  });

  document.getElementById(`content-${tab}`).classList.remove("hidden");

  document.querySelectorAll('[id^="tab-"]').forEach((btn) => {
    btn.classList.remove("bg-purple-600");
    btn.classList.add("hover:bg-gray-700/50");
  });

  const activeBtn = document.getElementById(`tab-${tab}`);
  activeBtn.classList.add("bg-purple-600");
  activeBtn.classList.remove("hover:bg-gray-700/50");
}

// ===== KEYBOARD SHORTCUTS =====

function setupKeyboardShortcuts() {
  document.getElementById("chat-input").addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });

  document.getElementById("new-streamer").addEventListener("keypress", (e) => {
    if (e.key === "Enter") addStreamer();
  });

  // Atalhos globais
  document.addEventListener("keydown", (e) => {
    // Ctrl+D = Toggle Debug
    if (e.ctrlKey && e.key === "d") {
      e.preventDefault();
      toggleDebugMode();
    }

    // Ctrl+V = Toggle Voice
    if (e.ctrlKey && e.key === "v") {
      e.preventDefault();
      toggleVoiceRecognition();
    }

    // Ctrl+L = Limpar Logs
    if (e.ctrlKey && e.key === "l") {
      e.preventDefault();
      clearLogs();
    }
  });
}

// ===== TOAST NOTIFICATIONS =====

function showToast(message, type = "info") {
  const colors = {
    success: "bg-green-600",
    error: "bg-red-600",
    warning: "bg-yellow-600",
    info: "bg-blue-600",
  };

  const icons = {
    success: "✅",
    error: "❌",
    warning: "⚠️",
    info: "ℹ️",
  };

  const toast = document.createElement("div");
  toast.className = `fixed bottom-8 right-8 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2`;
  toast.innerHTML = `
    <span>${icons[type]}</span>
    <span>${message}</span>
  `;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = "opacity 0.3s";
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ===== AUTO-ATUALIZAÇÃO =====

// Atualizar stats a cada 5 segundos
setInterval(loadStats, 30000);

// Cleanup ao sair
window.addEventListener("beforeunload", () => {
  if (AppState.voiceEnabled) {
    AppState.voiceRecognition.stop();
  }
});

// ===== EXPORTS PARA CONSOLE =====
window.AppState = AppState;
window.debugLog = debugLog;
window.toggleDebugMode = toggleDebugMode;
window.toggleVoiceRecognition = toggleVoiceRecognition;
