#!/usr/bin/env python3
"""
Create static demonstration images of the network visualization charts.
This shows what the GUI would look like without requiring a display.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime, timedelta
import random

def create_demo_charts():
    """Create demonstration charts showing the visualization capabilities."""
    
    # Set up the figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Network Visualization Dashboard Demo', fontsize=16, fontweight='bold')
    
    # Generate sample data
    base_time = datetime.now()
    times = [base_time + timedelta(seconds=i) for i in range(60)]
    
    # Traffic intensity chart
    packets_per_sec = [random.randint(5, 50) for _ in range(60)]
    colors = []
    max_packets = max(packets_per_sec)
    for count in packets_per_sec:
        if count == 0:
            colors.append('gray')
        elif count < max_packets * 0.3:
            colors.append('green')
        elif count < max_packets * 0.7:
            colors.append('orange')
        else:
            colors.append('red')
    
    ax1.plot(times, packets_per_sec, 'b-', linewidth=2, alpha=0.7)
    for i in range(len(times)):
        ax1.scatter(times[i], packets_per_sec[i], c=colors[i], s=20, alpha=0.8)
    
    ax1.set_title('Natężenie ruchu sieciowego', fontweight='bold')
    ax1.set_xlabel('Czas')
    ax1.set_ylabel('Pakiety/sek')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax1.xaxis.set_major_locator(mdates.SecondLocator(interval=15))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Data size chart
    bytes_per_sec = [random.randint(1000, 100000) for _ in range(60)]
    kb_per_sec = [b / 1024 for b in bytes_per_sec]  # Convert to KB
    
    ax2.plot(times, kb_per_sec, 'g-', linewidth=2)
    ax2.fill_between(times, kb_per_sec, alpha=0.3, color='green')
    ax2.set_title('Rozmiar przesyłanych danych', fontweight='bold')
    ax2.set_xlabel('Czas')
    ax2.set_ylabel('KB/sek')
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax2.xaxis.set_major_locator(mdates.SecondLocator(interval=15))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    # Protocol distribution pie chart
    protocols = ['TCP', 'UDP', 'IP', 'ICMP', 'Inne']
    sizes = [60, 25, 10, 3, 2]
    colors_pie = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ffb3e6']
    
    wedges, texts, autotexts = ax3.pie(sizes, labels=protocols, autopct='%1.1f%%', 
                                       colors=colors_pie, startangle=90)
    ax3.set_title('Rozkład protokołów', fontweight='bold')
    
    # Network statistics as text
    ax4.axis('off')
    stats_text = """Statystyki sieciowe:

Łączna liczba pakietów: 1,675
Łączny rozmiar danych: 2,984,412 bajtów (2.84 MB)
Pakiety/minutę: 28
Bajty/minutę: 49,674
Średni rozmiar pakietu: 324.1 bajtów
Unikalne protokoły: 4

Geolokalizacja (przykładowe adresy):
8.8.8.8: Stany Zjednoczone, Mountain View
1.1.1.1: Australia, Sydney
208.67.222.222: Stany Zjednoczone, San Francisco

Funkcjonalności:
✓ Wykresy czasu rzeczywistego
✓ Interaktywne kontrole (zoom, przesuwanie)
✓ Konfigurowalny zakres czasu
✓ Kolorowanie według intensywności
✓ Automatyczne konwersje jednostek"""
    
    ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
    
    ax4.set_title('Informacje i statystyki', fontweight='bold')
    
    plt.tight_layout()
    
    # Save the demo image
    plt.savefig('/tmp/network_visualization_demo.png', dpi=150, bbox_inches='tight')
    print("Demo chart saved as: /tmp/network_visualization_demo.png")
    
    # Also create a simplified version showing the UI layout
    fig2, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.axis('off')
    
    layout_text = """
    ┌─────────────────────────────────────────────────────────────────────┐
    │                          SKANER3 - WIZUALIZACJA                    │
    ├─────────────────────────────────────────────────────────────────────┤
    │ Zakres czasu: [5 minut ▼] Odświeżanie: [2s] [Wyczyść dane]        │
    ├─────────────────────────────────┬───────────────────────────────────┤
    │                                 │                                   │
    │   📈 NATĘŻENIE RUCHU           │   🥧 ROZKŁAD PROTOKOŁÓW          │
    │   (Pakiety/sek w czasie)        │   (TCP, UDP, IP, ICMP)            │
    │                                 │                                   │
    │   - Kolorowanie intensywności   │   📍 GEOLOKALIZACJA               │
    │   - Interaktywne zoom/pan       │   (Kraje i miasta IP)             │
    │   - Automatyczne skalowanie     │                                   │
    │                                 │   📊 STATYSTYKI                   │
    ├─────────────────────────────────│   - Łączne pakiety                │
    │                                 │   - Transfer danych               │
    │   📊 ROZMIAR DANYCH            │   - Średnie rozmiary              │
    │   (Bajty/sek w czasie)          │   - Unikalne protokoły            │
    │                                 │                                   │
    │   - Automatyczne jednostki      │   ⚙️ KONTROLE                    │
    │   - Wypełnienie obszaru         │   - Zakres czasu (1min-1h)        │
    │   - Adaptacyjne skalowanie      │   - Częstotliwość odświeżania     │
    │                                 │   - Czyszczenie danych            │
    └─────────────────────────────────┴───────────────────────────────────┘
    
    FUNKCJONALNOŚCI:
    ✅ Real-time monitoring ruchu sieciowego
    ✅ Interaktywne wykresy z zoom i pan
    ✅ Geolokalizacja zewnętrznych adresów IP
    ✅ Analiza protokołów i statystyki
    ✅ Konfigurowalne opcje wyświetlania
    ✅ Bezproblemowa integracja z istniejącym kodem
    """
    
    ax.text(0.05, 0.95, layout_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    
    plt.title('Network Visualization Tab - Layout & Features', fontsize=14, fontweight='bold', pad=20)
    plt.savefig('/tmp/network_visualization_layout.png', dpi=150, bbox_inches='tight')
    print("Layout diagram saved as: /tmp/network_visualization_layout.png")
    
    return True

if __name__ == "__main__":
    create_demo_charts()