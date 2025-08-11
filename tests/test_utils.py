import unittest

from core.utils import bytes_to_hex_dump, bytes_to_ascii


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


if __name__ == "__main__":
    unittest.main()


