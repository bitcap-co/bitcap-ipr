# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Dialog for selecting stored miner logs to download."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..titlebar import IPRTitlebar


class MinerLogDownloadDialog(QDialog):
    download_requested: Signal = Signal(list)  # list[str]

    def __init__(
        self,
        ip_addr: str,
        logs: list[str],
        parent: QWidget,
        *,
        allow_multiple: bool = True,
    ) -> None:
        super().__init__(parent, Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setModal(True)
        self.setWindowTitle("Download Miner Logs")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_bar = IPRTitlebar(self, "Download Miner Logs", ["close"])
        title_bar.setFixedHeight(30)
        title_bar.close_button.clicked.connect(self.reject)
        layout.addWidget(title_bar)

        body = QWidget(self)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(15, 15, 15, 15)
        body_layout.setSpacing(8)
        body_layout.addWidget(QLabel(f"Select logs to download from {ip_addr}:"))

        self._list = QListWidget(body)
        self._list.setMinimumSize(420, 220)
        selection_mode = (
            QAbstractItemView.SelectionMode.ExtendedSelection
            if allow_multiple
            else QAbstractItemView.SelectionMode.SingleSelection
        )
        self._list.setSelectionMode(selection_mode)
        self._list.addItems(logs)
        if self._list.count():
            self._list.setCurrentRow(0)
        self._list.itemSelectionChanged.connect(self._update_download_button)
        body_layout.addWidget(self._list)

        buttons = QHBoxLayout()
        if allow_multiple:
            select_all = QPushButton("Select All", body)
            select_all.clicked.connect(self._list.selectAll)
            buttons.addWidget(select_all)
        buttons.addStretch(1)

        cancel = QPushButton("Cancel", body)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)

        self._download = QPushButton("Download Selected", body)
        self._download.setDefault(True)
        self._download.clicked.connect(self._request_download)
        buttons.addWidget(self._download)
        body_layout.addLayout(buttons)
        layout.addWidget(body)

        self._update_download_button()

    def _update_download_button(self) -> None:
        self._download.setEnabled(bool(self._list.selectedItems()))

    def _request_download(self) -> None:
        selected = [item.text() for item in self._list.selectedItems()]
        if not selected:
            return
        self.download_requested.emit(selected)
        self.accept()
