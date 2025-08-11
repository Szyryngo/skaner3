import unittest

from core.ai_engine import AIEngine, RIVER_AVAILABLE
from core.utils import PacketInfo


class TestAIEngine(unittest.TestCase):
    def make_packet(self, length=60, proto="TCP", src_port=1234, dst_port=80):
        return PacketInfo(
            timestamp=0.0,
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=src_port,
            dst_port=dst_port,
            protocol=proto,
            length=length,
            raw_bytes=b"\x00" * length,
        )

    def test_heuristic_threshold(self):
        engine = AIEngine(large_packet_threshold=1000, ml_enabled=False, ml_stream_enabled=False)
        p_small = self.make_packet(length=200)
        p_large = self.make_packet(length=2000)
        r_small = engine.analyze_packet(p_small)
        r_large = engine.analyze_packet(p_large)
        self.assertFalse(r_small["is_anomaly"])  # heurystyka sama z siebie nie przekracza progu
        self.assertIn("large_length>=1000", r_large["reasons"])  # wykrywa powód

    @unittest.skipUnless(RIVER_AVAILABLE, "river not available")
    def test_streaming_learns(self):
        engine = AIEngine(ml_enabled=False, ml_stream_enabled=True, stream_z_threshold=10.0)
        for _ in range(50):
            engine.analyze_packet(self.make_packet(length=100))
        status = engine.get_status()
        self.assertGreaterEqual(status.get("stream_count", 0), 1)


if __name__ == "__main__":
    unittest.main()


