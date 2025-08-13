# System Status Viewer Implementation

## Overview
Created a new system monitoring tab in the Skaner3 GUI application that displays real-time system information.

## Files Created/Modified

### New Files:
1. `ui/system_status_viewer.py` - Main system status widget implementation
2. `tests/test_system_status_viewer.py` - Tests for system status functionality

### Modified Files:
1. `ui/main_window.py` - Added import and new "System" tab

## Features Implemented

### System Metrics Group
- **CPU Usage**: Real-time CPU percentage using `psutil.cpu_percent()`
- **RAM Usage**: Memory usage percentage using `psutil.virtual_memory().percent`
- **System Uptime**: Formatted uptime (days, hours, minutes) calculated from `psutil.boot_time()`
- **Active Threads**: Thread count using `threading.active_count()`

### Network Interfaces Table
- **Name**: Interface name (eth0, wlan0, etc.)
- **Status**: Active/Inactive status based on `is_up` flag
- **Type**: Interface type (Ethernet, Wi-Fi, Loopback, etc.) 
- **IPv4 Address**: Current IPv4 address or "-" if none

## Technical Details

### Auto-refresh
- Uses `QTimer` with 3-second intervals
- Updates both system metrics and network interfaces continuously
- Graceful error handling with fallback values

### UI Layout
- Two main groups: "Parametry systemowe" and "Interfejsy sieciowe"
- Clean table layout for network interfaces with proper column sizing
- Organized metrics display in a 2x2 grid layout

### Integration
- Seamlessly integrated as 5th tab: "Pakiety", "Alerty", "AI", "Wizualizacja", "System"
- Follows existing code patterns and styling
- No changes to existing functionality

## Usage
1. Start the application: `python3 main.py`
2. Navigate to the "System" tab
3. View real-time system information updating every 3 seconds

## Tab Layout Preview
```
┌─ System Tab ─────────────────────────────────────────┐
│ ┌─ Parametry systemowe ─────────────────────────────┐ │
│ │ CPU: 15.2%        RAM: 45.8%                      │ │
│ │ Uptime: 2d 14h 23m    Aktywne wątki: 24          │ │
│ └───────────────────────────────────────────────────┘ │
│                                                       │
│ ┌─ Interfejsy sieciowe ─────────────────────────────┐ │
│ │ Nazwa    │ Status     │ Typ      │ Adres IPv4     │ │
│ │ eth0     │ Aktywny    │ Ethernet │ 192.168.1.100  │ │
│ │ wlan0    │ Nieaktywny │ Wi-Fi    │ -              │ │
│ │ lo       │ Aktywny    │ Loopback │ 127.0.0.1      │ │
│ └───────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
```

## Tests
- All existing tests continue to pass (17/17)
- New tests validate:
  - Uptime formatting functionality
  - System data availability
  - Network interface data structure
  - Integration with existing functions