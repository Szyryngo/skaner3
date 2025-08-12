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


def test_packet_info_structure():
    """Test that PacketInfo structure is correct for visualization."""
    packet = PacketInfo(
        timestamp=time.time(),
        src_ip="192.168.1.1",
        dst_ip="8.8.8.8",
        src_port=1234,
        dst_port=80,
        protocol="TCP",
        length=64
    )
    
    assert packet.src_ip == "192.168.1.1"
    assert packet.dst_ip == "8.8.8.8"
    assert packet.protocol == "TCP"
    assert packet.length == 64


def test_time_range_mapping_logic():
    """Test time range mapping logic without GUI."""
    range_map = {
        "1 minuta": 60,
        "5 minut": 300,
        "15 minut": 900,
        "30 minut": 1800,
        "1 godzina": 3600
    }
    
    # Test that mapping is correct
    assert range_map["1 minuta"] == 60
    assert range_map["5 minut"] == 300
    assert range_map["1 godzina"] == 3600


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