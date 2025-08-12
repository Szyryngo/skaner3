from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout
from core.system_info import get_system_info
from core.ai_engine import get_ai_status

class AiStatusViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.system_group = QGroupBox("Status systemu")
        self.ai_group = QGroupBox("Status AI")

        self.system_layout = QFormLayout()
        self.ai_layout = QFormLayout()
        self.system_group.setLayout(self.system_layout)
        self.ai_group.setLayout(self.ai_layout)

        self.layout.addWidget(self.system_group)
        self.layout.addWidget(self.ai_group)

        self.refresh_status()

    def refresh_status(self):
        # Czyść stare widgety
        while self.system_layout.count():
            self.system_layout.removeRow(0)
        while self.ai_layout.count():
            self.ai_layout.removeRow(0)
        # Dodaj aktualne dane
        for k, v in get_system_info().items():
            self.system_layout.addRow(QLabel(str(k)), QLabel(str(v)))
        for k, v in get_ai_status().items():
            self.ai_layout.addRow(QLabel(str(k)), QLabel(str(v)))


