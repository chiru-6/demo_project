"""Comprehensive Add Entry form with all dropdowns and new fields."""

import os
from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QDialogButtonBox,
    QDoubleSpinBox,
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
    QSpinBox,
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
        """Populate dropdowns from database."""
        try:
            df = self.db.get_all_data()
            if not df.empty:
                if "lru_name" in df.columns:
                    lru_names = sorted(df["lru_name"].dropna().unique().tolist())
                    self.lru_name_combo.clear()
                    self.lru_name_combo.addItem("Add New LRU...")
                    self.lru_name_combo.addItems(lru_names)
        except Exception:
            pass

    def init_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(16)

        # LRU Identification Section
        lru_group = QGroupBox("LRU Identification")
        lru_layout = QFormLayout()
        self.lru_name_combo = self._create_combo_with_manual([], "Add New LRU or select...")
        lru_layout.addRow("LRU Name *:", self.lru_name_combo)
        self.lru_category = self._create_combo_with_manual([
            "Avionics", "Power Systems", "Communication", "Navigation",
            "Flight Control", "Monitoring System", "Data Acquisition",
            "Safety System", "Environmental Control"
        ])
        lru_layout.addRow("LRU Category:", self.lru_category)
        self.platform = self._create_combo_with_manual([
            "Fixed Wing", "Rotary Wing", "UAV", "Fighter Jet",
            "Transport Aircraft", "Commercial Aircraft", "Helicopter"
        ])
        lru_layout.addRow("Platform / Aircraft Type:", self.platform)
        self.manufacturer = self._create_combo_with_manual([
            "Honeywell", "Collins Aerospace", "Thales", "HAL", "BEL",
            "Custom Vendor", "In-house Development"
        ])
        lru_layout.addRow("Manufacturer:", self.manufacturer)
        self.part_number = QLineEdit()
        lru_layout.addRow("Part Number:", self.part_number)
        self.serial_no = QLineEdit()
        lru_layout.addRow("Serial No *:", self.serial_no)
        lru_group.setLayout(lru_layout)
        layout.addWidget(lru_group)

        # Test Identification Section
        test_group = QGroupBox("Test Identification")
        test_layout = QFormLayout()
        self.project = self._create_combo_with_manual(["AMCA", "TEJAS", "LCH", "IJT"])
        test_layout.addRow("Project *:", self.project)
        self.division_group = self._create_combo_with_manual(["A/C Division", "Avionics Division"])
        test_layout.addRow("Division / Group *:", self.division_group)
        self.system = self._create_combo_with_manual(["HYD", "ELE", "PNEU", "GEN", "AVIONICS"])
        test_layout.addRow("System *:", self.system)
        self.type_of_test = self._create_combo_with_manual([
            "Type Test", "Qualification Test", "Acceptance Test",
            "Environmental Test", "Functional Test", "Stress Test",
            "Reliability Test", "EMI/EMC Test", "Vibration Test", "Thermal Test"
        ])
        test_layout.addRow("Test Type *:", self.type_of_test)
        self.test_standard = self._create_combo_with_manual([
            "DO-160", "MIL-STD-810", "MIL-STD-461", "ARINC 600",
            "IEC 60068", "Custom Specification"
        ])
        test_layout.addRow("Test Standard:", self.test_standard)
        self.test_rig = self._create_combo_with_manual([
            "Hydraulic", "Avionics", "DT EPGS", "LCA EPGS", "IJT EPGS"
        ])
        test_layout.addRow("Test Rig *:", self.test_rig)
        self.test_lab = self._create_combo_with_manual([
            "Internal Lab", "Certified External Lab", "HAL Lab",
            "DRDO Lab", "Third-Party Lab"
        ])
        test_layout.addRow("Test Lab:", self.test_lab)
        self.test_engineer = self._create_combo_with_manual([])
        test_layout.addRow("Test Engineer:", self.test_engineer)
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)

        # Environmental Conditions
        env_group = QGroupBox("Environmental Conditions")
        env_layout = QFormLayout()
        self.temperature_range = self._create_combo_with_manual([
            "-55°C to +70°C", "-40°C to +85°C", "-20°C to +60°C",
            "Standard Ambient", "High Temperature", "Low Temperature"
        ])
        env_layout.addRow("Temperature Range:", self.temperature_range)
        self.humidity_level = self._create_combo_with_manual([
            "0-20%", "20-50%", "50-80%", "80-95%"
        ])
        env_layout.addRow("Humidity Level:", self.humidity_level)
        self.vibration_level = self._create_combo_with_manual([
            "Low", "Medium", "High", "MIL Standard Profile", "Custom Profile"
        ])
        env_layout.addRow("Vibration Level:", self.vibration_level)
        self.altitude_condition = self._create_combo_with_manual([
            "Sea Level", "10,000 ft", "20,000 ft", "35,000 ft", "High Altitude Simulation"
        ])
        env_layout.addRow("Altitude Condition:", self.altitude_condition)
        env_group.setLayout(env_layout)
        layout.addWidget(env_group)

        # Electrical Parameters
        elec_group = QGroupBox("Electrical Parameters")
        elec_layout = QFormLayout()
        self.voltage_input = self._create_combo_with_manual([
            "0V DC", "5V DC", "12V DC", "24V DC", "28V DC", "115V AC", "230V AC"
        ])
        elec_layout.addRow("Voltage Input:", self.voltage_input)
        self.power_consumption = self._create_combo_with_manual([
            "<10W", "10-50W", "50-100W", ">100W"
        ])
        elec_layout.addRow("Power Consumption Range:", self.power_consumption)
        elec_group.setLayout(elec_layout)
        layout.addWidget(elec_group)

        # Test Result Section
        result_group = QGroupBox("Test Result")
        result_layout = QFormLayout()
        self.date_of_pi = OptionalDateWidget()
        result_layout.addRow("Date of PI *:", self.date_of_pi)
        self.results_remarks = self._create_combo_with_manual([
            "Pass", "Fail", "Conditional Pass", "Retest Required", "Under Review"
        ])
        result_layout.addRow("Test Result Status *:", self.results_remarks)
        self.failure_type = self._create_combo_with_manual([
            "Hardware Failure", "Software Bug", "Overheating",
            "EMI Interference", "Voltage Instability", "Mechanical Damage",
            "Calibration Error"
        ])
        result_layout.addRow("Failure Type (if Fail):", self.failure_type)
        self.severity_level = self._create_combo_with_manual([
            "Minor", "Moderate", "Major", "Critical"
        ])
        result_layout.addRow("Severity Level:", self.severity_level)
        self.corrective_action = self._create_combo_with_manual([
            "Not Required", "Under Investigation", "Fix Implemented", "Verified", "Closed"
        ])
        result_layout.addRow("Corrective Action Status:", self.corrective_action)
        self.date_of_clearance = OptionalDateWidget()
        result_layout.addRow("Date of Clearance:", self.date_of_clearance)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

        # Reliability & Statistics
        reliability_group = QGroupBox("Reliability & Statistics")
        rel_layout = QFormLayout()
        self.mtbf_category = self._create_combo_with_manual([
            "<100 hrs", "100-500 hrs", "500-1000 hrs", ">1000 hrs"
        ])
        rel_layout.addRow("MTBF Category:", self.mtbf_category)
        self.reliability_rating = self._create_combo_with_manual([
            "Excellent", "Good", "Acceptable", "Risky", "Poor"
        ])
        rel_layout.addRow("Reliability Rating:", self.reliability_rating)
        reliability_group.setLayout(rel_layout)
        layout.addWidget(reliability_group)

        # Administrative
        admin_group = QGroupBox("Administrative")
        admin_layout = QFormLayout()
        self.approval_status = self._create_combo_with_manual([
            "Draft", "Submitted", "Approved", "Rejected", "Archived"
        ])
        admin_layout.addRow("Approval Status:", self.approval_status)
        self.revision_number = self._create_combo_with_manual([
            "Rev A", "Rev B", "Rev C", "Rev 1.0", "Rev 2.0"
        ])
        admin_layout.addRow("Revision Number:", self.revision_number)
        self.received_data = QLineEdit()
        admin_layout.addRow("Received Data:", self.received_data)
        admin_group.setLayout(admin_layout)
        layout.addWidget(admin_group)

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
        btn_layout.addWidget(self.submit_btn)
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

    def add_entry(self) -> None:
        lru_text = self.lru_name_combo.currentText() or self.lru_name_combo.lineEdit().text()
        if not lru_text or lru_text == "Add New LRU...":
            QMessageBox.warning(self, "Validation Error", "Please enter LRU Name.")
            return

        # Date of PI: required; blank means missing
        date_pi = self.date_of_pi.date()
        date_pi_str = date_pi.toString("dd-MM-yyyy") if date_pi and date_pi.isValid() else ""
        required = {
            "LRU Name": lru_text if lru_text and lru_text != "Add New LRU..." else "",
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
            "lru_name": lru_text,
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
            "lru_category": self._get_combo_value(self.lru_category),
            "platform_aircraft_type": self._get_combo_value(self.platform),
            "manufacturer": self._get_combo_value(self.manufacturer),
            "test_standard": self._get_combo_value(self.test_standard),
            "test_lab": self._get_combo_value(self.test_lab),
            "temperature_range": self._get_combo_value(self.temperature_range),
            "humidity_level": self._get_combo_value(self.humidity_level),
            "vibration_level": self._get_combo_value(self.vibration_level),
            "altitude_condition": self._get_combo_value(self.altitude_condition),
            "voltage_input": self._get_combo_value(self.voltage_input),
            "power_consumption_range": self._get_combo_value(self.power_consumption),
            "failure_type": self._get_combo_value(self.failure_type),
            "severity_level": self._get_combo_value(self.severity_level),
            "corrective_action_status": self._get_combo_value(self.corrective_action),
            "mtbf_category": self._get_combo_value(self.mtbf_category),
            "reliability_rating": self._get_combo_value(self.reliability_rating),
            "test_engineer": self._get_combo_value(self.test_engineer),
            "approval_status": self._get_combo_value(self.approval_status),
            "revision_number": self._get_combo_value(self.revision_number),
        }

        success, message = self.db.add_entry(entry_data)
        if success:
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
        """Clear all form values."""
        for widget in self.findChildren(QComboBox):
            widget.setCurrentIndex(-1)  # Clear selection
            if widget.isEditable():
                le = widget.lineEdit()
                le.clear()
                # Reset dropdown selection flag
                widget._selected_from_dropdown = False
        for widget in self.findChildren(QLineEdit):
            widget.clear()
        for widget in self.findChildren(QDateEdit):
            widget.setDate(QDate.currentDate())
        self.date_of_pi.clear()
        self.date_of_clearance.clear()
        # Clear uploaded files
        self.uploaded_files = []
        self.uploaded_files_list.clear()
        self.file_preview_label.setText("Select a file to preview")
        self.file_preview_label.setPixmap(QPixmap())
