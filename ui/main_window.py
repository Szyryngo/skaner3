from __future__ import annotations

from queue import Queue, Empty
from typing import Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QLabel,
    QToolBar,
    QSizePolicy,
)
from PyQt5.QtCore import QSettings
import psutil

from core.ai_engine import AIEngine
from core.packet_sniffer import PacketSniffer
from core.rules import RuleEngine
from core.utils import packetinfo_to_row, PacketInfo
from .ai_status_viewer import AIStatusViewer
from .alert_viewer import AlertViewer
from .config_dialog import ConfigDialog
from .packet_viewer import PacketViewer


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI Network Sniffer")
        self.resize(1000, 600)

        # Model/engine
        self.ai_engine = AIEngine()
        self.rule_engine = RuleEngine()

        # Kolejka pakietów od sniffera
        self.packet_queue: Queue[PacketInfo] = Queue(maxsize=5000)
        self.sniffer: Optional[PacketSniffer] = None

        # UI
        self.tabs = QTabWidget(self)
        self.packet_viewer = PacketViewer(self)
        self.alert_viewer = AlertViewer(self)
        self.ai_status = AIStatusViewer(self)

        # Szczegóły pakietu (hex/ascii/geolokalizacja)
        self.detail_hex = QTextEdit(self)
        self.detail_hex.setReadOnly(True)
        self.detail_ascii = QTextEdit(self)
        self.detail_ascii.setReadOnly(True)
        self.detail_geo = QLabel(self)
        self.detail_geo.setWordWrap(True)

        detail_widget = QWidget(self)
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.addWidget(QLabel("Hex dump:"))
        detail_layout.addWidget(self.detail_hex)
        detail_layout.addWidget(QLabel("ASCII:"))
        detail_layout.addWidget(self.detail_ascii)
        detail_layout.addWidget(QLabel("Geolokalizacja (dst/src):"))
        detail_layout.addWidget(self.detail_geo)

        splitter = QSplitter(self)
        splitter.addWidget(self.packet_viewer)
        splitter.addWidget(detail_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        tab_packets = QWidget(self)
        tab_packets_layout = QVBoxLayout(tab_packets)
        tab_packets_layout.addWidget(splitter)

        self.tabs.addTab(tab_packets, "Pakiety")
        self.tabs.addTab(self.alert_viewer, "Alerty")
        self.tabs.addTab(self.ai_status, "AI")
        self.setCentralWidget(self.tabs)

        # Status bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self._set_status("Idle")

        # Menu/Actions
        self._create_actions()

        # Timer do przetwarzania pakietów → UI
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._drain_queue)
        self.timer.start()

        # Timer do metryk systemowych (CPU/RAM)
        self.resource_label = QLabel("CPU: --%  RAM: --%", self)
        self.resource_timer = QTimer(self)
        self.resource_timer.setInterval(1000)
        self.resource_timer.timeout.connect(self._update_resource_label)
        self.resource_timer.start()

        # Domyślna konfiguracja
        settings = QSettings("Skaner3", "AI Network Sniffer")
        self.cfg_interface: Optional[str] = settings.value("capture/interface", None, type=str)
        self.cfg_bpf_filter: Optional[str] = settings.value("capture/bpf", None, type=str)
        sim_val = settings.value("capture/simulation", True)
        self.cfg_simulation: bool = bool(sim_val if isinstance(sim_val, bool) else str(sim_val).lower() in {"true", "1"})
        self.cfg_ai: dict = {
            "ml_enabled": bool(settings.value("ai/ml_enabled", True)),
            "ml_contamination": float(settings.value("ai/contamination", 0.02)),
            "ml_refit_interval": int(settings.value("ai/refit_interval", 500)),
        }
        self.cfg_export: dict = {
            "format": str(settings.value("export/format", "csv")),
            "rotate_rows": int(settings.value("export/rotate_rows", 100000)),
        }

        # Bufor indeksowany od najstarszego
        self._packets_buffer: list[PacketInfo] = []

        # Statystyki
        self._total_packets: int = 0

        # Połączenie wyboru pakietu
        self.packet_viewer.packet_selected.connect(self._on_packet_selected)

        # Inicjalizacja AI z konfiguracji
        self._recreate_ai()

    # --- UI helpers ---
    def _create_actions(self) -> None:
        menu = self.menuBar().addMenu("Plik")
        action_start = QAction("Start", self)
        action_start.setShortcut("F5")
        action_start.triggered.connect(self.start_capture)
        menu.addAction(action_start)

        action_stop = QAction("Stop", self)
        action_stop.setShortcut("Shift+F5")
        action_stop.triggered.connect(self.stop_capture)
        menu.addAction(action_stop)

        menu.addSeparator()
        action_config = QAction("Konfiguracja...", self)
        action_config.setShortcut("Ctrl+,")
        action_config.triggered.connect(self.open_config)
        menu.addAction(action_config)

        menu.addSeparator()
        # Eksport logów
        action_export_packets = QAction("Eksportuj pakiety...", self)
        action_export_packets.triggered.connect(self.export_packets)
        menu.addAction(action_export_packets)

        action_export_alerts = QAction("Eksportuj alerty...", self)
        action_export_alerts.triggered.connect(self.export_alerts)
        menu.addAction(action_export_alerts)

        menu.addSeparator()
        action_exit = QAction("Zakończ", self)
        action_exit.triggered.connect(self.close)
        menu.addAction(action_exit)

        # Toolbar for quick access
        toolbar = QToolBar("Akcje", self)
        toolbar.addAction(action_start)
        toolbar.addAction(action_stop)
        toolbar.addAction(action_config)
        # Wypychacz (spacer), by kolejne widgety poszły na prawo
        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        # Etykieta z metrykami w prawym górnym rogu
        toolbar.addWidget(self.resource_label)
        self.addToolBar(toolbar)

    def _set_status(self, text: str) -> None:
        self.status_bar.showMessage(text)

    def _update_status(self) -> None:
        mode = "SIMULATION" if (self.sniffer and self.sniffer.use_simulation) else ("SCAPY" if self.sniffer else "Idle")
        self._set_status(f"{mode} | {self._total_packets} pkt")

    def _update_resource_label(self) -> None:
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            self.resource_label.setText(f"CPU: {cpu:.0f}%  RAM: {ram:.0f}%")
        except Exception:
            self.resource_label.setText("CPU: n/a  RAM: n/a")

    def _recreate_ai(self) -> None:
        try:
            self.ai_engine = AIEngine(
                ml_enabled=self.cfg_ai.get("ml_enabled", True),
                ml_contamination=self.cfg_ai.get("ml_contamination", 0.02),
                ml_refit_interval=self.cfg_ai.get("ml_refit_interval", 500),
            )
        except Exception:
            self.ai_engine = AIEngine()

    # --- Capture control ---
    def start_capture(self) -> None:
        if self.sniffer is not None:
            return
        self.sniffer = PacketSniffer(
            packet_queue=self.packet_queue,
            use_simulation=self.cfg_simulation,
            interface=self.cfg_interface,
            bpf_filter=self.cfg_bpf_filter,
        )
        self.sniffer.start()
        self._update_status()

    def stop_capture(self) -> None:
        if self.sniffer is None:
            return
        self.sniffer.stop()
        self.sniffer = None
        self._update_status()

    def open_config(self) -> None:
        dialog = ConfigDialog(
            self,
            interface=self.cfg_interface,
            bpf_filter=self.cfg_bpf_filter,
            simulation=self.cfg_simulation,
        )
        if dialog.exec_() == dialog.Accepted:
            (
                self.cfg_interface,
                self.cfg_bpf_filter,
                self.cfg_simulation,
                self.cfg_ai,
                self.cfg_export,
            ) = dialog.get_values()
            # Zapisz ustawienia
            settings = QSettings("Skaner3", "AI Network Sniffer")
            if self.cfg_interface is not None:
                settings.setValue("capture/interface", self.cfg_interface)
            settings.setValue("capture/bpf", self.cfg_bpf_filter or "")
            settings.setValue("capture/simulation", self.cfg_simulation)
            settings.setValue("ai/ml_enabled", self.cfg_ai.get("ml_enabled", True))
            settings.setValue("ai/contamination", self.cfg_ai.get("ml_contamination", 0.02))
            settings.setValue("ai/refit_interval", self.cfg_ai.get("ml_refit_interval", 500))
            settings.setValue("export/format", self.cfg_export.get("format", "csv"))
            settings.setValue("export/rotate_rows", self.cfg_export.get("rotate_rows", 100000))
            self._recreate_ai()
            self._set_status("Config updated")

    # --- Packet pipeline ---
    def _drain_queue(self) -> None:
        # Przerwij szybko, jeśli nic nie działa
        if self.sniffer is None and self.packet_queue.empty():
            return

        processed = 0
        # Batch update UI dla lepszej wydajności
        self.packet_viewer.table.setUpdatesEnabled(False)
        while processed < 200:  # ogranicz pętlę na tick
            try:
                packet_info = self.packet_queue.get_nowait()
            except Empty:
                break
            self._handle_packet(packet_info)
            processed += 1
        self.packet_viewer.table.setUpdatesEnabled(True)
        # Po batchu – przewiń na dół raz
        if processed > 0:
            self.packet_viewer.table.scrollToBottom()
        # Limit wierszy, aby nie rosnąć bez końca
        self._enforce_row_limit()

    def _handle_packet(self, packet_info: PacketInfo) -> None:
        # Zachowaj kolejność: od najstarszego do najnowszego
        self._packets_buffer.append(packet_info)
        row = packetinfo_to_row(packet_info)
        self.packet_viewer.add_packet_row(row)
        self._total_packets += 1
        if (self._total_packets % 20) == 0:
            self._update_status()

        ai = self.ai_engine.analyze_packet(packet_info)
        if ai.get("is_anomaly"):
            self.alert_viewer.add_alert("AI anomaly", row, score=float(ai.get("score", 0.0)))

        for alert in self.rule_engine.evaluate(packet_info):
            self.alert_viewer.add_alert(alert, row)

        # Aktualizuj status AI na bieżąco przy anomaliach
        try:
            self.ai_status.update_status(self.ai_engine.get_status())
        except Exception:
            pass

    # --- Selection details ---
    def _on_packet_selected(self, row_index: int) -> None:
        if row_index < 0 or row_index >= len(self._packets_buffer):
            return
        packet = self._packets_buffer[row_index]
        raw = packet.raw_bytes or b""

        from core.utils import bytes_to_ascii, bytes_to_hex_dump, geolocate_ip

        self.detail_hex.setPlainText(bytes_to_hex_dump(raw))
        self.detail_ascii.setPlainText(bytes_to_ascii(raw))

        geo_dst = geolocate_ip(packet.dst_ip)
        geo_src = geolocate_ip(packet.src_ip)
        geo_text = (
            f"DST: {packet.dst_ip} → {geo_dst.get('country')}, {geo_dst.get('regionName')}, {geo_dst.get('city')} (ISP: {geo_dst.get('isp')})\n"
            f"SRC: {packet.src_ip} → {geo_src.get('country')}, {geo_src.get('regionName')}, {geo_src.get('city')} (ISP: {geo_src.get('isp')})"
        )
        self.detail_geo.setText(geo_text)

    # --- Export ---
    def export_packets(self) -> None:
        try:
            from PyQt5.QtWidgets import QFileDialog
            import csv

            path, _ = QFileDialog.getSaveFileName(self, "Eksportuj pakiety", "packets.csv", "CSV Files (*.csv)")
            if not path:
                return
            headers = ["time", "src_ip", "dst_ip", "src_port", "dst_port", "protocol", "length"]
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for p in self._packets_buffer:
                    row = [
                        row_value
                        for row_value in [
                            *([row := packetinfo_to_row(p)] and [
                                row["time"], row["src_ip"], row["dst_ip"], row["src_port"], row["dst_port"], row["protocol"], row["length"]
                            ])
                        ]
                    ]
                    writer.writerow(row)
        except Exception:
            pass

    def export_alerts(self) -> None:
        try:
            from PyQt5.QtWidgets import QFileDialog
            path, _ = QFileDialog.getSaveFileName(self, "Eksportuj alerty", "alerts.txt", "Text Files (*.txt)")
            if not path:
                return
            with open(path, "w", encoding="utf-8") as f:
                for i in range(self.alert_viewer.list_widget.count()):
                    f.write(self.alert_viewer.list_widget.item(i).text())
                    f.write("\n")
        except Exception:
            pass

    def _enforce_row_limit(self, max_rows: int = 5000) -> None:
        table = self.packet_viewer.table
        while table.rowCount() > max_rows:
            # Usuń najstarszy (pierwszy) wiersz
            table.removeRow(0)
            if self._packets_buffer:
                self._packets_buffer.pop(0)
