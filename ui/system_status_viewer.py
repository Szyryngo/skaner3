from __future__ import annotations

import threading
import time
from typing import List, Dict

import psutil
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QVBoxLayout, 
    QHBoxLayout, 
    QWidget, 
    QLabel, 
    QTableWidget, 
    QTableWidgetItem,
    QGroupBox,
    QHeaderView
)

from core.utils import list_network_interfaces
from core.system_info import get_system_info


class SystemStatusViewer(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._setup_timer()
        self._update_status()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # System metrics group
        metrics_group = QGroupBox("Parametry systemowe", self)
        metrics_layout = QVBoxLayout(metrics_group)
        
        # System metrics labels
        self.cpu_label = QLabel("CPU: --%", self)
        self.ram_label = QLabel("RAM: --%", self)
        self.uptime_label = QLabel("Uptime: --", self)
        self.threads_label = QLabel("Aktywne wątki: --", self)
        
        # Arrange metrics in a grid-like layout
        metrics_row1 = QHBoxLayout()
        metrics_row1.addWidget(self.cpu_label)
        metrics_row1.addWidget(self.ram_label)
        
        metrics_row2 = QHBoxLayout()
        metrics_row2.addWidget(self.uptime_label)
        metrics_row2.addWidget(self.threads_label)
        
        metrics_layout.addLayout(metrics_row1)
        metrics_layout.addLayout(metrics_row2)
        
        # Network interfaces group
        network_group = QGroupBox("Interfejsy sieciowe", self)
        network_layout = QVBoxLayout(network_group)
        
        # Network interfaces table
        self.interfaces_table = QTableWidget(self)
        self.interfaces_table.setColumnCount(4)
        self.interfaces_table.setHorizontalHeaderLabels([
            "Nazwa", "Status", "Typ", "Adres IPv4"
        ])
        
        # Make table headers stretch to fill width
        header = self.interfaces_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        
        # Set table properties
        self.interfaces_table.setAlternatingRowColors(True)
        self.interfaces_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.interfaces_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        network_layout.addWidget(self.interfaces_table)
        
        # Add groups to main layout
        layout.addWidget(metrics_group)
        layout.addWidget(network_group)
        
        self.setLayout(layout)

    def _setup_timer(self) -> None:
        """Setup timer for periodic updates every 3 seconds"""
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(3000)  # 3 seconds
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start()

    def _update_status(self) -> None:
        """Update all system status information"""
        self._update_system_metrics()
        self._update_network_interfaces()

    def _update_system_metrics(self) -> None:
        """Update CPU, RAM, uptime and thread count"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            self.cpu_label.setText(f"CPU: {cpu_percent:.1f}%")
            
            # RAM usage
            memory = psutil.virtual_memory()
            self.ram_label.setText(f"RAM: {memory.percent:.1f}%")
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_str = self._format_uptime(uptime_seconds)
            self.uptime_label.setText(f"Uptime: {uptime_str}")
            
            # Active threads
            thread_count = threading.active_count()
            self.threads_label.setText(f"Aktywne wątki: {thread_count}")
            
        except Exception:
            # Fallback values if any metric fails
            self.cpu_label.setText("CPU: n/a")
            self.ram_label.setText("RAM: n/a")
            self.uptime_label.setText("Uptime: n/a")
            self.threads_label.setText("Aktywne wątki: n/a")

    def _update_network_interfaces(self) -> None:
        """Update network interfaces table"""
        try:
            # Get network interfaces (including inactive ones)
            interfaces = list_network_interfaces(show_inactive=True)
            
            # Clear and resize table
            self.interfaces_table.setRowCount(len(interfaces))
            
            # Populate table
            for row, interface in enumerate(interfaces):
                # Name
                name_item = QTableWidgetItem(interface.get("name", ""))
                self.interfaces_table.setItem(row, 0, name_item)
                
                # Status
                status = "Aktywny" if interface.get("is_up", False) else "Nieaktywny"
                status_item = QTableWidgetItem(status)
                self.interfaces_table.setItem(row, 1, status_item)
                
                # Type
                type_item = QTableWidgetItem(interface.get("type", "Unknown"))
                self.interfaces_table.setItem(row, 2, type_item)
                
                # IPv4 address
                ipv4 = interface.get("ipv4", "") or "-"
                ipv4_item = QTableWidgetItem(ipv4)
                self.interfaces_table.setItem(row, 3, ipv4_item)
                
        except Exception:
            # Clear table on error
            self.interfaces_table.setRowCount(0)

    def _format_uptime(self, uptime_seconds: float) -> str:
        """Format uptime in a human-readable way"""
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"