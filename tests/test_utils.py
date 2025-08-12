import unittest

from core.utils import (
    bytes_to_hex_dump, 
    bytes_to_ascii, 
    get_cpu_usage, 
    get_ram_usage, 
    get_process_cpu_usage, 
    get_process_ram_usage, 
    get_disk_io, 
    get_net_io
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

    def test_get_cpu_usage(self):
        """Test that CPU usage returns a valid percentage."""
        cpu = get_cpu_usage()
        self.assertIsInstance(cpu, float)
        self.assertGreaterEqual(cpu, 0.0)
        self.assertLessEqual(cpu, 100.0)

    def test_get_ram_usage(self):
        """Test that RAM usage returns a valid percentage."""
        ram = get_ram_usage()
        self.assertIsInstance(ram, float)
        self.assertGreaterEqual(ram, 0.0)
        self.assertLessEqual(ram, 100.0)

    def test_get_process_cpu_usage(self):
        """Test that process CPU usage returns a valid percentage."""
        cpu = get_process_cpu_usage()
        self.assertIsInstance(cpu, float)
        self.assertGreaterEqual(cpu, 0.0)

    def test_get_process_ram_usage(self):
        """Test that process RAM usage returns valid MB and percentage."""
        ram_mb, ram_percent = get_process_ram_usage()
        self.assertIsInstance(ram_mb, float)
        self.assertIsInstance(ram_percent, float)
        self.assertGreaterEqual(ram_mb, 0.0)
        self.assertGreaterEqual(ram_percent, 0.0)
        self.assertLessEqual(ram_percent, 100.0)

    def test_get_disk_io(self):
        """Test that disk I/O returns valid counters."""
        read_bytes, write_bytes, read_count, write_count = get_disk_io()
        self.assertIsInstance(read_bytes, int)
        self.assertIsInstance(write_bytes, int)
        self.assertIsInstance(read_count, int)
        self.assertIsInstance(write_count, int)
        self.assertGreaterEqual(read_bytes, 0)
        self.assertGreaterEqual(write_bytes, 0)
        self.assertGreaterEqual(read_count, 0)
        self.assertGreaterEqual(write_count, 0)

    def test_get_net_io(self):
        """Test that network I/O returns valid counters."""
        sent_bytes, recv_bytes, sent_packets, recv_packets = get_net_io()
        self.assertIsInstance(sent_bytes, int)
        self.assertIsInstance(recv_bytes, int)
        self.assertIsInstance(sent_packets, int)
        self.assertIsInstance(recv_packets, int)
        self.assertGreaterEqual(sent_bytes, 0)
        self.assertGreaterEqual(recv_bytes, 0)
        self.assertGreaterEqual(sent_packets, 0)
        self.assertGreaterEqual(recv_packets, 0)


if __name__ == "__main__":
    unittest.main()


