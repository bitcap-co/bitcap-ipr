# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import asyncio
import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock

from ipr import IPR
from mod.ipr_asic import MinerType
from mod.lm import IPReport


class TestIPRResultProcessing(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def _subject(identify: AsyncMock) -> Any:
        subject = SimpleNamespace(
            _processing_report_ips=set(),
            _report_processing_lock=asyncio.Lock(),
            inactive=Mock(),
            asic=SimpleNamespace(identify=identify),
            checkEnableListenFilter=Mock(),
            notify=Mock(),
            show_confirmation=Mock(),
        )
        subject.inactive.isActive.return_value = False
        subject.checkEnableListenFilter.isChecked.return_value = False
        subject._process_result = lambda result: IPR._process_result(subject, result)
        return subject

    async def test_duplicate_ip_is_ignored_while_first_report_is_processing(self):
        entered = asyncio.Event()
        release = asyncio.Event()

        async def identify(**_kwargs):
            entered.set()
            await release.wait()
            return MinerType.UNKNOWN

        identify_mock = AsyncMock(side_effect=identify)
        subject = self._subject(identify_mock)
        report = IPReport(
            updated_at=1234,
            ip="172.16.35.128",
            mac="aa:bb:cc:dd:ee:ff",
        )
        process_result = IPR.process_result.__wrapped__

        first = asyncio.create_task(process_result(subject, report))
        await asyncio.wait_for(entered.wait(), timeout=1)
        await process_result(subject, report)

        self.assertEqual(identify_mock.await_count, 1)
        self.assertEqual(subject._processing_report_ips, {report.ip})

        release.set()
        await asyncio.wait_for(first, timeout=1)

        subject.show_confirmation.assert_called_once()
        self.assertEqual(subject._processing_report_ips, set())

    async def test_different_ips_are_processed_sequentially(self):
        first_entered = asyncio.Event()
        release_first = asyncio.Event()
        second_entered = asyncio.Event()

        async def identify(*, ip, **_kwargs):
            if ip == "172.16.35.128":
                first_entered.set()
                await release_first.wait()
            else:
                second_entered.set()
            return MinerType.UNKNOWN

        identify_mock = AsyncMock(side_effect=identify)
        subject = self._subject(identify_mock)
        first_report = IPReport(updated_at=1234, ip="172.16.35.128")
        second_report = IPReport(updated_at=1235, ip="172.16.35.129")
        process_result = IPR.process_result.__wrapped__

        first = asyncio.create_task(process_result(subject, first_report))
        await asyncio.wait_for(first_entered.wait(), timeout=1)
        second = asyncio.create_task(process_result(subject, second_report))
        await asyncio.sleep(0)

        self.assertFalse(second_entered.is_set())
        self.assertEqual(
            subject._processing_report_ips,
            {first_report.ip, second_report.ip},
        )

        release_first.set()
        await asyncio.wait_for(asyncio.gather(first, second), timeout=1)

        self.assertTrue(second_entered.is_set())
        self.assertEqual(identify_mock.await_count, 2)
        self.assertEqual(subject._processing_report_ips, set())

    async def test_processing_ip_is_released_after_error(self):
        identify_mock = AsyncMock(side_effect=RuntimeError("lookup failed"))
        subject = self._subject(identify_mock)
        report = IPReport(ip="172.16.35.128")
        process_result = IPR.process_result.__wrapped__

        with self.assertRaisesRegex(RuntimeError, "lookup failed"):
            await process_result(subject, report)

        self.assertEqual(subject._processing_report_ips, set())


if __name__ == "__main__":
    unittest.main()
