# AI Network Sniffer - Punkt startowy aplikacji

import sys
import argparse
import json

from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow
from core.adaptive_engine import AdaptiveEngine
from core.system_info import get_system_info


def format_bytes(bytes_value):
    """Formatuje bajty do czytelnej postaci."""
    if bytes_value is None:
        return "N/A"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(bytes_value)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def demonstrate_system_adaptation():
    """
    Demonstracja funkcjonalności automatycznego dostosowania parametrów aplikacji.
    Pokazuje wykryte parametry systemu i sugerowane ustawienia.
    """
    print("=" * 70)
    print("🔧 AUTOMATYCZNE DOSTOSOWANIE PARAMETRÓW APLIKACJI")
    print("=" * 70)
    
    # Pobierz informacje o systemie
    print("\n📊 ANALIZA SYSTEMU OPERACYJNEGO:")
    print("-" * 40)
    
    system_info = get_system_info()
    
    print(f"System operacyjny: {system_info.get('os', 'N/A')}")
    print(f"Wersja systemu: {system_info.get('os_version', 'N/A')}")
    
    print(f"\n🖥️ PROCESOR:")
    print(f"   Rdzenie fizyczne: {system_info.get('cpu_count', 'N/A')}")
    print(f"   Wątki logiczne: {system_info.get('cpu_threads', 'N/A')}")
    cpu_freq = system_info.get('cpu_freq')
    if cpu_freq:
        print(f"   Częstotliwość: {cpu_freq:.1f} MHz")
    else:
        print(f"   Częstotliwość: N/A")
    
    print(f"\n💾 PAMIĘĆ RAM:")
    ram_total = system_info.get('ram_total')
    ram_available = system_info.get('ram_available')
    print(f"   Całkowita: {format_bytes(ram_total)}")
    print(f"   Dostępna: {format_bytes(ram_available)}")
    if ram_total and ram_available:
        usage_percent = ((ram_total - ram_available) / ram_total) * 100
        print(f"   Wykorzystanie: {usage_percent:.1f}%")
    
    print(f"\n💿 DYSK TWARDY:")
    disk_total = system_info.get('disk_total')
    disk_free = system_info.get('disk_free')
    print(f"   Całkowita pojemność: {format_bytes(disk_total)}")
    print(f"   Wolne miejsce: {format_bytes(disk_free)}")
    if disk_total and disk_free:
        usage_percent = ((disk_total - disk_free) / disk_total) * 100
        print(f"   Wykorzystanie: {usage_percent:.1f}%")
    
    # Wykonaj analizę adaptacyjną
    print("\n🤖 ANALIZA AI I SUGEROWANE PARAMETRY:")
    print("-" * 40)
    
    # Tryb normalny
    print("\n📈 TRYB NORMALNY (zrównoważony):")
    normal_engine = AdaptiveEngine(conservative_mode=False)
    normal_results = normal_engine.analyze_system()
    
    print(f"   Optymalna liczba wątków: {normal_results['optimal_threads']}")
    print(f"   Rozmiar bufora głównego: {normal_results['buffer_size_mb']} MB")
    print(f"   Rozmiar bufora pakietów: {normal_results['packet_buffer_size']} MB")
    print(f"   Maksymalny rozmiar logów: {normal_results['max_log_size_mb']} MB")
    print(f"   Rozmiar paczki przetwarzania: {normal_results['processing_batch_size']} pakietów")
    print(f"   Interwał odświeżania UI: {normal_results['ui_update_interval_ms']} ms")
    print(f"   Profil wydajnościowy: {normal_results['performance_profile']}")
    
    # Tryb zachowawczy
    print("\n🛡️ TRYB ZACHOWAWCZY (niskie zużycie zasobów):")
    conservative_engine = AdaptiveEngine(conservative_mode=True)
    conservative_results = conservative_engine.analyze_system()
    
    print(f"   Optymalna liczba wątków: {conservative_results['optimal_threads']}")
    print(f"   Rozmiar bufora głównego: {conservative_results['buffer_size_mb']} MB")
    print(f"   Rozmiar bufora pakietów: {conservative_results['packet_buffer_size']} MB")
    print(f"   Maksymalny rozmiar logów: {conservative_results['max_log_size_mb']} MB")
    print(f"   Rozmiar paczki przetwarzania: {conservative_results['processing_batch_size']} pakietów")
    print(f"   Interwał odświeżania UI: {conservative_results['ui_update_interval_ms']} ms")
    
    # Rekomendacje AI
    print("\n💡 REKOMENDACJE AI:")
    print("-" * 40)
    recommendations = normal_results['recommendations']
    
    for category, recommendation in recommendations.items():
        print(f"\n🔸 {category.upper()}:")
        print(f"   {recommendation}")
    
    print("\n" + "=" * 70)
    print("✅ Analiza zakończona. Aplikacja może używać tych parametrów dla")
    print("   optymalnej wydajności dostosowanej do Twojego systemu.")
    print("=" * 70)


def main() -> int:
    """Główna funkcja aplikacji z obsługą argumentów linii poleceń."""
    parser = argparse.ArgumentParser(
        description="AI Network Sniffer - Inteligentny analizator ruchu sieciowego",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady użycia:
  python main.py                    # Uruchom aplikację GUI
  python main.py --demo             # Pokaż demonstrację adaptacji systemu
  python main.py --system-info      # Wyświetl informacje o systemie
        """
    )
    
    parser.add_argument(
        '--demo', 
        action='store_true',
        help='Uruchom demonstrację automatycznego dostosowania parametrów'
    )
    
    parser.add_argument(
        '--system-info',
        action='store_true', 
        help='Wyświetl szczegółowe informacje o systemie'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Wyświetl wyniki w formacie JSON (dla --demo lub --system-info)'
    )
    
    args = parser.parse_args()
    
    # Tryb demonstracji
    if args.demo:
        if args.json:
            # Wyświetl wyniki w formacie JSON
            engine = AdaptiveEngine()
            results = engine.analyze_system()
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            demonstrate_system_adaptation()
        return 0
    
    # Tryb informacji o systemie
    if args.system_info:
        system_info = get_system_info()
        if args.json:
            print(json.dumps(system_info, indent=2, ensure_ascii=False))
        else:
            print("Informacje o systemie:")
            print(json.dumps(system_info, indent=2, ensure_ascii=False))
        return 0
    
    # Tryb GUI (domyślny)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())