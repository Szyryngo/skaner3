from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QComboBox, QLabel, QPushButton, QTextEdit,
    QTabWidget, QSpinBox, QCheckBox, QGroupBox,
    QScrollArea
)

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
import seaborn as sns

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
        self._ip_traffic_matrix: Dict[Tuple[str, str], int] = defaultdict(int)  # For heatmap
        self._port_usage: Dict[int, int] = defaultdict(int)  # Port usage statistics
        
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
        
        # Protocol chart type selector
        controls_layout.addWidget(QLabel("Protokoły:"))
        self.protocol_chart_type = QComboBox()
        self.protocol_chart_type.addItems(["Wykres kołowy", "Wykres słupkowy"])
        self.protocol_chart_type.currentTextChanged.connect(self._update_protocol_chart)
        controls_layout.addWidget(self.protocol_chart_type)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Main visualization area with tabs
        self.viz_tabs = QTabWidget()
        
        # Tab 1: Time Series Charts
        time_series_widget = QWidget()
        time_series_layout = QVBoxLayout(time_series_widget)
        
        # Traffic intensity chart
        self.traffic_figure = Figure(figsize=(10, 4))
        self.traffic_canvas = FigureCanvas(self.traffic_figure)
        self.traffic_canvas.mpl_connect('scroll_event', self._on_chart_scroll)
        self.traffic_canvas.mpl_connect('button_press_event', self._on_chart_click)
        self.traffic_ax = self.traffic_figure.add_subplot(111)
        self.traffic_ax.set_title("Natężenie ruchu sieciowego")
        self.traffic_ax.set_xlabel("Czas")
        self.traffic_ax.set_ylabel("Pakiety/sek")
        time_series_layout.addWidget(self.traffic_canvas)
        
        # Data size chart
        self.size_figure = Figure(figsize=(10, 4))
        self.size_canvas = FigureCanvas(self.size_figure)
        self.size_canvas.mpl_connect('scroll_event', self._on_chart_scroll)
        self.size_canvas.mpl_connect('button_press_event', self._on_chart_click)
        self.size_ax = self.size_figure.add_subplot(111)
        self.size_ax.set_title("Rozmiar przesyłanych danych")
        self.size_ax.set_xlabel("Czas")
        self.size_ax.set_ylabel("Bajty/sek")
        time_series_layout.addWidget(self.size_canvas)
        
        self.viz_tabs.addTab(time_series_widget, "Ruch w czasie")
        
        # Tab 2: Protocol Analysis
        protocol_widget = QWidget()
        protocol_layout = QVBoxLayout(protocol_widget)
        
        # Protocol distribution chart
        self.protocol_figure = Figure(figsize=(8, 6))
        self.protocol_canvas = FigureCanvas(self.protocol_figure)
        self.protocol_ax = self.protocol_figure.add_subplot(111)
        self.protocol_ax.set_title("Rozkład protokołów")
        protocol_layout.addWidget(self.protocol_canvas)
        
        self.viz_tabs.addTab(protocol_widget, "Protokoły")
        
        # Tab 3: IP Traffic Heatmap
        heatmap_widget = QWidget()
        heatmap_layout = QVBoxLayout(heatmap_widget)
        
        # IP traffic heatmap
        self.heatmap_figure = Figure(figsize=(10, 8))
        self.heatmap_canvas = FigureCanvas(self.heatmap_figure)
        self.heatmap_ax = self.heatmap_figure.add_subplot(111)
        self.heatmap_ax.set_title("Mapa ruchu IP (źródło → cel)")
        heatmap_layout.addWidget(self.heatmap_canvas)
        
        self.viz_tabs.addTab(heatmap_widget, "Mapa ruchu IP")
        
        # Tab 4: Network Statistics
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        
        # Left side: Top talkers chart
        top_talkers_group = QGroupBox("Top 10 źródeł IP")
        top_talkers_layout = QVBoxLayout(top_talkers_group)
        self.top_talkers_figure = Figure(figsize=(6, 4))
        self.top_talkers_canvas = FigureCanvas(self.top_talkers_figure)
        self.top_talkers_ax = self.top_talkers_figure.add_subplot(111)
        top_talkers_layout.addWidget(self.top_talkers_canvas)
        stats_layout.addWidget(top_talkers_group)
        
        # Right side: Port usage
        port_usage_group = QGroupBox("Wykorzystanie portów")
        port_usage_layout = QVBoxLayout(port_usage_group)
        self.port_usage_figure = Figure(figsize=(6, 4))
        self.port_usage_canvas = FigureCanvas(self.port_usage_figure)
        self.port_usage_ax = self.port_usage_figure.add_subplot(111)
        port_usage_layout.addWidget(self.port_usage_canvas)
        stats_layout.addWidget(port_usage_group)
        
        self.viz_tabs.addTab(stats_widget, "Statystyki")
        
        # Tab 5: Geolocation
        geo_widget = QWidget()
        geo_layout = QVBoxLayout(geo_widget)
        
        # Geolocation info
        geo_layout.addWidget(QLabel("Informacje geolokalizacyjne:"))
        self.geo_text = QTextEdit()
        self.geo_text.setReadOnly(True)
        geo_layout.addWidget(self.geo_text)
        
        # Network statistics
        geo_layout.addWidget(QLabel("Statystyki sieciowe:"))
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        geo_layout.addWidget(self.stats_text)
        
        self.viz_tabs.addTab(geo_widget, "Geolokalizacja")
        
        layout.addWidget(self.viz_tabs)
        
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
                
                # Update IP traffic matrix for heatmap
                if packet.src_ip != "?" and packet.dst_ip != "?":
                    src_key = self._normalize_ip_for_heatmap(packet.src_ip)
                    dst_key = self._normalize_ip_for_heatmap(packet.dst_ip)
                    self._ip_traffic_matrix[(src_key, dst_key)] += 1
                
                # Update port usage statistics
                if packet.dst_port:
                    self._port_usage[packet.dst_port] += 1
                if packet.src_port:
                    self._port_usage[packet.src_port] += 1
        
        # Store data point
        timestamp = datetime.fromtimestamp(current_time)
        self._traffic_history.append((timestamp, packets_count))
        self._packet_size_history.append((timestamp, bytes_count))
        
        self._last_update_time = current_time
        
    def _normalize_ip_for_heatmap(self, ip: str) -> str:
        """Normalize IP addresses for heatmap display."""
        # Group private IPs into categories for better visualization
        if ip.startswith("192.168."):
            return "192.168.x.x"
        elif ip.startswith("10."):
            return "10.x.x.x"
        elif ip.startswith("172.16.") or ip.startswith("172.17.") or ip.startswith("172.18.") or ip.startswith("172.19."):
            return "172.16-31.x.x"
        elif ip.startswith("127."):
            return "localhost"
        else:
            # For public IPs, keep the first two octets for privacy
            parts = ip.split(".")
            if len(parts) >= 2:
                return f"{parts[0]}.{parts[1]}.x.x"
            return ip
        
    def _update_visualizations(self) -> None:
        """Update all visualization components."""
        self._update_traffic_chart()
        self._update_size_chart()
        self._update_protocol_chart()
        self._update_ip_heatmap()
        self._update_top_talkers_chart()
        self._update_port_usage_chart()
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
        """Update the protocol distribution chart (pie or bar chart)."""
        if not self._protocol_counts:
            return
            
        self.protocol_ax.clear()
        
        protocols = list(self._protocol_counts.keys())
        counts = list(self._protocol_counts.values())
        
        # Only show top 8 protocols
        if len(protocols) > 8:
            # Sort by count and take top 8
            protocol_data = sorted(zip(protocols, counts), key=lambda x: x[1], reverse=True)
            protocols = [p[0] for p in protocol_data[:8]]
            counts = [p[1] for p in protocol_data[:8]]
            
            # Add "Others" category
            other_count = sum(p[1] for p in protocol_data[8:])
            if other_count > 0:
                protocols.append("Inne")
                counts.append(other_count)
        
        chart_type = self.protocol_chart_type.currentText()
        
        if chart_type == "Wykres kołowy":
            # Pie chart
            colors = plt.cm.Set3(np.linspace(0, 1, len(protocols)))
            self.protocol_ax.pie(counts, labels=protocols, autopct='%1.1f%%', colors=colors)
            self.protocol_ax.set_title("Rozkład protokołów")
        else:
            # Bar chart
            colors = plt.cm.viridis(np.linspace(0, 1, len(protocols)))
            bars = self.protocol_ax.bar(protocols, counts, color=colors)
            self.protocol_ax.set_title("Rozkład protokołów")
            self.protocol_ax.set_xlabel("Protokół")
            self.protocol_ax.set_ylabel("Liczba pakietów")
            
            # Add value labels on bars
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                self.protocol_ax.text(bar.get_x() + bar.get_width()/2., height + max(counts)*0.01,
                                    f'{count}', ha='center', va='bottom')
            
            # Rotate x-axis labels for better readability
            plt.setp(self.protocol_ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        self.protocol_figure.tight_layout()
        self.protocol_canvas.draw()
        
    def _update_ip_heatmap(self) -> None:
        """Update the IP traffic heatmap."""
        if not self._ip_traffic_matrix:
            return
            
        self.heatmap_ax.clear()
        
        # Get top IP pairs for better visualization
        sorted_pairs = sorted(self._ip_traffic_matrix.items(), key=lambda x: x[1], reverse=True)[:20]
        
        if not sorted_pairs:
            return
        
        # Create matrix for heatmap
        sources = sorted(set([pair[0][0] for pair in sorted_pairs]))
        destinations = sorted(set([pair[0][1] for pair in sorted_pairs]))
        
        if len(sources) < 2 or len(destinations) < 2:
            self.heatmap_ax.text(0.5, 0.5, 'Zbyt mało danych dla mapy cieplnej', 
                               ha='center', va='center', transform=self.heatmap_ax.transAxes)
            self.heatmap_canvas.draw()
            return
        
        # Create the matrix
        matrix = np.zeros((len(sources), len(destinations)))
        for (src, dst), count in sorted_pairs:
            if src in sources and dst in destinations:
                src_idx = sources.index(src)
                dst_idx = destinations.index(dst)
                matrix[src_idx][dst_idx] = count
        
        # Create heatmap using seaborn for better styling
        sns.heatmap(matrix, 
                   xticklabels=destinations,
                   yticklabels=sources,
                   annot=True, 
                   fmt='g',
                   cmap='YlOrRd',
                   ax=self.heatmap_ax,
                   cbar_kws={'label': 'Liczba pakietów'})
        
        self.heatmap_ax.set_title("Mapa ruchu IP (źródło → cel)")
        self.heatmap_ax.set_xlabel("IP docelowe")
        self.heatmap_ax.set_ylabel("IP źródłowe")
        
        # Rotate labels for better readability
        plt.setp(self.heatmap_ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        plt.setp(self.heatmap_ax.yaxis.get_majorticklabels(), rotation=0)
        
        self.heatmap_figure.tight_layout()
        self.heatmap_canvas.draw()
        
    def _update_top_talkers_chart(self) -> None:
        """Update the top IP sources chart."""
        if not self._packets_buffer:
            return
            
        self.top_talkers_ax.clear()
        
        # Count packets by source IP
        ip_counts = defaultdict(int)
        for packet in self._packets_buffer[-1000:]:  # Last 1000 packets
            if packet.src_ip != "?":
                normalized_ip = self._normalize_ip_for_heatmap(packet.src_ip)
                ip_counts[normalized_ip] += 1
        
        if not ip_counts:
            return
            
        # Get top 10
        top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ips, counts = zip(*top_ips)
        
        # Create horizontal bar chart
        y_pos = np.arange(len(ips))
        colors = plt.cm.viridis(np.linspace(0, 1, len(ips)))
        bars = self.top_talkers_ax.barh(y_pos, counts, color=colors)
        
        self.top_talkers_ax.set_yticks(y_pos)
        self.top_talkers_ax.set_yticklabels(ips)
        self.top_talkers_ax.set_xlabel("Liczba pakietów")
        self.top_talkers_ax.set_title("Top 10 źródeł IP")
        
        # Add value labels
        for i, (bar, count) in enumerate(zip(bars, counts)):
            width = bar.get_width()
            self.top_talkers_ax.text(width + max(counts)*0.01, bar.get_y() + bar.get_height()/2,
                                   f'{count}', ha='left', va='center')
        
        self.top_talkers_figure.tight_layout()
        self.top_talkers_canvas.draw()
        
    def _update_port_usage_chart(self) -> None:
        """Update the port usage chart."""
        if not self._port_usage:
            return
            
        self.port_usage_ax.clear()
        
        # Get top 10 ports
        top_ports = sorted(self._port_usage.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if not top_ports:
            return
            
        ports, counts = zip(*top_ports)
        port_labels = [self._get_port_name(port) for port in ports]
        
        # Create bar chart
        colors = plt.cm.plasma(np.linspace(0, 1, len(ports)))
        bars = self.port_usage_ax.bar(range(len(ports)), counts, color=colors)
        
        self.port_usage_ax.set_xticks(range(len(ports)))
        self.port_usage_ax.set_xticklabels(port_labels, rotation=45, ha='right')
        self.port_usage_ax.set_ylabel("Liczba pakietów")
        self.port_usage_ax.set_title("Top 10 portów")
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            self.port_usage_ax.text(bar.get_x() + bar.get_width()/2., height + max(counts)*0.01,
                                  f'{count}', ha='center', va='bottom')
        
        self.port_usage_figure.tight_layout()
        self.port_usage_canvas.draw()
        
    def _get_port_name(self, port: int) -> str:
        """Get human-readable port name."""
        common_ports = {
            80: "HTTP (80)",
            443: "HTTPS (443)",
            53: "DNS (53)",
            22: "SSH (22)",
            21: "FTP (21)",
            25: "SMTP (25)",
            110: "POP3 (110)",
            143: "IMAP (143)",
            993: "IMAPS (993)",
            995: "POP3S (995)",
            3389: "RDP (3389)",
            1433: "MSSQL (1433)",
            3306: "MySQL (3306)",
            5432: "PostgreSQL (5432)",
        }
        return common_ports.get(port, f"Port {port}")
        
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
        self._ip_traffic_matrix.clear()
        self._port_usage.clear()
        
        # Clear charts
        self.traffic_ax.clear()
        self.size_ax.clear()
        self.protocol_ax.clear()
        self.heatmap_ax.clear()
        self.top_talkers_ax.clear()
        self.port_usage_ax.clear()
        
        self.traffic_canvas.draw()
        self.size_canvas.draw()
        self.protocol_canvas.draw()
        self.heatmap_canvas.draw()
        self.top_talkers_canvas.draw()
        self.port_usage_canvas.draw()
        
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