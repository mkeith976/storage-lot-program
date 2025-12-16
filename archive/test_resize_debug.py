#!/usr/bin/env python3
"""Debug script to test window resize functionality."""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QEvent, QPoint
from PyQt6.QtGui import QCursor


class DebugResizeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(400, 300)
        
        # Resizing variables
        self.resizing = False
        self.resize_edge = None
        self.resize_start_pos = None
        self.resize_start_geometry = None
        self.resize_margin = 10
        
        # Create central widget with content
        central = QWidget()
        central.setStyleSheet("background-color: #2b2b2b;")
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        
        # Debug label
        self.debug_label = QLabel("Move mouse to edges to test resize detection")
        self.debug_label.setStyleSheet("color: white; padding: 20px; font-size: 14px;")
        self.debug_label.setWordWrap(True)
        layout.addWidget(self.debug_label)
        
        # Info label
        info = QLabel(f"Window size: {self.width()}x{self.height()}\nResize margin: {self.resize_margin}px")
        info.setStyleSheet("color: #888; padding: 20px;")
        layout.addWidget(info)
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        self.installEventFilter(self)
        
        print(f"Window initialized: {self.width()}x{self.height()}")
        print(f"Window geometry: {self.geometry()}")
        print(f"Resize margin: {self.resize_margin}px")
    
    def get_resize_edge(self, pos):
        """Determine which edge the mouse is near for resizing."""
        rect = self.rect()
        margin = self.resize_margin
        
        left = pos.x() < margin
        right = pos.x() > rect.width() - margin
        top = pos.y() < margin
        bottom = pos.y() > rect.height() - margin
        
        print(f"  pos: ({pos.x()}, {pos.y()}) | rect: {rect.width()}x{rect.height()}")
        print(f"  left={left} (x<{margin}), right={right} (x>{rect.width()-margin})")
        print(f"  top={top} (y<{margin}), bottom={bottom} (y>{rect.height()-margin})")
        
        if top and left:
            return 'top_left'
        elif top and right:
            return 'top_right'
        elif bottom and left:
            return 'bottom_left'
        elif bottom and right:
            return 'bottom_right'
        elif top:
            return 'top'
        elif bottom:
            return 'bottom'
        elif left:
            return 'left'
        elif right:
            return 'right'
        return None
    
    def eventFilter(self, obj, event):
        """Event filter to handle resize from anywhere in the window."""
        
        if event.type() == QEvent.Type.MouseMove:
            # Get global position and convert to window coordinates
            global_pos = event.globalPosition().toPoint()
            window_pos = self.mapFromGlobal(global_pos)
            
            if self.resizing:
                print(f"RESIZING: edge={self.resize_edge}")
                delta = global_pos - self.resize_start_pos
                geo = self.resize_start_geometry
                
                x, y = geo.x(), geo.y()
                w, h = geo.width(), geo.height()
                
                if 'left' in self.resize_edge:
                    x = geo.x() + delta.x()
                    w = geo.width() - delta.x()
                if 'right' in self.resize_edge:
                    w = geo.width() + delta.x()
                if 'top' in self.resize_edge:
                    y = geo.y() + delta.y()
                    h = geo.height() - delta.y()
                if 'bottom' in self.resize_edge:
                    h = geo.height() + delta.y()
                
                # Apply minimum size constraints
                if w < self.minimumWidth():
                    w = self.minimumWidth()
                    if 'left' in self.resize_edge:
                        x = geo.x() + geo.width() - w
                if h < self.minimumHeight():
                    h = self.minimumHeight()
                    if 'top' in self.resize_edge:
                        y = geo.y() + geo.height() - h
                
                self.setGeometry(x, y, w, h)
                return True
            else:
                # Update cursor based on edge proximity
                print(f"MouseMove at global=({global_pos.x()}, {global_pos.y()}) window=({window_pos.x()}, {window_pos.y()})")
                edge = self.get_resize_edge(window_pos)
                print(f"  -> Detected edge: {edge}")
                
                if edge:
                    if edge in ['top', 'bottom']:
                        print(f"  -> Setting SizeVerCursor")
                        self.setCursor(Qt.CursorShape.SizeVerCursor)
                    elif edge in ['left', 'right']:
                        print(f"  -> Setting SizeHorCursor")
                        self.setCursor(Qt.CursorShape.SizeHorCursor)
                    elif edge in ['top_left', 'bottom_right']:
                        print(f"  -> Setting SizeFDiagCursor")
                        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                    elif edge in ['top_right', 'bottom_left']:
                        print(f"  -> Setting SizeBDiagCursor")
                        self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                    
                    self.debug_label.setText(f"Edge detected: {edge}\nCursor should change!")
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                    self.debug_label.setText("No edge detected - normal cursor")
                print()
        
        elif event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                global_pos = event.globalPosition().toPoint()
                window_pos = self.mapFromGlobal(global_pos)
                
                print(f"MousePress at global=({global_pos.x()}, {global_pos.y()}) window=({window_pos.x()}, {window_pos.y()})")
                self.resize_edge = self.get_resize_edge(window_pos)
                print(f"  -> Detected edge: {self.resize_edge}")
                
                if self.resize_edge:
                    self.resizing = True
                    self.resize_start_pos = global_pos
                    self.resize_start_geometry = self.geometry()
                    print(f"  -> Started resizing from {self.resize_edge}")
                    self.debug_label.setText(f"Resizing from: {self.resize_edge}")
                    return True
                print()
        
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if self.resizing:
                print(f"MouseRelease - stopped resizing")
                self.resizing = False
                self.resize_edge = None
                self.resize_start_pos = None
                self.resize_start_geometry = None
                self.debug_label.setText("Resize complete")
                return True
        
        return super().eventFilter(obj, event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DebugResizeWindow()
    window.show()
    print("\n=== Debug window shown ===")
    print("Try moving mouse to each edge and corner")
    print("Watch the terminal for debug output\n")
    sys.exit(app.exec())
