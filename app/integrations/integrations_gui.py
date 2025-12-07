"""
Interface gráfica para gerenciar integrações
Discord, Minecraft, Email, Twitch API, Reconhecimento de Voz
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from modern_button import ModernButton


def open_integrations_window(gui):
    """Abre janela de gerenciamento de integrações"""

    window = tk.Toplevel(gui.window)
    window.title("🔌 Integrações")
    window.geometry("800x700")
    window.configure(bg=gui.colors["surface"])

    # Header
    tk.Label(
        window,
        text="🔌 GERENCIAMENTO DE INTEGRAÇÕES",
        bg=gui.colors["surface"],
        fg=gui.colors["text"],
        font=("Segoe UI", 16, "bold"),
    ).pack(pady=20)

    # Notebook com abas
    notebook = ttk.Notebook(window)
    notebook.pack(fill="both", expand=True, padx=20, pady=10)

    # Estilos
    style = ttk.Style()
    style.configure("TNotebook", background=gui.colors["bg"])
    style.configure("TNotebook.Tab", padding=[15, 8])

    # Criar abas
    create_discord_tab(notebook, gui)
    create_minecraft_tab(notebook, gui)
    create_email_tab(notebook, gui)
    create_twitch_api_tab(notebook, gui)
    create_voice_tab(notebook, gui)
    create_import_tab(notebook, gui)


def create_discord_tab(notebook, gui):
    """Aba de integração Discord"""
    frame = tk.Frame(notebook, bg=gui.colors["surface"])
    notebook.add(frame, text="💬 Discord")

    tk.Label(
        frame,
        text="Integração com Discord",
        bg=gui.colors["surface"],
        fg=gui.colors["text"],
        font=("Segoe UI", 12, "bold"),
    ).pack(pady=15)

    # Info
    info = tk.Label(
        frame,
        text="Envie notificações e mensagens para um canal do Discord\n"
        + "quando eventos ocorrerem no seu chat da Twitch",
        bg=gui.colors["surface"],
        fg=gui.colors["text_dim"],
        font=("Segoe UI", 9),
        justify="center",
    )
    info.pack(pady=10)

    # Campos
    fields_frame = tk.Frame(frame, bg=gui.colors["surface"])
    fields_frame.pack(pady=20)

    tk.Label(
        fields_frame, text="Bot Token:", bg=gui.colors["surface"], fg=gui.colors["text"]
    ).grid(row=0, column=0, sticky="e", padx=5, pady=5)
    discord_token = tk.Entry(
        fields_frame, bg=gui.colors["bg"], fg=gui.colors["text"], width=40, show="*"
    )
    discord_token.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(
        fields_frame,
        text="Channel ID:",
        bg=gui.colors["surface"],
        fg=gui.colors["text"],
    ).grid(row=1, column=0, sticky="e", padx=5, pady=5)
    discord_channel = tk.Entry(
        fields_frame, bg=gui.colors["bg"], fg=gui.colors["text"], width=40
    )
    discord_channel.grid(row=1, column=1, padx=5, pady=5)

    def save_discord():
        if not hasattr(gui, "integration_manager"):
            from integrations_manager import IntegrationManager

            gui.integration_manager = IntegrationManager(gui.data_dir)

        token = discord_token.get().strip()
        channel_id = discord_channel.get().strip()

        if not token or not channel_id:
            messagebox.showwarning("Atenção", "Preencha todos os campos!")
            return

        success, message = gui.integration_manager.setup_discord(token, channel_id)
        if success:
            messagebox.showinfo("Sucesso", message)
            gui.log("✅", "Discord configurado", "success")
        else:
            messagebox.showerror("Erro", message)

    ModernButton(
        frame,
        "💾 SALVAR",
        save_discord,
        gui.colors["primary"],
        gui.colors["text"],
        150,
        40,
    ).pack(pady=10)

    # Teste
    def test_discord():
        if not hasattr(gui, "integration_manager"):
            messagebox.showwarning("Atenção", "Configure primeiro!")
            return

        success, msg = gui.integration_manager.send_to_discord("Teste de integração!")
        messagebox.showinfo("Teste", msg)

    ModernButton(
        frame,
        "🧪 TESTAR",
        test_discord,
        gui.colors["secondary"],
        gui.colors["text"],
        150,
        35,
    ).pack(pady=5)


def create_minecraft_tab(notebook, gui):
    """Aba de integração Minecraft"""
    frame = tk.Frame(notebook, bg=gui.colors["surface"])
    notebook.add(frame, text="⛏️ Minecraft")

    tk.Label(
        frame,
        text="Integração com Servidor Minecraft (RCON)",
        bg=gui.colors["surface"],
        fg=gui.colors["text"],
        font=("Segoe UI", 12, "bold"),
    ).pack(pady=15)

    info = tk.Label(
        frame,
        text="Execute comandos no servidor Minecraft\n"
        + "quando eventos ocorrerem na Twitch (subs, raids, etc)",
        bg=gui.colors["surface"],
        fg=gui.colors["text_dim"],
        font=("Segoe UI", 9),
        justify="center",
    )
    info.pack(pady=10)

    fields_frame = tk.Frame(frame, bg=gui.colors["surface"])
    fields_frame.pack(pady=20)

    tk.Label(
        fields_frame, text="Host:", bg=gui.colors["surface"], fg=gui.colors["text"]
    ).grid(row=0, column=0, sticky="e", padx=5, pady=5)
    mc_host = tk.Entry(
        fields_frame, bg=gui.colors["bg"], fg=gui.colors["text"], width=30
    )
    mc_host.grid(row=0, column=1, padx=5, pady=5)
    mc_host.insert(0, "localhost")

    tk.Label(
        fields_frame, text="Porta:", bg=gui.colors["surface"], fg=gui.colors["text"]
    ).grid(row=1, column=0, sticky="e", padx=5, pady=5)
    mc_port = tk.Entry(
        fields_frame, bg=gui.colors["bg"], fg=gui.colors["text"], width=30
    )
    mc_port.grid(row=1, column=1, padx=5, pady=5)
    mc_port.insert(0, "25575")

    tk.Label(
        fields_frame,
        text="Senha RCON:",
        bg=gui.colors["surface"],
        fg=gui.colors["text"],
    ).grid(row=2, column=0, sticky="e", padx=5, pady=5)
    mc_password = tk.Entry(
        fields_frame, bg=gui.colors["bg"], fg=gui.colors["text"], width=30, show="*"
    )
    mc_password.grid(row=2, column=1, padx=5, pady=5)

    def save_minecraft():
        if not hasattr(gui, "integration_manager"):
            from integrations_manager import IntegrationManager

            gui.integration_manager = IntegrationManager(gui.data_dir)

        host = mc_host.get().strip()
        port = int(mc_port.get().strip() or 25575)
        password = mc_password.get().strip()

        success, message = gui.integration_manager.setup_minecraft(host, port, password)
        if success:
            messagebox.showinfo("Sucesso", message)
            gui.log("✅", "Minecraft configurado", "success")
        else:
            messagebox.showerror("Erro", message)

    ModernButton(
        frame,
        "💾 SALVAR",
        save_minecraft,
        gui.colors["primary"],
        gui.colors["text"],
        150,
        40,
    ).pack(pady=10)

    # Teste
    def test_minecraft():
        if not hasattr(gui, "integration_manager"):
            messagebox.showwarning("Atenção", "Configure primeiro!")
            return

        success, msg = gui.integration_manager.announce_to_minecraft("Teste do bot!")
        messagebox.showinfo("Teste", msg)

    ModernButton(
        frame,
        "🧪 TESTAR",
        test_minecraft,
        gui.colors["secondary"],
        gui.colors["text"],
        150,
        35,
    ).pack(pady=5)


def create_email_tab(notebook, gui):
    """Aba de integração Email"""
    frame = tk.Frame(notebook, bg=gui.colors["surface"])
    notebook.add(frame, text="📧 Email")

    tk.Label(
        frame,
        text="Integração com Email (SMTP)",
        bg=gui.colors["surface"],
        fg=gui.colors["text"],
        font=("Segoe UI", 12, "bold"),
    ).pack(pady=15)

    fields_frame = tk.Frame(frame, bg=gui.colors["surface"])
    fields_frame.pack(pady=20)

    labels = ["Servidor SMTP:", "Porta:", "Email:", "Senha:"]
    entries = []
    defaults = ["smtp.gmail.com", "587", "", ""]

    for i, (label, default) in enumerate(zip(labels, defaults)):
        tk.Label(
            fields_frame, text=label, bg=gui.colors["surface"], fg=gui.colors["text"]
        ).grid(row=i, column=0, sticky="e", padx=5, pady=5)
        entry = tk.Entry(
            fields_frame,
            bg=gui.colors["bg"],
            fg=gui.colors["text"],
            width=35,
            show="*" if "Senha" in label else None,
        )
        entry.grid(row=i, column=1, padx=5, pady=5)
        entry.insert(0, default)
        entries.append(entry)

    def save_email():
        if not hasattr(gui, "integration_manager"):
            from integrations_manager import IntegrationManager

            gui.integration_manager = IntegrationManager(gui.data_dir)

        smtp = entries[0].get().strip()
        port = int(entries[1].get().strip() or 587)
        email = entries[2].get().strip()
        password = entries[3].get().strip()

        success, message = gui.integration_manager.setup_email(
            smtp, port, email, password
        )
        if success:
            messagebox.showinfo("Sucesso", message)
            gui.log("✅", "Email configurado", "success")
        else:
            messagebox.showerror("Erro", message)

    ModernButton(
        frame,
        "💾 SALVAR",
        save_email,
        gui.colors["primary"],
        gui.colors["text"],
        150,
        40,
    ).pack(pady=10)


def create_twitch_api_tab(notebook, gui):
    """Aba de Twitch API avançada"""
    frame = tk.Frame(notebook, bg=gui.colors["surface"])
    notebook.add(frame, text="📊 Twitch API")

    tk.Label(
        frame,
        text="Twitch API Helix (Followers & Subs)",
        bg=gui.colors["surface"],
        fg=gui.colors["text"],
        font=("Segoe UI", 12, "bold"),
    ).pack(pady=15)

    info = tk.Label(
        frame,
        text="Acesse dados avançados da Twitch:\n"
        + "• Lista de seguidores\n"
        + "• Lista de subscribers\n"
        + "• Informações de usuários\n"
        + "• Bônus automático para subs/followers",
        bg=gui.colors["surface"],
        fg=gui.colors["text_dim"],
        font=("Segoe UI", 9),
        justify="left",
    )
    info.pack(pady=10)

    fields_frame = tk.Frame(frame, bg=gui.colors["surface"])
    fields_frame.pack(pady=20)

    tk.Label(
        fields_frame, text="Client ID:", bg=gui.colors["surface"], fg=gui.colors["text"]
    ).grid(row=0, column=0, sticky="e", padx=5, pady=5)
    api_client_id = tk.Entry(
        fields_frame, bg=gui.colors["bg"], fg=gui.colors["text"], width=40
    )
    api_client_id.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(
        fields_frame,
        text="Client Secret:",
        bg=gui.colors["surface"],
        fg=gui.colors["text"],
    ).grid(row=1, column=0, sticky="e", padx=5, pady=5)
    api_client_secret = tk.Entry(
        fields_frame, bg=gui.colors["bg"], fg=gui.colors["text"], width=40, show="*"
    )
    api_client_secret.grid(row=1, column=1, padx=5, pady=5)

    def save_api():
        if not hasattr(gui, "integration_manager"):
            from integrations_manager import IntegrationManager

            gui.integration_manager = IntegrationManager(gui.data_dir)

        client_id = api_client_id.get().strip()
        client_secret = api_client_secret.get().strip()

        success, message = gui.integration_manager.setup_twitch_api(
            client_id, client_secret
        )
        if success:
            messagebox.showinfo("Sucesso", message)
            gui.log("✅", "Twitch API configurada", "success")
        else:
            messagebox.showerror("Erro", message)

    ModernButton(
        frame, "💾 SALVAR", save_api, gui.colors["primary"], gui.colors["text"], 150, 40
    ).pack(pady=10)


def create_voice_tab(notebook, gui):
    """Aba de reconhecimento de voz"""
    frame = tk.Frame(notebook, bg=gui.colors["surface"])
    notebook.add(frame, text="🎤 Voz")

    tk.Label(
        frame,
        text="Reconhecimento de Voz",
        bg=gui.colors["surface"],
        fg=gui.colors["text"],
        font=("Segoe UI", 12, "bold"),
    ).pack(pady=15)

    info = tk.Label(
        frame,
        text="Controle o bot com sua voz durante a live!\n"
        + "Diga 'bot' + comando para executar ações",
        bg=gui.colors["surface"],
        fg=gui.colors["text_dim"],
        font=("Segoe UI", 9),
        justify="center",
    )
    info.pack(pady=10)

    # Status
    status_frame = tk.Frame(frame, bg=gui.colors["bg"], relief="ridge", bd=2)
    status_frame.pack(pady=15, padx=20, fill="x")

    status_label = tk.Label(
        status_frame,
        text="🔴 Desativado",
        bg=gui.colors["bg"],
        fg=gui.colors["error"],
        font=("Segoe UI", 11, "bold"),
    )
    status_label.pack(pady=10)

    # Botões de controle
    btn_frame = tk.Frame(frame, bg=gui.colors["surface"])
    btn_frame.pack(pady=10)

    def toggle_voice():
        try:
            if not hasattr(gui, "voice_manager"):
                from app.integrations.voice_recognition import VoiceCommandManager, VoiceIntegration

                gui.voice_manager = VoiceCommandManager(gui.data_dir)
                gui.voice_integration = VoiceIntegration(gui, gui.voice_manager)

            if (
                hasattr(gui.voice_manager, "is_listening")
                and gui.voice_manager.is_listening
            ):
                # Parar
                gui.voice_manager.stop_listening()
                status_label.config(text="🔴 Desativado", fg=gui.colors["error"])
                gui.log("🎤", "Reconhecimento de voz desativado", "warning")
            else:
                # Iniciar
                success, msg = gui.voice_manager.start_listening()
                if success:
                    status_label.config(text="🟢 Escutando", fg=gui.colors["success"])
                    gui.log("🎤", "Reconhecimento de voz ativado", "success")
                else:
                    messagebox.showerror("Erro", msg)
        except ImportError:
            messagebox.showerror(
                "Módulo Não Encontrado",
                "O módulo voice_recognition.py não foi encontrado.\n\n"
                + "Certifique-se de que o arquivo existe na mesma pasta.\n"
                + "Instale dependências: pip install SpeechRecognition pyaudio pyttsx3",
            )

    ModernButton(
        btn_frame,
        "🎤 ATIVAR/DESATIVAR",
        toggle_voice,
        gui.colors["primary"],
        gui.colors["text"],
        180,
        45,
    ).pack(pady=5)

    # Lista de comandos
    tk.Label(
        frame,
        text="📋 Comandos Disponíveis",
        bg=gui.colors["surface"],
        fg=gui.colors["text"],
        font=("Segoe UI", 10, "bold"),
    ).pack(pady=(20, 5))

    commands_list = scrolledtext.ScrolledText(
        frame,
        height=12,
        bg=gui.colors["bg"],
        fg=gui.colors["text"],
        font=("Consolas", 9),
        wrap="word",
    )
    commands_list.pack(padx=20, pady=5, fill="both", expand=True)

    # Adicionar comandos sugeridos
    try:
        from app.integrations.voice_recognition import SUGGESTED_COMMANDS

        for cmd, desc in SUGGESTED_COMMANDS.items():
            commands_list.insert("end", f"• bot {cmd}\n  → {desc}\n\n")
    except ImportError:
        commands_list.insert("end", "Módulo voice_recognition não disponível.\n")
        commands_list.insert(
            "end", "Instale: pip install SpeechRecognition pyaudio pyttsx3\n\n"
        )
        commands_list.insert("end", "Comandos exemplo:\n")
        commands_list.insert("end", "• bot ler chat\n")
        commands_list.insert("end", "• bot obrigado\n")
        commands_list.insert("end", "• bot quantos viewers\n")

    commands_list.config(state="disabled")


def create_import_tab(notebook, gui):
    """Aba de importação de dados"""
    frame = tk.Frame(notebook, bg=gui.colors["surface"])
    notebook.add(frame, text="📥 Importar")

    tk.Label(
        frame,
        text="Importar Dados de Outros Bots",
        bg=gui.colors["surface"],
        fg=gui.colors["text"],
        font=("Segoe UI", 12, "bold"),
    ).pack(pady=15)

    info = tk.Label(
        frame,
        text="Importe pontos do StreamElements, Nightbot ou outros bots",
        bg=gui.colors["surface"],
        fg=gui.colors["text_dim"],
        font=("Segoe UI", 9),
    )
    info.pack(pady=10)

    # StreamElements
    se_frame = tk.Frame(frame, bg=gui.colors["bg"], relief="ridge", bd=1)
    se_frame.pack(pady=10, padx=20, fill="x")

    tk.Label(
        se_frame,
        text="StreamElements (CSV)",
        bg=gui.colors["bg"],
        fg=gui.colors["text"],
        font=("Segoe UI", 10, "bold"),
    ).pack(pady=10)

    def import_streamelements():
        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo CSV", filetypes=[("CSV files", "*.csv")]
        )
        if file_path:
            if not hasattr(gui, "integration_manager"):
                from integrations_manager import IntegrationManager, merge_points

                gui.integration_manager = IntegrationManager(gui.data_dir)

            imported = gui.integration_manager.import_streamelements_points(file_path)
            if imported and gui.bot:
                # Fazer merge
                from integrations_manager import merge_points

                gui.bot.user_points = merge_points(dict(gui.bot.user_points), imported)
                gui.bot.save_data()
                messagebox.showinfo("Sucesso", f"{len(imported)} usuários importados!")
                gui.log(
                    "✅",
                    f"Importados {len(imported)} usuários do StreamElements",
                    "success",
                )
            else:
                messagebox.showwarning("Atenção", "Nenhum dado importado")

    ModernButton(
        se_frame,
        "📁 IMPORTAR CSV",
        import_streamelements,
        gui.colors["primary"],
        gui.colors["text"],
        150,
        35,
    ).pack(pady=10)

    # Nightbot
    nb_frame = tk.Frame(frame, bg=gui.colors["bg"], relief="ridge", bd=1)
    nb_frame.pack(pady=10, padx=20, fill="x")

    tk.Label(
        nb_frame,
        text="Nightbot (JSON)",
        bg=gui.colors["bg"],
        fg=gui.colors["text"],
        font=("Segoe UI", 10, "bold"),
    ).pack(pady=10)

    def import_nightbot():
        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo JSON", filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            if not hasattr(gui, "integration_manager"):
                from integrations_manager import IntegrationManager, merge_points

                gui.integration_manager = IntegrationManager(gui.data_dir)

            imported = gui.integration_manager.import_nightbot_points(file_path)
            if imported and gui.bot:
                from integrations_manager import merge_points

                gui.bot.user_points = merge_points(dict(gui.bot.user_points), imported)
                gui.bot.save_data()
                messagebox.showinfo("Sucesso", f"{len(imported)} usuários importados!")
                gui.log(
                    "✅", f"Importados {len(imported)} usuários do Nightbot", "success"
                )
            else:
                messagebox.showwarning("Atenção", "Nenhum dado importado")

    ModernButton(
        nb_frame,
        "📁 IMPORTAR JSON",
        import_nightbot,
        gui.colors["primary"],
        gui.colors["text"],
        150,
        35,
    ).pack(pady=10)
