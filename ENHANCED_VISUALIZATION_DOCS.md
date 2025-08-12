# Enhanced Network Visualization - Filter Documentation

## Overview

The enhanced network visualization module provides comprehensive filtering capabilities for analyzing network traffic data in real-time. This implementation adds advanced filtering options, new chart types, and dynamic data presentation to the existing Skaner3 application.

## New Features

### 1. Comprehensive Filter Panel

The filter panel is located at the top of the "Wizualizacja" tab and includes:

#### Time Range Filter
- **Options**: 1 minuta, 5 minut, 15 minut, 30 minut, 1 godzina, 6 godzin
- **Purpose**: Controls the time window for data analysis
- **Default**: 5 minut
- **Behavior**: Auto-applies when changed

#### Protocol Filter
- **Input**: Comma-separated list (e.g., "TCP,UDP,ICMP")
- **Purpose**: Filters packets by protocol type
- **Default**: Empty (shows all protocols)
- **Case Insensitive**: Yes
- **Auto-apply**: Yes

#### Source IP Filter
- **Input**: Comma-separated list of IP addresses
- **Purpose**: Shows only packets from specified source IPs
- **Example**: "192.168.1.1,10.0.0.1"
- **Default**: Empty (shows all source IPs)
- **Auto-apply**: Yes

#### Destination IP Filter
- **Input**: Comma-separated list of IP addresses
- **Purpose**: Shows only packets to specified destination IPs
- **Example**: "8.8.8.8,1.1.1.1"
- **Default**: Empty (shows all destination IPs)
- **Auto-apply**: Yes

#### Threat Level Filter
- **Interface**: Dual-slider range selector
- **Range**: 0.0 to 1.0 (AI anomaly score)
- **Purpose**: Filters packets by AI-detected threat level
- **Default**: 0.0 - 1.0 (shows all threat levels)
- **Auto-apply**: Yes
- **Labels**: Dynamic min/max display

### 2. Enhanced Chart Types

#### Existing Charts (Enhanced with Filtering)
- **Traffic Intensity**: Line chart showing packets/second over time
- **Data Size**: Line chart showing bytes/second over time
- **Protocol Distribution**: Pie chart showing protocol breakdown

#### New Charts
- **Threat Level Distribution**: Bar chart showing threat level categories
- **Top IP Addresses**: Horizontal bar chart showing most active IPs

### 3. Filter Management

#### Control Buttons
- **"Zastosuj filtry"**: Manually trigger filter application
- **"Wyczyść filtry"**: Reset all filters to default state
- **"Wyczyść dane"**: Clear all collected data and charts

#### Auto-Application
- Filters automatically apply when changed
- Real-time chart updates
- Responsive UI performance

## Technical Implementation

### Data Structure Enhancements

#### PacketInfo Extension
```python
@dataclass
class PacketInfo:
    # ... existing fields ...
    ai_score: float = 0.0  # AI anomaly score for threat filtering
```

#### Filter State Management
```python
_active_filters = {
    'time_range': 300,              # seconds
    'protocols': set(),             # empty = all protocols
    'src_ips': set(),              # empty = all source IPs  
    'dst_ips': set(),              # empty = all destination IPs
    'threat_level_min': 0.0,       # minimum AI score
    'threat_level_max': 1.0        # maximum AI score
}
```

### Filtering Algorithm

The core filtering method `_get_filtered_packets()` applies filters in sequence:

1. **Time Filter**: Excludes packets older than selected time range
2. **Protocol Filter**: Includes only specified protocols (if any)
3. **Source IP Filter**: Includes only specified source IPs (if any)
4. **Destination IP Filter**: Includes only specified destination IPs (if any)
5. **Threat Level Filter**: Includes only packets within threat score range

### Chart Integration

All visualizations now use filtered data:
- Traffic and size charts show filtered packet rates
- Protocol distribution shows filtered protocol breakdown
- New threat and IP charts display filtered statistics
- Statistics panel shows filtered packet counts and metrics

## Usage Examples

### Example 1: Analyze High-Risk TCP Traffic
1. Set Protocol Filter: "TCP"
2. Set Threat Level: Min 0.7, Max 1.0
3. Set Time Range: "1 godzina"
4. View results in threat distribution and traffic charts

### Example 2: Monitor Specific Network Segment
1. Set Source IP Filter: "192.168.1.1,192.168.1.2,192.168.1.3"
2. Set Time Range: "30 minut"
3. View protocol distribution and top destination IPs

### Example 3: Detect Anomalies in DNS Traffic
1. Set Protocol Filter: "DNS"
2. Set Threat Level: Min 0.3, Max 1.0
3. Monitor threat distribution chart for unusual patterns

## Extensibility

### Adding New Filter Types

The filter architecture is designed for easy extension:

1. **Add filter field** to `_active_filters` dictionary
2. **Create UI control** in `_setup_ui()` method
3. **Add event handler** for filter changes
4. **Update `_get_filtered_packets()`** with new filter logic
5. **Test filtering** with new criteria

### Adding New Chart Types

To add new visualizations:

1. **Create figure and canvas** in `_setup_ui()`
2. **Add update method** (e.g., `_update_new_chart()`)
3. **Call update method** in `_update_visualizations()`
4. **Use filtered data** from `_get_filtered_packets()`

### Example: Adding Port Filter

```python
# 1. Add to filter state
_active_filters['ports'] = set()

# 2. Add UI control
self.port_filter = QLineEdit()
self.port_filter.setPlaceholderText("80,443,53")
self.port_filter.textChanged.connect(self._on_port_filter_changed)

# 3. Add event handler
def _on_port_filter_changed(self, text: str) -> None:
    if text.strip():
        ports = {int(p.strip()) for p in text.split(',') if p.strip().isdigit()}
        self._active_filters['ports'] = ports
    else:
        self._active_filters['ports'] = set()
    self._apply_filters()

# 4. Update filtering logic
def _get_filtered_packets(self) -> List[PacketInfo]:
    # ... existing filters ...
    
    # Port filter
    if (self._active_filters['ports'] and 
        packet.src_port not in self._active_filters['ports'] and
        packet.dst_port not in self._active_filters['ports']):
        continue
```

## Performance Considerations

### Optimization Strategies
- **Efficient filtering**: Single pass through packet buffer
- **Batch updates**: Chart updates triggered by timer, not per packet
- **Data limits**: Automatic cleanup of old data to prevent memory issues
- **Responsive UI**: Filters auto-apply without blocking interface

### Scalability
- **Memory management**: Deque with maxlen for time-series data
- **Update frequency**: Configurable refresh intervals (1-60 seconds)
- **Chart complexity**: Limited number of displayed items (top 10 IPs, 6 protocols)

## Integration Notes

### Main Window Integration
- Filter panel seamlessly integrated into existing UI
- Packets buffer shared between components
- AI scores automatically populated from analysis engine
- No breaking changes to existing functionality

### Backwards Compatibility
- All existing features preserved
- Default filter state shows all data (no filtering)
- Gradual adoption possible (filters can be ignored)

## Testing

The implementation includes comprehensive tests:

- **Unit tests**: Core filtering logic validation
- **Integration tests**: Chart update verification
- **Demo script**: Interactive testing with sample data
- **Performance tests**: Memory and update speed validation

## Future Enhancements

### Potential Additions
1. **Geolocation filtering**: Filter by country/region
2. **Time-of-day filters**: Show traffic for specific hours
3. **Statistical filters**: Standard deviation-based anomaly detection
4. **Custom filter expressions**: Boolean logic combinations
5. **Filter presets**: Save and load common filter combinations
6. **Export filtered data**: CSV/JSON export of filtered results

### UI Improvements
1. **Filter indicators**: Visual badges showing active filters
2. **Quick filters**: One-click common filter presets
3. **Filter history**: Recently used filter combinations
4. **Advanced mode**: Complex filter expressions
5. **Filter tooltips**: Help text for each filter type