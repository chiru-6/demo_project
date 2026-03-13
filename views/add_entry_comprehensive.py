"""Comprehensive Add Entry form with all dropdowns and new fields."""

import os
import random

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class _DropZoneWidget(QFrame):
    """Widget that accepts drag-and-drop of files. The label inside must also accept drops."""

    files_dropped = Signal(list)  # list of file paths

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
        e.acceptProposedAction()


class OptionalDateWidget(QWidget):
    """Date field: type dd-mm-yyyy or use calendar button. Starts blank."""

    _FORMATS = ("dd-MM-yyyy", "yyyy-MM-dd", "d-M-yyyy", "dd/MM/yyyy")

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._line = QLineEdit()
        self._line.setPlaceholderText("dd-mm-yyyy or pick date...")
        self._value = None  # QDate or None (from calendar)
        btn = QPushButton("📅")
        btn.setToolTip("Pick date")
        btn.setFixedWidth(36)
        btn.clicked.connect(self._open_calendar)
        layout.addWidget(self._line)
        layout.addWidget(btn)

    def _parse_text(self):
        """Parse line edit text to QDate; return None if empty or invalid."""
        text = self._line.text().strip()
        if not text:
            return None
        for fmt in self._FORMATS:
            d = QDate.fromString(text, fmt)
            if d.isValid():
                return d
        return None

    def _open_calendar(self):
        d = QDialog(self)
        d.setWindowTitle("Select date")
        cal = QDateEdit()
        cal.setCalendarPopup(True)
        prefill = self.date()  # Uses typed text or _value
        cal.setDate(prefill if prefill and prefill.isValid() else QDate.currentDate())
        lay = QVBoxLayout(d)
        lay.addWidget(cal)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(d.accept)
        bb.rejected.connect(d.reject)
        lay.addWidget(bb)
        if d.exec() == QDialog.DialogCode.Accepted:
            self._value = cal.date()
            self._line.setText(self._value.toString("dd-MM-yyyy"))

    def date(self):
        """Return selected QDate or None if blank. Uses typed text or calendar value."""
        parsed = self._parse_text()
        if parsed and parsed.isValid():
            return parsed
        return self._value

    def set_date(self, qdate: QDate) -> None:
        """Set the date from a QDate."""
        if qdate and qdate.isValid():
            self._value = qdate
            self._line.setText(qdate.toString("dd-MM-yyyy"))
        else:
            self.clear()

    def clear(self):
        self._value = None
        self._line.clear()


class ComprehensiveAddEntryWidget(QWidget):
    """Comprehensive add entry form with dropdowns and all new fields."""

    entry_added = Signal()

    def __init__(self, db) -> None:
        super().__init__()
        self.db = db
        self.uploaded_files = []  # List of dicts: {name, path, type}
        self.init_ui()
        self._populate_dropdowns()

    def _create_combo_with_manual(self, options: list, placeholder: str = "") -> QComboBox:
        """Create a QComboBox that only fills when option is selected from dropdown.
        Manual typing is cleared - only dropdown selections are kept."""
        combo = QComboBox()
        combo.setEditable(True)
        combo.addItems(options)
        le = combo.lineEdit()
        placeholder_text = placeholder or "Select or type..."
        le.setPlaceholderText(placeholder_text)
        # Store placeholder for validation
        combo._placeholder_text = placeholder_text
        # Track if selection came from dropdown
        combo._selected_from_dropdown = False
        combo._last_valid_index = -1
        
        # Track dropdown selection
        def on_activated(index):
            if index >= 0:
                combo._selected_from_dropdown = True
                combo._last_valid_index = index
                # Keep the selected text
            else:
                combo._selected_from_dropdown = False
        
        def on_editing_finished():
            # When editing finishes, if it wasn't from dropdown selection, clear it
            if not combo._selected_from_dropdown:
                # User typed manually - restore last valid selection or clear
                if combo._last_valid_index >= 0:
                    combo.setCurrentIndex(combo._last_valid_index)
                else:
                    le.clear()
            combo._selected_from_dropdown = False
        
        combo.activated.connect(on_activated)
        le.editingFinished.connect(on_editing_finished)
        
        return combo

    def _populate_dropdowns(self) -> None:
        """Populate dropdowns from database. LRU combo shows only existing LRUs; placeholder hints 'Add New LRU'."""
        try:
            df = self.db.get_all_data()
            if not df.empty and "lru_name" in df.columns:
                lru_names = sorted(df["lru_name"].dropna().unique().tolist())
                self.lru_name_combo.clear()
                self.lru_name_combo.addItems(lru_names)
        except Exception:
            pass

    def init_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(16)

        # Entry fields (match dataset.csv columns)
        entry_group = QGroupBox("Entry Details")
        entry_layout = QFormLayout()
        self.lru_name_combo = self._create_combo_with_manual([], "Type new LRU or select existing...")
        entry_layout.addRow("LRU Name *:", self.lru_name_combo)
        self.part_number = QLineEdit()
        entry_layout.addRow("Part Number:", self.part_number)
        self.serial_no = QLineEdit()
        entry_layout.addRow("Serial No *:", self.serial_no)
        self.project = self._create_combo_with_manual(["AMCA", "TEJAS", "LCH", "IJT", "LCA", "ALH", "MIG-21 Upgrade"])
        entry_layout.addRow("Project *:", self.project)
        self.division_group = self._create_combo_with_manual(["A/C Division", "Avionics Division", "TD/Sagar", "ELE Group", "Hydraulics", "Quality Assurance", "Engine Division", "Avionics Group"])
        entry_layout.addRow("Division / Group *:", self.division_group)
        self.system = self._create_combo_with_manual(["HYD", "ELE", "PNEU", "GEN", "AVIONICS"])
        entry_layout.addRow("System *:", self.system)
        self.type_of_test = self._create_combo_with_manual([
            "Type Test", "Qualification Test", "Acceptance Test", "PI", "PI Starter",
            "Environmental Test", "Functional Test", "Stress Test", "Calibration",
            "Reliability Test", "EMI/EMC Test", "Vibration Test", "Thermal Test", "Endurance Test"
        ])
        entry_layout.addRow("Type of Test *:", self.type_of_test)
        self.test_rig = self._create_combo_with_manual([
            "Hydraulic", "Avionics", "DT EPGS", "LCA EPGS", "IJT EPGS",
            "Hydraulic Test Bench", "Avionics Rig", "Engine Test Cell",
            "TEJAS Rig A", "AMCA Rig 1"
        ])
        entry_layout.addRow("Test Rig *:", self.test_rig)
        self.received_data = QLineEdit()
        self.received_data.setPlaceholderText("e.g. Unit received for inspection")
        entry_layout.addRow("Received Data:", self.received_data)
        self.date_of_pi = OptionalDateWidget()
        entry_layout.addRow("Date of PI *:", self.date_of_pi)
        self.results_remarks = self._create_combo_with_manual([
            "OK", "NOT OK", "Pass", "Fail", "Conditional Pass", "Retest Required",
            "Under Review", "Pending"
        ])
        entry_layout.addRow("Results & Remarks *:", self.results_remarks)
        self.date_of_clearance = OptionalDateWidget()
        entry_layout.addRow("Date of Clearance:", self.date_of_clearance)
        entry_group.setLayout(entry_layout)
        layout.addWidget(entry_group)

        # File Uploads Section
        files_group = QGroupBox("File Attachments & Test Data")
        files_layout = QVBoxLayout()
        
        # File upload buttons
        upload_btn_layout = QHBoxLayout()
        self.upload_file_btn = QPushButton("📎 Upload File")
        self.upload_file_btn.setStyleSheet(
            "background-color: #2196F3; color: white; padding: 8px 16px; font-size: 13px;"
        )
        self.upload_file_btn.clicked.connect(self._upload_file)
        upload_btn_layout.addWidget(self.upload_file_btn)
        
        self.upload_csv_btn = QPushButton("📊 Upload Test Data CSV")
        self.upload_csv_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 8px 16px; font-size: 13px;"
        )
        self.upload_csv_btn.clicked.connect(self._upload_csv)
        upload_btn_layout.addWidget(self.upload_csv_btn)
        upload_btn_layout.addStretch()
        files_layout.addLayout(upload_btn_layout)
        
        files_layout.addWidget(QLabel("Uploaded Files: (or drag & drop multiple files here)"))
        self.uploaded_files_list = QListWidget()
        self.uploaded_files_list.setMaximumHeight(100)
        self.uploaded_files_list.setAcceptDrops(True)
        self.uploaded_files_list.itemClicked.connect(self._on_file_selected)
        files_layout.addWidget(self.uploaded_files_list)
        
        # Preview area (drop zone) - drop zone must be the widget under cursor
        drop_frame = _DropZoneWidget()
        drop_frame.setObjectName("dropZone")
        drop_frame.setMinimumHeight(220)
        drop_frame.setStyleSheet(
            "#dropZone { border: 2px dashed #94a3b8; border-radius: 8px; background: #f1f5f9; padding: 12px; }"
        )
        drop_layout = QVBoxLayout(drop_frame)
        self.file_preview_label = QLabel("Select a file to preview — or drag & drop files here")
        self.file_preview_label.setAlignment(Qt.AlignCenter)
        self.file_preview_label.setMinimumHeight(180)
        self.file_preview_label.setWordWrap(True)
        self.file_preview_label.setStyleSheet("QLabel { background: transparent; }")
        self.file_preview_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        drop_layout.addWidget(self.file_preview_label)
        drop_frame.files_dropped.connect(self._on_files_dropped)
        files_layout.addWidget(drop_frame)
        
        # Store uploaded files
        self.uploaded_files = []  # List of dicts: {name, path, type}
        
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.submit_btn = QPushButton("✅ Add Entry")
        self.submit_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 10px; font-size: 14px;"
        )
        self.submit_btn.clicked.connect(self.add_entry)
        self.clear_btn = QPushButton("🗑️ Clear Values")
        self.clear_btn.setStyleSheet(
            "background-color: #f44336; color: white; padding: 10px; font-size: 14px;"
        )
        self.clear_btn.clicked.connect(self.clear_form)
        self.clear_btn.setToolTip("Clear all form values")
        self.random_btn = QPushButton("🎲 Random")
        self.random_btn.setStyleSheet(
            "background-color: #9C27B0; color: white; padding: 10px; font-size: 14px;"
        )
        self.random_btn.clicked.connect(self._fill_random)
        self.random_btn.setToolTip("Fill all fields with random values")
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.random_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addStretch()

        scroll.setWidget(scroll_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def _get_combo_value(self, combo: QComboBox) -> str:
        """Get combo value - only return if selected from dropdown."""
        # Check current index - only return if valid dropdown selection
        idx = combo.currentIndex()
        if idx >= 0:
            return combo.itemText(idx)
        return ""

    def _set_combo_random(self, combo: QComboBox, options: list) -> None:
        """Set combo to a random option from the list (must exist in combo items)."""
        valid = [o for o in options if combo.findText(o) >= 0]
        if valid:
            choice = random.choice(valid)
            idx = combo.findText(choice)
            combo.setCurrentIndex(idx)
            combo._selected_from_dropdown = True
            combo._last_valid_index = idx

    def _fill_random(self) -> None:
        """Fill all form fields with random values."""
        lru_names = [
            "EPGS Controller", "DCMB GPRU", "Hydraulic Pump Unit", "5RW GEN",
            "Starter Motor Assembly", "5RW GEN, DCMB GPRU"
        ]
        part_prefixes = ["AVN", "STM", "EPGS", "GCCAIA", "HDP", "22460"]
        projects = ["AMCA", "TEJAS", "LCH", "IJT", "LCA", "ALH", "MIG-21 Upgrade"]
        divisions = [
            "A/C Division", "Avionics Division", "TD/Sagar", "ELE Group",
            "Hydraulics", "Quality Assurance", "Engine Division", "Avionics Group"
        ]
        systems = ["HYD", "ELE", "PNEU", "GEN", "AVIONICS"]
        test_types = [
            "Type Test", "Qualification Test", "Acceptance Test", "PI", "PI Starter",
            "Environmental Test", "Functional Test", "Calibration", "Endurance Test"
        ]
        test_rigs = [
            "Hydraulic", "Avionics", "LCA EPGS", "IJT EPGS", "Hydraulic Test Bench",
            "Avionics Rig", "Engine Test Cell", "TEJAS Rig A", "AMCA Rig 1"
        ]
        results = ["OK", "NOT OK", "Pass", "Fail", "Under Review", "Pending"]
        received = ["Unit received for inspection", "Unit received for PI", "Unit for calibration"]

        # LRU Name - pick from existing or type new
        if self.lru_name_combo.count() > 0 and random.random() > 0.3:
            valid = [self.lru_name_combo.itemText(i) for i in range(self.lru_name_combo.count())]
            if valid:
                choice = random.choice(valid)
                idx = self.lru_name_combo.findText(choice)
                self.lru_name_combo.setCurrentIndex(idx)
                self.lru_name_combo._selected_from_dropdown = True
                self.lru_name_combo._last_valid_index = idx
        else:
            self.lru_name_combo.setCurrentIndex(-1)
            self.lru_name_combo.lineEdit().clear()
            self.lru_name_combo.lineEdit().setText(random.choice(lru_names))
            self.lru_name_combo._selected_from_dropdown = False

        self.part_number.setText(
            random.choice(part_prefixes) + str(random.randint(100, 999))
        )
        serial = f"{random.randint(90, 450)} / 16100000{random.randint(1000000, 9999999)}2024"
        self.serial_no.setText(serial)

        self._set_combo_random(self.project, projects)
        self._set_combo_random(self.division_group, divisions)
        self._set_combo_random(self.system, systems)
        self._set_combo_random(self.type_of_test, test_types)
        self._set_combo_random(self.test_rig, test_rigs)
        self.received_data.setText(random.choice(received))
        self._set_combo_random(self.results_remarks, results)

        # Random dates (within last 2 years)
        base = QDate.currentDate()
        days_pi = random.randint(-730, 0)
        date_pi = base.addDays(days_pi)
        self.date_of_pi.set_date(date_pi)

        if random.random() > 0.3:
            days_clear = days_pi + random.randint(1, 30)
            date_clear = base.addDays(days_clear)
            self.date_of_clearance.set_date(date_clear)
        else:
            self.date_of_clearance.clear()

    def add_entry(self) -> None:
        lru_text = self.lru_name_combo.currentText() or self.lru_name_combo.lineEdit().text()
        if not lru_text or not lru_text.strip():
            QMessageBox.warning(self, "Validation Error", "Please enter LRU Name.")
            return

        # Date of PI: required; blank means missing
        date_pi = self.date_of_pi.date()
        date_pi_str = date_pi.toString("dd-MM-yyyy") if date_pi and date_pi.isValid() else ""
        required = {
            "LRU Name": lru_text.strip(),
            "Project": self._get_combo_value(self.project),
            "Division / Group": self._get_combo_value(self.division_group),
            "System": self._get_combo_value(self.system),
            "Serial No": self.serial_no.text().strip(),
            "Type of Test": self._get_combo_value(self.type_of_test),
            "Test Rig": self._get_combo_value(self.test_rig),
            "Date of PI": date_pi_str,
            "Results & Remarks": self._get_combo_value(self.results_remarks),
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            QMessageBox.warning(self, "Validation Error", f"Missing: {', '.join(missing)}")
            return

        entry_data = {
            "lru_name": lru_text.strip(),
            "project": required["Project"],
            "division_group": required["Division / Group"],
            "system": required["System"],
            "part_number": self.part_number.text().strip(),
            "serial_no": required["Serial No"],
            "received_data": self.received_data.text().strip(),
            "type_of_test": required["Type of Test"],
            "test_rig": required["Test Rig"],
            "date_of_pi": required["Date of PI"],
            "results_remarks": required["Results & Remarks"],
            "date_of_clearance": (self.date_of_clearance.date().toString("dd-MM-yyyy") if self.date_of_clearance.date() and self.date_of_clearance.date().isValid() else ""),
        }

        success, message = self.db.add_entry(entry_data)
        if success:
            # Append new entry to dataset.csv so it appears on the dataset page
            self._append_to_dataset_csv(entry_data)
            # Add uploaded files as attachments and CSV test data
            for file_info in self.uploaded_files:
                if file_info['type'] == 'CSV':
                    # Copy CSV to project folder lru_test_data/<LRU>/ and import
                    dest_path = self._copy_test_data_csv_to_project(lru_text, file_info['path'], file_info['name'])
                    csv_success, csv_msg = self.db.import_test_data_csv(
                        lru_text,
                        dest_path
                    )
                    if not csv_success:
                        QMessageBox.warning(self, "CSV Import Warning", f"CSV import failed: {csv_msg}")
                else:
                    # Add as regular attachment
                    self.db.add_attachment(
                        lru_text,
                        file_info['name'],
                        file_info['path'],
                        file_info['type']
                    )
            QMessageBox.information(self, "Success", message)
            self.clear_form()
            self.entry_added.emit()
        else:
            QMessageBox.critical(self, "Error", message)

    def _copy_test_data_csv_to_project(self, lru_name: str, source_path: str, file_name: str) -> str:
        """Copy CSV to project folder lru_test_data/<LRU_name>/ and return destination path.
        Path is relative to project (same dir as database.db). If copy fails, return source_path.
        """
        import os
        import shutil
        import re
        try:
            project_dir = os.path.dirname(os.path.abspath(self.db.db_path))
            safe_name = re.sub(r'[<>:"/\\|?*]', "_", (lru_name or "unknown").strip()) or "unknown"
            lru_folder = os.path.join(project_dir, "lru_test_data", safe_name)
            os.makedirs(lru_folder, exist_ok=True)
            dest_path = os.path.join(lru_folder, file_name)
            shutil.copy2(source_path, dest_path)
            return dest_path
        except Exception:
            return source_path

    def _append_to_dataset_csv(self, entry_data: dict) -> None:
        """Append the new entry to dataset.csv so it appears on the dataset page."""
        try:
            import csv
            project_dir = os.path.dirname(os.path.abspath(self.db.db_path))
            csv_path = os.path.join(project_dir, "dataset.csv")
            if not os.path.exists(csv_path):
                csv_path = os.path.join(project_dir, "LCA_Test_Data.csv")
            if not os.path.exists(csv_path):
                return
            col_map = {
                "LRU Name": "lru_name",
                "Project": "project",
                "Division / Group": "division_group",
                "System": "system",
                "Part Number": "part_number",
                "Serial No": "serial_no",
                "Received Data": "received_data",
                "Type of Test": "type_of_test",
                "Test Rig": "test_rig",
                "Date of PI": "date_of_pi",
                "Results & Remarks": "results_remarks",
                "Date of Clearance": "date_of_clearance",
            }
            with open(csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or list(col_map.keys())
            row = {}
            for h in headers:
                key = col_map.get(h)
                row[h] = entry_data.get(key, "") if key else ""
            with open(csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
                writer.writerow(row)
        except Exception:
            pass

    def _on_files_dropped(self, paths: list) -> None:
        """Handle multiple files dropped. Auto-detect CSV as test data, others as attachments."""
        csv_paths = [p for p in paths if p.lower().endswith(".csv")]
        other_paths = [p for p in paths if not p.lower().endswith(".csv")]
        for p in other_paths:
            name = os.path.basename(p)
            ext = os.path.splitext(name)[1][1:].upper() or "FILE"
            self.uploaded_files.append({"name": name, "path": p, "type": ext})
        if len(csv_paths) == 1:
            name = os.path.basename(csv_paths[0])
            self.uploaded_files.append({"name": name, "path": csv_paths[0], "type": "CSV"})
        elif len(csv_paths) >= 2:
            from PySide6.QtWidgets import QInputDialog
            names = ["(None - add all as attachments)"] + [os.path.basename(p) for p in csv_paths]
            selected, ok = QInputDialog.getItem(
                self, "Multiple CSV Files",
                "Which file should be used as Test Data?",
                names, 0, False
            )
            if ok and selected and selected != names[0]:
                idx = names.index(selected) - 1
                self.uploaded_files.append({
                    "name": os.path.basename(csv_paths[idx]), "path": csv_paths[idx], "type": "CSV"
                })
                for i, p in enumerate(csv_paths):
                    if i != idx:
                        self.uploaded_files.append({
                            "name": os.path.basename(p), "path": p, "type": "FILE"
                        })
            else:
                for p in csv_paths:
                    self.uploaded_files.append({
                        "name": os.path.basename(p), "path": p, "type": "FILE"
                    })
        self._update_files_list()
        if self.uploaded_files:
            self._preview_file(self.uploaded_files[-1])

    def _upload_file(self) -> None:
        """Upload a file (PDF, image, etc.) for the LRU."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "All Files (*.*);;Images (*.png *.jpg *.jpeg *.gif *.bmp);;PDF (*.pdf)"
        )
        if file_path:
            import os
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1][1:].upper() or "FILE"
            file_info = {
                'name': file_name,
                'path': file_path,
                'type': file_ext
            }
            self.uploaded_files.append(file_info)
            self._update_files_list()
            self._preview_file(file_info)

    def _upload_csv(self) -> None:
        """Upload CSV file for test data."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv)"
        )
        if file_path:
            import os
            file_name = os.path.basename(file_path)
            file_info = {
                'name': file_name,
                'path': file_path,
                'type': 'CSV'
            }
            self.uploaded_files.append(file_info)
            self._update_files_list()
            self._preview_file(file_info)

    def _update_files_list(self) -> None:
        """Update the uploaded files list widget."""
        self.uploaded_files_list.clear()
        for file_info in self.uploaded_files:
            icon = "📎"
            if file_info['type'] in ['PNG', 'JPG', 'JPEG', 'GIF', 'BMP']:
                icon = "🖼️"
            elif file_info['type'] == 'PDF':
                icon = "📄"
            elif file_info['type'] == 'CSV':
                icon = "📊"
            item = QListWidgetItem(f"{icon} {file_info['name']}")
            item.setData(Qt.UserRole, file_info)
            self.uploaded_files_list.addItem(item)

    def _on_file_selected(self, item: QListWidgetItem) -> None:
        """Show preview when file is selected."""
        file_info = item.data(Qt.UserRole)
        if file_info:
            self._preview_file(file_info)

    def _preview_file(self, file_info: dict) -> None:
        """Preview the selected file."""
        file_path = file_info['path']
        file_type = file_info['type']
        import os
        
        if not os.path.exists(file_path):
            self.file_preview_label.setText(f"File not found: {file_info['name']}")
            self.file_preview_label.setPixmap(QPixmap())
            return
        
        # Handle image files
        if file_type in ['PNG', 'JPG', 'JPEG', 'GIF', 'BMP']:
            try:
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.file_preview_label.setPixmap(scaled_pixmap)
                    self.file_preview_label.setText("")
                else:
                    self.file_preview_label.setText("Unable to load image")
                    self.file_preview_label.setPixmap(QPixmap())
            except Exception as e:
                self.file_preview_label.setText(f"Error loading image: {str(e)}")
                self.file_preview_label.setPixmap(QPixmap())
        
        # Handle PDF files
        elif file_type == 'PDF':
            self.file_preview_label.setText(f"PDF File\n\nFile: {file_info['name']}\n\nWill be attached to LRU entry")
            self.file_preview_label.setPixmap(QPixmap())
        
        # Handle CSV files
        elif file_type == 'CSV':
            try:
                import pandas as pd
                df = pd.read_csv(file_path)
                preview_text = f"CSV Test Data\n\nFile: {file_info['name']}\n"
                preview_text += f"Rows: {len(df)}\n"
                preview_text += f"Columns: {', '.join(df.columns[:5].tolist())}"
                if len(df.columns) > 5:
                    preview_text += "..."
                self.file_preview_label.setText(preview_text)
                self.file_preview_label.setPixmap(QPixmap())
            except Exception as e:
                self.file_preview_label.setText(f"Error reading CSV: {str(e)}")
                self.file_preview_label.setPixmap(QPixmap())
        
        # Other file types
        else:
            self.file_preview_label.setText(f"File: {file_info['name']}\n\nWill be attached to LRU entry")
            self.file_preview_label.setPixmap(QPixmap())

    def clear_form(self) -> None:
        """Clear all form values and reset to empty state."""
        for widget in self.findChildren(QComboBox):
            widget.setCurrentIndex(-1)
            if widget.isEditable():
                le = widget.lineEdit()
                le.clear()
            if hasattr(widget, "_selected_from_dropdown"):
                widget._selected_from_dropdown = False
            if hasattr(widget, "_last_valid_index"):
                widget._last_valid_index = -1
        for widget in self.findChildren(QLineEdit):
            widget.clear()
        for widget in self.findChildren(QDateEdit):
            widget.setDate(QDate.currentDate())
        self.date_of_pi.clear()
        self.date_of_clearance.clear()
        self.uploaded_files = []
        self.uploaded_files_list.clear()
        self.file_preview_label.setText("Select a file to preview")
        self.file_preview_label.setPixmap(QPixmap())
