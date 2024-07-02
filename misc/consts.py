import asyncio

FPS = 15
PHOTO_PATH = ''
CAMERAS = dict()
FULL_CAMERAS = dict()
LOCK = asyncio.Lock()

GLOB_SETTINGS = {'cam_for_save': {'CAM2': False, 'CAM3': True},
                 'cameras': {'CAM2': 'rtsp://admin:admin@192.168.48.188'},
                 'cameras_from_ini': True,
                 'fps': '20',
                 'full_cameras': [{'FDateCreate': None,
                                   'FDesc': None,
                                   'FID': None,
                                   'FName': 'CAM2',
                                   'FRTSP': 'rtsp://admin:admin@192.168.48.188',
                                   'isPlateRecEnable': False}],
                 'host': '0.0.0.0',
                 'log_path': '.\\logs\\',
                 'save_video': False,
                 'photo_path': '.\\PHOTOS\\RTSP server (Asterisk)\\',
                 'port': '80'}


class ConstManager:

    @staticmethod
    def set_glob_settings(set_ini: dict) -> bool:
        global GLOB_SETTINGS
        GLOB_SETTINGS = set_ini
        return True

    @staticmethod
    def set_fps(fps: int) -> bool:
        global FPS

        if type(fps) is int:
            FPS = fps
        else:
            try:
                FPS = int(fps)
            except Exception as ex:
                print(f"ConstChanger.set_fps: Исключение в попытке преобразовать данные к типу int: {ex}")
                return False
        return True

    @staticmethod
    def set_photo_path(path: str) -> bool:
        global PHOTO_PATH
        PHOTO_PATH = path

        return True

    @staticmethod
    def set_cameras(cameras: dict) -> bool:
        global CAMERAS
        CAMERAS = cameras

        return True

    @staticmethod
    def set_cameras_full(full_cameras: dict) -> bool:
        global FULL_CAMERAS
        FULL_CAMERAS = full_cameras

        return True

    @staticmethod
    def get_cameras() -> dict:
        ret_value = dict()
        ret_value['cameras'] = GLOB_SETTINGS.get('cameras')
        ret_value['cam_for_save'] = GLOB_SETTINGS.get('cam_for_save')
        ret_value['save_video'] = GLOB_SETTINGS.get('save_video')

        return ret_value
