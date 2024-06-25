import datetime
import multiprocessing as mp
import time
from rtsp_connect.resources_loader import ResLoader


class ProcessManager:
    """ Класс организует межпроцессную-связь и создает процессы """
    def __init__(self):
        # Связь с процессом
        self.manager = mp.Manager()
        self.manager.connect()
        self.manager_cameras = self.manager.dict()

        # Пустой кадр
        self.no_frame = ResLoader.load_no_signal()

        # Кадр из камеры
        self.frames_from_cams = {'CAM999': {'time': datetime.datetime.now(),
                                            'frame': b''}}

    async def get_frame(self, cam_name: str = None) -> bytes:

        return self.no_frame
