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
import json
import logging
import logging.handlers
import traceback
from pathlib import Path

from PySide6.QtCore import QSystemSemaphore, QSharedMemory
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
)
from ipr import IPR
from utils import (
    MAX_ROTATE_LOG_FILES,
    get_stylesheet,
    get_default_config,
    get_config_path,
    get_log_path,
    get_config,
    deep_update,
    flush_log,
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


def exception_hook(exc_type, exc_value, exc_tb):
    QMessageBox.critical(
        None,
        "BitCap IPR - Critical Error",
        f"Application has encounter an error!\nSee output log at {Path(get_log_path(), 'ipr.log')}.",
    )
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical("exception_hook : exception caught!")
    logger.critical(f"exception_hook : {tb}")
    QApplication.exit(0)


def init_app():
    default_config = get_default_config()
    config_path = get_config_path()
    log_path = get_log_path()
    os.makedirs(config_path, exist_ok=True)
    os.makedirs(log_path, exist_ok=True)

    config = get_config(default_config)
    if not os.path.exists(Path(config_path, "config.json")):
        config_json = json.dumps(config, indent=4)
        with open(Path(config_path, "config.json"), "w") as f:
            f.write(config_json)
    else:
        curr_config = get_config(Path(config_path, "config.json"))
        config = deep_update(config, curr_config)
        config_json = json.dumps(config, indent=4)
        with open(Path(config_path, "config.json"), "w") as f:
            f.write(config_json)

    # init logger
    max_log_size = int(config["logs"]["maxLogSize"]) * 1000
    match config["logs"]["onMaxLogSize"]:
        case 0:

            def namer(name):
                return name

            def rotator(source, dest):
                # override rotator to clear log instead
                flush_log(Path(log_path, "ipr.log"))

            rfh = logging.handlers.RotatingFileHandler(
                Path(log_path, "ipr.log"), maxBytes=max_log_size, backupCount=1
            )
            rfh.rotator = rotator
            rfh.namer = namer
        case 1:
            rfh = logging.handlers.RotatingFileHandler(
                Path(log_path, "ipr.log"),
                maxBytes=max_log_size,
                backupCount=MAX_ROTATE_LOG_FILES,
            )

    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s:%(message)s",
        datefmt="%m/%d/%Y %I:%M:%S%p",
        level=logging.INFO,
        handlers=[rfh],
    )

    logger.manager.root.setLevel(config["logs"]["logLevel"])
    logger.info(f"init_app : set logger to log level {config['logs']['logLevel']}.")


def launch_app():
    init_app()
    logger.info("launch_app : finish init.")
    logger.info("launch_app : start app.")

    app = QApplication(sys.argv)
    with open(get_stylesheet()) as theme:
        app.setStyleSheet(theme.read())

    # Here we are making sure that only one instance is running at a time
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
        is_running = True
    else:
        shared_mem.create(1)
        is_running = False

    semaphore.release()

    if is_running:
        # if already running, send warning dialog and close app
        QMessageBox.warning(
            None,
            "BitCapIPR - Application already running",
            "One instance of the application is already running.",
        )
        return

    app.setWindowIcon(QIcon(":rc/img/BitCapIPR_BLK-02_Square.png"))
    app.setStyle("Fusion")

    w = IPR()
    w.show()
    sys.excepthook = exception_hook
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_app()
