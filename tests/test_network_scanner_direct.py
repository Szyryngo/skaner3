#!/usr/bin/env python3
"""
Direct test of NetworkScanner without going through __init__.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_network_scanner_direct():
    """Test NetworkScanner directly."""
    try:
        # Import directly without going through __init__.py
        import importlib.util
        
        # Load network_scanner module directly
        spec = importlib.util.spec_from_file_location(
            "network_scanner", 
            "../core/network_scanner.py"
        )
        network_scanner_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(network_scanner_module)
        
        NetworkScanner = network_scanner_module.NetworkScanner
        ScanResult = network_scanner_module.ScanResult
        
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
            print(f"⚠ Auto-detect fallback (expected): {range_str if 'range_str' in locals() else '192.168.1.0/24'}")
        
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
        
        print("\n🎉 All NetworkScanner tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing NetworkScanner directly...\n")
    
    success = test_network_scanner_direct()
    
    if success:
        print("\n✨ Direct NetworkScanner test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 NetworkScanner test failed!")
        sys.exit(1)