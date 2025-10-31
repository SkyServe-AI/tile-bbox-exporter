"""
UI Components Module
Handles all GUI setup and styling for the BBox Selector
"""
import tkinter as tk
from tkinter import ttk


class UIComponents:
    """Manages UI components and styling"""
    
    def __init__(self, root, app):
        self.root = root
        self.app = app
        
    def setup_gui(self):
        """Setup the main GUI layout"""
        self._setup_control_panel()
        self._setup_status_bar()
        self._setup_main_content()
        
    def _setup_control_panel(self):
        """Setup the top control panel with buttons"""
        control_frame = tk.Frame(self.root, bg="#2d2d2d", relief=tk.FLAT, bd=0)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
        
        # Top row
        top_row = tk.Frame(control_frame, bg="#2d2d2d")
        top_row.pack(side=tk.TOP, fill=tk.X, padx=0, pady=(10, 5))
        
        # Bottom row
        bottom_row = tk.Frame(control_frame, bg="#2d2d2d")
        bottom_row.pack(side=tk.TOP, fill=tk.X, padx=0, pady=(5, 10))
        
        # Create button sections
        self._create_file_operations(top_row)
        self._create_zoom_controls(top_row)
        self._create_action_buttons(top_row)
        self._create_bbox_controls(bottom_row)
        
    def _create_file_operations(self, parent):
        """Create file operation buttons"""
        left_section = tk.Frame(parent, bg="#2d2d2d")
        left_section.pack(side=tk.LEFT, padx=10, pady=0)
        
        btn_style = self._get_button_style()
        
        upload_btn = tk.Button(left_section, text="📁 Load Image", 
                              command=self.app.load_image, **btn_style)
        upload_btn.pack(side=tk.LEFT, padx=3)
        
        upload_folder_btn = tk.Button(left_section, text="📂 Load Folder", 
                                      command=self.app.upload_folder, **btn_style)
        upload_folder_btn.pack(side=tk.LEFT, padx=3)
        
        # Polygon mode checkbox
        custom_check = tk.Checkbutton(left_section, text="✏️ Polygon Mode", 
                                     variable=self.app.custom_select_mode,
                                     command=self.app.toggle_custom_select,
                                     bg="#2d2d2d", fg="white", 
                                     selectcolor="#0078d4",
                                     activebackground="#2d2d2d",
                                     activeforeground="white",
                                     font=('Segoe UI', self.app.base_font_size),
                                     cursor='hand2',
                                     relief=tk.FLAT,
                                     borderwidth=0)
        custom_check.pack(side=tk.LEFT, padx=12)
        
    def _create_zoom_controls(self, parent):
        """Create zoom control buttons"""
        zoom_section = tk.Frame(parent, bg="#2d2d2d")
        zoom_section.pack(side=tk.LEFT, padx=10, pady=0)
        
        tk.Label(zoom_section, text="Zoom:", bg="#2d2d2d", fg="white", 
                font=('Segoe UI', self.app.base_font_size)).pack(side=tk.LEFT, padx=3)
        
        zoom_btn_style = self._get_button_style()
        zoom_btn_style['padx'] = 10
        zoom_btn_style['pady'] = 6
        
        zoom_out_btn = tk.Button(zoom_section, text="➖", 
                                command=self.app.zoom_out, **zoom_btn_style)
        zoom_out_btn.pack(side=tk.LEFT, padx=2)
        
        self.app.zoom_label = tk.Label(zoom_section, text="100%", bg="#2d2d2d", fg="white", 
                                       font=('Segoe UI', self.app.base_font_size, 'bold'), width=6)
        self.app.zoom_label.pack(side=tk.LEFT, padx=3)
        
        zoom_in_btn = tk.Button(zoom_section, text="➕", 
                               command=self.app.zoom_in, **zoom_btn_style)
        zoom_in_btn.pack(side=tk.LEFT, padx=2)
        
        zoom_reset_btn = tk.Button(zoom_section, text="⟲", 
                                   command=self.app.zoom_reset, **zoom_btn_style)
        zoom_reset_btn.pack(side=tk.LEFT, padx=2)
        
    def _create_action_buttons(self, parent):
        """Create action buttons (Delete, Clear, Save)"""
        right_section = tk.Frame(parent, bg="#2d2d2d")
        right_section.pack(side=tk.RIGHT, padx=10, pady=0)
        
        btn_style = self._get_button_style()
        
        # Delete button
        delete_style = btn_style.copy()
        delete_style['bg'] = '#d13438'
        delete_style['activebackground'] = '#a72629'
        
        delete_selected_btn = tk.Button(right_section, text="🗑️ Delete", 
                                       command=self.app.delete_selected_shape, **delete_style)
        delete_selected_btn.pack(side=tk.LEFT, padx=3)
        
        # Clear button
        clear_style = btn_style.copy()
        clear_style['bg'] = '#e74856'
        clear_style['activebackground'] = '#c42b1c'
        
        clear_btn = tk.Button(right_section, text="🧹 Clear All", 
                             command=self.app.clear_all_shapes, **clear_style)
        clear_btn.pack(side=tk.LEFT, padx=3)
        
        # Save button
        export_style = btn_style.copy()
        export_style['bg'] = '#107c10'
        export_style['activebackground'] = '#0e6b0e'
        
        export_btn = tk.Button(right_section, text="💾 Save All", 
                              command=self.app.save_all_shapes, **export_style)
        export_btn.pack(side=tk.LEFT, padx=3)
        
    def _create_bbox_controls(self, parent):
        """Create bbox size control inputs"""
        middle_section = tk.Frame(parent, bg="#2d2d2d")
        middle_section.pack(side=tk.LEFT, padx=10, pady=0)
        
        tk.Label(middle_section, text="BBox Size:", bg="#2d2d2d", fg="white", 
                font=('Segoe UI', self.app.base_font_size)).pack(side=tk.LEFT, padx=3)
        
        # Width input
        tk.Label(middle_section, text="Width:", bg="#2d2d2d", fg="#b8b8b8", 
                font=('Segoe UI', self.app.base_font_size)).pack(side=tk.LEFT, padx=(8, 2))
        self.app.bbox_width_var = tk.StringVar(value=str(self.app.bbox_width))
        width_entry = tk.Entry(middle_section, textvariable=self.app.bbox_width_var, width=8, 
                              font=('Segoe UI', self.app.base_font_size), relief=tk.FLAT, 
                              bg="#404040", fg="white", insertbackground="#0078d4", 
                              borderwidth=1, highlightthickness=1,
                              highlightbackground="#505050", highlightcolor="#0078d4")
        width_entry.pack(side=tk.LEFT, padx=2)
        width_entry.bind("<FocusOut>", self.app.validate_bbox_size)
        width_entry.bind("<Return>", self.app.validate_bbox_size)
        
        # Height input
        tk.Label(middle_section, text="Height:", bg="#2d2d2d", fg="#b8b8b8", 
                font=('Segoe UI', self.app.base_font_size)).pack(side=tk.LEFT, padx=(10, 2))
        self.app.bbox_height_var = tk.StringVar(value=str(self.app.bbox_height))
        height_entry = tk.Entry(middle_section, textvariable=self.app.bbox_height_var, width=8, 
                               font=('Segoe UI', self.app.base_font_size), relief=tk.FLAT, 
                               bg="#404040", fg="white", insertbackground="#0078d4", 
                               borderwidth=1, highlightthickness=1,
                               highlightbackground="#505050", highlightcolor="#0078d4")
        height_entry.pack(side=tk.LEFT, padx=2)
        height_entry.bind("<FocusOut>", self.app.validate_bbox_size)
        height_entry.bind("<Return>", self.app.validate_bbox_size)
        
        # Apply button
        apply_style = self._get_button_style()
        apply_style['bg'] = '#8764b8'
        apply_style['activebackground'] = '#744da9'
        apply_size_btn = tk.Button(middle_section, text="✓ Apply Size", 
                                   command=self.app.apply_size_to_selected, **apply_style)
        apply_size_btn.pack(side=tk.LEFT, padx=10)
        
    def _setup_status_bar(self):
        """Setup the status bar at the bottom"""
        status_frame = tk.Frame(self.root, bg="#252525", relief=tk.FLAT, bd=0)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.app.status_label = tk.Label(status_frame, text="Ready | Load an image to start", 
                                         bg="#252525", fg="#aaaaaa", 
                                         font=('Segoe UI', self.app.status_font_size),
                                         anchor='w', padx=12, pady=6)
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
        nav_header = tk.Label(self.app.side_panel, text="📂 Images", bg="#2d2d2d", fg="#ffffff", 
                             font=('Segoe UI', self.app.heading_font_size, 'bold'), pady=15)
        nav_header.pack(side=tk.TOP, fill=tk.X)
        
        # Navigation buttons
        nav_btn_frame = tk.Frame(self.app.side_panel, bg="#2d2d2d")
        nav_btn_frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=5)
        
        nav_btn_style = {
            'bg': '#0078d4',
            'fg': 'white',
            'font': ('Segoe UI', self.app.button_font_size),
            'relief': tk.FLAT,
            'padx': 10,
            'pady': 7,
            'cursor': 'hand2',
            'activebackground': '#106ebe',
            'activeforeground': 'white',
            'borderwidth': 0
        }
        
        self.app.prev_btn = tk.Button(nav_btn_frame, text="◄ Previous", 
                                      command=self.app.prev_image, **nav_btn_style)
        self.app.prev_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.app.next_btn = tk.Button(nav_btn_frame, text="Next ►", 
                                      command=self.app.next_image, **nav_btn_style)
        self.app.next_btn.pack(side=tk.RIGHT, padx=2, expand=True, fill=tk.X)
        
        # Image counter
        self.app.image_counter_label = tk.Label(self.app.side_panel, text="0 / 0", 
                                                bg="#2d2d2d", fg="#b8b8b8", 
                                                font=('Segoe UI', self.app.base_font_size, 'bold'))
        self.app.image_counter_label.pack(side=tk.TOP, pady=8)
        
        # Image list
        list_frame = tk.Frame(self.app.side_panel, bg="#2d2d2d")
        list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=5)
        
        list_scroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL, width=12)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.app.image_listbox = tk.Listbox(list_frame, bg="#404040", fg="white", 
                                            font=('Segoe UI', self.app.base_font_size), 
                                            relief=tk.FLAT, selectbackground="#0078d4", 
                                            selectforeground="white", yscrollcommand=list_scroll.set, 
                                            activestyle='none', borderwidth=0, highlightthickness=0)
        self.app.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.app.image_listbox.yview)
        self.app.image_listbox.bind('<<ListboxSelect>>', self.app.on_image_select)
        
    def _setup_canvas(self, parent):
        """Setup canvas for image display"""
        canvas_frame = tk.Frame(parent, bg="#1e1e1e")
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.app.canvas = tk.Canvas(canvas_frame, bg="#0a0a0a", highlightthickness=0, cursor="crosshair")
        self.app.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Setup scrollbars
        self._setup_scrollbars(canvas_frame)
        
    def _setup_scrollbars(self, parent):
        """Setup canvas scrollbars"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Vertical.TScrollbar", 
                       background="#505050",
                       troughcolor="#1e1e1e",
                       bordercolor="#1e1e1e",
                       arrowcolor="#b8b8b8",
                       darkcolor="#404040",
                       lightcolor="#606060")
        style.configure("Horizontal.TScrollbar",
                       background="#505050",
                       troughcolor="#1e1e1e",
                       bordercolor="#1e1e1e",
                       arrowcolor="#b8b8b8",
                       darkcolor="#404040",
                       lightcolor="#606060")
        
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
            'bg': '#0078d4',
            'fg': 'white',
            'font': ('Segoe UI', self.app.button_font_size, 'normal'),
            'relief': tk.FLAT,
            'padx': 16,
            'pady': 9,
            'cursor': 'hand2',
            'activebackground': '#106ebe',
            'activeforeground': 'white',
            'borderwidth': 0,
            'highlightthickness': 0
        }
