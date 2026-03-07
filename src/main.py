# nuitka-project: --lto=no
# nuitka-project: --jobs=4
# nuitka-project: --static-libpython=no
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --follow-imports
# nuitka-project: --nofollow-import-to="*.tests"
# nuitka-project: --nofollow-import-to="*.distutils"
# nuitka-project: --nofollow-import-to="distutils"
# nuitka-project: --nofollow-import-to="unittest"
# nuitka-project: --nofollow-import-to="pydoc"
# nuitka-project: --nofollow-import-to="tkinter"
# nuitka-project: --nofollow-import-to="test"
# nuitka-project: --noinclude-dlls=*.cpp.o
# nuitka-project: --noinclude-dlls=*.qsb
# nuitka-project: --noinclude-qt-translations
# nuitka-project: --include-package=passlib.handlers.md5_crypt
# nuitka-project: --include-data-dir=resources/app=resources/app
# nuitka-project: --include-data-files=src/ui/theme.qss=ui/theme.qss
# nuitka-project: --remove-output
# nuitka-project: --company-name="Bit Capital Group"
# nuitka-project: --product-name="BitCap IPReporter"
# nuitka-project: --file-version=0.0.0.0
# nuitka-project: --product-version=0.0.0.0


import logging
import logging.handlers
import os
import sys
import traceback
from json.decoder import JSONDecodeError

from pydantic import ValidationError
from PySide6.QtCore import QSharedMemory, QSystemSemaphore, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
)

from config import IPRConfig
from ipr import IPR
from utils import (
    IPR_METADATA,
    IPR_THEME,
    MAX_ROTATE_LOG_FILES,
    flush_log,
    get_config_file_path,
    get_log_dir,
    get_log_file_path,
)

# logger
logger = logging.getLogger(__name__)

# windows taskbar
try:
    from ctypes import windll

    myappid = "bitcap.ipr.ipreporter"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


class Main:
    def __init__(self, argv: list[str] = []):
        self.args = argv
        self.app = QApplication(self.args)

        self.is_running = False

        self.config_path = get_config_file_path()
        self.config = IPRConfig()

        self.log_dir = get_log_dir()
        self.log_path = get_log_file_path()

        self.__ipr_entry()

    def __init_conf(self) -> bool:
        try:
            self.config.read()
            self.config.write()
        except (JSONDecodeError, ValidationError) as exc:
            logger.critical("init_conf : failed to read/validate configuration file.")
            logger.critical(f"init_conf : {exc}")
            error_action = QMessageBox.critical(
                None,
                "BitCapIPR - Critical error",
                f"Failed to read existing configuration file!\n{exc.__repr__()}\nPlease fix configuration file or restore to defaults and relaunch the application.",
                buttons=QMessageBox.StandardButton.Open
                | QMessageBox.StandardButton.RestoreDefaults
                | QMessageBox.StandardButton.Ok,
            )
            match error_action:
                case QMessageBox.StandardButton.Open:
                    QDesktopServices.openUrl(
                        QUrl.fromLocalFile(self.config.config_path.resolve())
                    )
                case QMessageBox.StandardButton.RestoreDefaults:
                    self.config.write_default()
            return False
        return True

    def __init_logger(self) -> None:
        os.makedirs(self.log_dir, exist_ok=True)

        max_log_size_kb = self.config.logs.max_log_size * 1000
        rfh = logging.handlers.RotatingFileHandler(
            self.log_path.as_posix(), maxBytes=max_log_size_kb, backupCount=1
        )
        match self.config.logs.on_max_log_size:
            case 0:

                def namer(name):
                    return name

                def rotator(source, dest):
                    # override rotator to flush log instead.
                    flush_log()

                rfh.rotator = rotator
                rfh.namer = namer
            case 1:
                rfh.backupCount = MAX_ROTATE_LOG_FILES

        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(name)s:%(message)s",
            datefmt="%m/%d/%Y %I:%M:%S%p",
            level=logging.INFO,
            handlers=[rfh],
        )
        logger.info("init_logger : init finished.")

        logger.manager.root.setLevel(self.config.logs.log_level)
        logger.info(f"init_logger : set logger to level {self.config.logs.log_level}.")

    def __ipr_entry(self) -> None:
        if not self.__init_conf():
            return
        self.__init_logger()
        logger.debug(f"launch_app : bitcap-ipr v{IPR_METADATA['appversion']}")
        logger.info("launch_app: start app.")

        with open(IPR_THEME) as theme:
            self.app.setStyleSheet(theme.read())

        window_key = "BitCapIPR"
        shared_mem_key = "IPRSharedMemory"
        semaphore = QSystemSemaphore(window_key, 1)
        semaphore.acquire()

        if os.name == "posix":
            # manually destroy shared memory if on unix
            unix_fix_shared_mem = QSharedMemory(shared_mem_key)
            if unix_fix_shared_mem.attach():
                unix_fix_shared_mem.detach()

        shared_mem = QSharedMemory(shared_mem_key)

        if shared_mem.attach():
            self.is_running = True
        else:
            shared_mem.create(1)
            self.is_running = False

        semaphore.release()

        if self.is_running:
            # if already running, send warning dialog and close app
            QMessageBox.warning(
                None,
                "BitCapIPR - Application already running",
                "One instance of the application is already running.",
            )
            return

        self.app.setWindowIcon(QIcon(":rc/img/BitCapIPR_BLK-02_Square.png"))
        self.app.setStyle("Fusion")

        self.main_window = IPR(stored=self.config)
        self.main_window.show()

        sys.excepthook = self.__exc_hook
        sys.exit(self.app.exec())

    def __exc_hook(self, exc_type, exc_value, exc_tb):
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logger.critical("exception_hook : exception caught!")
        logger.critical(f"exception_hook : {tb}")
        logger.info("exception_hook : store any unsaved data.")
        if (
            self.main_window.menu_bar.actionEnableIDTable.isChecked()
            and self.main_window.idTable.rowCount() > 0
        ):
            logger.info("exception_hook: export current table.")
            self.main_window.export_table()
        # graceful exit
        self.main_window.quit()
        input = QMessageBox.critical(
            None,
            "BitCap IPR - Critical Error",
            f"Application has encounter an error!\nSee output log at {self.log_path.resolve()}.",
            buttons=QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Ok,
        )
        if input == QMessageBox.StandardButton.Open:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.log_path.resolve()))
        self.app.exit(1)


if __name__ == "__main__":
    Main(sys.argv)
