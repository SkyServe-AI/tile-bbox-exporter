"""
UI Components Module for Tile Selector
Handles all GUI setup and styling
"""
import tkinter as tk
from tkinter import ttk


class UIComponents:
    """Manages UI components and styling for Tile Selector"""
    
    def __init__(self, root, app):
        self.root = root
        self.app = app
        
    def setup_gui(self):
        """Setup the main GUI layout"""
        self._setup_control_panel()
        self._setup_status_bar()
        self._setup_main_content()
        
    def _setup_control_panel(self):
        """Setup the top control panel with buttons - Two rows for better space management"""
        control_frame = tk.Frame(self.root, bg="#2d2d2d", relief=tk.FLAT, bd=0)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
        
        # Top row
        top_row = tk.Frame(control_frame, bg="#2d2d2d")
        top_row.pack(side=tk.TOP, fill=tk.X, padx=0, pady=(8, 4))
        
        # Bottom row
        bottom_row = tk.Frame(control_frame, bg="#2d2d2d")
        bottom_row.pack(side=tk.TOP, fill=tk.X, padx=0, pady=(4, 8))
        
        self._create_file_operations(top_row)
        self._create_zoom_controls(top_row)
        self._create_export_buttons(top_row)
        self._create_tile_controls(bottom_row)
        
    def _create_file_operations(self, parent):
        """Create file operation buttons"""
        left_section = tk.Frame(parent, bg="#2d2d2d")
        left_section.pack(side=tk.LEFT, padx=15, pady=12)
        
        btn_style = self._get_button_style()
        
        upload_file_btn = tk.Button(left_section, text="📁 Images", 
                                    command=self.app.upload_images, **btn_style)
        upload_file_btn.pack(side=tk.LEFT, padx=3)

        upload_folder_btn = tk.Button(left_section, text="📂 Folder", 
                                      command=self.app.upload_folder, **btn_style)
        upload_folder_btn.pack(side=tk.LEFT, padx=3)
        
    def _create_tile_controls(self, parent):
        """Create tile size control inputs"""
        middle_section = tk.Frame(parent, bg="#2d2d2d")
        middle_section.pack(side=tk.LEFT, padx=15, pady=12)
        
        tk.Label(middle_section, text="Tile Size:", bg="#2d2d2d", fg="white", 
                font=('Segoe UI', self.app.base_font_size)).pack(side=tk.LEFT, padx=3)
        
        self.app.tile_size_var = tk.StringVar(value=str(self.app.tile_size))
        tile_size_entry = tk.Entry(middle_section, textvariable=self.app.tile_size_var, width=8, 
                                   font=('Segoe UI', self.app.base_font_size), relief=tk.FLAT, 
                                   bg="#3c3c3c", fg="white", insertbackground="white")
        tile_size_entry.pack(side=tk.LEFT, padx=3)
        tile_size_entry.bind("<FocusOut>", self.app.validate_tile_size)

        btn_style = self._get_button_style()
        apply_btn = tk.Button(middle_section, text="✓ Apply", 
                             command=self.app.apply_tile_size, **btn_style)
        apply_btn.pack(side=tk.LEFT, padx=8)
        
    def _create_zoom_controls(self, parent):
        """Create zoom control buttons"""
        zoom_section = tk.Frame(parent, bg="#2d2d2d")
        zoom_section.pack(side=tk.LEFT, padx=15, pady=12)
        
        tk.Label(zoom_section, text="Zoom:", bg="#2d2d2d", fg="white", 
                font=('Segoe UI', self.app.base_font_size)).pack(side=tk.LEFT, padx=3)
        
        zoom_btn_style = self._get_button_style()
        zoom_btn_style['padx'] = 8
        zoom_btn_style['pady'] = 5
        
        zoom_out_btn = tk.Button(zoom_section, text="➖", 
                                command=self.app.zoom_out, **zoom_btn_style)
        zoom_out_btn.pack(side=tk.LEFT, padx=2)
        
        self.app.zoom_label = tk.Label(zoom_section, text="100%", bg="#2d2d2d", fg="white", 
                                       font=('Segoe UI', self.app.base_font_size, 'bold'), width=5)
        self.app.zoom_label.pack(side=tk.LEFT, padx=3)
        
        zoom_in_btn = tk.Button(zoom_section, text="➕", 
                               command=self.app.zoom_in, **zoom_btn_style)
        zoom_in_btn.pack(side=tk.LEFT, padx=2)
        
        zoom_reset_btn = tk.Button(zoom_section, text="⟲", 
                                   command=self.app.zoom_reset, **zoom_btn_style)
        zoom_reset_btn.pack(side=tk.LEFT, padx=2)
        
    def _create_export_buttons(self, parent):
        """Create export buttons"""
        right_section = tk.Frame(parent, bg="#2d2d2d")
        right_section.pack(side=tk.RIGHT, padx=10, pady=0)
        
        # Classification checkbox
        self.app.is_classification = tk.BooleanVar(value=False)
        classification_check = tk.Checkbutton(right_section, text="Classification", 
                                             variable=self.app.is_classification,
                                             bg="#2d2d2d", fg="white", 
                                             selectcolor="#3c3c3c",
                                             activebackground="#2d2d2d",
                                             activeforeground="white",
                                             font=('Segoe UI', self.app.base_font_size),
                                             cursor='hand2')
        classification_check.pack(side=tk.LEFT, padx=8)
        
        btn_style = self._get_button_style()
        export_style = btn_style.copy()
        export_style['bg'] = '#0d7d3a'
        export_style['activebackground'] = '#0e9647'
        
        export_btn = tk.Button(right_section, text="💾 Export", 
                              command=self.app.export_tiles_wrapper, **export_style)
        export_btn.pack(side=tk.LEFT, padx=3)
        
    def _setup_status_bar(self):
        """Setup the status bar at the bottom"""
        status_frame = tk.Frame(self.root, bg="#252525", relief=tk.FLAT, bd=0)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.app.status_label = tk.Label(status_frame, text="Ready | Upload images to start", 
                                         bg="#252525", fg="#aaaaaa", 
                                         font=('Segoe UI', self.app.status_font_size),
                                         anchor='w', padx=10, pady=5)
        self.app.status_label.pack(fill=tk.X)
        
    def _setup_main_content(self):
        """Setup main content area with side panel and canvas"""
        content_frame = tk.Frame(self.root, bg="#1e1e1e")
        content_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        self._setup_side_panel(content_frame)
        self._setup_canvas(content_frame)
        
    def _setup_side_panel(self, parent):
        """Setup side panel for image navigation"""
        self.app.side_panel = tk.Frame(parent, bg="#2d2d2d", width=200)
        self.app.side_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.app.side_panel.pack_propagate(False)
        
        # Header
        nav_header = tk.Label(self.app.side_panel, text="Images", bg="#2d2d2d", fg="white", 
                             font=('Segoe UI', 11, 'bold'), pady=10)
        nav_header.pack(side=tk.TOP, fill=tk.X)
        
        # Navigation buttons
        nav_btn_frame = tk.Frame(self.app.side_panel, bg="#2d2d2d")
        nav_btn_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        nav_btn_style = {
            'bg': '#0e639c',
            'fg': 'white',
            'font': ('Segoe UI', 9),
            'relief': tk.FLAT,
            'padx': 10,
            'pady': 5,
            'cursor': 'hand2',
            'activebackground': '#1177bb',
            'activeforeground': 'white'
        }
        
        self.app.prev_btn = tk.Button(nav_btn_frame, text="◄ Prev", 
                                      command=self.app.prev_image, **nav_btn_style)
        self.app.prev_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.app.next_btn = tk.Button(nav_btn_frame, text="Next ►", 
                                      command=self.app.next_image, **nav_btn_style)
        self.app.next_btn.pack(side=tk.RIGHT, padx=2, expand=True, fill=tk.X)
        
        # Image counter
        self.app.image_counter_label = tk.Label(self.app.side_panel, text="0 / 0", 
                                                bg="#2d2d2d", fg="#aaaaaa", font=('Segoe UI', 9))
        self.app.image_counter_label.pack(side=tk.TOP, pady=5)
        
        # Image list
        list_frame = tk.Frame(self.app.side_panel, bg="#2d2d2d")
        list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        list_scroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.app.image_listbox = tk.Listbox(list_frame, bg="#3c3c3c", fg="white", 
                                            font=('Segoe UI', 9), relief=tk.FLAT,
                                            selectbackground="#0e639c", selectforeground="white",
                                            yscrollcommand=list_scroll.set, activestyle='none')
        self.app.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.app.image_listbox.yview)
        self.app.image_listbox.bind('<<ListboxSelect>>', self.app.on_image_select)
        
    def _setup_canvas(self, parent):
        """Setup canvas for tile display"""
        canvas_frame = tk.Frame(parent, bg="#1e1e1e")
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.app.canvas = tk.Canvas(canvas_frame, bg="#0a0a0a", highlightthickness=0)
        self.app.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Setup scrollbars
        self._setup_scrollbars(canvas_frame)
        
    def _setup_scrollbars(self, parent):
        """Setup canvas scrollbars"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Vertical.TScrollbar", 
                       background="#2d2d2d",
                       troughcolor="#1e1e1e",
                       bordercolor="#1e1e1e",
                       arrowcolor="#aaaaaa",
                       darkcolor="#2d2d2d",
                       lightcolor="#2d2d2d")
        style.configure("Horizontal.TScrollbar",
                       background="#2d2d2d",
                       troughcolor="#1e1e1e",
                       bordercolor="#1e1e1e",
                       arrowcolor="#aaaaaa",
                       darkcolor="#2d2d2d",
                       lightcolor="#2d2d2d")
        
        v_scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, 
                                command=self.app.canvas.yview, style="Vertical.TScrollbar")
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scroll = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, 
                                command=self.app.canvas.xview, style="Horizontal.TScrollbar")
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.app.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
    def _get_button_style(self):
        """Get default button style"""
        return {
            'bg': '#0e639c',
            'fg': 'white',
            'font': ('Segoe UI', self.app.button_font_size),
            'relief': tk.FLAT,
            'padx': 12,
            'pady': 7,
            'cursor': 'hand2',
            'activebackground': '#1177bb',
            'activeforeground': 'white'
        }
