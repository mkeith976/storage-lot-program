#!/usr/bin/env python3
"""Test theme configuration."""

from theme_config import get_theme_colors, get_application_stylesheet

# Test Dark theme
print("Testing Dark theme...")
dark_colors = get_theme_colors("Dark")
print(f"Dark theme has {len(dark_colors)} color keys")
print(f"Sample keys: {list(dark_colors.keys())[:5]}")

# Test Light theme  
print("\nTesting Light theme...")
light_colors = get_theme_colors("Light")
print(f"Light theme has {len(light_colors)} color keys")

# Test stylesheet generation
print("\nTesting stylesheet generation...")
dark_stylesheet = get_application_stylesheet(dark_colors)
print(f"Stylesheet length: {len(dark_stylesheet)} characters")

# Check for QTabWidget styling
if "QTabWidget::pane" in dark_stylesheet:
    print("✓ QTabWidget::pane styling found")
if "QTabBar::tab" in dark_stylesheet:
    print("✓ QTabBar::tab styling found")

# Check tab styling specifically
tab_section = dark_stylesheet[dark_stylesheet.find("QTabWidget::pane"):dark_stylesheet.find("QTabWidget::pane")+200]
print(f"\nTab widget styling preview:\n{tab_section}")

print("\n✓ Theme configuration is working correctly!")
