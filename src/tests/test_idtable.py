# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import Any, override
from unittest.mock import Mock, patch

from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtWidgets import QDialog

import config  # noqa: F401  # initialize Pydantic before importing PySide-backed IPR
from mod.ipr_asic.data import (
    MinerData,
    MinerFirmware,
    MinerType,
    clean_model_name,
    model_identity,
)
from ui.widgets import (
    COL_ACTION,
    COL_IP,
    COL_SERIAL,
    ExportColumnScope,
    ExportRowScope,
    IPRFilterProxyModel,
    IPRTableController,
    IPRTableModel,
    TableExportOptions,
)
from ui.widgets.ipr.idtable.csv import parse_miner_csv
from ui.widgets.ipr.idtable.model import (
    COL_SUBTYPE,
    IPR_SORT_ROLE,
    column_for_field,
)


def _miner(ip: str, mac: str, serial: str) -> MinerData:
    return MinerData(
        ip=ip,
        mac=mac,
        serial=serial,
        type=MinerType.ANTMINER,
    )


class TestModelNormalization(unittest.TestCase):
    def test_clean_model_name_normalizes_spacing_and_vendor_prefix(self) -> None:
        self.assertEqual(
            clean_model_name("  Antminer   S19j Pro  ", vendor="Antminer"),
            "S19j Pro",
        )
        self.assertEqual(
            clean_model_name("AntminerS19", vendor="Antminer"),
            "AntminerS19",
        )
        self.assertIsNone(clean_model_name("   "))

    def test_model_identity_groups_format_variants_without_losing_suffixes(
        self,
    ) -> None:
        variants = {
            model_identity(value)
            for value in (
                "S19JPRO",
                "S19j Pro",
                "S19j-Pro",
                "Ｓ１９ｊ＿Ｐｒｏ",
            )
        }

        self.assertEqual(variants, {"s19jpro"})
        self.assertNotEqual(model_identity("S19 Pro"), model_identity("S19 Pro+"))
        self.assertNotEqual(model_identity("S19 Pro+"), model_identity("S19 Pro++"))


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

    def test_uptime_displays_as_duration_and_exposes_seconds_for_sorting(self) -> None:
        model = IPRTableModel()
        model.append(MinerData(ip="10.0.0.1", uptime=90_061))
        uptime_column = column_for_field("uptime")
        assert uptime_column is not None
        index = model.index(0, uptime_column)

        self.assertEqual(model.data(index), "1d 1h 1m 1s")
        self.assertEqual(model.data(index, IPR_SORT_ROLE), 90_061)

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

    def export_subject(
        self,
        selection: QItemSelectionModel | None = None,
        hidden_columns: set[int] | None = None,
    ) -> Any:
        if selection is None:
            selection = QItemSelectionModel(self.proxy)
        if hidden_columns is None:
            hidden_columns = set()
        table = SimpleNamespace(
            selectionModel=lambda: selection,
            isColumnHidden=lambda column: column in hidden_columns,
        )
        subject: Any = SimpleNamespace(
            model=self.model,
            proxy=self.proxy,
            _table=table,
        )
        subject.export_source_rows = lambda scope: (
            IPRTableController.export_source_rows(subject, scope)
        )
        subject.export_columns = lambda scope: IPRTableController.export_columns(
            subject, scope
        )
        return subject

    def test_subtype_filter_groups_model_format_variants(self) -> None:
        self.model.clear()
        for index, subtype in enumerate(
            ("S19JPRO", "S19j Pro", "S19j-Pro", "S19 Pro+"), start=1
        ):
            miner = _miner(
                f"10.0.0.{index}",
                f"aa:bb:cc:dd:ee:{index:02x}",
                f"SERIAL-{index}",
            )
            miner.subtype = subtype
            self.model.append(miner)

        values = dict(self.model.distinct_values(COL_SUBTYPE))
        self.assertEqual(values, {"S19JPRO": 3, "S19 Pro+": 1})

        self.proxy.set_column_filter(COL_SUBTYPE, ["S19j Pro"])

        self.assertEqual(self.proxy.rowCount(), 3)
        displayed = {
            self.proxy.data(self.proxy.index(row, COL_SUBTYPE))
            for row in range(self.proxy.rowCount())
        }
        self.assertEqual(displayed, {"S19JPRO", "S19j Pro", "S19j-Pro"})

    def test_sorting_maps_proxy_rows_back_to_source_rows(self) -> None:
        self.proxy.sort(COL_IP, Qt.SortOrder.DescendingOrder)

        source_rows = [
            self.proxy.mapToSource(self.proxy.index(row, COL_IP)).row()
            for row in range(self.proxy.rowCount())
        ]

        self.assertEqual(source_rows, [2, 1, 0])

    def test_uptime_sorts_by_raw_seconds(self) -> None:
        self.model.clear()
        short = _miner("10.0.0.1", "aa:bb:cc:dd:ee:01", "SERIAL-1")
        short.uptime = 7_200
        long = _miner("10.0.0.2", "aa:bb:cc:dd:ee:02", "SERIAL-2")
        long.uptime = 36_000
        self.model.append(short)
        self.model.append(long)
        uptime_column = column_for_field("uptime")
        assert uptime_column is not None

        self.proxy.sort(uptime_column, Qt.SortOrder.AscendingOrder)

        self.assertEqual(
            [
                self.proxy.mapToSource(self.proxy.index(row, uptime_column)).row()
                for row in range(self.proxy.rowCount())
            ],
            [0, 1],
        )

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

    def test_populate_data_upserts_miner_model_by_source_row(self) -> None:
        table = Mock()
        subject: Any = SimpleNamespace(
            model=self.model,
            _table=table,
        )
        self.model.clear()

        first = MinerData(
            recv_at=1234,
            ip="10.0.0.1",
            mac="aa:bb:cc:dd:ee:01",
            type=MinerType.ANTMINER,
        )
        updated = MinerData(
            recv_at=5678,
            ip="10.0.0.10",
            mac="aa:bb:cc:dd:ee:01",
            serial="SERIAL-UPDATED",
            type=MinerType.ANTMINER,
        )
        first_row = IPRTableController.populate_data(subject, first, dedupe_key="mac")
        updated_row = IPRTableController.populate_data(
            subject, updated, dedupe_key="mac"
        )

        self.assertEqual((first_row, updated_row), (0, 0))
        self.assertEqual(self.model.rowCount(), 1)
        self.assertIs(self.model.miner_at(0), updated)
        self.assertEqual(self.model.miner_at(0).recv_at, 5678)
        self.assertEqual(self.model.miner_at(0).ip, "10.0.0.10")
        table.scrollToBottom.assert_called_once_with()

    def test_miner_target_uses_firmware_specific_client_type(self) -> None:
        miner = MinerData(
            ip="10.0.0.1",
            type=MinerType.ANTMINER,
            firmware=MinerFirmware.VNISH,
        )
        subject: Any = SimpleNamespace(miner_at=lambda _row: miner)

        target = IPRTableController.miner_target(subject, 3)

        self.assertEqual(
            target,
            ("10.0.0.1", MinerType.VNISH, MinerFirmware.VNISH),
        )

    def test_export_csv_defaults_to_all_rows_and_columns(self) -> None:
        self.model.miner_at(0).uptime = 90_061
        self.proxy.sort(COL_IP, Qt.SortOrder.DescendingOrder)
        self.proxy.set_filter_text("10.0.0.2")
        subject = self.export_subject(hidden_columns={COL_SERIAL})

        output = IPRTableController.export_csv(subject)

        self.assertIsNotNone(output)
        lines = output.splitlines() if output is not None else []
        self.assertEqual(
            lines[0],
            "RECV_AT,IP,MAC,TYPE,SUBTYPE,SERIAL,ALGORITHM,HOSTNAME,UPTIME,"
            "STRATUM_URL,USERNAME,WORKER_NAME,API_VERSION,FIRMWARE,FW_VERSION,PLATFORM",
        )
        self.assertEqual(
            [line.split(",")[1] for line in lines[1:]],
            ["10.0.0.1", "10.0.0.2", "10.0.0.3"],
        )
        uptime_column = lines[0].split(",").index("UPTIME")
        self.assertEqual(lines[1].split(",")[uptime_column], "1d 1h 1m 1s")
        if output is None:
            self.fail("Expected exported CSV")
        imported = parse_miner_csv(output)
        self.assertEqual(imported[0].uptime, 90_061)

    def test_export_csv_current_view_uses_proxy_order_and_visible_columns(self) -> None:
        self.proxy.sort(COL_IP, Qt.SortOrder.DescendingOrder)
        subject = self.export_subject(hidden_columns={COL_SERIAL})
        options = TableExportOptions(
            row_scope=ExportRowScope.CURRENT_VIEW,
            column_scope=ExportColumnScope.VISIBLE,
        )

        output = IPRTableController.export_csv(subject, options)

        self.assertIsNotNone(output)
        lines = output.splitlines() if output is not None else []
        self.assertNotIn("SERIAL", lines[0].split(","))
        self.assertEqual(
            [line.split(",")[1] for line in lines[1:]],
            ["10.0.0.3", "10.0.0.2", "10.0.0.1"],
        )

    def test_export_csv_current_view_respects_active_filter(self) -> None:
        self.proxy.set_filter_text("10.0.0.2")
        subject = self.export_subject()
        options = TableExportOptions(row_scope=ExportRowScope.CURRENT_VIEW)

        output = IPRTableController.export_csv(subject, options)

        self.assertIsNotNone(output)
        lines = output.splitlines() if output is not None else []
        self.assertEqual(
            [line.split(",")[1] for line in lines[1:]],
            ["10.0.0.2"],
        )

    def test_export_csv_selected_rows_are_deduplicated_in_view_order(self) -> None:
        self.proxy.sort(COL_IP, Qt.SortOrder.DescendingOrder)
        selection = QItemSelectionModel(self.proxy)
        for index in (
            self.proxy.index(0, COL_IP),
            self.proxy.index(0, COL_SERIAL),
            self.proxy.index(2, COL_IP),
        ):
            selection.select(index, QItemSelectionModel.SelectionFlag.Select)
        subject = self.export_subject(selection)
        options = TableExportOptions(row_scope=ExportRowScope.SELECTED)

        output = IPRTableController.export_csv(subject, options)

        self.assertIsNotNone(output)
        lines = output.splitlines() if output is not None else []
        self.assertEqual(
            [line.split(",")[1] for line in lines[1:]],
            ["10.0.0.3", "10.0.0.1"],
        )

    def test_import_table_parses_before_replacing_model(self) -> None:
        subject: Any = SimpleNamespace(
            _window=Mock(),
            clear=Mock(),
            append_miner=Mock(),
            notification_requested=Mock(),
        )
        with TemporaryDirectory() as directory:
            file_path = Path(directory, "miners.csv")
            file_path.write_text(
                'IP,HOSTNAME,TYPE\n10.0.0.1,"rack, west",antminer\n',
                encoding="utf-8",
            )
            with patch(
                "ui.widgets.ipr.idtable.controller.QFileDialog.getOpenFileName",
                return_value=(str(file_path), ".CSV Files (*.csv)"),
            ):
                IPRTableController.import_table(subject)

        subject.clear.assert_called_once_with()
        imported = subject.append_miner.call_args.args[0]
        self.assertEqual(imported.ip, "10.0.0.1")
        self.assertEqual(imported.hostname, "rack, west")

    def test_import_table_preserves_model_when_csv_is_invalid(self) -> None:
        subject: Any = SimpleNamespace(
            _window=Mock(),
            clear=Mock(),
            append_miner=Mock(),
            notification_requested=Mock(),
        )
        with TemporaryDirectory() as directory:
            file_path = Path(directory, "invalid.csv")
            file_path.write_text("NAME,VALUE\nexample,1\n", encoding="utf-8")
            with patch(
                "ui.widgets.ipr.idtable.controller.QFileDialog.getOpenFileName",
                return_value=(str(file_path), ".CSV Files (*.csv)"),
            ):
                IPRTableController.import_table(subject)

        subject.clear.assert_not_called()
        subject.append_miner.assert_not_called()
        subject.notification_requested.emit.assert_called_once_with(
            "Status :: Failed to import table.", 5000
        )

    @patch("ui.widgets.ipr.idtable.controller.IDTableExportDialog")
    def test_export_table_uses_accepted_dialog_options(self, dialog_type: Mock) -> None:
        options = TableExportOptions(
            row_scope=ExportRowScope.CURRENT_VIEW,
            column_scope=ExportColumnScope.VISIBLE,
        )
        dialog = dialog_type.return_value
        dialog.exec.return_value = QDialog.DialogCode.Accepted
        dialog.options = options
        subject = self.export_subject()
        subject._window = Mock()
        subject.has_rows = Mock(return_value=True)
        subject.export_with_options = Mock()

        IPRTableController.export_table(subject)

        subject.export_with_options.assert_called_once_with(options)

    def test_write_export_writes_serialized_output(self) -> None:
        notification = Mock()
        subject: Any = SimpleNamespace(
            export_csv=Mock(return_value="IP,HOSTNAME\n10.0.0.1,rack-west\n"),
            notification_requested=notification,
        )
        with TemporaryDirectory() as directory:
            home = Path(directory)
            with patch(
                "ui.widgets.ipr.idtable.controller.Path.home", return_value=home
            ):
                IPRTableController._write_export(
                    subject, "IP,HOSTNAME\n10.0.0.1,rack-west\n"
                )
            output_dir = home / "Documents" / "ipr"
            output_files = list(output_dir.glob("id_table-*.csv"))
            self.assertEqual(len(output_files), 1)
            self.assertEqual(
                output_files[0].read_text(encoding="utf-8"),
                "IP,HOSTNAME\n10.0.0.1,rack-west\n",
            )

        notification.emit.assert_called_once_with(
            f"Status :: Wrote table as .CSV to {output_dir.resolve()}.", 3000
        )

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

    def test_single_miner_action_emits_source_row(self) -> None:
        signal = Mock()
        subject: Any = SimpleNamespace(miner_action_requested=signal)

        IPRTableController._request_miner_action(subject, COL_ACTION, 4)

        signal.emit.assert_called_once_with(4)

    def test_bulk_action_emits_action_and_source_rows(self) -> None:
        signal = Mock()
        subject: Any = SimpleNamespace(
            action_target_rows=Mock(return_value=[2, 0]),
            bulk_miner_action_requested=signal,
            notification_requested=Mock(),
        )

        IPRTableController.request_bulk_action(subject, "refresh")

        subject.action_target_rows.assert_called_once_with("Refresh")
        signal.emit.assert_called_once_with("refresh", [2, 0])

    def test_bulk_action_reports_empty_target_set(self) -> None:
        notification = Mock()
        subject: Any = SimpleNamespace(
            action_target_rows=Mock(return_value=[]),
            bulk_miner_action_requested=Mock(),
            notification_requested=notification,
        )

        IPRTableController.request_bulk_action(subject, "locate")

        subject.bulk_miner_action_requested.emit.assert_not_called()
        notification.emit.assert_called_once_with(
            "Status :: Failed action: no miners to locate.", 5000
        )

    def test_pool_actions_emit_selected_source_rows(self) -> None:
        retrieval = Mock()
        update = Mock()
        subject: Any = SimpleNamespace(
            selected_source_rows=Mock(return_value=[5, 3]),
            selected_source_rows_for_action=Mock(return_value=[5, 3]),
            pool_retrieval_requested=retrieval,
            pool_update_requested=update,
            notification_requested=Mock(),
        )

        IPRTableController.request_pool_retrieval(subject)
        IPRTableController.request_pool_update(subject)

        retrieval.emit.assert_called_once_with(5)
        update.emit.assert_called_once_with([5, 3])

    def test_configurator_visibility_is_routed_and_synchronized(self) -> None:
        visibility = Mock()
        IPRTableController.request_configurator_visibility(
            SimpleNamespace(configurator_visibility_requested=visibility), True
        )
        visibility.emit.assert_called_once_with(True)

        show_hide = Mock()
        show_hide.blockSignals.side_effect = [False, None]
        get_pool = Mock()
        set_pools = Mock()
        subject: Any = SimpleNamespace(
            _context_menu=SimpleNamespace(
                contextActionConfiguratorShowHide=show_hide,
                contextActionConfigutorGetPool=get_pool,
                contextActionConfiguratorSetPools=set_pools,
            )
        )

        IPRTableController.set_configurator_visible(subject, True)

        self.assertEqual(show_hide.blockSignals.call_args_list[0].args, (True,))
        show_hide.setChecked.assert_called_once_with(True)
        get_pool.setEnabled.assert_called_once_with(True)
        set_pools.setEnabled.assert_called_once_with(True)

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
