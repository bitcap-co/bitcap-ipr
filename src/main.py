import os
import sys
import json
import glob
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
from util import *

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


def init_app():
    default_config = get_default_config()
    config_path = get_config_path()
    log_path = get_log_path()
    os.makedirs(config_path, exist_ok=True)
    os.makedirs(log_path, exist_ok=True)

    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s:%(message)s",
        datefmt="%m/%d/%Y %I:%M:%S%p",
        filename=f"{Path(log_path, 'ipr.log.0')}",
        level=logging.INFO,
    )

    config = get_config(default_config)
    if not os.path.exists(Path(config_path, "config.json")):
        config_json = json.dumps(config, indent=4)
        with open(Path(config_path, "config.json"), "w") as f:
            f.write(config_json)
    else:
        curr_config = get_config(Path(config_path, "config.json"))
        config.update(curr_config)
        config_json = json.dumps(config, indent=4)
        with open(Path(config_path, "config.json"), "w") as f:
            f.write(config_json)

    max_log_size = int(config["logs"]["maxLogSize"]) * 1000
    match config["logs"]["onMaxLogSize"]:
        case 0:
            curr_log_size = os.stat(Path(log_path, "ipr.log.0")).st_size
            if curr_log_size >= max_log_size:
                flush_log(Path(log_path, "ipr.log.0"))
        case 1:
            latest_log = max(glob.glob(f"{log_path}/*"), key=os.path.getmtime)
            curr_log_size = os.stat(latest_log).st_size
            if curr_log_size >= max_log_size:
                log_index = int(os.path.basename(latest_log).split(".")[-1]) + 1
                if int(log_index) == MAX_ROTATE_LOG_FILES:
                    log_index = 0
                if os.path.exists(Path(log_path, f"ipr.log.{log_index}")):
                    flush_log(Path(log_path, f"ipr.log.{log_index}"))
                logging.basicConfig(
                    format="%(asctime)s - %(levelname)s - %(name)s:%(message)s",
                    datefmt="%m/%d/%Y %I:%M:%S%p",
                    filename=f"{Path(log_path, f'ipr.log.{log_index}')}",
                    level=logging.INFO,
                    force=True
                )

    logger.manager.root.setLevel(config["logs"]["logLevel"])
    logger.info(f"init_app : set logger to log level {config['logs']['logLevel']}")


def launch_app():
    init_app()
    logger.info("launch_app : finish init.")
    logger.info("launch_app : start app.")

    app = QApplication(sys.argv)
    with open(Path(BASEDIR, "ui", "theme", "theme.qss")) as theme:
        app.setStyleSheet(theme.read())

    # Here we are making sure that only one instance is running at a time
    window_key = "BitCapIPR"
    shared_mem_key = "IPRSharedMemory"
    semaphore = QSystemSemaphore(window_key, 1)
    semaphore.acquire()

    if CURR_PLATFORM != "win32":
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

    w = MainWindow()
    w.show()
    sys.excepthook = exception_hook
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_app()
