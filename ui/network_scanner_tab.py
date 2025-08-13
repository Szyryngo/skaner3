from __future__ import annotations

import time
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLineEdit, QTextEdit, QComboBox, QPushButton, QProgressBar,
    QTableWidget, QTableWidgetItem, QLabel, QGroupBox, QCheckBox,
    QSpinBox, QSplitter, QHeaderView, QAbstractItemView, QMenu,
    QAction, QFileDialog, QMessageBox
)

from core.network_scanner import NetworkScanner, ScanMode, HostInfo, ScanProgress


class NetworkScannerTab(QWidget):
    """
    Zakładka GUI dla skanera sieciowego.
    
    Funkcjonalności:
    - Konfiguracja zakresów IP
    - Wybór portów i trybu skanowania
    - Kontrola start/stop z paskiem postępu
    - Prezentacja wyników na żywo
    - Eksport wyników
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        # Scanner
        self.scanner = NetworkScanner()
        self.scanner.on_host_found = self._on_host_found
        self.scanner.on_progress_update = self._on_progress_update
        self.scanner.on_scan_complete = self._on_scan_complete
        self.scanner.on_error = self._on_error
        
        # UI State
        self._scan_start_time: Optional[float] = None
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Konfiguruje interfejs użytkownika."""
        layout = QVBoxLayout(self)
        
        # Panel konfiguracji
        config_group = self._create_config_panel()
        layout.addWidget(config_group)
        
        # Panel kontroli
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # Panel wyników
        results_panel = self._create_results_panel()
        layout.addWidget(results_panel)
        
        self.setLayout(layout)

    def _create_config_panel(self) -> QGroupBox:
        """Tworzy panel konfiguracji skanowania."""
        group = QGroupBox("Konfiguracja skanowania")
        layout = QFormLayout()
        
        # Zakres IP
        self.ip_ranges_edit = QTextEdit()
        self.ip_ranges_edit.setMaximumHeight(80)
        self.ip_ranges_edit.setPlaceholderText(
            "Wprowadź zakresy IP (po jednym w linii):\n"
            "192.168.1.0/24\n"
            "10.0.0.1-10.0.0.50\n"
            "172.16.1.10"
        )
        layout.addRow("Zakresy IP:", self.ip_ranges_edit)
        
        # Tryb skanowania
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Light (ping + podstawowe porty)", "Hard (pełne skanowanie portów)"])
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        layout.addRow("Tryb:", self.mode_combo)
        
        # Porty
        ports_layout = QHBoxLayout()
        
        self.ports_preset_combo = QComboBox()
        self.ports_preset_combo.addItems([
            "Podstawowe (21,22,23,25,53,80,443...)",
            "Web (80,443,8080,8443)",
            "Mail (25,110,143,993,995)",
            "Custom"
        ])
        self.ports_preset_combo.currentTextChanged.connect(self._on_ports_preset_changed)
        ports_layout.addWidget(self.ports_preset_combo)
        
        self.custom_ports_edit = QLineEdit()
        self.custom_ports_edit.setPlaceholderText("np. 22,80,443 lub 1-1000")
        self.custom_ports_edit.setEnabled(False)
        ports_layout.addWidget(self.custom_ports_edit)
        
        layout.addRow("Porty:", ports_layout)
        
        # Opcje
        options_layout = QHBoxLayout()
        
        self.resolve_hostnames_cb = QCheckBox("Resolwuj nazwy hostów")
        self.resolve_hostnames_cb.setChecked(True)
        options_layout.addWidget(self.resolve_hostnames_cb)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setMinimum(1)
        self.timeout_spin.setMaximum(30)
        self.timeout_spin.setValue(2)
        self.timeout_spin.setSuffix(" s")
        options_layout.addWidget(QLabel("Timeout:"))
        options_layout.addWidget(self.timeout_spin)
        
        self.threads_spin = QSpinBox()
        self.threads_spin.setMinimum(1)
        self.threads_spin.setMaximum(200)
        self.threads_spin.setValue(50)
        options_layout.addWidget(QLabel("Wątki:"))
        options_layout.addWidget(self.threads_spin)
        
        options_layout.addStretch()
        layout.addRow("Opcje:", options_layout)
        
        group.setLayout(layout)
        return group

    def _create_control_panel(self) -> QWidget:
        """Tworzy panel kontroli skanowania."""
        widget = QWidget()
        layout = QHBoxLayout()
        
        # Przyciski kontroli
        self.start_button = QPushButton("🚀 Start Scan")
        self.start_button.setStyleSheet("QPushButton { font-weight: bold; }")
        layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)
        
        # Pasek postępu
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Gotowy do skanowania")
        self.progress_label.setStyleSheet("color: gray; font-size: 11px;")
        progress_layout.addWidget(self.progress_label)
        
        layout.addLayout(progress_layout, 1)  # Rozciągnij pasek postępu
        
        # Export button
        self.export_button = QPushButton("💾 Export")
        self.export_button.setEnabled(False)
        layout.addWidget(self.export_button)
        
        widget.setLayout(layout)
        return widget

    def _create_results_panel(self) -> QWidget:
        """Tworzy panel wyników skanowania."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Statystyki
        stats_layout = QHBoxLayout()
        
        self.stats_hosts = QLabel("Hosty: 0/0")
        self.stats_alive = QLabel("Aktywne: 0")
        self.stats_ports = QLabel("Otwarte porty: 0")
        self.stats_time = QLabel("Czas: 0s")
        
        for label in [self.stats_hosts, self.stats_alive, self.stats_ports, self.stats_time]:
            label.setStyleSheet("font-weight: bold; margin: 5px;")
            stats_layout.addWidget(label)
            
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Tabela wyników
        self.results_table = QTableWidget(0, 6)
        self.results_table.setHorizontalHeaderLabels([
            "IP Address", "Hostname", "Status", "Response Time", "Open Ports", "Last Seen"
        ])
        
        # Konfiguracja tabeli
        header = self.results_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # IP
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Hostname
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Response Time
        header.setSectionResizeMode(4, QHeaderView.Stretch)           # Open Ports
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Last Seen
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSortingEnabled(True)
        self.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.results_table)
        
        widget.setLayout(layout)
        return widget

    def _connect_signals(self) -> None:
        """Łączy sygnały z slotami."""
        self.start_button.clicked.connect(self._start_scan)
        self.stop_button.clicked.connect(self._stop_scan)
        self.export_button.clicked.connect(self._export_results)
        
        # Timer do aktualizacji czasu
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self._update_time_display)
        self.time_timer.setInterval(1000)  # Co sekundę

    def _on_mode_changed(self, mode_text: str) -> None:
        """Obsługuje zmianę trybu skanowania."""
        if "Hard" in mode_text:
            self.scanner.mode = ScanMode.HARD
            # W trybie hard wyłącz presets portów i pozwól na custom
            self.ports_preset_combo.setCurrentText("Custom")
            self.custom_ports_edit.setText("1-1024")
        else:
            self.scanner.mode = ScanMode.LIGHT

    def _on_ports_preset_changed(self, preset: str) -> None:
        """Obsługuje zmianę presetu portów."""
        if preset == "Custom":
            self.custom_ports_edit.setEnabled(True)
        else:
            self.custom_ports_edit.setEnabled(False)
            
            if "Web" in preset:
                self.custom_ports_edit.setText("80,443,8080,8443")
            elif "Mail" in preset:
                self.custom_ports_edit.setText("25,110,143,993,995")
            else:  # Podstawowe
                self.custom_ports_edit.setText("21,22,23,25,53,80,110,443")

    def _start_scan(self) -> None:
        """Rozpoczyna skanowanie."""
        # Walidacja danych wejściowych
        ip_ranges_text = self.ip_ranges_edit.toPlainText().strip()
        if not ip_ranges_text:
            QMessageBox.warning(self, "Błąd", "Wprowadź zakresy IP do skanowania.")
            return
            
        ip_ranges = [line.strip() for line in ip_ranges_text.split('\n') if line.strip()]
        
        # Parsowanie portów
        ports = self._parse_ports()
        if ports is None:
            QMessageBox.warning(self, "Błąd", "Nieprawidłowy format portów.")
            return
            
        # Konfiguracja scannera
        self.scanner.timeout = float(self.timeout_spin.value())
        self.scanner.max_threads = self.threads_spin.value()
        
        # UI state
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.export_button.setEnabled(False)
        
        # Wyczyść poprzednie wyniki
        self.results_table.setRowCount(0)
        self._update_stats()
        
        # Start timing
        self._scan_start_time = time.time()
        self.time_timer.start()
        
        # Rozpocznij skanowanie
        self.scanner.start_scan(
            ip_ranges=ip_ranges,
            ports=ports,
            resolve_hostnames=self.resolve_hostnames_cb.isChecked()
        )

    def _stop_scan(self) -> None:
        """Zatrzymuje skanowanie."""
        self.scanner.stop_scan()
        self._scan_complete()

    def _parse_ports(self) -> Optional[List[int]]:
        """Parsuje porty z UI."""
        if not self.custom_ports_edit.isEnabled():
            return None  # Użyj domyślnych dla trybu
            
        ports_text = self.custom_ports_edit.text().strip()
        if not ports_text:
            return None
            
        ports = []
        try:
            for part in ports_text.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = part.split('-', 1)
                    ports.extend(range(int(start), int(end) + 1))
                else:
                    ports.append(int(part))
            return sorted(set(ports))  # Usuń duplikaty i posortuj
        except ValueError:
            return None

    def _on_host_found(self, host: HostInfo) -> None:
        """Callback wywoływany gdy znaleziono host."""
        # Znajdź lub dodaj wiersz dla tego hosta
        row = self._find_host_row(host.ip)
        if row == -1:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
        # Aktualizuj dane w tabeli
        self._update_host_row(row, host)
        self._update_stats()

    def _find_host_row(self, ip: str) -> int:
        """Znajduje wiersz dla danego IP."""
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item and item.text() == ip:
                return row
        return -1

    def _update_host_row(self, row: int, host: HostInfo) -> None:
        """Aktualizuje wiersz w tabeli wyników."""
        # IP Address
        ip_item = QTableWidgetItem(host.ip)
        self.results_table.setItem(row, 0, ip_item)
        
        # Hostname
        hostname_item = QTableWidgetItem(host.hostname or "-")
        self.results_table.setItem(row, 1, hostname_item)
        
        # Status
        status_item = QTableWidgetItem("🟢 Alive" if host.is_alive else "🔴 Dead")
        if host.is_alive:
            status_item.setBackground(Qt.green)
        self.results_table.setItem(row, 2, status_item)
        
        # Response Time
        response_time = f"{host.response_time:.1f} ms" if host.response_time else "-"
        time_item = QTableWidgetItem(response_time)
        self.results_table.setItem(row, 3, time_item)
        
        # Open Ports
        ports_text = ", ".join(map(str, sorted(host.open_ports))) if host.open_ports else "-"
        ports_item = QTableWidgetItem(ports_text)
        if host.open_ports:
            ports_item.setBackground(Qt.yellow)
        self.results_table.setItem(row, 4, ports_item)
        
        # Last Seen
        last_seen = time.strftime("%H:%M:%S", time.localtime(host.last_seen)) if host.last_seen else "-"
        seen_item = QTableWidgetItem(last_seen)
        self.results_table.setItem(row, 5, seen_item)

    def _on_progress_update(self, progress: ScanProgress) -> None:
        """Callback wywoływany przy aktualizacji postępu."""
        # Pasek postępu
        total_work = progress.hosts_total + progress.ports_total
        done_work = progress.hosts_scanned + progress.ports_scanned
        
        if total_work > 0:
            percent = int((done_work / total_work) * 100)
            self.progress_bar.setValue(percent)
            
        # Etykieta postępu
        status_parts = []
        if progress.current_target:
            status_parts.append(f"Cel: {progress.current_target}")
        if progress.hosts_scanned > 0:
            status_parts.append(f"Hosty: {progress.hosts_scanned}/{progress.hosts_total}")
        if progress.ports_scanned > 0:
            status_parts.append(f"Porty: {progress.ports_scanned}/{progress.ports_total}")
        if progress.estimated_remaining > 0:
            status_parts.append(f"Pozostało: {progress.estimated_remaining:.0f}s")
            
        self.progress_label.setText(" | ".join(status_parts))
        
        # Aktualizuj statystyki
        self._update_stats()

    def _on_scan_complete(self) -> None:
        """Callback wywoływany po zakończeniu skanowania."""
        self._scan_complete()

    def _on_error(self, error_message: str) -> None:
        """Callback wywoływany przy błędzie."""
        QMessageBox.critical(self, "Błąd skanowania", error_message)
        self._scan_complete()

    def _scan_complete(self) -> None:
        """Wspólna logika zakończenia skanowania."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.export_button.setEnabled(True)
        
        self.progress_bar.setValue(100)
        self.progress_label.setText("Skanowanie zakończone")
        self.time_timer.stop()

    def _update_stats(self) -> None:
        """Aktualizuje statystyki."""
        total_hosts = len(self.scanner.hosts)
        alive_hosts = len([h for h in self.scanner.hosts.values() if h.is_alive])
        total_open_ports = sum(len(h.open_ports) for h in self.scanner.hosts.values())
        
        progress = self.scanner.progress
        self.stats_hosts.setText(f"Hosty: {progress.hosts_scanned}/{progress.hosts_total}")
        self.stats_alive.setText(f"Aktywne: {alive_hosts}")
        self.stats_ports.setText(f"Otwarte porty: {total_open_ports}")

    def _update_time_display(self) -> None:
        """Aktualizuje wyświetlanie czasu."""
        if self._scan_start_time:
            elapsed = time.time() - self._scan_start_time
            self.stats_time.setText(f"Czas: {elapsed:.0f}s")

    def _show_context_menu(self, position) -> None:
        """Pokazuje menu kontekstowe dla tabeli."""
        if self.results_table.itemAt(position) is None:
            return
            
        menu = QMenu(self)
        
        copy_ip_action = QAction("📋 Kopiuj IP", self)
        copy_ip_action.triggered.connect(self._copy_selected_ip)
        menu.addAction(copy_ip_action)
        
        copy_hostname_action = QAction("📋 Kopiuj hostname", self)
        copy_hostname_action.triggered.connect(self._copy_selected_hostname)
        menu.addAction(copy_hostname_action)
        
        menu.addSeparator()
        
        rescan_action = QAction("🔄 Reskanuj host", self)
        rescan_action.triggered.connect(self._rescan_selected_host)
        menu.addAction(rescan_action)
        
        menu.exec_(self.results_table.mapToGlobal(position))

    def _copy_selected_ip(self) -> None:
        """Kopiuje IP wybranego hosta."""
        row = self.results_table.currentRow()
        if row >= 0:
            ip_item = self.results_table.item(row, 0)
            if ip_item:
                from PyQt5.QtWidgets import QApplication
                QApplication.clipboard().setText(ip_item.text())

    def _copy_selected_hostname(self) -> None:
        """Kopiuje hostname wybranego hosta."""
        row = self.results_table.currentRow()
        if row >= 0:
            hostname_item = self.results_table.item(row, 1)
            if hostname_item and hostname_item.text() != "-":
                from PyQt5.QtWidgets import QApplication
                QApplication.clipboard().setText(hostname_item.text())

    def _rescan_selected_host(self) -> None:
        """Reskanuje wybrany host."""
        # TODO: Implementacja reskanowania pojedynczego hosta
        QMessageBox.information(self, "Info", "Funkcja reskanowania pojedynczego hosta będzie dostępna w przyszłej wersji.")

    def _export_results(self) -> None:
        """Eksportuje wyniki do pliku."""
        if not self.scanner.hosts:
            QMessageBox.information(self, "Info", "Brak wyników do eksportu.")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Eksportuj wyniki skanowania",
            f"scan_results_{int(time.time())}.csv",
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if filename:
            try:
                self._save_results_to_csv(filename)
                QMessageBox.information(self, "Sukces", f"Wyniki zostały zapisane do:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać pliku:\n{e}")

    def _save_results_to_csv(self, filename: str) -> None:
        """Zapisuje wyniki do pliku CSV."""
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Nagłówki
            writer.writerow([
                "IP Address", "Hostname", "Is Alive", "Response Time (ms)",
                "Open Ports", "Last Seen"
            ])
            
            # Dane
            for host in self.scanner.hosts.values():
                writer.writerow([
                    host.ip,
                    host.hostname or "",
                    "Yes" if host.is_alive else "No",
                    f"{host.response_time:.1f}" if host.response_time else "",
                    ",".join(map(str, sorted(host.open_ports))) if host.open_ports else "",
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(host.last_seen)) if host.last_seen else ""
                ])