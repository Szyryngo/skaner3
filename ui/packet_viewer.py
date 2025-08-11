from __future__ import annotations

from typing import Dict, List, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QHeaderView,
    QHBoxLayout,
    QLineEdit,
    QMenu,
    QAction,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QVBoxLayout,
)


class PacketViewer(QWidget):
    packet_selected = pyqtSignal(int)
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Filtry
        self.filter_text = QLineEdit(self)
        self.filter_text.setPlaceholderText("Szukaj: IP, port, proto...")
        self.filter_text.setClearButtonEnabled(True)
        self.filter_protocol = QComboBox(self)
        self.filter_protocol.addItems(["ALL", "TCP", "UDP", "IP"])

        filters_layout = QHBoxLayout()
        filters_layout.addWidget(self.filter_text)
        filters_layout.addWidget(self.filter_protocol)

        self.table = QTableWidget(0, 7, self)
        self.table.setHorizontalHeaderLabels(
            ["Time", "Src IP", "Dst IP", "Src Port", "Dst Port", "Proto", "Len"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.itemSelectionChanged.connect(self._emit_selected_index)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

        layout = QVBoxLayout(self)
        layout.addLayout(filters_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

        # Podłącz filtrację
        self.filter_text.textChanged.connect(self.apply_filters)
        self.filter_protocol.currentIndexChanged.connect(self.apply_filters)

    def add_packet_row(self, row: Dict[str, str]) -> None:
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)
        for col_index, key in enumerate(["time", "src_ip", "dst_ip", "src_port", "dst_port", "protocol", "length"]):
            self.table.setItem(row_index, col_index, QTableWidgetItem(row.get(key, "")))
        # Opcjonalnie można przewijać do końca
        self.table.scrollToBottom()

    def clear_all(self) -> None:
        self.table.setRowCount(0)

    def _emit_selected_index(self) -> None:
        selected = self.table.selectedIndexes()
        if not selected:
            return
        # Wybór całego wiersza, weź indeks wiersza pierwszej kolumny
        row_index = selected[0].row()
        self.packet_selected.emit(row_index)

    # --- Filtry i wyszukiwanie ---
    def apply_filters(self) -> None:
        text = self.filter_text.text().strip().lower()
        proto_filter = self.filter_protocol.currentText()
        for row in range(self.table.rowCount()):
            show = True
            # Proto
            if proto_filter != "ALL":
                proto_item = self.table.item(row, 5)
                if not proto_item or proto_item.text().upper() != proto_filter:
                    show = False
            # Tekst
            if show and text:
                matched = False
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item and text in item.text().lower():
                        matched = True
                        break
                show = matched
            self.table.setRowHidden(row, not show)

    # --- Menu kontekstowe ---
    def _open_context_menu(self, pos) -> None:
        index = self.table.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        src_ip = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        dst_ip = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
        proto = self.table.item(row, 5).text() if self.table.item(row, 5) else ""

        menu = QMenu(self)
        act_copy = QAction("Kopiuj wiersz", self)
        act_filter_src = QAction(f"Filtruj: SRC={src_ip}", self)
        act_filter_dst = QAction(f"Filtruj: DST={dst_ip}", self)
        act_proto = QAction(f"Filtruj: PROTO={proto}", self)

        def do_copy():
            texts = [self.table.item(row, c).text() if self.table.item(row, c) else "" for c in range(self.table.columnCount())]
            clipboard = QApplication.clipboard()
            clipboard.setText("\t".join(texts))

        def do_filter_src():
            self.filter_text.setText(src_ip)

        def do_filter_dst():
            self.filter_text.setText(dst_ip)

        def do_proto():
            idx = self.filter_protocol.findText(proto)
            if idx >= 0:
                self.filter_protocol.setCurrentIndex(idx)

        act_copy.triggered.connect(do_copy)
        act_filter_src.triggered.connect(do_filter_src)
        act_filter_dst.triggered.connect(do_filter_dst)
        act_proto.triggered.connect(do_proto)

        menu.addAction(act_copy)
        menu.addSeparator()
        if src_ip:
            menu.addAction(act_filter_src)
        if dst_ip:
            menu.addAction(act_filter_dst)
        if proto:
            menu.addAction(act_proto)
        menu.exec_(self.table.viewport().mapToGlobal(pos))
