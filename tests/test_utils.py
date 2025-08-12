import unittest

from core.utils import (
    bytes_to_hex_dump, bytes_to_ascii,
    get_cpu_usage, get_ram_usage, get_process_cpu_usage, get_process_ram_usage,
    get_disk_io, get_net_io, PSUTIL_AVAILABLE
)


class TestUtils(unittest.TestCase):
    def test_hex_dump_basic(self):
        data = bytes(range(16))
        dump = bytes_to_hex_dump(data)
        self.assertIn("0000:", dump)
        self.assertIn("00 01 02 03", dump)

    def test_ascii_masking(self):
        data = b"ABC\x00\x01XYZ"
        ascii_view = bytes_to_ascii(data)
        self.assertEqual(ascii_view, "ABC..XYZ")

    def test_system_monitoring_functions(self):
        """Test that system monitoring functions return expected types."""
        # CPU usage
        cpu = get_cpu_usage()
        if PSUTIL_AVAILABLE:
            self.assertTrue(cpu is None or (isinstance(cpu, (int, float)) and 0 <= cpu <= 100))
        else:
            self.assertIsNone(cpu)

        # RAM usage
        ram = get_ram_usage()
        if PSUTIL_AVAILABLE:
            self.assertTrue(ram is None or (isinstance(ram, (int, float)) and 0 <= ram <= 100))
        else:
            self.assertIsNone(ram)

        # Process CPU usage
        proc_cpu = get_process_cpu_usage()
        if PSUTIL_AVAILABLE:
            self.assertTrue(proc_cpu is None or isinstance(proc_cpu, (int, float)))
        else:
            self.assertIsNone(proc_cpu)

        # Process RAM usage
        proc_ram_mb, proc_ram_pct = get_process_ram_usage()
        if PSUTIL_AVAILABLE:
            self.assertTrue(proc_ram_mb is None or isinstance(proc_ram_mb, (int, float)))
            self.assertTrue(proc_ram_pct is None or isinstance(proc_ram_pct, (int, float)))
        else:
            self.assertIsNone(proc_ram_mb)
            self.assertIsNone(proc_ram_pct)

        # Disk I/O
        disk_read, disk_write, disk_read_count, disk_write_count = get_disk_io()
        if PSUTIL_AVAILABLE:
            for val in [disk_read, disk_write]:
                self.assertTrue(val is None or isinstance(val, (int, float)))
            for val in [disk_read_count, disk_write_count]:
                self.assertTrue(val is None or isinstance(val, int))
        else:
            self.assertIsNone(disk_read)
            self.assertIsNone(disk_write)
            self.assertIsNone(disk_read_count)
            self.assertIsNone(disk_write_count)

        # Network I/O
        net_sent, net_recv, net_sent_pkts, net_recv_pkts = get_net_io()
        if PSUTIL_AVAILABLE:
            for val in [net_sent, net_recv]:
                self.assertTrue(val is None or isinstance(val, (int, float)))
            for val in [net_sent_pkts, net_recv_pkts]:
                self.assertTrue(val is None or isinstance(val, int))
        else:
            self.assertIsNone(net_sent)
            self.assertIsNone(net_recv)
            self.assertIsNone(net_sent_pkts)
            self.assertIsNone(net_recv_pkts)


if __name__ == "__main__":
    unittest.main()


