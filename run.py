"""
Twitch Bot Dashboard - Flask Application
Arquivo principal de execução

Execute: python run.py
Acesse: http://localhost:5000
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.web.app import app, socketio

if __name__ == "__main__":
    print(
        """
    ╔════════════════════════════════════════════════════╗
    ║                                                    ║
    ║      🎮  TWITCH BOT DASHBOARD - PREMIUM v3.0      ║
    ║                                                    ║
    ╚════════════════════════════════════════════════════╝
    
    ✅ Servidor iniciado com sucesso!
    
    🌐 Acesse: http://localhost:5000
    👤 Login: admin / admin
    
    📋 Funcionalidades:
       ✓ Controle de múltiplos canais
       ✓ Chat ao vivo com WebSocket
       ✓ Logs em tempo real
       ✓ Auto respostas personalizadas
       ✓ Estatísticas agregadas
       ✓ API REST completa
    
    ⚡ Pressione CTRL+C para parar
    """
    )

    DebugOptionBool: bool = False
    try:
        DebugOption = int(
            input("Deseja iniciar o servidor em modo de Debug? \n1 - Sim\n2 - Não: \n")
        )
        match DebugOption:
            case 1:
                DebugOptionBool = True
            case 2:
                DebugOptionBool = False
            case _:
                print("Invalid option! Using default (Debug=False)")
    except ValueError:
        print("Invalid input! Using default (Debug=False)")
    except KeyboardInterrupt:
        print("\n\n⚠️  Inicialização cancelada pelo usuário.\n")
        sys.exit(0)

    try:
        socketio.run(app, debug=DebugOptionBool, host="127.0.0.1", port=5000)
    except KeyboardInterrupt:
        print("\n\n")
        print("╔════════════════════════════════════════════════════╗")
        print("║                                                    ║")
        print("║           🛑  Servidor encerrado com sucesso       ║")
        print("║                                                    ║")
        print("╚════════════════════════════════════════════════════╝")
        print("\nObrigado por usar o Twitch Bot Dashboard! 👋\n")
        sys.exit(0)
