// Import handler

document
  .getElementById("form-streamelements")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    await handleImport("streamelements", "/api/import/streamelements");
  });

document
  .getElementById("form-nightbot")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    await handleImport("nightbot", "/api/import/nightbot");
  });

async function handleImport(type, endpoint) {
  const fileInput = document.getElementById(`file-${type}`);
  const resultDiv = document.getElementById(`result-${type}`);

  if (!fileInput.files.length) {
    showResult(resultDiv, "Selecione um arquivo primeiro!", "error");
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);

  resultDiv.innerHTML = '<div class="text-blue-400">⏳ Importando...</div>';
  resultDiv.classList.remove("hidden");

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    if (res.ok) {
      let message = `✅ ${data.imported} itens importados com sucesso!`;

      if (data.users) {
        message +=
          '<br><br><strong>Primeiros usuários:</strong><ul class="mt-2">';
        data.users.forEach((u) => {
          message += `<li>• ${u.username}: ${u.points} pontos</li>`;
        });
        message += "</ul>";
      }

      if (data.commands) {
        message +=
          '<br><br><strong>Primeiros comandos:</strong><ul class="mt-2">';
        data.commands.forEach((c) => {
          message += `<li>• !${c.trigger}</li>`;
        });
        message += "</ul>";
      }

      showResult(resultDiv, message, "success");
      fileInput.value = "";
    } else {
      showResult(resultDiv, `❌ ${data.error}`, "error");
    }
  } catch (err) {
    console.error("Erro ao importar:", err);
    showResult(resultDiv, "❌ Erro de conexão", "error");
  }
}

function showResult(div, message, type) {
  const colors = {
    success: "bg-green-600/20 border-green-600 text-green-400",
    error: "bg-red-600/20 border-red-600 text-red-400",
  };

  div.innerHTML = `
    <div class="border-l-4 ${colors[type]} p-4 rounded">
      ${message}
    </div>
  `;
  div.classList.remove("hidden");
}
