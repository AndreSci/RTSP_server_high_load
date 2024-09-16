import datetime
from typing import Dict
from fastapi import APIRouter, Response, Request, Depends
from misc.logger import Logger
from misc.glob_process import ProcessConstManager
from data_base.cameras import CamerasDB
from data_base.add_event import EventDB
from data_base.models import t_camera, query_cameras_by_caller_id

from data_base.database import GlobControlDatabase
from sqlalchemy.sql import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = Logger()

asterisk_router = APIRouter(
    tags=['AsteriskAsync']
)


@asterisk_router.get('/asterisk_save')
async def save_frame_to_file(caller_id: int, answer_id: int,
                                db: AsyncSession = Depends(GlobControlDatabase.get_db)):
    """ Через caller_id находит в базе данные камер которые связаны (caller_id == tasteriskcaller.FName)"""

    frame = b''

    logger.event(f"Обращение на сохранения кадра: caller_id {caller_id} answer_id {answer_id}")

    try:
        # cameras = CamerasDB().find_cameras_by_caller_id(caller_id)

        result = await db.execute(query_cameras_by_caller_id, {"fname": str(caller_id)})
        cameras_res = result.mappings().fetchall()

        print(cameras_res)

        if len(cameras_res) > 0:
            logger.info(cameras_res, print_it=False)

            for camera in cameras_res:
                cam_name = camera.get('FName')
                cam_id = camera.get('FID')

                cam_manager = ProcessConstManager.get_process_manager()
                # Get frame
                frame = await cam_manager.get_frame(cam_name)

                file_url = (f"./screenshots/{caller_id}-{answer_id}-"
                            f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")

                with open(file_url, 'wb') as file:
                    file.write(frame)

                res_add_event = await EventDB().add_photo_async(caller_id, answer_id, cam_id, file_url, db)
                # res_add_event = EventDB().add_photo(caller_id, answer_id, cam_id, file_url)

                if res_add_event:
                    logger.info(f"Успешно создано событие в БД для: {caller_id} {answer_id} {cam_id} {file_url}")
                else:
                    logger.warning(f"Не удалось создать событие в БД для: {caller_id} {answer_id} {cam_id} {file_url}")

            status_code = 201
        else:
            status_code = 204

    except Exception as ex:
        status_code = 400
        frame = b''
        logger.exception(f"Request can't be completed correctly: {ex}")

    return Response(content=frame, status_code=status_code, media_type="image/png")
