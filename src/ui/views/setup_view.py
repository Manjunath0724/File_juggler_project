"""Setup View: Source/Destination folder selection, organization modes, and advanced settings."""
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QButtonGroup, QCheckBox,
    QComboBox, QFrame, QFileDialog, QScrollArea, QSizePolicy
)

from src.models.organization_rule import OrganizationConfig, OrganizationMode, DuplicatePolicy
from src.utils.file_utils import get_default_downloads_folder, is_safe_to_organize
from src.ui.theme import apply_card_shadow


class SetupView(QWidget):
    """Initial configuration view for File Juggler."""

    # Emitted when user clicks 'Preview Files' with validated configuration
    preview_requested = Signal(object, str, str)  # (config, source_path, dest_path)
    open_settings_requested = Signal()
    open_history_requested = Signal()
    toggle_theme_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = OrganizationConfig()
        self.cards = []
        self._init_ui()

    def _init_ui(self):
        self.setObjectName("setupView")
        self.setAttribute(Qt.WA_StyledBackground, True)

        # Outer layout with scroll area for responsive fitting on various screen sizes
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setObjectName("mainScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        if scroll.viewport():
            scroll.viewport().setObjectName("scrollViewport")

        container = QWidget()
        container.setObjectName("scrollContainer")
        container.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(36, 28, 36, 36)
        layout.setSpacing(20)

        # 1. Header Bar
        layout.addLayout(self._build_header())

        # 2. Source Folder Card
        self.source_card = self._build_source_card()
        layout.addWidget(self.source_card)
        self.cards.append(self.source_card)

        # 3. Destination Folder Card
        self.dest_card = self._build_dest_card()
        layout.addWidget(self.dest_card)
        self.cards.append(self.dest_card)

        # 4. Organization Mode Card
        self.mode_card = self._build_mode_card()
        layout.addWidget(self.mode_card)
        self.cards.append(self.mode_card)

        # 5. Advanced Options Collapsible Card
        self.adv_card = self._build_advanced_card()
        layout.addWidget(self.adv_card)
        self.cards.append(self.adv_card)

        # 6. Action Footer
        layout.addLayout(self._build_footer())

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

        # Apply initial 3D shadows
        self.apply_shadows("dark")

    def apply_shadows(self, theme: str = "dark"):
        """Apply or refresh 3D elevation drop shadows on cards."""
        for card in self.cards:
            apply_card_shadow(card, theme)

    def update_theme_label(self, theme: str):
        """Update theme toggle button text reflecting next state."""
        self.theme_btn.setText("Light Mode" if theme == "dark" else "Dark Mode")
        self.apply_shadows(theme)

    def _build_header(self) -> QHBoxLayout:
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 8)

        titles_col = QVBoxLayout()
        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        title_lbl = QLabel("File Juggler")
        title_lbl.setProperty("class", "title")

        version_badge = QLabel("PRO v1.0")
        version_badge.setProperty("class", "badge")
        version_badge.setStyleSheet(
            "font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 4px; letter-spacing: 0.5px;"
        )

        status_dot = QLabel("System Ready")
        status_dot.setStyleSheet("font-size: 11px; font-weight: 500; color: #10b981;")

        title_row.addWidget(title_lbl)
        title_row.addWidget(version_badge)
        title_row.addSpacing(6)
        title_row.addWidget(status_dot)
        title_row.addStretch()

        sub_lbl = QLabel("Automated, non-destructive file classification and organization engine")
        sub_lbl.setProperty("class", "subtitle")

        titles_col.addLayout(title_row)
        titles_col.addWidget(sub_lbl)
        header_layout.addLayout(titles_col)

        header_layout.addStretch()

        # Theme toggle button
        self.theme_btn = QPushButton("Light Mode")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self.toggle_theme_requested.emit)
        header_layout.addWidget(self.theme_btn)

        # History button
        self.history_btn = QPushButton("History")
        self.history_btn.setCursor(Qt.PointingHandCursor)
        self.history_btn.clicked.connect(self.open_history_requested.emit)
        header_layout.addWidget(self.history_btn)

        # Settings button
        self.settings_btn = QPushButton("Preferences")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self.open_settings_requested.emit)
        header_layout.addWidget(self.settings_btn)

        return header_layout

    def _build_source_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        header = QLabel("1. Source Directory")
        header.setProperty("class", "section-header")
        desc = QLabel("Select the target directory to analyze and reorganize (e.g., Downloads, Desktop).")
        desc.setProperty("class", "card-desc")

        layout.addWidget(header)
        layout.addWidget(desc)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Select a folder to organize...")
        self.source_input.textChanged.connect(self._on_source_changed)

        self.browse_source_btn = QPushButton("Browse...")
        self.browse_source_btn.setCursor(Qt.PointingHandCursor)
        self.browse_source_btn.clicked.connect(self._browse_source)

        self.downloads_btn = QPushButton("Use Downloads")
        self.downloads_btn.setCursor(Qt.PointingHandCursor)
        self.downloads_btn.setToolTip("Quickly select your Windows Downloads folder")
        self.downloads_btn.clicked.connect(self._use_downloads)

        input_row.addWidget(self.source_input, stretch=1)
        input_row.addWidget(self.browse_source_btn)
        input_row.addWidget(self.downloads_btn)

        layout.addLayout(input_row)
        return card

    def _build_dest_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        header = QLabel("2. Destination Directory")
        header.setProperty("class", "section-header")
        desc = QLabel("Files can be structured into subfolders in-place or relocated to a separate directory.")
        desc.setProperty("class", "card-desc")

        layout.addWidget(header)
        layout.addWidget(desc)

        self.dest_group = QButtonGroup(self)

        self.dest_in_place_rb = QRadioButton("Organize inside the source folder (recommended)")
        self.dest_in_place_rb.setChecked(True)
        self.dest_in_place_rb.toggled.connect(self._on_dest_mode_toggled)

        self.dest_custom_rb = QRadioButton("Relocate to a custom destination directory")
        self.dest_custom_rb.toggled.connect(self._on_dest_mode_toggled)

        self.dest_group.addButton(self.dest_in_place_rb)
        self.dest_group.addButton(self.dest_custom_rb)

        layout.addWidget(self.dest_in_place_rb)
        layout.addWidget(self.dest_custom_rb)

        # Custom destination row
        self.custom_dest_row = QWidget()
        custom_layout = QHBoxLayout(self.custom_dest_row)
        custom_layout.setContentsMargins(28, 0, 0, 0)
        custom_layout.setSpacing(10)

        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Select destination directory...")
        self.dest_input.setEnabled(False)

        self.browse_dest_btn = QPushButton("Browse...")
        self.browse_dest_btn.setCursor(Qt.PointingHandCursor)
        self.browse_dest_btn.setEnabled(False)
        self.browse_dest_btn.clicked.connect(self._browse_dest)

        custom_layout.addWidget(self.dest_input, stretch=1)
        custom_layout.addWidget(self.browse_dest_btn)

        layout.addWidget(self.custom_dest_row)
        return card

    def _build_mode_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setSpacing(14)

        header = QLabel("3. Organization Strategy")
        header.setProperty("class", "section-header")
        desc = QLabel("Define the classification criteria used to partition files into subfolders.")
        desc.setProperty("class", "card-desc")

        layout.addWidget(header)
        layout.addWidget(desc)

        self.mode_group = QButtonGroup(self)

        modes = [
            (OrganizationMode.BY_TYPE, "By File Type & Format", "PDF, Excel, Word, Presentations, Photos, Vectors, GIFs, Code, Media, Archives"),
            (OrganizationMode.BY_SIZE, "By File Size", "Tiny (<1MB), Small (1-10MB), Medium (10-100MB), Large (100MB-1GB), Huge (>1GB)"),
            (OrganizationMode.BY_DATE, "By Date Modified", "Today, Yesterday, This Week, This Month, or Year"),
            (OrganizationMode.COMBINED, "Combined Hierarchy", "Multi-tier nested subfolders (e.g. Documents / Small)"),
        ]

        for mode_val, title, subtitle in modes:
            row_box = QHBoxLayout()
            rb = QRadioButton(title)
            rb.setProperty("mode", mode_val.value)
            if mode_val == OrganizationMode.BY_TYPE:
                rb.setChecked(True)
            self.mode_group.addButton(rb)

            sub = QLabel(f"— {subtitle}")
            sub.setProperty("class", "card-desc")

            row_box.addWidget(rb)
            row_box.addWidget(sub)
            row_box.addStretch()
            layout.addLayout(row_box)

        # Combined pattern selector
        self.combined_settings = QWidget()
        c_layout = QHBoxLayout(self.combined_settings)
        c_layout.setContentsMargins(28, 0, 0, 0)
        c_lbl = QLabel("Combined Hierarchy Order:")
        c_lbl.setProperty("class", "card-desc")
        c_layout.addWidget(c_lbl)

        self.combined_combo = QComboBox()
        self.combined_combo.addItem("Type then Size (e.g., Documents / Small)", "type_then_size")
        self.combined_combo.addItem("Date then Type (e.g., 2026 / Documents)", "date_then_type")
        self.combined_combo.addItem("Size then Type (e.g., Huge / Videos)", "size_then_type")
        c_layout.addWidget(self.combined_combo)
        c_layout.addStretch()
        layout.addWidget(self.combined_settings)

        return card

    def _build_advanced_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        # Toggle button as section title
        self.adv_toggle_btn = QPushButton("Show Advanced Configuration & Safety Controls")
        self.adv_toggle_btn.setFlat(True)
        self.adv_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.adv_toggle_btn.setStyleSheet(
            "text-align: left; font-weight: 600; font-size: 13px; border: none; padding: 4px 0;"
        )
        self.adv_toggle_btn.clicked.connect(self._toggle_advanced)
        layout.addWidget(self.adv_toggle_btn)

        # Collapsible content container with height animation
        self.adv_content = QWidget()
        self.adv_content.setMaximumHeight(0)
        self.adv_content_expanded = False

        content_layout = QVBoxLayout(self.adv_content)
        content_layout.setContentsMargins(12, 10, 12, 10)
        content_layout.setSpacing(12)

        # Checkboxes
        self.cb_subfolders = QCheckBox("Include subfolders (recursively process nested directories)")
        self.cb_subfolders.setChecked(False)

        self.cb_hidden = QCheckBox("Include hidden and system files")
        self.cb_hidden.setChecked(False)

        self.cb_dry_run = QCheckBox("Dry-run simulation mode (evaluate movements without modifying disk)")
        self.cb_dry_run.setChecked(False)

        self.cb_nested = QCheckBox("Group into parent folders (e.g. Documents/PDF, Images/Photos)")
        self.cb_nested.setChecked(False)

        content_layout.addWidget(self.cb_subfolders)
        content_layout.addWidget(self.cb_hidden)
        content_layout.addWidget(self.cb_dry_run)
        content_layout.addWidget(self.cb_nested)

        # Duplicate Handling Policy
        dup_row = QHBoxLayout()
        dup_lbl = QLabel("Collision Resolution Policy:")
        dup_lbl.setProperty("class", "card-desc")
        dup_row.addWidget(dup_lbl)

        self.dup_combo = QComboBox()
        self.dup_combo.addItem("Auto-Rename (photo (1).jpg)", DuplicatePolicy.RENAME.value)
        self.dup_combo.addItem("Skip File (leave untouched)", DuplicatePolicy.SKIP.value)
        self.dup_combo.addItem("Overwrite Destination (replace existing)", DuplicatePolicy.REPLACE.value)
        dup_row.addWidget(self.dup_combo)
        dup_row.addStretch()
        content_layout.addLayout(dup_row)

        # Excluded extensions
        ext_row = QHBoxLayout()
        ext_lbl = QLabel("Excluded File Extensions:")
        ext_lbl.setProperty("class", "card-desc")
        ext_row.addWidget(ext_lbl)
        self.ext_input = QLineEdit(".tmp, .part, .crdownload, .bak")
        ext_row.addWidget(self.ext_input)
        content_layout.addLayout(ext_row)

        layout.addWidget(self.adv_content)
        return card

    def _build_footer(self) -> QVBoxLayout:
        footer = QVBoxLayout()
        footer.setSpacing(10)

        # Error / Validation Label
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: #ef4444; font-weight: 600;")
        self.error_lbl.setAlignment(Qt.AlignCenter)
        footer.addWidget(self.error_lbl)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.preview_btn = QPushButton("Preview Proposed Movements  →")
        self.preview_btn.setProperty("class", "primary")
        self.preview_btn.setMinimumHeight(46)
        self.preview_btn.setMinimumWidth(260)
        self.preview_btn.setCursor(Qt.PointingHandCursor)
        self.preview_btn.clicked.connect(self._on_preview_clicked)

        btn_row.addWidget(self.preview_btn)
        btn_row.addStretch()

        footer.addLayout(btn_row)
        return footer

    def _browse_source(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory to Organize")
        if folder:
            self.source_input.setText(folder)

    def _browse_dest(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Directory")
        if folder:
            self.dest_input.setText(folder)

    def _use_downloads(self):
        downloads = get_default_downloads_folder()
        self.source_input.setText(downloads)

    def _on_source_changed(self, text: str):
        self.error_lbl.setText("")

    def _on_dest_mode_toggled(self):
        is_custom = self.dest_custom_rb.isChecked()
        self.dest_input.setEnabled(is_custom)
        self.browse_dest_btn.setEnabled(is_custom)

    def _toggle_advanced(self):
        """Smooth animated height toggle for advanced controls."""
        target_height = 250 if not self.adv_content_expanded else 0
        self.adv_content_expanded = not self.adv_content_expanded

        self.anim = QPropertyAnimation(self.adv_content, b"maximumHeight")
        self.anim.setDuration(240)
        self.anim.setStartValue(self.adv_content.maximumHeight())
        self.anim.setEndValue(target_height)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()

        self.adv_toggle_btn.setText(
            "Hide Advanced Configuration & Safety Controls" if self.adv_content_expanded
            else "Show Advanced Configuration & Safety Controls"
        )

    def _on_preview_clicked(self):
        source = self.source_input.text().strip()
        if not source:
            self.error_lbl.setText("Please select a source folder before continuing.")
            return

        is_safe, reason = is_safe_to_organize(source)
        if not is_safe:
            self.error_lbl.setText(f"Invalid Folder: {reason}")
            return

        if self.dest_custom_rb.isChecked():
            dest = self.dest_input.text().strip()
            if not dest:
                self.error_lbl.setText("Please select a destination folder or choose in-place organization.")
                return
            is_dest_safe, d_reason = is_safe_to_organize(dest)
            if not is_dest_safe:
                self.error_lbl.setText(f"Invalid Destination: {d_reason}")
                return
        else:
            dest = source

        # Gather Configuration
        selected_mode_str = self.mode_group.checkedButton().property("mode")
        self.config.mode = OrganizationMode(selected_mode_str)
        self.config.include_subfolders = self.cb_subfolders.isChecked()
        self.config.include_hidden_files = self.cb_hidden.isChecked()
        self.config.dry_run = self.cb_dry_run.isChecked()
        self.config.nested_subcategories = self.cb_nested.isChecked()
        self.config.duplicate_policy = DuplicatePolicy(self.dup_combo.currentData())
        self.config.combined_pattern = self.combined_combo.currentData()

        # Parse excluded extensions
        exts = [e.strip().lower() for e in self.ext_input.text().split(",") if e.strip()]
        self.config.excluded_extensions = [e if e.startswith(".") else f".{e}" for e in exts]

        self.error_lbl.setText("")
        self.preview_requested.emit(self.config, source, dest)
