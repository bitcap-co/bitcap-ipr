import os
import sys
import json
import logging
import traceback
from pathlib import Path

from PyQt6.QtCore import (
    QSystemSemaphore,
    QSharedMemory,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox,
)
from PyQt6.QtGui import QIcon
from MainWindow import MainWindow
from util import curr_platform, config_path, log_path

basedir = os.path.dirname(__file__)

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
        "Application has encounter an error!\nSee output log.",
    )
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical("exception_hook : exception caught!")
    logger.critical(f"exception_hook : {tb}")
    QApplication.exit(0)


def launch_app():
    # paths
    os.makedirs(config_path, exist_ok=True)
    os.makedirs(log_path, exist_ok=True)

    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s:%(message)s",
        datefmt="%m/%d/%Y %I:%M:%S%p",
        filename=f"{Path(log_path, 'ipr.log')}",
        level=logging.INFO,
    )
    logger.info("launch_app : start init.")

    app = QApplication(sys.argv)
    with open(Path(basedir, "resources", "app", "ui", "theme.qss")) as theme:
        app.setStyleSheet(theme.read())
    # first-time launch
    logger.info("launch_app : check for existing config.")
    with open(Path(basedir, "resources", "app", "config.json.default"), "r") as f:
        default_config = json.load(f)
    if not os.path.exists(Path(config_path, "config.json")):
        # no config so write them on first-time launch
        logger.info("launch_app : first time launch; write default config.")
        default_config_json = json.dumps(default_config, indent=4)
        with open(Path(config_path, "config.json"), "w") as f:
            f.write(default_config_json)
    else:
        logger.info("launch_app : update config.")
        with open(Path(config_path, "config.json"), "r") as f:
            user_config = json.load(f)
        default_config.update(user_config)
        update_config_json = json.dumps(default_config, indent=4)
        with open(Path(config_path, "config.json"), "w") as f:
            f.write(update_config_json)

    # Here we are making sure that only one instance is running at a time
    window_key = "BitCapIPR"
    shared_mem_key = "IPRSharedMemory"
    semaphore = QSystemSemaphore(window_key, 1)
    semaphore.acquire()

    if curr_platform != "win32":
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

    logger.info("launch_app : finish app init.")
    w = MainWindow()
    w.show()
    sys.excepthook = exception_hook
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_app()
