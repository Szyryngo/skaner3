from __future__ import annotations

from typing import Dict, Optional, List

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTextEdit, QLabel, QListWidgetItem
)

from core.utils import PacketInfo


class AlertViewer(QWidget):
    alert_selected = pyqtSignal(int)  # Emituje indeks pakietu
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        # Lista alertów
        self.list_widget = QListWidget(self)
        self.list_widget.itemSelectionChanged.connect(self._on_alert_selected)
        
        # Szczegóły pakietu (hex/ascii)
        self.detail_hex = QTextEdit(self)
        self.detail_hex.setReadOnly(True)
        self.detail_ascii = QTextEdit(self)
        self.detail_ascii.setReadOnly(True)
        
        detail_widget = QWidget(self)
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.addWidget(QLabel("Hex dump:"))
        detail_layout.addWidget(self.detail_hex)
        detail_layout.addWidget(QLabel("ASCII:"))
        detail_layout.addWidget(self.detail_ascii)
        
        # Splitter dla listy i szczegółów
        self.splitter = QSplitter(self)
        self.splitter.addWidget(self.list_widget)
        self.splitter.addWidget(detail_widget)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 3)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.splitter)
        self.setLayout(layout)
        
        # Bufor pakietów dla podglądu
        self._packets_buffer: List[PacketInfo] = []
        
    def add_alert(self, message: str, packet_row: Dict[str, str], score: Optional[float] = None) -> None:
        score_text = f" [score={score}]" if score is not None else ""
        summary = (
            f"{message}{score_text} | {packet_row.get('time','')} "
            f"{packet_row.get('src_ip','')}:{packet_row.get('src_port','')} -> "
            f"{packet_row.get('dst_ip','')}:{packet_row.get('dst_port','')} "
            f"{packet_row.get('protocol','')}/{packet_row.get('length','')}"
        )
        item = QListWidgetItem(summary, self.list_widget)
        
        # Koloruj według score - bardziej zaawansowane kolorowanie
        if score is not None:
            if score >= 0.9:
                # Czerwony - wysokie zagrożenie
                item.setBackground(QColor(255, 150, 150))
                item.setForeground(QColor(139, 0, 0))
                font = QFont()
                font.setBold(True)
                item.setFont(font)
            elif score >= 0.7:
                # Pomarańczowy - średnie zagrożenie
                item.setBackground(QColor(255, 200, 150))
                item.setForeground(QColor(139, 69, 19))
                font = QFont()
                font.setBold(True)
                item.setFont(font)
            elif score >= 0.5:
                # Żółty - niskie zagrożenie
                item.setBackground(QColor(255, 255, 150))
                item.setForeground(QColor(85, 85, 0))
            else:
                # Zielony - bezpieczny
                item.setBackground(QColor(200, 255, 200))
                item.setForeground(QColor(0, 100, 0))
        
    def set_packets_buffer(self, packets_buffer: List[PacketInfo]) -> None:
        """Ustaw bufor pakietów z MainWindow dla podglądu"""
        self._packets_buffer = packets_buffer
        
    def _on_alert_selected(self) -> None:
        """Obsługa wyboru alertu - pokaż szczegóły pakietu"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
            
        # Znajdź indeks wybranego alertu
        alert_index = self.list_widget.row(selected_items[0])
        if alert_index < len(self._packets_buffer):
            packet_row = self._packets_buffer[alert_index]
            self._show_packet_details(packet_row)
            
    def _show_packet_details(self, packet_row: Dict[str, str]) -> None:
        """Pokaż szczegóły pakietu w hex i ASCII"""
        # Znajdź oryginalny pakiet w buforze
        packet_info = None
        for packet in self._packets_buffer:
            # Porównaj kluczowe pola
            if (str(packet.src_ip) == packet_row.get('src_ip', '') and 
                str(packet.dst_ip) == packet_row.get('dst_ip', '') and
                str(packet.src_port) == packet_row.get('src_port', '') and
                str(packet.dst_port) == packet_row.get('dst_port', '') and
                str(packet.protocol) == packet_row.get('protocol', '')):
                packet_info = packet
                break
        
        if packet_info and hasattr(packet_info, 'raw_bytes') and packet_info.raw_bytes:
            # Użyj oryginalnych surowych danych
            raw_data = packet_info.raw_bytes
        else:
            # Fallback: symuluj dane
            raw_data = self._simulate_raw_packet(packet_row)
        
        # Hex dump
        hex_dump = self._bytes_to_hex_dump(raw_data)
        self.detail_hex.setPlainText(hex_dump)
        
        # ASCII
        ascii_text = self._bytes_to_ascii(raw_data)
        self.detail_ascii.setPlainText(ascii_text)
        
    def _simulate_raw_packet(self, packet_row: Dict[str, str]) -> bytes:
        """Symuluj surowe bajty pakietu na podstawie danych"""
        # To jest uproszczona symulacja - w rzeczywistości powinno używać oryginalnych danych
        src_ip = packet_row.get('src_ip', '0.0.0.0')
        dst_ip = packet_row.get('dst_ip', '0.0.0.0')
        src_port = packet_row.get('src_port', '0')
        dst_port = packet_row.get('dst_port', '0')
        protocol = packet_row.get('protocol', 'TCP')
        length = packet_row.get('length', '0')
        
        # Stwórz przykładowe dane pakietu
        packet_str = f"{src_ip}:{src_port} -> {dst_ip}:{dst_port} {protocol} len={length}"
        return packet_str.encode('utf-8')
        
    def _bytes_to_hex_dump(self, data: bytes) -> str:
        """Konwertuj bajty na hex dump"""
        if not data:
            return "Brak danych"
            
        hex_lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_part = ' '.join(f'{b:02x}' for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            
            # Wyrównaj hex do 48 znaków
            hex_part = hex_part.ljust(48)
            
            line = f'{i:08x}  {hex_part}  |{ascii_part}|'
            hex_lines.append(line)
            
        return '\n'.join(hex_lines)
        
    def _bytes_to_ascii(self, data: bytes) -> str:
        """Konwertuj bajty na ASCII"""
        if not data:
            return "Brak danych"
            
        return ''.join(chr(b) if 32 <= b <= 126 else f'\\x{b:02x}' for b in data)
        
    def clear_all(self) -> None:
        """Wyczyść wszystkie alerty"""
        self.list_widget.clear()
        self._packets_buffer.clear()
        self.detail_hex.clear()
        self.detail_ascii.clear()
