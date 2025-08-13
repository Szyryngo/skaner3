"""Test system status viewer functionality."""

import unittest
import time
import threading


class TestSystemStatusFunctions(unittest.TestCase):
    
    def test_format_uptime(self):
        """Test uptime formatting functionality - standalone function."""
        
        def format_uptime(uptime_seconds: float) -> str:
            """Format uptime in a human-readable way"""
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        
        # Test minutes only
        self.assertEqual(format_uptime(150), "2m")
        
        # Test hours and minutes
        self.assertEqual(format_uptime(3660), "1h 1m")
        
        # Test days, hours and minutes
        self.assertEqual(format_uptime(90061), "1d 1h 1m")
        
        # Test zero uptime
        self.assertEqual(format_uptime(0), "0m")

    def test_system_data_availability(self):
        """Test that all required system monitoring functions work."""
        try:
            from core.utils import list_network_interfaces
            from core.system_info import get_system_info
            import psutil
            
            # Test network interfaces
            interfaces = list_network_interfaces(show_inactive=True)
            self.assertIsInstance(interfaces, list)
            
            # Test system info
            sys_info = get_system_info()
            self.assertIsInstance(sys_info, dict)
            self.assertIn('cpu_count', sys_info)
            
            # Test CPU percentage
            cpu_pct = psutil.cpu_percent(interval=0.1)
            self.assertIsInstance(cpu_pct, float)
            self.assertGreaterEqual(cpu_pct, 0)
            
            # Test memory
            memory = psutil.virtual_memory()
            self.assertIsInstance(memory.percent, float)
            self.assertGreaterEqual(memory.percent, 0)
            
            # Test uptime calculation
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            self.assertGreater(uptime, 0)
            
            # Test thread count
            thread_count = threading.active_count()
            self.assertIsInstance(thread_count, int)
            self.assertGreater(thread_count, 0)
            
        except Exception as e:
            self.fail(f"System monitoring functions failed: {e}")

    def test_network_interface_data_structure(self):
        """Test network interface data has expected structure."""
        from core.utils import list_network_interfaces
        
        interfaces = list_network_interfaces(show_inactive=True)
        
        if interfaces:  # Only test if we have interfaces
            interface = interfaces[0]
            required_keys = ['name', 'is_up', 'type', 'ipv4']
            
            for key in required_keys:
                self.assertIn(key, interface, f"Interface missing required key: {key}")
            
            # Check data types
            self.assertIsInstance(interface['name'], str)
            self.assertIsInstance(interface['is_up'], bool)
            self.assertIsInstance(interface['type'], str)
            # ipv4 can be empty string or valid IP
            self.assertIsInstance(interface['ipv4'], str)


if __name__ == '__main__':
    unittest.main()