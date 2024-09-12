import asyncio
from fastapi import APIRouter, Response, Request
from misc.logger import Logger
from misc.glob_process import ProcessConstManager

from starlette.responses import StreamingResponse

GLOB_CONNECT_ID = {0000: True}
GLOB_CONNECT_STATUS = {0000: StreamingResponse}

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


async def get_video_stream(cam_name: str, connect_id: int):
    """ Функция трансляции видео потока """
    cam_manager = ProcessConstManager.get_process_manager()

    while GLOB_CONNECT_ID[connect_id]:
        # Gain a frame
        ret_value = await cam_manager.get_frame_res(cam_name)

        if not ret_value['result']:
            break

        frame = ret_value['frame']

        await asyncio.sleep(0.01)

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


async def stream(cam_name: str, connect_id: int):
    global GLOB_CONNECT_ID

    GLOB_CONNECT_ID[connect_id] = True

    try:
        async for frame in get_video_stream(cam_name, connect_id):
            yield frame
    finally:
        GLOB_CONNECT_ID[connect_id] = False
        print(f"Streaming {connect_id} ended.")


@camera_router.get("/video_feed")
async def video_feed(video_in: str, request: Request):

    global GLOB_CONNECT_ID, GLOB_CONNECT_STATUS

    connect_id = request.client.port

    cam_name = str(video_in)
    cam_name = 'CAM' + cam_name[cam_name.find(':') + 1:]

    ret_value = StreamingResponse(stream(cam_name, connect_id), media_type="multipart/x-mixed-replace; boundary=frame")

    return ret_value


@camera_router.get("/test_thread_request")
async def video_feed():
    print("Тест на входе HELLO")
    await asyncio.sleep(5)

    return "HELLO"
