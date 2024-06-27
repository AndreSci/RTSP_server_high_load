from rtsp_connect.manager import ProcessManager


CAM_PROC: ProcessManager


class ProcessConstManager:
    """ Для доступа из любой точки программы """
    @staticmethod
    def set_process_manager(value: ProcessManager) -> bool:
        global CAM_PROC
        CAM_PROC = value
        return True

    @staticmethod
    def get_process_manager() -> ProcessManager:
        return CAM_PROC
