import pytest
import time
from unittest.mock import Mock, patch
from core.network_scanner import NetworkScanner, ScanMode, HostInfo, ScanProgress


class TestNetworkScanner:
    """Testy dla klasy NetworkScanner."""

    def test_scanner_creation(self):
        """Test tworzenia instancji skanera."""
        scanner = NetworkScanner()
        assert scanner.mode == ScanMode.LIGHT
        assert scanner.timeout == 2.0
        assert scanner.max_threads == 50
        assert not scanner.is_running()
        assert len(scanner.hosts) == 0

    def test_scanner_modes(self):
        """Test różnych trybów skanera."""
        light_scanner = NetworkScanner(mode=ScanMode.LIGHT)
        hard_scanner = NetworkScanner(mode=ScanMode.HARD)
        
        assert light_scanner.mode == ScanMode.LIGHT
        assert hard_scanner.mode == ScanMode.HARD
        assert len(light_scanner.common_ports) < len(hard_scanner.full_ports)

    def test_ip_range_parsing(self):
        """Test parsowania zakresów IP."""
        scanner = NetworkScanner()
        
        # Test pojedynczego IP
        targets = scanner._parse_ip_ranges(["192.168.1.1"])
        assert targets == ["192.168.1.1"]
        
        # Test zakresu IP
        targets = scanner._parse_ip_ranges(["192.168.1.1-192.168.1.3"])
        assert targets == ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
        
        # Test CIDR - małej sieci
        targets = scanner._parse_ip_ranges(["192.168.1.0/30"])
        assert len(targets) == 2  # .1 i .2 (bez network i broadcast)
        assert "192.168.1.1" in targets
        assert "192.168.1.2" in targets

    def test_ip_range_parsing_errors(self):
        """Test obsługi błędów w parsowaniu IP."""
        scanner = NetworkScanner()
        
        # Błędny format IP
        targets = scanner._parse_ip_ranges(["invalid.ip.address"])
        assert targets == []
        
        # Błędny zakres
        targets = scanner._parse_ip_ranges(["192.168.1.10-invalid"])
        assert targets == []

    def test_host_info_structure(self):
        """Test struktury danych HostInfo."""
        host = HostInfo(ip="192.168.1.1")
        assert host.ip == "192.168.1.1"
        assert host.hostname is None
        assert not host.is_alive
        assert host.open_ports == []
        assert host.response_time is None
        assert host.last_seen is not None

    def test_scan_progress_structure(self):
        """Test struktury danych ScanProgress."""
        progress = ScanProgress()
        assert progress.hosts_total == 0
        assert progress.hosts_scanned == 0
        assert progress.ports_total == 0
        assert progress.ports_scanned == 0
        assert progress.hosts_found == 0
        assert progress.open_ports_found == 0
        assert progress.current_target == ""
        assert not progress.is_running
        assert progress.elapsed_time == 0.0
        assert progress.estimated_remaining == 0.0

    def test_callbacks_setup(self):
        """Test ustawiania callbacków."""
        scanner = NetworkScanner()
        
        # Mock callbacki
        on_host_found = Mock()
        on_progress_update = Mock()
        on_scan_complete = Mock()
        on_error = Mock()
        
        scanner.on_host_found = on_host_found
        scanner.on_progress_update = on_progress_update
        scanner.on_scan_complete = on_scan_complete
        scanner.on_error = on_error
        
        assert scanner.on_host_found == on_host_found
        assert scanner.on_progress_update == on_progress_update
        assert scanner.on_scan_complete == on_scan_complete
        assert scanner.on_error == on_error

    def test_simulation_mode(self):
        """Test trybu symulacji."""
        scanner = NetworkScanner(use_simulation=True)
        assert scanner.use_simulation is True

    def test_scan_start_validation(self):
        """Test walidacji przed rozpoczęciem skanowania."""
        scanner = NetworkScanner()
        
        # Pusty zakres IP powinien być obsłużony
        scanner.on_error = Mock()
        scanner.start_scan([])
        
        # Callback błędu powinien być wywołany
        assert scanner.on_error.called

    def test_scanner_stop(self):
        """Test zatrzymywania skanowania."""
        scanner = NetworkScanner(use_simulation=True)
        
        # Uruchom symulowane skanowanie z większym zakresem
        scanner.start_scan(["192.168.1.1-192.168.1.10"])
        
        # Sprawdź czy działa
        time.sleep(0.1)
        assert scanner.is_running()
        
        # Zatrzymaj
        scanner.stop_scan()
        time.sleep(0.1)
        assert not scanner.is_running()

    def test_get_results_methods(self):
        """Test metod pobierania wyników."""
        scanner = NetworkScanner()
        
        # Dodaj przykładowe wyniki
        alive_host = HostInfo(ip="192.168.1.1", is_alive=True)
        alive_host.open_ports = [80, 443]
        
        dead_host = HostInfo(ip="192.168.1.2", is_alive=False)
        
        scanner.hosts = {
            "192.168.1.1": alive_host,
            "192.168.1.2": dead_host
        }
        
        # Test metod
        all_results = scanner.get_results()
        assert len(all_results) == 2
        
        alive_hosts = scanner.get_alive_hosts()
        assert len(alive_hosts) == 1
        assert alive_hosts[0].ip == "192.168.1.1"
        
        hosts_with_ports = scanner.get_hosts_with_open_ports()
        assert len(hosts_with_ports) == 1
        assert hosts_with_ports[0].ip == "192.168.1.1"

    @patch('socket.socket')
    def test_ping_host_socket(self, mock_socket):
        """Test pingowania hosta przez socket."""
        scanner = NetworkScanner(use_simulation=False)
        
        # Mock sukcesu połączenia
        mock_sock_instance = Mock()
        mock_sock_instance.connect_ex.return_value = 0
        mock_socket.return_value = mock_sock_instance
        
        is_alive, response_time = scanner._ping_host_socket("127.0.0.1")
        
        assert is_alive is True
        assert response_time is not None
        assert response_time >= 0

    @patch('socket.socket')
    def test_ping_host_socket_failure(self, mock_socket):
        """Test niepowodzenia pingowania hosta przez socket."""
        scanner = NetworkScanner(use_simulation=False)
        
        # Mock niepowodzenia połączenia
        mock_sock_instance = Mock()
        mock_sock_instance.connect_ex.return_value = 1
        mock_socket.return_value = mock_sock_instance
        
        is_alive, response_time = scanner._ping_host_socket("192.168.1.999")
        
        assert is_alive is False
        assert response_time is None

    @patch('socket.socket')
    def test_scan_port(self, mock_socket):
        """Test skanowania pojedynczego portu."""
        scanner = NetworkScanner(use_simulation=False)
        
        # Mock otwartego portu
        mock_sock_instance = Mock()
        mock_sock_instance.connect_ex.return_value = 0
        mock_socket.return_value = mock_sock_instance
        
        is_open = scanner._scan_port("127.0.0.1", 80)
        assert is_open is True
        
        # Mock zamkniętego portu
        mock_sock_instance.connect_ex.return_value = 1
        is_open = scanner._scan_port("127.0.0.1", 9999)
        assert is_open is False