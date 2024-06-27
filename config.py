from typing import Tuple
HOST = '0.0.0.0'
SOCKET_PORT = 9098
FRAME_TIME_LIFE = 0.1  # sec

SAVED_VIDEO_DIR = "saved_video\\"


class ConfigAccess:
    @staticmethod
    def set_param(host: str, socket_port: int) -> bool:
        global HOST, SOCKET_PORT
        HOST = host
        SOCKET_PORT = socket_port

        return True

    @staticmethod
    def get_param() -> Tuple:
        return HOST, SOCKET_PORT

    @staticmethod
    def get_frame_time_life() -> int:
        return FRAME_TIME_LIFE
