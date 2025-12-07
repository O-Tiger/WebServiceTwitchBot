"""
Classe principal do bot Twitch com funcionalidades avançadas
Sistema de pontos, comandos personalizados e moderação
"""

from twitchio.ext import commands
import asyncio
import json
import os
from datetime import datetime
from collections import defaultdict
import random


class TwitchBot(commands.Bot):
    """Bot com sistema de pontos, comandos e auto-respostas"""

    def __init__(self, token, prefix, channels, gui):
        super().__init__(token=token, prefix=prefix, initial_channels=channels)
        self.gui = gui
        self.channel_name = channels[0] if channels else "unknown"  # Nome do canal
        self.user_points = defaultdict(int)
        self.message_count = defaultdict(int)
        self.auto_responses = {}

        # Pasta para dados
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.load_data()

    def load_data(self):
        """Carrega dados de pontos, mensagens e auto-respostas"""
        try:
            bot_data_file = os.path.join(self.data_dir, "bot_data.json")
            if os.path.exists(bot_data_file):
                with open(bot_data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.user_points = defaultdict(int, data.get("points", {}))
                    self.message_count = defaultdict(int, data.get("messages", {}))
                    self.auto_responses = data.get("responses", {})

            # Carregar auto-respostas do arquivo separado
            auto_file = os.path.join(self.data_dir, "auto_responses.json")
            if os.path.exists(auto_file):
                with open(auto_file, "r", encoding="utf-8") as f:
                    auto_data = json.load(f)
                    self.auto_responses.update(auto_data.get("responses", {}))

            print(
                f"✅ Dados carregados: {len(self.user_points)} usuários, "
                f"{len(self.auto_responses)} respostas automáticas"
            )
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")

    def save_data(self):
        """Salva dados em arquivo"""
        try:
            data = {
                "points": dict(self.user_points),
                "messages": dict(self.message_count),
                # responses agora são gerenciadas separadamente
                # PATCH_APPLIED_AUTO_RESPONSES
            }
            bot_data_file = os.path.join(self.data_dir, "bot_data.json")
            with open(bot_data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")

    async def event_ready(self):
        """Executado quando o bot conecta com sucesso"""
        self.gui.log(
            "✅", f"[{self.channel_name}] Bot conectado como: {self.nick}", "success"
        )
        self.gui.update_status("online")

        # ✅ CORREÇÃO: Armazenar task para poder cancelar depois
        self.auto_points_task = self.loop.create_task(self.auto_award_points())

    async def auto_award_points(self):
        """Concede pontos automaticamente a cada 5 minutos"""
        try:
            while True:
                await asyncio.sleep(300)  # 5 minutos

                # ✅ CORREÇÃO: Verificar se o loop ainda está rodando
                if self.loop.is_closed():
                    print(f"⚠️ Loop fechado, parando auto_award_points")
                    break

                for user in list(self.message_count.keys()):
                    if self.message_count[user] > 0:
                        self.user_points[user] += 10

                self.save_data()
        except asyncio.CancelledError:
            print(f"⚠️ Task auto_award_points cancelada")
        except Exception as e:
            print(f"❌ Erro em auto_award_points: {e}")

    async def event_message(self, message):
        """Processa cada mensagem recebida"""
        if message.echo:
            return

        username = message.author.name
        content = message.content

        # Contagem e pontos
        self.message_count[username] += 1
        self.user_points[username] += 1

        # Atualizar GUI - CORRIGIDO: agora passa o texto da mensagem
        self.gui.update_stats(
            username,
            self.message_count[username],
            self.user_points[username],
            message_text=content,  # ✅ Parâmetro nomeado - CORRETO
        )

        # Log com indicação do canal
        self.gui.log("💬", f"[{self.channel_name}] {username}: {content}", "message")

        # Respostas automáticas
        for trigger, response in self.auto_responses.items():
            if trigger.lower() in content.lower():
                await message.channel.send(response)
                self.gui.log(
                    "🤖",
                    f"[{self.channel_name}] Resposta automática: {response}",
                    "bot",
                )
                break  # Apenas uma resposta por mensagem

        # Processar comandos
        try:
            await self.handle_commands(message)
        except Exception as e:
            # ✅ Ignorar erros de comando não encontrado
            if "CommandNotFound" not in str(type(e).__name__):
                self.gui.log("⚠️", f"Erro ao processar comando: {e}", "warning")

        # Moderação básica
        palavras_banidas = ["spam", "hack", "cheat"]
        if any(palavra in content.lower() for palavra in palavras_banidas):
            self.gui.log(
                "⚠️", f"[{self.channel_name}] Conteúdo suspeito de {username}", "warning"
            )

    async def close(self):
        """Método para fechar o bot corretamente"""
        try:
            # Cancelar task de pontos automáticos
            if hasattr(self, "auto_points_task") and not self.auto_points_task.done():
                self.auto_points_task.cancel()
                try:
                    await self.auto_points_task
                except asyncio.CancelledError:
                    pass

            # Salvar dados antes de fechar
            self.save_data()

            # Fechar conexão
            await super().close()

            print(f"✅ Bot fechado corretamente: {self.channel_name}")
        except Exception as e:
            print(f"❌ Erro ao fechar bot: {e}")

    # ===== COMANDOS =====

    @commands.command(name="oi")
    async def hello(self, ctx):
        """Saudação personalizada"""
        await ctx.send(f"Olá @{ctx.author.name}! 👋 Bem-vindo ao chat!")
        self.gui.log("🤖", f"[{self.channel_name}] Saudando {ctx.author.name}", "bot")

    @commands.command(name="dados")
    async def roll_dice(self, ctx):
        """Rola um dado de 1 a 6"""
        numero = random.randint(1, 6)
        await ctx.send(f"🎲 @{ctx.author.name} rolou um {numero}!")
        self.gui.log(
            "🎲", f"[{self.channel_name}] {ctx.author.name} rolou {numero}", "game"
        )

    @commands.command(name="pontos")
    async def check_points(self, ctx):
        """Verifica pontos do usuário"""
        points = self.user_points[ctx.author.name]
        await ctx.send(f"💰 @{ctx.author.name} tem {points} pontos!")

    @commands.command(name="top")
    async def top_users(self, ctx):
        """Top 5 usuários com mais pontos"""
        sorted_users = sorted(
            self.user_points.items(), key=lambda x: x[1], reverse=True
        )[:5]
        top_list = " | ".join(
            [f"{i+1}. {user}: {pts}pts" for i, (user, pts) in enumerate(sorted_users)]
        )
        await ctx.send(f"🏆 Top 5: {top_list}")

    @commands.command(name="comandos")
    async def list_commands(self, ctx):
        """Lista todos os comandos disponíveis"""
        await ctx.send(
            "📋 Comandos: !oi, !dados, !pontos, !top, !piada, !hora, !comandos"
        )

    @commands.command(name="piada")
    async def joke(self, ctx):
        """Conta uma piada aleatória"""
        piadas = [
            "Por que o Python foi ao psicólogo? Tinha muitos imports!",
            "O que o JavaScript disse pro HTML? Você tem class!",
            "Como o programador pede café? Java, please!",
            "Por que o bot não conta segredos? Porque tem muitos logs!",
            "O que é um bug na selva? Um inseto programador!",
            "Por que o CSS foi ao terapeuta? Tinha problemas de alinhamento!",
        ]
        await ctx.send(f"😄 {random.choice(piadas)}")

    @commands.command(name="hora")
    async def current_time(self, ctx):
        """Mostra horário atual"""
        now = datetime.now().strftime("%H:%M:%S")
        await ctx.send(f"🕐 Horário atual: {now}")

    @commands.command(name="moeda")
    async def flip_coin(self, ctx):
        """Cara ou coroa"""
        resultado = random.choice(["Cara 🪙", "Coroa 🪙"])
        await ctx.send(f"@{ctx.author.name} jogou a moeda... {resultado}!")

    async def event_subscription(self, subscription):
        """Evento de nova inscrição"""
        username = subscription.user.name
        await subscription.channel.send(f"🎉 Obrigado pela sub, @{username}! 💜")
        self.user_points[username] += 500
        self.gui.log("🎉", f"[{self.channel_name}] Nova sub de {username}!", "event")
        self.save_data()
