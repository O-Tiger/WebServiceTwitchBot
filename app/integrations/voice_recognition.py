"""
Módulo de Reconhecimento de Voz para Twitch Bot
Responde comandos de voz durante a live
Instalação: pip install SpeechRecognition pyaudio pyttsx3
"""

import threading
import queue
import json
import os
from typing import Callable, Dict, List, Optional

try:
    import speech_recognition as sr

    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import pyttsx3

    TEXT_TO_SPEECH_AVAILABLE = True
except ImportError:
    TEXT_TO_SPEECH_AVAILABLE = False


class VoiceCommandManager:
    """Gerenciador de comandos de voz"""

    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "voice_config.json")

        # Estado
        self.is_listening = False
        self.recognition_thread = None
        self.command_queue = queue.Queue()

        # Configuração
        self.config = self.load_config()
        self.voice_commands = self.config.get("commands", {})

        # Callbacks
        self.on_command_callback = None
        self.on_text_callback = None

        # Inicializar engines
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None

        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
            try:
                self.microphone = sr.Microphone()
                # Calibrar para ruído ambiente
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
            except Exception as e:
                print(f"❌ Erro ao inicializar microfone: {e}")

        if TEXT_TO_SPEECH_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty("rate", 150)  # Velocidade
                self.tts_engine.setProperty("volume", 0.9)  # Volume
            except Exception as e:
                print(f"❌ Erro ao inicializar TTS: {e}")

    def load_config(self) -> Dict:
        """Carrega configurações"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar config de voz: {e}")

        return {
            "enabled": False,
            "language": "pt-BR",
            "activation_word": "bot",
            "commands": {
                "iniciar stream": {
                    "action": "start_stream",
                    "response": "Iniciando stream",
                },
                "parar stream": {"action": "stop_stream", "response": "Parando stream"},
                "mostrar chat": {"action": "show_chat", "response": "Mostrando chat"},
                "esconder chat": {"action": "hide_chat", "response": "Escondendo chat"},
                "próxima música": {"action": "next_song", "response": "Próxima música"},
                "pausar música": {
                    "action": "pause_song",
                    "response": "Pausando música",
                },
                "volume máximo": {
                    "action": "max_volume",
                    "response": "Volume no máximo",
                },
                "silenciar": {"action": "mute", "response": "Silenciando"},
                "ler chat": {
                    "action": "read_chat",
                    "response": "Lendo últimas mensagens",
                },
                "quantos viewers": {
                    "action": "viewer_count",
                    "response": "Verificando viewers",
                },
                "enviar mensagem": {
                    "action": "send_message",
                    "response": "Enviando mensagem",
                },
                "obrigado": {
                    "action": "thank_viewers",
                    "response": "Obrigado a todos!",
                },
            },
        }

    def save_config(self):
        """Salva configurações"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print("✅ Config de voz salva")
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")

    def add_command(self, phrase: str, action: str, response: str):
        """Adiciona comando de voz personalizado"""
        self.voice_commands[phrase.lower()] = {"action": action, "response": response}
        self.config["commands"] = self.voice_commands
        self.save_config()

    def remove_command(self, phrase: str):
        """Remove comando de voz"""
        phrase_lower = phrase.lower()
        if phrase_lower in self.voice_commands:
            del self.voice_commands[phrase_lower]
            self.config["commands"] = self.voice_commands
            self.save_config()
            return True
        return False

    def start_listening(self):
        """Inicia escuta contínua"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            return (
                False,
                "SpeechRecognition não disponível. Use: pip install SpeechRecognition pyaudio",
            )

        if not self.microphone:
            return False, "Microfone não disponível"

        if self.is_listening:
            return False, "Já está escutando"

        self.is_listening = True
        self.recognition_thread = threading.Thread(
            target=self._listen_loop, daemon=True
        )
        self.recognition_thread.start()

        return True, "Reconhecimento de voz iniciado"

    def stop_listening(self):
        """Para escuta"""
        self.is_listening = False
        if self.recognition_thread:
            self.recognition_thread.join(timeout=2)
        return True, "Reconhecimento de voz parado"

    def _listen_loop(self):
        """Loop de escuta (roda em thread separada)"""
        print("🎤 Escutando comandos de voz...")

        while self.is_listening:
            try:
                with self.microphone as source:
                    # Escutar com timeout
                    audio = self.recognizer.listen(
                        source, timeout=1, phrase_time_limit=5
                    )

                try:
                    # Reconhecer em português do Brasil
                    text = self.recognizer.recognize_google(
                        audio, language=self.config.get("language", "pt-BR")
                    ).lower()

                    print(f"🎤 Reconhecido: {text}")

                    # Callback para texto reconhecido
                    if self.on_text_callback:
                        self.on_text_callback(text)

                    # Verificar palavra de ativação
                    activation_word = self.config.get("activation_word", "bot").lower()
                    if activation_word in text:
                        self._process_command(text)

                except sr.UnknownValueError:
                    # Não entendeu
                    pass
                except sr.RequestError as e:
                    print(f"❌ Erro no serviço de reconhecimento: {e}")

            except sr.WaitTimeoutError:
                # Timeout normal, continuar
                pass
            except Exception as e:
                print(f"❌ Erro na escuta: {e}")

    def _process_command(self, text: str):
        """Processa comando reconhecido"""
        text_lower = text.lower()

        # Procurar comando correspondente
        for phrase, command_data in self.voice_commands.items():
            if phrase in text_lower:
                action = command_data.get("action")
                response = command_data.get("response")

                print(f"✅ Comando executado: {phrase} -> {action}")

                # Falar resposta
                if response and self.tts_engine:
                    self.speak(response)

                # Callback
                if self.on_command_callback:
                    self.on_command_callback(action, phrase, text)

                break

    def speak(self, text: str):
        """Fala texto usando TTS"""
        if not TEXT_TO_SPEECH_AVAILABLE or not self.tts_engine:
            print(f"🔊 [TTS] {text}")
            return

        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"❌ Erro no TTS: {e}")

    def set_command_callback(self, callback: Callable):
        """Define callback para quando comando é reconhecido"""
        self.on_command_callback = callback

    def set_text_callback(self, callback: Callable):
        """Define callback para todo texto reconhecido"""
        self.on_text_callback = callback


class VoiceIntegration:
    """Integração de voz com o bot Twitch"""

    def __init__(self, bot_gui, voice_manager: VoiceCommandManager):
        self.gui = bot_gui
        self.voice = voice_manager

        # Registrar callbacks
        self.voice.set_command_callback(self.handle_voice_command)
        self.voice.set_text_callback(self.handle_voice_text)

    def handle_voice_command(self, action: str, phrase: str, full_text: str):
        """Handler para comandos de voz"""
        # Log
        self.gui.log("🎤", f"Comando de voz: {phrase}", "info")

        # Ações predefinidas
        actions = {
            "show_chat": lambda: self.gui.log("👁️", "Mostrando chat", "info"),
            "hide_chat": lambda: self.gui.log("🙈", "Escondendo chat", "info"),
            "read_chat": lambda: self.read_last_messages(),
            "viewer_count": lambda: self.announce_viewer_count(),
            "send_message": lambda: self.send_voice_message(full_text),
            "thank_viewers": lambda: self.thank_all_viewers(),
        }

        # Executar ação
        action_func = actions.get(action)
        if action_func:
            action_func()
        else:
            self.gui.log("⚠️", f"Ação não implementada: {action}", "warning")

    def handle_voice_text(self, text: str):
        """Handler para todo texto reconhecido"""
        # Pode ser usado para log ou análise
        pass

    def read_last_messages(self):
        """Lê últimas mensagens do chat em voz alta"""
        if not self.gui.bot:
            return

        # Pegar últimas 3 mensagens do log
        log_content = self.gui.chat_text.get("end-80l", "end")
        lines = [l for l in log_content.split("\n") if l.strip()][-3:]

        for line in lines:
            # Extrair username e mensagem
            if ":" in line:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    username = parts[1].strip()
                    message = parts[2].strip()
                    self.voice.speak(f"{username} disse: {message}")

    def announce_viewer_count(self):
        """Anuncia quantidade de viewers"""
        # Contar usuários únicos que enviaram mensagens
        unique_users = set()
        for bot_instance in self.gui.bots.values():
            unique_users.update(bot_instance.user_points.keys())

        count = len(unique_users)
        self.voice.speak(f"Temos {count} usuários ativos no chat")
        self.gui.log("👥", f"{count} usuários ativos", "info")

    def send_voice_message(self, full_text: str):
        """Envia mensagem baseada no comando de voz"""
        # Extrair mensagem após palavra-chave
        if "enviar mensagem" in full_text:
            message = full_text.split("enviar mensagem", 1)[1].strip()
            if message and self.gui.bot:
                self.gui.message_entry.delete(0, "end")
                self.gui.message_entry.insert(0, message)
                self.gui.send_message()

    def thank_all_viewers(self):
        """Agradece todos os viewers"""
        if self.gui.bot:
            # Enviar mensagem no chat
            for channel, bot_instance in self.gui.bots.items():
                import asyncio

                ch = bot_instance.get_channel(channel)
                if ch:
                    asyncio.run_coroutine_threadsafe(
                        ch.send("Muito obrigado a todos por assistirem! ❤️"),
                        bot_instance.loop,
                    )

        self.voice.speak("Obrigado a todos!")


# ===== COMANDOS DE VOZ SUGERIDOS =====

SUGGESTED_COMMANDS = {
    # Controle de Stream
    "iniciar stream": "Começar transmissão",
    "parar stream": "Encerrar transmissão",
    "pausar stream": "Pausar transmissão",
    # Chat
    "ler chat": "Ler últimas mensagens",
    "limpar chat": "Limpar mensagens",
    "modo somente seguidores": "Ativar modo followers",
    # Música/Audio
    "próxima música": "Pular música",
    "música anterior": "Voltar música",
    "pausar música": "Pausar/despausar",
    "volume mais alto": "Aumentar volume",
    "volume mais baixo": "Diminuir volume",
    # Cenas OBS (requer integração)
    "cena gameplay": "Trocar para cena de jogo",
    "cena câmera": "Trocar para cena câmera",
    "cena começando": "Cena de início",
    "cena finalizando": "Cena de encerramento",
    # Informações
    "quantos viewers": "Checar viewers",
    "quem está no top": "Ver top usuários",
    "última sub": "Ver última subscription",
    # Interação
    "obrigado": "Agradecer viewers",
    "bem vindos": "Dar boas vindas",
    "até logo": "Despedir-se",
}


def check_voice_dependencies() -> Dict[str, bool]:
    """Verifica dependências de voz"""
    return {
        "SpeechRecognition": SPEECH_RECOGNITION_AVAILABLE,
        "TextToSpeech": TEXT_TO_SPEECH_AVAILABLE,
    }
