from __future__ import annotations

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QLabel, 
    QVBoxLayout, 
    QWidget, 
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox
)

from core.system_info import get_system_status


class SystemStatusViewer(QWidget):
    """
    Widok statusu systemu - prezentuje informacje o CPU, RAM, 
    interfejsach sieciowych i czasie działania systemu.
    """
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        
        # Główny layout
        layout = QVBoxLayout(self)
        
        # Grupa - Zasoby systemowe
        resources_group = QGroupBox("Zasoby systemowe", self)
        resources_layout = QVBoxLayout(resources_group)
        
        # Etykiety statusu
        self.cpu_label = QLabel("CPU: --%", self)
        self.ram_label = QLabel("RAM: --% (-- / -- GB)", self)
        self.threads_label = QLabel("Wątki: --", self)
        self.uptime_label = QLabel("Uptime: --", self)
        
        resources_layout.addWidget(self.cpu_label)
        resources_layout.addWidget(self.ram_label)
        resources_layout.addWidget(self.threads_label)
        resources_layout.addWidget(self.uptime_label)
        
        layout.addWidget(resources_group)
        
        # Grupa - Interfejsy sieciowe
        network_group = QGroupBox("Interfejsy sieciowe", self)
        network_layout = QVBoxLayout(network_group)
        
        # Tabela interfejsów
        self.interfaces_table = QTableWidget(self)
        self.interfaces_table.setColumnCount(4)
        self.interfaces_table.setHorizontalHeaderLabels(["Nazwa", "Status", "Typ", "Adres IPv4"])
        
        # Ustawienia tabeli
        header = self.interfaces_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Nazwa
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Typ
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # IPv4
        
        self.interfaces_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.interfaces_table.setAlternatingRowColors(True)
        
        network_layout.addWidget(self.interfaces_table)
        layout.addWidget(network_group)
        
        # Etykieta czasu ostatniej aktualizacji
        self.last_update_label = QLabel("Ostatnia aktualizacja: --", self)
        layout.addWidget(self.last_update_label)
        
        # Timer do odświeżania danych
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.refresh_status)
        self.update_timer.setInterval(2000)  # Aktualizacja co 2 sekundy
        self.update_timer.start()
        
        # Początkowe odświeżenie
        self.refresh_status()
    
    def refresh_status(self) -> None:
        """Odświeża dane statusu systemu."""
        try:
            status = get_system_status()
            self._update_resources(status)
            self._update_network_interfaces(status)
            
            from datetime import datetime
            now = datetime.now().strftime("%H:%M:%S")
            self.last_update_label.setText(f"Ostatnia aktualizacja: {now}")
            
        except Exception:
            # W przypadku błędu, zachowaj poprzednie dane
            pass
    
    def _update_resources(self, status: dict) -> None:
        """Aktualizuje informacje o zasobach systemowych."""
        try:
            # CPU
            cpu_percent = status.get("cpu_percent", 0.0)
            self.cpu_label.setText(f"CPU: {cpu_percent:.1f}%")
            
            # RAM
            ram_percent = status.get("ram_percent", 0.0)
            ram_used = status.get("ram_used", 0)
            ram_total = status.get("ram_total", 0)
            
            if ram_total > 0:
                ram_used_gb = ram_used / (1024**3)
                ram_total_gb = ram_total / (1024**3)
                self.ram_label.setText(f"RAM: {ram_percent:.1f}% ({ram_used_gb:.1f} / {ram_total_gb:.1f} GB)")
            else:
                self.ram_label.setText(f"RAM: {ram_percent:.1f}%")
            
            # Wątki
            thread_count = status.get("thread_count", 0)
            self.threads_label.setText(f"Wątki: {thread_count}")
            
            # Uptime
            uptime = status.get("uptime", "nieznany")
            self.uptime_label.setText(f"Uptime: {uptime}")
            
        except Exception:
            pass
    
    def _update_network_interfaces(self, status: dict) -> None:
        """Aktualizuje tabelę interfejsów sieciowych."""
        try:
            interfaces = status.get("network_interfaces", [])
            
            # Wyczyść tabelę
            self.interfaces_table.setRowCount(0)
            
            # Dodaj interfejsy
            for i, interface in enumerate(interfaces):
                self.interfaces_table.insertRow(i)
                
                # Nazwa
                name_item = QTableWidgetItem(interface.get("name", ""))
                self.interfaces_table.setItem(i, 0, name_item)
                
                # Status
                status_text = interface.get("status", "nieznany")
                status_item = QTableWidgetItem(status_text)
                
                # Kolorowanie statusu
                if status_text == "aktywny":
                    status_item.setBackground(self.palette().color(self.palette().Base))
                elif status_text == "nieaktywny":
                    status_item.setBackground(self.palette().color(self.palette().AlternateBase))
                
                self.interfaces_table.setItem(i, 1, status_item)
                
                # Typ
                type_item = QTableWidgetItem(interface.get("type", "inne"))
                self.interfaces_table.setItem(i, 2, type_item)
                
                # IPv4
                ipv4_item = QTableWidgetItem(interface.get("ipv4", "brak"))
                self.interfaces_table.setItem(i, 3, ipv4_item)
                
        except Exception:
            pass