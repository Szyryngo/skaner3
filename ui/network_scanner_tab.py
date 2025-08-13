from __future__ import annotations

from typing import List, Optional

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QProgressBar,
    QTextEdit, QLabel, QGroupBox, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.network_scanner import NetworkScanner, ScanResult
from core.utils import list_network_interfaces


class NetworkScannerTab(QWidget):
    """Network scanner tab with configuration and results display."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanner = NetworkScanner()
        self.scan_results: List[ScanResult] = []
        
        # Setup callbacks
        self.scanner.set_result_callback(self._on_scan_result)
        self.scanner.set_progress_callback(self._on_progress_update)
        self.scanner.set_completion_callback(self._on_scan_complete)
        
        self._setup_ui()
        self._load_default_settings()
        
    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal, self)
        
        # Left panel - Configuration
        config_panel = self._create_config_panel()
        splitter.addWidget(config_panel)
        
        # Right panel - Results
        results_panel = self._create_results_panel()
        splitter.addWidget(results_panel)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 1)  # Config panel
        splitter.setStretchFactor(1, 2)  # Results panel
        
        layout.addWidget(splitter)
        
    def _create_config_panel(self) -> QWidget:
        """Create configuration panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Network Configuration Group
        network_group = QGroupBox("Konfiguracja sieci")
        network_layout = QFormLayout(network_group)
        
        # Interface selection
        self.interface_combo = QComboBox()
        self._populate_interfaces()
        self.interface_combo.currentTextChanged.connect(self._on_interface_changed)
        network_layout.addRow("Interfejs:", self.interface_combo)
        
        # IP range
        self.ip_range_edit = QLineEdit()
        self.ip_range_edit.setPlaceholderText("np. 192.168.1.0/24")
        network_layout.addRow("Zakres IP:", self.ip_range_edit)
        
        # Auto-detect button
        auto_detect_btn = QPushButton("Auto-wykryj zakres")
        auto_detect_btn.clicked.connect(self._auto_detect_range)
        network_layout.addRow("", auto_detect_btn)
        
        layout.addWidget(network_group)
        
        # Scan Configuration Group
        scan_group = QGroupBox("Konfiguracja skanowania")
        scan_layout = QFormLayout(scan_group)
        
        # Scan mode
        self.scan_mode_combo = QComboBox()
        self.scan_mode_combo.addItems(["light", "heavy"])
        self.scan_mode_combo.setCurrentText("light")
        scan_layout.addRow("Tryb skanowania:", self.scan_mode_combo)
        
        # Mode description
        self.mode_description = QLabel()
        self._update_mode_description()
        self.scan_mode_combo.currentTextChanged.connect(self._update_mode_description)
        scan_layout.addRow("", self.mode_description)
        
        # Port range (for heavy scan)
        self.port_range_edit = QLineEdit()
        self.port_range_edit.setText("22,80,443,8080")
        self.port_range_edit.setPlaceholderText("np. 22,80,443,8080-8090")
        scan_layout.addRow("Porty (heavy):", self.port_range_edit)
        
        # Advanced settings
        self.max_threads_spin = QSpinBox()
        self.max_threads_spin.setRange(1, 200)
        self.max_threads_spin.setValue(50)
        scan_layout.addRow("Max wątki:", self.max_threads_spin)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 10)
        self.timeout_spin.setValue(1)
        self.timeout_spin.setSuffix(" s")
        scan_layout.addRow("Timeout:", self.timeout_spin)
        
        layout.addWidget(scan_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Skanowanie")
        self.start_btn.clicked.connect(self._start_scan)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._stop_scan)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        layout.addLayout(control_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Gotowy do skanowania")
        layout.addWidget(self.status_label)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        return panel
        
    def _create_results_panel(self) -> QWidget:
        """Create results panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "IP", "Status", "Hostname", "Otwarte porty", "Czas odpowiedzi"
        ])
        
        # Auto-resize columns
        header = self.results_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # IP
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Hostname
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Ports
        
        layout.addWidget(self.results_table)
        
        # Summary
        self.summary_label = QLabel("Wyniki: 0 hostów")
        layout.addWidget(self.summary_label)
        
        # Export button
        export_btn = QPushButton("Eksportuj wyniki")
        export_btn.clicked.connect(self._export_results)
        layout.addWidget(export_btn)
        
        return panel
        
    def _populate_interfaces(self):
        """Populate interface combo box."""
        self.interface_combo.clear()
        self.interface_combo.addItem("Auto", None)
        
        interfaces = list_network_interfaces(show_inactive=False)
        for interface in interfaces:
            if interface["is_up"] and interface["ipv4"]:
                display_name = f"{interface['name']} ({interface['type']}) - {interface['ipv4']}"
                self.interface_combo.addItem(display_name, interface["id"])
                
    def _on_interface_changed(self):
        """Handle interface selection change."""
        # Auto-detect range when interface changes
        if self.interface_combo.currentData() is not None:
            self._auto_detect_range()
            
    def _auto_detect_range(self):
        """Auto-detect network range based on selected interface."""
        interface_id = self.interface_combo.currentData()
        
        if interface_id == "":  # Auto selection
            interface_id = None
            
        detected_range = self.scanner.auto_detect_network_range(interface_id)
        self.ip_range_edit.setText(detected_range)
        
    def _update_mode_description(self):
        """Update scan mode description."""
        mode = self.scan_mode_combo.currentText()
        if mode == "light":
            desc = "Lekki: ARP/ICMP ping (szybki, minimalny ślad)"
        else:
            desc = "Twardy: skanowanie portów TCP (wolniejszy, więcej informacji)"
        self.mode_description.setText(desc)
        self.mode_description.setWordWrap(True)
        
    def _load_default_settings(self):
        """Load default scanner settings."""
        self._auto_detect_range()
        
    def _start_scan(self):
        """Start network scan."""
        # Validate input
        if not self.ip_range_edit.text().strip():
            self.status_label.setText("Błąd: Wprowadź zakres IP")
            return
            
        # Configure scanner
        self.scanner.ip_range = self.ip_range_edit.text().strip()
        self.scanner.port_range = self.port_range_edit.text().strip()
        self.scanner.scan_mode = self.scan_mode_combo.currentText()
        self.scanner.max_threads = self.max_threads_spin.value()
        self.scanner.timeout = float(self.timeout_spin.value())
        
        # Clear previous results
        self.scan_results.clear()
        self.results_table.setRowCount(0)
        self._update_summary()
        
        # Start scan
        if self.scanner.start_scan():
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("Skanowanie w toku...")
        else:
            self.status_label.setText("Błąd: Nie można rozpocząć skanowania")
            
    def _stop_scan(self):
        """Stop network scan."""
        self.scanner.stop_scan()
        self._on_scan_complete()
        
    def _on_scan_result(self, result: ScanResult):
        """Handle scan result."""
        self.scan_results.append(result)
        
        # Add to table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # IP
        self.results_table.setItem(row, 0, QTableWidgetItem(result.ip))
        
        # Status
        status_item = QTableWidgetItem("UP" if result.is_up else "DOWN")
        if result.is_up:
            status_item.setBackground(Qt.green)
        else:
            status_item.setBackground(Qt.lightGray)
        self.results_table.setItem(row, 1, status_item)
        
        # Hostname
        hostname = result.hostname or ""
        self.results_table.setItem(row, 2, QTableWidgetItem(hostname))
        
        # Open ports
        if result.open_ports:
            ports_str = ", ".join(map(str, result.open_ports))
        else:
            ports_str = ""
        self.results_table.setItem(row, 3, QTableWidgetItem(ports_str))
        
        # Response time
        if result.response_time is not None:
            time_str = f"{result.response_time:.2f}s"
        else:
            time_str = ""
        self.results_table.setItem(row, 4, QTableWidgetItem(time_str))
        
        self._update_summary()
        
    def _on_progress_update(self, current: int, total: int):
        """Handle progress update."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Skanowanie: {current}/{total} hostów")
        
    def _on_scan_complete(self):
        """Handle scan completion."""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        up_count = sum(1 for r in self.scan_results if r.is_up)
        total_count = len(self.scan_results)
        self.status_label.setText(f"Skanowanie zakończone: {up_count}/{total_count} hostów aktywnych")
        
    def _update_summary(self):
        """Update results summary."""
        total = len(self.scan_results)
        up_count = sum(1 for r in self.scan_results if r.is_up)
        down_count = total - up_count
        
        with_ports = sum(1 for r in self.scan_results if r.open_ports)
        
        summary = f"Wyniki: {total} hostów ({up_count} UP, {down_count} DOWN"
        if with_ports > 0:
            summary += f", {with_ports} z otwartymi portami"
        summary += ")"
        
        self.summary_label.setText(summary)
        
    def _export_results(self):
        """Export scan results to file."""
        if not self.scan_results:
            self.status_label.setText("Brak wyników do eksportu")
            return
            
        from PyQt5.QtWidgets import QFileDialog
        import csv
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Zapisz wyniki skanowania",
            "network_scan_results.csv",
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['IP', 'Status', 'Hostname', 'Open_Ports', 'Response_Time'])
                    
                    for result in self.scan_results:
                        writer.writerow([
                            result.ip,
                            'UP' if result.is_up else 'DOWN',
                            result.hostname or '',
                            ','.join(map(str, result.open_ports)) if result.open_ports else '',
                            f"{result.response_time:.3f}" if result.response_time else ''
                        ])
                        
                self.status_label.setText(f"Wyniki zapisane do: {filename}")
            except Exception as e:
                self.status_label.setText(f"Błąd zapisu: {str(e)}")