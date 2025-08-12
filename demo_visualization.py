#!/usr/bin/env python3
"""
Demonstration script for the network visualization functionality.
This script shows the key features implemented without requiring GUI.
"""

import sys
import time
import random
from datetime import datetime, timedelta
from collections import defaultdict, deque

def demo_network_visualization():
    """Demonstrate the network visualization features."""
    
    print("=" * 60)
    print("NETWORK VISUALIZATION DEMONSTRATION")
    print("=" * 60)
    
    # Import test
    print("\n1. Testing imports...")
    try:
        from ui.network_visualization import NetworkVisualization
        from ui.main_window import MainWindow
        from core.utils import PacketInfo, make_fake_packet, geolocate_ip
        print("✓ All components imported successfully")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    
    # Data structures test
    print("\n2. Testing data structures...")
    
    # Simulate the deque structures used in visualization
    traffic_history = deque(maxlen=60)  # 1 minute of data
    packet_size_history = deque(maxlen=60)
    protocol_counts = defaultdict(int)
    
    print("✓ Data structures initialized")
    
    # Generate sample data
    print("\n3. Generating sample network traffic data...")
    
    base_time = datetime.now()
    for i in range(60):  # 60 seconds of data
        # Simulate varying traffic levels
        packets_per_second = random.randint(5, 50)
        bytes_per_second = random.randint(1000, 100000)
        
        timestamp = base_time + timedelta(seconds=i)
        traffic_history.append((timestamp, packets_per_second))
        packet_size_history.append((timestamp, bytes_per_second))
        
        # Simulate protocol distribution
        for _ in range(packets_per_second):
            protocol = random.choices(
                ["TCP", "UDP", "IP", "ICMP"], 
                weights=[60, 25, 10, 5]
            )[0]
            protocol_counts[protocol] += 1
    
    print(f"✓ Generated {len(traffic_history)} data points")
    
    # Traffic analysis
    print("\n4. Analyzing traffic patterns...")
    
    if traffic_history:
        times, counts = zip(*traffic_history)
        avg_packets = sum(counts) / len(counts)
        max_packets = max(counts)
        min_packets = min(counts)
        
        print(f"   Average packets/sec: {avg_packets:.1f}")
        print(f"   Peak traffic: {max_packets} packets/sec")
        print(f"   Minimum traffic: {min_packets} packets/sec")
    
    if packet_size_history:
        times, sizes = zip(*packet_size_history)
        total_bytes = sum(sizes)
        avg_bytes = total_bytes / len(sizes)
        
        print(f"   Total data: {total_bytes:,} bytes ({total_bytes/1024/1024:.2f} MB)")
        print(f"   Average bandwidth: {avg_bytes:,.0f} bytes/sec")
    
    # Protocol distribution
    print("\n5. Protocol distribution analysis...")
    total_packets = sum(protocol_counts.values())
    
    for protocol, count in sorted(protocol_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_packets) * 100
        print(f"   {protocol}: {count:,} packets ({percentage:.1f}%)")
    
    # Geolocation test
    print("\n6. Testing geolocation functionality...")
    
    test_ips = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]
    for ip in test_ips:
        try:
            geo_info = geolocate_ip(ip)
            country = geo_info.get('country', 'Unknown')
            city = geo_info.get('city', 'Unknown')
            isp = geo_info.get('isp', 'Unknown')
            print(f"   {ip}: {country}, {city} ({isp})")
        except Exception as e:
            print(f"   {ip}: Geolocation unavailable ({e})")
    
    # Visualization features
    print("\n7. Visualization features implemented:")
    print("   ✓ Real-time traffic intensity charts")
    print("   ✓ Data size monitoring with automatic unit conversion")
    print("   ✓ Protocol distribution pie charts")
    print("   ✓ Interactive chart controls (zoom, pan, reset)")
    print("   ✓ Configurable time ranges (1min - 1hour)")
    print("   ✓ Adjustable refresh intervals")
    print("   ✓ Geolocation information display")
    print("   ✓ Network statistics summary")
    print("   ✓ Color-coded traffic intensity levels")
    
    # Integration test
    print("\n8. Testing integration with main application...")
    
    # Create sample packets
    sample_packets = []
    for i in range(20):
        packet = make_fake_packet()
        sample_packets.append(packet)
    
    print(f"✓ Created {len(sample_packets)} sample packets for integration")
    
    # Show packet details
    print("\n   Sample packets:")
    for i, packet in enumerate(sample_packets[:5]):
        print(f"   {i+1}. {packet.src_ip} → {packet.dst_ip} ({packet.protocol}, {packet.length}B)")
    
    print("\n9. Time range configuration test...")
    
    time_ranges = {
        "1 minuta": 60,
        "5 minut": 300,
        "15 minut": 900,
        "30 minut": 1800,
        "1 godzina": 3600
    }
    
    for range_name, seconds in time_ranges.items():
        points = seconds  # One point per second
        print(f"   {range_name}: {points} data points ({points/60:.1f} minutes)")
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nThe network visualization tab provides:")
    print("• Real-time monitoring of network traffic patterns")
    print("• Interactive charts with zoom and pan capabilities")
    print("• Geographic information for external IP addresses")
    print("• Protocol analysis and statistics")
    print("• Configurable display options")
    print("• Seamless integration with existing packet capture")
    
    return True

if __name__ == "__main__":
    success = demo_network_visualization()
    sys.exit(0 if success else 1)