# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Tests for the main-window miner control action bridge."""

import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock

import config  # noqa: F401  # initialize Pydantic before importing PySide-backed IPR
from ipr import IPR
from mod.ipr_asic import MinerResult
from mod.ipr_asic.data import MinerFirmware, MinerType
from mod.ipr_asic.errors import APIError


class _ControlFacade:
    def __init__(self, result: MinerResult | None = None) -> None:
        self.result = result or MinerResult(data={"success": True})
        self.calls: list[tuple[str, MinerType, str, str | None]] = []

    async def start_miner(self, miner_type, ip, alt_pwd=None):
        self.calls.append(("start", miner_type, ip, alt_pwd))
        return self.result

    async def reboot_miner(self, miner_type, ip, alt_pwd=None):
        self.calls.append(("reboot", miner_type, ip, alt_pwd))
        return self.result


class TestMinerControlBridge(unittest.IsolatedAsyncioTestCase):
    async def test_single_control_forwards_target_and_auth(self):
        facade = _ControlFacade()
        subject: Any = SimpleNamespace(
            asic=facade,
            retrieve_miner_from_table=Mock(
                return_value=(
                    "10.0.0.1",
                    MinerType.ANTMINER,
                    MinerFirmware.STOCK,
                )
            ),
            get_client_auth=Mock(return_value="secret"),
            notify=Mock(),
        )

        await IPR._control_miner(subject, 4, "start")

        subject.retrieve_miner_from_table.assert_called_once_with(4)
        subject.get_client_auth.assert_called_once_with(MinerType.ANTMINER.value)
        self.assertEqual(
            facade.calls,
            [("start", MinerType.ANTMINER, "10.0.0.1", "secret")],
        )
        subject.notify.assert_called_once_with(
            "Status :: Successfully completed start for 10.0.0.1.",
            3000,
        )

    async def test_single_control_reports_facade_error(self):
        error = APIError("command failed")
        facade = _ControlFacade(MinerResult(error=error))
        subject: Any = SimpleNamespace(
            asic=facade,
            retrieve_miner_from_table=Mock(
                return_value=(
                    "10.0.0.2",
                    MinerType.ANTMINER,
                    MinerFirmware.STOCK,
                )
            ),
            get_client_auth=Mock(return_value=None),
            notify=Mock(),
        )

        await IPR._control_miner(subject, 1, "start")

        subject.notify.assert_called_once_with(
            "Status :: Failed to start 10.0.0.2: command failed",
            5000,
        )

    async def test_bulk_control_uses_shared_bulk_engine(self):
        facade = _ControlFacade()
        run_bulk_action = AsyncMock()
        subject: Any = SimpleNamespace(
            asic=facade,
            get_action_target_rows=Mock(return_value=[2, 5]),
            _run_bulk_action=run_bulk_action,
            notify=Mock(),
        )

        await IPR._bulk_control_miners(subject, "reboot")

        subject.get_action_target_rows.assert_called_once_with("Reboot")
        run_bulk_action.assert_awaited_once()
        await_args = run_bulk_action.await_args
        if await_args is None:
            self.fail("bulk action was not awaited")
        action, rows, make_coro = await_args.args
        self.assertEqual(action, "Reboot")
        self.assertEqual(rows, [2, 5])

        result = await make_coro(
            2,
            "10.0.0.3",
            MinerType.ANTMINER,
            MinerFirmware.STOCK,
            "secret",
        )
        self.assertTrue(result.ok)
        self.assertEqual(
            facade.calls,
            [("reboot", MinerType.ANTMINER, "10.0.0.3", "secret")],
        )

    async def test_bulk_refresh_redetects_type_and_auth_before_fetch(self):
        result = MinerResult(data={"type": "antminer", "mac": "N/A"})
        asic = SimpleNamespace(
            _parse_http_type=AsyncMock(return_value=MinerType.ANTMINER),
            get_miner_data=AsyncMock(return_value=result),
        )
        run_bulk_action = AsyncMock()
        subject: Any = SimpleNamespace(
            asic=asic,
            get_action_target_rows=Mock(return_value=[3]),
            get_client_auth=Mock(return_value="antminer-secret"),
            _run_bulk_action=run_bulk_action,
            notify=Mock(),
        )

        await IPR.bulk_refresh_miners(subject)

        run_bulk_action.assert_awaited_once()
        await_args = run_bulk_action.await_args
        if await_args is None:
            self.fail("bulk refresh was not awaited")
        action, rows, make_coro = await_args.args
        self.assertEqual(action, "Refresh")
        self.assertEqual(rows, [3])

        refresh_result = await make_coro(
            3,
            "10.0.0.4",
            MinerType.VNISH,
            MinerFirmware.VNISH,
            "vnish-secret",
        )

        self.assertIs(refresh_result, result)
        asic._parse_http_type.assert_awaited_once_with("10.0.0.4")
        subject.get_client_auth.assert_called_once_with(MinerType.ANTMINER.value)
        asic.get_miner_data.assert_awaited_once_with(
            MinerType.ANTMINER,
            "10.0.0.4",
            alt_pwd="antminer-secret",
        )

    async def test_update_pools_uses_shared_bulk_engine(self):
        result = MinerResult(data={"success": True})
        asic = SimpleNamespace(update_miner_pools=AsyncMock(return_value=result))
        selected_index = Mock()
        source_index = Mock()
        source_index.row.return_value = 7
        run_bulk_action = AsyncMock()

        def field(value):
            widget = Mock()
            widget.text.return_value = value
            return widget

        subject: Any = SimpleNamespace(
            asic=asic,
            get_selected_indexes_for_action=Mock(return_value=[selected_index]),
            id_proxy=Mock(),
            id_model=Mock(),
            linePoolURL=field("stratum://pool-1"),
            linePoolURL_2=field("stratum://pool-2"),
            linePoolURL_3=field(""),
            linePoolUser=field("account.worker"),
            linePoolUser_2=field("backup"),
            linePoolUser_3=field(""),
            linePoolPasswd=field("x"),
            linePoolPasswd_2=field("y"),
            linePoolPasswd_3=field(""),
            checkAutomaticWorkerNames=Mock(),
            _run_bulk_action=run_bulk_action,
            notify=Mock(),
        )
        subject.id_proxy.mapToSource.return_value = source_index
        subject.id_model.miner_at.return_value = SimpleNamespace(
            serial="ANTMINER12345",
            mac="aa:bb:cc:dd:ee:ff",
        )
        subject.checkAutomaticWorkerNames.isChecked.return_value = True

        await IPR.update_miner_pools(subject)

        subject.get_selected_indexes_for_action.assert_called_once_with(
            "update_miner_pools", section=2
        )
        run_bulk_action.assert_awaited_once()
        await_args = run_bulk_action.await_args
        if await_args is None:
            self.fail("pool update bulk action was not awaited")
        action, rows, make_coro = await_args.args
        self.assertEqual(action, "Update Pools")
        self.assertEqual(rows, [7])

        update_result = await make_coro(
            7,
            "10.0.0.5",
            MinerType.ANTMINER,
            MinerFirmware.STOCK,
            "secret",
        )

        self.assertIs(update_result, result)
        asic.update_miner_pools.assert_awaited_once_with(
            MinerType.ANTMINER,
            "10.0.0.5",
            ["stratum://pool-1", "stratum://pool-2", ""],
            ["account.worker.12345", "backup.12345", ""],
            ["x", "y", ""],
            alt_pwd="secret",
        )

    async def test_bulk_control_reports_empty_target_set(self):
        subject: Any = SimpleNamespace(
            asic=_ControlFacade(),
            get_action_target_rows=Mock(return_value=[]),
            _run_bulk_action=AsyncMock(),
            notify=Mock(),
        )

        await IPR._bulk_control_miners(subject, "stop")

        subject._run_bulk_action.assert_not_awaited()
        subject.notify.assert_called_once_with(
            "Status :: Failed action: no miners to stop.",
            5000,
        )


if __name__ == "__main__":
    unittest.main()
