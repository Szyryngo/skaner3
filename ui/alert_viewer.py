from __future__ import annotations

from typing import Dict, Optional

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QWidget, QVBoxLayout


class AlertViewer(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.list_widget = QListWidget(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def add_alert(self, message: str, packet_row: Dict[str, str], score: Optional[float] = None) -> None:
        score_text = f" [score={score}]" if score is not None else ""
        summary = (
            f"{message}{score_text} | {packet_row.get('time','')} "
            f"{packet_row.get('src_ip','')}:{packet_row.get('src_port','')} -> "
            f"{packet_row.get('dst_ip','')}:{packet_row.get('dst_port','')} "
            f"{packet_row.get('protocol','')}/{packet_row.get('length','')}"
        )
        item = QListWidgetItem(summary, self.list_widget)
        # Koloruj według score
        if score is not None:
            if score >= 0.9:
                item.setBackground(QColor(255, 200, 200))
            elif score >= 0.7:
                item.setBackground(QColor(255, 230, 200))
