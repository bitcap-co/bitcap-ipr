# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import unittest
from types import SimpleNamespace
from typing import Any, override
from unittest.mock import Mock, patch

from PySide6.QtCore import QItemSelectionModel, Qt

import config  # noqa: F401  # initialize Pydantic before importing PySide-backed IPR
from mod.ipr_asic.data import MinerData, MinerType
from ui.widgets import (
    COL_ACTION,
    COL_IP,
    COL_SERIAL,
    IPRFilterProxyModel,
    IPRTableController,
    IPRTableModel,
)


def _miner(ip: str, mac: str, serial: str) -> MinerData:
    return MinerData(
        ip=ip,
        mac=mac,
        serial=serial,
        type=MinerType.ANTMINER,
    )


class TestIPRTableModel(unittest.TestCase):
    def test_named_column_constants_match_model_headers(self) -> None:
        model = IPRTableModel()

        self.assertEqual(
            model.headerData(COL_IP, Qt.Orientation.Horizontal),
            "IP",
        )
        self.assertEqual(
            model.headerData(COL_SERIAL, Qt.Orientation.Horizontal),
            "SERIAL",
        )

    def test_append_update_and_upsert(self) -> None:
        model = IPRTableModel()
        first = _miner("10.0.0.1", "aa:bb:cc:dd:ee:01", "SERIAL-1")
        second = _miner("10.0.0.2", "aa:bb:cc:dd:ee:02", "SERIAL-2")

        self.assertEqual(model.append(first), 0)
        self.assertEqual(model.append(second), 1)

        updated = _miner("10.0.0.10", first.mac or "", "SERIAL-1-UPDATED")
        self.assertEqual(model.upsert(updated, key="mac"), 0)
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.miner_at(0).ip, "10.0.0.10")
        self.assertEqual(model.miner_at(0).serial, "SERIAL-1-UPDATED")

        replacement = _miner("10.0.0.20", second.mac or "", "SERIAL-2-UPDATED")
        model.update_row(1, replacement)
        self.assertIs(model.miner_at(1), replacement)


class TestIPRTableProxy(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.model = IPRTableModel()
        self.proxy = IPRFilterProxyModel()

    @override
    def setUp(self) -> None:
        self.model = IPRTableModel()
        self.model.append(_miner("10.0.0.1", "aa:bb:cc:dd:ee:01", "SERIAL-1"))
        self.model.append(_miner("10.0.0.2", "aa:bb:cc:dd:ee:02", "SERIAL-2"))
        self.model.append(_miner("10.0.0.3", "aa:bb:cc:dd:ee:03", "SERIAL-3"))
        self.proxy = IPRFilterProxyModel()
        self.proxy.setSourceModel(self.model)

    def test_sorting_maps_proxy_rows_back_to_source_rows(self) -> None:
        self.proxy.sort(COL_IP, Qt.SortOrder.DescendingOrder)

        source_rows = [
            self.proxy.mapToSource(self.proxy.index(row, COL_IP)).row()
            for row in range(self.proxy.rowCount())
        ]

        self.assertEqual(source_rows, [2, 1, 0])

    def test_text_and_column_filters_can_be_reset(self) -> None:
        self.proxy.set_filter_text("SERIAL-2")
        self.assertEqual(self.proxy.rowCount(), 1)

        self.proxy.set_filter_text("")
        self.proxy.set_column_filter(COL_IP, ["10.0.0.3"])
        self.assertEqual(self.proxy.rowCount(), 1)
        self.assertEqual(self.proxy.active_filter_columns(), {COL_IP})

        self.proxy.clear_column_filters()
        self.assertEqual(self.proxy.rowCount(), 3)
        self.assertEqual(self.proxy.active_filter_columns(), set())

    def test_reset_view_clears_controls_and_column_filters(self) -> None:
        self.proxy.set_column_filter(COL_IP, ["10.0.0.3"])
        line_filter = Mock()
        header = Mock()
        reset_sort = Mock()
        subject: Any = SimpleNamespace(
            _text_filter=line_filter,
            proxy=self.proxy,
            header=header,
            reset_sort=reset_sort,
        )

        IPRTableController.reset_view(subject)

        line_filter.clear.assert_called_once_with()
        self.assertEqual(self.proxy.active_filter_columns(), set())
        header.set_active_columns.assert_called_once_with(set())
        reset_sort.assert_called_once_with()

    def test_selected_source_rows_map_from_sorted_proxy(self) -> None:
        self.proxy.sort(COL_IP, Qt.SortOrder.DescendingOrder)
        selection = QItemSelectionModel(self.proxy)
        selection.select(
            self.proxy.index(0, COL_IP),
            QItemSelectionModel.SelectionFlag.Select,
        )
        subject: Any = SimpleNamespace(
            proxy=self.proxy,
            _table=SimpleNamespace(selectionModel=lambda: selection),
        )

        rows = IPRTableController.selected_source_rows(subject, COL_IP)

        self.assertEqual(rows, [2])

    def test_selected_source_rows_for_action_notifies_and_maps_rows(self) -> None:
        self.proxy.sort(COL_IP, Qt.SortOrder.DescendingOrder)
        selection = QItemSelectionModel(self.proxy)
        selection.select(
            self.proxy.index(1, COL_IP),
            QItemSelectionModel.SelectionFlag.Select,
        )
        notification = Mock()
        subject: Any = SimpleNamespace(
            proxy=self.proxy,
            _table=SimpleNamespace(selectionModel=lambda: selection),
            notification_requested=notification,
        )

        rows = IPRTableController.selected_source_rows_for_action(
            subject, "update_miner_pools", COL_IP
        )

        self.assertEqual(rows, [1])
        notification.emit.assert_called_once_with(
            "Status :: Running action: update_miner_pools for [10.0.0.2...]...",
            3000,
        )

    def test_action_targets_use_selection_or_all_visible_rows(self) -> None:
        self.proxy.sort(COL_IP, Qt.SortOrder.DescendingOrder)
        selection = QItemSelectionModel(self.proxy)
        table = SimpleNamespace(selectionModel=lambda: selection)
        subject: Any = SimpleNamespace(
            proxy=self.proxy,
            _table=table,
            notification_requested=Mock(),
        )
        subject.selected_source_rows = lambda column=None: (
            IPRTableController.selected_source_rows(subject, column)
        )

        self.assertEqual(
            IPRTableController.action_target_rows(subject, "Refresh"),
            [2, 1, 0],
        )

        selection.select(
            self.proxy.index(1, COL_IP),
            QItemSelectionModel.SelectionFlag.Select,
        )
        self.assertEqual(IPRTableController.action_target_rows(subject, "Refresh"), [1])

        selection.clearSelection()
        self.proxy.set_filter_text("10.0.0.2")
        self.assertEqual(IPRTableController.action_target_rows(subject, "Refresh"), [1])

    @patch("ui.widgets.ipr.idtable.controller.QApplication")
    def test_copy_selected_preserves_display_row_and_column_order(
        self, application: Mock
    ) -> None:
        selection = QItemSelectionModel(self.proxy)
        for index in (
            self.proxy.index(1, COL_SERIAL),
            self.proxy.index(0, COL_IP),
            self.proxy.index(0, COL_SERIAL),
            self.proxy.index(0, COL_ACTION),
        ):
            selection.select(index, QItemSelectionModel.SelectionFlag.Select)

        clipboard = application.clipboard.return_value
        subject: Any = SimpleNamespace(
            proxy=self.proxy,
            model=self.model,
            _table=SimpleNamespace(selectionModel=lambda: selection),
            _dashboard_url=Mock(side_effect=lambda host, _type: f"http://{host}"),
            notification_requested=Mock(),
        )

        IPRTableController.copy_selected(subject)

        clipboard.setText.assert_called_once_with(
            "http://10.0.0.1,SERIAL-1,\nSERIAL-2",
            mode=clipboard.Mode.Clipboard,
        )
        subject.notification_requested.emit.assert_called_once_with(
            "Status :: Copied elements to clipboard.", 3000
        )


if __name__ == "__main__":
    unittest.main()
