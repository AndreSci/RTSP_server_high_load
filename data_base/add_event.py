from misc.logger import Logger
from data_base.db_connection import DBConnection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


logger = Logger()


class EventDB(DBConnection):

    def add_photo(self, caller_id: str, answer_id: str, cam_id: str, file_name: str) -> bool:
        """ Функция создает ивент в БД с фотографией и информацией какой абонент предоставил доступ. """
        ret_value = False

        msg_event = f"Абонент {answer_id} предоставил доступ для {caller_id}."
        desc_event = f"{caller_id}/{cam_id}/{answer_id}"

        try:
            event_type_id = 20

            with self.connection.cursor() as cur:
                # Добавляем событие
                cur.execute(f"insert into vig_sender.tevent(FEventTypeID, FDateEvent, FDateRegistration, "
                            f"FOwnerName, FEventMessage, FEventDescription, FProcessed) "
                            f"values (%s, now(), now(), 'RTSP server (Asterisk)', %s, %s, 2)",
                            (event_type_id, msg_event, desc_event))
                self.connection.commit()

                cur.execute(f"select * from vig_sender.tevent where FEventTypeID = {event_type_id} "
                            f"and FProcessed = 2 order by FID desc")
                res_sql = cur.fetchone()

                event_id = res_sql.get('FID')
                # Добавляем имя файла и связываем с событием
                cur.execute(f"insert into vig_sender.teventphoto(FEventID, FFileName, FDateTime) "
                            f"values (%s, %s, now())", (event_id, file_name))
                # Обновляем статус FProcessed = 0
                cur.execute(f"update vig_sender.tevent set FProcessed = 0 where FID = %s", event_id)
                self.connection.commit()

                logger.event(f"Добавлено событие в БД: {res_sql}")
                ret_value = True
        except Exception as ex:
            logger.exception(f"Исключение вызвало: {ex}")

        return ret_value

    @staticmethod
    async def add_photo_async(caller_id: str, answer_id: str,
                              cam_id: str, file_name: str, async_db: AsyncSession) -> bool:
        """ Функция создает ивент в БД с фотографией и информацией какой абонент предоставил доступ. """
        ret_value = False

        msg_event = f"Абонент {answer_id} предоставил доступ для {caller_id}."
        desc_event = f"{caller_id}/{cam_id}/{answer_id}"

        try:
            event_type_id = 20

            insert_query = text("insert into vig_sender.tevent(FEventTypeID, FDateEvent, "
                                "FDateRegistration, FOwnerName, FEventMessage, FEventDescription, FProcessed) "
                                "values (:Event_Type_ID, now(), now(), 'RTSP server (Asterisk)', "
                                ":Event_Message, "
                                ":Event_Description, "
                                "2)")

            # Добавляем событие
            insert_result = await async_db.execute(insert_query, {"Event_Type_ID": event_type_id,
                                                                          "Event_Message": msg_event,
                                                                          "Event_Description": desc_event})
            # Получаем FID (в БД должен быть авто-инкремент)
            event_id = insert_result.lastrowid

            # Добавляем имя файла и связываем с событием
            await async_db.execute(text("insert into vig_sender.teventphoto(FEventID, FFileName, FDateTime) "
                                        "values (:event_id, :file_name, now())"),
                                   {"event_id": event_id, "file_name": file_name})
            # Обновляем статус FProcessed = 0
            await async_db.execute(text("update vig_sender.tevent set FProcessed = 0 where FID = :event_id"),
                                   {"event_id": event_id})
            await async_db.commit()

            logger.event(f"Добавлено событие в БД: {event_id}")
            ret_value = True
        except Exception as ex:
            logger.exception(f"Исключение вызвало: {ex}")

        return ret_value
