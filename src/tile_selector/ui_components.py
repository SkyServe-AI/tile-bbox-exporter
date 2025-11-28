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
        
        # Preprocessing checkbox
        self.app.preprocess_enabled = tk.BooleanVar(value=False)
        preprocess_check = tk.Checkbutton(middle_section, text="Preprocess", 
                                         variable=self.app.preprocess_enabled,
                                         command=self.app.toggle_preprocessing,
                                         bg="#2d2d2d", fg="white", 
                                         selectcolor="#3c3c3c",
                                         activebackground="#2d2d2d", 
                                         activeforeground="white",
                                         font=('Segoe UI', self.app.base_font_size))
        preprocess_check.pack(side=tk.LEFT, padx=8)
        self._create_tooltip(preprocess_check, "Apply CLAHE and color correction to image")
        
        # LULC Classify button
        classify_style = btn_style.copy()
        classify_style['bg'] = '#9C27B0'
        classify_style['activebackground'] = '#BA68C8'
        classify_btn = tk.Button(middle_section, text="🔍 Classify LULC", 
                                command=self.app.classify_tiles_lulc, **classify_style)
        classify_btn.pack(side=tk.LEFT, padx=8)
        
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
        
        # Hand tool button with tooltip
        hand_tool_style = zoom_btn_style.copy()
        self.app.hand_tool_btn = tk.Button(zoom_section, text="✋", 
                                           command=self.app.toggle_hand_tool, **hand_tool_style)
        self.app.hand_tool_btn.pack(side=tk.LEFT, padx=8)
        self._create_tooltip(self.app.hand_tool_btn, "Hand Tool: Hover over tiles to see through overlay")
        
        # Overlay toggle button with tooltip
        overlay_style = zoom_btn_style.copy()
        self.app.overlay_toggle_btn = tk.Button(zoom_section, text="👁", 
                                                command=self.app.toggle_overlay, **overlay_style)
        self.app.overlay_toggle_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(self.app.overlay_toggle_btn, "Toggle Overlay: Show/Hide LULC classification overlay")
        
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
        
        # LULC Category Legend (initially hidden)
        self._setup_category_legend()
        
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
        
    def _setup_category_legend(self):
        """Setup LULC category legend panel"""
        from .lulc_classifier import LULCClassifier
        
        legend_frame = tk.Frame(self.app.side_panel, bg="#2d2d2d")
        self.app.legend_frame = legend_frame
        
        # Header
        legend_header = tk.Label(legend_frame, text="LULC Categories", bg="#2d2d2d", fg="white", 
                                font=('Segoe UI', 10, 'bold'), pady=8)
        legend_header.pack(side=tk.TOP, fill=tk.X)
        
        # Scrollable legend with proper padding
        legend_canvas = tk.Canvas(legend_frame, bg="#2d2d2d", highlightthickness=0, height=250)
        legend_scrollbar = tk.Scrollbar(legend_frame, orient=tk.VERTICAL, command=legend_canvas.yview)
        legend_inner = tk.Frame(legend_canvas, bg="#2d2d2d")
        
        legend_inner.bind("<Configure>", lambda e: legend_canvas.configure(scrollregion=legend_canvas.bbox("all")))
        legend_canvas.create_window((0, 0), window=legend_inner, anchor="nw")
        legend_canvas.configure(yscrollcommand=legend_scrollbar.set)
        
        legend_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=(0, 10))
        legend_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create category items
        self.app.category_counts = {}
        for category in LULCClassifier.CATEGORIES:
            color = LULCClassifier.CATEGORY_COLORS[category]
            
            item_frame = tk.Frame(legend_inner, bg="#2d2d2d")
            item_frame.pack(side=tk.TOP, fill=tk.X, pady=2, padx=5)
            
            # Color box
            color_box = tk.Label(item_frame, bg=color, width=2, relief=tk.RAISED, bd=1)
            color_box.pack(side=tk.LEFT, padx=3)
            
            # Category name and count
            label_text = f"{category}: 0"
            count_label = tk.Label(item_frame, text=label_text, bg="#2d2d2d", fg="white",
                                  font=('Segoe UI', 8), anchor='w')
            count_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)
            
            self.app.category_counts[category] = count_label
    
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
    
    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="#ffffe0", 
                           relief=tk.SOLID, borderwidth=1, font=('Segoe UI', 8))
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
