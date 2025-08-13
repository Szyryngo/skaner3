"""
Moduł zbierający informacje o systemie operacyjnym oraz zasobach sprzętowych.
Wspiera dynamiczne dostosowanie parametrów programu do środowiska uruchomienia.

Funkcje:
    get_system_info() -> dict: Zwraca słownik z danymi o systemie, CPU, pamięci i dysku.
    get_system_status() -> dict: Zwraca status systemu dla GUI (CPU, RAM, interfejsy, uptime).

Wymaga pakietów: psutil, platform, socket
"""

import platform
import os
import socket
import time
from datetime import datetime, timedelta

try:
    import psutil
except ImportError:
    psutil = None

def get_system_info():
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


def get_system_status():
    """
    Pobiera aktualny status systemu dla prezentacji w GUI.
    
    Returns:
        dict: Słownik z kluczami:
            - cpu_percent (float): Aktualne obciążenie CPU (%).
            - ram_percent (float): Aktualne obciążenie RAM (%).
            - ram_used (int): Użyta pamięć RAM (B).
            - ram_total (int): Całkowita pamięć RAM (B).
            - thread_count (int): Liczba uruchomionych wątków w systemie.
            - uptime (str): Czas działania systemu (format: "X dni, Y godzin").
            - network_interfaces (list): Lista interfejsów sieciowych, każdy jako dict z:
                - name (str): Nazwa interfejsu.
                - status (str): Status ("aktywny", "nieaktywny", "nieznany").
                - type (str): Typ interfejsu ("ethernet", "wifi", "loopback", "inne").
                - ipv4 (str): Adres IPv4 lub "brak".
    """
    status = {
        "cpu_percent": 0.0,
        "ram_percent": 0.0,
        "ram_used": 0,
        "ram_total": 0,
        "thread_count": 0,
        "uptime": "nieznany",
        "network_interfaces": []
    }
    
    if not psutil:
        return status
    
    try:
        # CPU
        status["cpu_percent"] = psutil.cpu_percent(interval=None)
    except Exception:
        pass
    
    try:
        # RAM
        vm = psutil.virtual_memory()
        status["ram_percent"] = vm.percent
        status["ram_used"] = vm.used
        status["ram_total"] = vm.total
    except Exception:
        pass
    
    try:
        # Liczba wątków w systemie
        total_threads = 0
        for proc in psutil.process_iter(['num_threads']):
            try:
                total_threads += proc.info['num_threads'] or 0
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        status["thread_count"] = total_threads
    except Exception:
        pass
    
    try:
        # Uptime systemu
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime_delta = timedelta(seconds=int(uptime_seconds))
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            status["uptime"] = f"{days} dni, {hours} godzin"
        elif hours > 0:
            status["uptime"] = f"{hours} godzin, {minutes} minut"
        else:
            status["uptime"] = f"{minutes} minut"
    except Exception:
        pass
    
    try:
        # Interfejsy sieciowe
        interfaces = []
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()
        
        for if_name in net_if_addrs:
            interface_info = {
                "name": if_name,
                "status": "nieznany",
                "type": "inne",
                "ipv4": "brak"
            }
            
            # Status interfejsu
            try:
                if if_name in net_if_stats:
                    stats = net_if_stats[if_name]
                    interface_info["status"] = "aktywny" if stats.isup else "nieaktywny"
            except Exception:
                pass
            
            # Typ interfejsu (na podstawie nazwy)
            if_name_lower = if_name.lower()
            if if_name_lower.startswith(('lo', 'loopback')):
                interface_info["type"] = "loopback"
            elif if_name_lower.startswith(('eth', 'en', 'em')):
                interface_info["type"] = "ethernet"
            elif if_name_lower.startswith(('wlan', 'wifi', 'wl')):
                interface_info["type"] = "wifi"
            
            # Adres IPv4
            try:
                for addr in net_if_addrs[if_name]:
                    if addr.family == socket.AF_INET:  # IPv4
                        interface_info["ipv4"] = addr.address
                        break
            except Exception:
                pass
            
            interfaces.append(interface_info)
        
        # Sortuj interfejsy: loopback na końcu, reszta alfabetycznie
        interfaces.sort(key=lambda x: (x["type"] == "loopback", x["name"]))
        status["network_interfaces"] = interfaces
        
    except Exception:
        pass
    
    return status
