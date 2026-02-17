"""Add entry view: form for creating new test data records."""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class AddEntryWidget(QWidget):
    """Widget for adding new test data entries."""

    entry_added = pyqtSignal()

    def __init__(self, db) -> None:
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("➕ Add New Test Data Entry")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        form_group = QGroupBox("Entry Details")
        form_layout = QFormLayout()
        self.lru_name = QLineEdit()
        self.lru_name.setPlaceholderText("e.g., 5RW GEN, DCMB GPRU")
        self.project = QLineEdit()
        self.project.setPlaceholderText("e.g., LCA")
        self.division_group = QLineEdit()
        self.division_group.setPlaceholderText("e.g., A/C Division")
        self.system = QLineEdit()
        self.system.setPlaceholderText("e.g., ELE")
        self.part_number = QLineEdit()
        self.part_number.setPlaceholderText("e.g., GCCAIA")
        self.serial_no = QLineEdit()
        self.serial_no.setPlaceholderText("e.g., 96 / 1610000412024")
        self.received_data = QLineEdit()
        self.received_data.setPlaceholderText("e.g., Unit received for inspection")
        self.type_of_test = QLineEdit()
        self.type_of_test.setPlaceholderText("e.g., PI, PI Starter")
        self.test_rig = QLineEdit()
        self.test_rig.setPlaceholderText("e.g., LCA EPGS, IJT EPGS")
        self.date_of_pi = QLineEdit()
        self.date_of_pi.setPlaceholderText("e.g., 01-01-2026")
        self.results_remarks = QComboBox()
        self.results_remarks.addItems(["", "OK", "NOT OK"])
        self.date_of_clearance = QLineEdit()
        self.date_of_clearance.setPlaceholderText("e.g., 04-01-2026")
        form_layout.addRow("LRU Name *:", self.lru_name)
        form_layout.addRow("Project *:", self.project)
        form_layout.addRow("Division / Group *:", self.division_group)
        form_layout.addRow("System *:", self.system)
        form_layout.addRow("Part Number:", self.part_number)
        form_layout.addRow("Serial No *:", self.serial_no)
        form_layout.addRow("Received Data:", self.received_data)
        form_layout.addRow("Type of Test *:", self.type_of_test)
        form_layout.addRow("Test Rig *:", self.test_rig)
        form_layout.addRow("Date of PI *:", self.date_of_pi)
        form_layout.addRow("Results & Remarks *:", self.results_remarks)
        form_layout.addRow("Date of Clearance:", self.date_of_clearance)
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        button_layout = QHBoxLayout()
        self.submit_btn = QPushButton("✅ Add Entry")
        self.submit_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 10px; font-size: 14px;"
        )
        self.submit_btn.clicked.connect(self.add_entry)
        self.clear_btn = QPushButton("🗑️ Clear Form")
        self.clear_btn.setStyleSheet(
            "background-color: #f44336; color: white; padding: 10px; font-size: 14px;"
        )
        self.clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(self.submit_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        layout.addStretch()

    def add_entry(self) -> None:
        required_fields = {
            "LRU Name": self.lru_name.text().strip(),
            "Project": self.project.text().strip(),
            "Division / Group": self.division_group.text().strip(),
            "System": self.system.text().strip(),
            "Serial No": self.serial_no.text().strip(),
            "Type of Test": self.type_of_test.text().strip(),
            "Test Rig": self.test_rig.text().strip(),
            "Date of PI": self.date_of_pi.text().strip(),
            "Results & Remarks": self.results_remarks.currentText(),
        }
        missing_fields = [k for k, v in required_fields.items() if not v]
        if missing_fields:
            QMessageBox.warning(
                self,
                "Validation Error",
                f"Please fill in all required fields.\n"
                f"Missing: {', '.join(missing_fields)}",
            )
            return
        entry_data = {
            "lru_name": self.lru_name.text().strip(),
            "project": self.project.text().strip(),
            "division_group": self.division_group.text().strip(),
            "system": self.system.text().strip(),
            "part_number": self.part_number.text().strip(),
            "serial_no": self.serial_no.text().strip(),
            "received_data": self.received_data.text().strip(),
            "type_of_test": self.type_of_test.text().strip(),
            "test_rig": self.test_rig.text().strip(),
            "date_of_pi": self.date_of_pi.text().strip(),
            "results_remarks": self.results_remarks.currentText(),
            "date_of_clearance": self.date_of_clearance.text().strip(),
        }
        success, message = self.db.add_entry(entry_data)
        if success:
            QMessageBox.information(self, "Success", message)
            self.clear_form()
            self.entry_added.emit()
        else:
            QMessageBox.critical(self, "Error", message)

    def clear_form(self) -> None:
        self.lru_name.clear()
        self.project.clear()
        self.division_group.clear()
        self.system.clear()
        self.part_number.clear()
        self.serial_no.clear()
        self.received_data.clear()
        self.type_of_test.clear()
        self.test_rig.clear()
        self.date_of_pi.clear()
        self.results_remarks.setCurrentIndex(0)
        self.date_of_clearance.clear()
