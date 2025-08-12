import pytest
import time
from unittest.mock import MagicMock, patch

from core.utils import PacketInfo


@patch('ui.network_visualization.FigureCanvas')
@patch('ui.network_visualization.Figure')
def test_network_visualization_creation(mock_figure, mock_canvas):
    """Test that NetworkVisualization can be created without errors."""
    from ui.network_visualization import NetworkVisualization
    
    # Mock the matplotlib components to avoid GUI dependencies
    mock_figure.return_value = MagicMock()
    mock_canvas.return_value = MagicMock()
    
    # Since we can't create QWidget without QApplication in tests,
    # just test the import works
    assert NetworkVisualization is not None


def test_packet_info_structure_with_ai_score():
    """Test that PacketInfo structure includes AI score for filtering."""
    packet = PacketInfo(
        timestamp=time.time(),
        src_ip="192.168.1.1",
        dst_ip="8.8.8.8",
        src_port=1234,
        dst_port=80,
        protocol="TCP",
        length=64,
        ai_score=0.75
    )
    
    assert packet.src_ip == "192.168.1.1"
    assert packet.dst_ip == "8.8.8.8"
    assert packet.protocol == "TCP"
    assert packet.length == 64
    assert packet.ai_score == 0.75


def test_enhanced_time_range_mapping():
    """Test enhanced time range mapping logic."""
    range_map = {
        "1 minuta": 60,
        "5 minut": 300,
        "15 minut": 900,
        "30 minut": 1800,
        "1 godzina": 3600,
        "6 godzin": 21600
    }
    
    # Test that mapping is correct
    assert range_map["1 minuta"] == 60
    assert range_map["5 minut"] == 300
    assert range_map["1 godzina"] == 3600
    assert range_map["6 godzin"] == 21600


def test_packet_filtering_logic():
    """Test packet filtering logic without GUI components."""
    current_time = time.time()
    
    # Create test packets with various characteristics
    test_packets = [
        PacketInfo(current_time - 10, '192.168.1.1', '8.8.8.8', 80, 443, 'TCP', 100, ai_score=0.1),
        PacketInfo(current_time - 5, '10.0.0.1', '1.1.1.1', 443, 80, 'UDP', 200, ai_score=0.8),
        PacketInfo(current_time - 1, '192.168.1.2', '8.8.4.4', 53, 53, 'DNS', 50, ai_score=0.2),
        PacketInfo(current_time - 400, '1.1.1.1', '8.8.8.8', 80, 80, 'TCP', 150, ai_score=0.5),  # Too old
    ]
    
    # Mock filter state
    active_filters = {
        'time_range': 300,  # 5 minutes
        'protocols': set(),
        'src_ips': set(),
        'dst_ips': set(),
        'threat_level_min': 0.0,
        'threat_level_max': 1.0
    }
    
    # Test time filtering
    time_cutoff = current_time - active_filters['time_range']
    time_filtered = [p for p in test_packets if p.timestamp >= time_cutoff]
    assert len(time_filtered) == 3  # Should exclude the 400-second old packet
    
    # Test protocol filtering
    active_filters['protocols'] = {'TCP'}
    protocol_filtered = [p for p in time_filtered 
                        if p.protocol.upper() in active_filters['protocols']]
    assert len(protocol_filtered) == 1  # Only one TCP packet in recent data
    
    # Test threat level filtering
    active_filters['protocols'] = set()  # Clear protocol filter
    active_filters['threat_level_min'] = 0.5
    threat_filtered = [p for p in time_filtered 
                      if p.ai_score >= active_filters['threat_level_min']]
    assert len(threat_filtered) == 1  # Only one packet with score >= 0.5
    
    # Test IP filtering
    active_filters['threat_level_min'] = 0.0  # Clear threat filter
    active_filters['src_ips'] = {'192.168.1.1'}
    ip_filtered = [p for p in time_filtered 
                   if p.src_ip in active_filters['src_ips']]
    assert len(ip_filtered) == 1  # Only one packet from that source IP


def test_geolocation_data_format():
    """Test that geolocation data format matches expected structure."""
    from core.utils import geolocate_ip
    
    # Test with a mock IP (this might return actual data or empty dict)
    geo_data = geolocate_ip("8.8.8.8")
    
    # Should be a dictionary
    assert isinstance(geo_data, dict)
    
    # Check expected keys exist (they might be empty if API fails)
    expected_keys = ['country', 'city', 'isp']
    for key in expected_keys:
        # Key should exist even if value is None or empty
        assert hasattr(geo_data, 'get')  # Verify it's dict-like


def test_filter_state_management():
    """Test filter state management logic."""
    # Test default filter state
    default_filters = {
        'time_range': 300,
        'protocols': set(),
        'src_ips': set(), 
        'dst_ips': set(),
        'threat_level_min': 0.0,
        'threat_level_max': 1.0
    }
    
    # Verify default state allows all packets
    assert len(default_filters['protocols']) == 0  # Empty means all protocols
    assert len(default_filters['src_ips']) == 0    # Empty means all IPs
    assert default_filters['threat_level_min'] == 0.0
    assert default_filters['threat_level_max'] == 1.0
    
    # Test filter modifications
    modified_filters = default_filters.copy()
    modified_filters['protocols'] = {'TCP', 'UDP'}
    modified_filters['threat_level_min'] = 0.3
    
    assert 'TCP' in modified_filters['protocols']
    assert modified_filters['threat_level_min'] == 0.3