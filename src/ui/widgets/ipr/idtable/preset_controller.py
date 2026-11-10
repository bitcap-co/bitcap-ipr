# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from functools import partial
from typing import ClassVar

from pydantic import BaseModel, ConfigDict
from PySide6.QtCore import QObject, QSignalBlocker
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QTableView, QToolButton

from config import IDTablePreset, IPRConfig, PresetType

from ..preset_selector import IPRPresetSelector
from .model import COL_ACTION, column_for_field, configurable_columns


class IDTablePresetWidgets(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", arbitrary_types_allowed=True
    )

    table: QTableView
    selector: IPRPresetSelector
    columns_button: QToolButton


class IDTablePresetController(QObject):
    """Synchronizes ID-table column visibility presets and their controls."""

    def __init__(
        self,
        parent: QObject,
        config: IPRConfig,
        widgets: IDTablePresetWidgets,
    ) -> None:
        super().__init__(parent)
        self._config: IPRConfig = config
        self._widgets: IDTablePresetWidgets = widgets
        self._syncing: bool = False
        self._column_actions: dict[str, QAction] = {}

        self._configure_columns_menu()
        selector = widgets.selector
        _ = selector.combo.currentIndexChanged.connect(self.select)
        _ = selector.combo.editTextChanged.connect(self.rename)
        _ = selector.create_requested.connect(self.create)
        _ = selector.remove_requested.connect(self.remove)
        self.reload()

    @property
    def index(self) -> int:
        return self._widgets.selector.index

    def _configure_columns_menu(self) -> None:
        menu = QMenu(self._widgets.columns_button)
        for _, column in configurable_columns():
            action = menu.addAction(column.header)
            action.setCheckable(True)
            _ = action.toggled.connect(partial(self.set_column_visible, column.field))
            self._column_actions[column.field] = action
        self._widgets.columns_button.setMenu(menu)
        self._widgets.columns_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )

    def reload(self) -> None:
        presets = self._config.instance.views.table_presets
        index = self._config.instance.views.selected_table_preset
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
        presets = self._config.instance.views.table_presets
        hidden: set[str] = (
            set(presets[index].hidden_columns) if 0 <= index < len(presets) else set()
        )
        for column_index, column in configurable_columns():
            self._widgets.table.setColumnHidden(column_index, column.field in hidden)
        self._widgets.table.setColumnHidden(COL_ACTION, False)
        self._sync_actions()

    def _sync_actions(self) -> None:
        for field, action in self._column_actions.items():
            column = column_for_field(field)
            blocker = QSignalBlocker(action)
            action.setChecked(
                column is not None and not self._widgets.table.isColumnHidden(column)
            )
            del blocker

    def select(self, index: int) -> None:
        if self._syncing:
            return
        presets = self._config.instance.views.table_presets
        if index < 0 or index >= len(presets):
            return
        self._config.instance.views.selected_table_preset = index
        self._apply(index)
        self._config.write()

    def rename(self, name: str) -> None:
        if self._syncing:
            return
        index = self.index
        presets = self._config.instance.views.table_presets
        if index < 0 or index >= len(presets):
            return
        if presets[index].preset_name == name:
            return
        presets[index].preset_name = name
        self._syncing = True
        try:
            self._widgets.selector.update_selected_preset_name(name)
        finally:
            self._syncing = False
        self._config.write()

    def create(self, preset: IDTablePreset | None = None) -> None:
        if preset is None:
            preset = IDTablePreset(
                preset_name="New Preset",
                hiddenColumns=self._hidden_columns(),
            )
        presets = self._config.instance.views.table_presets
        index = len(presets)
        presets.append(preset)
        self._config.instance.views.selected_table_preset = index

        combo = self._widgets.selector.combo
        blocker = QSignalBlocker(combo)
        self._widgets.selector.create_preset(preset.preset_name, index)
        del blocker
        self._apply(index)
        self._config.write()

    def remove(self) -> None:
        index = self.index
        presets = self._config.instance.views.table_presets
        if index < 0 or index >= len(presets):
            return
        presets.pop(index)

        combo = self._widgets.selector.combo
        blocker = QSignalBlocker(combo)
        combo.removeItem(index)
        new_index = combo.currentIndex()
        del blocker
        self._config.instance.views.selected_table_preset = new_index
        self._apply(new_index)
        self._config.write()

    def set_column_visible(self, field: str, visible: bool) -> None:
        if self._syncing:
            return
        column = column_for_field(field)
        if column is None or column == COL_ACTION:
            return
        self._widgets.table.setColumnHidden(column, not visible)

        index = self.index
        presets = self._config.instance.views.table_presets
        if 0 <= index < len(presets):
            hidden = presets[index].hidden_columns
            if visible:
                presets[index].hidden_columns = [
                    stored for stored in hidden if stored != field
                ]
            elif field not in hidden:
                hidden.append(field)
            self._config.write()
        self._sync_actions()

    def _hidden_columns(self) -> list[str]:
        return [
            column.field
            for index, column in configurable_columns()
            if self._widgets.table.isColumnHidden(index)
        ]

    def snapshot(self) -> list[dict[str, object]]:
        return self._config.dump_stored_presets(PresetType.TABLE_VIEW)
