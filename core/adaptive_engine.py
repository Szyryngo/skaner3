"""
Moduł adaptacyjnego silnika dostosowującego parametry aplikacji do środowiska uruchomieniowego.
Analizuje dane systemowe i sugeruje optymalne ustawienia dla wydajności aplikacji.

Funkcje:
    AdaptiveEngine.analyze_system() -> dict: Analizuje system i zwraca sugerowane parametry
    AdaptiveEngine.get_recommendations() -> dict: Zwraca rekomendacje z wyjaśnieniami

Wymaga modułu: core.system_info
"""

from __future__ import annotations
import math
from typing import Dict, Any, Optional

from .system_info import get_system_info


class AdaptiveEngine:
    """
    Silnik analizujący parametry systemowe i sugerujący optymalne ustawienia aplikacji.
    
    Analizuje dane o CPU, pamięci RAM i dysku aby dynamicznie dobrać:
    - Liczbę wątków roboczych
    - Wielkość buforów
    - Maksymalny rozmiar logów
    - Inne parametry wydajnościowe
    """
    
    def __init__(self, 
                 conservative_mode: bool = False,
                 min_threads: int = 1,
                 max_threads: int = 32,
                 min_buffer_mb: int = 1,
                 max_buffer_mb: int = 512,
                 min_log_mb: int = 10,
                 max_log_mb: int = 1024):
        """
        Inicjalizuje adaptacyjny silnik z parametrami ograniczającymi.
        
        Args:
            conservative_mode: Czy używać zachowawczych ustawień (mniej agresywne wykorzystanie zasobów)
            min_threads: Minimalna liczba wątków
            max_threads: Maksymalna liczba wątków  
            min_buffer_mb: Minimalny rozmiar bufora w MB
            max_buffer_mb: Maksymalny rozmiar bufora w MB
            min_log_mb: Minimalny rozmiar logów w MB
            max_log_mb: Maksymalny rozmiar logów w MB
        """
        self.conservative_mode = conservative_mode
        self.min_threads = min_threads
        self.max_threads = max_threads
        self.min_buffer_mb = min_buffer_mb
        self.max_buffer_mb = max_buffer_mb
        self.min_log_mb = min_log_mb
        self.max_log_mb = max_log_mb
        self._last_system_info: Optional[Dict[str, Any]] = None
        self._last_recommendations: Optional[Dict[str, Any]] = None
    
    def _bytes_to_mb(self, bytes_value: Optional[int]) -> Optional[float]:
        """Konwertuje bajty na megabajty."""
        if bytes_value is None:
            return None
        return bytes_value / (1024 * 1024)
    
    def _bytes_to_gb(self, bytes_value: Optional[int]) -> Optional[float]:
        """Konwertuje bajty na gigabajty."""
        if bytes_value is None:
            return None
        return bytes_value / (1024 * 1024 * 1024)
    
    def _calculate_optimal_threads(self, cpu_cores: int, cpu_threads: int) -> int:
        """
        Oblicza optymalną liczbę wątków roboczych na podstawie parametrów CPU.
        
        Args:
            cpu_cores: Liczba fizycznych rdzeni CPU
            cpu_threads: Liczba logicznych wątków CPU
            
        Returns:
            Optymalna liczba wątków roboczych
        """
        if self.conservative_mode:
            # W trybie zachowawczym używamy 75% dostępnych rdzeni
            optimal = max(1, int(cpu_cores * 0.75))
        else:
            # W trybie normalnym używamy liczbę równą liczbie logicznych wątków
            # ale nie więcej niż 1.5x liczby fizycznych rdzeni
            optimal = min(cpu_threads, int(cpu_cores * 1.5))
        
        return max(self.min_threads, min(self.max_threads, optimal))
    
    def _calculate_buffer_size(self, available_ram_gb: float) -> int:
        """
        Oblicza optymalny rozmiar bufora na podstawie dostępnej pamięci RAM.
        
        Args:
            available_ram_gb: Dostępna pamięć RAM w GB
            
        Returns:
            Rozmiar bufora w MB
        """
        if self.conservative_mode:
            # W trybie zachowawczym używamy max 5% dostępnej pamięci
            buffer_mb = max(1, int(available_ram_gb * 1024 * 0.05))
        else:
            # W trybie normalnym używamy 10-15% dostępnej pamięci
            if available_ram_gb > 8:
                # Dla systemów z dużą pamięcią używamy 10%
                buffer_mb = int(available_ram_gb * 1024 * 0.1)
            else:
                # Dla systemów z małą pamięcią używamy 15%
                buffer_mb = int(available_ram_gb * 1024 * 0.15)
        
        return max(self.min_buffer_mb, min(self.max_buffer_mb, buffer_mb))
    
    def _calculate_max_log_size(self, free_disk_gb: float) -> int:
        """
        Oblicza maksymalny rozmiar logów na podstawie dostępnego miejsca na dysku.
        
        Args:
            free_disk_gb: Dostępne miejsce na dysku w GB
            
        Returns:
            Maksymalny rozmiar logów w MB
        """
        if self.conservative_mode:
            # W trybie zachowawczym używamy max 1% wolnego miejsca
            log_mb = max(10, int(free_disk_gb * 1024 * 0.01))
        else:
            # W trybie normalnym dostosowujemy do ilości wolnego miejsca
            if free_disk_gb > 50:
                # Dużo miejsca - używamy max 2%
                log_mb = int(free_disk_gb * 1024 * 0.02)
            elif free_disk_gb > 10:
                # Średnio miejsca - używamy 1.5%
                log_mb = int(free_disk_gb * 1024 * 0.015)
            else:
                # Mało miejsca - używamy 1%
                log_mb = int(free_disk_gb * 1024 * 0.01)
        
        return max(self.min_log_mb, min(self.max_log_mb, log_mb))
    
    def _determine_performance_profile(self, system_info: Dict[str, Any]) -> str:
        """
        Określa profil wydajnościowy systemu na podstawie jego parametrów.
        
        Args:
            system_info: Informacje o systemie z get_system_info()
            
        Returns:
            Profil wydajnościowy: 'high_performance', 'balanced', 'low_resource'
        """
        cpu_threads = system_info.get('cpu_threads', 1)
        ram_gb = self._bytes_to_gb(system_info.get('ram_total', 0)) or 0
        
        # Kryteria dla profili wydajnościowych
        if cpu_threads >= 8 and ram_gb >= 16:
            return 'high_performance'
        elif cpu_threads >= 4 and ram_gb >= 8:
            return 'balanced'
        else:
            return 'low_resource'
    
    def analyze_system(self) -> Dict[str, Any]:
        """
        Analizuje system i zwraca sugerowane parametry konfiguracyjne.
        
        Returns:
            Słownik z kluczami:
                - optimal_threads: Optymalna liczba wątków roboczych
                - buffer_size_mb: Rozmiar bufora w MB
                - max_log_size_mb: Maksymalny rozmiar logów w MB
                - performance_profile: Profil wydajnościowy systemu
                - system_analysis: Analiza systemu
                - recommendations: Szczegółowe rekomendacje
        """
        # Pobierz aktualne informacje o systemie
        system_info = get_system_info()
        self._last_system_info = system_info
        
        # Podstawowe parametry systemowe
        cpu_cores = system_info.get('cpu_count', 1)
        cpu_threads = system_info.get('cpu_threads', 1)
        ram_total_gb = self._bytes_to_gb(system_info.get('ram_total', 0)) or 0
        ram_available_gb = self._bytes_to_gb(system_info.get('ram_available', 0)) or 0
        disk_free_gb = self._bytes_to_gb(system_info.get('disk_free', 0)) or 0
        cpu_freq = system_info.get('cpu_freq', 0)
        
        # Oblicz optymalne parametry
        optimal_threads = self._calculate_optimal_threads(cpu_cores, cpu_threads)
        buffer_size_mb = self._calculate_buffer_size(ram_available_gb)
        max_log_size_mb = self._calculate_max_log_size(disk_free_gb)
        performance_profile = self._determine_performance_profile(system_info)
        
        # Dodatkowe parametry na podstawie profilu wydajnościowego
        if performance_profile == 'high_performance':
            packet_buffer_multiplier = 2.0
            processing_batch_size = 1000
            ui_update_interval_ms = 250
        elif performance_profile == 'balanced':
            packet_buffer_multiplier = 1.5
            processing_batch_size = 500
            ui_update_interval_ms = 500
        else:  # low_resource
            packet_buffer_multiplier = 1.0
            processing_batch_size = 100
            ui_update_interval_ms = 1000
        
        packet_buffer_size = int(buffer_size_mb * packet_buffer_multiplier)
        
        # Przygotuj wyniki analizy
        results = {
            'optimal_threads': optimal_threads,
            'buffer_size_mb': buffer_size_mb,
            'packet_buffer_size': packet_buffer_size,
            'max_log_size_mb': max_log_size_mb,
            'processing_batch_size': processing_batch_size,
            'ui_update_interval_ms': ui_update_interval_ms,
            'performance_profile': performance_profile,
            'system_analysis': {
                'cpu_cores': cpu_cores,
                'cpu_threads': cpu_threads,
                'cpu_frequency_mhz': round(cpu_freq, 1) if cpu_freq else None,
                'ram_total_gb': round(ram_total_gb, 1),
                'ram_available_gb': round(ram_available_gb, 1),
                'ram_usage_percent': round((1 - ram_available_gb / ram_total_gb) * 100, 1) if ram_total_gb > 0 else 0,
                'disk_free_gb': round(disk_free_gb, 1),
                'os': system_info.get('os', 'Unknown'),
                'conservative_mode': self.conservative_mode
            },
            'recommendations': self._generate_recommendations(system_info, {
                'optimal_threads': optimal_threads,
                'buffer_size_mb': buffer_size_mb,
                'max_log_size_mb': max_log_size_mb,
                'performance_profile': performance_profile
            })
        }
        
        self._last_recommendations = results
        return results
    
    def _generate_recommendations(self, system_info: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, str]:
        """
        Generuje szczegółowe rekomendacje na podstawie analizy systemu.
        
        Args:
            system_info: Informacje o systemie
            params: Obliczone parametry
            
        Returns:
            Słownik z rekomendacjami
        """
        recommendations = {}
        
        # Rekomendacje dotyczące wątków
        cpu_threads = system_info.get('cpu_threads', 1)
        optimal_threads = params['optimal_threads']
        
        if optimal_threads == cpu_threads:
            recommendations['threads'] = f"Wykryto {cpu_threads} wątków CPU. Używam wszystkich dostępnych wątków dla maksymalnej wydajności."
        elif optimal_threads < cpu_threads:
            recommendations['threads'] = f"Wykryto {cpu_threads} wątków CPU, ale sugeruję {optimal_threads} dla stabilności i zostawienia zasobów dla systemu."
        else:
            recommendations['threads'] = f"Wykryto {cpu_threads} wątków CPU. Używam optymalnej liczby: {optimal_threads}."
        
        # Rekomendacje dotyczące pamięci
        ram_available_gb = self._bytes_to_gb(system_info.get('ram_available', 0)) or 0
        buffer_size_mb = params['buffer_size_mb']
        buffer_percent = (buffer_size_mb / 1024 / ram_available_gb) * 100 if ram_available_gb > 0 else 0
        
        recommendations['memory'] = f"Dostępne {ram_available_gb:.1f} GB RAM. Bufor {buffer_size_mb} MB ({buffer_percent:.1f}% dostępnej pamięci) zapewni optymalną wydajność bez wpływu na stabilność systemu."
        
        # Rekomendacje dotyczące dysku
        disk_free_gb = self._bytes_to_gb(system_info.get('disk_free', 0)) or 0
        max_log_mb = params['max_log_size_mb']
        log_percent = (max_log_mb / 1024 / disk_free_gb) * 100 if disk_free_gb > 0 else 0
        
        recommendations['storage'] = f"Dostępne {disk_free_gb:.1f} GB na dysku. Maksymalny rozmiar logów {max_log_mb} MB ({log_percent:.1f}% wolnego miejsca) pozwoli na długoterminowe działanie bez wypełnienia dysku."
        
        # Rekomendacje ogólne
        profile = params['performance_profile']
        if profile == 'high_performance':
            recommendations['general'] = "System ma wysoką wydajność. Możesz używać agresywnych ustawień dla maksymalnej przepustowości."
        elif profile == 'balanced':
            recommendations['general'] = "System ma zrównoważone parametry. Ustawienia zapewniają dobrą wydajność przy stabilności."
        else:
            recommendations['general'] = "System ma ograniczone zasoby. Ustawienia są zoptymalizowane pod kątem niskiego zużycia zasobów."
        
        return recommendations
    
    def get_system_info(self) -> Optional[Dict[str, Any]]:
        """
        Zwraca ostatnie pobrane informacje o systemie.
        
        Returns:
            Słownik z informacjami o systemie lub None jeśli nie wykonano jeszcze analizy
        """
        return self._last_system_info
    
    def get_recommendations(self) -> Optional[Dict[str, Any]]:
        """
        Zwraca ostatnie rekomendacje lub None jeśli nie wykonano jeszcze analizy.
        
        Returns:
            Słownik z rekomendacjami lub None
        """
        return self._last_recommendations
    
    def update_constraints(self, **kwargs) -> None:
        """
        Aktualizuje ograniczenia silnika adaptacyjnego.
        
        Args:
            **kwargs: Parametry do aktualizacji (conservative_mode, min_threads, max_threads, etc.)
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)