"""
Zakładka GUI do diagnostyki systemu i optymalizacji AI.
Umożliwia przeglądanie aktualnych danych systemowych, decyzji AI
dotyczących optymalizacji oraz historii uruchomień i decyzji.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QLabel, QPushButton,
    QGroupBox, QGridLayout, QTextEdit, QComboBox,
    QProgressBar, QScrollArea, QSplitter, QHeaderView
)
from PyQt5.QtGui import QFont

from core.system_info import (
    get_realtime_system_info, get_network_info, get_process_info,
    format_bytes, format_uptime
)
from core.diagnostics_history import DiagnosticsHistory


class SystemDiagnosticsTab(QWidget):
    """Zakładka diagnostyki systemu i optymalizacji AI."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ai_engine = None  # Zostanie ustawione przez main_window
        self._diagnostics_history: Optional[DiagnosticsHistory] = None
        
        # Timery
        self.system_update_timer = QTimer(self)
        self.system_update_timer.timeout.connect(self._update_system_info)
        self.system_update_timer.setInterval(2000)  # 2 sekundy
        
        self.ai_update_timer = QTimer(self)
        self.ai_update_timer.timeout.connect(self._update_ai_info)
        self.ai_update_timer.setInterval(5000)  # 5 sekund
        
        self._setup_ui()
        self._start_timers()
    
    def set_ai_engine(self, ai_engine):
        """Ustawia silnik AI dla tej zakładki."""
        self.ai_engine = ai_engine
        if ai_engine:
            self._diagnostics_history = ai_engine.get_diagnostics_history()
    
    def _setup_ui(self):
        """Konfiguruje interfejs użytkownika."""
        main_layout = QVBoxLayout(self)
        
        # Górna sekcja z przyciskami kontroli
        control_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Odśwież dane")
        self.refresh_btn.clicked.connect(self._manual_refresh)
        control_layout.addWidget(self.refresh_btn)
        
        control_layout.addStretch()
        
        self.status_label = QLabel("Status: Aktywny")
        control_layout.addWidget(self.status_label)
        
        main_layout.addLayout(control_layout)
        
        # Główny splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Lewa strona - informacje systemowe
        system_widget = self._create_system_info_widget()
        splitter.addWidget(system_widget)
        
        # Prawa strona - informacje AI i historia
        ai_widget = self._create_ai_info_widget()
        splitter.addWidget(ai_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
    
    def _create_system_info_widget(self) -> QWidget:
        """Tworzy widget z informacjami systemowymi."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Metryki systemowe w czasie rzeczywistym
        metrics_group = QGroupBox("Metryki systemowe")
        metrics_layout = QGridLayout(metrics_group)
        
        # CPU
        metrics_layout.addWidget(QLabel("CPU:"), 0, 0)
        self.cpu_label = QLabel("-%")
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        metrics_layout.addWidget(self.cpu_label, 0, 1)
        metrics_layout.addWidget(self.cpu_progress, 0, 2)
        
        # RAM
        metrics_layout.addWidget(QLabel("RAM:"), 1, 0)
        self.ram_label = QLabel("-%")
        self.ram_progress = QProgressBar()
        self.ram_progress.setRange(0, 100)
        metrics_layout.addWidget(self.ram_label, 1, 1)
        metrics_layout.addWidget(self.ram_progress, 1, 2)
        
        # Dysk
        metrics_layout.addWidget(QLabel("Dysk:"), 2, 0)
        self.disk_label = QLabel("-%")
        self.disk_progress = QProgressBar()
        self.disk_progress.setRange(0, 100)
        metrics_layout.addWidget(self.disk_label, 2, 1)
        metrics_layout.addWidget(self.disk_progress, 2, 2)
        
        # Sieć
        metrics_layout.addWidget(QLabel("Połączenia:"), 3, 0)
        self.network_label = QLabel("-")
        metrics_layout.addWidget(self.network_label, 3, 1, 1, 2)
        
        # Uptime
        metrics_layout.addWidget(QLabel("Uptime:"), 4, 0)
        self.uptime_label = QLabel("-")
        metrics_layout.addWidget(self.uptime_label, 4, 1, 1, 2)
        
        layout.addWidget(metrics_group)
        
        # Szczegółowe informacje
        details_group = QGroupBox("Szczegóły systemu")
        details_layout = QVBoxLayout(details_group)
        
        self.system_details = QTextEdit()
        self.system_details.setReadOnly(True)
        self.system_details.setMaximumHeight(200)
        details_layout.addWidget(self.system_details)
        
        layout.addWidget(details_group)
        
        # Procesy
        processes_group = QGroupBox("Top procesy (CPU/pamięć)")
        processes_layout = QVBoxLayout(processes_group)
        
        self.processes_table = QTableWidget()
        self.processes_table.setColumnCount(4)
        self.processes_table.setHorizontalHeaderLabels(["PID", "Nazwa", "CPU%", "RAM%"])
        self.processes_table.horizontalHeader().setStretchLastSection(True)
        self.processes_table.setMaximumHeight(150)
        processes_layout.addWidget(self.processes_table)
        
        layout.addWidget(processes_group)
        
        return widget
    
    def _create_ai_info_widget(self) -> QWidget:
        """Tworzy widget z informacjami AI i historią."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tabs dla różnych widoków AI
        ai_tabs = QTabWidget()
        
        # Tab 1: Status AI
        ai_status_tab = self._create_ai_status_tab()
        ai_tabs.addTab(ai_status_tab, "Status AI")
        
        # Tab 2: Historia decyzji
        ai_history_tab = self._create_ai_history_tab()
        ai_tabs.addTab(ai_history_tab, "Historia decyzji")
        
        # Tab 3: Statystyki
        ai_stats_tab = self._create_ai_stats_tab()
        ai_tabs.addTab(ai_stats_tab, "Statystyki")
        
        layout.addWidget(ai_tabs)
        
        return widget
    
    def _create_ai_status_tab(self) -> QWidget:
        """Tworzy zakładkę statusu AI."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Status główny
        status_group = QGroupBox("Status silnika AI")
        status_layout = QGridLayout(status_group)
        
        # Podstawowe info
        status_layout.addWidget(QLabel("ML aktywny:"), 0, 0)
        self.ml_status_label = QLabel("-")
        status_layout.addWidget(self.ml_status_label, 0, 1)
        
        status_layout.addWidget(QLabel("Model gotowy:"), 1, 0)
        self.model_status_label = QLabel("-")
        status_layout.addWidget(self.model_status_label, 1, 1)
        
        status_layout.addWidget(QLabel("Przetworzonych próbek:"), 2, 0)
        self.samples_label = QLabel("-")
        status_layout.addWidget(self.samples_label, 2, 1)
        
        status_layout.addWidget(QLabel("Ostatni wynik:"), 3, 0)
        self.last_score_label = QLabel("-")
        status_layout.addWidget(self.last_score_label, 3, 1)
        
        layout.addWidget(status_group)
        
        # Konfiguracja
        config_group = QGroupBox("Konfiguracja")
        config_layout = QGridLayout(config_group)
        
        config_layout.addWidget(QLabel("Próg anomalii:"), 0, 0)
        self.threshold_label = QLabel("-")
        config_layout.addWidget(self.threshold_label, 0, 1)
        
        config_layout.addWidget(QLabel("Interwał retreningu:"), 1, 0)
        self.refit_interval_label = QLabel("-")
        config_layout.addWidget(self.refit_interval_label, 1, 1)
        
        config_layout.addWidget(QLabel("Streaming aktywny:"), 2, 0)
        self.streaming_label = QLabel("-")
        config_layout.addWidget(self.streaming_label, 2, 1)
        
        layout.addWidget(config_group)
        
        # Ostatnie powody
        reasons_group = QGroupBox("Ostatnie powody anomalii")
        reasons_layout = QVBoxLayout(reasons_group)
        
        self.reasons_text = QTextEdit()
        self.reasons_text.setReadOnly(True)
        self.reasons_text.setMaximumHeight(100)
        reasons_layout.addWidget(self.reasons_text)
        
        layout.addWidget(reasons_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_ai_history_tab(self) -> QWidget:
        """Tworzy zakładkę historii decyzji AI."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Kontrolki filtrowania
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Okres:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Ostatnia godzina", "Ostatnie 6 godzin", "Ostatnie 24 godziny", "Wszystkie"])
        self.period_combo.currentTextChanged.connect(self._update_ai_history)
        filter_layout.addWidget(self.period_combo)
        
        filter_layout.addWidget(QLabel("Limit:"))
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(["50", "100", "200", "500"])
        self.limit_combo.setCurrentText("100")
        self.limit_combo.currentTextChanged.connect(self._update_ai_history)
        filter_layout.addWidget(self.limit_combo)
        
        refresh_history_btn = QPushButton("Odśwież historię")
        refresh_history_btn.clicked.connect(self._update_ai_history)
        filter_layout.addWidget(refresh_history_btn)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Tabela historii
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Czas", "Wynik", "Anomalia", "Powody", "Źródło", "Cel"
        ])
        
        # Ustaw rozmiary kolumn
        header = self.history_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Czas
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Wynik
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Anomalia
        
        layout.addWidget(self.history_table)
        
        return widget
    
    def _create_ai_stats_tab(self) -> QWidget:
        """Tworzy zakładkę statystyk AI."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Statystyki ogólne
        stats_group = QGroupBox("Statystyki (ostatnie 24h)")
        stats_layout = QGridLayout(stats_group)
        
        stats_layout.addWidget(QLabel("Łączne decyzje:"), 0, 0)
        self.total_decisions_label = QLabel("-")
        stats_layout.addWidget(self.total_decisions_label, 0, 1)
        
        stats_layout.addWidget(QLabel("Wykryte anomalie:"), 1, 0)
        self.anomalies_detected_label = QLabel("-")
        stats_layout.addWidget(self.anomalies_detected_label, 1, 1)
        
        stats_layout.addWidget(QLabel("Współczynnik anomalii:"), 2, 0)
        self.anomaly_rate_label = QLabel("-")
        stats_layout.addWidget(self.anomaly_rate_label, 2, 1)
        
        stats_layout.addWidget(QLabel("Średni wynik:"), 3, 0)
        self.avg_score_label = QLabel("-")
        stats_layout.addWidget(self.avg_score_label, 3, 1)
        
        layout.addWidget(stats_group)
        
        # Wykres czasowy (symulowany tekstowo)
        timeline_group = QGroupBox("Rozkład anomalii w czasie")
        timeline_layout = QVBoxLayout(timeline_group)
        
        self.timeline_text = QTextEdit()
        self.timeline_text.setReadOnly(True)
        self.timeline_text.setMaximumHeight(150)
        timeline_layout.addWidget(self.timeline_text)
        
        layout.addWidget(timeline_group)
        
        layout.addStretch()
        
        return widget
    
    def _start_timers(self):
        """Uruchamia timery aktualizacji."""
        self.system_update_timer.start()
        self.ai_update_timer.start()
        
        # Pierwsze aktualizacje
        self._update_system_info()
        self._update_ai_info()
        self._update_ai_history()
    
    def _manual_refresh(self):
        """Ręczne odświeżenie wszystkich danych."""
        self._update_system_info()
        self._update_ai_info()
        self._update_ai_history()
        self.status_label.setText("Status: Odświeżono " + datetime.now().strftime("%H:%M:%S"))
    
    def _update_system_info(self):
        """Aktualizuje informacje systemowe."""
        try:
            # Metryki w czasie rzeczywistym
            realtime_info = get_realtime_system_info()
            
            # CPU
            cpu_percent = realtime_info.get("cpu_percent", 0)
            self.cpu_label.setText(f"{cpu_percent:.1f}%")
            self.cpu_progress.setValue(int(cpu_percent))
            
            # RAM
            ram_percent = realtime_info.get("ram_percent", 0)
            self.ram_label.setText(f"{ram_percent:.1f}%")
            self.ram_progress.setValue(int(ram_percent))
            
            # Dysk
            disk_percent = realtime_info.get("disk_percent", 0)
            self.disk_label.setText(f"{disk_percent:.1f}%")
            self.disk_progress.setValue(int(disk_percent))
            
            # Sieć
            connections = realtime_info.get("connections_count", 0) if hasattr(realtime_info, 'get') else 0
            self.network_label.setText(f"{connections} połączeń")
            
            # Uptime
            uptime_seconds = realtime_info.get("uptime_seconds", 0)
            self.uptime_label.setText(format_uptime(uptime_seconds))
            
            # Szczegóły systemowe
            details = []
            details.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            details.append(f"Procesy: {realtime_info.get('processes_count', 'N/A')}")
            details.append(f"Sieć wysłane: {format_bytes(realtime_info.get('network_bytes_sent', 0))}")
            details.append(f"Sieć odebrane: {format_bytes(realtime_info.get('network_bytes_recv', 0))}")
            details.append(f"Pakiety wysłane: {realtime_info.get('network_packets_sent', 0)}")
            details.append(f"Pakiety odebrane: {realtime_info.get('network_packets_recv', 0)}")
            
            self.system_details.setPlainText("\n".join(details))
            
            # Procesy
            self._update_processes_table()
            
        except Exception as e:
            self.system_details.setPlainText(f"Błąd aktualizacji: {str(e)}")
    
    def _update_processes_table(self):
        """Aktualizuje tabelę procesów."""
        try:
            process_info = get_process_info()
            top_processes = process_info.get("top_cpu_processes", [])[:5]
            
            self.processes_table.setRowCount(len(top_processes))
            
            for i, proc in enumerate(top_processes):
                self.processes_table.setItem(i, 0, QTableWidgetItem(str(proc.get("pid", "-"))))
                self.processes_table.setItem(i, 1, QTableWidgetItem(str(proc.get("name", "-"))))
                self.processes_table.setItem(i, 2, QTableWidgetItem(f"{proc.get('cpu_percent', 0):.1f}%"))
                self.processes_table.setItem(i, 3, QTableWidgetItem(f"{proc.get('memory_percent', 0):.1f}%"))
                
        except Exception:
            pass
    
    def _update_ai_info(self):
        """Aktualizuje informacje AI."""
        if not self.ai_engine:
            return
        
        try:
            status = self.ai_engine.get_status()
            
            # Status główny
            self.ml_status_label.setText("TAK" if status.get("ml_enabled", False) else "NIE")
            self.model_status_label.setText("TAK" if status.get("model_ready", False) else "NIE")
            self.samples_label.setText(str(status.get("samples_seen", 0)))
            
            last_score = status.get("last_score")
            if last_score is not None:
                self.last_score_label.setText(f"{last_score:.3f}")
            else:
                self.last_score_label.setText("-")
            
            # Konfiguracja
            self.threshold_label.setText(f"{status.get('combined_threshold', 0):.2f}")
            self.refit_interval_label.setText(str(status.get("refit_interval", 0)))
            self.streaming_label.setText("TAK" if status.get("stream_enabled", False) else "NIE")
            
            # Ostatnie powody
            reasons = status.get("last_reasons", [])
            if reasons:
                self.reasons_text.setPlainText("\n".join(f"• {reason}" for reason in reasons))
            else:
                self.reasons_text.setPlainText("Brak ostatnich anomalii")
            
            # Aktualizuj statystyki
            self._update_ai_stats()
            
        except Exception as e:
            self.reasons_text.setPlainText(f"Błąd aktualizacji AI: {str(e)}")
    
    def _update_ai_history(self):
        """Aktualizuje historię decyzji AI."""
        if not self.ai_engine:
            return
        
        try:
            # Parsuj okres
            period_text = self.period_combo.currentText()
            hours = None
            if period_text == "Ostatnia godzina":
                hours = 1
            elif period_text == "Ostatnie 6 godzin":
                hours = 6
            elif period_text == "Ostatnie 24 godziny":
                hours = 24
            
            # Parsuj limit
            limit = int(self.limit_combo.currentText())
            
            # Pobierz historię
            decisions = self.ai_engine.get_recent_decisions(hours=hours, limit=limit)
            
            # Aktualizuj tabelę
            self.history_table.setRowCount(len(decisions))
            
            for i, decision in enumerate(decisions):
                # Czas
                timestamp = decision.get("timestamp", time.time())
                time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                self.history_table.setItem(i, 0, QTableWidgetItem(time_str))
                
                # Wynik
                score = decision.get("score", 0)
                self.history_table.setItem(i, 1, QTableWidgetItem(f"{score:.3f}"))
                
                # Anomalia
                is_anomaly = decision.get("is_anomaly", False)
                anomaly_text = "TAK" if is_anomaly else "NIE"
                item = QTableWidgetItem(anomaly_text)
                if is_anomaly:
                    item.setBackground(Qt.red)
                self.history_table.setItem(i, 2, item)
                
                # Powody
                reasons = decision.get("reasons", [])
                reasons_text = ", ".join(reasons) if reasons else "-"
                self.history_table.setItem(i, 3, QTableWidgetItem(reasons_text))
                
                # Źródło i cel
                packet_info = decision.get("packet_info", {})
                src_ip = packet_info.get("src_ip", "-")
                dst_ip = packet_info.get("dst_ip", "-")
                self.history_table.setItem(i, 4, QTableWidgetItem(src_ip))
                self.history_table.setItem(i, 5, QTableWidgetItem(dst_ip))
                
        except Exception as e:
            # Wyczyść tabelę w przypadku błędu
            self.history_table.setRowCount(0)
    
    def _update_ai_stats(self):
        """Aktualizuje statystyki AI."""
        if not self._diagnostics_history:
            return
        
        try:
            stats = self._diagnostics_history.get_summary_stats(hours=24)
            
            self.total_decisions_label.setText(str(stats.get("ai_decisions_total", 0)))
            self.anomalies_detected_label.setText(str(stats.get("anomalies_detected", 0)))
            
            anomaly_rate = stats.get("anomaly_rate", 0)
            self.anomaly_rate_label.setText(f"{anomaly_rate:.1%}")
            
            # Oblicz średni wynik z ostatnich decyzji
            recent_decisions = self.ai_engine.get_recent_decisions(hours=24, limit=1000)
            if recent_decisions:
                avg_score = sum(d.get("score", 0) for d in recent_decisions) / len(recent_decisions)
                self.avg_score_label.setText(f"{avg_score:.3f}")
            else:
                self.avg_score_label.setText("-")
            
            # Generuj prosty timeline
            self._generate_timeline(recent_decisions)
            
        except Exception:
            pass
    
    def _generate_timeline(self, decisions: List[Dict[str, Any]]):
        """Generuje prosty timeline anomalii."""
        try:
            # Pogrupuj decyzje według godzin
            hours_anomalies = {}
            current_time = time.time()
            
            for decision in decisions:
                timestamp = decision.get("timestamp", current_time)
                hour = int((current_time - timestamp) // 3600)
                if hour < 24:  # Ostatnie 24 godziny
                    if hour not in hours_anomalies:
                        hours_anomalies[hour] = 0
                    if decision.get("is_anomaly", False):
                        hours_anomalies[hour] += 1
            
            # Generuj wykres tekstowy
            timeline = ["Anomalie w ostatnich 24 godzinach:"]
            for hour in range(24):
                anomalies = hours_anomalies.get(hour, 0)
                bar = "█" * min(anomalies, 20)  # Maksymalnie 20 znaków
                timeline.append(f"{23-hour:2d}h temu: {bar} ({anomalies})")
            
            self.timeline_text.setPlainText("\n".join(timeline))
            
        except Exception:
            self.timeline_text.setPlainText("Błąd generowania timeline")
    
    def closeEvent(self, event):
        """Zatrzymuje timery przy zamykaniu."""
        self.system_update_timer.stop()
        self.ai_update_timer.stop()
        super().closeEvent(event)