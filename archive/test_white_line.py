#!/usr/bin/env python3
"""Test to isolate the white line issue."""

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel
from PyQt6.QtCore import Qt
import sys

app = QApplication(sys.argv)

window = QMainWindow()
window.setWindowTitle("White Line Test")
window.setGeometry(100, 100, 800, 600)
window.setWindowFlags(Qt.WindowType.FramelessWindowHint)

# Central widget
central = QWidget()
window.setCentralWidget(central)
layout = QVBoxLayout(central)
layout.setContentsMargins(0, 0, 0, 0)
layout.setSpacing(0)

# Title bar simulation
title_bar = QWidget()
title_bar.setFixedHeight(40)
title_bar.setStyleSheet("background-color: #1e1e1e; border: none;")
layout.addWidget(title_bar)

# Content widget
content = QWidget()
content.setStyleSheet("background-color: #2b2b2b; border: none;")
content_layout = QVBoxLayout(content)
content_layout.setContentsMargins(0, 0, 0, 0)
content_layout.setSpacing(0)
layout.addWidget(content)

# Tab widget
tabs = QTabWidget()
tabs.setDocumentMode(True)
tabs.setStyleSheet("""
    QTabWidget {
        border: none;
        background: #2b2b2b;
    }
    QTabWidget::pane {
        border: none;
        background: #3c3c3c;
        margin: 0;
        padding: 0;
    }
    QTabBar {
        border: none;
        background: transparent;
    }
    QTabBar::tab {
        background: #3c3c3c;
        color: white;
        padding: 10px 20px;
        margin: 0;
        border: none;
    }
""")

tab1 = QWidget()
tab1.setStyleSheet("background: #3c3c3c;")
tab1_layout = QVBoxLayout(tab1)
tab1_layout.addWidget(QLabel("Tab 1 Content"))

tabs.addTab(tab1, "Tab 1")
tabs.addTab(QWidget(), "Tab 2")

content_layout.addWidget(tabs)

window.show()
print("Look for white line between title bar and tabs")
print("Title bar: #1e1e1e")
print("Main bg: #2b2b2b")
print("Tab bg: #3c3c3c")

sys.exit(app.exec())
