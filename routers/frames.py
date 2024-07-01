from fastapi import APIRouter, Response
from misc.logger import Logger
from misc.glob_process import ProcessConstManager

logger = Logger()

camera_router = APIRouter(
    tags=['CameraAsync']
)


@camera_router.get('/action.do')
async def take_frame(video_in: str):
    """ video_in: 'CAM:2' where 'CAM' option, number must be after ':' """

    status_code = 200

    try:
        cam_name = str(video_in)
        cam_name = 'CAM' + cam_name[cam_name.find(':') + 1:]

        cam_manager = ProcessConstManager.get_process_manager()
        # Gain a frame
        frame = await cam_manager.get_frame(cam_name)

    except Exception as ex:
        status_code = 204
        frame = b''
        logger.exception(f"Request can't be completed correctly: {ex}")

    return Response(content=frame, status_code=status_code, media_type="image/png")
