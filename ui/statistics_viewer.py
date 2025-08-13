from __future__ import annotations

import time
from typing import Dict, List, Optional
from collections import deque, defaultdict

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QGroupBox, QGridLayout, QListWidget, QListWidgetItem, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.utils import PacketInfo, format_timestamp_human


class StatisticsViewer(QWidget):
    """Widget wyświetlający statystyki w czasie rzeczywistym:
    - Liczba pakietów TCP, UDP, ICMP i suma
    - Liczba wykrytych alertów (AI + reguły)
    - Liczba i lista anomalii AI
    - Pakiety na sekundę (średnia z ostatnich 10s)
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        # Dane statystyczne
        self._packet_counts = defaultdict(int)  # Liczniki protokołów
        self._total_packets = 0
        self._total_alerts = 0
        self._ai_anomalies = 0
        self._ai_anomaly_list: List[Dict] = []  # Lista anomalii z czasem i detalami
        
        # Pakiety na sekundę - bufor z timestampami
        self._packet_timestamps: deque = deque(maxlen=1000)  # Ostatnie 1000 pakietów
        
        # Inicjalizacja UI
        self._setup_ui()
        
        # Timer do aktualizacji wyświetlanych statystyk
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_display)
        self._update_timer.start(1000)  # Aktualizuj co sekundę
        
    def _setup_ui(self) -> None:
        """Inicjalizacja interfejsu użytkownika"""
        layout = QVBoxLayout(self)
        
        # Główny splitter - statystyki po lewej, anomalie po prawej
        main_splitter = QSplitter(Qt.Horizontal)
        
        # === Lewa strona - statystyki ===
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        
        # Grupa statystyk pakietów
        packet_group = QGroupBox("Statystyki pakietów")
        packet_layout = QGridLayout(packet_group)
        
        # Etykiety dla statystyk pakietów
        self.label_total = QLabel("Suma wszystkich: 0")
        self.label_tcp = QLabel("TCP: 0")
        self.label_udp = QLabel("UDP: 0")
        self.label_icmp = QLabel("ICMP: 0")
        self.label_other = QLabel("Inne: 0")
        
        # Ustaw czcionkę dla głównych statystyk
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        for label in [self.label_total, self.label_tcp, self.label_udp, self.label_icmp, self.label_other]:
            label.setFont(font)
        
        packet_layout.addWidget(self.label_total, 0, 0, 1, 2)
        packet_layout.addWidget(self.label_tcp, 1, 0)
        packet_layout.addWidget(self.label_udp, 1, 1)
        packet_layout.addWidget(self.label_icmp, 2, 0)
        packet_layout.addWidget(self.label_other, 2, 1)
        
        stats_layout.addWidget(packet_group)
        
        # Grupa statystyk alertów
        alert_group = QGroupBox("Statystyki alertów")
        alert_layout = QGridLayout(alert_group)
        
        self.label_total_alerts = QLabel("Łączna liczba alertów: 0")
        self.label_ai_anomalies = QLabel("Anomalie AI: 0")
        
        font_alerts = QFont()
        font_alerts.setPointSize(10)
        font_alerts.setBold(True)
        self.label_total_alerts.setFont(font_alerts)
        self.label_ai_anomalies.setFont(font_alerts)
        
        alert_layout.addWidget(self.label_total_alerts, 0, 0)
        alert_layout.addWidget(self.label_ai_anomalies, 1, 0)
        
        stats_layout.addWidget(alert_group)
        
        # Grupa wydajności
        performance_group = QGroupBox("Wydajność")
        performance_layout = QVBoxLayout(performance_group)
        
        self.label_pps = QLabel("Pakiety/s (10s): 0.0")
        self.label_last_update = QLabel("Ostatnia aktualizacja: -")
        
        font_perf = QFont()
        font_perf.setPointSize(10)
        self.label_pps.setFont(font_perf)
        
        performance_layout.addWidget(self.label_pps)
        performance_layout.addWidget(self.label_last_update)
        
        stats_layout.addWidget(performance_group)
        
        # Dodaj rozciągacz
        stats_layout.addStretch()
        
        main_splitter.addWidget(stats_widget)
        
        # === Prawa strona - lista anomalii AI ===
        anomaly_widget = QWidget()
        anomaly_layout = QVBoxLayout(anomaly_widget)
        
        anomaly_group = QGroupBox("Wykryte anomalie AI")
        anomaly_group_layout = QVBoxLayout(anomaly_group)
        
        # Lista anomalii
        self.anomaly_list = QListWidget()
        self.anomaly_list.setMinimumHeight(200)
        anomaly_group_layout.addWidget(self.anomaly_list)
        
        anomaly_layout.addWidget(anomaly_group)
        
        # Pole na szczegóły wybranej anomalii
        details_group = QGroupBox("Szczegóły anomalii")
        details_layout = QVBoxLayout(details_group)
        
        self.anomaly_details = QTextEdit()
        self.anomaly_details.setReadOnly(True)
        self.anomaly_details.setMaximumHeight(150)
        details_layout.addWidget(self.anomaly_details)
        
        anomaly_layout.addWidget(details_group)
        
        main_splitter.addWidget(anomaly_widget)
        
        # Ustaw proporcje splitter
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 1)
        
        layout.addWidget(main_splitter)
        
        # Połączenie wyboru anomalii
        self.anomaly_list.itemSelectionChanged.connect(self._on_anomaly_selected)
    
    def add_packet(self, packet_info: PacketInfo) -> None:
        """Dodaj pakiet do statystyk"""
        # Zwiększ licznik dla protokołu
        protocol = packet_info.protocol.upper()
        self._packet_counts[protocol] += 1
        self._total_packets += 1
        
        # Dodaj timestamp dla obliczeń pakietów na sekundę
        self._packet_timestamps.append(packet_info.timestamp)
    
    def add_alert(self, alert_type: str, packet_row: Dict[str, str], score: Optional[float] = None) -> None:
        """Dodaj alert do statystyk"""
        self._total_alerts += 1
        
        # Jeśli to anomalia AI, dodaj do listy
        if "AI anomaly" in alert_type or "anomaly" in alert_type.lower():
            self._ai_anomalies += 1
            
            # Dodaj szczegóły anomalii
            anomaly_data = {
                "timestamp": time.time(),
                "type": alert_type,
                "score": score,
                "packet": packet_row,
                "details": f"Score: {score:.3f}" if score else "Brak score"
            }
            self._ai_anomaly_list.append(anomaly_data)
            
            # Dodaj do listy GUI
            time_str = format_timestamp_human(anomaly_data["timestamp"])
            summary = f"[{time_str}] {alert_type}"
            if score is not None:
                summary += f" (score: {score:.3f})"
            summary += f" - {packet_row.get('src_ip', '?')} → {packet_row.get('dst_ip', '?')}"
            
            item = QListWidgetItem(summary)
            # Koloruj według score
            if score is not None:
                if score >= 0.9:
                    item.setBackground(Qt.red)
                elif score >= 0.7:
                    item.setBackground(Qt.yellow)
                else:
                    item.setBackground(Qt.green)
            
            self.anomaly_list.addItem(item)
            
            # Przewiń do najnowszego elementu
            self.anomaly_list.scrollToBottom()
            
            # Ogranicz liczbę elementów w liście (pozostaw ostatnie 100)
            if self.anomaly_list.count() > 100:
                self.anomaly_list.takeItem(0)
                self._ai_anomaly_list.pop(0)
    
    def _calculate_packets_per_second(self) -> float:
        """Oblicz pakiety na sekundę z ostatnich 10 sekund"""
        if not self._packet_timestamps:
            return 0.0
        
        current_time = time.time()
        cutoff_time = current_time - 10.0  # Ostatnie 10 sekund
        
        # Policz pakiety z ostatnich 10 sekund
        recent_packets = sum(1 for ts in self._packet_timestamps if ts >= cutoff_time)
        
        return recent_packets / 10.0
    
    def _update_display(self) -> None:
        """Aktualizuj wyświetlane statystyki"""
        # Statystyki pakietów
        self.label_total.setText(f"Suma wszystkich: {self._total_packets}")
        self.label_tcp.setText(f"TCP: {self._packet_counts.get('TCP', 0)}")
        self.label_udp.setText(f"UDP: {self._packet_counts.get('UDP', 0)}")
        self.label_icmp.setText(f"ICMP: {self._packet_counts.get('ICMP', 0)}")
        
        # Oblicz "inne" protokoły
        other_count = self._total_packets - (
            self._packet_counts.get('TCP', 0) + 
            self._packet_counts.get('UDP', 0) + 
            self._packet_counts.get('ICMP', 0)
        )
        self.label_other.setText(f"Inne: {other_count}")
        
        # Statystyki alertów
        self.label_total_alerts.setText(f"Łączna liczba alertów: {self._total_alerts}")
        self.label_ai_anomalies.setText(f"Anomalie AI: {self._ai_anomalies}")
        
        # Wydajność
        pps = self._calculate_packets_per_second()
        self.label_pps.setText(f"Pakiety/s (10s): {pps:.1f}")
        
        # Ostatnia aktualizacja
        self.label_last_update.setText(f"Ostatnia aktualizacja: {format_timestamp_human(time.time())}")
    
    def _on_anomaly_selected(self) -> None:
        """Obsługa wyboru anomalii z listy"""
        selected_items = self.anomaly_list.selectedItems()
        if not selected_items:
            self.anomaly_details.clear()
            return
        
        # Znajdź indeks wybranej anomalii
        selected_index = self.anomaly_list.row(selected_items[0])
        if 0 <= selected_index < len(self._ai_anomaly_list):
            anomaly = self._ai_anomaly_list[selected_index]
            
            # Wyświetl szczegóły
            details = f"""Typ: {anomaly['type']}
Czas: {format_timestamp_human(anomaly['timestamp'])}
Score: {anomaly.get('score', 'N/A')}

Pakiet:
  Źródło: {anomaly['packet'].get('src_ip', 'N/A')}:{anomaly['packet'].get('src_port', 'N/A')}
  Cel: {anomaly['packet'].get('dst_ip', 'N/A')}:{anomaly['packet'].get('dst_port', 'N/A')}
  Protokół: {anomaly['packet'].get('protocol', 'N/A')}
  Rozmiar: {anomaly['packet'].get('length', 'N/A')} bajtów
  Czas pakietu: {anomaly['packet'].get('time', 'N/A')}

Szczegóły: {anomaly['details']}"""
            
            self.anomaly_details.setPlainText(details)
    
    def clear_statistics(self) -> None:
        """Wyczyść wszystkie statystyki"""
        self._packet_counts.clear()
        self._total_packets = 0
        self._total_alerts = 0
        self._ai_anomalies = 0
        self._ai_anomaly_list.clear()
        self._packet_timestamps.clear()
        
        # Wyczyść GUI
        self.anomaly_list.clear()
        self.anomaly_details.clear()
        
        # Wymuś aktualizację wyświetlania
        self._update_display()
    
    def get_statistics_summary(self) -> Dict:
        """Zwróć podsumowanie statystyk dla eksportu lub logowania"""
        return {
            "total_packets": self._total_packets,
            "tcp_packets": self._packet_counts.get('TCP', 0),
            "udp_packets": self._packet_counts.get('UDP', 0),
            "icmp_packets": self._packet_counts.get('ICMP', 0),
            "other_packets": self._total_packets - (
                self._packet_counts.get('TCP', 0) + 
                self._packet_counts.get('UDP', 0) + 
                self._packet_counts.get('ICMP', 0)
            ),
            "total_alerts": self._total_alerts,
            "ai_anomalies": self._ai_anomalies,
            "packets_per_second": self._calculate_packets_per_second(),
            "last_update": time.time()
        }