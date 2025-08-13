#!/usr/bin/env python3
"""
Demo script to test the debounced filtering functionality in PacketViewer.
This script creates a PacketViewer widget, adds some test packets, and demonstrates
the filtering capabilities without requiring the full application.
"""

import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QTimer

# Add the current directory to the path
sys.path.insert(0, '/home/runner/work/skaner3/skaner3')

from ui.packet_viewer import PacketViewer


class FilteringDemo(QMainWindow):
    """Demo window to showcase the filtering functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Packet Filtering Demo - Debounced Filtering")
        self.setGeometry(100, 100, 1000, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Info label
        info_label = QLabel("Demo: Debounced packet filtering (200ms delay)")
        info_label.setStyleSheet("font-weight: bold; padding: 10px; background-color: #e6f3ff;")
        layout.addWidget(info_label)
        
        # Create PacketViewer
        self.packet_viewer = PacketViewer()
        layout.addWidget(self.packet_viewer)
        
        # Add test data
        self.add_test_packets()
        
        # Instructions label
        instructions = QLabel(
            "Instructions:\n"
            "• Type in the search box to filter packets (IP, port, protocol, length)\n"
            "• Use the protocol dropdown to filter by protocol type\n"
            "• Notice the 200ms debounce delay when typing quickly\n"
            "• Filtering only affects the view, not the underlying data"
        )
        instructions.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(instructions)
        
    def add_test_packets(self):
        """Add various test packets to demonstrate filtering."""
        test_packets = [
            {"time": "10:00:01", "src_ip": "192.168.1.100", "dst_ip": "8.8.8.8", 
             "src_port": "54321", "dst_port": "53", "protocol": "UDP", "length": "64"},
            {"time": "10:00:02", "src_ip": "192.168.1.100", "dst_ip": "93.184.216.34", 
             "src_port": "54322", "dst_port": "80", "protocol": "TCP", "length": "1460"},
            {"time": "10:00:03", "src_ip": "192.168.1.100", "dst_ip": "93.184.216.34", 
             "src_port": "54322", "dst_port": "80", "protocol": "TCP", "length": "512"},
            {"time": "10:00:04", "src_ip": "10.0.0.1", "dst_ip": "192.168.1.100", 
             "src_port": "22", "dst_port": "54323", "protocol": "TCP", "length": "1024"},
            {"time": "10:00:05", "src_ip": "172.16.0.1", "dst_ip": "192.168.1.100", 
             "src_port": "443", "dst_port": "54324", "protocol": "TCP", "length": "1500"},
            {"time": "10:00:06", "src_ip": "192.168.1.200", "dst_ip": "8.8.4.4", 
             "src_port": "54325", "dst_port": "53", "protocol": "UDP", "length": "64"},
            {"time": "10:00:07", "src_ip": "192.168.1.200", "dst_ip": "1.1.1.1", 
             "src_port": "54326", "dst_port": "853", "protocol": "TCP", "length": "128"},
            {"time": "10:00:08", "src_ip": "192.168.1.100", "dst_ip": "142.250.185.206", 
             "src_port": "54327", "dst_port": "443", "protocol": "TCP", "length": "1024"},
            {"time": "10:00:09", "src_ip": "10.0.0.2", "dst_ip": "192.168.1.100", 
             "src_port": "8080", "dst_port": "54328", "protocol": "TCP", "length": "2048"},
            {"time": "10:00:10", "src_ip": "192.168.1.100", "dst_ip": "127.0.0.1", 
             "src_port": "54329", "dst_port": "3306", "protocol": "TCP", "length": "256"},
        ]
        
        print(f"Adding {len(test_packets)} test packets...")
        for i, packet in enumerate(test_packets):
            # Add some color scoring for demo
            score = 0.1 + (i % 4) * 0.25  # Varies from 0.1 to 0.85
            self.packet_viewer.add_packet_row(packet, score)
        
        print("Test packets added. Filter functionality is ready to test.")


def main():
    """Run the demo application."""
    app = QApplication(sys.argv)
    
    demo = FilteringDemo()
    demo.show()
    
    print("Demo window opened.")
    print("Test the following features:")
    print("1. Type '192.168' in the search box - should filter to show only those IPs")
    print("2. Clear and type '443' - should show only packets with port 443")
    print("3. Select 'TCP' from protocol dropdown - should show only TCP packets")
    print("4. Type quickly in the search box - notice the 200ms debounce delay")
    print("5. Clear all filters - should show all packets again")
    
    # For headless testing, exit after a short time
    if '--test' in sys.argv:
        QTimer.singleShot(2000, app.quit)
    
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())