""" For start, you need enter in terminal:
uvicorn app --port 8093 --reload
"""
import uvicorn
from fastapi import FastAPI
from routers.frames import camera_router
from routers.kus import kus_router
from data_base.database import GlobControlDatabase
from misc.settings import SettingsIni
from misc.consts import ConstManager
from misc.glob_process import ProcessConstManager
from rtsp_connect.manager import ProcessManager
from config import SETTINGS_FILE

# uvicorn_error = logging.getLogger("uvicorn.error")
# uvicorn_error.disabled = True
# uvicorn_access = logging.getLogger("uvicorn.access")
# uvicorn_access.disabled = True

GlobControlDatabase.set_url('root', '5682881', '192.168.15.10', 3306, 'vig_sender')

# Объявляем главного главаря
app = FastAPI()

# Register routes
app.include_router(camera_router)
app.include_router(kus_router)


# def start_socket():
#     time.sleep(2)
#     socket_server = AsyncSocketServer()
#
#     socket_server.start()
#     asyncio.create_subprocess_exec(socket_server.start_async())


# TODO изучить вопрос по ONVIF  (https://www.onvif.org)

if __name__ == "main":
    """ Запуск через терминал с uvicorn """
    # Напоминание для запуска через терминал
    # uvicorn --no-access-log main:app --port 80
    main_settings = SettingsIni()
    main_settings.load_data_from_file(SETTINGS_FILE)

    ConstManager.set_glob_settings(main_settings.take_settings_data())
    # start_process(set_ini)
    rtsp_manager = ProcessManager(ConstManager.get_cameras())
    rtsp_manager.start()
    ProcessConstManager.set_process_manager(rtsp_manager)


if __name__ == "__main__":
    main_settings = SettingsIni()
    main_settings.load_data_from_file(SETTINGS_FILE)

    ConstManager.set_glob_settings(main_settings.take_settings_data())
    # start_process(set_ini)
    rtsp_manager = ProcessManager(ConstManager.get_cameras())
    rtsp_manager.start()
    ProcessConstManager.set_process_manager(rtsp_manager)

    # start_thread = threading.Thread(target=start_socket, daemon=True)
    # start_thread.start()

    uvicorn.run(app, host='0.0.0.0', port=int(main_settings.settings_data.get('port')), reload=False)
