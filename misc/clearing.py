""" Ресурс предназначен для очистки директории от устаревших файлов """
import os
import datetime
import shutil
import multiprocessing


class CleanerDir:
    @classmethod
    def clear_dir(cls, dir_for_save: str, days_for_save: str = 1):
        """ Удаляет папки которым больше через указано в DAYS_FOR_SAVE (дата написана в имени папки)"""
        # Создаем процесс чтоб не блокировать поток обработки кадров, нам не нужно заботиться об его завершении.
        proc1 = multiprocessing.Process(target=cls.__work, args=(dir_for_save, days_for_save))
        proc1.start()

    @classmethod
    def __work(cls, dir_for_save: str, days_for_save):
        dir_res = os.walk(dir_for_save)
        try:
            test_days_step_1: list = None

            # Получаем список папок
            for fol in dir_res:
                test_days_step_1 = fol[1]
                break

            # Этап проверки срока жизни папок
            for day in test_days_step_1:
                try:
                    data_res = datetime.datetime.strptime(str(day), '%Y-%m-%d').date()

                    if (datetime.datetime.now().date() - data_res).days > days_for_save:
                        shutil.rmtree(f"{dir_for_save}{day}")

                except Exception as dex:
                    print(f"Не удалось обработать папку с именем: {dex}")

        except Exception as ex:
            print(f"Исключение в работе {ex}")


if __name__ == "__main__":
    CleanerDir.clear_dir("/tests/video_saves/CAM2\\")
