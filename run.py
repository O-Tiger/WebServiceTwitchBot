"""
Twitch Bot Dashboard - Flask Application
Arquivo principal de execução
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.web.app import app, socketio, start_background_tasks

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

    from dotenv import load_dotenv

    load_dotenv()
    debug_env = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))

    # 🆕 Iniciar background tasks
    start_background_tasks()

    try:
        socketio.run(
            app,
            debug=debug_env,
            host=host,
            port=port,
            use_reloader=False,
            log_output=True,  # Mostrar logs
        )

    except KeyboardInterrupt:
        print("\n\n")
        print("╔════════════════════════════════════════════════════╗")
        print("║                                                    ║")
        print("║           🛑  Servidor encerrado com sucesso       ║")
        print("║                                                    ║")
        print("╚════════════════════════════════════════════════════╝")
        print("\nObrigado por usar o Twitch Bot Dashboard! 👋\n")
        sys.exit(0)
