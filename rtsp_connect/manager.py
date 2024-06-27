import asyncio
import datetime
import multiprocessing as mp
import time
from typing import Dict
from rtsp_connect.resources_loader import ResLoader
from misc.logger import Logger
from rtsp_connect.connection import create_cam_connect, ConnectStatus

logger = Logger()
LOCK_NEW_FRAME = asyncio.Lock()
TIME_WAIT = 2


class ProcessManager:
    """ Класс организует межпроцессную-связь и создает процессы """
    def __init__(self, cameras: dict,
                 frame_life: int = 0.1,
                 frame_life_time_slow: int = 1):
        """ Принимает словарь, где содержится информация о всех камерах """
        self.cameras = cameras

        # Настройки
        self.frame_time_life = frame_life
        self.frame_life_time_slow = frame_life_time_slow
        self.fps_time = 10
        # Связь с процессом
        self.manager = mp.Manager()
        self.manager.connect()
        self.manager_cameras = self.manager.dict()

        # Организуем данные для межпроцессной связи
        self.it_started = False
        self.__organise_cameras()
        self.processes_dict: Dict[mp.Process] = None
        self.last_request = {'CAM999': datetime.datetime.now()}

        # Пустой кадр
        self.no_frame = ResLoader.load_no_signal()

        # Кадр из камеры
        self.frames_from_cams = {'CAM999': {'time': datetime.datetime.now(),
                                            'frame': b''}}

    async def get_frame(self, cam_name: str = None) -> bytes:
        """ Функция возвращает последний успешный кадр из указанной камеры """
        cam_name = cam_name.upper()

        if cam_name in self.frames_from_cams:
            # считаем время от последнего кадра
            delta_time_frame = (datetime.datetime.now() - self.frames_from_cams[cam_name].get(time)).total_seconds()

            if delta_time_frame > self.frame_time_life:
                # Обновляем кадр если кадр устарел
                await self.__new_frame(cam_name)
                delta_time_frame = (datetime.datetime.now() - self.frames_from_cams[cam_name].get(time)).total_seconds()

            if delta_time_frame < self.frame_life_time_slow:
                # Если пройдено времени от последнего успешного кадра меньше чем frame_life_time_slow
                # отправляем последний успешный кадр
                return self.frames_from_cams[cam_name].get('frame')

        else:
            print(f"The required camera could not be found: {cam_name}")

        return self.no_frame

    async def __new_frame(self, cam_name: str):
        """ Функция запроса кадра у процесса """
        async with LOCK_NEW_FRAME:
            # Проверяем нет ли запроса на данный момент нового кадра
            if cam_name in self.last_request:
                delta_time_frame = (datetime.datetime.now() - self.last_request[cam_name].get(time)).total_seconds()
                if delta_time_frame < self.frame_time_life:
                    # Если время с последнего запроса еще не прошло больше чем требуется, выходим из функции
                    return
            else:
                self.last_request[cam_name] = datetime.datetime.now()

        start_time = datetime.datetime.now()

        if cam_name in self.manager_cameras:
            # Защита от неизвестной камеры и отправки флага на запрос нового кадра
            camera = self.manager_cameras.get(cam_name)

            camera['get_frame'] = True
            self.manager_cameras[cam_name] = camera
        else:
            logger.warning(f"The required camera could not be found: {cam_name}")
            return

        while TIME_WAIT < (datetime.datetime.now() - start_time).total_seconds():
            # Обновляем время для очереди запросов
            self.last_request[cam_name] = datetime.datetime.now()

            if not self.manager_cameras[cam_name]['get_frame']:
                self.frames_from_cams[cam_name]['frame'] = self.manager_cameras[cam_name]['frame']
                break
            else:
                await asyncio.sleep(0.05)

        # await asyncio.sleep(0.1)
        # self.frames_from_cams[cam_name]['time'] = datetime.datetime.now()
        # self.frames_from_cams[cam_name]['frame'] = self.no_frame

    def __organise_cameras(self) -> bool:
        """ Структурируем данные """
        try:
            for name in self.cameras:
                name = str(name).upper()
                self.manager_cameras[name] = {"name": name,
                                              "url": self.cameras[name],
                                              "get_frame": True,
                                              "frame": b'',
                                              'need_save_video': self.cameras[name]}
        except Exception as ex:
            print(f"Критическая ошибка __organise_cameras: {ex}")
            raise

        return True

    def start(self) -> bool:
        """ Создаем процессы """
        if not self.it_started:
            self.it_started = True

            for cam_name in self.manager_cameras:
                self.processes_dict[cam_name] = mp.Process(target=create_cam_connect,
                                                           args=[self.manager_cameras,
                                                                 cam_name,
                                                                 self.fps_time,
                                                                 self.manager_cameras[cam_name].get('need_save_video')],
                                                           daemon=True)
                self.processes_dict[cam_name].start()

        return True
