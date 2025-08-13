#!/usr/bin/env python3
"""
GUI Layout Documentation for Network Scanner Tab
"""

def describe_gui_layout():
    """Describe the GUI layout for documentation purposes."""
    
    print("🖥️  Network Scanner GUI Layout")
    print("=" * 60)
    
    print("\n📋 Main Window - Tab Structure:")
    print("   [Pakiety] [Alerty] [AI] [Wizualizacja] [Skaner sieci] ← NEW")
    
    print("\n🔧 Network Scanner Tab Layout:")
    print("""
╭─────────────────────────────────────────────────────────╮
│                    Skaner sieci                         │
├─────────────────────┬───────────────────────────────────┤
│   KONFIGURACJA      │        WYNIKI                     │
│                     │                                   │
│ ┌─ Konfiguracja ──┐ │ ┌───────────────────────────────┐ │
│ │ sieci           │ │ │ Tabela wyników:               │ │
│ │                 │ │ │ ┌─────────────────────────────┐ │ │
│ │ Interfejs:      │ │ │ │IP        │Status│Hostname  │ │ │
│ │ [Wi-Fi ▼]       │ │ │ │          │      │Ports     │ │ │
│ │                 │ │ │ │          │Time  │          │ │ │
│ │ Zakres IP:      │ │ │ ├─────────────────────────────┤ │ │
│ │ [192.168.1.0/24]│ │ │ │192.168.1.1│ UP  │router    │ │ │
│ │                 │ │ │ │          │     │22,80,443 │ │ │
│ │ [Auto-wykryj]   │ │ │ │          │0.02s│          │ │ │
│ └─────────────────┘ │ │ ├─────────────────────────────┤ │ │
│                     │ │ │192.168.1.2│ UP  │desktop   │ │ │
│ ┌─ Konfiguracja ──┐ │ │ │          │     │22        │ │ │
│ │ skanowania      │ │ │ │          │0.15s│          │ │ │
│ │                 │ │ │ ├─────────────────────────────┤ │ │
│ │ Tryb:           │ │ │ │192.168.1.3│DOWN │          │ │ │
│ │ [light ▼]       │ │ │ │          │     │          │ │ │
│ │ Lekki: ARP/ICMP │ │ │ │          │     │          │ │ │
│ │                 │ │ │ └─────────────────────────────┘ │ │
│ │ Porty (heavy):  │ │ └───────────────────────────────┘ │
│ │ [22,80,443,8080]│ │                                   │
│ │                 │ │ Wyniki: 25 hostów (3 UP, 22 DOWN)│
│ │ Max wątki: [50] │ │                                   │
│ │ Timeout: [1s]   │ │ [Eksportuj wyniki]                │
│ └─────────────────┘ │                                   │
│                     │                                   │
│ [Start Skanowanie]  │                                   │
│ [Stop]              │                                   │
│                     │                                   │
│ Progress: ████▓▓▓▓▓▓│                                   │
│ Status: Skanowanie: │                                   │
│ 127/255 hostów      │                                   │
╰─────────────────────┴───────────────────────────────────╯
""")
    
    print("\n🎛️  Control Features:")
    print("   • Interface selection dropdown with auto-detection")
    print("   • IP range input field with validation")
    print("   • Auto-detect button for network range")
    print("   • Scan mode selection (Light/Heavy)")
    print("   • Port range configuration for heavy scans")
    print("   • Threading and timeout settings")
    print("   • Start/Stop scan buttons")
    print("   • Real-time progress bar")
    print("   • Live status updates")
    
    print("\n📊 Results Display:")
    print("   • Table with sortable columns:")
    print("     - IP address")
    print("     - Host status (UP/DOWN) with color coding")
    print("     - Resolved hostname")
    print("     - Open ports list")
    print("     - Response time")
    print("   • Live result updates during scanning")
    print("   • Summary statistics")
    print("   • Export to CSV functionality")
    
    print("\n⚡ Key Features:")
    print("   • Non-blocking asynchronous scanning")
    print("   • Two scan modes:")
    print("     - Light: ARP/ICMP ping (fast, minimal network footprint)")
    print("     - Heavy: TCP port scanning (detailed, slower)")
    print("   • Automatic network range detection")
    print("   • Manual IP range and port configuration")
    print("   • Multithreaded scanning with configurable thread count")
    print("   • Ability to stop scan in progress")
    print("   • Real-time progress tracking")
    print("   • Results export functionality")
    
    print("\n🔧 Integration:")
    print("   • Seamlessly integrated into existing main window")
    print("   • Uses same UI patterns as other tabs")
    print("   • Compatible with existing packet sniffer architecture")
    print("   • Follows application's PyQt5 conventions")
    print("   • Maintains consistent styling and behavior")

if __name__ == "__main__":
    describe_gui_layout()