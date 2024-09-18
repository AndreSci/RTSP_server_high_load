import os
import configparser
from misc.logger import Logger
import pprint

logger = Logger()


def create_default_settings(file_path):
    config = configparser.ConfigParser()

    # Пример значений по умолчанию, можно оставить пустым
    config['GENERAL'] = {
        'host': '0.0.0.0',
        'port': '8093',
        'log_path': '.\\logs\\',
        'cameras_from_ini': True,
        'fps': 20,
        'save_video': False
    }
    config['BASE'] = {
        'host': '0.0.0.0',
        'user': 'admin',
        'password': 'admin',
        'charset': 'cp1251',
        'dbname': 'vig_sender'
    }
    config['PHOTO'] = {
        'photo_path': '.\\PHOTOS\\RTSP server (Asterisk)\\'
    }
    config['CAMERAS'] = {
        'cam2': 'rtsp://admin:admin@192.168.48.188',
        'cam3': 'rtsp://admin:admin@192.168.48.189'
    }
    config['CAM_FOR_SAVE'] = {
        'cam2': False,
        'cam3': False
    }

    with open(file_path, 'w') as configfile:
        config.write(configfile)


def like_database_dict(FName: str, FRTSP: str, isPlateRecEnable: int):
    """ Функция организует данные загруженные из settings.ini раздел CAMERAS """
    return {"FID": None,
               "FName": FName,
               "FDateCreate": None,
               "FRTSP": FRTSP,
               "FDesc": None,
               "isPlateRecEnable": True if isPlateRecEnable == 1 else False
            }


class SettingsIni:

    def __init__(self):
        # general settings
        self.settings_data = dict()
        self.settings_file = configparser.ConfigParser()

    def load_data_from_file(self, file_path: str = "settings.ini") -> dict:
        """ Функция получения настройки из файла settings.ini. """
        error_mess = 'Успешная загрузка данных из settings.ini'
        ret_value = dict()
        ret_value["result"] = False

        if not os.path.isfile(file_path):
            create_default_settings(file_path)

        # проверяем файл settings.ini
        if os.path.isfile(file_path):
            try:
                self.settings_file.read(file_path, encoding="utf-8")
                # general settings ----------------------------------------
                self.settings_data["host"] = self.settings_file["GENERAL"]["HOST"]
                self.settings_data["port"] = self.settings_file["GENERAL"]["port"]
                self.settings_data["fps"] = int(self.settings_file["GENERAL"].get("fps"))
                self.settings_data['cam_for_save'] = dict()
                self.settings_data['photo_path'] = self.settings_file['PHOTO']. get("photo_path")

                self.settings_data['cameras_from_ini'] = self.settings_file.getboolean("GENERAL",
                                                                                        "cameras_from_ini")
                self.settings_data['save_video'] = self.settings_file.getboolean("GENERAL",
                                                                                        "save_video")
                if self.settings_data['cameras_from_ini']:
                    # Подгружаем данные о камерах которые будем обслуживать
                    temp_cam_dict = dict(self.settings_file["CAM_FOR_SAVE"])
                    for cam_name in temp_cam_dict:
                        # по соглашению сторон имена камер всегда в верхнем регистре
                        if temp_cam_dict[cam_name] == 'False':
                            self.settings_data['cam_for_save'][str(cam_name).upper()] = False
                        elif temp_cam_dict[cam_name] == 'True':
                            self.settings_data['cam_for_save'][str(cam_name).upper()] = True
                        else:
                            logger.warning(f"Ошибка TypeError: {temp_cam_dict[cam_name]} != False/True")
                    data_for_pars = dict(self.settings_file["CAMERAS"])

                    self.settings_data['cameras'] = dict()
                    self.settings_data['full_cameras'] = list()

                    for name in data_for_pars:
                        name = str(name)
                        if len(data_for_pars.get(name)) > 5:
                            self.settings_data['cameras'][name.upper()] = data_for_pars.get(name)

                    # Логика для ответа
                    pair_for_cams = dict()

                    for name in data_for_pars:
                        list_name = ''.join(name).split('_')
                        # После выгрузки из файла .ini названия переменных переводятся в нижний регистр
                        # Избегая проблем переводим в верхний
                        name_new = list_name[0].upper()

                        if name_new in pair_for_cams:
                            value = data_for_pars.get(name)

                            if len(list_name) > 1 and list_name[1].upper() == 'REC':
                                pair_for_cams[name_new]["isPlateRecEnable"] = int(value)
                            else:
                                pair_for_cams[name_new]["FRTSP"] = value
                        else:
                            value = data_for_pars.get(name)
                            if len(list_name) > 1 and list_name[1].upper() == 'REC':
                                pair_for_cams[name_new] = {"isPlateRecEnable": int(value)}
                            else:
                                pair_for_cams[name_new] = {"FRTSP": value}

                            pair_for_cams[name_new]['FName'] = name_new

                        if 'isPlateRecEnable' not in pair_for_cams[name_new]:
                            pair_for_cams[name_new]['isPlateRecEnable'] = 0

                    for name in pair_for_cams:
                        self.settings_data['full_cameras'].append(
                                                            like_database_dict(
                                                                pair_for_cams[name]['FName'],
                                                                pair_for_cams[name]['FRTSP'],
                                                                pair_for_cams[name]['isPlateRecEnable']))

                # self.settings_data['CAMERAS'] = dict(self.settings_file["CAMERAS"])

                self.settings_data["log_path"] = self.settings_file["GENERAL"].get("log_path")

                pprint.pprint(self.settings_data)

                ret_value["result"] = True
            except KeyError as ex:
                error_mess = f"Не удалось найти поле в файле settings.ini: {ex}"
                logger.exception(error_mess)
                print(error_mess)
            except Exception as ex:
                error_mess = f"Не удалось прочитать файл: {ex}"
                print(error_mess)
        else:
            error_mess = "Файл settings.ini не найден в корне проекта"

        ret_value["desc"] = error_mess

        return ret_value

    def take_settings_data(self):
        return self.settings_data

    def take_log_path(self):
        return self.settings_data.get("log_path")

    def save_video(self):
        return self.settings_data.get('need_save_video')


if __name__ == "__main__":
    ini = SettingsIni()
    print(ini.load_data_from_file(file_path="../settings.ini"))
