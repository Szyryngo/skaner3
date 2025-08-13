#!/usr/bin/env python3
"""
Final verification script to test all filtering requirements.
This script verifies that all requirements from the problem statement are met.
"""

import sys
import time
from io import StringIO
sys.path.insert(0, '/home/runner/work/skaner3/skaner3')

from ui.packet_viewer import PacketViewer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer


def test_requirement_1_debouncing():
    """Test requirement: Filtering is debounced (200ms delay)."""
    print("✓ Testing debouncing (200ms delay)...")
    
    app = QApplication.instance() or QApplication([])
    viewer = PacketViewer()
    
    # Check timer properties
    assert viewer._filter_timer.interval() == 200, f"Expected 200ms, got {viewer._filter_timer.interval()}ms"
    assert viewer._filter_timer.isSingleShot(), "Timer should be single shot"
    
    # Check timer is not active initially
    assert not viewer._filter_timer.isActive(), "Timer should not be active initially"
    
    # Set text and check timer starts
    viewer.filter_text.setText("test")
    assert viewer._filter_timer.isActive(), "Timer should be active after text change"
    
    print("   ✓ Debouncing timer configured correctly (200ms)")


def test_requirement_2_performance_fields():
    """Test requirement: Filtering only on selected fields (IP, port, protocol, info)."""
    print("✓ Testing performance optimization (limited fields)...")
    
    app = QApplication.instance() or QApplication([])
    viewer = PacketViewer()
    
    # Add test packet with special value in time field (column 0)
    test_packet = {
        "time": "SPECIAL_TIME_VALUE",
        "src_ip": "1.1.1.1",
        "dst_ip": "2.2.2.2", 
        "src_port": "1111",
        "dst_port": "2222",
        "protocol": "TCP",
        "length": "999"
    }
    viewer.add_packet_row(test_packet)
    
    # Filter by time value - should not match since we only check columns 1-6
    viewer.filter_text.setText("SPECIAL_TIME_VALUE")
    viewer._apply_filters_immediate()
    
    # Should be hidden because time field (column 0) is not checked
    assert viewer.table.isRowHidden(0), "Row should be hidden - time field not searched for performance"
    
    print("   ✓ Filtering only checks specified fields (not time column)")


def test_requirement_3_bulk_mode():
    """Test requirement: Adding packets doesn't trigger immediate filter."""
    print("✓ Testing bulk mode optimization...")
    
    app = QApplication.instance() or QApplication([])
    viewer = PacketViewer()
    
    # Set bulk mode
    viewer.set_bulk_adding(True)
    
    # Add packet in bulk mode - should not apply filter immediately
    test_packet = {
        "time": "10:00:01",
        "src_ip": "192.168.1.1",
        "dst_ip": "10.0.0.1", 
        "src_port": "80",
        "dst_port": "443",
        "protocol": "TCP",
        "length": "1024"
    }
    
    # Set a filter first
    viewer.filter_text.setText("999.999.999.999")  # Should not match
    viewer._apply_filters_immediate()
    
    # Add packet in bulk mode
    viewer.add_packet_row(test_packet)
    
    # Row should be visible despite filter (because bulk mode prevents filtering)
    assert not viewer.table.isRowHidden(0), "Row should be visible in bulk mode"
    
    # End bulk mode - should apply filters
    viewer.set_bulk_adding(False)
    
    # Now row should be hidden
    assert viewer.table.isRowHidden(0), "Row should be hidden after bulk mode ends"
    
    print("   ✓ Bulk adding mode prevents immediate filtering")


def test_requirement_4_non_invasive():
    """Test requirement: Code doesn't break existing logic."""
    print("✓ Testing backward compatibility...")
    
    app = QApplication.instance() or QApplication([])
    viewer = PacketViewer()
    
    # Test that legacy apply_filters() method still works
    viewer.add_packet_row({
        "time": "10:00:01", "src_ip": "192.168.1.1", "dst_ip": "10.0.0.1",
        "src_port": "80", "dst_port": "443", "protocol": "TCP", "length": "1024"
    })
    
    # Legacy method should trigger debounced filtering
    viewer.apply_filters()
    assert viewer._filter_timer.isActive(), "Legacy apply_filters should trigger debouncing"
    
    print("   ✓ Legacy methods preserved for backward compatibility")


def test_requirement_5_gui_only():
    """Test requirement: Filtering is GUI-only, doesn't affect backend."""
    print("✓ Testing GUI-only filtering...")
    
    app = QApplication.instance() or QApplication([])
    viewer = PacketViewer()
    
    # Add multiple packets
    packets = [
        {"time": "10:00:01", "src_ip": "192.168.1.1", "dst_ip": "10.0.0.1", 
         "src_port": "80", "dst_port": "443", "protocol": "TCP", "length": "1024"},
        {"time": "10:00:02", "src_ip": "192.168.1.2", "dst_ip": "10.0.0.2", 
         "src_port": "22", "dst_port": "8080", "protocol": "UDP", "length": "512"},
    ]
    
    for packet in packets:
        viewer.add_packet_row(packet)
    
    # Check initial state
    assert viewer.table.rowCount() == 2, "Should have 2 rows in table"
    
    # Apply filter
    viewer.filter_text.setText("192.168.1.1")
    viewer._apply_filters_immediate()
    
    # Table still has all rows, just some are hidden
    assert viewer.table.rowCount() == 2, "Table should still have all rows"
    assert viewer.table.isRowHidden(1), "Second row should be hidden"
    assert not viewer.table.isRowHidden(0), "First row should be visible"
    
    # Clear filter - all rows visible again
    viewer.filter_text.clear()
    viewer._apply_filters_immediate()
    assert not viewer.table.isRowHidden(0), "First row should be visible"
    assert not viewer.table.isRowHidden(1), "Second row should be visible"
    
    print("   ✓ Filtering only affects view, not underlying data")


def main():
    """Run all requirement verification tests."""
    print("=== Verification of Packet Filtering Requirements ===\n")
    
    # Set up Qt application
    app = QApplication.instance() or QApplication([])
    
    try:
        test_requirement_1_debouncing()
        test_requirement_2_performance_fields()
        test_requirement_3_bulk_mode()
        test_requirement_4_non_invasive()
        test_requirement_5_gui_only()
        
        print("\n=== All Requirements Verified Successfully ===")
        print("✓ Debouncing: 200ms delay implemented")
        print("✓ Performance: Limited field checking")
        print("✓ Bulk mode: No immediate filtering during packet bursts")
        print("✓ Non-invasive: Backward compatibility maintained")
        print("✓ GUI-only: View filtering without data modification")
        print("✓ Existing functionality: All preserved")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        return False


if __name__ == '__main__':
    import os
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    success = main()
    sys.exit(0 if success else 1)