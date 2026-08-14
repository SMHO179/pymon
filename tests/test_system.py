"""Basic tests for pymon system module."""
import unittest
from pymon.system import (
    read_cpu_stats, read_memory_info, read_disk_info,
    read_network_info, read_load_average, read_uptime,
    read_processes, CPUStats, MemoryInfo, DiskInfo,
    NetworkInfo, ProcessInfo, LoadAverage, Uptime,
    calculate_cpu_percent, format_bytes, format_uptime)


class TestCPUStats(unittest.TestCase):
    def test_stats_have_all_fields(self):
        stats = read_cpu_stats()
        self.assertGreater(len(stats), 0)
        for s in stats:
            self.assertIsInstance(s, CPUStats)
            self.assertGreater(s.total, 0)
            self.assertGreaterEqual(s.busy, 0)

    def test_total_property(self):
        stats = read_cpu_stats()
        s = stats[0]
        expected = (s.user + s.nice + s.system + s.idle +
                    s.iowait + s.irq + s.softirq + s.steal +
                    s.guest + s.guest_nice)
        self.assertEqual(s.total, expected)

    def test_busy_property(self):
        stats = read_cpu_stats()
        s = stats[0]
        expected = s.total - s.idle - s.iowait
        self.assertEqual(s.busy, expected)


class TestMemoryInfo(unittest.TestCase):
    def test_memory_has_all_fields(self):
        mem = read_memory_info()
        self.assertIsInstance(mem, MemoryInfo)
        self.assertGreater(mem.total, 0)
        self.assertGreaterEqual(mem.available, 0)
        self.assertGreaterEqual(mem.used, 0)
        self.assertGreaterEqual(mem.free, 0)
        self.assertGreaterEqual(mem.swap_total, 0)
        self.assertGreaterEqual(mem.swap_used, 0)
        self.assertGreaterEqual(mem.swap_free, 0)

    def test_format_bytes(self):
        self.assertEqual(format_bytes(0), "0.0B")
        self.assertEqual(format_bytes(1024), "1.0K")
        self.assertEqual(format_bytes(1048576), "1.0M")
        self.assertEqual(format_bytes(1073741824), "1.0G")


class TestLoadAverage(unittest.TestCase):
    def test_load_has_all_fields(self):
        load = read_load_average()
        self.assertIsInstance(load, LoadAverage)
        self.assertGreaterEqual(load.load1, 0)
        self.assertGreaterEqual(load.load5, 0)
        self.assertGreaterEqual(load.load15, 0)


class TestUptime(unittest.TestCase):
    def test_uptime_positive(self):
        uptime = read_uptime()
        self.assertIsInstance(uptime, Uptime)
        self.assertGreater(uptime.seconds, 0)
        self.assertGreaterEqual(uptime.idle_seconds, 0)


class TestProcesses(unittest.TestCase):
    def test_processes_have_required_fields(self):
        procs = read_processes()
        self.assertGreater(len(procs), 0)
        for p in procs:
            self.assertIsInstance(p, ProcessInfo)
            self.assertGreater(p.pid, 0)
            self.assertIsNotNone(p.name)
            self.assertIsNotNone(p.status)


class TestDiskInfo(unittest.TestCase):
    def test_disk_info(self):
        disks = read_disk_info()
        for d in disks:
            self.assertIsInstance(d, DiskInfo)
            self.assertGreaterEqual(d.total, 0)
            self.assertGreaterEqual(d.used, 0)
            self.assertGreaterEqual(d.free, 0)


class TestNetworkInfo(unittest.TestCase):
    def test_network_info(self):
        nets = read_network_info()
        for n in nets:
            self.assertIsInstance(n, NetworkInfo)
            self.assertNotEqual(n.interface, 'lo')
            self.assertGreaterEqual(n.rx_bytes, 0)
            self.assertGreaterEqual(n.tx_bytes, 0)


class TestFormatting(unittest.TestCase):
    def test_format_uptime(self):
        self.assertEqual(format_uptime(0), "0m")
        self.assertEqual(format_uptime(60), "1m")
        self.assertEqual(format_uptime(3600), "1h 0m")
        self.assertEqual(format_uptime(3661), "1h 1m")
        self.assertEqual(format_uptime(90061), "1d 1h 1m")


class TestCalculateCPUPercent(unittest.TestCase):
    def test_cpu_percent_calculation(self):
        prev = [CPUStats(10, 0, 20, 50, 5, 2, 1, 0, 0, 0)]
        curr = [CPUStats(20, 0, 30, 60, 5, 2, 1, 0, 0, 0)]
        percents = calculate_cpu_percent(prev, curr)
        self.assertEqual(len(percents), 1)
        self.assertGreater(percents[0], 0)
