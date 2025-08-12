from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QComboBox, QLabel, QPushButton, QTextEdit,
    QTabWidget, QSpinBox
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
        
        # Time tracking
        self._last_update_time = time.time()
        self._current_second_count = 0
        self._current_second_bytes = 0
        
        self._setup_ui()
        self._setup_timers()
        
    def _setup_ui(self) -> None:
        """Initialize the user interface components."""
        layout = QVBoxLayout(self)
        
        # Control panel
        controls_layout = QHBoxLayout()
        
        # Time range selector
        controls_layout.addWidget(QLabel("Zakres czasu:"))
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["1 minuta", "5 minut", "15 minut", "30 minut", "1 godzina"])
        self.time_range_combo.setCurrentText("5 minut")
        self.time_range_combo.currentTextChanged.connect(self._on_time_range_changed)
        controls_layout.addWidget(self.time_range_combo)
        
        # Refresh interval
        controls_layout.addWidget(QLabel("Odświeżanie (s):"))
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(1, 60)
        self.refresh_interval_spin.setValue(2)
        self.refresh_interval_spin.valueChanged.connect(self._on_refresh_interval_changed)
        controls_layout.addWidget(self.refresh_interval_spin)
        
        # Clear data button
        self.clear_button = QPushButton("Wyczyść dane")
        self.clear_button.clicked.connect(self._clear_data)
        controls_layout.addWidget(self.clear_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
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
        
        # Right side: Geolocation and stats
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        # Protocol distribution chart
        self.protocol_figure = Figure(figsize=(4, 4))
        self.protocol_canvas = FigureCanvas(self.protocol_figure)
        self.protocol_ax = self.protocol_figure.add_subplot(111)
        self.protocol_ax.set_title("Rozkład protokołów")
        info_layout.addWidget(self.protocol_canvas)
        
        # Geolocation info
        info_layout.addWidget(QLabel("Informacje geolokalizacyjne:"))
        self.geo_text = QTextEdit()
        self.geo_text.setMaximumHeight(200)
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
        
        # Count packets and bytes in the last second
        packets_count = 0
        bytes_count = 0
        
        for packet in self._packets_buffer:
            if packet.timestamp >= self._last_update_time:
                packets_count += 1
                bytes_count += packet.length
                
                # Update protocol counts
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
        if not self._protocol_counts:
            return
            
        self.protocol_ax.clear()
        
        protocols = list(self._protocol_counts.keys())
        counts = list(self._protocol_counts.values())
        
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
        
    def _update_geolocation_info(self) -> None:
        """Update geolocation information text."""
        if not self._packets_buffer:
            return
            
        # Get unique IPs from recent packets (last 100)
        recent_packets = self._packets_buffer[-100:] if len(self._packets_buffer) > 100 else self._packets_buffer
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
        if not self._packets_buffer:
            return
            
        total_packets = len(self._packets_buffer)
        total_bytes = sum(p.length for p in self._packets_buffer)
        
        # Calculate rates from recent data
        current_time = time.time()
        recent_packets = [p for p in self._packets_buffer if current_time - p.timestamp <= 60]  # Last minute
        
        if recent_packets:
            packets_per_minute = len(recent_packets)
            bytes_per_minute = sum(p.length for p in recent_packets)
            avg_packet_size = bytes_per_minute / len(recent_packets) if recent_packets else 0
        else:
            packets_per_minute = 0
            bytes_per_minute = 0
            avg_packet_size = 0
        
        stats_text = f"""Łączna liczba pakietów: {total_packets}
Łączny rozmiar danych: {total_bytes:,} bajtów ({total_bytes / 1024 / 1024:.2f} MB)
Pakiety/minutę: {packets_per_minute}
Bajty/minutę: {bytes_per_minute:,}
Średni rozmiar pakietu: {avg_packet_size:.1f} bajtów
Unikalne protokoły: {len(self._protocol_counts)}"""
        
        self.stats_text.setPlainText(stats_text)
        
    def _on_time_range_changed(self, range_text: str) -> None:
        """Handle time range selection change."""
        # Map text to seconds
        range_map = {
            "1 minuta": 60,
            "5 minut": 300,
            "15 minut": 900,
            "30 minut": 1800,
            "1 godzina": 3600
        }
        
        seconds = range_map.get(range_text, 300)
        max_points = seconds  # One point per second
        
        # Update deque max length
        self._traffic_history = deque(self._traffic_history, maxlen=max_points)
        self._packet_size_history = deque(self._packet_size_history, maxlen=max_points)
        
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
        
        self.traffic_canvas.draw()
        self.size_canvas.draw()
        self.protocol_canvas.draw()
        
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