import asyncio
from fastapi import APIRouter, Response, Request
from misc.logger import Logger
from misc.glob_process import ProcessConstManager
from data_base.cameras import CamerasDB

logger = Logger()

camera_router = APIRouter(
    tags=['AsteriskAsync']
)


@camera_router.get('/asterisk_save')
async def take_frame(caller_id: int, answer_id: int):
    """ video_in: 'CAM:2' where 'CAM' option, number must be after ':' """

    status_code = 200
    frame = b''

    logger.event(f"Обращение на сохранения кадра: caller_id {caller_id} answer_id {answer_id}")

    try:
        cameras = CamerasDB().find_cameras(caller_id)

        if cameras.get('RESULT') == 'SUCCESS':
            logger.info(cameras, print_it=False)

            for camera in cameras.get('DATA'):
                # cam_name = str(video_in)
                # cam_name = 'CAM' + cam_name[cam_name.find(':') + 1:]
                cam_name = camera.get('FName')

                cam_manager = ProcessConstManager.get_process_manager()
                # Get frame
                frame = await cam_manager.get_frame(cam_name)

    except Exception as ex:
        status_code = 204
        frame = b''
        logger.exception(f"Request can't be completed correctly: {ex}")

    return Response(content=frame, status_code=status_code, media_type="image/png")