import av
import av.datasets
import io
import os
import datetime
import queue
import threading
import time
import logging
from enum import Enum

from typing import Any, Dict
from misc.logger import Logger
from misc.clearing import CleanerDir

from config import SAVED_VIDEO_DIR

logger = Logger()

# Убираем сообщения связанные с ошибками чтения потока RTSP (из-за плохой связи с камерами)
logging.basicConfig()
# av.logging.set_level(av.logging.PANIC)
av.logging.set_level(av.logging.FATAL)
logging.getLogger('libav').setLevel(logging.ERROR)

TIME_WAIT_FRAME = 1.5
FILE_FORMAT = 'mp4'
SAVING_DIR = os.path.join(os.getcwd(), SAVED_VIDEO_DIR)
PERIOD_TO_SAVE = 300  # Число сохранённых кадров в файл

FRAME_STATUS_NEW = 201
FRAME_STATUS_ERROR = 202
FRAME_STATUS_OLD = 203


class ProcessData:
    """ Класс управление меж процессными данными """
    def __init__(self, name: str, url: str,
                 get_frame: bool = False, frame: bytes = b'',
                 save_video: bool = False, new_event: bool = False,
                 time_fps: int = 0.1):

        self.name = name
        self.url = url
        self.get_frame = get_frame
        self.frame = frame
        self.save_video = save_video
        self.new_event = new_event
        self.time_fps = time_fps  # Базово установил 10 кадров в секунду обновлять

    def get_dict(self) -> Dict:
        return {"name": self.name,
                 "url": self.url,
                 "get_frame": self.get_frame,
                 "frame": self.frame,
                 'save_video': self.save_video,
                 'new_event': self.new_event,
                'time_fps': self.time_fps}

    def update_data(self, manage_dict: dict) -> bool:
        self.name = manage_dict.get('name')
        self.url = manage_dict.get('url')
        self.get_frame = manage_dict.get('get_frame')
        self.frame = manage_dict.get('frame')
        self.save_video = manage_dict.get('save_video')
        self.new_event = manage_dict.get('new_event')

        return True

    def __str__(self):
        return f"{self.get_dict()}"


class ConnectStatus(Enum):
    Connecting = 1
    Connected = 2


class SavingControl:
    @staticmethod
    def check_dir(saving_dir: str) -> bool:
        """ Функция служит для проверки директории и создания для сохранения видео """
        try:
            dir_list = saving_dir.split("\\")

            index = 0
            check_dir: str = ''

            for it in dir_list:
                index += 1
                if ':' in it and index == 1:
                    check_dir = check_dir + it + '\\'
                    continue

                check_dir = check_dir + it + '\\'

                if not os.path.isdir(check_dir):
                    os.mkdir(check_dir)
        except Exception as ex:
            print(f"Исключение при попытке проверить и создать директорию для сохранения видео: {ex}")
            return False

        return True


class VideoRTSP:
    """ Класс для чтения видео потока из камеры передачи его в байт-код и сохранения в файл
    """

    def __init__(self, cam_name: str, url: str, saving_dir: str = None, save_video: bool = True):
        self.url = url
        self.cam_name = cam_name

        self.connect_status = ConnectStatus.Connecting

        self.time_file = datetime.datetime.now()
        self.file_name = str(datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))

        self.current_data = ''
        self.dir_save = ''
        self.saving_dir = saving_dir
        self.saving_dir_for_cam = ''
        self.saving_dir_for_days = ''
        self.file_name_with_dir = ''

        self.gop = 40  # опорный кадр
        self.first_index_gop = 0
        self.queue_gop = queue.Queue()
        self.queue_buffer = queue.Queue()
        self.median_buffer_size = 0

        self.save_video_bool = SavingControl.check_dir(self.dir_save)
        self.need_save_video = save_video

        self.allow_read_frame = False

        self.last_image = b''
        self.ret_image = b''

        self.restart_cam_connection = True
        self.save_frame = False
        self.last_time_save_frame = datetime.datetime.now()
        self.last_time_new_frame = datetime.datetime.now()
        self.last_frame_size = (0, 0)

        self.th_do_frame_lock = threading.Lock()

        self.allow_read_cam = True
        self.thread_object = threading.Thread
        self.miss_frame_index = 0

    def check_date(self, date_from: datetime.datetime) -> bool:
        """ Функция триггер на изменение даты """
        date_now = datetime.datetime.now()
        if date_now.day == date_from.day:
            return True
        else:
            self.time_file = datetime.datetime.now()
            return False

    def __upgrade_saving_dir(self):

        if self.saving_dir:
            self.saving_dir_for_cam = self.saving_dir + self.cam_name + '\\'

            self.saving_dir_for_days = (f"{self.saving_dir_for_cam}"
                                        f"{str(datetime.datetime.now().strftime('%Y-%m-%d'))}\\")
        else:
            self.saving_dir = os.path.join(os.getcwd(), f"video_saves\\")
            self.saving_dir_for_cam = os.path.join(os.getcwd(), f"video_saves\\{self.cam_name}\\")
            self.saving_dir_for_days = os.path.join(os.getcwd(), f"video_saves\\{self.cam_name}\\"
                                                                 f"{str(datetime.datetime.now().strftime('%Y-%m-%d'))}\\")

        self.save_video_bool = SavingControl.check_dir(self.saving_dir_for_days)

    def __update_file_name(self):
        print("Создаем новый файл для записи истории видео...")

        try:
            if os.path.exists(self.file_name_with_dir):
                new_file_name = str(datetime.datetime.now().strftime("%H-%M-%S"))
                dst = f"{self.saving_dir_for_days}{self.file_name} {new_file_name}.{FILE_FORMAT}"
                os.rename(self.file_name_with_dir, dst)

            if not self.current_data == str(datetime.datetime.now().strftime("%Y-%m-%d")):
                self.current_data = str(datetime.datetime.now().strftime("%Y-%m-%d"))
                self.__upgrade_saving_dir()

            self.file_name = str(datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))

            self.file_name_with_dir = f"{self.saving_dir_for_days}{self.file_name}.{FILE_FORMAT}"
            print(self.file_name_with_dir)
        except Exception as ex:
            logger.warning(f"Попытка записи в файл завершилась с ошибкой: {ex}")

        try:
            # Подчищаем папку от устаревших файлов и папок
            # Для защиты от зависания используем создание нового процесса без ожидания его завершения
            pr1 = threading.Thread(target=CleanerDir.clear_dir, args=[self.saving_dir_for_cam,], daemon=True)
            pr1.start()
        except Exception as ex:
            logger.exception(f"Исключение при попытке создать поток: {ex}")

    def start(self) -> bool:
        """ Функция для запуска чтения камеры в свободном потоке threading """
        try:
            self.thread_object = threading.Thread(target=self.__start, daemon=True)
            self.thread_object.start()
            return True
        except Exception as ex:
            logger.exception(f"Исключение вызвало: {ex}")
        return False

    def __start(self) -> Any:
        """ Функция подключения и повторного переподключения к камере"""

        while self.allow_read_cam:
            time.sleep(1)
            logger.event(f"Попытка подключиться к камере: {self.cam_name} - {self.url}")

            try:
                self.__read_camera()

            except Exception as ex:
                logger.exception(f"Исключение вызвала ошибка в работе с "
                                 f"видео потоком для камеры {self.cam_name}: {ex}")

            logger.warning(f"{self.cam_name} - Камера отключена: {self.url}")

    def find_gop(self, index: int, buffer_size: int) -> bool:
        """ Функция собирает данные и находит средний размер не опорного кадра
        и на полученных данных определяет опорный кадр и высчитывает его номер """

        self.queue_buffer.put(buffer_size)

        if self.queue_buffer.qsize() >= 10:
            self.queue_buffer.get_nowait()

            self.median_buffer_size = int(sum(list(self.queue_buffer.queue)) / self.queue_buffer.qsize())

            if buffer_size / self.median_buffer_size > 3:
                self.queue_gop.put(index)

                if self.queue_gop.qsize() > 4:
                    self.queue_gop.get()

                previous_index = 0
                for num_index in list(self.queue_gop.queue):
                    result = num_index - previous_index

                    if 150 > result > 5:
                        self.gop = result
                        previous_index = num_index

                if not self.first_index_gop:
                    self.first_index_gop = self.gop

                # print(f"index: {self.gop} - buffer_size: {buffer_size} - first_index_gop: {self.first_index_gop}")
                return True

        return False

    def __read_camera(self):

        while True:
            self.connect_status = ConnectStatus.Connecting

            input_ = av.open(self.url, mode='r', timeout=10)

            in_stream = input_.streams.video[0]
            av_options = {'avoid_negative_ts': '-1'}
            frag_dts = 0  # 1st original reference timestamp of a fragment
            index_err = 0

            self.connect_status = ConnectStatus.Connected

            while True:
                # Защита от множественной попытки повторно подключиться к камере (возникали при смене настроек камеры)
                # Ниже есть сброс счетчика если хотя бы один кадр прочитался
                if index_err == 10:
                    break
                else:
                    index_err += 1

                # Пред-создание директории для сохранения видео потока в файл
                if self.need_save_video:
                    self.__update_file_name()

                    output = av.open(self.file_name_with_dir, "w")
                    output.container_options.update(av_options)
                    out_stream = output.add_stream(template=in_stream)

                index = 0
                index_for_bytes = 0
                self.first_index_gop: int = None
                its_end = False

                # Число сохранённых кадров в файл
                time_to_new_save = PERIOD_TO_SAVE

                for packet in input_.demux(in_stream):

                    # We need to skip the "flushing" packets that `demux` generates.
                    if packet.dts is None:
                        continue

                    try:
                        # Пробуем сохранить кадр в байт-код
                        frame: list = packet.decode()

                        index_err = 0  # Защита от множественной попытки повторно подключиться к камере

                        it_gop = False

                        if self.need_save_video:
                            it_gop = self.find_gop(index, packet.buffer_size)

                        # Попытка сохранить кадр в файл если таково требуется
                        if self.save_video_bool and self.need_save_video and len(frame) > 0:
                            index += 1

                            # Пересчитываем временную линию видео
                            orig_dts = packet.dts
                            packet.dts = packet.dts - frag_dts
                            packet.pts = packet.pts - frag_dts

                            if it_gop:
                                if (index + self.gop) > time_to_new_save and not its_end:
                                    # print("I HAVE FOUND NEW INDEX")
                                    its_end = True
                                    time_to_new_save = index + self.gop - 1

                            if index >= time_to_new_save:
                                frag_dts = orig_dts
                                break

                            try:
                                # Сохраняем кадр в файл
                                packet.stream = out_stream
                                try:
                                    output.mux(packet)
                                except ValueError as vex:
                                    ...

                            except Exception as sex:
                                logger.exception(f"Исключение в сохранении файла: {sex}")

                        # Начинаем конвертировать кадр в байт-код формата JPEG
                        if self.save_frame or index_for_bytes < 5:

                            # Заглушка для сброса пустых кадров после подключения
                            if index_for_bytes < 5:
                                index_for_bytes += 1

                            if len(frame) > 0:  # Избегаем исключения связанного с битым пакетом
                                self.save_frame = False

                                image = frame[0].to_image()
                                self.last_frame_size = image.size
                                img_byte_arr = io.BytesIO()
                                image.save(img_byte_arr, format='JPEG')
                                self.last_image = img_byte_arr.getvalue()
                                self.last_time_new_frame = datetime.datetime.now()

                    except Exception as ex:
                        print(f"Исключение в работе чтения packet: {ex}")

                output.close()

            input_.close()

    def load_no_signal_pic(self):
        """ Функция подгружает картинку с надписью NoSignal """
        with open('./resources/no_signal.jpg', "rb") as file:
            self.ret_image = file.read()

    def take_frame(self):
        """ Функция запроса кадра у камеры, меняет ключ save_frame = True и ожидает его изменения на False """

        self.save_frame = True

        index = 0

        while index < 2000:  # Защита от сбитого времени на сервере
            index += 1

            if not self.save_frame:

                self.last_time_save_frame = datetime.datetime.now()
                print("New frame saved")
                break

            time.sleep(0.005)

        if self.save_frame is True:
            # Не удалось обновить кадр за указанное время
            return b''
        else:
            return self.last_image


def create_cams_threads(new_cams: dict) -> Dict[str, VideoRTSP]:
    """ Функция создает словарь с объектами класса VideoRTSP и запускает от их имени потоки """

    ret_value = dict()

    # Создаем объекты с потоками для камер
    for key in new_cams:
        key = str(key).upper()
        ret_value[key] = VideoRTSP(str(key), new_cams[key])
        ret_value[key].load_no_signal_pic()
        ret_value[key].start()
        time.sleep(0.1)

    return ret_value


def create_cam_connect(manager_cameras: dict, cam_name: str,
                       fps_time: float, save_video: bool = False) -> Any:
    """ Ядро созданного процесса
    cameras: словарь всех камер с параметрами
    cam_name: имя камеры с которой будем работать из словаря
    fps_time: скорость кадров ожидается от камеры
    """

    logger_proc = Logger()

    camera = VideoRTSP(manager_cameras[cam_name].get('name'),
                       manager_cameras[cam_name].get('url'),
                       save_video=save_video)

    camera.load_no_signal_pic()
    camera.start()

    logger_proc.event(f"Создан процесс для камеры: {manager_cameras[cam_name].get('name')}")

    while True:

        try:
            if manager_cameras[cam_name].get('stop_action'):
                break
            elif manager_cameras[cam_name].get('get_frame'):
                cam_data = manager_cameras[cam_name]

                # Буферное время для записи нового кадра (должно снять часть нагрузки)
                cam_data['frame'] = camera.take_frame()
                cam_data['frame_size'] = camera.last_frame_size
                cam_data['last_time_new_frame'] = str(camera.last_time_new_frame)
                cam_data['frame_status'] = FRAME_STATUS_NEW

                cam_data['connection_status'] = camera.connect_status

                cam_data['get_frame'] = False

                manager_cameras[cam_name] = cam_data

            elif manager_cameras[cam_name].get('new_event'):
                cam_data = manager_cameras[cam_name]

                camera.need_save_video = cam_data['save_video']
                cam_data['new_event'] = False

                manager_cameras[cam_name] = cam_data

        except Exception as ex:
            logger_proc.exception(f"Исключение вызвало: {ex}")

        time.sleep(0.005)

    logger_proc.warning(f"Процесс связанный с камерой: {cam_name} завершил свою работу!")


if __name__ == "__main__":
    VideoRTSP("CAM2", "rtsp://admin:admin@192.168.48.188", save_video=True).start()

    input()  # Заглушка от завершения работы программы
