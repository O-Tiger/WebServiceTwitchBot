// Dashboard JavaScript - Twitch Bot (VERSÃO CORRIGIDA COMPLETA)
const socket = io({
  transports: ["websocket", "polling"], // Websocket primeiro
  reconnection: true, // Reconectar automaticamente
  reconnectionDelay: 1000, // Esperar 1s antes de reconectar
  reconnectionDelayMax: 5000, // Máximo 5s entre tentativas
  reconnectionAttempts: Infinity, // Tentar infinitamente
  timeout: 30000, // Timeout de 30s
  autoConnect: true, // Conectar automaticamente
});

// Estado global
let currentTab = "chat";
let recentRaids = [];
let stats = {
  connected_channels: [],
  total_users: 0,
  total_messages: 0,
  total_points: 0,
};

// Inicialização
document.addEventListener("DOMContentLoaded", () => {
  setupWebSocket();
  loadStats();
  loadAutoResponses();
  setupKeyboardShortcuts();

  // ✅ Salvar canal selecionado quando mudar
  const chatChannel = document.getElementById("chat-channel");
  if (chatChannel) {
    chatChannel.addEventListener("change", (e) => {
      const selectedChannel = e.target.value;
      if (selectedChannel) {
        localStorage.setItem("selected_channel", selectedChannel);
        console.log("💾 Canal salvo:", selectedChannel);
      }
    });
  }
});

// ===== WEBSOCKET =====

function setupWebSocket() {
  socket.on("connect", () => {
    console.log("✅ Conectado ao servidor");
    updateStatus("online");
    addLogMessage({
      level: "success",
      message: "Conectado ao servidor WebSocket",
      timestamp: new Date().toLocaleTimeString(),
    });
  });

  socket.on("disconnect", (reason) => {
    console.log("❌ Desconectado do servidor - Razão:", reason);
    updateStatus("offline");
    addLogMessage({
      level: "error",
      message: `Desconectado: ${reason}`,
      timestamp: new Date().toLocaleTimeString(),
    });
  });

  socket.on("reconnect", (attemptNumber) => {
    console.log("🔄 Reconectado após", attemptNumber, "tentativas");
    addLogMessage({
      level: "success",
      message: `Reconectado ao servidor (tentativa ${attemptNumber})`,
      timestamp: new Date().toLocaleTimeString(),
    });
    loadStats(); // Recarregar dados após reconexão
  });

  socket.on("reconnect_attempt", (attemptNumber) => {
    console.log("🔄 Tentando reconectar...", attemptNumber);
  });

  socket.on("reconnect_error", (error) => {
    console.error("❌ Erro ao reconectar:", error);
  });

  socket.on("reconnect_failed", () => {
    console.error("❌ Falha ao reconectar após todas as tentativas");
    addLogMessage({
      level: "error",
      message: "Falha ao reconectar ao servidor",
      timestamp: new Date().toLocaleTimeString(),
    });
  });

  socket.on("connect_error", (error) => {
    console.error("❌ Erro de conexão:", error);
  });
  
  socket.on("chat_message", (data) => {
    console.log("📨 Mensagem recebida:", data);
    addChatMessage(data);
  });

  socket.on("log_message", (data) => {
    console.log("📝 Log recebido:", data);
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
      addLogMessage({
        level: "success",
        message: `Streamer ${username} adicionado`,
        timestamp: new Date().toLocaleTimeString(),
      });
      location.reload();
    } else {
      alert(data.error);
      addLogMessage({
        level: "error",
        message: `Erro ao adicionar ${username}: ${data.error}`,
        timestamp: new Date().toLocaleTimeString(),
      });
    }
  } catch (err) {
    console.error("Erro ao adicionar streamer:", err);
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
      addLogMessage({
        level: "warning",
        message: `Streamer ${username} removido`,
        timestamp: new Date().toLocaleTimeString(),
      });
      location.reload();
    }
  } catch (err) {
    console.error("Erro ao remover streamer:", err);
  }
}

// ===== BOT CONTROL =====

async function toggleBot(channel) {
  const isConnected = stats.connected_channels.includes(channel);

  try {
    const endpoint = isConnected ? "/api/bot/stop" : "/api/bot/start";
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel }),
    });

    const data = await res.json();

    if (res.ok) {
      addLogMessage({
        level: "success",
        message: `${isConnected ? "Desconectado" : "Conectado"} - ${channel}`,
        timestamp: new Date().toLocaleTimeString(),
      });

      // Atualizar UI após 1s
      setTimeout(() => location.reload(), 1000);
    } else {
      alert(data.error);
      addLogMessage({
        level: "error",
        message: `Erro ao ${isConnected ? "desconectar" : "conectar"}: ${
          data.error
        }`,
        timestamp: new Date().toLocaleTimeString(),
      });
    }
  } catch (err) {
    console.error("Erro ao controlar bot:", err);
  }
}

function handleStatusChange(data) {
  const { channel, status } = data;

  // Atualizar indicador visual
  const channelEl = document.querySelector(`[data-channel="${channel}"]`);
  if (channelEl) {
    const dot = channelEl.querySelector(".w-2");
    if (status === "online") {
      dot.className = "w-2 h-2 bg-green-500 rounded-full";
    } else {
      dot.className = "w-2 h-2 bg-gray-500 rounded-full";
    }
  }

  addLogMessage({
    level: "info",
    message: `Canal ${channel} está ${status}`,
    timestamp: new Date().toLocaleTimeString(),
  });

  loadStats();
}

// ===== CHAT =====

async function sendMessage() {
  const channelSelect = document.getElementById("chat-channel");
  const input = document.getElementById("chat-input");

  const channel = channelSelect.value;
  const message = input.value.trim();

  if (!channel || !message) {
    alert("Selecione um canal e digite uma mensagem");
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
      // A mensagem será adicionada via WebSocket
    } else {
      alert("Erro ao enviar mensagem");
    }
  } catch (err) {
    console.error("Erro ao enviar mensagem:", err);
  }
}

function addChatMessage(data) {
  const container = document.getElementById("chat-messages");

  // ✅ Limpar placeholder apenas UMA VEZ
  const placeholder = container.querySelector(".text-gray-500.text-center");
  if (placeholder) {
    console.log("🧹 Limpando placeholder inicial...");
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

  // ✅ ADICIONAR mensagem (não substituir)
  container.appendChild(msgEl);

  // ✅ Auto-scroll para a última mensagem
  container.scrollTop = container.scrollHeight;

  console.log(`📨 Mensagem adicionada: [${channel}] ${username}: ${message}`);
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
  };

  const logEl = document.createElement("div");
  logEl.className = `mb-1 ${colors[level] || "text-gray-400"}`;
  logEl.textContent = `[${timestamp}] ${message}`;

  container.appendChild(logEl);
  container.scrollTop = container.scrollHeight;

  // Limitar a 1000 logs
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
    alert("Preencha ambos os campos");
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

      addLogMessage({
        level: "success",
        message: `Resposta automática adicionada: "${trigger}" → "${response}"`,
        timestamp: new Date().toLocaleTimeString(),
      });

      loadAutoResponses();
    }
  } catch (err) {
    console.error("Erro ao adicionar resposta:", err);
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

    const data = await res.json();

    if (res.ok) {
      addLogMessage({
        level: "warning",
        message: `Resposta automática removida: "${trigger}"`,
        timestamp: new Date().toLocaleTimeString(),
      });

      loadAutoResponses();
      showSuccessToast("Resposta removida com sucesso!");
    } else {
      alert(data.error || "Erro ao remover resposta");
    }
  } catch (err) {
    console.error("Erro ao remover resposta:", err);
    alert("Erro ao remover resposta. Verifique o console.");
  }
}

function showSuccessToast(message) {
  const toast = document.createElement("div");
  toast.className =
    "fixed bottom-8 right-8 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50";
  toast.innerHTML = `
    <div class="flex items-center gap-2">
      <span>✅</span>
      <span>${message}</span>
    </div>
  `;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = "opacity 0.3s";
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
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
  stats = data;

  // Atualizar cards de estatísticas
  document.getElementById("active-channels").textContent =
    data.connected_channels.length;
  document.getElementById("total-users").textContent = data.total_users;
  document.getElementById("total-messages").textContent = data.total_messages;

  // Atualizar resumo na sidebar
  const summary = document.getElementById("stats-summary");
  summary.innerHTML = `
    <div>👥 Usuários: <span class="text-white">${data.total_users}</span></div>
    <div>💬 Mensagens: <span class="text-white">${data.total_messages}</span></div>
    <div>💰 Pontos: <span class="text-white">${data.total_points}</span></div>
  `;

  // ✅ CORREÇÃO: Atualizar select SEM destruir a seleção atual
  updateChannelSelect(data.connected_channels);
}

// ✅ NOVA FUNÇÃO: Atualiza o select de forma inteligente
function updateChannelSelect(connectedChannels) {
  const select = document.getElementById("chat-channel");
  const currentValue = select.value; // Salvar valor atual ANTES de qualquer mudança

  // Obter canais que já existem no select
  const existingChannels = Array.from(select.options)
    .map((opt) => opt.value)
    .filter((val) => val !== ""); // Remover option vazia

  // ✅ VERIFICAÇÃO 1: Os canais mudaram?
  const channelsChanged =
    connectedChannels.length !== existingChannels.length ||
    !connectedChannels.every((ch) => existingChannels.includes(ch));

  // ✅ SÓ RECONSTRUIR O SELECT SE OS CANAIS MUDARAM
  if (channelsChanged) {
    console.log("🔄 Canais mudaram, reconstruindo select...");

    // Reconstruir select
    select.innerHTML = '<option value="">Selecione canal...</option>';
    connectedChannels.forEach((channel) => {
      const option = document.createElement("option");
      option.value = channel;
      option.textContent = `📺 ${channel}`;
      select.appendChild(option);
    });

    // ✅ RESTAURAR SELEÇÃO ANTERIOR
    if (currentValue && connectedChannels.includes(currentValue)) {
      // Se o canal ainda existe, manter selecionado
      select.value = currentValue;
      console.log("✅ Canal mantido:", currentValue);
    } else {
      // Se o canal não existe mais, tentar localStorage
      const savedChannel = localStorage.getItem("selected_channel");

      if (savedChannel && connectedChannels.includes(savedChannel)) {
        select.value = savedChannel;
        console.log("✅ Canal restaurado do localStorage:", savedChannel);
      } else if (connectedChannels.length === 1) {
        // Se só tem 1 canal, selecionar automaticamente
        select.value = connectedChannels[0];
        localStorage.setItem("selected_channel", connectedChannels[0]);
        console.log(
          "✅ Canal único selecionado automaticamente:",
          connectedChannels[0]
        );
      }
    }
  } else {
    // ✅ CANAIS NÃO MUDARAM: Não fazer nada!
    console.log("✅ Canais inalterados, select mantido");
  }
}

// ===== TABS =====

function switchTab(tab) {
  currentTab = tab;

  // Ocultar todos os conteúdos
  document.querySelectorAll('[id^="content-"]').forEach((el) => {
    el.classList.add("hidden");
  });

  // Mostrar conteúdo selecionado
  document.getElementById(`content-${tab}`).classList.remove("hidden");

  // Atualizar botões
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
}

// Auto-atualizar stats a cada 5 segundos
setInterval(loadStats, 5000);

// ===== RAID NOTIFICATION =====

function handleRaidNotification(data) {
  const { channel, raider, viewers, timestamp } = data;

  // Adicionar ao histórico
  recentRaids.unshift({ channel, raider, viewers, timestamp });
  if (recentRaids.length > 5) recentRaids.pop();

  // Mostrar notificação visual
  showRaidNotification(raider, viewers, channel);

  // Log especial
  addLogMessage({
    level: "event",
    message: `🎉 RAID de ${raider} com ${viewers} viewers no canal ${channel}!`,
    timestamp: timestamp,
  });

  // Adicionar ao chat também
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

  // Remover após 10 segundos
  setTimeout(() => {
    notification.style.transition = "opacity 0.5s";
    notification.style.opacity = "0";
    setTimeout(() => notification.remove(), 500);
  }, 10000);
}
