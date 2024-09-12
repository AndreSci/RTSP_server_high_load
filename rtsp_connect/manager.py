import asyncio
import datetime
import multiprocessing as mp
from typing import Dict
from rtsp_connect.resources_loader import ResLoader
from misc.logger import Logger
from rtsp_connect.connection import create_cam_connect, ProcessData

logger = Logger()
LOCK_NEW_FRAME = asyncio.Lock()
TIME_WAIT = 2


class ProcessManager:
    """ Класс организует межпроцессную-связь и создает процессы """
    def __init__(self, cameras: dict,
                 frame_life: int = 0.03,
                 frame_life_time_slow: int = 1):
        """ Принимает словарь, где содержится информация о всех камерах """
        self.cameras = cameras

        # Настройки
        self.frame_time_life = frame_life
        self.frame_life_time_slow = frame_life_time_slow
        # Связь с процессом
        self.manager = mp.Manager()
        self.manager.connect()
        self.manager_cameras = self.manager.dict()

        # Организуем данные для межпроцессной связи
        self.it_started = False
        self.__organise_cameras()
        self.processes_dict: Dict[mp.Process] = {}
        self.last_request_new_frame = {'CAM999': datetime.datetime.now()}

        # Пустой кадр
        self.no_frame = b''

        # Кадр из камеры
        self.frames_from_cams = {'CAM999': {'time': datetime.datetime.now(),
                                            'frame': b''}}

    async def get_frame(self, cam_name: str = None) -> bytes:
        """ Функция возвращает последний успешный кадр из указанной камеры """
        cam_name = cam_name.upper()

        if cam_name in self.frames_from_cams:
            # считаем время от последнего кадра
            delta_time_frame = (datetime.datetime.now() - self.frames_from_cams[cam_name].get('time')).total_seconds()

            if delta_time_frame > self.frame_time_life:
                # print(f"Время от последнего нового кадра: {cam_name} - {delta_time_frame}: {self.frame_time_life}")
                # Обновляем кадр если кадр устарел
                await self.__new_frame(cam_name)

                self.frames_from_cams[cam_name]['time'] = datetime.datetime.now()

            # if delta_time_frame < self.frame_life_time_slow:
            #     # Если пройдено времени от последнего успешного кадра меньше чем frame_life_time_slow
            #     # отправляем последний успешный кадр
            return self.frames_from_cams[cam_name].get('frame')

        else:
            print(f"The required camera could not be found: {cam_name}")

        return self.no_frame

    async def get_frame_res(self, cam_name: str = None) -> bytes:
        # Функция добавлена для стрим соединения через FastAPI
        """ Функция возвращает последний успешный кадр из указанной камеры """

        ret_value = {"result": False, "frame": b''}

        cam_name = cam_name.upper()

        if cam_name in self.frames_from_cams:
            ret_value['result'] = True

            # считаем время от последнего кадра
            delta_time_frame = (datetime.datetime.now() - self.frames_from_cams[cam_name].get('time')).total_seconds()

            if delta_time_frame > self.frame_time_life:
                # Обновляем кадр если кадр устарел
                await self.__new_frame(cam_name)

                self.frames_from_cams[cam_name]['time'] = datetime.datetime.now()

            # if delta_time_frame < self.frame_life_time_slow:
            #     # Если пройдено времени от последнего успешного кадра меньше чем frame_life_time_slow
            #     # отправляем последний успешный кадр
            ret_value['frame'] = self.frames_from_cams[cam_name].get('frame')

        else:
            print(f"The required camera could not be found: {cam_name}")

        return ret_value

    async def __new_frame(self, cam_name: str):
        """ Функция запроса кадра у процесса """
        async with LOCK_NEW_FRAME:
            # Проверяем нет ли запроса на данный момент нового кадра
            if cam_name in self.last_request_new_frame:
                delta_time_frame = (datetime.datetime.now() -
                                    self.last_request_new_frame.get(cam_name)).total_seconds()

                if delta_time_frame < self.frame_time_life:
                    # Если время с последнего запроса еще не прошло больше чем требуется, выходим из функции
                    return
            else:
                self.last_request_new_frame[cam_name] = datetime.datetime.now()

        self.last_request_new_frame[cam_name] = datetime.datetime.now()

        if cam_name in self.manager_cameras:
            # Защита от неизвестной камеры и отправки флага на запрос нового кадра
            camera = self.manager_cameras.get(cam_name)

            camera['get_frame'] = True
            camera['frame'] = b''

            self.manager_cameras[cam_name] = camera
        else:
            logger.warning(f"The required camera could not be found: {cam_name}")
            return
        index = 0

        while index < 50:
            index += 1
            if not self.manager_cameras[cam_name]['get_frame']:
                self.frames_from_cams[cam_name]['frame'] = self.manager_cameras[cam_name].get('frame')
                break
            else:
                await asyncio.sleep(0.05)

        # await asyncio.sleep(0.1)
        # self.frames_from_cams[cam_name]['time'] = datetime.datetime.now()
        # self.frames_from_cams[cam_name]['frame'] = self.no_frame

    def __organise_cameras(self) -> bool:
        """ Структурируем данные """
        try:
            print(self.cameras)
            for name in self.cameras['cameras']:
                name = str(name).upper()
                # Режим сохранения видео для всех камер
                save_video = self.cameras.get('save_video')

                try:
                    # Проверяем нужно ли сохранять видео камере
                    if name in self.cameras['cam_for_save']:
                        if save_video and not self.cameras['cam_for_save'].get(name):
                            save_video = False

                except Exception as ex:
                    logger.exception(f"Exception in get setting for save video for {name}: {ex}")

                self.manager_cameras[name] = {"name": name,
                                              "url": self.cameras['cameras'].get(name),
                                              "get_frame": True,
                                              "frame": b'',
                                              'save_video': save_video,
                                              'new_event': False}
        except Exception as ex:
            print(f"Критическая ошибка __organise_cameras: {ex}")
            raise

        return True

    def start(self) -> bool:
        """ Создаем процессы """
        if not self.it_started:
            self.it_started = True

            # Записываем данные перед стартом процессов
            logger.info(f"{self.manager_cameras}")

            for cam_name in self.manager_cameras:
                cam_name = str(cam_name).upper()
                self.processes_dict[cam_name] = mp.Process(target=create_cam_connect,
                                                           args=[self.manager_cameras,
                                                                 cam_name,
                                                                 0.1,
                                                                 self.manager_cameras[cam_name].get('save_video')],
                                                           daemon=True)
                self.processes_dict[cam_name].start()

                self.frames_from_cams[cam_name] = {'time': datetime.datetime.now(),
                                                    'frame': b''}

        return True
