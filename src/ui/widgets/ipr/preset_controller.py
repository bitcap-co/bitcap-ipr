# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from collections.abc import Callable
from typing import ClassVar

from pydantic import BaseModel, ConfigDict
from PySide6.QtCore import QObject, QSignalBlocker, Signal
from PySide6.QtWidgets import QCheckBox, QLineEdit

from config import IPRConfig, PoolPreset, PresetType, SocketPreset

from .preset_selector import IPRPresetSelector

RestartCallback = Callable[[], object]


class PoolPresetWidgets(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", arbitrary_types_allowed=True
    )

    selector: IPRPresetSelector
    urls: tuple[QLineEdit, QLineEdit, QLineEdit]
    users: tuple[QLineEdit, QLineEdit, QLineEdit]
    passwords: tuple[QLineEdit, QLineEdit, QLineEdit]


class SocketPresetWidgets(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", arbitrary_types_allowed=True
    )

    selector: IPRPresetSelector
    address: QLineEdit
    auto_discover: QCheckBox


class PoolPresetController(QObject):
    """Synchronizes the pool preset selector, fields, and configuration."""

    notification_requested: Signal = Signal(str, int)

    def __init__(
        self,
        parent: QObject,
        config: IPRConfig,
        widgets: PoolPresetWidgets,
    ) -> None:
        super().__init__(parent)
        self._config: IPRConfig = config
        self._widgets: PoolPresetWidgets = widgets
        self._syncing: bool = False
        selector = widgets.selector
        selector.combo.currentIndexChanged.connect(self.select)
        selector.combo.editTextChanged.connect(self.rename)
        selector.create_requested.connect(self.create)
        selector.remove_requested.connect(self.remove)
        self.reload()

    @property
    def index(self) -> int:
        return self._widgets.selector.index

    def reload(self) -> None:
        presets = self._config.pool_config.pool_presets
        index = self._config.pool_config.selected_preset
        if index < 0 or index >= len(presets):
            index = 0 if presets else -1
        self._replace_names([preset.preset_name for preset in presets], index)
        self._apply(index)

    def _replace_names(self, names: list[str], index: int) -> None:
        combo = self._widgets.selector.combo
        blocker = QSignalBlocker(combo)
        combo.clear()
        combo.addItems(names)
        combo.setCurrentIndex(index)
        del blocker

    def _set_selector(self, name: str, index: int) -> None:
        combo = self._widgets.selector.combo
        blocker = QSignalBlocker(combo)
        self._widgets.selector.create_preset(name, index)
        del blocker

    def _apply(self, index: int) -> None:
        presets = self._config.pool_config.pool_presets
        if index < 0 or index >= len(presets):
            self.clear_fields()
            return
        preset = presets[index]
        for field, value in zip(
            self._widgets.urls, (preset.pool1, preset.pool2, preset.pool3)
        ):
            field.setText(value)
        for field, value in zip(
            self._widgets.users, (preset.user1, preset.user2, preset.user3)
        ):
            field.setText(value)
        for field, value in zip(
            self._widgets.passwords,
            (preset.passwd1, preset.passwd2, preset.passwd3),
        ):
            field.setText(value)

    def select(self, index: int) -> None:
        if self._syncing:
            return
        presets = self._config.pool_config.pool_presets
        if index < 0 or index >= len(presets):
            return
        self._config.pool_config.selected_preset = index
        self._apply(index)

    def rename(self, name: str) -> None:
        if self._syncing:
            return
        index = self.index
        presets = self._config.pool_config.pool_presets
        if index < 0 or index >= len(presets):
            return
        presets[index].preset_name = name
        self._syncing = True
        try:
            self._widgets.selector.update_selected_preset_name(name)
        finally:
            self._syncing = False
        self._config.write()

    def create(self, preset: PoolPreset | None = None) -> None:
        if preset is None:
            preset = PoolPreset(preset_name="New Preset")
        presets = self._config.pool_config.pool_presets
        index = len(presets)
        presets.append(preset)
        self._config.pool_config.selected_preset = index
        self._set_selector(preset.preset_name, index)
        self._apply(index)
        self._config.write()

    def remove(self) -> None:
        index = self.index
        presets = self._config.pool_config.pool_presets
        if index < 0 or index >= len(presets):
            return
        presets.pop(index)
        combo = self._widgets.selector.combo
        blocker = QSignalBlocker(combo)
        combo.removeItem(index)
        new_index = combo.currentIndex()
        del blocker
        self._config.pool_config.selected_preset = new_index
        self._apply(new_index)
        self._config.write()

    def save(self) -> None:
        index = self.index
        presets = self._config.pool_config.pool_presets
        if index < 0 or index >= len(presets):
            name = self._widgets.selector.preset_name or "New Preset"
            preset = self._preset_from_fields(name)
            self.create(preset)
        else:
            presets[index] = self._preset_from_fields(
                self._widgets.selector.preset_name
            )
            self._config.pool_config.selected_preset = index
            self._config.write()
        self.notification_requested.emit(
            "Status :: successfully wrote pool preset.", 3000
        )

    def _preset_from_fields(self, name: str) -> PoolPreset:
        urls = [field.text() for field in self._widgets.urls]
        users = [field.text() for field in self._widgets.users]
        passwords = [field.text() for field in self._widgets.passwords]
        return PoolPreset(
            preset_name=name,
            pool1=urls[0],
            pool2=urls[1],
            pool3=urls[2],
            user1=users[0],
            user2=users[1],
            user3=users[2],
            passwd1=passwords[0],
            passwd2=passwords[1],
            passwd3=passwords[2],
        )

    def clear_fields(self) -> None:
        for field in (
            *self._widgets.urls,
            *self._widgets.users,
            *self._widgets.passwords,
        ):
            field.clear()

    def snapshot(self) -> list[dict[str, str]]:
        saved = self._config.dump_stored_presets(PresetType.POOL)
        index = self.index
        if index < 0 or index >= len(saved):
            return saved
        current = self._preset_from_fields(self._widgets.selector.preset_name)
        saved[index] = current.model_dump()
        return saved


class SocketPresetController(QObject):
    """Synchronizes the IPRD socket preset selector and configuration."""

    def __init__(
        self,
        parent: QObject,
        config: IPRConfig,
        widgets: SocketPresetWidgets,
        restart_listener: RestartCallback,
    ) -> None:
        super().__init__(parent)
        self._config: IPRConfig = config
        self._widgets: SocketPresetWidgets = widgets
        self._restart_listener: RestartCallback = restart_listener
        self._syncing: bool = False
        selector = widgets.selector
        selector.combo.currentIndexChanged.connect(self.select)
        selector.combo.editTextChanged.connect(self.rename)
        selector.create_requested.connect(self.create)
        selector.remove_requested.connect(self.remove)
        self.reload()

    @property
    def index(self) -> int:
        return self._widgets.selector.index

    def reload(self) -> None:
        presets = self._config.listener.iprd.socket_presets
        index = self._config.listener.iprd.selected_preset
        if index < 0 or index >= len(presets):
            index = 0 if presets else -1
        combo = self._widgets.selector.combo
        blocker = QSignalBlocker(combo)
        combo.clear()
        combo.addItems([preset.preset_name for preset in presets])
        combo.setCurrentIndex(index)
        del blocker
        self._apply(index)

    def _apply(self, index: int) -> None:
        presets = self._config.listener.iprd.socket_presets
        if index < 0 or index >= len(presets):
            self._widgets.address.clear()
            return
        self._widgets.address.setText(presets[index].socket_addr)

    def select(self, index: int) -> None:
        if self._syncing:
            return
        presets = self._config.listener.iprd.socket_presets
        if index < 0 or index >= len(presets):
            return
        self._config.listener.iprd.selected_preset = index
        self._apply(index)
        self._restart_listener()

    def rename(self, name: str) -> None:
        if self._syncing:
            return
        index = self.index
        presets = self._config.listener.iprd.socket_presets
        if index < 0 or index >= len(presets):
            return
        presets[index].preset_name = name
        self._syncing = True
        try:
            self._widgets.selector.update_selected_preset_name(name)
        finally:
            self._syncing = False
        self._config.write()

    def create(self, preset: SocketPreset | None = None) -> None:
        if preset is None:
            preset = SocketPreset(
                preset_name="New Preset",
                socket_addr=self._widgets.address.text(),
            )
        presets = self._config.listener.iprd.socket_presets
        index = len(presets)
        presets.append(preset)
        self._config.listener.iprd.selected_preset = index
        combo = self._widgets.selector.combo
        blocker = QSignalBlocker(combo)
        self._widgets.selector.create_preset(preset.preset_name, index)
        del blocker
        self._apply(index)
        self._config.write()

    def remove(self) -> None:
        index = self.index
        presets = self._config.listener.iprd.socket_presets
        if index < 0 or index >= len(presets):
            return
        presets.pop(index)
        combo = self._widgets.selector.combo
        blocker = QSignalBlocker(combo)
        combo.removeItem(index)
        new_index = combo.currentIndex()
        del blocker
        self._config.listener.iprd.selected_preset = new_index
        self._apply(new_index)
        self._config.write()
        if new_index >= 0:
            self._restart_listener()

    def save(self) -> None:
        index = self.index
        presets = self._config.listener.iprd.socket_presets
        if index < 0 or index >= len(presets):
            return
        preset = presets[index]
        address = self._widgets.address.text()
        name = self._widgets.selector.preset_name
        if preset.socket_addr == address and preset.preset_name == name:
            return
        preset.socket_addr = address
        preset.preset_name = name
        self._config.listener.iprd.selected_preset = index
        self._config.write()

    def snapshot(self) -> list[dict[str, str]]:
        saved = self._config.dump_stored_presets(PresetType.SOCKET)
        index = self.index
        if self._widgets.auto_discover.isChecked() or index < 0 or index >= len(saved):
            return saved
        saved[index]["preset_name"] = self._widgets.selector.preset_name
        saved[index]["socket_addr"] = self._widgets.address.text()
        return saved
