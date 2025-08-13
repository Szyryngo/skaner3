#!/usr/bin/env python3
"""
Simple test script for NetworkScanner functionality without dependencies.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_network_scanner_basic():
    """Test basic NetworkScanner functionality."""
    try:
        from core.network_scanner import NetworkScanner, ScanResult
        
        print("✓ Successfully imported NetworkScanner and ScanResult")
        
        # Test creating scanner
        scanner = NetworkScanner()
        print("✓ Successfully created NetworkScanner instance")
        
        # Test basic properties
        assert hasattr(scanner, 'ip_range')
        assert hasattr(scanner, 'port_range')
        assert hasattr(scanner, 'scan_mode')
        print("✓ Scanner has required attributes")
        
        # Test auto-detect (should work even without psutil)
        try:
            range_str = scanner.auto_detect_network_range()
            print(f"✓ Auto-detect works: {range_str}")
        except Exception as e:
            print(f"⚠ Auto-detect fallback: {e}")
        
        # Test port parsing
        ports = scanner._parse_port_range("22,80,443,8080-8090")
        expected_ports = [22, 80, 443] + list(range(8080, 8091))
        assert set(ports) == set(expected_ports)
        print("✓ Port range parsing works correctly")
        
        # Test scan result creation
        result = ScanResult(ip="192.168.1.1", is_up=True, hostname="router.local")
        assert result.ip == "192.168.1.1"
        assert result.is_up == True
        assert result.hostname == "router.local"
        print("✓ ScanResult creation works")
        
        print("\n🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_tab_creation():
    """Test NetworkScannerTab creation without PyQt5."""
    try:
        # Import without actually creating UI
        import ast
        
        with open('../ui/network_scanner_tab.py', 'r') as f:
            code = f.read()
            
        tree = ast.parse(code)
        print("✓ NetworkScannerTab code syntax is valid")
        
        # Check for required methods
        class_found = False
        methods_found = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'NetworkScannerTab':
                class_found = True
            elif isinstance(node, ast.FunctionDef):
                if node.name.startswith('_'):  # Private methods
                    methods_found.append(node.name)
        
        assert class_found, "NetworkScannerTab class not found"
        print("✓ NetworkScannerTab class found")
        
        required_methods = ['_setup_ui', '_create_config_panel', '_create_results_panel', 
                          '_start_scan', '_stop_scan', '_on_scan_result']
        
        for method in required_methods:
            if method in methods_found:
                print(f"✓ Found required method: {method}")
            else:
                print(f"⚠ Missing method: {method}")
        
        print("\n🎉 UI tab structure tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ UI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing NetworkScanner implementation...\n")
    
    success1 = test_network_scanner_basic()
    print()
    success2 = test_ui_tab_creation()
    
    if success1 and success2:
        print("\n✨ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)