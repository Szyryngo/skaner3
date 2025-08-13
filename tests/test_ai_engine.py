import unittest
import logging
import io
import sys

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

    def test_logger_initialization(self):
        """Test that logger is properly initialized and configured."""
        engine = AIEngine(ml_enabled=False, ml_stream_enabled=False)
        
        # Check logger exists and is properly named
        self.assertEqual(engine.logger.name, "skaner3.ai_engine")
        
        # Check logger has handlers
        self.assertTrue(len(engine.logger.handlers) > 0)
        
        # Check logger respects hierarchy (doesn't override parent level)
        self.assertEqual(engine.logger.level, logging.NOTSET)  # Should inherit from parent

    def test_analyze_packet_preserves_api(self):
        """Test that analyze_packet API is unchanged after logging modifications."""
        engine = AIEngine(ml_enabled=False, ml_stream_enabled=False)
        packet = self.make_packet(length=1500, dst_port=23)  # Should trigger anomaly
        
        result = engine.analyze_packet(packet)
        
        # Check all expected keys are present
        expected_keys = ["is_anomaly", "score", "reasons", "combined_score"]
        for key in expected_keys:
            self.assertIn(key, result)
        
        # Check types are correct
        self.assertIsInstance(result["is_anomaly"], bool)
        self.assertIsInstance(result["score"], (int, float))
        self.assertIsInstance(result["reasons"], list)
        self.assertIsInstance(result["combined_score"], (int, float))

    def test_logging_captures_performance(self):
        """Test that logging captures initialization and analysis timing."""
        # Capture log output
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        
        # Create engine with custom logger to capture output
        engine = AIEngine(ml_enabled=False, ml_stream_enabled=False)
        
        # Clear existing handlers and add our test handler
        engine.logger.handlers.clear()
        engine.logger.addHandler(handler)
        engine.logger.setLevel(logging.DEBUG)
        
        # Re-trigger initialization log by creating a new engine
        engine2 = AIEngine(ml_enabled=False, ml_stream_enabled=False)
        
        # Clear existing handlers and add our test handler for analysis
        engine2.logger.handlers.clear()
        engine2.logger.addHandler(handler)
        engine2.logger.setLevel(logging.DEBUG)
        
        # Analyze a packet
        packet = self.make_packet()
        result = engine2.analyze_packet(packet)
        
        # Check log output contains timing information
        log_output = log_stream.getvalue()
        
        # Should contain timing information for packet analysis
        self.assertIn("ms", log_output)
        self.assertIn("anomaly:", log_output)
        
        # Clean up
        handler.close()


if __name__ == "__main__":
    unittest.main()


