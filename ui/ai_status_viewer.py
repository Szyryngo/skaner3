from __future__ import annotations

from typing import Dict

from PyQt5.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


class AIStatusViewer(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.label_summary = QLabel(self)
        self.text_details = QTextEdit(self)
        self.text_details.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label_summary)
        layout.addWidget(self.text_details)
        self.setLayout(layout)

    def update_status(self, status: Dict[str, object]) -> None:
        summary = (
            f"ML: {'ON' if status.get('ml_enabled') else 'OFF'} | "
            f"Model: {'ready' if status.get('model_ready') else 'loading'} | "
            f"Seen: {status.get('samples_seen', 0)} | "
            f"Last score: {status.get('last_score')}"
        )
        self.label_summary.setText(summary)

        reasons = status.get("last_reasons") or []
        decision = status.get("last_ml_decision")
        txt = [
            f"sklearn_available: {status.get('sklearn_available')}",
            f"contamination: {status.get('contamination')}",
            f"refit_interval: {status.get('refit_interval')}",
            f"buffer_size: {status.get('buffer_size')}",
            f"last_ml_decision: {decision}",
            f"last_reasons: {', '.join(map(str, reasons))}",
        ]
        self.text_details.setPlainText("\n".join(txt))


