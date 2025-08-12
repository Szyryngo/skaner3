# Mockup: System Diagnostics and AI Optimization Tab

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ [Pakiety] [Alerty] [AI] [Diagnostyka systemu i optymalizacja AI] <<<< NEW TAB   │
├─────────────────────────────────────────────────────────────────────────────────┤
│ [Odśwież dane]                                            Status: Aktywny       │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────┐ ┌─────────────────────────────────────────┐ │
│ │ METRYKI SYSTEMOWE               │ │ [Status AI] [Historia decyzji] [Stat.]  │ │
│ │                                 │ │                                         │ │
│ │ CPU:   [████████░░] 78.5%       │ │ Status silnika AI                       │ │
│ │ RAM:   [██████░░░░] 61.2%       │ │ ┌─────────────────────────────────────┐ │ │
│ │ Dysk:  [███░░░░░░░] 34.7%       │ │ │ ML aktywny:        TAK              │ │ │
│ │ Połączenia: 23                  │ │ │ Model gotowy:      TAK              │ │ │
│ │ Uptime: 2d 14h 32m              │ │ │ Przetworzonych:    1,247            │ │ │
│ │                                 │ │ │ Ostatni wynik:     0.652            │ │ │
│ │ Szczegóły systemu               │ │ └─────────────────────────────────────┘ │ │
│ │ ┌─────────────────────────────┐ │ │                                         │ │
│ │ │ Timestamp: 2024-01-15 14:32 │ │ │ Konfiguracja                            │ │
│ │ │ Procesy: 287                │ │ │ ┌─────────────────────────────────────┐ │ │
│ │ │ Sieć wysłane: 2.1 GB        │ │ │ │ Próg anomalii:     0.70             │ │ │
│ │ │ Sieć odebrane: 1.8 GB       │ │ │ │ Interwał retren.:  500              │ │ │
│ │ │ Pakiety wysłane: 15,234     │ │ │ │ Streaming aktywny: TAK              │ │ │
│ │ │ Pakiety odebrane: 14,987    │ │ │ └─────────────────────────────────────┘ │ │
│ │ └─────────────────────────────┘ │ │                                         │ │
│ │                                 │ │ Ostatnie powody anomalii                │ │
│ │ Top procesy (CPU/pamięć)        │ │ ┌─────────────────────────────────────┐ │ │
│ │ ┌─────────────────────────────┐ │ │ │ • large_length>=1400                │ │ │
│ │ │PID │Nazwa    │CPU%│RAM%    │ │ │ │ • suspicious_dst_port               │ │ │
│ │ │1234│firefox  │15.2│8.7     │ │ │ │ • iforest_decision<0                │ │ │
│ │ │5678│python   │12.1│4.3     │ │ │ └─────────────────────────────────────┘ │ │
│ │ │9012│chrome   │8.9 │12.1    │ │ │                                         │ │
│ │ └─────────────────────────────┘ │ │                                         │ │
│ └─────────────────────────────────┘ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘

Historia decyzji tab:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Okres: [Ostatnie 24 godziny ▼] Limit: [100 ▼] [Odśwież historię]              │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ Czas    │ Wynik │ Anomalia │ Powody               │ Źródło      │ Cel        │ │
│ │ 14:32:15│ 0.852 │ TAK      │ large_length, susp.. │192.168.1.10 │10.0.0.5    │ │
│ │ 14:32:12│ 0.234 │ NIE      │ -                    │192.168.1.15 │8.8.8.8     │ │
│ │ 14:32:09│ 0.721 │ TAK      │ iforest_decision<0   │10.0.0.100   │192.168.1.1 │ │
│ │ 14:32:06│ 0.156 │ NIE      │ -                    │192.168.1.20 │8.8.4.4     │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘

Statystyki tab:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Statystyki (ostatnie 24h)                                                      │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ Łączne decyzje:        1,247                                                │ │
│ │ Wykryte anomalie:      87                                                   │ │
│ │ Współczynnik anomalii: 7.0%                                                 │ │
│ │ Średni wynik:          0.423                                                │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│ Rozkład anomalii w czasie                                                      │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ Anomalie w ostatnich 24 godzinach:                                         │ │
│ │  0h temu: ████████ (8)                                                     │ │
│ │  1h temu: ██████ (6)                                                       │ │
│ │  2h temu: ████ (4)                                                         │ │
│ │  3h temu: ██████████ (10)                                                  │ │
│ │  4h temu: ██ (2)                                                           │ │
│ │  5h temu: ████████████ (12)                                                │ │
│ │  ...                                                                        │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Key Features Implemented:

### Left Panel: System Monitoring
- **Real-time metrics**: CPU, RAM, disk usage with progress bars
- **Network statistics**: Active connections, data transfer stats
- **System details**: Process count, network I/O, uptime
- **Top processes**: CPU and memory usage by process

### Right Panel: AI Analytics (3 tabs)
1. **Status AI**: 
   - AI engine status and readiness
   - Configuration parameters
   - Last anomaly reasons

2. **Historia decyzji**:
   - Filterable history table of AI decisions
   - Time period and limit controls
   - Detailed packet information for each decision

3. **Statystyki**:
   - Summary statistics over time periods
   - Anomaly detection rates
   - Timeline visualization of anomalies

### Technical Features:
- **Automatic updates**: System metrics refresh every 2s, AI data every 5s
- **Persistent history**: All AI decisions saved to JSON files
- **Memory management**: Automatic cleanup of old data
- **Performance optimized**: Efficient data structures and caching
- **Thread-safe**: Proper locking for concurrent access
