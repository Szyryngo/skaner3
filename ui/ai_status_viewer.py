from __future__ import annotations

from typing import Dict

from PyQt5.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


class AIStatusViewer(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.label_summary = QLabel(self)
        self.text_details = QTextEdit(self)
        self.text_details.setReadOnly(True)
        
        # Liczniki anomalii
        self._anomaly_count = 0
        self._last_effectiveness = None

        layout = QVBoxLayout(self)
        layout.addWidget(self.label_summary)
        layout.addWidget(self.text_details)
        self.setLayout(layout)

    def update_status(self, status: Dict[str, object]) -> None:
        summary = (
            f"ML: {'ON' if status.get('ml_enabled') else 'OFF'} | "
            f"Model: {'ready' if status.get('model_ready') else 'loading'} | "
            f"Seen: {status.get('samples_seen', 0)} | "
            f"Last score: {status.get('last_score')} | "
            f"Anomalies: {self._anomaly_count}"
        )
        self.label_summary.setText(summary)

        reasons = status.get("last_reasons") or []
        decision = status.get("last_ml_decision")
        stream_enabled = status.get("stream_enabled")
        stream_z = status.get("last_stream_z")
        stream_score = status.get("last_stream_score")
        txt = [
            f"sklearn_available: {status.get('sklearn_available')}",
            f"contamination: {status.get('contamination')}",
            f"refit_interval: {status.get('refit_interval')}",
            f"buffer_size: {status.get('buffer_size')}",
            f"last_ml_decision: {decision}",
            f"river_available: {status.get('river_available')}",
            f"stream_enabled: {stream_enabled}",
            f"stream_z_threshold: {status.get('stream_threshold_z')}",
            f"stream_count: {status.get('stream_count')}",
            f"last_stream_score: {stream_score}",
            f"last_stream_z: {stream_z}",
            f"last_reasons: {', '.join(map(str, reasons))}",
            f"anomaly_count: {self._anomaly_count}",
            f"last_effectiveness: {self._last_effectiveness}",
        ]
        self.text_details.setPlainText("\n".join(txt))
        
    def increment_anomaly_count(self) -> None:
        """Zwiększ licznik wykrytych anomalii"""
        self._anomaly_count += 1
        
    def set_last_effectiveness(self, effectiveness: float) -> None:
        """Ustaw ostatni wynik skuteczności"""
        self._last_effectiveness = effectiveness
        
    def reset_counters(self) -> None:
        """Resetuj liczniki"""
        self._anomaly_count = 0
        self._last_effectiveness = None


