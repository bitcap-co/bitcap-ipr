import logging
import time
from collections import OrderedDict

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QButtonGroup

from .ipreport import IPReport
from .listener import Listener

logger = logging.getLogger(__name__)

RECORD_MIN_AGE = 10.0


class Record(OrderedDict[str, IPReport]):
    """
    Record is a OrderedDict with a set size of record entries. FIFO order.
    """

    def __init__(self, size: int) -> None:
        super().__init__()
        self._record_size = size
        self._check_record_size()

    def __setitem__(self, key: str, value: IPReport) -> None:
        super().__setitem__(key, value)
        self._check_record_size()

    def _check_record_size(self):
        while len(self) > self._record_size:
            self.popitem(last=False)

    @property
    def size(self) -> int:
        return self._record_size


class ListenerManager(QObject):
    """
    Listener Manager class

    Args:
        parent (QObject): parent object.

    Signals:
        listen_complete (IPReport): emits IPReport result from Listener.result signal.
        listen_error (str): emits error from Listener.error signal.
    """

    listen_complete = Signal(IPReport)
    listen_error = Signal(str)

    def __init__(self, parent: QObject):
        super().__init__(parent)
        self._listeners: list[Listener] = []
        self.conf: QButtonGroup
        self.record: Record = Record(size=10)

    @property
    def enabled(self) -> list[str]:
        """get all enabled listener names from config.

        Returns:
            list[str]: list of enabled listener names.
        """
        return [btn.text() for btn in self.conf.buttons() if btn.isChecked()]

    @property
    def status(self) -> str:
        """get the current status message of active listeners.

        Returns:
            str: string of active listener names.
        """
        if len(self._listeners):
            return ", ".join(
                btn.text() for btn in self.conf.buttons() if btn.isChecked()
            )
        return ""

    @property
    def count(self) -> int:
        """get the number of active listeners.

        Returns:
            int: the number of active listeners.
        """
        return len(self._listeners)

    def _is_duplicate_record(self, result: IPReport) -> bool:
        if not len(self.record):
            return False
        for ent in self.record.items():
            key, data = ent
            if key == result.src_ip:
                if data.src_mac != result.src_mac:
                    return False
                else:
                    # check record age
                    if time.time() - data.updated_at <= RECORD_MIN_AGE:
                        logger.warning(
                            f"Listener[{result.port_type.value}] : duplicate packet."
                        )
                        return True
                    else:
                        return False
        return False

    def _append_listener(self, port: int):
        listener = Listener(port=port, parent=self)
        if listener.bound:
            logger.info(
                f" start listening on {listener.addr.toString()}:{listener.port}"
            )
            self._listeners.append(listener)

    def _start_listeners(self, conf: QButtonGroup):
        enabled = [x for x in conf.buttons() if x.isChecked()]
        for listenFor in enabled:
            match conf.id(listenFor):
                case 1 | 4 | 5:  # antminer | volcminer | hammer
                    self._append_listener(14235)
                case 2:  # iceriver
                    self._append_listener(11503)
                case 3:  # whatsminer
                    self._append_listener(8888)
                case 5:  # goldshell
                    self._append_listener(1314)
                case 6:  # sealminer
                    self._append_listener(18650)
                case 7:  # elphapex
                    self._append_listener(9999)
        for listener in self._listeners:
            listener.result.connect(self.emit_listen_complete)
            listener.error.connect(self.emit_listen_error)

    def _stop_listeners(self):
        logger.info(" close listeners.")
        if len(self._listeners):
            for listener in self._listeners:
                listener.close()
        self._listeners = []

    @Slot()
    def start(self, listen_config: QButtonGroup):
        self.conf = listen_config
        self._start_listeners(listen_config)

    def stop(self):
        self._stop_listeners()
        self.record.clear()

    def emit_listen_complete(self, result: IPReport):
        logger.debug(f" result: {result}.")
        if not self._is_duplicate_record(result):
            logger.info(" listen_complete signal result.")
            result.updated_at = time.time()
            self.record[result.src_ip] = result
            self.listen_complete.emit(result)

    def emit_listen_error(self, error: str):
        logger.error(" listen_error signal result!")
        self.listen_error.emit(error)
