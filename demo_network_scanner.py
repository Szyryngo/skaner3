#!/usr/bin/env python3
"""
Demo script dla testowania funkcjonalności Network Scanner.
Pokazuje działanie skanera w trybie symulacji bez potrzeby GUI.
"""

import time
from core.network_scanner import NetworkScanner, ScanMode, HostInfo, ScanProgress


def demo_callback_host_found(host: HostInfo) -> None:
    """Callback wywoływany gdy znaleziono host."""
    status = "🟢 ALIVE" if host.is_alive else "🔴 DEAD"
    ports = f" | Ports: {','.join(map(str, host.open_ports))}" if host.open_ports else ""
    hostname = f" | {host.hostname}" if host.hostname else ""
    response = f" | {host.response_time:.1f}ms" if host.response_time else ""
    
    print(f"{status} {host.ip}{hostname}{response}{ports}")


def demo_callback_progress(progress: ScanProgress) -> None:
    """Callback wywoływany przy aktualizacji postępu."""
    if progress.hosts_total > 0:
        hosts_percent = (progress.hosts_scanned / progress.hosts_total) * 100
        print(f"Progress: {progress.hosts_scanned}/{progress.hosts_total} hosts ({hosts_percent:.1f}%) | "
              f"Found: {progress.hosts_found} alive | "
              f"Open ports: {progress.open_ports_found} | "
              f"Current: {progress.current_target}")


def demo_callback_complete() -> None:
    """Callback wywoływany po zakończeniu skanowania."""
    print("\n🎉 Skanowanie zakończone!")


def demo_callback_error(error: str) -> None:
    """Callback wywoływany przy błędzie."""
    print(f"❌ Błąd: {error}")


def demo_network_scanner():
    """Demonstracja funkcjonalności Network Scanner."""
    print("🚀 Network Scanner Demo")
    print("=" * 50)
    
    # Konfiguracja skanera
    scanner = NetworkScanner(
        mode=ScanMode.LIGHT,
        timeout=1.0,
        max_threads=10,
        use_simulation=True  # Używamy symulacji dla demo
    )
    
    # Ustawienie callbacków
    scanner.on_host_found = demo_callback_host_found
    scanner.on_progress_update = demo_callback_progress
    scanner.on_scan_complete = demo_callback_complete
    scanner.on_error = demo_callback_error
    
    print(f"Tryb: {scanner.mode.value}")
    print(f"Timeout: {scanner.timeout}s")
    print(f"Max threads: {scanner.max_threads}")
    print(f"Symulacja: {scanner.use_simulation}")
    print()
    
    # Test 1: Skanowanie pojedynczego IP
    print("📡 Test 1: Skanowanie pojedynczego IP")
    print("-" * 40)
    scanner.start_scan(
        ip_ranges=["192.168.1.1"],
        ports=[22, 80, 443],
        resolve_hostnames=True
    )
    
    # Czekaj na zakończenie
    while scanner.is_running():
        time.sleep(0.1)
    
    # Test 2: Skanowanie zakresu IP
    print("\n📡 Test 2: Skanowanie zakresu IP")
    print("-" * 40)
    scanner.start_scan(
        ip_ranges=["10.0.0.1-10.0.0.5"],
        ports=None,  # Użyj domyślnych
        resolve_hostnames=False
    )
    
    # Czekaj na zakończenie
    while scanner.is_running():
        time.sleep(0.1)
    
    # Test 3: Skanowanie sieci CIDR
    print("\n📡 Test 3: Skanowanie sieci CIDR")
    print("-" * 40)
    scanner.start_scan(
        ip_ranges=["172.16.1.0/29"],  # Mała sieć /29 = 6 hostów
        ports=[21, 22, 23, 80, 443],
        resolve_hostnames=True
    )
    
    # Czekaj na zakończenie
    while scanner.is_running():
        time.sleep(0.1)
    
    # Podsumowanie wyników
    print("\n📊 Podsumowanie wyników:")
    print("-" * 40)
    results = scanner.get_results()
    alive_hosts = scanner.get_alive_hosts()
    hosts_with_ports = scanner.get_hosts_with_open_ports()
    
    print(f"Łącznie przeskanowanych hostów: {len(results)}")
    print(f"Hostów aktywnych: {len(alive_hosts)}")
    print(f"Hostów z otwartymi portami: {len(hosts_with_ports)}")
    
    if alive_hosts:
        print("\n🟢 Aktywne hosty:")
        for host in alive_hosts:
            hostname = f" ({host.hostname})" if host.hostname else ""
            ports = f" - Porty: {','.join(map(str, host.open_ports))}" if host.open_ports else ""
            print(f"  • {host.ip}{hostname}{ports}")
    
    print("\n✅ Demo zakończone!")


if __name__ == "__main__":
    demo_network_scanner()