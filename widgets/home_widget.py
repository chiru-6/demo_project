"""Home page widget for the LCA Test Data Management System.

Provides a visually rich landing page with quick navigation cards
to key sections: Dashboard, Dataset Manager, Visualizations, and Chatbot.
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class HomeWidget(QWidget):
    """Interactive home page with navigation cards."""

    # Signals for navigation; MainWindow can connect these to switch tabs/pages.
    go_dashboard = pyqtSignal()
    go_dataset = pyqtSignal()
    go_visualizations = pyqtSignal()
    go_chatbot = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._init_ui()

    def _create_card(
        self,
        title: str,
        description: str,
        button_text: str,
        signal,
    ) -> QFrame:
        """Create a clickable card with title, description and action button."""
        card = QFrame()
        card.setObjectName("homeCard")
        card.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("homeCardTitle")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        desc_label = QLabel(description)
        desc_label.setObjectName("homeCardDesc")
        desc_label.setWordWrap(True)

        btn = QPushButton(button_text)
        btn.setObjectName("homeCardButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(signal)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        layout.addWidget(btn, alignment=Qt.AlignRight)

        return card

    def _init_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(24)

        # Header
        header = QLabel("Project Test Data Manager")
        header.setObjectName("homeHeader")
        header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        root_layout.addWidget(header)

        sub = QLabel(
            "Use the cards below to quickly jump to dashboards, edit datasets, "
            "explore visualizations, or ask questions via the AI chatbot."
        )
        sub.setObjectName("homeSubHeader")
        sub.setWordWrap(True)
        root_layout.addWidget(sub)

        # Cards grid
        grid = QGridLayout()
        grid.setSpacing(16)

        dashboard_card = self._create_card(
            "📊 Dashboard",
            "Overview of all test data with filters and summary statistics.",
            "Open dashboard",
            self.go_dashboard,
        )

        dataset_card = self._create_card(
            "🗂 Dataset Manager",
            "View and edit the underlying dataset, import new CSV files, and "
            "autofill missing values.",
            "Open dataset manager",
            self.go_dataset,
        )

        viz_card = self._create_card(
            "📈 Visualizations",
            "Interactive charts for projects, test rigs, results and more.",
            "View charts",
            self.go_visualizations,
        )

        chatbot_card = self._create_card(
            "🤖 AI Chatbot",
            "Ask natural-language questions about your test data.",
            "Chat with AI",
            self.go_chatbot,
        )

        grid.addWidget(dashboard_card, 0, 0)
        grid.addWidget(dataset_card, 0, 1)
        grid.addWidget(viz_card, 1, 0)
        grid.addWidget(chatbot_card, 1, 1)

        root_layout.addLayout(grid)

