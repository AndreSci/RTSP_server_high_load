import asyncio
import socket

from rtsp_connect.manager import ProcessManager


class AsyncSocketServer:
    def __init__(self, host, port, process_manager: ProcessManager):
        self.host = host
        self.port = port

        self.process_manager = process_manager

    async def handle_client(self, client):
        loop = asyncio.get_event_loop()
        try:
            while True:
                data = await loop.sock_recv(client, 255)
                if not data:
                    break
                response = await self.process_request(data)
                await loop.sock_sendall(client, response)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client.close()

    async def process_request(self, data):
        ret_value = await self.process_manager.get_frame('CAM1')
        return ret_value

    async def run_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(100)
        server.setblocking(False)

        loop = asyncio.get_event_loop()
        print(f"Server running on {self.host}:{self.port}")
        while True:
            client, addr = await loop.sock_accept(server)
            print(f"Accepted connection from {addr}")
            loop.create_task(self.handle_client(client))
