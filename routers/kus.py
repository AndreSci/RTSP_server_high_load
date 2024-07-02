import datetime
from fastapi import APIRouter, Request
from misc.logger import Logger
from misc.glob_process import ProcessConstManager
# from data_base.cameras import CamerasDB
# from data_base.add_event import EventDB
from typing import Any
import pymysql

from data_base.models import t_camera
from data_base.database import GlobControlDatabase
from typing import Dict

logger = Logger()

kus_router = APIRouter(
    tags=['KusAsync']
)


@kus_router.on_event("startup")
async def startup():
    db_con = GlobControlDatabase.get_database()
    try:
        await db_con.connect()
    except pymysql.err.OperationalError as osex:
        logger.warning(f"Can't connect to DATABASE: {osex}")
    except Exception as ex:
        logger.exception(f"Exception in: {ex}")


@kus_router.on_event("shutdown")
async def shutdown():
    db_con = GlobControlDatabase.get_database()
    try:
        await db_con.disconnect()
    except Exception as ex:
        logger.exception(f"Exception in: {ex}")


# @kus_router.get('/action.save')
# async def save_frame_asterisk(answer_id: Any, caller_id: Any, request: Request):
#     """ Запрашиваем последний кадр и сохраняем его в папку согласно настройкам settings.ini """
#
#     async with LOCK:
#         # Защита от перезапуска камер
#         pass
#
#     ret_value = {"RESULT": "ERROR", "STATUS_CODE": 400, "DESC": "", "DATA": list()}
#
#     user_ip = request.client
#
#     # получаем данные из параметров запроса
#     answer_id = str(answer_id)
#     caller_id = str(caller_id)
#
#     logger.event(f"Обращение к rtsp от адреса {user_ip}. Абонент {caller_id} связался с {answer_id}")
#
#     db_request_cams = CamerasDB().find_camera(caller_id)
#
#     if db_request_cams['RESULT'] != "SUCCESS":
#         logger.error(db_request_cams)
#         return db_request_cams
#
#     try:
#         for it in db_request_cams.get('DATA'):
#
#             cameras_process = ProcessConstManager.get_process_manager()
#             # Получить кадр
#             image = await cameras_process.get_frame(it.get('FName'))
#
#             # Получаем дату и генерируем полный путь к файлу
#             date_time = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
#             file_name = f"{it.get('FName')}-{caller_id}-{date_time}.jpg"
#             file_path = f"{ConstManager.get_photo_path()}{file_name}"
#
#             with open(file_path, 'wb') as file:
#                 # Сохраняем кадр в файл
#                 file.write(image)
#
#             logger.event(f"Успешно создан файл: {file_name}")
#
#             # Добавляем событие в БД
#             db_add = EventDB().add_photo(caller_id, answer_id, it.get('FName'), file_name)
#
#             if db_add:
#                 ret_value['DATA'].append({"file_name": file_name})
#                 ret_value["RESULT"] = "SUCCESS"
#                 ret_value['STATUS_CODE'] = 200
#             else:
#                 logger.warning(f"Не удалось внести данные в БД: {db_add}")
#                 ret_value['DESC'] = ret_value['DESC'] + f"Не удалось внести данные в БД: {file_name}."
#
#     except Exception as ex:
#         logger.exception(f"Не удалось получить/сохранить кадр из камеры: {ex}")
#
#     return ret_value
#
#
# @kus_router.get('/action.save2')
# async def save_frame_asterisk(answer_id: Any, caller_id: Any, request: Request):
#     """ Запрашиваем последний кадр и сохраняем его в папку согласно настройкам settings.ini """
#
#     async with LOCK:
#         # Защита от перезапуска камер
#         pass
#
#     ret_value = {"RESULT": "ERROR", "STATUS_CODE": 400, "DESC": "", "DATA": list()}
#
#     user_ip = request.client
#
#     # получаем данные из параметров запроса
#     answer_id = str(answer_id)
#     caller_id = str(caller_id)
#
#     logger.event(f"Обращение к rtsp от адреса {user_ip}. Абонент {caller_id} связался с {answer_id}")
#
#     db_request_cams = CamerasDB().find_camera(caller_id)
#
#     if db_request_cams['RESULT'] != "SUCCESS":
#         logger.error(db_request_cams)
#         return db_request_cams
#
#     try:
#         for it in db_request_cams.get('DATA'):
#
#             cameras_process = ProcessConstManager.get_process_manager()
#             # Получить кадр
#             image = await cameras_process.get_frame(it.get('FName'))
#
#             # Получаем дату и генерируем полный путь к файлу
#             date_time = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
#             file_name = f"{it.get('FName')}-{caller_id}-{date_time}.jpg"
#             file_path = f"{ConstManager.get_photo_path()}{file_name}"
#
#             with open(file_path, 'wb') as file:
#                 # Сохраняем кадр в файл
#                 file.write(image)
#
#             logger.event(f"Успешно создан файл: {file_name}")
#
#             # Добавляем событие в БД
#             db_add = EventDB().add_photo(caller_id, answer_id, it.get('FName'), file_name)
#
#             if db_add:
#                 ret_value['DATA'].append({"file_name": file_name})
#                 ret_value["RESULT"] = "SUCCESS"
#                 ret_value['STATUS_CODE'] = 200
#             else:
#                 logger.warning(f"Не удалось внести данные в БД: {db_add}")
#                 ret_value['DESC'] = ret_value['DESC'] + f"Не удалось внести данные в БД: {file_name}."
#
#     except Exception as ex:
#         logger.exception(f"Не удалось получить/сохранить кадр из камеры: {ex}")
#
#     return ret_value
#

# @kus_router.post('/action.update_cams')
# async def update_cameras():
#     """ Даём команду RTSP серверу на обновления списка работающих камер """
#
#     async with LOCK:
#         ret_value = {"RESULT": "ERROR", "DESC": '', "DATA": dict()}
#
#         try:
#             # Запрашиваем у БД список камер
#             # new_cams = CamerasDB().take_cameras()
#             cameras_process = ProcessConstManager.get_process_manager()
#             kill_all = cameras_process.kill_all()
#
#             if kill_all.get('result'):
#
#                 set_ini = load_settings()
#                 start_process(set_ini)
#
#                 ret_value['RESULT'] = "SUCCESS"
#             else:
#                 ret_value['DESC'] = kill_all.get('desc')
#         except Exception as ex:
#             logger.exception(f"Исключение вызвало: {ex}")
#             ret_value['DESC'] = f"Исключение в работе сервиса: {ex}"
#
#     return ret_value


@kus_router.get('/action.get_cameras', response_model=Dict)
async def get_cameras(user: str, password: str, skip: int = 0, limit: int = 500):
    """ Даём команду RTSP серверу на обновления списка работающих камер """
    ret_value = {"RESULT": "ERROR", "DESC": '', "DATA": dict(), 'FULL_CAMERAS': list()}

    if user == 'admin' and password == 'admin':
        db_con = GlobControlDatabase.get_database()

        query = t_camera.select().offset(skip).limit(limit)

        results = await db_con.fetch_all(query)
        # results_dict = [dict(result) for result in results]

        # Данный метод нужен для Димы (распознавание номеров)
        ret_value = {'RESULT': 'SUCCESS', 'DATA': dict(), 'FULL_CAMERAS': list()}

        # Требуется для корректного вывода времени и перестройки в bool числа (требования ТЗ)
        for camera in results:
            camera = dict(camera)
            ret_value['DATA'][camera['FName']] = camera['FRTSP']

            try:
                ret_value['FULL_CAMERAS'].append({"FID": camera['FID'],
                                                  "FName": camera['FName'],
                                                  "FDateCreate": str(camera['FDateCreate']),
                                                  "FRTSP": camera['FRTSP'],
                                                  "FDesc": camera['FDesc'],
                                                  "isPlateRec"
                                                  "Enable": True if camera['isPlateRecEnable'] == 1 else False})
            except Exception as ex:
                logger.exception(f"Exception in: {ex}")

    else:
        ret_value['DESC'] = f"Access Denied: Wrong UserName/Password"

    return ret_value
