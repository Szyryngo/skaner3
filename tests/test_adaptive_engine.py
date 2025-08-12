import unittest
from unittest.mock import patch, MagicMock

from core.adaptive_engine import AdaptiveEngine


class TestAdaptiveEngine(unittest.TestCase):
    
    def setUp(self):
        """Przygotowanie do testów."""
        self.engine = AdaptiveEngine()
        self.conservative_engine = AdaptiveEngine(conservative_mode=True)
    
    def test_init_default_parameters(self):
        """Test domyślnych parametrów inicjalizacji."""
        engine = AdaptiveEngine()
        self.assertFalse(engine.conservative_mode)
        self.assertEqual(engine.min_threads, 1)
        self.assertEqual(engine.max_threads, 32)
        self.assertEqual(engine.min_buffer_mb, 1)
        self.assertEqual(engine.max_buffer_mb, 512)
    
    def test_init_custom_parameters(self):
        """Test niestandardowych parametrów inicjalizacji."""
        engine = AdaptiveEngine(
            conservative_mode=True,
            min_threads=2,
            max_threads=16,
            min_buffer_mb=10,
            max_buffer_mb=256
        )
        self.assertTrue(engine.conservative_mode)
        self.assertEqual(engine.min_threads, 2)
        self.assertEqual(engine.max_threads, 16)
        self.assertEqual(engine.min_buffer_mb, 10)
        self.assertEqual(engine.max_buffer_mb, 256)
    
    def test_bytes_to_mb_conversion(self):
        """Test konwersji bajtów na megabajty."""
        # Test prawidłowej konwersji
        result = self.engine._bytes_to_mb(1024 * 1024 * 100)  # 100 MB
        self.assertEqual(result, 100.0)
        
        # Test None
        result = self.engine._bytes_to_mb(None)
        self.assertIsNone(result)
        
        # Test 0
        result = self.engine._bytes_to_mb(0)
        self.assertEqual(result, 0.0)
    
    def test_bytes_to_gb_conversion(self):
        """Test konwersji bajtów na gigabajty."""
        # Test prawidłowej konwersji
        result = self.engine._bytes_to_gb(1024 * 1024 * 1024 * 2)  # 2 GB
        self.assertEqual(result, 2.0)
        
        # Test None
        result = self.engine._bytes_to_gb(None)
        self.assertIsNone(result)
    
    def test_calculate_optimal_threads(self):
        """Test obliczania optymalnej liczby wątków."""
        # Normal mode
        normal_engine = AdaptiveEngine(conservative_mode=False)
        
        # Test z 4 rdzeniami fizycznymi, 8 wątkami logicznymi
        result = normal_engine._calculate_optimal_threads(4, 8)
        self.assertEqual(result, 6)  # min(8, 4*1.5)
        
        # Test z 2 rdzeniami fizycznymi, 4 wątkami logicznymi  
        result = normal_engine._calculate_optimal_threads(2, 4)
        self.assertEqual(result, 3)  # min(4, 2*1.5)
        
        # Conservative mode
        conservative_engine = AdaptiveEngine(conservative_mode=True)
        result = conservative_engine._calculate_optimal_threads(4, 8)
        self.assertEqual(result, 3)  # max(1, 4*0.75)
    
    def test_calculate_optimal_threads_with_constraints(self):
        """Test obliczania optymalnej liczby wątków z ograniczeniami."""
        # Test z niskim maksimum
        engine = AdaptiveEngine(max_threads=2)
        result = engine._calculate_optimal_threads(4, 8)
        self.assertEqual(result, 2)  # Ograniczone przez max_threads
        
        # Test z wysokim minimum
        engine = AdaptiveEngine(min_threads=10)
        result = engine._calculate_optimal_threads(2, 4)
        self.assertEqual(result, 10)  # Ograniczone przez min_threads
    
    def test_calculate_buffer_size(self):
        """Test obliczania rozmiaru bufora."""
        # Normal mode z dużą ilością pamięci (ale ograniczone maksimum)
        normal_engine = AdaptiveEngine(conservative_mode=False, max_buffer_mb=2048)
        result = normal_engine._calculate_buffer_size(16.0)  # 16 GB
        expected = min(int(16 * 1024 * 0.1), 2048)  # 10% z 16 GB, max 2048
        self.assertEqual(result, expected)
        
        # Normal mode z małą ilością pamięci
        result = normal_engine._calculate_buffer_size(4.0)  # 4 GB
        expected = int(4 * 1024 * 0.15)  # 15% z 4 GB
        self.assertEqual(result, expected)
        
        # Conservative mode
        conservative_engine = AdaptiveEngine(conservative_mode=True, max_buffer_mb=2048)
        result = conservative_engine._calculate_buffer_size(16.0)
        expected = int(16 * 1024 * 0.05)  # 5% z 16 GB
        self.assertEqual(result, expected)
    
    def test_calculate_buffer_size_with_constraints(self):
        """Test obliczania rozmiaru bufora z ograniczeniami."""
        # Test z niskim maksimum
        engine = AdaptiveEngine(max_buffer_mb=100)
        result = engine._calculate_buffer_size(16.0)  # Duża pamięć
        self.assertEqual(result, 100)  # Ograniczone przez max_buffer_mb
        
        # Test z wysokim minimum
        engine = AdaptiveEngine(min_buffer_mb=500)
        result = engine._calculate_buffer_size(1.0)  # Mała pamięć
        self.assertEqual(result, 500)  # Ograniczone przez min_buffer_mb
    
    def test_calculate_max_log_size(self):
        """Test obliczania maksymalnego rozmiaru logów."""
        # Normal mode z dużą ilością miejsca (ale ograniczone maksimum)
        normal_engine = AdaptiveEngine(conservative_mode=False, max_log_mb=3000)
        result = normal_engine._calculate_max_log_size(100.0)  # 100 GB
        expected = min(int(100 * 1024 * 0.02), 3000)  # 2% ze 100 GB, max 3000
        self.assertEqual(result, expected)
        
        # Normal mode ze średnią ilością miejsca
        result = normal_engine._calculate_max_log_size(20.0)  # 20 GB
        expected = int(20 * 1024 * 0.015)  # 1.5% z 20 GB
        self.assertEqual(result, expected)
        
        # Normal mode z małą ilością miejsca
        result = normal_engine._calculate_max_log_size(5.0)  # 5 GB
        expected = int(5 * 1024 * 0.01)  # 1% z 5 GB
        self.assertEqual(result, expected)
        
        # Conservative mode
        conservative_engine = AdaptiveEngine(conservative_mode=True, max_log_mb=3000)
        result = conservative_engine._calculate_max_log_size(100.0)
        expected = int(100 * 1024 * 0.01)  # 1% ze 100 GB
        self.assertEqual(result, expected)
    
    def test_determine_performance_profile(self):
        """Test określania profilu wydajnościowego."""
        # High performance
        system_info = {'cpu_threads': 16, 'ram_total': 32 * 1024 * 1024 * 1024}  # 32 GB
        result = self.engine._determine_performance_profile(system_info)
        self.assertEqual(result, 'high_performance')
        
        # Balanced
        system_info = {'cpu_threads': 4, 'ram_total': 8 * 1024 * 1024 * 1024}  # 8 GB
        result = self.engine._determine_performance_profile(system_info)
        self.assertEqual(result, 'balanced')
        
        # Low resource
        system_info = {'cpu_threads': 2, 'ram_total': 4 * 1024 * 1024 * 1024}  # 4 GB
        result = self.engine._determine_performance_profile(system_info)
        self.assertEqual(result, 'low_resource')
    
    @patch('core.adaptive_engine.get_system_info')
    def test_analyze_system(self, mock_get_system_info):
        """Test głównej funkcji analizy systemu."""
        # Mock danych systemowych
        mock_system_info = {
            'os': 'Linux',
            'os_version': 'Ubuntu 20.04',
            'cpu_count': 4,
            'cpu_threads': 8,
            'cpu_freq': 3000.0,
            'ram_total': 16 * 1024 * 1024 * 1024,  # 16 GB
            'ram_available': 12 * 1024 * 1024 * 1024,  # 12 GB
            'disk_total': 500 * 1024 * 1024 * 1024,  # 500 GB
            'disk_free': 200 * 1024 * 1024 * 1024,  # 200 GB
        }
        mock_get_system_info.return_value = mock_system_info
        
        # Wykonaj analizę
        results = self.engine.analyze_system()
        
        # Sprawdź strukturę wyników
        self.assertIn('optimal_threads', results)
        self.assertIn('buffer_size_mb', results)
        self.assertIn('packet_buffer_size', results)
        self.assertIn('max_log_size_mb', results)
        self.assertIn('processing_batch_size', results)
        self.assertIn('ui_update_interval_ms', results)
        self.assertIn('performance_profile', results)
        self.assertIn('system_analysis', results)
        self.assertIn('recommendations', results)
        
        # Sprawdź typy wartości
        self.assertIsInstance(results['optimal_threads'], int)
        self.assertIsInstance(results['buffer_size_mb'], int)
        self.assertIsInstance(results['packet_buffer_size'], int)
        self.assertIsInstance(results['max_log_size_mb'], int)
        self.assertIsInstance(results['processing_batch_size'], int)
        self.assertIsInstance(results['ui_update_interval_ms'], int)
        self.assertIsInstance(results['performance_profile'], str)
        self.assertIsInstance(results['system_analysis'], dict)
        self.assertIsInstance(results['recommendations'], dict)
        
        # Sprawdź wartości w przedziale ograniczeń
        self.assertGreaterEqual(results['optimal_threads'], self.engine.min_threads)
        self.assertLessEqual(results['optimal_threads'], self.engine.max_threads)
        self.assertGreaterEqual(results['buffer_size_mb'], self.engine.min_buffer_mb)
        self.assertLessEqual(results['buffer_size_mb'], self.engine.max_buffer_mb)
        
        # Sprawdź że zachowało informacje systemowe
        self.assertEqual(self.engine.get_system_info(), mock_system_info)
        self.assertEqual(self.engine.get_recommendations(), results)
    
    def test_update_constraints(self):
        """Test aktualizacji ograniczeń."""
        engine = AdaptiveEngine()
        
        # Aktualizuj ograniczenia
        engine.update_constraints(
            conservative_mode=True,
            max_threads=16,
            min_buffer_mb=20
        )
        
        # Sprawdź czy zostały zaktualizowane
        self.assertTrue(engine.conservative_mode)
        self.assertEqual(engine.max_threads, 16)
        self.assertEqual(engine.min_buffer_mb, 20)
        
        # Sprawdź że inne parametry nie zostały zmienione
        self.assertEqual(engine.min_threads, 1)  # Nie został zmieniony
    
    def test_get_system_info_before_analysis(self):
        """Test pobierania informacji o systemie przed analizą."""
        engine = AdaptiveEngine()
        self.assertIsNone(engine.get_system_info())
        self.assertIsNone(engine.get_recommendations())


if __name__ == "__main__":
    unittest.main()