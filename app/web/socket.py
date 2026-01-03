from flask_socketio import SocketIO

socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    ping_timeout=60, 
    ping_interval=25,  
    engineio_logger=False,  
    logger=False,
    transports=["websocket", "polling"],
    manage_session=False
)