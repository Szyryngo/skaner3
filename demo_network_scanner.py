#!/usr/bin/env python3
"""
Demo script showing NetworkScanner functionality
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def demo_network_scanner():
    """Demonstrate NetworkScanner functionality."""
    try:
        # Import directly
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            "network_scanner", 
            "core/network_scanner.py"
        )
        network_scanner_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(network_scanner_module)
        
        NetworkScanner = network_scanner_module.NetworkScanner
        ScanResult = network_scanner_module.ScanResult
        
        print("🔍 NetworkScanner Demo")
        print("=" * 50)
        
        scanner = NetworkScanner()
        
        # Demo 1: Auto-detect network range
        print("\n1. Auto-detecting network range...")
        detected_range = scanner.auto_detect_network_range()
        print(f"   Detected range: {detected_range}")
        
        # Demo 2: Port range parsing
        print("\n2. Port range parsing examples...")
        test_ranges = ["22,80,443", "8080-8090", "22,80,443,8080-8085"]
        for range_str in test_ranges:
            ports = scanner._parse_port_range(range_str)
            print(f"   '{range_str}' -> {ports}")
        
        # Demo 3: Scan configuration
        print("\n3. Scan configuration...")
        scanner.ip_range = "192.168.1.1-192.168.1.5"  # Small range for demo
        scanner.scan_mode = "light"
        scanner.port_range = "22,80,443"
        scanner.timeout = 0.5
        scanner.max_threads = 5
        
        print(f"   IP Range: {scanner.ip_range}")
        print(f"   Scan Mode: {scanner.scan_mode}")
        print(f"   Port Range: {scanner.port_range}")
        print(f"   Timeout: {scanner.timeout}s")
        print(f"   Max Threads: {scanner.max_threads}")
        
        # Demo 4: Mock scan results
        print("\n4. Sample scan results...")
        sample_results = [
            ScanResult("192.168.1.1", True, "router.local", [22, 80, 443], 0.045),
            ScanResult("192.168.1.2", True, "desktop-pc.local", [22], 0.123),
            ScanResult("192.168.1.3", False, None, [], None),
            ScanResult("192.168.1.4", True, "printer.local", [80, 443], 0.089),
            ScanResult("192.168.1.5", False, None, [], None),
        ]
        
        print(f"   {'IP':<15} {'Status':<8} {'Hostname':<20} {'Ports':<15} {'Time':<8}")
        print("   " + "-" * 70)
        
        for result in sample_results:
            status = "UP" if result.is_up else "DOWN"
            hostname = result.hostname or ""
            ports = ",".join(map(str, result.open_ports)) if result.open_ports else ""
            response_time = f"{result.response_time:.3f}s" if result.response_time else ""
            
            print(f"   {result.ip:<15} {status:<8} {hostname:<20} {ports:<15} {response_time:<8}")
        
        # Demo 5: Statistics
        print("\n5. Scan statistics...")
        total_hosts = len(sample_results)
        up_hosts = sum(1 for r in sample_results if r.is_up)
        down_hosts = total_hosts - up_hosts
        hosts_with_ports = sum(1 for r in sample_results if r.open_ports)
        
        print(f"   Total hosts scanned: {total_hosts}")
        print(f"   Hosts UP: {up_hosts}")
        print(f"   Hosts DOWN: {down_hosts}")
        print(f"   Hosts with open ports: {hosts_with_ports}")
        
        print("\n✨ Demo completed successfully!")
        print("\nNote: This is a demonstration with mock data.")
        print("In a real GUI application, the scanner would perform actual network scans.")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    demo_network_scanner()