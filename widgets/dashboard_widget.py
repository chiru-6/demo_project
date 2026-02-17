from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtGui import QColor


class DashboardWidget(QWidget):
    """Dashboard widget showing high-level insights."""

    def __init__(self, db) -> None:
        """Initialize dashboard with a reference to the database (currently unused)."""
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        self.setObjectName("dashboardRoot")

        # MAIN LAYOUT
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(16, 8, 16, 16)

        # ================= TITLE =================
        title = QLabel("📊 Dashboard — Test Data Overview")
        title.setObjectName("dashboardTitle")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("margin: 0px; padding: 0px;")
        main_layout.addWidget(title)
        main_layout.addSpacing(0)


        # ================= STATS SECTION =================
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(12)
        stats_layout.setContentsMargins(16, 0, 16, 16)

        # Create Stat Cards
        stats_layout.addWidget(self.create_stat_card("Total Records\n360"))
        stats_layout.addWidget(self.create_stat_card("OK\n173"))
        stats_layout.addWidget(self.create_stat_card("NOT OK\n62"))

        main_layout.addWidget(stats_frame)

        # ================= INSIGHTS SECTION =================
        insights_layout = QHBoxLayout()
        insights_layout.setSpacing(12)

        insights_layout.addWidget(self.create_insight_card(
            "Top Projects",
            "AMCA (62)\nTEJAS (59)\nLCH (54)"
        ))

        insights_layout.addWidget(self.create_insight_card(
            "Top Test Rigs",
            "Hydraulic (61)\nAvionics (54)\nDT EPGS (53)"
        ))

        insights_layout.addWidget(self.create_insight_card(
            "Top Test Types",
            "Endurance (76)\nPI Starter (67)\nAcceptance (61)"
        ))

        main_layout.addLayout(insights_layout)

        # ================= STYLES =================
        self.setStyleSheet("""
        #dashboardRoot {
            background-color: #f4f6fb;
        }

        #dashboardTitle {
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
        }

        #statsFrame {
            background-color: white;
            border-radius: 14px;
        }

        #statCard {
            background-color: #e0e7ff;
            border-radius: 12px;
            padding: 12px;
            font-weight: bold;
            color: #1e3a8a;
        }

        #insightCard {
            background-color: white;
            border-radius: 14px;
            padding: 14px;
        }

        #insightTitle {
            font-weight: bold;
            font-size: 14px;
            color: #111827;
        }

        #insightBody {
            font-size: 13px;
            color: #374151;
        }
        """)

    # ================= HELPER FUNCTIONS =================

    def create_stat_card(self, text: str) -> QFrame:
        """Create a statistic card with shadow."""
        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("statCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)

        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(label)

        container_layout.addWidget(card)

        # Apply shadow to inner card, not layout container
        self.add_shadow(card)

        return container

    def create_insight_card(self, title: str, body: str) -> QFrame:
        """Create an insight card with title and multi-line body."""
        card = QFrame()
        card.setObjectName("insightCard")
        layout = QVBoxLayout(card)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("insightTitle")

        body_label = QLabel(body)
        body_label.setObjectName("insightBody")
        body_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(body_label)

        self.add_shadow(card)
        return card

    def add_shadow(self, widget: QFrame) -> None:
        """Apply a subtle drop shadow to a card widget."""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 40))
        widget.setGraphicsEffect(shadow)
