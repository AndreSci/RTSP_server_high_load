

class ResLoader:
    @staticmethod
    def load_no_signal() -> bytes:
        """ Функция подгружает кадр с надписью NoSignal """

        image = b''

        try:
            with open('./resources/no_signal.jpg', "rb") as file:
                image = file.read()
        except Exception as ex:
            print(f"Критическая ошибка load_no_signal_pic: {ex}")
            raise

        return image
