#!/usr/bin/env python3
"""
Manual test script to verify SystemStatusViewer implementation.
Run this script to test the new System tab functionality.

Usage:
    python3 manual_test_system.py
"""
import os
import sys

# Set offscreen mode for headless environments
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt5.QtWidgets import QApplication
    from ui.main_window import MainWindow
    from core.system_info import get_system_info
    
    def manual_test():
        """Manual test function for SystemStatusViewer."""
        print("=== SystemStatusViewer Manual Test ===")
        
        # Create QApplication
        app = QApplication([])
        
        # Test 1: Check system_info function
        print("\n1. Testing get_system_info()...")
        system_info = get_system_info()
        print(f"   ✓ Retrieved {len(system_info)} system parameters")
        for key, value in system_info.items():
            print(f"     - {key}: {value}")
        
        # Test 2: Create main window
        print("\n2. Testing MainWindow creation...")
        window = MainWindow()
        print(f"   ✓ MainWindow created with {window.tabs.count()} tabs")
        
        # Test 3: Check tabs
        print("\n3. Testing tab structure...")
        expected_tabs = ["Pakiety", "Alerty", "AI", "Wizualizacja", "System"]
        for i, expected in enumerate(expected_tabs):
            actual = window.tabs.tabText(i)
            status = "✓" if actual == expected else "✗"
            print(f"     {status} Tab {i}: {actual}")
        
        # Test 4: Check System tab content
        print("\n4. Testing System tab content...")
        window.tabs.setCurrentIndex(4)  # Switch to System tab
        
        system_widget = window.system_status
        summary = system_widget.label_summary.text()
        details = system_widget.text_details.toPlainText()
        
        print(f"   Summary: {summary}")
        print(f"   Details preview: {details[:100]}...")
        
        # Verify content
        checks = [
            ("OS info in summary", "OS:" in summary),
            ("CPU info in summary", "CPU:" in summary),
            ("RAM info in summary", "RAM:" in summary),
            ("Disk info in summary", "Disk:" in summary),
            ("System section in details", "SYSTEM OPERACYJNY" in details),
            ("CPU section in details", "PROCESOR" in details),
            ("RAM section in details", "PAMIĘĆ RAM" in details),
            ("Disk section in details", "DYSK" in details),
        ]
        
        print("\n   Content verification:")
        all_passed = True
        for desc, condition in checks:
            status = "✓" if condition else "✗"
            print(f"     {status} {desc}")
            if not condition:
                all_passed = False
        
        # Test 5: Update functionality
        print("\n5. Testing update functionality...")
        try:
            new_info = get_system_info()
            system_widget.update_status(new_info)
            new_summary = system_widget.label_summary.text()
            print(f"   ✓ Update successful: {new_summary}")
        except Exception as e:
            print(f"   ✗ Update failed: {e}")
            all_passed = False
        
        # Final result
        print(f"\n=== Test Result: {'PASS' if all_passed else 'FAIL'} ===")
        
        app.quit()
        return all_passed
    
    if __name__ == "__main__":
        success = manual_test()
        sys.exit(0 if success else 1)
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running this from the skaner3 directory")
    print("and that all dependencies are installed (pip install -r requirements.txt)")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)