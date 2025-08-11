from __future__ import annotations

from typing import Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QComboBox,
    QCheckBox,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QHBoxLayout,
    QWidget,
)


class ConfigDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None, *, interface: Optional[str] = None, bpf_filter: Optional[str] = None, simulation: bool = True) -> None:
        super().__init__(parent)
        self.setWindowTitle("Konfiguracja przechwytywania")

        from core.utils import list_network_interfaces

        self.select_interface = QComboBox(self)
        self.checkbox_show_inactive = QCheckBox("Pokaż nieaktywne interfejsy", self)
        self.checkbox_show_inactive.setChecked(False)

        def _color_for_type(type_name: str) -> QColor:
            mapping = {
                "Wi‑Fi": QColor(25, 118, 210),     # blue
                "Ethernet": QColor(46, 125, 50),   # green
                "Loopback": QColor(97, 97, 97),    # gray
                "Virtual": QColor(123, 31, 162),   # purple
                "Cellular": QColor(230, 81, 0),    # orange
            }
            return mapping.get(type_name, QColor(33, 33, 33))

        def _emoji_for_type(type_name: str) -> str:
            return {
                "Wi‑Fi": "📶",
                "Ethernet": "🖧",
                "Loopback": "♾",
                "Virtual": "🌐",
                "Cellular": "📡",
                "Other": "🧩",
            }.get(type_name, "🧩")

        def populate_interfaces() -> None:
            self.select_interface.clear()
            ints = list_network_interfaces(show_inactive=self.checkbox_show_inactive.isChecked())
            for iface in ints:
                emoji = _emoji_for_type(iface['type'])
                ip_txt = f" ({iface['ipv4']})" if iface['ipv4'] else ""
                label = f"{emoji} {iface['type']}: {iface['name']}{ip_txt}"
                self.select_interface.addItem(label, iface['id'])
                idx = self.select_interface.count() - 1
                self.select_interface.setItemData(idx, _color_for_type(iface['type']), Qt.ForegroundRole)
            # Ustaw wskazany, jeśli jest
            if interface:
                idx = self.select_interface.findData(interface)
                if idx >= 0:
                    self.select_interface.setCurrentIndex(idx)

        populate_interfaces()
        self.checkbox_show_inactive.toggled.connect(populate_interfaces)

        self.input_filter = QLineEdit(self)
        self.input_filter.setPlaceholderText("np. tcp port 80")
        if bpf_filter:
            self.input_filter.setText(bpf_filter)

        self.checkbox_simulation = QCheckBox("Tryb symulacji (bez scapy)", self)
        self.checkbox_simulation.setChecked(simulation)

        # Sekcja AI
        ai_group = QGroupBox("AI")
        ai_form = QFormLayout(ai_group)
        self.checkbox_ai_enabled = QCheckBox("Włącz IsolationForest", ai_group)
        self.checkbox_ai_enabled.setChecked(True)
        self.spin_ai_combined_threshold = QDoubleSpinBox(ai_group)
        self.spin_ai_combined_threshold.setRange(0.1, 3.0)
        self.spin_ai_combined_threshold.setSingleStep(0.05)
        self.spin_ai_combined_threshold.setValue(0.7)
        self.spin_ai_contamination = QDoubleSpinBox(ai_group)
        self.spin_ai_contamination.setRange(0.001, 0.5)
        self.spin_ai_contamination.setSingleStep(0.001)
        self.spin_ai_contamination.setValue(0.02)
        self.spin_ai_refit = QSpinBox(ai_group)
        self.spin_ai_refit.setRange(100, 20000)
        self.spin_ai_refit.setSingleStep(100)
        self.spin_ai_refit.setValue(500)
        self.checkbox_ai_stream = QCheckBox("Włącz model strumieniowy (Half-Space Trees)", ai_group)
        ai_form.addRow(self.checkbox_ai_enabled)
        ai_form.addRow("Combined threshold:", self.spin_ai_combined_threshold)
        ai_form.addRow("Contamination:", self.spin_ai_contamination)
        ai_form.addRow("Refit interval:", self.spin_ai_refit)
        self.spin_ai_stream_threshold = QDoubleSpinBox(ai_group)
        self.spin_ai_stream_threshold.setRange(0.5, 10.0)
        self.spin_ai_stream_threshold.setSingleStep(0.1)
        self.spin_ai_stream_threshold.setValue(2.5)
        ai_form.addRow(self.checkbox_ai_stream)
        ai_form.addRow("Z-threshold (stream):", self.spin_ai_stream_threshold)

        # Sekcja Alerty
        alerts_group = QGroupBox("Alerty")
        alerts_form = QFormLayout(alerts_group)
        self.checkbox_alerts_only_anomalies = QCheckBox("Tylko anomalie (wyłącz alerty reguł)", alerts_group)
        self.checkbox_alerts_only_anomalies.setChecked(False)
        alerts_form.addRow(self.checkbox_alerts_only_anomalies)

        # Sekcja eksportu
        export_group = QGroupBox("Eksport logów")
        export_form = QFormLayout(export_group)
        self.combo_export_format = QComboBox(export_group)
        self.combo_export_format.addItems(["CSV", "TXT"])
        self.spin_export_rotate = QSpinBox(export_group)
        self.spin_export_rotate.setRange(1000, 1000000)
        self.spin_export_rotate.setSingleStep(1000)
        self.spin_export_rotate.setValue(100000)
        self.checkbox_export_auto = QCheckBox("Automatyczny zapis pakietów i alertów", export_group)
        # Katalog docelowy
        self.input_export_dir = QLineEdit(export_group)
        self.input_export_dir.setReadOnly(True)
        btn_pick_dir = QPushButton("Wybierz...", export_group)
        def pick_dir():
            path = QFileDialog.getExistingDirectory(self, "Wybierz katalog docelowy")
            if path:
                self.input_export_dir.setText(path)
        btn_pick_dir.clicked.connect(pick_dir)
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.input_export_dir)
        dir_layout.addWidget(btn_pick_dir)
        export_form.addRow("Format:", self.combo_export_format)
        export_form.addRow("Rotacja co (wiersze):", self.spin_export_rotate)
        export_form.addRow(self.checkbox_export_auto)
        export_form.addRow("Katalog docelowy:", dir_layout)

        form = QFormLayout()
        form.addRow("Interfejs:", self.select_interface)
        form.addRow("", self.checkbox_show_inactive)
        form.addRow("BPF filter:", self.input_filter)
        form.addRow("", self.checkbox_simulation)
        form.addRow(ai_group)
        form.addRow(alerts_group)
        # Reset do domyślnych
        btn_reset = QPushButton("Przywróć domyślne", self)
        def reset_defaults():
            # Capture
            self.select_interface.setCurrentIndex(0 if self.select_interface.count() else -1)
            self.input_filter.setText("")
            self.checkbox_simulation.setChecked(True)
            # AI
            self.checkbox_ai_enabled.setChecked(True)
            self.spin_ai_combined_threshold.setValue(0.7)
            self.spin_ai_contamination.setValue(0.02)
            self.spin_ai_refit.setValue(500)
            self.checkbox_ai_stream.setChecked(True)
            self.spin_ai_stream_threshold.setValue(2.5)
            self.checkbox_alerts_only_anomalies.setChecked(False)
            # Export
            self.combo_export_format.setCurrentIndex(0)
            self.spin_export_rotate.setValue(100000)
            self.checkbox_export_auto.setChecked(False)
            self.input_export_dir.setText("")
        btn_reset.clicked.connect(reset_defaults)

        form.addRow(export_group)
        form.addRow(btn_reset)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        form.addRow(buttons)
        self.setLayout(form)

    def get_values(self) -> Tuple[Optional[str], Optional[str], bool, dict, dict]:
        interface = self.select_interface.currentData()
        bpf_filter = self.input_filter.text().strip() or None
        simulation = self.checkbox_simulation.isChecked()
        ai_cfg = {
            "ml_enabled": bool(self.checkbox_ai_enabled.isChecked()),
            "ml_contamination": float(self.spin_ai_contamination.value()),
            "ml_refit_interval": int(self.spin_ai_refit.value()),
            "ml_stream_enabled": bool(self.checkbox_ai_stream.isChecked()),
            "stream_z_threshold": float(self.spin_ai_stream_threshold.value()),
            "combined_threshold": float(self.spin_ai_combined_threshold.value()),
            "alerts_only_anomalies": bool(self.checkbox_alerts_only_anomalies.isChecked()),
        }
        export_cfg = {
            "format": self.combo_export_format.currentText().lower(),
            "rotate_rows": int(self.spin_export_rotate.value()),
            "auto": bool(self.checkbox_export_auto.isChecked()),
            "dir": self.input_export_dir.text().strip() or "",
        }
        return interface, bpf_filter, simulation, ai_cfg, export_cfg
