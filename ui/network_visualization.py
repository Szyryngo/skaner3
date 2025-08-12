from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QComboBox, QLabel, QPushButton, QTextEdit,
    QTabWidget, QSpinBox, QLineEdit, QCheckBox,
    QGroupBox, QGridLayout, QSlider
)

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation

import numpy as np

from core.utils import PacketInfo, geolocate_ip


class NetworkVisualization(QWidget):
    """Network traffic visualization widget with charts and geolocation map."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        # Data storage for visualizations
        self._packets_buffer: List[PacketInfo] = []  # Will be set from main window
        self._traffic_history: deque = deque(maxlen=300)  # 5 minutes at 1-second intervals
        self._packet_size_history: deque = deque(maxlen=300)
        self._protocol_counts: Dict[str, int] = defaultdict(int)
        self._geo_locations: Dict[str, Dict] = {}  # Cache for geolocation data
        
        # Filtering state
        self._active_filters = {
            'time_range': 300,  # seconds
            'protocols': set(),  # empty means all protocols
            'src_ips': set(),    # empty means all IPs  
            'dst_ips': set(),    # empty means all IPs
            'threat_level_min': 0.0,  # minimum threat score
            'threat_level_max': 1.0   # maximum threat score
        }
        
        # Time tracking
        self._last_update_time = time.time()
        self._current_second_count = 0
        self._current_second_bytes = 0
        
        self._setup_ui()
        self._setup_timers()
        
    def _setup_ui(self) -> None:
        """Initialize the user interface components."""
        layout = QVBoxLayout(self)
        
        # Filter panel
        filter_group = QGroupBox("Filtry")
        filter_layout = QGridLayout(filter_group)
        
        # Time range filter
        filter_layout.addWidget(QLabel("Zakres czasu:"), 0, 0)
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["1 minuta", "5 minut", "15 minut", "30 minut", "1 godzina", "6 godzin"])
        self.time_range_combo.setCurrentText("5 minut")
        self.time_range_combo.currentTextChanged.connect(self._on_time_range_changed)
        filter_layout.addWidget(self.time_range_combo, 0, 1)
        
        # Protocol filter
        filter_layout.addWidget(QLabel("Protokoły:"), 0, 2)
        self.protocol_filter = QLineEdit()
        self.protocol_filter.setPlaceholderText("TCP,UDP,ICMP (puste = wszystkie)")
        self.protocol_filter.textChanged.connect(self._on_protocol_filter_changed)
        filter_layout.addWidget(self.protocol_filter, 0, 3)
        
        # Source IP filter
        filter_layout.addWidget(QLabel("IP źródłowe:"), 1, 0)
        self.src_ip_filter = QLineEdit()
        self.src_ip_filter.setPlaceholderText("192.168.1.1,10.0.0.1 (puste = wszystkie)")
        self.src_ip_filter.textChanged.connect(self._on_src_ip_filter_changed)
        filter_layout.addWidget(self.src_ip_filter, 1, 1)
        
        # Destination IP filter
        filter_layout.addWidget(QLabel("IP docelowe:"), 1, 2)
        self.dst_ip_filter = QLineEdit()
        self.dst_ip_filter.setPlaceholderText("8.8.8.8,1.1.1.1 (puste = wszystkie)")
        self.dst_ip_filter.textChanged.connect(self._on_dst_ip_filter_changed)
        filter_layout.addWidget(self.dst_ip_filter, 1, 3)
        
        # Threat level filter
        filter_layout.addWidget(QLabel("Poziom zagrożenia:"), 2, 0)
        threat_layout = QHBoxLayout()
        self.threat_min_slider = QSlider(Qt.Horizontal)
        self.threat_min_slider.setRange(0, 100)
        self.threat_min_slider.setValue(0)
        self.threat_min_slider.valueChanged.connect(self._on_threat_filter_changed)
        self.threat_min_label = QLabel("Min: 0.0")
        threat_layout.addWidget(self.threat_min_label)
        threat_layout.addWidget(self.threat_min_slider)
        
        self.threat_max_slider = QSlider(Qt.Horizontal)
        self.threat_max_slider.setRange(0, 100)
        self.threat_max_slider.setValue(100)
        self.threat_max_slider.valueChanged.connect(self._on_threat_filter_changed)
        self.threat_max_label = QLabel("Max: 1.0")
        threat_layout.addWidget(self.threat_max_label)
        threat_layout.addWidget(self.threat_max_slider)
        
        threat_widget = QWidget()
        threat_widget.setLayout(threat_layout)
        filter_layout.addWidget(threat_widget, 2, 1, 1, 2)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.apply_filters_btn = QPushButton("Zastosuj filtry")
        self.apply_filters_btn.clicked.connect(self._apply_filters)
        self.clear_filters_btn = QPushButton("Wyczyść filtry")
        self.clear_filters_btn.clicked.connect(self._clear_filters)
        self.clear_data_btn = QPushButton("Wyczyść dane")
        self.clear_data_btn.clicked.connect(self._clear_data)
        control_layout.addWidget(self.apply_filters_btn)
        control_layout.addWidget(self.clear_filters_btn)
        control_layout.addWidget(self.clear_data_btn)
        
        # Refresh interval
        control_layout.addWidget(QLabel("Odświeżanie (s):"))
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(1, 60)
        self.refresh_interval_spin.setValue(2)
        self.refresh_interval_spin.valueChanged.connect(self._on_refresh_interval_changed)
        control_layout.addWidget(self.refresh_interval_spin)
        
        control_layout.addStretch()
        filter_layout.addLayout(control_layout, 2, 3)
        
        layout.addWidget(filter_group)
        
        # Main visualization area
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Charts
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        
        # Traffic intensity chart
        self.traffic_figure = Figure(figsize=(8, 3))
        self.traffic_canvas = FigureCanvas(self.traffic_figure)
        self.traffic_canvas.mpl_connect('scroll_event', self._on_chart_scroll)
        self.traffic_canvas.mpl_connect('button_press_event', self._on_chart_click)
        self.traffic_ax = self.traffic_figure.add_subplot(111)
        self.traffic_ax.set_title("Natężenie ruchu sieciowego")
        self.traffic_ax.set_xlabel("Czas")
        self.traffic_ax.set_ylabel("Pakiety/sek")
        charts_layout.addWidget(self.traffic_canvas)
        
        # Data size chart
        self.size_figure = Figure(figsize=(8, 3))
        self.size_canvas = FigureCanvas(self.size_figure)
        self.size_canvas.mpl_connect('scroll_event', self._on_chart_scroll)
        self.size_canvas.mpl_connect('button_press_event', self._on_chart_click)
        self.size_ax = self.size_figure.add_subplot(111)
        self.size_ax.set_title("Rozmiar przesyłanych danych")
        self.size_ax.set_xlabel("Czas")
        self.size_ax.set_ylabel("Bajty/sek")
        charts_layout.addWidget(self.size_canvas)
        
        main_splitter.addWidget(charts_widget)
        
        # Right side: Additional charts and info
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        # Tabs for different chart types
        chart_tabs = QTabWidget()
        
        # Protocol distribution tab
        protocol_tab = QWidget()
        protocol_tab_layout = QVBoxLayout(protocol_tab)
        self.protocol_figure = Figure(figsize=(4, 4))
        self.protocol_canvas = FigureCanvas(self.protocol_figure)
        self.protocol_ax = self.protocol_figure.add_subplot(111)
        self.protocol_ax.set_title("Rozkład protokołów")
        protocol_tab_layout.addWidget(self.protocol_canvas)
        chart_tabs.addTab(protocol_tab, "Protokoły")
        
        # Threat level distribution tab
        threat_tab = QWidget()
        threat_tab_layout = QVBoxLayout(threat_tab)
        self.threat_figure = Figure(figsize=(4, 4))
        self.threat_canvas = FigureCanvas(self.threat_figure)
        self.threat_ax = self.threat_figure.add_subplot(111)
        self.threat_ax.set_title("Rozkład poziomów zagrożenia")
        threat_tab_layout.addWidget(self.threat_canvas)
        chart_tabs.addTab(threat_tab, "Zagrożenia")
        
        # Top IPs tab
        ips_tab = QWidget()
        ips_tab_layout = QVBoxLayout(ips_tab)
        self.ips_figure = Figure(figsize=(4, 4))
        self.ips_canvas = FigureCanvas(self.ips_figure)
        self.ips_ax = self.ips_figure.add_subplot(111)
        self.ips_ax.set_title("Najaktywniejsze IP")
        ips_tab_layout.addWidget(self.ips_canvas)
        chart_tabs.addTab(ips_tab, "Top IP")
        
        info_layout.addWidget(chart_tabs)
        
        # Geolocation info
        info_layout.addWidget(QLabel("Informacje geolokalizacyjne:"))
        self.geo_text = QTextEdit()
        self.geo_text.setMaximumHeight(150)
        self.geo_text.setReadOnly(True)
        info_layout.addWidget(self.geo_text)
        
        # Network statistics
        info_layout.addWidget(QLabel("Statystyki sieciowe:"))
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(150)
        self.stats_text.setReadOnly(True)
        info_layout.addWidget(self.stats_text)
        
        main_splitter.addWidget(info_widget)
        
        # Set splitter proportions
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 1)
        
        layout.addWidget(main_splitter)
        
    def _setup_timers(self) -> None:
        """Setup timers for automatic data updates."""
        # Timer for updating visualizations
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_visualizations)
        self.update_timer.start(2000)  # Update every 2 seconds by default
        
        # Timer for collecting data every second
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self._collect_data_point)
        self.data_timer.start(1000)  # Collect data every second
        
    def set_packets_buffer(self, packets_buffer: List[PacketInfo]) -> None:
        """Set the reference to the main packets buffer."""
        self._packets_buffer = packets_buffer
        
    def _collect_data_point(self) -> None:
        """Collect network traffic data for the current second."""
        current_time = time.time()
        
        # Get filtered packets for counting
        filtered_packets = self._get_filtered_packets()
        
        # Count packets and bytes in the last second from filtered data
        packets_count = 0
        bytes_count = 0
        
        for packet in filtered_packets:
            if packet.timestamp >= self._last_update_time:
                packets_count += 1
                bytes_count += packet.length
                
                # Update protocol counts (only from filtered data)
                self._protocol_counts[packet.protocol] += 1
        
        # Store data point
        timestamp = datetime.fromtimestamp(current_time)
        self._traffic_history.append((timestamp, packets_count))
        self._packet_size_history.append((timestamp, bytes_count))
        
        self._last_update_time = current_time
        
    def _update_visualizations(self) -> None:
        """Update all visualization components."""
        self._update_traffic_chart()
        self._update_size_chart()
        self._update_protocol_chart()
        self._update_threat_chart()
        self._update_ips_chart()
        self._update_geolocation_info()
        self._update_network_stats()
        
    def _update_traffic_chart(self) -> None:
        """Update the traffic intensity chart."""
        if not self._traffic_history:
            return
            
        self.traffic_ax.clear()
        
        times, counts = zip(*self._traffic_history)
        
        # Color code based on traffic intensity
        colors = []
        max_count = max(counts) if counts else 1
        for count in counts:
            if count == 0:
                colors.append('gray')
            elif count < max_count * 0.3:
                colors.append('green')
            elif count < max_count * 0.7:
                colors.append('orange')
            else:
                colors.append('red')
        
        # Create line plot with color segments
        self.traffic_ax.plot(times, counts, 'b-', linewidth=2, alpha=0.7)
        
        # Add scatter plot for color coding
        if len(times) > 1:
            for i in range(len(times)):
                self.traffic_ax.scatter(times[i], counts[i], c=colors[i], s=30, alpha=0.8)
        
        self.traffic_ax.set_title("Natężenie ruchu sieciowego")
        self.traffic_ax.set_xlabel("Czas")
        self.traffic_ax.set_ylabel("Pakiety/sek")
        self.traffic_ax.grid(True, alpha=0.3)
        
        # Format x-axis for time
        if len(times) > 1:
            time_range = (times[-1] - times[0]).total_seconds()
            if time_range > 3600:  # More than 1 hour
                self.traffic_ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                self.traffic_ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
            elif time_range > 600:  # More than 10 minutes
                self.traffic_ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                self.traffic_ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=2))
            else:
                self.traffic_ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                self.traffic_ax.xaxis.set_major_locator(mdates.SecondLocator(interval=30))
        
        # Rotate labels for better readability
        plt.setp(self.traffic_ax.xaxis.get_majorticklabels(), rotation=45)
        
        self.traffic_figure.tight_layout()
        self.traffic_canvas.draw()
        
    def _update_size_chart(self) -> None:
        """Update the data size chart."""
        if not self._packet_size_history:
            return
            
        self.size_ax.clear()
        
        times, sizes = zip(*self._packet_size_history)
        
        # Convert bytes to more readable units
        max_size = max(sizes) if sizes else 1
        if max_size > 1024 * 1024:  # MB
            unit = "MB"
            sizes = [s / (1024 * 1024) for s in sizes]
        elif max_size > 1024:  # KB
            unit = "KB"
            sizes = [s / 1024 for s in sizes]
        else:
            unit = "Bytes"
        
        self.size_ax.plot(times, sizes, 'g-', linewidth=2)
        self.size_ax.fill_between(times, sizes, alpha=0.3, color='green')
        self.size_ax.set_title("Rozmiar przesyłanych danych")
        self.size_ax.set_xlabel("Czas")
        self.size_ax.set_ylabel(f"{unit}/sek")
        self.size_ax.grid(True, alpha=0.3)
        
        # Format x-axis for time
        if len(times) > 1:
            time_range = (times[-1] - times[0]).total_seconds()
            if time_range > 3600:  # More than 1 hour
                self.size_ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                self.size_ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
            elif time_range > 600:  # More than 10 minutes
                self.size_ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                self.size_ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=2))
            else:
                self.size_ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                self.size_ax.xaxis.set_major_locator(mdates.SecondLocator(interval=30))
        
        # Rotate labels for better readability
        plt.setp(self.size_ax.xaxis.get_majorticklabels(), rotation=45)
        
        self.size_figure.tight_layout()
        self.size_canvas.draw()
        
    def _update_protocol_chart(self) -> None:
        """Update the protocol distribution pie chart."""
        # Use filtered data for protocol counts
        filtered_packets = self._get_filtered_packets()
        protocol_counts = defaultdict(int)
        
        for packet in filtered_packets:
            protocol_counts[packet.protocol] += 1
            
        if not protocol_counts:
            self.protocol_ax.clear()
            self.protocol_ax.text(0.5, 0.5, 'Brak danych', 
                                ha='center', va='center', transform=self.protocol_ax.transAxes)
            self.protocol_canvas.draw()
            return
            
        self.protocol_ax.clear()
        
        protocols = list(protocol_counts.keys())
        counts = list(protocol_counts.values())
        
        # Only show top 6 protocols
        if len(protocols) > 6:
            # Sort by count and take top 6
            protocol_data = sorted(zip(protocols, counts), key=lambda x: x[1], reverse=True)
            protocols = [p[0] for p in protocol_data[:6]]
            counts = [p[1] for p in protocol_data[:6]]
            
            # Add "Others" category
            other_count = sum(p[1] for p in protocol_data[6:])
            if other_count > 0:
                protocols.append("Inne")
                counts.append(other_count)
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(protocols)))
        
        self.protocol_ax.pie(counts, labels=protocols, autopct='%1.1f%%', colors=colors)
        self.protocol_ax.set_title("Rozkład protokołów")
        
        self.protocol_figure.tight_layout()
        self.protocol_canvas.draw()
        
    def _update_threat_chart(self) -> None:
        """Update the threat level distribution chart."""
        filtered_packets = self._get_filtered_packets()
        
        if not filtered_packets:
            self.threat_ax.clear()
            self.threat_ax.text(0.5, 0.5, 'Brak danych', 
                              ha='center', va='center', transform=self.threat_ax.transAxes)
            self.threat_canvas.draw()
            return
            
        # Collect threat scores
        threat_scores = []
        for packet in filtered_packets:
            score = getattr(packet, 'ai_score', 0.0)
            threat_scores.append(score)
            
        if not threat_scores:
            self.threat_ax.clear()
            self.threat_ax.text(0.5, 0.5, 'Brak danych o zagrożeniach', 
                              ha='center', va='center', transform=self.threat_ax.transAxes)
            self.threat_canvas.draw()
            return
            
        self.threat_ax.clear()
        
        # Create histogram of threat levels
        bins = [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        labels = ['Bardzo niski', 'Niski', 'Średni', 'Podwyższony', 'Wysoki', 'Krytyczny']
        colors = ['green', 'lightgreen', 'yellow', 'orange', 'red', 'darkred']
        
        hist, _ = np.histogram(threat_scores, bins=bins)
        
        # Create bar chart
        x_pos = range(len(labels))
        bars = self.threat_ax.bar(x_pos, hist, color=colors, alpha=0.7)
        
        self.threat_ax.set_title("Rozkład poziomów zagrożenia")
        self.threat_ax.set_xlabel("Poziom zagrożenia")
        self.threat_ax.set_ylabel("Liczba pakietów")
        self.threat_ax.set_xticks(x_pos)
        self.threat_ax.set_xticklabels(labels, rotation=45, ha='right')
        
        # Add value labels on bars
        for bar, count in zip(bars, hist):
            if count > 0:
                self.threat_ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                                  str(count), ha='center', va='bottom')
        
        self.threat_figure.tight_layout()
        self.threat_canvas.draw()
        
    def _update_ips_chart(self) -> None:
        """Update the top IPs chart."""
        filtered_packets = self._get_filtered_packets()
        
        if not filtered_packets:
            self.ips_ax.clear()
            self.ips_ax.text(0.5, 0.5, 'Brak danych', 
                           ha='center', va='center', transform=self.ips_ax.transAxes)
            self.ips_canvas.draw()
            return
            
        # Count IP occurrences (both source and destination)
        ip_counts = defaultdict(int)
        for packet in filtered_packets:
            if packet.src_ip and packet.src_ip != "?":
                ip_counts[packet.src_ip] += 1
            if packet.dst_ip and packet.dst_ip != "?":
                ip_counts[packet.dst_ip] += 1
                
        if not ip_counts:
            self.ips_ax.clear()
            self.ips_ax.text(0.5, 0.5, 'Brak danych IP', 
                           ha='center', va='center', transform=self.ips_ax.transAxes)
            self.ips_canvas.draw()
            return
            
        self.ips_ax.clear()
        
        # Get top 10 IPs
        top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if top_ips:
            ips, counts = zip(*top_ips)
            
            # Create horizontal bar chart
            y_pos = range(len(ips))
            bars = self.ips_ax.barh(y_pos, counts, color='skyblue', alpha=0.7)
            
            self.ips_ax.set_title("Najaktywniejsze adresy IP")
            self.ips_ax.set_xlabel("Liczba pakietów")
            self.ips_ax.set_yticks(y_pos)
            
            # Truncate long IP addresses for better display
            display_ips = [ip[:15] + '...' if len(ip) > 15 else ip for ip in ips]
            self.ips_ax.set_yticklabels(display_ips)
            
            # Add value labels on bars
            for bar, count in zip(bars, counts):
                self.ips_ax.text(bar.get_width() + max(counts) * 0.01, 
                               bar.get_y() + bar.get_height()/2,
                               str(count), ha='left', va='center')
        
        self.ips_figure.tight_layout()
        self.ips_canvas.draw()
        
    def _update_geolocation_info(self) -> None:
        """Update geolocation information text."""
        filtered_packets = self._get_filtered_packets()
        
        if not filtered_packets:
            self.geo_text.setPlainText("Brak danych do wyświetlenia")
            return
            
        # Get unique IPs from filtered packets (last 100)
        recent_packets = filtered_packets[-100:] if len(filtered_packets) > 100 else filtered_packets
        unique_ips = set()
        
        for packet in recent_packets:
            if packet.src_ip != "?" and not packet.src_ip.startswith("192.168.") and not packet.src_ip.startswith("10."):
                unique_ips.add(packet.src_ip)
            if packet.dst_ip != "?" and not packet.dst_ip.startswith("192.168.") and not packet.dst_ip.startswith("10."):
                unique_ips.add(packet.dst_ip)
        
        geo_info = []
        for ip in list(unique_ips)[:10]:  # Limit to 10 IPs to avoid spam
            if ip not in self._geo_locations:
                self._geo_locations[ip] = geolocate_ip(ip)
            
            geo_data = self._geo_locations[ip]
            location = f"{geo_data.get('country', 'N/A')}, {geo_data.get('city', 'N/A')}"
            isp = geo_data.get('isp', 'N/A')
            geo_info.append(f"{ip}: {location} ({isp})")
        
        self.geo_text.setPlainText("\n".join(geo_info))
        
    def _update_network_stats(self) -> None:
        """Update network statistics text."""
        filtered_packets = self._get_filtered_packets()
        
        if not filtered_packets:
            self.stats_text.setPlainText("Brak danych do wyświetlenia")
            return
            
        total_packets = len(filtered_packets)
        total_bytes = sum(p.length for p in filtered_packets)
        
        # Calculate rates from recent filtered data
        current_time = time.time()
        recent_packets = [p for p in filtered_packets if current_time - p.timestamp <= 60]  # Last minute
        
        if recent_packets:
            packets_per_minute = len(recent_packets)
            bytes_per_minute = sum(p.length for p in recent_packets)
            avg_packet_size = bytes_per_minute / len(recent_packets) if recent_packets else 0
        else:
            packets_per_minute = 0
            bytes_per_minute = 0
            avg_packet_size = 0
            
        # Count unique protocols in filtered data
        unique_protocols = set(p.protocol for p in filtered_packets)
        
        # Count threat levels
        high_threat_count = sum(1 for p in filtered_packets 
                              if getattr(p, 'ai_score', 0.0) > 0.7)
        
        stats_text = f"""Filtrowane pakiety: {total_packets}
Łączny rozmiar danych: {total_bytes:,} bajtów ({total_bytes / 1024 / 1024:.2f} MB)
Pakiety/minutę: {packets_per_minute}
Bajty/minutę: {bytes_per_minute:,}
Średni rozmiar pakietu: {avg_packet_size:.1f} bajtów
Unikalne protokoły: {len(unique_protocols)}
Pakiety wysokiego ryzyka: {high_threat_count}

Aktywne filtry:
- Zakres czasu: {self._active_filters['time_range']}s
- Protokoły: {', '.join(self._active_filters['protocols']) or 'wszystkie'}
- IP źródłowe: {', '.join(self._active_filters['src_ips']) or 'wszystkie'}
- IP docelowe: {', '.join(self._active_filters['dst_ips']) or 'wszystkie'}
- Zagrożenie: {self._active_filters['threat_level_min']:.2f} - {self._active_filters['threat_level_max']:.2f}"""
        
        self.stats_text.setPlainText(stats_text)
        
    def _on_time_range_changed(self, range_text: str) -> None:
        """Handle time range selection change."""
        # Map text to seconds
        range_map = {
            "1 minuta": 60,
            "5 minut": 300,
            "15 minut": 900,
            "30 minut": 1800,
            "1 godzina": 3600,
            "6 godzin": 21600
        }
        
        seconds = range_map.get(range_text, 300)
        self._active_filters['time_range'] = seconds
        max_points = seconds  # One point per second
        
        # Update deque max length
        self._traffic_history = deque(self._traffic_history, maxlen=max_points)
        self._packet_size_history = deque(self._packet_size_history, maxlen=max_points)
        
        # Apply filters and update visualizations
        self._apply_filters()
        
    def _on_protocol_filter_changed(self, text: str) -> None:
        """Handle protocol filter change."""
        if text.strip():
            protocols = {p.strip().upper() for p in text.split(',') if p.strip()}
            self._active_filters['protocols'] = protocols
        else:
            self._active_filters['protocols'] = set()
        # Auto-apply filters on change
        self._apply_filters()
        
    def _on_src_ip_filter_changed(self, text: str) -> None:
        """Handle source IP filter change."""
        if text.strip():
            ips = {ip.strip() for ip in text.split(',') if ip.strip()}
            self._active_filters['src_ips'] = ips
        else:
            self._active_filters['src_ips'] = set()
        # Auto-apply filters on change
        self._apply_filters()
        
    def _on_dst_ip_filter_changed(self, text: str) -> None:
        """Handle destination IP filter change."""
        if text.strip():
            ips = {ip.strip() for ip in text.split(',') if ip.strip()}
            self._active_filters['dst_ips'] = ips
        else:
            self._active_filters['dst_ips'] = set()
        # Auto-apply filters on change
        self._apply_filters()
        
    def _on_threat_filter_changed(self) -> None:
        """Handle threat level filter change."""
        min_val = self.threat_min_slider.value() / 100.0
        max_val = self.threat_max_slider.value() / 100.0
        
        # Ensure min <= max
        if min_val > max_val:
            if self.sender() == self.threat_min_slider:
                self.threat_max_slider.setValue(int(min_val * 100))
                max_val = min_val
            else:
                self.threat_min_slider.setValue(int(max_val * 100))
                min_val = max_val
        
        self._active_filters['threat_level_min'] = min_val
        self._active_filters['threat_level_max'] = max_val
        
        # Update labels
        self.threat_min_label.setText(f"Min: {min_val:.2f}")
        self.threat_max_label.setText(f"Max: {max_val:.2f}")
        
        # Auto-apply filters on change
        self._apply_filters()
        
    def _apply_filters(self) -> None:
        """Apply current filters and update all visualizations."""
        # Force immediate update of visualizations with current filters
        self._update_visualizations()
        
    def _clear_filters(self) -> None:
        """Clear all filters and reset to default state."""
        # Reset filter controls
        self.protocol_filter.clear()
        self.src_ip_filter.clear()
        self.dst_ip_filter.clear()
        self.threat_min_slider.setValue(0)
        self.threat_max_slider.setValue(100)
        
        # Reset filter state
        self._active_filters = {
            'time_range': 300,
            'protocols': set(),
            'src_ips': set(),
            'dst_ips': set(),
            'threat_level_min': 0.0,
            'threat_level_max': 1.0
        }
        
        # Update labels
        self.threat_min_label.setText("Min: 0.0")
        self.threat_max_label.setText("Max: 1.0")
        
        # Apply cleared filters
        self._apply_filters()
        
    def _get_filtered_packets(self) -> List[PacketInfo]:
        """Get packets that match current filter criteria."""
        if not self._packets_buffer:
            return []
            
        current_time = time.time()
        time_cutoff = current_time - self._active_filters['time_range']
        
        filtered = []
        for packet in self._packets_buffer:
            # Time filter
            if packet.timestamp < time_cutoff:
                continue
                
            # Protocol filter
            if (self._active_filters['protocols'] and 
                packet.protocol.upper() not in self._active_filters['protocols']):
                continue
                
            # Source IP filter
            if (self._active_filters['src_ips'] and 
                packet.src_ip not in self._active_filters['src_ips']):
                continue
                
            # Destination IP filter  
            if (self._active_filters['dst_ips'] and
                packet.dst_ip not in self._active_filters['dst_ips']):
                continue
                
            # Threat level filter (requires AI score from packet)
            threat_score = getattr(packet, 'ai_score', 0.0)
            if (threat_score < self._active_filters['threat_level_min'] or
                threat_score > self._active_filters['threat_level_max']):
                continue
                
            filtered.append(packet)
            
        return filtered
        
    def _on_refresh_interval_changed(self, interval: int) -> None:
        """Handle refresh interval change."""
        self.update_timer.setInterval(interval * 1000)
        
    def _clear_data(self) -> None:
        """Clear all visualization data."""
        self._traffic_history.clear()
        self._packet_size_history.clear()
        self._protocol_counts.clear()
        self._geo_locations.clear()
        
        # Clear charts
        self.traffic_ax.clear()
        self.size_ax.clear()
        self.protocol_ax.clear()
        self.threat_ax.clear()
        self.ips_ax.clear()
        
        self.traffic_canvas.draw()
        self.size_canvas.draw()
        self.protocol_canvas.draw()
        self.threat_canvas.draw()
        self.ips_canvas.draw()
        
        # Clear text areas
        self.geo_text.clear()
        self.stats_text.clear()
        
    def _on_chart_scroll(self, event) -> None:
        """Handle mouse scroll for chart zooming."""
        if event.inaxes is None:
            return
            
        # Zoom in/out based on scroll direction
        scale_factor = 1.1 if event.step > 0 else 1/1.1
        
        xlim = event.inaxes.get_xlim()
        ylim = event.inaxes.get_ylim()
        
        # Get mouse position
        xdata = event.xdata
        ydata = event.ydata
        
        if xdata is not None and ydata is not None:
            # Zoom around mouse position
            x_range = (xlim[1] - xlim[0]) / 2
            y_range = (ylim[1] - ylim[0]) / 2
            
            new_x_range = x_range / scale_factor
            new_y_range = y_range / scale_factor
            
            event.inaxes.set_xlim([xdata - new_x_range, xdata + new_x_range])
            event.inaxes.set_ylim([ydata - new_y_range, ydata + new_y_range])
            
            event.canvas.draw()
            
    def _on_chart_click(self, event) -> None:
        """Handle chart click events."""
        if event.dblclick:
            # Double-click to reset zoom
            if event.inaxes is not None:
                event.inaxes.autoscale()
                event.canvas.draw()