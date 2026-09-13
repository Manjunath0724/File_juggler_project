"""Preview View: Interactive table showing proposed file reorganizations, filters, and controls."""
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QFrame, QAbstractItemView, QCheckBox
)

from src.models.file_item import FileItem
from src.utils.size_utils import format_size
from src.ui.theme import apply_card_shadow


class PreviewView(QWidget):
    """View displaying preview table of scanned files and their proposed locations."""

    back_requested = Signal()
    confirm_requested = Signal(list)  # list of selected FileItem objects

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: List[FileItem] = []
        self._init_ui()

    def _init_ui(self):
        self.setObjectName("previewView")
        self.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 28, 36, 32)
        layout.setSpacing(16)

        # Header bar
        layout.addLayout(self._build_header())

        # Filter toolbar card
        self.toolbar_card = self._build_toolbar()
        layout.addWidget(self.toolbar_card)

        # Table
        self.table = self._build_table()
        layout.addWidget(self.table, stretch=1)

        # Footer
        layout.addLayout(self._build_footer())

        self.apply_shadows("dark")

    def apply_shadows(self, theme: str = "dark"):
        """Apply 3D elevation drop shadows to cards."""
        apply_card_shadow(self.toolbar_card, theme)

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()

        self.back_btn = QPushButton("Back to Configuration")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(self.back_btn)

        header.addSpacing(18)

        col = QVBoxLayout()
        title = QLabel("Proposed File Movements")
        title.setProperty("class", "title")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        sub = QLabel("Review file moves before applying. Deselect any files you wish to leave untouched.")
        sub.setProperty("class", "subtitle")
        col.addWidget(title)
        col.addWidget(sub)
        header.addLayout(col)

        header.addStretch()
        return header

    def _build_toolbar(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("class", "card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by filename or extension...")
        self.search_input.textChanged.connect(self._apply_filters)
        layout.addWidget(self.search_input, stretch=2)

        # Category Filter
        cat_lbl = QLabel("Category:")
        cat_lbl.setProperty("class", "card-desc")
        layout.addWidget(cat_lbl)

        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", "all")
        self.category_combo.currentIndexChanged.connect(self._apply_filters)
        layout.addWidget(self.category_combo, stretch=1)

        # Select all / deselect all
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setCursor(Qt.PointingHandCursor)
        self.select_all_btn.clicked.connect(lambda: self._set_all_selection(True))
        layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.setCursor(Qt.PointingHandCursor)
        self.deselect_all_btn.clicked.connect(lambda: self._set_all_selection(False))
        layout.addWidget(self.deselect_all_btn)

        return frame

    def _build_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Select", "File Name", "Category", "Size", "Current Location", "Target Destination"
        ])
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        table.cellClicked.connect(self._on_cell_clicked)
        return table

    def _build_footer(self) -> QHBoxLayout:
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 10, 0, 0)

        # Summary label
        self.summary_lbl = QLabel("0 files selected (0 B)")
        self.summary_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #3b82f6;")
        footer.addWidget(self.summary_lbl)

        footer.addStretch()

        self.juggle_btn = QPushButton("Apply File Organization  →")
        self.juggle_btn.setProperty("class", "primary")
        self.juggle_btn.setMinimumHeight(44)
        self.juggle_btn.setMinimumWidth(240)
        self.juggle_btn.setCursor(Qt.PointingHandCursor)
        self.juggle_btn.clicked.connect(self._on_confirm_clicked)
        footer.addWidget(self.juggle_btn)

        return footer

    def populate(self, items: List[FileItem]):
        """Load scanned FileItem list into the preview table."""
        self.items = items
        self.search_input.clear()

        # Populate Category Filter
        categories = sorted(list({item.category for item in items}))
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("All Categories", "all")
        for cat in categories:
            self.category_combo.addItem(cat, cat)
        self.category_combo.blockSignals(False)

        self._render_table()
        self._update_summary()

    def _render_table(self):
        query = self.search_input.text().strip().lower()
        cat_filter = self.category_combo.currentData()

        visible_items = []
        for item in self.items:
            if query and query not in item.name.lower():
                continue
            if cat_filter != "all" and item.category != cat_filter:
                continue
            visible_items.append(item)

        self.table.setRowCount(len(visible_items))

        for row, item in enumerate(visible_items):
            # Checkbox item
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            check_item.setCheckState(Qt.Checked if item.selected else Qt.Unchecked)
            check_item.setData(Qt.UserRole, item)

            name_item = QTableWidgetItem(item.name)
            name_item.setToolTip(item.full_path)

            cat_item = QTableWidgetItem(item.category.upper())
            cat_item.setTextAlignment(Qt.AlignCenter)

            size_item = QTableWidgetItem(format_size(item.size_bytes))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            curr_dir = str(Path(item.full_path).parent)
            curr_item = QTableWidgetItem(curr_dir)
            curr_item.setToolTip(item.full_path)

            new_item = QTableWidgetItem(item.proposed_destination)
            new_item.setToolTip(item.proposed_destination)

            self.table.setItem(row, 0, check_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, cat_item)
            self.table.setItem(row, 3, size_item)
            self.table.setItem(row, 4, curr_item)
            self.table.setItem(row, 5, new_item)

    def _on_cell_clicked(self, row: int, column: int):
        check_item = self.table.item(row, 0)
        if not check_item:
            return
        item: FileItem = check_item.data(Qt.UserRole)
        if column == 0:
            item.selected = (check_item.checkState() == Qt.Checked)
        self._update_summary()

    def _set_all_selection(self, select: bool):
        state = Qt.Checked if select else Qt.Unchecked
        for row in range(self.table.rowCount()):
            chk = self.table.item(row, 0)
            if chk:
                chk.setCheckState(state)
                item: FileItem = chk.data(Qt.UserRole)
                if item:
                    item.selected = select
        self._update_summary()

    def _apply_filters(self):
        self._render_table()
        self._update_summary()

    def _update_summary(self):
        selected = [item for item in self.items if item.selected]
        total_size = sum(item.size_bytes for item in selected)
        self.summary_lbl.setText(
            f"{len(selected)} of {len(self.items)} files selected ({format_size(total_size)})"
        )
        self.juggle_btn.setEnabled(len(selected) > 0)

    def _on_confirm_clicked(self):
        selected = [item for item in self.items if item.selected]
        if selected:
            self.confirm_requested.emit(selected)
