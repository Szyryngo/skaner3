from __future__ import annotations

from typing import Dict, List, Optional, Set
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QHeaderView,
    QHBoxLayout,
    QLineEdit,
    QMenu,
    QAction,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QVBoxLayout,
    QLabel,
)

from core.utils import PacketInfo, NetworkDevice, format_timestamp_human, now_timestamp, extract_device_info_from_packet, resolve_hostname, get_oui_vendor


class NetworkDevicesViewer(QWidget):
    """Widget do wyświetlania urządzeń wykrytych w sieci"""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        # Słownik urządzeń: ip_address -> NetworkDevice
        self._devices: Dict[str, NetworkDevice] = {}
        
        # Interfejs użytkownika
        self._setup_ui()
        
        # Timer do odświeżania tabeli
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(2000)  # Odświeżaj co 2 sekundy
        self._refresh_timer.timeout.connect(self._refresh_table)
        self._refresh_timer.start()

    def _setup_ui(self) -> None:
        """Konfiguracja interfejsu użytkownika"""
        
        # Filtry
        filter_layout = QHBoxLayout()
        
        self.filter_text = QLineEdit(self)
        self.filter_text.setPlaceholderText("Szukaj: IP, MAC, hostname, vendor...")
        self.filter_text.setClearButtonEnabled(True)
        self.filter_text.textChanged.connect(self._apply_filters)
        
        self.filter_protocol = QComboBox(self)
        self.filter_protocol.addItems(["ALL", "TCP", "UDP", "IP", "OTHER"])
        self.filter_protocol.currentIndexChanged.connect(self._apply_filters)
        
        filter_layout.addWidget(QLabel("Filtr:"))
        filter_layout.addWidget(self.filter_text)
        filter_layout.addWidget(QLabel("Protokół:"))
        filter_layout.addWidget(self.filter_protocol)
        filter_layout.addStretch()
        
        # Tabela urządzeń
        self.table = QTableWidget(0, 7, self)
        self.table.setHorizontalHeaderLabels([
            "Adres IP", "Adres MAC", "Hostname", "Vendor (OUI)", 
            "User-Agent", "Protokoły", "Ostatnia aktywność"
        ])
        
        # Konfiguracja tabeli
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Dopasowanie kolumn
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # IP
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # MAC
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Hostname
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Vendor
        header.setSectionResizeMode(4, QHeaderView.Stretch)           # User-Agent
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Protokoły
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Czas
        
        # Menu kontekstowe
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Layout główny
        layout = QVBoxLayout(self)
        layout.addLayout(filter_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def add_packet(self, packet_info: PacketInfo) -> None:
        """Dodaj pakiet i zaktualizuj informacje o urządzeniach"""
        current_time = packet_info.timestamp
        
        # Aktualizuj urządzenie źródłowe
        self._update_device_from_packet(packet_info.src_ip, packet_info, current_time, is_source=True)
        
        # Aktualizuj urządzenie docelowe (tylko podstawowe info)
        self._update_device_from_packet(packet_info.dst_ip, packet_info, current_time, is_source=False)

    def _update_device_from_packet(self, ip_address: str, packet_info: PacketInfo, current_time: float, is_source: bool) -> None:
        """Zaktualizuj informacje o urządzeniu na podstawie pakietu"""
        if ip_address in ["?", "", "0.0.0.0"]:
            return
            
        # Sprawdź czy to lokalne IP (prosta heurystyka)
        if not self._is_local_ip(ip_address):
            return
            
        device = self._devices.get(ip_address)
        
        if device is None:
            # Nowe urządzenie
            # Tylko używaj MAC address dla pakietów źródłowych - są bardziej wiarygodne
            mac_address = packet_info.src_mac if is_source else ""
            hostname = resolve_hostname(ip_address) if ip_address != resolve_hostname(ip_address) else ip_address
            oui_vendor = get_oui_vendor(mac_address) if mac_address else ""
            user_agent = packet_info.user_agent if is_source else ""
            
            device = NetworkDevice(
                ip_address=ip_address,
                mac_address=mac_address,
                hostname=hostname,
                oui_vendor=oui_vendor,
                user_agent=user_agent,
                protocols=set(),
                first_seen=current_time,
                last_seen=current_time
            )
            self._devices[ip_address] = device
        
        # Aktualizuj protokoły i czas ostatniej aktywności
        device.protocols.add(packet_info.protocol)
        device.last_seen = current_time
        
        # Aktualizuj informacje o urządzeniu jeśli dostępne i nie były wcześniej ustawione
        # Tylko dla pakietów źródłowych, bo te mają wiarygodne informacje
        if is_source:
            if packet_info.src_mac and not device.mac_address:
                device.mac_address = packet_info.src_mac
                device.oui_vendor = get_oui_vendor(packet_info.src_mac)
            if packet_info.user_agent and not device.user_agent:
                device.user_agent = packet_info.user_agent

    def _is_local_ip(self, ip: str) -> bool:
        """Sprawdź czy IP jest lokalny (prosta heurystyka)"""
        if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
            return True
        if ip.startswith("169.254."):  # Link-local
            return True
        return False

    def _refresh_table(self) -> None:
        """Odśwież tabelę urządzeń"""
        # Pamiętaj aktualny wiersz
        current_row = self.table.currentRow()
        
        # Wyczyść tabelę
        self.table.setRowCount(0)
        
        # Sortuj urządzenia według ostatniej aktywności (najnowsze pierwsze)
        sorted_devices = sorted(
            self._devices.values(), 
            key=lambda d: d.last_seen, 
            reverse=True
        )
        
        # Dodaj urządzenia do tabeli
        for device in sorted_devices:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            
            # Kolumny
            self.table.setItem(row_idx, 0, QTableWidgetItem(device.ip_address))
            self.table.setItem(row_idx, 1, QTableWidgetItem(device.mac_address))
            self.table.setItem(row_idx, 2, QTableWidgetItem(device.hostname))
            self.table.setItem(row_idx, 3, QTableWidgetItem(device.oui_vendor))
            self.table.setItem(row_idx, 4, QTableWidgetItem(device.user_agent))
            self.table.setItem(row_idx, 5, QTableWidgetItem(", ".join(sorted(device.protocols))))
            self.table.setItem(row_idx, 6, QTableWidgetItem(format_timestamp_human(device.last_seen)))
        
        # Przywróć zaznaczenie
        if 0 <= current_row < self.table.rowCount():
            self.table.setCurrentRow(current_row)
            
        # Zastosuj filtry
        self._apply_filters()

    def _apply_filters(self) -> None:
        """Zastosuj filtry do tabeli"""
        text_filter = self.filter_text.text().strip().lower()
        protocol_filter = self.filter_protocol.currentText()
        
        for row in range(self.table.rowCount()):
            show_row = True
            
            # Filtr protokołu
            if protocol_filter != "ALL":
                protocols_item = self.table.item(row, 5)
                if protocols_item:
                    protocols_text = protocols_item.text()
                    if protocol_filter not in protocols_text:
                        show_row = False
            
            # Filtr tekstowy
            if show_row and text_filter:
                match_found = False
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item and text_filter in item.text().lower():
                        match_found = True
                        break
                show_row = match_found
            
            self.table.setRowHidden(row, not show_row)

    def _show_context_menu(self, pos) -> None:
        """Pokaż menu kontekstowe"""
        item = self.table.itemAt(pos)
        if not item:
            return
            
        row = item.row()
        ip_item = self.table.item(row, 0)
        mac_item = self.table.item(row, 1)
        hostname_item = self.table.item(row, 2)
        
        if not ip_item:
            return
            
        ip_address = ip_item.text()
        mac_address = mac_item.text() if mac_item else ""
        hostname = hostname_item.text() if hostname_item else ""
        
        menu = QMenu(self)
        
        # Kopiuj IP
        copy_ip_action = QAction(f"Kopiuj IP: {ip_address}", self)
        copy_ip_action.triggered.connect(lambda: self._copy_to_clipboard(ip_address))
        menu.addAction(copy_ip_action)
        
        # Kopiuj MAC (jeśli dostępny)
        if mac_address:
            copy_mac_action = QAction(f"Kopiuj MAC: {mac_address}", self)
            copy_mac_action.triggered.connect(lambda: self._copy_to_clipboard(mac_address))
            menu.addAction(copy_mac_action)
        
        # Kopiuj hostname (jeśli dostępny i różny od IP)
        if hostname and hostname != ip_address:
            copy_hostname_action = QAction(f"Kopiuj hostname: {hostname}", self)
            copy_hostname_action.triggered.connect(lambda: self._copy_to_clipboard(hostname))
            menu.addAction(copy_hostname_action)
        
        menu.addSeparator()
        
        # Filtruj według IP
        filter_ip_action = QAction(f"Filtruj według IP", self)
        filter_ip_action.triggered.connect(lambda: self.filter_text.setText(ip_address))
        menu.addAction(filter_ip_action)
        
        menu.exec_(self.table.viewport().mapToGlobal(pos))

    def _copy_to_clipboard(self, text: str) -> None:
        """Kopiuj tekst do schowka"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def clear_devices(self) -> None:
        """Wyczyść wszystkie urządzenia"""
        self._devices.clear()
        self.table.setRowCount(0)

    def get_device_count(self) -> int:
        """Zwróć liczbę wykrytych urządzeń"""
        return len(self._devices)