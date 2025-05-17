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


import os
import sys
import logging
import logging.handlers
import traceback

from PySide6.QtCore import QSystemSemaphore, QSharedMemory, QUrl
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
)
from ipr import IPR
from utils import (
    get_stylesheet,
    MAX_ROTATE_LOG_FILES,
    get_log_dir,
    get_log_file_path,
    flush_log,
    get_default_config,
    get_config_dir,
    get_config_file_path,
    read_config,
    write_config,
    deep_update,
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


class main:
    def __init__(self, args: list = []):
        self.args = args
        self.config_dir = get_config_dir()
        self.log_dir = get_log_dir()
        self.default_config = get_default_config()
        self.config_path = get_config_file_path()
        self.log_path = get_log_file_path()
        self.stylesheet = get_stylesheet()

        self.config = None

        self.init_configuration()
        self.init_logger()
        self.app = None
        self.is_running = False
        self.main_window = None
        self.launch_app(self.args)

    def init_configuration(self):
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

        config = read_config(self.default_config)
        if not os.path.exists(self.config_path):
            self.config = config
            write_config(self.config_path, config)
        else:
            curr_config = read_config(self.config_path)
            config = deep_update(config, curr_config)
            self.config = config
            write_config(self.config_path, config)

    def init_logger(self):
        max_log_size = int(self.config["logs"]["maxLogSize"]) * 1000
        match self.config["logs"]["onMaxLogSize"]:
            case 0:

                def namer(name):
                    return name

                def rotator(source, dest):
                    # override rotator to clear log instead
                    flush_log()

                rfh = logging.handlers.RotatingFileHandler(
                    self.log_path, maxBytes=max_log_size, backupCount=1
                )
                rfh.rotator = rotator
                rfh.namer = namer
            case 1:
                rfh = logging.handlers.RotatingFileHandler(
                    self.log_path,
                    maxBytes=max_log_size,
                    backupCount=MAX_ROTATE_LOG_FILES,
                )

        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(name)s:%(message)s",
            datefmt="%m/%d/%Y %I:%M:%S%p",
            level=logging.INFO,
            handlers=[rfh],
        )

        logger.info("init_logger : init finished.")

        logger.manager.root.setLevel(self.config["logs"]["logLevel"])
        logger.info(
            f"init_logger : set logger to log level {self.config['logs']['logLevel']}."
        )

    def launch_app(self, args: list = []):
        logger.info("launch_app: start app.")
        self.app = QApplication(args)
        with open(self.stylesheet) as theme:
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

        self.main_window = IPR()
        self.main_window.show()

        sys.excepthook = self.exception_hook
        sys.exit(self.app.exec())

    def exception_hook(self, exc_type, exc_value, exc_tb):
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
            QDesktopServices.openUrl(
                QUrl(
                    f"file:///{self.log_path.resolve()}", QUrl.ParsingMode.TolerantMode
                )
            )
        self.app.exit(1)


if __name__ == "__main__":
    main(sys.argv)
