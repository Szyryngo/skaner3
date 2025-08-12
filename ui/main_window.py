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
import json
import psutil

from core.ai_engine import AIEngine
from core import APP_NAME, __version__
from core.packet_sniffer import PacketSniffer
from core.rules import RuleEngine
from core.utils import packetinfo_to_row, PacketInfo, LogWriter
from .ai_status_viewer import AIStatusViewer
from .alert_viewer import AlertViewer
from .config_dialog import ConfigDialog
from .packet_viewer import PacketViewer
from .system_diagnostics_tab import SystemDiagnosticsTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{__version__}")
        self.resize(1000, 600)

        # Model/engine
        self.ai_engine = AIEngine()
        self.rule_engine = RuleEngine()

        # Kolejka pakietów od sniffera
        self.packet_queue: Queue[PacketInfo] = Queue(maxsize=5000)
        self.sniffer: Optional[PacketSniffer] = None
        
        # Bufor pakietów dla UI
        self._packets_buffer: list[PacketInfo] = []
        self._total_packets = 0

        # UI
        self.tabs = QTabWidget(self)
        self.packet_viewer = PacketViewer(self)
        self.alert_viewer = AlertViewer(self)
        self.ai_status = AIStatusViewer(self)
        self.system_diagnostics = SystemDiagnosticsTab(self)
        
        # Przekaż bufor pakietów do AlertViewer dla podglądu
        self.alert_viewer.set_packets_buffer(self._packets_buffer)

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

        self.splitter = QSplitter(self)
        self.splitter.addWidget(self.packet_viewer)
        self.splitter.addWidget(detail_widget)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)

        tab_packets = QWidget(self)
        tab_packets_layout = QVBoxLayout(tab_packets)
        tab_packets_layout.addWidget(self.splitter)

        self.tabs.addTab(tab_packets, "Pakiety")
        self.tabs.addTab(self.alert_viewer, "Alerty")
        self.tabs.addTab(self.ai_status, "AI")
        self.tabs.addTab(self.system_diagnostics, "Diagnostyka systemu i optymalizacja AI")
        self.setCentralWidget(self.tabs)

        # Status bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self._set_status("Idle")

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
            "ml_stream_enabled": bool(settings.value("ai/stream_enabled", True)),
            "stream_z_threshold": float(settings.value("ai/stream_z", 2.5)),
            "combined_threshold": float(settings.value("ai/combined_threshold", 0.7)),
            "alerts_only_anomalies": bool(settings.value("ai/alerts_only_anomalies", False)),
        }
        self.cfg_export: dict = {
            "format": str(settings.value("export/format", "csv")),
            "format_packets": str(settings.value("export/format_packets", "")),
            "format_alerts": str(settings.value("export/format_alerts", "")),
            "rotate_rows": int(settings.value("export/rotate_rows", 100000)),
            "auto": bool(settings.value("export/auto", False)),
            "dir": str(settings.value("export/dir", "")),
            "cleanup_days": int(settings.value("export/cleanup_days", 0)),
        }

        # Statystyki
        self._total_packets: int = 0
        self._packet_logger: Optional[LogWriter] = None
        self._alert_logger: Optional[LogWriter] = None

        # Połączenie wyboru pakietu
        self.packet_viewer.packet_selected.connect(self._on_packet_selected)

        # Menu/Actions
        self._create_actions()

        # Timer do przetwarzania pakietów → UI
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._drain_queue)
        self.timer.start()

        # Inicjalizacja AI z konfiguracji
        self._recreate_ai()
        
        # Przekaż silnik AI do zakładki diagnostyki
        self.system_diagnostics.set_ai_engine(self.ai_engine)
        
        # Przywrócenie UI
        self._restore_ui_settings()

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
        action_save_cfg = QAction("Zapisz konfigurację...", self)
        action_save_cfg.triggered.connect(self.export_config)
        menu.addAction(action_save_cfg)

        action_load_cfg = QAction("Wczytaj konfigurację...", self)
        action_load_cfg.triggered.connect(self.import_config)
        menu.addAction(action_load_cfg)

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

    # --- Settings (UI/state) ---
    def _save_ui_settings(self) -> None:
        settings = QSettings("Skaner3", "AI Network Sniffer")
        try:
            geom_hex = bytes(self.saveGeometry().toHex()).decode("ascii")
            settings.setValue("ui/geometry", geom_hex)
        except Exception:
            pass
        try:
            settings.setValue("ui/tabs_index", self.tabs.currentIndex())
        except Exception:
            pass
        try:
            settings.setValue("ui/splitter_sizes", self.splitter.sizes())
        except Exception:
            pass

    def _restore_ui_settings(self) -> None:
        settings = QSettings("Skaner3", "AI Network Sniffer")
        try:
            geom_hex = settings.value("ui/geometry", None, type=str)
            if geom_hex:
                self.restoreGeometry(bytes.fromhex(geom_hex))
        except Exception:
            pass
        try:
            idx = settings.value("ui/tabs_index", 0, type=int)
            self.tabs.setCurrentIndex(int(idx))
        except Exception:
            pass
        try:
            sizes = settings.value("ui/splitter_sizes", None)
            if isinstance(sizes, list) and sizes:
                self.splitter.setSizes([int(x) for x in sizes])
        except Exception:
            pass

    def _recreate_ai(self) -> None:
        try:
            self.ai_engine = AIEngine(
                ml_enabled=self.cfg_ai.get("ml_enabled", True),
                ml_contamination=self.cfg_ai.get("ml_contamination", 0.02),
                ml_refit_interval=self.cfg_ai.get("ml_refit_interval", 500),
                ml_stream_enabled=self.cfg_ai.get("ml_stream_enabled", True),
                stream_z_threshold=self.cfg_ai.get("stream_z_threshold", 2.5),
                combined_threshold=self.cfg_ai.get("combined_threshold", 0.7),
            )
        except Exception:
            self.ai_engine = AIEngine()
        
        # Aktualizuj referencję w zakładce diagnostyki
        if hasattr(self, 'system_diagnostics'):
            self.system_diagnostics.set_ai_engine(self.ai_engine)

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
        self._setup_loggers()
        self._update_status()

    def stop_capture(self) -> None:
        if self.sniffer is None:
            return
        self.sniffer.stop()
        self.sniffer = None
        self._teardown_loggers()
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
            settings.setValue("export/format_packets", self.cfg_export.get("format_packets", ""))
            settings.setValue("export/format_alerts", self.cfg_export.get("format_alerts", ""))
            settings.setValue("export/rotate_rows", self.cfg_export.get("rotate_rows", 100000))
            settings.setValue("ai/stream_enabled", self.cfg_ai.get("ml_stream_enabled", True))
            settings.setValue("ai/stream_z", self.cfg_ai.get("stream_z_threshold", 2.5))
            settings.setValue("ai/combined_threshold", self.cfg_ai.get("combined_threshold", 0.7))
            settings.setValue("ai/alerts_only_anomalies", self.cfg_ai.get("alerts_only_anomalies", False))
            settings.setValue("export/auto", self.cfg_export.get("auto", False))
            settings.setValue("export/dir", self.cfg_export.get("dir", ""))
            settings.setValue("export/cleanup_days", self.cfg_export.get("cleanup_days", 0))
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
        
        # Analiza AI przed dodaniem do UI
        ai = self.ai_engine.analyze_packet(packet_info)
        score = float(ai.get("score", 0.0))
        
        # Dodaj pakiet z kolorowaniem według score
        self.packet_viewer.add_packet_row(row, score=score)
        self._total_packets += 1
        if (self._total_packets % 20) == 0:
            self._update_status()

        # Dodaj alert jeśli to anomalia
        if ai.get("is_anomaly"):
            self.alert_viewer.add_alert("AI anomaly", row, score=score)
            self._log_alert(["AI anomaly", str(score), row["time"], row["src_ip"], row["dst_ip"], row["protocol"], row["length"]])

        # Dodaj alerty z reguł (jeśli nie tylko anomalie)
        if not self.cfg_ai.get("alerts_only_anomalies", False):
            for alert in self.rule_engine.evaluate(packet_info):
                self.alert_viewer.add_alert(alert, row)
                self._log_alert([alert, "", row["time"], row["src_ip"], row["dst_ip"], row["protocol"], row["length"]])

        # Aktualizuj status AI na bieżąco przy anomaliach
        try:
            self.ai_status.update_status(self.ai_engine.get_status())
        except Exception:
            pass

        # Zapis pakietu
        self._log_packet(row)

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
                    row = packetinfo_to_row(p)
                    writer.writerow([
                        row["time"], row["src_ip"], row["dst_ip"], 
                        row["src_port"], row["dst_port"], row["protocol"], row["length"]
                    ])
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

    # --- Config import/export ---
    def export_config(self) -> None:
        try:
            from PyQt5.QtWidgets import QFileDialog
            path, _ = QFileDialog.getSaveFileName(self, "Zapisz konfigurację", "config.json", "JSON (*.json)")
            if not path:
                return
            cfg = {
                "capture": {
                    "interface": self.cfg_interface,
                    "bpf": self.cfg_bpf_filter,
                    "simulation": self.cfg_simulation,
                },
                "ai": self.cfg_ai,
                "export": self.cfg_export,
                "ui": {
                    "tabs_index": self.tabs.currentIndex(),
                    "splitter_sizes": self.splitter.sizes(),
                    "geometry": bytes(self.saveGeometry().toHex()).decode("ascii"),
                },
                "version": 1,
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def import_config(self) -> None:
        try:
            from PyQt5.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(self, "Wczytaj konfigurację", "", "JSON (*.json)")
            if not path:
                return
            with open(path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cap = cfg.get("capture", {})
            ai = cfg.get("ai", {})
            exp = cfg.get("export", {})
            ui_state = cfg.get("ui", {})

            # Zapis do QSettings
            settings = QSettings("Skaner3", "AI Network Sniffer")
            if cap.get("interface") is not None:
                settings.setValue("capture/interface", cap.get("interface"))
            settings.setValue("capture/bpf", cap.get("bpf", ""))
            settings.setValue("capture/simulation", bool(cap.get("simulation", True)))
            # AI
            for key, qkey in [
                ("ml_enabled", "ai/ml_enabled"),
                ("ml_contamination", "ai/contamination"),
                ("ml_refit_interval", "ai/refit_interval"),
                ("ml_stream_enabled", "ai/stream_enabled"),
                ("stream_z_threshold", "ai/stream_z"),
                ("combined_threshold", "ai/combined_threshold"),
                ("alerts_only_anomalies", "ai/alerts_only_anomalies"),
            ]:
                if key in ai:
                    settings.setValue(qkey, ai[key])
            # Export
            for key, qkey in [
                ("format", "export/format"),
                ("format_packets", "export/format_packets"),
                ("format_alerts", "export/format_alerts"),
                ("rotate_rows", "export/rotate_rows"),
                ("auto", "export/auto"),
                ("dir", "export/dir"),
                ("cleanup_days", "export/cleanup_days"),
            ]:
                if key in exp:
                    settings.setValue(qkey, exp[key])
            # UI
            try:
                if "geometry" in ui_state:
                    self.restoreGeometry(bytes.fromhex(ui_state["geometry"]))
                if "tabs_index" in ui_state:
                    self.tabs.setCurrentIndex(int(ui_state["tabs_index"]))
                if "splitter_sizes" in ui_state and ui_state["splitter_sizes"]:
                    self.splitter.setSizes([int(x) for x in ui_state["splitter_sizes"]])
            except Exception:
                pass

            # Odśwież lokalne struktury i AI
            self.cfg_interface = settings.value("capture/interface", None, type=str)
            self.cfg_bpf_filter = settings.value("capture/bpf", None, type=str)
            sim_val = settings.value("capture/simulation", True)
            self.cfg_simulation = bool(sim_val if isinstance(sim_val, bool) else str(sim_val).lower() in {"true", "1"})
            self.cfg_ai.update(ai)
            self.cfg_export.update(exp)
            self._recreate_ai()
            self._set_status("Config loaded")
        except Exception:
            pass

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._save_ui_settings()
        super().closeEvent(event)

    def _enforce_row_limit(self, max_rows: int = 5000) -> None:
        table = self.packet_viewer.table
        while table.rowCount() > max_rows:
            # Usuń najstarszy (pierwszy) wiersz
            table.removeRow(0)
            if self._packets_buffer:
                self._packets_buffer.pop(0)

    # --- Logging helpers ---
    def _setup_loggers(self) -> None:
        if not self.cfg_export.get("auto", False):
            self._teardown_loggers()
            return
        
        # Wybór formatów
        fmt_global = self.cfg_export.get("format", "csv")
        fmt_packets = (self.cfg_export.get("format_packets") or fmt_global)
        fmt_alerts = (self.cfg_export.get("format_alerts") or fmt_global)
        is_csv_packets = (fmt_packets == "csv")
        is_csv_alerts = (fmt_alerts == "csv")
        rotate = int(self.cfg_export.get("rotate_rows", 100000))
        base_dir = self.cfg_export.get("dir", "").strip() or "."
        import os
        try:
            os.makedirs(base_dir, exist_ok=True)
        except Exception:
            base_dir = "."
        try:
            self._packet_logger = LogWriter(os.path.join(base_dir, f"packets_log.{ 'csv' if is_csv_packets else 'txt'}"), is_csv=is_csv_packets, max_rows_per_file=rotate, headers=["time","src_ip","dst_ip","src_port","dst_port","protocol","length"])
            self._alert_logger = LogWriter(os.path.join(base_dir, f"alerts_log.{ 'csv' if is_csv_alerts else 'txt'}"), is_csv=is_csv_alerts, max_rows_per_file=rotate, headers=["type","score","time","src_ip","dst_ip","protocol","length"])
        except Exception:
            self._packet_logger = None
            self._alert_logger = None
        
        # Auto-cleanup
        try:
            days = int(self.cfg_export.get("cleanup_days", 0))
            if days > 0:
                self._cleanup_old_logs(base_dir, days)
        except Exception:
            pass

    def _teardown_loggers(self) -> None:
        try:
            if self._packet_logger:
                self._packet_logger.close()
        finally:
            self._packet_logger = None
        try:
            if self._alert_logger:
                self._alert_logger.close()
        finally:
            self._alert_logger = None

    def _log_packet(self, row: dict) -> None:
        if not self._packet_logger:
            return
        try:
            self._packet_logger.write_row([row.get("time",""), row.get("src_ip",""), row.get("dst_ip",""), row.get("src_port",""), row.get("dst_port",""), row.get("protocol",""), row.get("length","")])
        except Exception:
            pass

    def _log_alert(self, row: list[str]) -> None:
        if not self._alert_logger:
            return
        try:
            self._alert_logger.write_row(row)
        except Exception:
            pass

    def _cleanup_old_logs(self, base_dir: str, days: int) -> None:
        import os, time
        cutoff = time.time() - days * 86400
        for name in os.listdir(base_dir):
            if name.startswith("packets_log.") or name.startswith("alerts_log."):
                path = os.path.join(base_dir, name)
                try:
                    if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                        os.remove(path)
                except Exception:
                    continue
