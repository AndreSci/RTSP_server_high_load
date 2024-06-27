import ctypes
from misc.settings import SettingsIni
from misc.logger import Logger
from misc.glob_process import ProcessConstManager
from misc.consts import ConstManager
from data_base.cameras import CamerasDB
from rtsp_connect.manager import ProcessManager


# Метод заглушка для сохранения всех камер в файл
# GlobControlProcessorManager.turn_on_save()


def load_settings() -> dict:
    settings = SettingsIni()
    settings.load_data_from_file()
    data = settings.take_settings_data()

    # Если нужно сохранять историю видео в файл
    # if settings.save_video():
    #     GlobControlProcessorManager.turn_on_save()

    # Загружаем глобальные константы
    ConstManager.set_fps(data.get('fps'))
    ConstManager.set_photo_path(data.get('photo_path'))

    if data.get("cameras_from_ini"):
        print("Загрузка списка камер из settings.ini")
        ConstManager.set_cameras(data.get("CAMERAS"))
        ConstManager.set_cameras_full(data.get("FULL_CAMERAS"))
    else:
        print("Загрузка списка камер из БД")
        res = CamerasDB().take_cameras()
        ConstManager.set_cameras(res.get("DATA"))
        ConstManager.set_cameras_full(res.get("FULL_CAMERAS"))

    # Обьявляем логирование
    logger = Logger(settings.take_log_path())

    return data


def start_process(settings: dict):
    # Меняем имя терминала
    ctypes.windll.kernel32.SetConsoleTitleW(f"RSTP interface port: {settings['port']} - (use PyAv)")

    proc_res = ProcessManager(ConstManager.get_cameras())
    ProcessConstManager.set_process_manager(proc_res)
