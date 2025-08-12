"""
Moduł zbierający informacje o systemie operacyjnym oraz zasobach sprzętowych.
Wspiera dynamiczne dostosowanie parametrów programu do środowiska uruchomienia.

Funkcje:
    get_system_info() -> dict: Zwraca słownik z danymi o systemie, CPU, pamięci i dysku.

Wymaga pakietu: psutil
"""

import platform
import os

try:
    import psutil
except ImportError:
    psutil = None

def get_detailed_system_info():
    """
    Pobiera informacje o systemie operacyjnym, CPU, pamięci RAM oraz dysku.

    Returns:
        dict: Słownik z kluczami:
            - os (str): Nazwa systemu operacyjnego.
            - os_version (str): Wersja systemu operacyjnego.
            - cpu_count (int): Liczba fizycznych rdzeni CPU.
            - cpu_threads (int): Liczba logicznych wątków CPU.
            - cpu_freq (float): Aktualna częstotliwość CPU (MHz).
            - ram_total (int): Całkowita pamięć RAM (B).
            - ram_available (int): Wolna pamięć RAM (B).
            - disk_total (int): Całkowita powierzchnia dysku (B).
            - disk_free (int): Wolna powierzchnia dysku (B).
    """
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "cpu_count": os.cpu_count(),
        "cpu_threads": os.cpu_count(),
        "cpu_freq": None,
        "ram_total": None,
        "ram_available": None,
        "disk_total": None,
        "disk_free": None,
    }
    if psutil:
        # CPU
        try:
            info["cpu_count"] = psutil.cpu_count(logical=False) or info["cpu_count"]
            info["cpu_threads"] = psutil.cpu_count(logical=True) or info["cpu_threads"]
            freq = psutil.cpu_freq()
            info["cpu_freq"] = freq.current if freq else None
        except Exception:
            pass
        # RAM
        try:
            vm = psutil.virtual_memory()
            info["ram_total"] = vm.total
            info["ram_available"] = vm.available
        except Exception:
            pass
        # Dysk (główny)
        try:
            disk = psutil.disk_usage(os.path.abspath(os.sep))
            info["disk_total"] = disk.total
            info["disk_free"] = disk.free
        except Exception:
            pass
    return info


def get_system_info():
    """Zwraca podstawowe informacje o systemie w formie słownika."""
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    threads = psutil.cpu_count()
    return {
        "CPU (%)": cpu,
        "RAM (%)": ram,
        "Wątki": threads
    }
