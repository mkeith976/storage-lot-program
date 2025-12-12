"""Tkinter UI for the Storage & Recovery Lot program."""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import subprocess
import tempfile
import tkinter.font as tkfont

from lot_logic import (
    add_notice,
    balance,
    build_contract,
    default_fee_schedule,
    format_contract_summary,
    format_contract_record,
    lien_eligibility,
    lien_timeline,
    load_data,
    load_fee_templates,
    past_due_status,
    record_payment,
    save_data,
    save_fee_templates,
    storage_days,
)
from lot_models import Customer, Vehicle, StorageContract, StorageData, DATE_FORMAT


def create_rounded_frame(parent, width, height, radius, bg_color, border_color="#000000"):
    """Create a frame with rounded corners using Canvas."""
    canvas = tk.Canvas(parent, width=width, height=height, bg=parent.cget("bg"), 
                      highlightthickness=0, bd=0)
    
    # Draw rounded rectangle
    canvas.create_arc(0, 0, radius*2, radius*2, start=90, extent=90, 
                     fill=bg_color, outline=border_color, width=1)
    canvas.create_arc(width-radius*2, 0, width, radius*2, start=0, extent=90, 
                     fill=bg_color, outline=border_color, width=1)
    canvas.create_arc(0, height-radius*2, radius*2, height, start=180, extent=90, 
                     fill=bg_color, outline=border_color, width=1)
    canvas.create_arc(width-radius*2, height-radius*2, width, height, start=270, extent=90, 
                     fill=bg_color, outline=border_color, width=1)
    
    # Fill the middle
    canvas.create_rectangle(radius, 0, width-radius, height, fill=bg_color, outline=border_color, width=1)
    canvas.create_rectangle(0, radius, width, height-radius, fill=bg_color, outline="")
    
    return canvas


class ThemeManager:
    """Centralized theme management for consistent styling across all widgets."""
    
    THEMES = {
        "Light": {
            "bg": "#f5f6f7",
            "fg": "#2c3e50",
            "select_bg": "#0078d4",
            "select_fg": "#ffffff",
            "tree_odd": "#ffffff",
            "tree_even": "#f8f9fa",
            "button_bg": "#0078d4",
            "button_fg": "#ffffff",
            "button_hover": "#005a9e",
            "entry_bg": "#ffffff",
            "entry_fg": "#2c3e50",
            "frame_bg": "#f5f6f7",
            "accent": "#0078d4",
            "border": "#e1e4e8",
            "menu_bg": "#f5f6f7",
        },
        "Dark": {
            "bg": "#1e1e1e",
            "fg": "#e0e0e0",
            "select_bg": "#0e639c",
            "select_fg": "#ffffff",
            "tree_odd": "#252526",
            "tree_even": "#2d2d30",
            "button_bg": "#0e639c",
            "button_fg": "#ffffff",
            "button_hover": "#1177bb",
            "entry_bg": "#2d2d30",
            "entry_fg": "#e0e0e0",
            "frame_bg": "#1e1e1e",
            "accent": "#0e639c",
            "border": "#3e3e42",
            "menu_bg": "#2d2d30",
        },
        "Blue": {
            "bg": "#e8f2ff",
            "fg": "#002b5c",
            "select_bg": "#0066cc",
            "select_fg": "#ffffff",
            "tree_odd": "#f5faff",
            "tree_even": "#e0efff",
            "button_bg": "#0066cc",
            "button_fg": "#ffffff",
            "button_hover": "#0052a3",
            "entry_bg": "#ffffff",
            "entry_fg": "#002b5c",
            "frame_bg": "#e8f2ff",
            "accent": "#0066cc",
            "border": "#b3d9ff",
            "menu_bg": "#d0e7ff",
        },
        "Green": {
            "bg": "#e8f5e9",
            "fg": "#1b5e20",
            "select_bg": "#2e7d32",
            "select_fg": "#ffffff",
            "tree_odd": "#f1f8f4",
            "tree_even": "#dcedc8",
            "button_bg": "#2e7d32",
            "button_fg": "#ffffff",
            "button_hover": "#1b5e20",
            "entry_bg": "#ffffff",
            "entry_fg": "#1b5e20",
            "frame_bg": "#e8f5e9",
            "accent": "#2e7d32",
            "border": "#a5d6a7",
            "menu_bg": "#d4e8d5",
        },
        "Purple": {
            "bg": "#f3e5f5",
            "fg": "#4a148c",
            "select_bg": "#7b1fa2",
            "select_fg": "#ffffff",
            "tree_odd": "#faf5fc",
            "tree_even": "#ede7f6",
            "button_bg": "#7b1fa2",
            "button_fg": "#ffffff",
            "button_hover": "#6a1b9a",
            "entry_bg": "#ffffff",
            "entry_fg": "#4a148c",
            "frame_bg": "#f3e5f5",
            "accent": "#7b1fa2",
            "border": "#ce93d8",
            "menu_bg": "#e8d5ed",
        },
        "Monokai": {
            "bg": "#272822",
            "fg": "#f8f8f2",
            "select_bg": "#49483e",
            "select_fg": "#f8f8f2",
            "tree_odd": "#272822",
            "tree_even": "#3e3d32",
            "button_bg": "#66d9ef",
            "button_fg": "#272822",
            "button_hover": "#a6e22e",
            "entry_bg": "#3e3d32",
            "entry_fg": "#f8f8f2",
            "frame_bg": "#272822",
            "accent": "#66d9ef",
            "border": "#49483e",
            "menu_bg": "#3e3d32",
        },
    }
    
    def __init__(self, theme_name="Light"):
        self.current_theme = theme_name
        self.colors = self.THEMES[theme_name]
    
    def get_colors(self):
        return self.colors
    
    def set_theme(self, theme_name):
        if theme_name in self.THEMES:
            self.current_theme = theme_name
            self.colors = self.THEMES[theme_name]
            return True
        return False
    
    def configure_ttk_style(self, style):
        """Configure all ttk widget styles with current theme."""
        c = self.colors
        
        # Configure fonts
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Segoe UI", size=10)
        heading_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        
        # Frame
        style.configure("TFrame", background=c["frame_bg"])
        
        # Label
        style.configure("TLabel", background=c["frame_bg"], foreground=c["fg"], font=default_font)
        
        # Button
        style.configure("TButton",
                       background=c["button_bg"],
                       foreground=c["button_fg"],
                       borderwidth=0,
                       focuscolor="none",
                       padding=(12, 6),
                       relief="flat")
        style.map("TButton",
                 background=[("active", c["button_hover"]), ("pressed", c["button_hover"])],
                 foreground=[("active", c["button_fg"])])
        
        # Entry
        style.configure("TEntry",
                       fieldbackground=c["entry_bg"],
                       foreground=c["entry_fg"],
                       borderwidth=1,
                       relief="solid",
                       padding=6,
                       insertcolor=c["fg"])
        style.map("TEntry",
                 fieldbackground=[("focus", c["entry_bg"])],
                 bordercolor=[("focus", c["accent"])])
        
        # Combobox
        style.configure("TCombobox",
                       fieldbackground=c["entry_bg"],
                       background=c["entry_bg"],
                       foreground=c["entry_fg"],
                       borderwidth=1,
                       relief="solid",
                       padding=6,
                       arrowsize=14,
                       insertcolor=c["fg"])
        style.map("TCombobox",
                 fieldbackground=[("readonly", c["entry_bg"]), ("focus", c["entry_bg"])],
                 foreground=[("readonly", c["entry_fg"])],
                 selectbackground=[("focus", c["select_bg"])],
                 selectforeground=[("focus", c["select_fg"])],
                 bordercolor=[("focus", c["accent"])])
        
        # Treeview
        style.configure("Treeview",
                       background=c["tree_odd"],
                       foreground=c["fg"],
                       fieldbackground=c["tree_odd"],
                       borderwidth=0,
                       relief="flat",
                       rowheight=28,
                       font=default_font)
        style.configure("Treeview.Heading",
                       background=c["button_bg"],
                       foreground=c["button_fg"],
                       borderwidth=0,
                       relief="flat",
                       font=heading_font)
        style.map("Treeview",
                 background=[("selected", c["select_bg"])],
                 foreground=[("selected", c["select_fg"])])
        style.map("Treeview.Heading",
                 background=[("active", c["button_hover"])])
        
        # Notebook - Modern smooth tabs
        style.configure("TNotebook", 
                       background=c["bg"], 
                       borderwidth=0,
                       tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab",
                       background=c["button_bg"],
                       foreground=c["fg"],
                       padding=(20, 10),
                       borderwidth=0,
                       focuscolor="")
        style.map("TNotebook.Tab",
                 background=[("selected", c["accent"]), ("active", c["button_hover"])],
                 foreground=[("selected", c["select_fg"]), ("active", c["fg"])],
                 expand=[("selected", [1, 1, 1, 0])])
        
        # Frame styling for tab content
        style.configure("Tab.TFrame",
                       background=c["frame_bg"],
                       relief="flat",
                       borderwidth=0)
        
        # LabelFrame
        style.configure("TLabelframe",
                       background=c["frame_bg"],
                       borderwidth=1,
                       bordercolor=c["border"],
                       relief="solid",
                       padding=8)
        style.configure("TLabelframe.Label",
                       background=c["frame_bg"],
                       foreground=c["fg"],
                       padding=(4, 2),
                       font=heading_font)
        
        # Scrollbar
        style.configure("Vertical.TScrollbar",
                       background=c["frame_bg"],
                       troughcolor=c["frame_bg"],
                       borderwidth=0,
                       relief="flat",
                       width=12,
                       arrowsize=10)
        style.map("Vertical.TScrollbar",
                 background=[("active", c["select_bg"]), ("!active", c["border"])])


class LotApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        
        # Use normal window with title
        self.title("Storage & Recovery Lot")
        self.geometry("1200x700")
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        self._load_theme_preference()
        
        # Set initial window background
        c = self.theme_manager.get_colors()
        self.configure(bg=c["bg"], highlightthickness=0)
        
        # Apply theme
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except:
            pass
        
        self._apply_full_theme()
        self.storage_data: StorageData = load_data()
        self.fee_templates: Dict[str, Dict[str, float]] = load_fee_templates()

        # Create custom title bar with menu
        self._build_custom_titlebar()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.contract_tab = ttk.Frame(self.notebook)
        self.intake_tab = ttk.Frame(self.notebook)
        self.fee_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.contract_tab, text="Contracts")
        self.notebook.add(self.intake_tab, text="Intake")
        self.notebook.add(self.fee_tab, text="Fee Templates")

        self._build_contract_tab()
        self._build_intake_tab()
        self._build_fee_tab()

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.refresh_contracts()

    def _load_theme_preference(self) -> None:
        """Load saved theme from file."""
        try:
            theme_file = Path(__file__).parent / "theme_preference.txt"
            if theme_file.exists():
                saved = theme_file.read_text().strip()
                if self.theme_manager.set_theme(saved):
                    return
        except Exception:
            pass
        self.theme_manager.set_theme("Light")

    def _save_theme_preference(self) -> None:
        """Save current theme to file."""
        try:
            theme_file = Path(__file__).parent / "theme_preference.txt"
            theme_file.write_text(self.theme_manager.current_theme)
        except Exception:
            pass

    def _refresh_all_widget_colors(self) -> None:
        """Refresh colors for all created widgets."""
        c = self.theme_manager.get_colors()
        
        # Update main window background
        self.configure(bg=c["bg"])
        
        # Update treeview tags
        try:
            self.contract_tree.tag_configure("odd", background=c["tree_odd"], foreground=c["fg"])
            self.contract_tree.tag_configure("even", background=c["tree_even"], foreground=c["fg"])
        except: pass
        
        try:
            self.fee_tree.tag_configure("odd", background=c["tree_odd"], foreground=c["fg"])
            self.fee_tree.tag_configure("even", background=c["tree_even"], foreground=c["fg"])
        except: pass
        
        # Update summary text
        try:
            self.summary_text.configure(
                bg=c["entry_bg"],
                fg=c["entry_fg"],
                insertbackground=c["fg"],
                selectbackground=c["select_bg"],
                selectforeground=c["select_fg"]
            )
        except: pass
        
        # Update canvas backgrounds
        try:
            self.intake_canvas.configure(bg=c["frame_bg"])
        except: pass
        
        # Update custom title bar
        try:
            self.titlebar.configure(bg=c["menu_bg"])
            for widget in self.titlebar.winfo_children():
                if isinstance(widget, tk.Frame):
                    widget.configure(bg=c["menu_bg"])
                    for child in widget.winfo_children():
                        if isinstance(child, (tk.Label, tk.Menubutton)):
                            child.configure(bg=c["menu_bg"], fg=c["fg"])
                elif isinstance(widget, (tk.Label, tk.Menubutton)):
                    widget.configure(bg=c["menu_bg"], fg=c["fg"])
        except: pass
        
        # Update search bar
        try:
            self.search_container.configure(bg=c["entry_bg"], highlightbackground=c["border"], 
                                           highlightcolor=c["accent"])
            self.search_inner_frame.configure(bg=c["entry_bg"])
            self.search_entry.configure(bg=c["entry_bg"], fg=c["entry_fg"], 
                                       insertbackground=c["fg"], selectbackground=c["select_bg"],
                                       selectforeground=c["select_fg"])
            self.search_icon.configure(bg=c["entry_bg"], fg=c["fg"])
            # Update placeholder color if active
            if self.search_placeholder_active:
                self.search_entry.config(fg=c["border"])
        except: pass

    def _apply_full_theme(self) -> None:
        """Apply full theme styling via theme_manager."""
        c = self.theme_manager.get_colors()
        self.configure(bg=c["bg"])
        style = ttk.Style(self)
        self.theme_manager.configure_ttk_style(style)

    def _apply_theme(self, theme_name: str) -> None:
        """Apply a new theme and refresh all widgets."""
        if not self.theme_manager.set_theme(theme_name):
            return
        
        self._save_theme_preference()
        
        # Reapply full theme
        self._apply_full_theme()
        
        # Rebuild menu with new colors
        self._build_menu()
        
        # Refresh widget-specific colors
        self._refresh_all_widget_colors()
        
        # Refresh data displays
        self.refresh_contracts()
        self._refresh_fee_tree()

    def _show_settings(self) -> None:
        """Show settings dialog with theme, font size, and other preferences."""
        c = self.theme_manager.get_colors()
        settings_win = tk.Toplevel(self)
        settings_win.title("Settings")
        settings_win.geometry("500x600")
        settings_win.configure(bg=c["bg"])
        
        # Main container with scrollbar
        canvas = tk.Canvas(settings_win, bg=c["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(settings_win, orient=tk.VERTICAL, command=canvas.yview)
        frame = ttk.Frame(canvas, padding=20)
        
        frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Color Scheme Section
        ttk.Label(frame, text="Color Scheme", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 8))
        
        theme_frame = ttk.Frame(frame)
        theme_frame.pack(fill=tk.X, pady=(0, 16))
        
        theme_var = tk.StringVar(value=self.theme_manager.current_theme)
        
        # Display themes in a grid
        col = 0
        row = 0
        for theme_name in self.theme_manager.THEMES.keys():
            rb = ttk.Radiobutton(
                theme_frame,
                text=theme_name,
                variable=theme_var,
                value=theme_name,
                command=lambda t=theme_name: self._apply_theme(t)
            )
            rb.grid(row=row, column=col, sticky=tk.W, padx=10, pady=4)
            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1
        
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=16)
        
        # Font Size Section
        ttk.Label(frame, text="Font Size", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 8))
        
        font_frame = ttk.Frame(frame)
        font_frame.pack(fill=tk.X, pady=(0, 16))
        
        current_size = tkfont.nametofont("TkDefaultFont").actual("size")
        font_var = tk.IntVar(value=current_size)
        
        ttk.Label(font_frame, text="Base font size:").pack(side=tk.LEFT, padx=(0, 8))
        font_scale = ttk.Scale(font_frame, from_=8, to=14, variable=font_var, orient=tk.HORIZONTAL, 
                               command=lambda v: self._update_font_size(int(float(v))))
        font_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        font_label = ttk.Label(font_frame, text=f"{current_size}pt")
        font_label.pack(side=tk.LEFT)
        
        def update_label(v):
            size = int(float(v))
            font_label.config(text=f"{size}pt")
            self._update_font_size(size)
        
        font_scale.config(command=update_label)
        
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=16)
        
        # Window Settings
        ttk.Label(frame, text="Window Settings", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 8))
        
        window_frame = ttk.Frame(frame)
        window_frame.pack(fill=tk.X, pady=(0, 16))
        
        remember_size = tk.BooleanVar(value=True)
        ttk.Checkbutton(window_frame, text="Remember window size on exit", variable=remember_size).pack(anchor=tk.W, pady=4)
        
        maximize_start = tk.BooleanVar(value=False)
        ttk.Checkbutton(window_frame, text="Start maximized", variable=maximize_start).pack(anchor=tk.W, pady=4)
        
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=16)
        
        # Data Settings
        ttk.Label(frame, text="Data Management", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 8))
        
        data_frame = ttk.Frame(frame)
        data_frame.pack(fill=tk.X, pady=(0, 16))
        
        auto_save = tk.BooleanVar(value=True)
        ttk.Checkbutton(data_frame, text="Auto-save after each change", variable=auto_save).pack(anchor=tk.W, pady=4)
        
        backup_reminder = tk.BooleanVar(value=True)
        ttk.Checkbutton(data_frame, text="Show backup reminder on exit", variable=backup_reminder).pack(anchor=tk.W, pady=4)
        
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=16)
        
        # Display Settings
        ttk.Label(frame, text="Display Options", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 8))
        
        display_frame = ttk.Frame(frame)
        display_frame.pack(fill=tk.X, pady=(0, 16))
        
        show_grid = tk.BooleanVar(value=False)
        ttk.Checkbutton(display_frame, text="Show grid lines in tables", variable=show_grid).pack(anchor=tk.W, pady=4)
        
        compact_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(display_frame, text="Compact mode (smaller spacing)", variable=compact_mode).pack(anchor=tk.W, pady=4)
        
        # Close button
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(16, 0))
        ttk.Button(btn_frame, text="Close", command=settings_win.destroy).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Reset to Defaults", command=lambda: self._reset_settings(settings_win)).pack(side=tk.RIGHT, padx=(0, 8))
    
    def _update_font_size(self, size: int) -> None:
        """Update application font size."""
        try:
            default_font = tkfont.nametofont("TkDefaultFont")
            default_font.configure(size=size)
            heading_font = tkfont.nametofont("TkHeadingFont")
            heading_font.configure(size=size)
        except Exception:
            pass
    
    def _reset_settings(self, window) -> None:
        """Reset all settings to defaults."""
        from tkinter import messagebox
        if messagebox.askyesno("Reset Settings", "Reset all settings to defaults?"):
            self._apply_theme("Light")
            self._update_font_size(10)
            window.destroy()

    # ------------------------------------------------------------------
    # Contracts tab
    # ------------------------------------------------------------------
    def _build_contract_tab(self) -> None:
        container = ttk.Frame(self.contract_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Treeview with scrollbar
        tree_frame = ttk.Frame(container)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.contract_tree = ttk.Treeview(
            tree_frame,
            columns=("id", "customer", "vehicle", "type", "start", "balance", "status"),
            show="headings",
            height=12,
            yscrollcommand=vsb.set,
        )
        vsb.config(command=self.contract_tree.yview)
        
        for col, text, width in [
            ("id", "ID", 50),
            ("customer", "Customer", 200),
            ("vehicle", "Vehicle", 200),
            ("type", "Contract Type", 130),
            ("start", "Start", 90),
            ("balance", "Balance", 90),
            ("status", "Status", 80),
        ]:
            self.contract_tree.heading(col, text=text, command=lambda c=col: self._treeview_sort_column(c))
            self.contract_tree.column(col, width=width)
        
        self.contract_tree.bind("<<TreeviewSelect>>", lambda *_: self._show_selected_contract())
        self.contract_tree.bind("<Double-1>", lambda *_: self._on_contract_double_click())
        self.contract_tree.bind("<Button-3>", self._show_contract_menu)
        self.contract_tree.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=(8, 8))
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_contracts).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_frame, text="Record Payment", command=self._record_payment_dialog).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Add Note", command=self._add_note_dialog).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Generate Notice", command=self._add_notice_dialog).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Print Record", command=self._print_record).pack(side=tk.RIGHT, padx=(6, 0))

        detail = ttk.LabelFrame(container, text="Contract Details")
        detail.pack(fill=tk.BOTH, expand=True)

        # Text with vertical scrollbar
        text_frame = ttk.Frame(detail, relief="flat", borderwidth=0)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        text_vsb = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        text_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        c = self.theme_manager.get_colors()
        self.summary_text = tk.Text(text_frame, height=16, wrap="word", yscrollcommand=text_vsb.set, 
                                     relief="flat", borderwidth=0, highlightthickness=0,
                                     bg=c["entry_bg"], fg=c["entry_fg"], insertbackground=c["fg"],
                                     selectbackground=c["select_bg"], selectforeground=c["select_fg"])
        text_vsb.config(command=self.summary_text.yview)
        self.summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.summary_text.configure(state="disabled")

        timeline_frame = ttk.Frame(detail)
        timeline_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        # Initialize timeline labels with friendly defaults
        self.first_notice_var = tk.StringVar(value="1st Notice: —")
        self.second_notice_var = tk.StringVar(value="2nd Notice: —")
        self.lien_var = tk.StringVar(value="Earliest lien: —")
        self.lien_status_var = tk.StringVar(value="Lien status: —")
        ttk.Label(timeline_frame, textvariable=self.first_notice_var).pack(side=tk.LEFT, padx=8)
        ttk.Label(timeline_frame, textvariable=self.second_notice_var).pack(side=tk.LEFT, padx=8)
        ttk.Label(timeline_frame, textvariable=self.lien_var).pack(side=tk.LEFT, padx=8)
        ttk.Label(timeline_frame, textvariable=self.lien_status_var, foreground="blue").pack(side=tk.LEFT, padx=8)

    def _build_custom_titlebar(self) -> None:
        """Create custom menu bar with search integrated."""
        c = self.theme_manager.get_colors()
        
        # Menu bar frame with increased height
        self.titlebar = tk.Frame(self, bg=c["menu_bg"], relief="flat", bd=0, height=40)
        self.titlebar.pack(side=tk.TOP, fill=tk.X)
        self.titlebar.pack_propagate(False)  # Maintain fixed height
        
        # Modern search box (right side)
        search_outer = tk.Frame(self.titlebar, bg=c["menu_bg"])
        search_outer.pack(side=tk.RIGHT, padx=15, pady=8)
        
        search_container = tk.Frame(search_outer, bg=c["entry_bg"], 
                                   highlightthickness=1, 
                                   highlightbackground=c["border"], 
                                   highlightcolor=c["accent"],
                                   relief="solid", bd=0)
        search_container.pack()
        
        # Add some internal padding for rounded appearance
        inner_frame = tk.Frame(search_container, bg=c["entry_bg"])
        inner_frame.pack(padx=2, pady=2)
        
        # Search icon
        search_icon = tk.Label(inner_frame, text="🔍", bg=c["entry_bg"], fg=c["fg"], 
                              font=("Segoe UI", 10), padx=6, cursor="xterm")
        search_icon.pack(side=tk.LEFT)
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_placeholder_active = True
        
        search_entry = tk.Entry(inner_frame, textvariable=self.search_var, width=20,
                               bg=c["entry_bg"], fg=c["border"], relief="flat", 
                               insertbackground=c["fg"], selectbackground=c["select_bg"],
                               selectforeground=c["select_fg"], font=("Segoe UI", 9),
                               borderwidth=0, highlightthickness=0, cursor="xterm")
        search_entry.pack(side=tk.LEFT, padx=(0, 6), ipady=2)
        
        # Insert placeholder
        search_entry.insert(0, "Search contracts...")
        
        # Placeholder text handling
        def on_focus_in(event):
            if self.search_placeholder_active:
                self.search_var.set("")
                search_entry.config(fg=c["entry_fg"])
                self.search_placeholder_active = False
                search_container.config(highlightbackground=c["accent"], highlightthickness=2)
        
        def on_focus_out(event):
            search_container.config(highlightbackground=c["border"], highlightthickness=1)
            if not self.search_var.get():
                self.search_var.set("Search contracts...")
                search_entry.config(fg=c["border"])
                self.search_placeholder_active = True
        
        def on_key_release(event):
            # Update filter only if not placeholder
            if not self.search_placeholder_active:
                self._filter_contracts()
        
        # Click on icon to focus entry
        search_icon.bind("<Button-1>", lambda e: search_entry.focus_set())
        
        search_entry.bind("<FocusIn>", on_focus_in)
        search_entry.bind("<FocusOut>", on_focus_out)
        search_entry.bind("<KeyRelease>", on_key_release)
        
        # Store references for theme updates
        self.search_container = search_container
        self.search_inner_frame = inner_frame
        self.search_entry = search_entry
        self.search_icon = search_icon
        
        # Build menu (integrated into this bar)
        self._build_menu()

    def _build_menu(self) -> None:
        """Create the menubar with File / Edit / Help integrated into title bar."""
        colors = self.theme_manager.get_colors()
        
        # Menu container in title bar (left side)
        menu_frame = tk.Frame(self.titlebar, bg=colors["menu_bg"])
        menu_frame.pack(side=tk.LEFT, padx=8, pady=5)
        
        # File menu button
        file_btn = tk.Menubutton(menu_frame, text="File", bg=colors["menu_bg"], fg=colors["fg"],
                                 font=("Segoe UI", 9), relief="flat", cursor="hand2", borderwidth=0,
                                 activebackground=colors["button_hover"], activeforeground=colors["fg"],
                                 padx=8, pady=4)
        file_btn.pack(side=tk.LEFT, padx=1)
        file_menu = tk.Menu(file_btn, tearoff=0, bg=colors["entry_bg"], fg=colors["fg"],
                           activebackground=colors["select_bg"], activeforeground=colors["select_fg"],
                           borderwidth=0)
        file_menu.add_command(label="Print", accelerator="Ctrl+P", command=self._print_record)
        file_menu.add_command(label="Export Selected Summary...", accelerator="Ctrl+E", command=self._export_selected_summary)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", accelerator="Ctrl+Q", command=self.quit)
        file_btn["menu"] = file_menu

        # Edit menu button
        edit_btn = tk.Menubutton(menu_frame, text="Edit", bg=colors["menu_bg"], fg=colors["fg"],
                                font=("Segoe UI", 9), relief="flat", cursor="hand2", borderwidth=0,
                                activebackground=colors["button_hover"], activeforeground=colors["fg"],
                                padx=8, pady=4)
        edit_btn.pack(side=tk.LEFT, padx=1)
        edit_menu = tk.Menu(edit_btn, tearoff=0, bg=colors["entry_bg"], fg=colors["fg"],
                           activebackground=colors["select_bg"], activeforeground=colors["select_fg"],
                           borderwidth=0)
        edit_menu.add_command(label="Copy Summary", accelerator="Ctrl+C", command=self._copy_summary)
        edit_btn["menu"] = edit_menu

        # Help menu button
        help_btn = tk.Menubutton(menu_frame, text="Help", bg=colors["menu_bg"], fg=colors["fg"],
                                font=("Segoe UI", 9), relief="flat", cursor="hand2", borderwidth=0,
                                activebackground=colors["button_hover"], activeforeground=colors["fg"],
                                padx=8, pady=4)
        help_btn.pack(side=tk.LEFT, padx=1)
        help_menu = tk.Menu(help_btn, tearoff=0, bg=colors["entry_bg"], fg=colors["fg"],
                           activebackground=colors["select_bg"], activeforeground=colors["select_fg"],
                           borderwidth=0)
        help_menu.add_command(label="Settings", command=self._show_settings)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)
        help_btn["menu"] = help_menu

        # Keyboard shortcuts (Ctrl on Linux/Windows)
        # Bindings call the same handlers; event arg is ignored.
        self.bind_all("<Control-c>", lambda e: self._copy_summary())
        self.bind_all("<Control-C>", lambda e: self._copy_summary())
        self.bind_all("<Control-e>", lambda e: self._export_selected_summary())
        self.bind_all("<Control-E>", lambda e: self._export_selected_summary())
        self.bind_all("<Control-p>", lambda e: self._print_record())
        self.bind_all("<Control-P>", lambda e: self._print_record())
        self.bind_all("<Control-q>", lambda e: self.quit())
        self.bind_all("<Control-Q>", lambda e: self.quit())

    def refresh_contracts(self) -> None:
        # Clear existing rows
        for row in self.contract_tree.get_children():
            self.contract_tree.delete(row)

        # Configure alternating row colors based on theme
        colors = self.theme_manager.get_colors()
        try:
            self.contract_tree.tag_configure("odd", background=colors["tree_odd"])
            self.contract_tree.tag_configure("even", background=colors["tree_even"])
        except Exception:
            pass

        for i, contract in enumerate(self.storage_data.contracts):
            bal = balance(contract)
            vehicle = f"{contract.vehicle.vehicle_type} {contract.vehicle.plate}"
            tag = "odd" if i % 2 == 0 else "even"
            self.contract_tree.insert(
                "",
                tk.END,
                iid=str(contract.contract_id),
                values=(
                    contract.contract_id,
                    contract.customer.name,
                    vehicle,
                    contract.contract_type,
                    contract.start_date,
                    f"${bal:.2f}",
                    contract.status,
                ),
                tags=(tag,),
            )
        # Update status bar with contract count
        try:
            self.status_var.set(f"Contracts: {len(self.storage_data.contracts)}")
        except Exception:
            pass
        self._show_selected_contract()

    def _filter_contracts(self) -> None:
        """Filter contracts based on search query."""
        # Check if contract_tree exists yet
        if not hasattr(self, 'contract_tree'):
            return
        
        # Check if placeholder is active
        if hasattr(self, 'search_placeholder_active') and self.search_placeholder_active:
            self.refresh_contracts()
            return
            
        search_text = self.search_var.get().lower()
        if not search_text:
            self.refresh_contracts()
            return
        
        # Clear existing rows
        for row in self.contract_tree.get_children():
            self.contract_tree.delete(row)
        
        # Configure alternating row colors based on theme
        colors = self.theme_manager.get_colors()
        try:
            self.contract_tree.tag_configure("odd", background=colors["tree_odd"])
            self.contract_tree.tag_configure("even", background=colors["tree_even"])
        except Exception:
            pass
        
        count = 0
        for i, contract in enumerate(self.storage_data.contracts):
            bal = balance(contract)
            vehicle = f"{contract.vehicle.vehicle_type} {contract.vehicle.plate}"
            # Search in customer name, vehicle, or contract ID
            if (search_text in contract.customer.name.lower() or
                search_text in vehicle.lower() or
                search_text in str(contract.contract_id).lower()):
                tag = "odd" if count % 2 == 0 else "even"
                self.contract_tree.insert(
                    "",
                    tk.END,
                    iid=str(contract.contract_id),
                    values=(
                        contract.contract_id,
                        contract.customer.name,
                        vehicle,
                        contract.contract_type,
                        contract.start_date,
                        f"${bal:.2f}",
                        contract.status,
                    ),
                    tags=(tag,),
                )
                count += 1
        self._show_selected_contract()

    def _on_contract_double_click(self) -> None:
        """Handle double-click on contract row."""
        contract = self._get_selected_contract()
        if contract:
            self.status_var.set(f"Selected contract #{contract.contract_id}")

    def _show_contract_menu(self, event: tk.Event) -> None:
        """Show right-click context menu for contract."""
        item = self.contract_tree.selection()
        if not item:
            return
        
        colors = self.theme_manager.get_colors()
        menu = tk.Menu(self, tearoff=0, bg=colors["entry_bg"], fg=colors["fg"],
                      activebackground=colors["select_bg"], activeforeground=colors["select_fg"],
                      borderwidth=0, relief="flat")
        menu.add_command(label="Record Payment", command=self._record_payment_dialog)
        menu.add_command(label="Add Note", command=self._add_note_dialog)
        menu.add_command(label="Generate Notice", command=self._add_notice_dialog)
        menu.add_separator()
        menu.add_command(label="Print Record", command=self._print_record)
        
        menu.post(event.x_root, event.y_root)

    def _treeview_sort_column(self, col: str) -> None:
        """Sort treeview by column."""
        items = [(self.contract_tree.set(k, col), k) for k in self.contract_tree.get_children()]
        items.sort()
        for index, (val, k) in enumerate(items):
            self.contract_tree.move(k, '', index)

    def _get_selected_contract(self) -> Optional[StorageContract]:
        sel = self.contract_tree.selection()
        if not sel:
            return None
        contract_id = int(sel[0])
        for contract in self.storage_data.contracts:
            if contract.contract_id == contract_id:
                return contract
        return None

    def _show_selected_contract(self) -> None:
        contract = self._get_selected_contract()
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", tk.END)
        if not contract:
            self.summary_text.insert("1.0", "Select a contract to see details.")
            self.summary_text.configure(state="disabled")
            return

        summary = format_contract_summary(contract)
        self.summary_text.insert("1.0", summary)
        self.summary_text.configure(state="disabled")

        timeline = lien_timeline(contract)
        past_due, days_past_due = past_due_status(contract)
        total_days = storage_days(contract)
        status_text = "Past due" if past_due else "Current"
        first_notice, second_notice, lien_eligible, lien_status = lien_eligibility(contract)
        self.first_notice_var.set(f"1st Notice: {timeline['first_notice']}")
        self.second_notice_var.set(f"2nd Notice: {timeline['second_notice']}")
        suffix = f"{total_days} days since intake"
        if past_due:
            suffix += f" | {days_past_due} days past due"
        self.lien_var.set(f"Earliest lien: {timeline['earliest_lien']} | {status_text} ({suffix})")
        self.lien_status_var.set(f"Lien status: {lien_status} (eligible {lien_eligible})")

    def _record_payment_dialog(self) -> None:
        contract = self._get_selected_contract()
        if not contract:
            messagebox.showwarning("Payment", "Select a contract first.")
            return
        amount_str = simpledialog.askstring("Payment", "Amount received:")
        if not amount_str:
            return
        try:
            amount = float(amount_str)
        except ValueError:
            messagebox.showerror("Payment", "Invalid amount")
            return
        method = simpledialog.askstring("Payment", "Method (cash/card/check):", initialvalue="cash") or "cash"
        note = simpledialog.askstring("Payment", "Note (optional):", initialvalue="") or ""
        record_payment(contract, amount, method, note)
        save_data(self.storage_data)
        self.refresh_contracts()

    def _add_note_dialog(self) -> None:
        contract = self._get_selected_contract()
        if not contract:
            messagebox.showwarning("Notes", "Select a contract first.")
            return
        note = simpledialog.askstring("Note", "Add note/attachment placeholder:")
        if not note:
            return
        contract.notes.append(note)
        save_data(self.storage_data)
        self._show_selected_contract()

    def _add_notice_dialog(self) -> None:
        contract = self._get_selected_contract()
        if not contract:
            messagebox.showwarning("Notices", "Select a contract first.")
            return
        amount_due = balance(contract)
        notice_type = simpledialog.askstring("Notice", "Notice type (1st/2nd/lien)", initialvalue="1st") or "1st"
        add_notice(contract, notice_type, amount_due)
        today = datetime.today().strftime(DATE_FORMAT)
        lower_type = notice_type.lower()
        if "1" in lower_type or "first" in lower_type:
            contract.first_notice_sent_date = today
        elif "2" in lower_type or "second" in lower_type:
            contract.second_notice_sent_date = today
        save_data(self.storage_data)
        self._show_selected_contract()

    def _print_record(self) -> None:
        contract = self._get_selected_contract()
        if not contract:
            messagebox.showwarning("Print Record", "Select a contract first.")
            return
        record = format_contract_record(contract)
        
        colors = self.theme_manager.get_colors()
        win = tk.Toplevel(self)
        win.title(f"Contract {contract.contract_id} Print Record")
        win.configure(bg=colors["bg"])
        
        # Text widget with theme colors
        text_frame = ttk.Frame(win)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        txt_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        txt_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        txt = tk.Text(text_frame, wrap="word", yscrollcommand=txt_scroll.set,
                     bg=colors["entry_bg"], fg=colors["entry_fg"],
                     insertbackground=colors["fg"], relief="flat",
                     borderwidth=0, highlightthickness=0, padx=12, pady=12)
        txt_scroll.config(command=txt.yview)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        txt.insert("1.0", record)
        txt.configure(state="disabled")
        
        button_frame = ttk.Frame(win)
        button_frame.pack(pady=8)
        ttk.Button(button_frame, text="Save to file", command=lambda: self._save_summary_to_file(record)).pack(side=tk.LEFT, padx=4)
        ttk.Button(button_frame, text="Print", command=lambda: self._print_to_default_printer(record)).pack(side=tk.LEFT, padx=4)


    def _save_summary_to_file(self, content: str) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not path:
            return
        Path(path).write_text(content, encoding="utf-8")
        messagebox.showinfo("Save", f"Saved to {path}")

    def _print_to_printer(self, content: str) -> None:
        """Write content to temp file and send to system printer using lpr."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            result = subprocess.run(['lpr', tmp_path], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                messagebox.showinfo("Print", "Contract sent to printer successfully.")
            else:
                messagebox.showerror("Print Error", f"Printer error: {result.stderr}")
        except FileNotFoundError:
            messagebox.showerror("Print Error", "lpr command not found. Ensure a printer is configured.")
        except subprocess.TimeoutExpired:
            messagebox.showerror("Print Error", "Print operation timed out.")
        except Exception as e:
            messagebox.showerror("Print Error", f"Failed to print: {str(e)}")
        finally:
            # Clean up temp file
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass

    def _print_to_default_printer(self, content: str) -> None:
        """Send content to the system default printer using `lpr`.

        This helper writes the content to a temporary file and calls `lpr`.
        Shows messagebox notifications on success/failure.
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            # Call lpr to send to default printer
            result = subprocess.run(['lpr', tmp_path], capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                messagebox.showinfo("Print", "Sent to default printer successfully.")
            else:
                messagebox.showerror("Print Error", f"Printer error: {result.stderr}")
        except FileNotFoundError:
            messagebox.showerror("Print Error", "lpr command not found. Ensure a printer is configured.")
        except subprocess.TimeoutExpired:
            messagebox.showerror("Print Error", "Print operation timed out.")
        except Exception as e:
            messagebox.showerror("Print Error", f"Failed to print: {str(e)}")
        finally:
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Intake tab
    # ------------------------------------------------------------------
    def _build_intake_tab(self) -> None:
        # Create canvas with scrollbar for intake form
        c = self.theme_manager.get_colors()
        canvas = tk.Canvas(self.intake_tab, highlightthickness=0, bg=c["frame_bg"])
        scrollbar = ttk.Scrollbar(self.intake_tab, orient=tk.VERTICAL, command=canvas.yview)
        frame = ttk.Frame(canvas, padding=12)
        
        # Store canvas reference for theme updates
        self.intake_canvas = canvas
        
        frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mouse wheel scrolling - bind to canvas and frame, not globally
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux
        
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        
        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)
        frame.bind("<Enter>", _bind_mousewheel)
        frame.bind("<Leave>", _unbind_mousewheel)

        contract_type_frame = ttk.Frame(frame)
        contract_type_frame.pack(fill=tk.X, pady=4)
        ttk.Label(contract_type_frame, text="Contract Type", width=20).pack(side=tk.LEFT)
        self.contract_type = tk.StringVar(value="Storage Only")
        ttk.Combobox(
            contract_type_frame,
            textvariable=self.contract_type,
            values=["Storage Only", "Tow & Recovery"],
            state="readonly",
        ).pack(side=tk.LEFT, padx=4)
        self.contract_type.trace_add("write", lambda *_: self._load_defaults_for_type())

        # Customer
        cust = ttk.LabelFrame(frame, text="Customer")
        cust.pack(fill=tk.X, pady=4)
        self.cust_name = tk.StringVar()
        self.cust_phone = tk.StringVar()
        self.cust_address = tk.StringVar()
        self._add_labeled_entry(cust, "Name", self.cust_name)
        self._add_labeled_entry(cust, "Phone", self.cust_phone)
        self._add_labeled_entry(cust, "Address", self.cust_address, width=50)

        # Vehicle
        veh = ttk.LabelFrame(frame, text="Vehicle")
        veh.pack(fill=tk.X, pady=4)
        self.plate = tk.StringVar()
        self.vin = tk.StringVar()
        self.vehicle_type = tk.StringVar(value="Car")
        self.make = tk.StringVar()
        self.model = tk.StringVar()
        self.color = tk.StringVar()
        self.recovery_miles = tk.StringVar(value="0")
        self.extra_labor = tk.StringVar(value="0")
        self.labor_rate = tk.StringVar()

        self._add_labeled_entry(veh, "Plate", self.plate)
        self._add_labeled_entry(veh, "VIN", self.vin)
        self._add_labeled_entry(veh, "Make", self.make)
        self._add_labeled_entry(veh, "Model", self.model)
        self._add_labeled_entry(veh, "Color", self.color)

        row = ttk.Frame(veh)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Vehicle Type", width=15).pack(side=tk.LEFT)
        type_box = ttk.Combobox(row, textvariable=self.vehicle_type, values=list(self.fee_templates.keys()))
        type_box.pack(side=tk.LEFT, padx=4)
        type_box.bind("<<ComboboxSelected>>", lambda *_: self._load_defaults_for_type())
        # load schedule for initial vehicle type
        schedule = self.fee_templates.get(self.vehicle_type.get(), default_fee_schedule(self.vehicle_type.get()))
        ttk.Label(row, text="Tow Miles", width=12).pack(side=tk.LEFT, padx=4)
        ttk.Entry(row, textvariable=self.recovery_miles, width=10).pack(side=tk.LEFT)
        ttk.Label(row, text="Extra Labor Minutes").pack(side=tk.LEFT, padx=4)
        ttk.Entry(row, textvariable=self.extra_labor, width=10).pack(side=tk.LEFT)
        ttk.Label(row, text="Labor Rate/hr").pack(side=tk.LEFT, padx=4)
        ttk.Entry(row, textvariable=self.labor_rate, width=10).pack(side=tk.LEFT)

        # Contract
        contract_frame = ttk.LabelFrame(frame, text="Storage Contract")
        contract_frame.pack(fill=tk.X, pady=4)
        # initialize contract fields from fee template for the selected vehicle type
        self.daily_rate = tk.StringVar(value=str(schedule.get('daily_rate', 0.0)))
        self.tow_fee = tk.StringVar(value=str(schedule.get('tow_fee', 0.0)))
        self.impound_fee = tk.StringVar(value=str(schedule.get('impound_fee', 0.0)))
        self.admin_fee = tk.StringVar(value=str(schedule.get('admin_fee', 0.0)))
        self.start_date = tk.StringVar(value=datetime.today().strftime(DATE_FORMAT))
        self.mileage_included = tk.StringVar(value=str(schedule.get('mileage_included', 0.0)))
        self.mileage_rate = tk.StringVar(value=str(schedule.get('mileage_rate', 0.0)))
        self.certified_mail_first = tk.StringVar(value=str(schedule.get('certified_mail_fee_first', 0.0)))
        self.certified_mail_second = tk.StringVar(value=str(schedule.get('certified_mail_fee_second', 0.0)))
        self.labor_rate = tk.StringVar(value=str(schedule.get('labor_rate', 0.0)))

        self._add_labeled_entry(contract_frame, "Start Date (YYYY-MM-DD)", self.start_date)
        self._add_labeled_entry(contract_frame, "Daily Storage Rate", self.daily_rate)
        self._add_labeled_entry(contract_frame, "Tow Fee", self.tow_fee)
        self._add_labeled_entry(contract_frame, "Impound Fee", self.impound_fee)
        self._add_labeled_entry(contract_frame, "Admin Fee", self.admin_fee)
        self._add_labeled_entry(contract_frame, "Mileage Included", self.mileage_included)
        self._add_labeled_entry(contract_frame, "Mileage Rate", self.mileage_rate)
        self._add_labeled_entry(contract_frame, "Certified Mail (1st)", self.certified_mail_first)
        self._add_labeled_entry(contract_frame, "Certified Mail (2nd)", self.certified_mail_second)

        ttk.Button(frame, text="Create Contract", command=self._create_contract).pack(pady=8)
        self._load_defaults_for_type()

    def _load_defaults_for_type(self) -> None:
        schedule = self.fee_templates.get(self.vehicle_type.get(), default_fee_schedule("Car"))
        self.daily_rate.set(f"{schedule['daily_rate']}")
        self.tow_fee.set(f"{schedule['tow_fee']}")
        self.impound_fee.set(f"{schedule['impound_fee']}")
        self.admin_fee.set(f"{schedule['admin_fee']}")
        if self.contract_type.get() == "Storage Only":
            self.mileage_included.set("0")
            self.mileage_rate.set("0")
            self.certified_mail_first.set("0")
            self.certified_mail_second.set("0")
        else:
            self.mileage_included.set(f"{schedule.get('mileage_included', 0.0)}")
            self.mileage_rate.set(f"{schedule.get('mileage_rate', 0.0)}")
            self.certified_mail_first.set(f"{schedule.get('certified_mail_fee_first', 0.0)}")
            self.certified_mail_second.set(f"{schedule.get('certified_mail_fee_second', 0.0)}")
        self.labor_rate.set(f"{schedule.get('labor_rate', self.labor_rate.get())}")

    def _create_contract(self) -> None:
        try:
            daily_rate = float(self.daily_rate.get())
            tow_fee = float(self.tow_fee.get())
            impound_fee = float(self.impound_fee.get())
            admin_fee = float(self.admin_fee.get())
            labor_minutes = float(self.extra_labor.get())
            labor_rate = float(self.labor_rate.get())
            recovery_miles = float(self.recovery_miles.get())
            miles_included = float(self.mileage_included.get())
            mileage_rate = float(self.mileage_rate.get())
            certified_first = float(self.certified_mail_first.get())
            certified_second = float(self.certified_mail_second.get())
        except ValueError:
            messagebox.showerror("Intake", "Please check numeric fields.")
            return

        customer = Customer(
            name=self.cust_name.get(),
            phone=self.cust_phone.get(),
            address=self.cust_address.get(),
        )
        vehicle = Vehicle(
            plate=self.plate.get(),
            vin=self.vin.get(),
            vehicle_type=self.vehicle_type.get(),
            make=self.make.get(),
            model=self.model.get(),
            color=self.color.get(),
            initial_mileage=0,
        )

        contract = build_contract(
            self.storage_data,
            customer,
            vehicle,
            self.start_date.get(),
            self.contract_type.get(),
            daily_rate,
            tow_fee,
            impound_fee,
            admin_fee,
            tow_fee,  # Use tow_fee as base fee
            miles_included,
            mileage_rate,
            certified_first,
            certified_second,
            labor_minutes,
            labor_rate,
            recovery_miles,
        )
        save_data(self.storage_data)
        messagebox.showinfo("Intake", f"Created contract #{contract.contract_id}")
        self.refresh_contracts()
        self._reset_intake_form()
        self.notebook.select(self.contract_tab)

    def _reset_intake_form(self) -> None:
        self.contract_type.set("Storage Only")
        self.cust_name.set("")
        self.cust_phone.set("")
        self.cust_address.set("")
        self.plate.set("")
        self.vin.set("")
        self.vehicle_type.set("Car")
        self.make.set("")
        self.model.set("")
        self.color.set("")
        self.recovery_miles.set("0")
        self.extra_labor.set("0")
        self.start_date.set(datetime.today().strftime(DATE_FORMAT))
        self._load_defaults_for_type()

        self.notebook.select(self.contract_tab)

    def _add_labeled_entry(self, parent: tk.Widget, label: str, var: tk.StringVar, width: int = 25) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label, width=20).pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=var, width=width).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Fee template tab
    # ------------------------------------------------------------------
    def _build_fee_tab(self) -> None:
        frame = ttk.Frame(self.fee_tab, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        self.fee_tree = ttk.Treeview(
            frame,
            columns=("type", "daily", "tow", "admin", "mileage_rate", "labor_rate"),
            show="headings",
            height=8,
        )
        for col, text, width in [
            ("type", "Vehicle Type", 160),
            ("daily", "Daily Storage", 120),
            ("tow", "Tow Fee", 100),
            ("admin", "Admin", 100),
            ("mileage_rate", "Mileage Rate", 110),
            ("labor_rate", "Labor/hr", 90),
        ]:
            self.fee_tree.heading(col, text=text)
            self.fee_tree.column(col, width=width)
        self.fee_tree.bind("<<TreeviewSelect>>", lambda *_: self._populate_fee_form())
        self.fee_tree.pack(fill=tk.X, pady=(0, 8))

        form = ttk.Frame(frame)
        form.pack(fill=tk.X, pady=4)
        self.fee_type = tk.StringVar()
        self.fee_daily = tk.StringVar()
        self.fee_tow = tk.StringVar()
        self.fee_admin = tk.StringVar()
        self.fee_mileage_included = tk.StringVar()
        self.fee_mileage_rate = tk.StringVar()
        self.fee_labor_rate = tk.StringVar()
        self.fee_cert_first = tk.StringVar()
        self.fee_cert_second = tk.StringVar()

        self._add_labeled_entry(form, "Vehicle Type", self.fee_type)
        self._add_labeled_entry(form, "Daily Storage", self.fee_daily)
        self._add_labeled_entry(form, "Tow Fee", self.fee_tow)
        self._add_labeled_entry(form, "Admin Fee", self.fee_admin)
        self._add_labeled_entry(form, "Mileage Included", self.fee_mileage_included)
        self._add_labeled_entry(form, "Mileage Rate", self.fee_mileage_rate)
        self._add_labeled_entry(form, "Labor Rate", self.fee_labor_rate)
        self._add_labeled_entry(form, "Cert Mail (1st)", self.fee_cert_first)
        self._add_labeled_entry(form, "Cert Mail (2nd)", self.fee_cert_second)

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=4)
        ttk.Button(btns, text="Save", command=self._save_fee_template).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Reset to Defaults", command=self._reset_templates).pack(side=tk.LEFT, padx=4)

        self._refresh_fee_tree()

    # ------------------------------------------------------------------
    # Menu actions
    # ------------------------------------------------------------------
    def _copy_summary(self) -> None:
        """Copy currently displayed summary text to the clipboard."""
        try:
            self.summary_text.configure(state="normal")
            text = self.summary_text.get("1.0", "end").strip()
            self.summary_text.configure(state="disabled")
            if not text:
                # Try to build from selected contract
                contract = self._get_selected_contract()
                if not contract:
                    messagebox.showwarning("Copy Summary", "No summary available to copy.")
                    return
                text = format_contract_summary(contract)
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copy", "Summary copied to clipboard.")
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy summary: {e}")

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About",
            "Storage & Recovery Lot\nVersion: 1.0\n\nManage contracts, fees, payments, and print records.",
        )

    def _export_selected_summary(self) -> None:
        contract = self._get_selected_contract()
        if not contract:
            messagebox.showwarning("Export", "Select a contract first.")
            return
        content = format_contract_record(contract)
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")], initialfile=f"contract_{contract.contract_id}.txt")
        if not path:
            return
        Path(path).write_text(content, encoding="utf-8")
        messagebox.showinfo("Export", f"Exported contract to {path}")

    def _refresh_fee_tree(self) -> None:
        # Clear existing rows
        for row in self.fee_tree.get_children():
            self.fee_tree.delete(row)

        # Configure alternating row colors based on theme
        colors = self.theme_manager.get_colors()
        try:
            self.fee_tree.tag_configure("odd", background=colors["tree_odd"])
            self.fee_tree.tag_configure("even", background=colors["tree_even"])
        except Exception:
            pass

        for i, (vehicle_type, fees) in enumerate(self.fee_templates.items()):
            tag = "odd" if i % 2 == 0 else "even"
            self.fee_tree.insert(
                "",
                tk.END,
                iid=vehicle_type,
                values=(
                    vehicle_type,
                    f"${fees['daily_rate']:.2f}",
                    f"${fees['tow_fee']:.2f}",
                    f"${fees['admin_fee']:.2f}",
                    f"${fees.get('mileage_rate', 0.0):.2f}",
                    f"${fees.get('labor_rate', 0.0):.2f}",
                ),
                tags=(tag,),
            )
        # Update status bar with template count
        try:
            self.status_var.set(f"Templates: {len(self.fee_templates)}")
        except Exception:
            pass

    def _populate_fee_form(self) -> None:
        sel = self.fee_tree.selection()
        if not sel:
            return
        vehicle_type = sel[0]
        fees = self.fee_templates.get(vehicle_type, default_fee_schedule("Car"))
        self.fee_type.set(vehicle_type)
        self.fee_daily.set(str(fees["daily_rate"]))
        self.fee_tow.set(str(fees["tow_fee"]))
        self.fee_admin.set(str(fees["admin_fee"]))
        self.fee_mileage_included.set(str(fees.get("mileage_included", 0.0)))
        self.fee_mileage_rate.set(str(fees.get("mileage_rate", 0.0)))
        self.fee_labor_rate.set(str(fees.get("labor_rate", 0.0)))
        self.fee_cert_first.set(str(fees.get("certified_mail_fee_first", 0.0)))
        self.fee_cert_second.set(str(fees.get("certified_mail_fee_second", 0.0)))

    def _save_fee_template(self) -> None:
        try:
            daily = float(self.fee_daily.get())
            tow = float(self.fee_tow.get())
            admin = float(self.fee_admin.get())
            miles_included = float(self.fee_mileage_included.get())
            mileage_rate = float(self.fee_mileage_rate.get())
            labor_rate = float(self.fee_labor_rate.get())
            cert_first = float(self.fee_cert_first.get())
            cert_second = float(self.fee_cert_second.get())
        except ValueError:
            messagebox.showerror("Fees", "Please enter numeric values")
            return
        vehicle_type = self.fee_type.get().strip() or "Custom"
        self.fee_templates[vehicle_type] = {
            "daily_rate": daily,
            "tow_fee": tow,
            "impound_fee": 0.0,
            "admin_fee": admin,
            "tow_base_fee": tow,  # Use same as tow_fee for compatibility
            "mileage_included": miles_included,
            "mileage_rate": mileage_rate,
            "labor_rate": labor_rate,
            "certified_mail_fee_first": cert_first,
            "certified_mail_fee_second": cert_second,
        }
        save_fee_templates(self.fee_templates)
        self._refresh_fee_tree()
        messagebox.showinfo("Fees", f"Saved template for {vehicle_type}")

    def _reset_templates(self) -> None:
        from lot_logic import DEFAULT_VEHICLE_FEES

        self.fee_templates = DEFAULT_VEHICLE_FEES.copy()
        save_fee_templates(self.fee_templates)
        self._refresh_fee_tree()


if __name__ == "__main__":
    app = LotApp()
    app.mainloop()
