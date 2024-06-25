import asyncio

from async_server.socket_server import AsyncSocketServer
from rtsp_connect.manager import ProcessManager

from config import HOST, SOCKET_PORT

if __name__ == "__main__":
    process_manager_main = ProcessManager()
    server = AsyncSocketServer(HOST, SOCKET_PORT, process_manager_main)
    asyncio.run(server.run_server())
