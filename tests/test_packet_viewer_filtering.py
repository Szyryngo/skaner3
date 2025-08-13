"""
Tests for PacketViewer filtering functionality with debouncing.
"""

import unittest
import sys
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtTest import QTest

# Add the parent directory to the path to import modules
sys.path.insert(0, '/home/runner/work/skaner3/skaner3')

from ui.packet_viewer import PacketViewer


class TestPacketViewerFiltering(unittest.TestCase):
    """Test the debounced filtering functionality in PacketViewer."""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for testing."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test fixture."""
        self.packet_viewer = PacketViewer()
        
        # Add some test packets
        self.test_packets = [
            {"time": "10:00:01", "src_ip": "192.168.1.1", "dst_ip": "10.0.0.1", 
             "src_port": "80", "dst_port": "443", "protocol": "TCP", "length": "1024"},
            {"time": "10:00:02", "src_ip": "192.168.1.2", "dst_ip": "10.0.0.2", 
             "src_port": "22", "dst_port": "8080", "protocol": "UDP", "length": "512"},
            {"time": "10:00:03", "src_ip": "172.16.0.1", "dst_ip": "8.8.8.8", 
             "src_port": "53", "dst_port": "443", "protocol": "TCP", "length": "256"},
        ]
        
        for packet in self.test_packets:
            self.packet_viewer.add_packet_row(packet)

    def test_debounce_timer_exists(self):
        """Test that debounce timer is created."""
        self.assertIsInstance(self.packet_viewer._filter_timer, QTimer)
        self.assertEqual(self.packet_viewer._filter_timer.interval(), 200)
        self.assertTrue(self.packet_viewer._filter_timer.isSingleShot())

    def test_text_filter_debouncing(self):
        """Test that text filter is debounced and doesn't trigger immediately."""
        # Check if timer starts when filter changes
        self.assertFalse(self.packet_viewer._filter_timer.isActive())
        
        # Set filter text
        self.packet_viewer.filter_text.setText("192.168")
        
        # Timer should now be active
        self.assertTrue(self.packet_viewer._filter_timer.isActive())
        
        # Change text again quickly
        self.packet_viewer.filter_text.setText("192.168.1")
        
        # Timer should still be active (restarted)
        self.assertTrue(self.packet_viewer._filter_timer.isActive())
        
        # Let the timer finish and check that filtering occurs
        initial_visible = self._count_visible_rows()
        
        # Process the timer
        while self.packet_viewer._filter_timer.isActive():
            self.app.processEvents()
            QTest.qWait(10)
        
        # Timer should be finished
        self.assertFalse(self.packet_viewer._filter_timer.isActive())
        
        # Verify filtering actually happened
        filtered_visible = self._count_visible_rows()
        self.assertLess(filtered_visible, initial_visible)  # Should have fewer visible rows

    def test_protocol_filter_works(self):
        """Test that protocol filter works correctly."""
        # Initially all rows should be visible
        self.assertEqual(self._count_visible_rows(), 3)
        
        # Filter by TCP
        self.packet_viewer.filter_protocol.setCurrentText("TCP")
        self.packet_viewer._apply_filters_immediate()
        
        # Should show only TCP packets (2 packets)
        self.assertEqual(self._count_visible_rows(), 2)
        
        # Filter by UDP
        self.packet_viewer.filter_protocol.setCurrentText("UDP")
        self.packet_viewer._apply_filters_immediate()
        
        # Should show only UDP packets (1 packet)
        self.assertEqual(self._count_visible_rows(), 1)

    def test_text_filter_works(self):
        """Test that text filter works on specified fields."""
        # Filter by IP address
        self.packet_viewer.filter_text.setText("192.168.1.1")
        self.packet_viewer._apply_filters_immediate()
        
        # Should show only packets with that IP (1 packet)
        self.assertEqual(self._count_visible_rows(), 1)
        
        # Filter by port
        self.packet_viewer.filter_text.clear()
        self.packet_viewer.filter_text.setText("443")
        self.packet_viewer._apply_filters_immediate()
        
        # Should show packets with port 443 (2 packets)
        self.assertEqual(self._count_visible_rows(), 2)

    def test_combined_filters(self):
        """Test that text and protocol filters work together."""
        # Filter by TCP and port 443
        self.packet_viewer.filter_protocol.setCurrentText("TCP")
        self.packet_viewer.filter_text.setText("443")
        self.packet_viewer._apply_filters_immediate()
        
        # Should show only TCP packets with port 443 (2 packets)
        self.assertEqual(self._count_visible_rows(), 2)

    def test_bulk_adding_mode(self):
        """Test that bulk adding mode prevents immediate filtering."""
        # Set bulk adding mode
        self.packet_viewer.set_bulk_adding(True)
        
        # Add a new packet - should not trigger filtering
        with patch.object(self.packet_viewer, '_apply_filter_to_row') as mock_filter:
            new_packet = {"time": "10:00:04", "src_ip": "10.10.10.10", "dst_ip": "20.20.20.20", 
                         "src_port": "9999", "dst_port": "8888", "protocol": "TCP", "length": "128"}
            self.packet_viewer.add_packet_row(new_packet)
            
            # Should not apply filter to the row in bulk mode
            mock_filter.assert_not_called()
        
        # End bulk adding mode
        with patch.object(self.packet_viewer, '_apply_filters_immediate') as mock_apply_all:
            self.packet_viewer.set_bulk_adding(False)
            # Should apply filters to all rows when bulk mode ends
            mock_apply_all.assert_called_once()

    def test_clear_filter_shows_all_rows(self):
        """Test that clearing filters shows all rows."""
        # Apply a filter first
        self.packet_viewer.filter_text.setText("192.168.1.1")
        self.packet_viewer._apply_filters_immediate()
        self.assertEqual(self._count_visible_rows(), 1)
        
        # Clear the filter
        self.packet_viewer.filter_text.clear()
        self.packet_viewer._apply_filters_immediate()
        
        # All rows should be visible again
        self.assertEqual(self._count_visible_rows(), 3)

    def test_performance_optimization_limited_fields(self):
        """Test that filtering only checks specified fields for performance."""
        # This test ensures we only check specific columns as per requirements
        # Add a packet with a special value in the time field (column 0)
        special_packet = {"time": "SPECIAL_TIME_VALUE", "src_ip": "1.1.1.1", "dst_ip": "2.2.2.2", 
                         "src_port": "1111", "dst_port": "2222", "protocol": "TCP", "length": "999"}
        self.packet_viewer.add_packet_row(special_packet)
        
        # Filter by the special time value
        self.packet_viewer.filter_text.setText("SPECIAL_TIME_VALUE")
        self.packet_viewer._apply_filters_immediate()
        
        # Since we only check columns 1-6 (not time column 0), this should not match
        # All rows should be hidden
        self.assertEqual(self._count_visible_rows(), 0)

    def _count_visible_rows(self):
        """Helper method to count visible rows in the table."""
        count = 0
        for row in range(self.packet_viewer.table.rowCount()):
            if not self.packet_viewer.table.isRowHidden(row):
                count += 1
        return count


if __name__ == '__main__':
    unittest.main()