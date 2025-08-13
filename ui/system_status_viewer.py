from __future__ import annotations

from typing import Dict

from PyQt5.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


class SystemStatusViewer(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.label_summary = QLabel(self)
        self.text_details = QTextEdit(self)
        self.text_details.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label_summary)
        layout.addWidget(self.text_details)
        self.setLayout(layout)

        # Initial state
        self.label_summary.setText("System: loading...")
        self.text_details.setPlainText("Ładowanie informacji o systemie...")

    def update_status(self, system_info: Dict[str, object]) -> None:
        """Update the system status display with new information."""
        # Format summary line
        os_name = system_info.get("os", "Unknown")
        cpu_count = system_info.get("cpu_count", 0)
        
        # Calculate RAM percentage if available
        ram_total = system_info.get("ram_total")
        ram_available = system_info.get("ram_available")
        ram_percent = "n/a"
        if ram_total and ram_available:
            ram_used_percent = ((ram_total - ram_available) / ram_total) * 100
            ram_percent = f"{ram_used_percent:.1f}%"
        
        # Calculate disk percentage if available
        disk_total = system_info.get("disk_total")
        disk_free = system_info.get("disk_free")
        disk_percent = "n/a"
        if disk_total and disk_free:
            disk_used_percent = ((disk_total - disk_free) / disk_total) * 100
            disk_percent = f"{disk_used_percent:.1f}%"

        summary = (
            f"OS: {os_name} | "
            f"CPU: {cpu_count} cores | "
            f"RAM: {ram_percent} used | "
            f"Disk: {disk_percent} used"
        )
        self.label_summary.setText(summary)

        # Format detailed information
        def format_bytes(bytes_value):
            """Convert bytes to human readable format."""
            if bytes_value is None:
                return "n/a"
            
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.1f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.1f} PB"

        details = [
            "=== SYSTEM OPERACYJNY ===",
            f"Nazwa: {system_info.get('os', 'Unknown')}",
            f"Wersja: {system_info.get('os_version', 'Unknown')}",
            "",
            "=== PROCESOR ===",
            f"Rdzenie fizyczne: {system_info.get('cpu_count', 'n/a')}",
            f"Wątki logiczne: {system_info.get('cpu_threads', 'n/a')}",
            f"Częstotliwość: {system_info.get('cpu_freq', 'n/a')} MHz" if system_info.get('cpu_freq') else "Częstotliwość: n/a",
            "",
            "=== PAMIĘĆ RAM ===",
            f"Całkowita: {format_bytes(system_info.get('ram_total'))}",
            f"Dostępna: {format_bytes(system_info.get('ram_available'))}",
            f"Wykorzystanie: {ram_percent}",
            "",
            "=== DYSK ===",
            f"Całkowita pojemność: {format_bytes(system_info.get('disk_total'))}",
            f"Wolne miejsce: {format_bytes(system_info.get('disk_free'))}",
            f"Wykorzystanie: {disk_percent}",
        ]
        
        self.text_details.setPlainText("\n".join(details))