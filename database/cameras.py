from database.db_connection import DBConnection


class CamerasDB(DBConnection):

    def take_cameras(self) -> dict:

        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": {}, "FULL_CAMERAS": list()}

        try:
            with self.connection.cursor() as cur:
                # Получаем список камер
                cur.execute("select * from vig_sender.tcamera")

                res = cur.fetchall()

                for camera in res:

                    ret_value['DATA'][camera['FName']] = camera['FRTSP']

                    ret_value['FULL_CAMERAS'].append({"FID": camera['FID'],
                                                       "FName": camera['FName'],
                                                       "FDateCreate": str(camera['FDateCreate']),
                                                       "FRTSP": camera['FRTSP'],
                                                       "FDesc": camera['FDesc'],
                                                       "isPlateRec"
                                                       "Enable": True if camera['isPlateRecEnable'] == 1 else False})

                ret_value['RESULT'] = "SUCCESS"
        except Exception as ex:
            ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value

    def find_camera(self, caller_id: str) -> dict:

        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": {}}

        try:
            with self.connection.cursor() as cur:
                # Получаем список камер с которых нужно получить кадры
                cur.execute(f"select tcamera.FName, tcamera.FRTSP "
                            f"from vig_sender.tasteriskcaller, vig_sender.tcameragroups, vig_sender.tcamera "
                            f"where tasteriskcaller.FName = %s "
                            f"and tcameragroups.FAsteriskCallerID = tasteriskcaller.FID "
                            f"and tcamera.FID = tcameragroups.FCameraID", (str(caller_id), ))

                res = cur.fetchall()

                if len(res) > 0:
                    ret_value['DATA'] = res
                    ret_value['RESULT'] = "SUCCESS"
                else:
                    ret_value['DESC'] = (f"Не удалось найти камеру связанную с абонентом: {caller_id} / "
                                         f"Could not find the camera associated with the caller.")

        except Exception as ex:
            ret_value["DESC"] = f"Исключение вызвало: {ex}"

        return ret_value
