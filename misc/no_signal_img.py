from PIL import Image, ImageSequence
import io

GLOB_IMG_NO_SIGNAL = []
IMG_URL = './resources/no-signal-stand-by.gif'


class GifToBytes:
    def __init__(self, img_url: str = IMG_URL):
        """ Предварительно у нас 110 кадров """
        self.full_gif = Image.open(img_url)

        self._rebuild_global()

    @staticmethod
    def get_img(index: int) -> bytes:
        if index > len(GLOB_IMG_NO_SIGNAL):
            raise IndexError(f"Исключение вызвало указание индекса больше чем доступно в массиве ")
        return GLOB_IMG_NO_SIGNAL[index]

    @staticmethod
    def get_size() -> int:
        return len(GLOB_IMG_NO_SIGNAL)

    def _rebuild_global(self):
        """ Заполняем глобальную переменную кадрами """
        global GLOB_IMG_NO_SIGNAL

        try:
            for image in ImageSequence.Iterator(self.full_gif):

                img_byte_arr = io.BytesIO()
                image.convert('RGB').save(img_byte_arr, format='JPEG')

                GLOB_IMG_NO_SIGNAL.append(img_byte_arr.getvalue())
        except Exception as ex:
            print(f"GifToBytes._rebuild_global: Исключение вызвало: {ex}")
