import unittest
import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.system_info import get_system_status


class TestSystemStatus(unittest.TestCase):
    """Test case dla funkcjonalności statusu systemu."""
    
    def test_get_system_status_returns_dict(self):
        """Test sprawdza czy get_system_status zwraca słownik."""
        status = get_system_status()
        self.assertIsInstance(status, dict)
    
    def test_get_system_status_has_required_keys(self):
        """Test sprawdza czy wynik zawiera wszystkie wymagane klucze."""
        status = get_system_status()
        required_keys = [
            "cpu_percent",
            "ram_percent", 
            "ram_used",
            "ram_total",
            "thread_count",
            "uptime",
            "network_interfaces"
        ]
        
        for key in required_keys:
            self.assertIn(key, status, f"Missing key: {key}")
    
    def test_cpu_percent_is_numeric(self):
        """Test sprawdza czy cpu_percent jest liczbą."""
        status = get_system_status()
        cpu_percent = status["cpu_percent"]
        self.assertIsInstance(cpu_percent, (int, float))
        self.assertGreaterEqual(cpu_percent, 0.0)
        self.assertLessEqual(cpu_percent, 100.0)
    
    def test_ram_values_are_valid(self):
        """Test sprawdza czy wartości RAM są poprawne."""
        status = get_system_status()
        ram_percent = status["ram_percent"]
        ram_used = status["ram_used"]
        ram_total = status["ram_total"]
        
        self.assertIsInstance(ram_percent, (int, float))
        self.assertGreaterEqual(ram_percent, 0.0)
        self.assertLessEqual(ram_percent, 100.0)
        
        self.assertIsInstance(ram_used, int)
        self.assertGreaterEqual(ram_used, 0)
        
        self.assertIsInstance(ram_total, int)
        self.assertGreaterEqual(ram_total, 0)
        
        # ram_used nie powinno być większe niż ram_total
        if ram_total > 0:
            self.assertLessEqual(ram_used, ram_total)
    
    def test_thread_count_is_positive_integer(self):
        """Test sprawdza czy liczba wątków jest dodatnią liczbą całkowitą."""
        status = get_system_status()
        thread_count = status["thread_count"]
        self.assertIsInstance(thread_count, int)
        self.assertGreaterEqual(thread_count, 0)
    
    def test_uptime_is_string(self):
        """Test sprawdza czy uptime jest stringiem."""
        status = get_system_status()
        uptime = status["uptime"]
        self.assertIsInstance(uptime, str)
        self.assertGreater(len(uptime), 0)
    
    def test_network_interfaces_structure(self):
        """Test sprawdza strukturę danych interfejsów sieciowych."""
        status = get_system_status()
        interfaces = status["network_interfaces"]
        self.assertIsInstance(interfaces, list)
        
        for interface in interfaces:
            self.assertIsInstance(interface, dict)
            required_interface_keys = ["name", "status", "type", "ipv4"]
            for key in required_interface_keys:
                self.assertIn(key, interface, f"Missing interface key: {key}")
                self.assertIsInstance(interface[key], str)
            
            # Sprawdź czy status ma poprawne wartości
            self.assertIn(interface["status"], ["aktywny", "nieaktywny", "nieznany"])
            
            # Sprawdź czy typ ma poprawne wartości
            self.assertIn(interface["type"], ["ethernet", "wifi", "loopback", "inne"])


if __name__ == '__main__':
    unittest.main()