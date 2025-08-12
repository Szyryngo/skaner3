"""
Moduł zbierający informacje o systemie operacyjnym oraz zasobach sprzętowych.
Wspiera dynamiczne dostosowanie parametrów programu do środowiska uruchomienia.

Funkcje:
    get_system_info() -> dict: Zwraca słownik z danymi o systemie, CPU, pamięci i dysku.
    get_realtime_system_info() -> dict: Zwraca aktualne dane systemowe w czasie rzeczywistym.
    get_network_info() -> dict: Zwraca informacje o interfejsach sieciowych.

Wymaga pakietu: psutil
"""

import platform
import os
import time
from typing import Dict, List, Any, Optional

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


def get_realtime_system_info() -> Dict[str, Any]:
    """
    Pobiera aktualne informacje o systemie w czasie rzeczywistym.
    
    Returns:
        dict: Słownik z aktualnymi metrykami systemu.
    """
    info = {
        "timestamp": time.time(),
        "cpu_percent": 0.0,
        "ram_percent": 0.0,
        "disk_percent": 0.0,
        "network_bytes_sent": 0,
        "network_bytes_recv": 0,
        "network_packets_sent": 0,
        "network_packets_recv": 0,
        "processes_count": 0,
        "boot_time": None,
        "uptime_seconds": 0,
    }
    
    if not psutil:
        return info
    
    try:
        # CPU usage
        info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
    except Exception:
        pass
    
    try:
        # Memory usage
        vm = psutil.virtual_memory()
        info["ram_percent"] = vm.percent
    except Exception:
        pass
    
    try:
        # Disk usage
        disk = psutil.disk_usage(os.path.abspath(os.sep))
        info["disk_percent"] = (disk.used / disk.total) * 100 if disk.total > 0 else 0.0
    except Exception:
        pass
    
    try:
        # Network stats
        net_io = psutil.net_io_counters()
        if net_io:
            info["network_bytes_sent"] = net_io.bytes_sent
            info["network_bytes_recv"] = net_io.bytes_recv
            info["network_packets_sent"] = net_io.packets_sent
            info["network_packets_recv"] = net_io.packets_recv
    except Exception:
        pass
    
    try:
        # Process count
        info["processes_count"] = len(psutil.pids())
    except Exception:
        pass
    
    try:
        # System uptime
        boot_time = psutil.boot_time()
        info["boot_time"] = boot_time
        info["uptime_seconds"] = time.time() - boot_time
    except Exception:
        pass
    
    return info


def get_network_info() -> Dict[str, Any]:
    """
    Pobiera informacje o interfejsach sieciowych.
    
    Returns:
        dict: Informacje o interfejsach sieciowych.
    """
    info = {
        "interfaces": [],
        "connections_count": 0,
        "listening_ports": [],
    }
    
    if not psutil:
        return info
    
    try:
        # Network interfaces
        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        for interface_name, addrs in interfaces.items():
            interface_info = {
                "name": interface_name,
                "addresses": [],
                "is_up": False,
                "speed": 0,
            }
            
            # Get addresses
            for addr in addrs:
                interface_info["addresses"].append({
                    "family": str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast,
                })
            
            # Get stats
            if interface_name in stats:
                stat = stats[interface_name]
                interface_info["is_up"] = stat.isup
                interface_info["speed"] = stat.speed
            
            info["interfaces"].append(interface_info)
    except Exception:
        pass
    
    try:
        # Network connections
        connections = psutil.net_connections()
        info["connections_count"] = len(connections)
        
        # Listening ports
        listening_ports = []
        for conn in connections:
            if conn.status == 'LISTEN' and conn.laddr:
                listening_ports.append({
                    "port": conn.laddr.port,
                    "address": conn.laddr.ip,
                    "family": str(conn.family),
                    "type": str(conn.type),
                })
        info["listening_ports"] = listening_ports
    except Exception:
        pass
    
    return info


def get_process_info() -> Dict[str, Any]:
    """
    Pobiera informacje o procesach systemowych.
    
    Returns:
        dict: Informacje o procesach.
    """
    info = {
        "total_processes": 0,
        "running_processes": 0,
        "sleeping_processes": 0,
        "top_cpu_processes": [],
        "top_memory_processes": [],
    }
    
    if not psutil:
        return info
    
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        info["total_processes"] = len(processes)
        
        # Count by status
        for proc in processes:
            if proc['status'] == 'running':
                info["running_processes"] += 1
            elif proc['status'] == 'sleeping':
                info["sleeping_processes"] += 1
        
        # Top CPU processes
        cpu_sorted = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)
        info["top_cpu_processes"] = cpu_sorted[:5]
        
        # Top memory processes
        mem_sorted = sorted(processes, key=lambda x: x['memory_percent'] or 0, reverse=True)
        info["top_memory_processes"] = mem_sorted[:5]
        
    except Exception:
        pass
    
    return info


def format_bytes(bytes_value: int) -> str:
    """
    Formatuje liczbę bajtów do czytelnej postaci.
    
    Args:
        bytes_value: Liczba bajtów
        
    Returns:
        str: Sformatowana wartość (np. "1.2 GB")
    """
    if bytes_value == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(bytes_value)
    
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    
    return f"{size:.1f} {units[i]}"


def format_uptime(seconds: float) -> str:
    """
    Formatuje czas działania systemu.
    
    Args:
        seconds: Liczba sekund
        
    Returns:
        str: Sformatowany czas (np. "2d 3h 45m")
    """
    if seconds <= 0:
        return "0s"
    
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    
    return " ".join(parts) if parts else "< 1m"
