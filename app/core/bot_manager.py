"""
CORREÇÃO DEFINITIVA - bot_manager.py
O problema era que socketio.emit() de threads assíncronas não é confiável
Solução: Usar socketio com async_mode='threading'
"""

import asyncio
import threading
from collections import defaultdict
from typing import Dict, Optional
from app.core.twitch_bot_class import TwitchBot


class BotManager:
    """Gerenciador central para múltiplos bots da Twitch"""

    def __init__(self):
        self.bots: Dict[str, TwitchBot] = {}
        self.bot_threads: Dict[str, threading.Thread] = {}
        self.bot_loops: Dict[str, asyncio.AbstractEventLoop] = {}
        self.connected_channels = set()

        # Callbacks para eventos
        self.on_message_callback = None
        self.on_status_change_callback = None
        self.on_log_callback = None
        self.on_raid_callback = None

        # ✅ ADICIONAR: Lock para thread safety
        self._callback_lock = threading.Lock()

        # Inicializar banco de dados
        from app.database.crud import BotDatabase

        self.db = BotDatabase()

        # Carregar auto-respostas do banco de dados
        self.auto_responses = self._load_auto_responses()

    def set_callbacks(self, on_message=None, on_status=None, on_log=None, on_raid=None):
        """Define callbacks para eventos"""
        self.on_message_callback = on_message
        self.on_status_change_callback = on_status
        self.on_log_callback = on_log
        self.on_raid_callback = on_raid

    def connect_to_channel(self, channel: str, token: str, prefix: str = "$") -> bool:
        """Conecta a um canal específico"""
        if channel in self.connected_channels:
            self._log("warning", f"Já conectado ao canal {channel}")
            return False

        self._log("info", f"Conectando ao canal {channel}...")

        # Criar bot config
        bot_config = {"token": token, "channel": channel, "prefix": prefix}

        # Criar thread para este canal
        thread = threading.Thread(
            target=self._run_bot_for_channel, args=(channel, bot_config), daemon=True
        )
        thread.start()

        self.bot_threads[channel] = thread
        self.connected_channels.add(channel)

        if self.on_status_change_callback:
            self._safe_callback(self.on_status_change_callback, channel, "connecting")

        return True

    def disconnect_from_channel(self, channel: str) -> bool:
        """Desconecta de um canal específico"""
        if channel not in self.connected_channels:
            self._log("warning", f"Não está conectado ao canal {channel}")
            return False

        self._log("info", f"Desconectando do canal {channel}...")

        # Salvar dados antes de desconectar
        if channel in self.bots:
            bot_instance = self.bots[channel]
            if bot_instance:
                bot_instance.save_data()

                # Fechar bot usando asyncio de forma correta
                if channel in self.bot_loops:
                    loop = self.bot_loops[channel]
                    if loop and not loop.is_closed():
                        # Agendar o close no loop correto
                        asyncio.run_coroutine_threadsafe(bot_instance.close(), loop)

                        # Aguardar um pouco para finalizar
                        import time

                        time.sleep(0.5)

            # Remover bot
            del self.bots[channel]

        # Remover thread e loop
        if channel in self.bot_threads:
            del self.bot_threads[channel]

        if channel in self.bot_loops:
            loop = self.bot_loops[channel]
            if loop and not loop.is_closed():
                # Parar o loop de forma segura
                loop.call_soon_threadsafe(loop.stop)
            del self.bot_loops[channel]

        # Remover dos canais conectados
        self.connected_channels.discard(channel)

        if self.on_status_change_callback:
            self._safe_callback(self.on_status_change_callback, channel, "offline")

        self._log("success", f"Desconectado do canal {channel}")
        return True

    def _run_bot_for_channel(self, channel: str, bot_config: dict):
        """Executa bot para um canal específico (roda em thread separada)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.bot_loops[channel] = loop

        try:
            # Wrapper GUI para callbacks
            gui_wrapper = GUIWrapper(
                channel=channel,
                on_message=self.on_message_callback,
                on_log=self.on_log_callback,
                on_raid=self.on_raid_callback,
                callback_lock=self._callback_lock,  # ✅ Passar lock
            )

            bot_instance = TwitchBot(
                token=bot_config["token"],
                prefix=bot_config.get("prefix", "$"),
                channels=[channel],
                gui=gui_wrapper,
            )

            # Carregar auto-respostas centralizadas
            bot_instance.auto_responses.update(self.auto_responses)

            # Armazenar instância do bot
            self.bots[channel] = bot_instance

            # Notificar status
            if self.on_status_change_callback:
                self._safe_callback(self.on_status_change_callback, channel, "online")

            loop.run_until_complete(bot_instance.start())
        except Exception as e:
            self._log("error", f"Erro no canal {channel}: {str(e)}")
            self.connected_channels.discard(channel)
            if self.on_status_change_callback:
                self._safe_callback(self.on_status_change_callback, channel, "error")
        finally:
            loop.close()

    def send_message(self, channel: str, message: str) -> bool:
        """Envia mensagem para um canal específico"""
        if channel not in self.bots:
            self._log("warning", f"Bot não conectado ao canal {channel}")
            return False

        try:
            bot_instance = self.bots[channel]
            ch = bot_instance.get_channel(channel)

            if ch is None:
                self._log("warning", f"Canal '{channel}' não acessível")
                return False

            asyncio.run_coroutine_threadsafe(ch.send(message), bot_instance.loop)

            self._log("bot", f"[{channel}] Você: {message}")
            return True
        except Exception as e:
            self._log("error", f"Erro ao enviar mensagem: {str(e)}")
            return False

    # ✅ NOVO MÉTODO: Executar callback de forma thread-safe
    def _safe_callback(self, callback, *args, **kwargs):
        """Executa callback de forma thread-safe"""
        if callback:
            with self._callback_lock:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    print(f"❌ Erro no callback: {e}")

    def add_auto_response(self, trigger: str, response: str) -> bool:
        """Adiciona resposta automática"""
        self.auto_responses[trigger] = response

        # Adicionar a todos os bots ativos
        for bot in self.bots.values():
            bot.auto_responses[trigger] = response
            bot.save_data()

        # Salvar no arquivo separado
        self._save_auto_responses()
        return True

    def remove_auto_response(self, trigger: str) -> bool:
        """Remove resposta automática"""
        if trigger not in self.auto_responses:
            return False

        # Remover do gerenciador
        del self.auto_responses[trigger]

        # Remover de todos os bots ativos
        for bot in self.bots.values():
            if trigger in bot.auto_responses:
                del bot.auto_responses[trigger]
                bot.save_data()

        # Salvar alteração no arquivo
        self._save_auto_responses()
        return True

    def _load_auto_responses(self) -> dict:
        """Carrega auto-respostas do banco de dados"""
        try:
            responses_list = self.db.auto_responses.get_all(
                channel=None, enabled_only=False
            )
            responses = {}
            for item in responses_list:
                responses[item["trigger"]] = item["response"]
            print(f"✅ {len(responses)} auto-respostas carregadas do banco de dados")
            return responses
        except Exception as e:
            print(f"⚠️ Erro ao carregar auto-respostas: {e}")
            return {}

    def _save_auto_responses(self):
        """Salva auto-respostas no banco de dados"""
        try:
            for trigger, response in self.auto_responses.items():
                # Verificar se existe
                existing = self.db.auto_responses.get_by_trigger(
                    trigger, channel=None
                )
                if existing:
                    self.db.auto_responses.update(existing["id"], response=response)
                else:
                    self.db.auto_responses.create(
                        trigger=trigger,
                        response=response,
                        channel=None,
                        enabled=True,
                    )
            print(
                f"💾 {len(self.auto_responses)} auto-respostas salvas no banco de dados"
            )
        except Exception as e:
            print(f"❌ Erro ao salvar auto-respostas: {e}")

    def get_aggregated_stats(self) -> dict:
        """Retorna estatísticas agregadas de todos os canais"""
        all_points = defaultdict(int)
        all_messages = defaultdict(int)

        for bot in self.bots.values():
            for user, pts in bot.user_points.items():
                all_points[user] += pts
            for user, msgs in bot.message_count.items():
                all_messages[user] += msgs

        return {
            "points": dict(all_points),
            "messages": dict(all_messages),
            "connected_channels": list(self.connected_channels),
            "total_users": len(all_points),
            "total_messages": sum(all_messages.values()),
            "total_points": sum(all_points.values()),
        }

    def get_channel_stats(self, channel: str) -> Optional[dict]:
        """Retorna estatísticas de um canal específico"""
        if channel not in self.bots:
            return None

        bot = self.bots[channel]
        return {
            "channel": channel,
            "points": dict(bot.user_points),
            "messages": dict(bot.message_count),
            "auto_responses": bot.auto_responses,
            "total_users": len(bot.user_points),
            "total_messages": sum(bot.message_count.values()),
        }

    def disconnect_all(self):
        """Desconecta de todos os canais"""
        channels = list(self.connected_channels)
        for channel in channels:
            self.disconnect_from_channel(channel)

    def _log(self, level: str, message: str):
        """Helper para logging"""
        if self.on_log_callback:
            self._safe_callback(self.on_log_callback, level, message)

    def import_user_points(self, username, points, channel=None):
        """Importa pontos de um usuário para todos os bots ativos ou canal específico"""
        username = username.lower()

        # Se canal específico for informado
        if channel and channel in self.bots:
            bot = self.bots[channel]
            if username in bot.user_points:
                bot.user_points[username] += points
            else:
                bot.user_points[username] = points
            bot.save_data()
            print(f"✅ Importado para {channel}: {username} com {points} pontos")
            return

        # Caso contrário, adiciona para todos os bots ativos
        for bot in self.bots.values():
            if username in bot.user_points:
                bot.user_points[username] += points
            else:
                bot.user_points[username] = points
            bot.save_data()

        # Também salvar no banco de dados para persistência
        try:
            # Usar primeiro canal disponível ou 'global'
            target_channel = list(self.bots.keys())[0] if self.bots else 'global'
            self.db.users.add_points(username, target_channel, points)
        except Exception as e:
            print(f"⚠️ Erro ao salvar no DB: {e}")

        print(f"✅ Importado: {username} com {points} pontos")
    
class GUIWrapper:
    """Wrapper para simular interface GUI para TwitchBot"""

    def __init__(
        self,
        channel: str,
        on_message=None,
        on_log=None,
        on_raid=None,
        callback_lock=None,
    ):
        self.channel = channel
        self.on_message_callback = on_message
        self.on_log_callback = on_log
        self.on_raid_callback = on_raid
        self.callback_lock = callback_lock or threading.Lock()  # ✅ Thread safety

    def log(self, icon: str, message: str, tag: str = ""):
        """Simula método log da GUI"""
        if self.on_log_callback:
            # ✅ Thread-safe callback
            with self.callback_lock:
                try:
                    self.on_log_callback(tag or "info", f"{icon} {message}")
                except Exception as e:
                    print(f"❌ Erro no log callback: {e}")

    def update_status(self, status: str):
        """Simula atualização de status"""
        pass

    def update_stats(
        self, username: str, messages: int, points: int, message_text: str = ""
    ):
        """Simula atualização de stats - THREAD-SAFE"""
        if self.on_message_callback:
            # ✅ Thread-safe callback com retry
            with self.callback_lock:
                try:
                    print(
                        f"🔵 Chamando callback: {self.channel} | {username} | {message_text}"
                    )
                    self.on_message_callback(
                        self.channel, username, message_text, messages, points
                    )
                    print(f"✅ Callback executado com sucesso")
                except Exception as e:
                    print(f"❌ Erro no callback de mensagem: {e}")
                    import traceback

                    traceback.print_exc()

    def on_raid(self, raider: str, viewers: int):
        """Callback para evento de raid"""
        if self.on_raid_callback:
            # ✅ Thread-safe callback
            with self.callback_lock:
                try:
                    self.on_raid_callback(self.channel, raider, viewers)
                except Exception as e:
                    print(f"❌ Erro no callback de raid: {e}")
