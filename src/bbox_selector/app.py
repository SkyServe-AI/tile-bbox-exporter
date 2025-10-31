import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
import os
import json

class BBoxSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("SkyServe BBox Selector - Beta Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1e1e1e")

        # Variables
        self.image = None  # Current PIL Image
        self.image_path = None
        self.display_image = None  # Image displayed on canvas
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.bbox_width = 64  # Default bbox width in pixels
        self.bbox_height = 64  # Default bbox height in pixels
        self.bboxes = []  # List of bboxes: {'x': int, 'y': int, 'width': int, 'height': int, 'rect_id': int}
        self.bbox_counter = 0  # Counter for bbox naming
        self.selected_bbox = None  # Currently selected bbox for editing
        self.hovered_bbox = None  # Bbox currently under mouse
        self.dragging = False  # Whether currently dragging
        self.drag_handle = None  # Which handle/edge is being dragged
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Polygon mode variables
        self.custom_select_mode = tk.BooleanVar(value=False)
        self.polygon_points = []  # List of (x, y) points in image coordinates
        self.polygon_counter = 0
        self.polygons = []  # List of completed polygons
        self.selected_polygon = None  # Currently selected polygon

        # GUI Elements
        self.setup_gui()

    def setup_gui(self):
        # Modern styled control panel
        control_frame = tk.Frame(self.root, bg="#2d2d2d", relief=tk.FLAT, bd=0)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
        
        # Left section - File operations
        left_section = tk.Frame(control_frame, bg="#2d2d2d")
        left_section.pack(side=tk.LEFT, padx=15, pady=12)
        
        # Button styling
        btn_style = {
            'bg': '#0e639c',
            'fg': 'white',
            'font': ('Segoe UI', 10),
            'relief': tk.FLAT,
            'padx': 15,
            'pady': 8,
            'cursor': 'hand2',
            'activebackground': '#1177bb',
            'activeforeground': 'white'
        }
        
        upload_btn = tk.Button(left_section, text="📁 Load Image", command=self.load_image, **btn_style)
        upload_btn.pack(side=tk.LEFT, padx=5)
        
        # Custom select checkbox
        custom_check = tk.Checkbutton(left_section, text="Custom Select", 
                                     variable=self.custom_select_mode,
                                     command=self.toggle_custom_select,
                                     bg="#2d2d2d", fg="white", 
                                     selectcolor="#3c3c3c",
                                     activebackground="#2d2d2d",
                                     activeforeground="white",
                                     font=('Segoe UI', 10),
                                     cursor='hand2')
        custom_check.pack(side=tk.LEFT, padx=10)
        
        # Middle section - BBox size controls
        middle_section = tk.Frame(control_frame, bg="#2d2d2d")
        middle_section.pack(side=tk.LEFT, padx=15, pady=12)
        
        tk.Label(middle_section, text="BBox Width:", bg="#2d2d2d", fg="white", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        self.bbox_width_var = tk.StringVar(value=str(self.bbox_width))
        width_entry = tk.Entry(middle_section, textvariable=self.bbox_width_var, width=8, 
                              font=('Segoe UI', 10), relief=tk.FLAT, bg="#3c3c3c", fg="white",
                              insertbackground="white")
        width_entry.pack(side=tk.LEFT, padx=5)
        width_entry.bind("<FocusOut>", self.validate_bbox_size)
        width_entry.bind("<Return>", self.validate_bbox_size)
        
        tk.Label(middle_section, text="Height:", bg="#2d2d2d", fg="white", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(15, 5))
        self.bbox_height_var = tk.StringVar(value=str(self.bbox_height))
        height_entry = tk.Entry(middle_section, textvariable=self.bbox_height_var, width=8, 
                               font=('Segoe UI', 10), relief=tk.FLAT, bg="#3c3c3c", fg="white",
                               insertbackground="white")
        height_entry.pack(side=tk.LEFT, padx=5)
        height_entry.bind("<FocusOut>", self.validate_bbox_size)
        height_entry.bind("<Return>", self.validate_bbox_size)
        
        # Apply size button for selected bbox
        apply_size_btn = tk.Button(middle_section, text="✓ Apply to Selected", command=self.apply_size_to_selected, **btn_style)
        apply_size_btn.pack(side=tk.LEFT, padx=5)
        
        # Zoom section
        zoom_section = tk.Frame(control_frame, bg="#2d2d2d")
        zoom_section.pack(side=tk.LEFT, padx=15, pady=12)
        
        tk.Label(zoom_section, text="Zoom:", bg="#2d2d2d", fg="white", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        
        zoom_btn_style = btn_style.copy()
        zoom_btn_style['padx'] = 10
        zoom_btn_style['pady'] = 6
        
        zoom_out_btn = tk.Button(zoom_section, text="➖", command=self.zoom_out, **zoom_btn_style)
        zoom_out_btn.pack(side=tk.LEFT, padx=2)
        
        self.zoom_label = tk.Label(zoom_section, text="100%", bg="#2d2d2d", fg="white", 
                                   font=('Segoe UI', 10, 'bold'), width=6)
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        
        zoom_in_btn = tk.Button(zoom_section, text="➕", command=self.zoom_in, **zoom_btn_style)
        zoom_in_btn.pack(side=tk.LEFT, padx=2)
        
        zoom_reset_btn = tk.Button(zoom_section, text="⟲", command=self.zoom_reset, **zoom_btn_style)
        zoom_reset_btn.pack(side=tk.LEFT, padx=2)

        # Right section - Actions
        right_section = tk.Frame(control_frame, bg="#2d2d2d")
        right_section.pack(side=tk.RIGHT, padx=15, pady=12)
        
        clear_style = btn_style.copy()
        clear_style['bg'] = '#c44e4e'
        clear_style['activebackground'] = '#d65555'
        
        delete_selected_btn = tk.Button(right_section, text="❌ Delete Selected", command=self.delete_selected_shape, **clear_style)
        delete_selected_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(right_section, text="🗑️ Clear All", command=self.clear_all_shapes, **clear_style)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        export_style = btn_style.copy()
        export_style['bg'] = '#0d7d3a'
        export_style['activebackground'] = '#0e9647'
        
        export_btn = tk.Button(right_section, text="💾 Save All Shapes", command=self.save_all_shapes, **export_style)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg="#252525", relief=tk.FLAT, bd=0)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(status_frame, text="Ready | Load an image to start", 
                                     bg="#252525", fg="#aaaaaa", font=('Segoe UI', 9),
                                     anchor='w', padx=10, pady=5)
        self.status_label.pack(fill=tk.X)

        # Canvas frame for scrollbars
        canvas_frame = tk.Frame(self.root, bg="#1e1e1e")
        canvas_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        # Canvas for displaying image
        self.canvas = tk.Canvas(canvas_frame, bg="#0a0a0a", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Modern styled scrollbars
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
        
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview, style="Vertical.TScrollbar")
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview, style="Horizontal.TScrollbar")
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-3>", self.on_right_click)  # Right click to remove bbox
        
        # Bind keyboard events to root window
        self.root.bind("<Delete>", self.on_delete_key)
        self.root.bind("<BackSpace>", self.on_delete_key)
        self.root.bind("<Return>", self.on_enter_key)
        self.root.bind("<Escape>", self.on_escape_key)
        
        # Give canvas focus for keyboard events
        self.canvas.focus_set()
        
        # Bind mouse wheel for scrolling and zoom
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_mouse_wheel)
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_mouse_wheel)
        
        # Bind middle mouse button for drag scrolling
        self.canvas.bind("<Button-2>", self.on_pan_start)
        self.canvas.bind("<B2-Motion>", self.on_pan_motion)
        self.canvas.bind("<ButtonRelease-2>", self.on_pan_end)

    def load_image(self):
        filetypes = [
            ('Image files', '*.png *.jpg *.jpeg *.bmp *.tiff *.gif'),
            ('All files', '*.*')
        ]
        filepath = filedialog.askopenfilename(title="Select Image", filetypes=filetypes)
        if filepath:
            try:
                self.image = Image.open(filepath)
                self.image_path = filepath
                self.bboxes = []
                self.bbox_counter = 0
                self.zoom_level = 1.0
                self.zoom_label.config(text="100%")
                self.display_image_on_canvas()
                self.update_status(f"Loaded: {os.path.basename(filepath)} | Size: {self.image.size[0]}x{self.image.size[1]}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")

    def validate_bbox_size(self, event=None):
        try:
            width = int(self.bbox_width_var.get())
            height = int(self.bbox_height_var.get())
            if width <= 0 or height <= 0:
                raise ValueError
            self.bbox_width = width
            self.bbox_height = height
        except ValueError:
            messagebox.showerror("Error", "BBox dimensions must be positive integers.")
            self.bbox_width_var.set(str(self.bbox_width))
            self.bbox_height_var.set(str(self.bbox_height))

    def display_image_on_canvas(self):
        if not self.image:
            return
        
        self.canvas.delete("all")
        
        # Apply zoom
        zoomed_width = int(self.image.width * self.zoom_level)
        zoomed_height = int(self.image.height * self.zoom_level)
        zoomed_img = self.image.resize((zoomed_width, zoomed_height), Image.LANCZOS)
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Center the image
        x_offset = max(10, (canvas_width - zoomed_width) // 2)
        y_offset = max(10, (canvas_height - zoomed_height) // 2)
        
        # Store offset for bbox calculations
        self.image_offset_x = x_offset
        self.image_offset_y = y_offset
        
        # Display image
        self.display_image = ImageTk.PhotoImage(zoomed_img)
        self.canvas.create_image(x_offset, y_offset, anchor='nw', image=self.display_image)
        
        # Redraw all bboxes
        self.redraw_bboxes()
        
        # Update scroll region
        scroll_width = max(zoomed_width + 2 * x_offset, canvas_width)
        scroll_height = max(zoomed_height + 2 * y_offset, canvas_height)
        self.canvas.config(scrollregion=(0, 0, scroll_width, scroll_height))
        
        # Center the view
        self.canvas.xview_moveto((x_offset - 10) / scroll_width if scroll_width > canvas_width else 0)
        self.canvas.yview_moveto((y_offset - 10) / scroll_height if scroll_height > canvas_height else 0)

    def redraw_bboxes(self):
        """Redraw all bboxes and polygons with current zoom level"""
        # Draw polygon points and lines if in polygon mode
        if self.custom_select_mode.get() and self.polygon_points:
            # Draw lines connecting points
            for i in range(len(self.polygon_points)):
                x1 = self.image_offset_x + int(self.polygon_points[i][0] * self.zoom_level)
                y1 = self.image_offset_y + int(self.polygon_points[i][1] * self.zoom_level)
                
                # Draw point
                self.canvas.create_oval(x1-4, y1-4, x1+4, y1+4, fill="#ff00ff", outline="white", width=2)
                
                # Draw line to next point
                if i < len(self.polygon_points) - 1:
                    x2 = self.image_offset_x + int(self.polygon_points[i+1][0] * self.zoom_level)
                    y2 = self.image_offset_y + int(self.polygon_points[i+1][1] * self.zoom_level)
                    self.canvas.create_line(x1, y1, x2, y2, fill="#ff00ff", width=2)
                
                # Draw closing line if we have at least 3 points
                if i == len(self.polygon_points) - 1 and len(self.polygon_points) >= 3:
                    x2 = self.image_offset_x + int(self.polygon_points[0][0] * self.zoom_level)
                    y2 = self.image_offset_y + int(self.polygon_points[0][1] * self.zoom_level)
                    self.canvas.create_line(x1, y1, x2, y2, fill="#ff00ff", width=2, dash=(5, 5))
        
        # Draw completed polygons
        for polygon in self.polygons:
            points = polygon['points']
            if len(points) >= 3:
                # Convert to canvas coordinates
                canvas_points = []
                for px, py in points:
                    cx = self.image_offset_x + int(px * self.zoom_level)
                    cy = self.image_offset_y + int(py * self.zoom_level)
                    canvas_points.extend([cx, cy])
                
                # Determine color based on selection
                is_selected = self.selected_polygon and self.selected_polygon['id'] == polygon['id']
                outline_color = "#ffcc00" if is_selected else "#00ff00"
                text_color = "#ffcc00" if is_selected else "#00ff00"
                line_width = 3 if is_selected else 2
                
                # Draw polygon outline
                self.canvas.create_polygon(canvas_points, outline=outline_color, fill="", width=line_width, tags=f"polygon_{polygon['id']}")
                
                # Draw label
                if canvas_points:
                    label_text = f"P#{polygon['id']}" + (" [SELECTED]" if is_selected else "")
                    self.canvas.create_text(canvas_points[0] + 5, canvas_points[1] + 5, 
                                          text=label_text, fill=text_color, 
                                          font=('Segoe UI', 9, 'bold'), anchor='nw', tags=f"polygon_{polygon['id']}")
        
        for bbox in self.bboxes:
            # Calculate bbox position in zoomed coordinates
            x1 = self.image_offset_x + int(bbox['x'] * self.zoom_level)
            y1 = self.image_offset_y + int(bbox['y'] * self.zoom_level)
            x2 = x1 + int(bbox['width'] * self.zoom_level)
            y2 = y1 + int(bbox['height'] * self.zoom_level)
            
            # Determine color based on selection and hover
            is_selected = self.selected_bbox and self.selected_bbox['id'] == bbox['id']
            is_hovered = self.hovered_bbox and self.hovered_bbox['id'] == bbox['id']
            
            if is_selected:
                outline_color = "#ffcc00"
                text_color = "#ffcc00"
                line_width = 3
            elif is_hovered:
                outline_color = "#00ccff"
                text_color = "#00ccff"
                line_width = 2
            else:
                outline_color = "#00ff00"
                text_color = "#00ff00"
                line_width = 2
            
            # Draw rectangle with fill for better hover detection
            rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline=outline_color, width=line_width, 
                                                   fill="", tags=f"bbox_{bbox['id']}")
            
            # Draw label
            label_text = f"#{bbox['id']}"
            if is_selected:
                label_text += " [SELECTED]"
            text_id = self.canvas.create_text(x1 + 5, y1 + 5, text=label_text, fill=text_color, 
                                             font=('Segoe UI', 9, 'bold'), anchor='nw', tags=f"bbox_{bbox['id']}")
            
            bbox['rect_id'] = rect_id
            bbox['text_id'] = text_id
            
            # Draw resize handles for selected bbox
            if is_selected:
                handle_size = 10  # Increased size for easier clicking
                # Corner handles
                self.canvas.create_rectangle(x1-handle_size//2, y1-handle_size//2, x1+handle_size//2, y1+handle_size//2, 
                                            fill="#ffcc00", outline="white", width=2, tags=f"handle_nw_{bbox['id']}")
                self.canvas.create_rectangle(x2-handle_size//2, y1-handle_size//2, x2+handle_size//2, y1+handle_size//2, 
                                            fill="#ffcc00", outline="white", width=2, tags=f"handle_ne_{bbox['id']}")
                self.canvas.create_rectangle(x1-handle_size//2, y2-handle_size//2, x1+handle_size//2, y2+handle_size//2, 
                                            fill="#ffcc00", outline="white", width=2, tags=f"handle_sw_{bbox['id']}")
                self.canvas.create_rectangle(x2-handle_size//2, y2-handle_size//2, x2+handle_size//2, y2+handle_size//2, 
                                            fill="#ffcc00", outline="white", width=2, tags=f"handle_se_{bbox['id']}")
                # Edge handles
                mid_x = (x1 + x2) // 2
                mid_y = (y1 + y2) // 2
                self.canvas.create_rectangle(mid_x-handle_size//2, y1-handle_size//2, mid_x+handle_size//2, y1+handle_size//2, 
                                            fill="#ffcc00", outline="white", width=2, tags=f"handle_n_{bbox['id']}")
                self.canvas.create_rectangle(mid_x-handle_size//2, y2-handle_size//2, mid_x+handle_size//2, y2+handle_size//2, 
                                            fill="#ffcc00", outline="white", width=2, tags=f"handle_s_{bbox['id']}")
                self.canvas.create_rectangle(x1-handle_size//2, mid_y-handle_size//2, x1+handle_size//2, mid_y+handle_size//2, 
                                            fill="#ffcc00", outline="white", width=2, tags=f"handle_w_{bbox['id']}")
                self.canvas.create_rectangle(x2-handle_size//2, mid_y-handle_size//2, x2+handle_size//2, mid_y+handle_size//2, 
                                            fill="#ffcc00", outline="white", width=2, tags=f"handle_e_{bbox['id']}")

    def toggle_custom_select(self):
        """Toggle between bbox mode and polygon mode"""
        if self.custom_select_mode.get():
            # Entering polygon mode
            self.polygon_points = []
            self.update_status("Polygon mode active | Click to add points | Right-click or press Enter to complete")
            self.canvas.config(cursor="crosshair")
        else:
            # Exiting polygon mode
            if self.polygon_points:
                result = messagebox.askyesno("Incomplete Polygon", "Discard current polygon points?")
                if not result:
                    self.custom_select_mode.set(True)
                    return
            self.polygon_points = []
            self.update_status("BBox mode active")
            self.canvas.config(cursor="crosshair")
            self.display_image_on_canvas()

    def on_canvas_click(self, event):
        """Select bbox, start dragging handle, create bbox, or add polygon point"""
        if not self.image:
            messagebox.showwarning("Warning", "Please load an image first.")
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Convert to image coordinates
        img_x = int((canvas_x - self.image_offset_x) / self.zoom_level)
        img_y = int((canvas_y - self.image_offset_y) / self.zoom_level)
        
        # Polygon mode - add point
        if self.custom_select_mode.get():
            # Clamp to image boundaries
            img_x = max(0, min(img_x, self.image.width))
            img_y = max(0, min(img_y, self.image.height))
            
            self.polygon_points.append((img_x, img_y))
            self.display_image_on_canvas()
            self.update_status(f"Polygon: {len(self.polygon_points)} points | Right-click or Enter to complete")
            return
        
        # BBox mode
        # First priority: Check if clicking on resize handle
        items = self.canvas.find_overlapping(canvas_x, canvas_y, canvas_x, canvas_y)
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("handle_"):
                    # Start dragging handle
                    parts = tag.split("_")
                    self.drag_handle = parts[1]  # nw, ne, sw, se, n, s, e, w
                    self.dragging = True
                    self.drag_start_x = canvas_x
                    self.drag_start_y = canvas_y
                    self.update_status(f"Resizing BBox #{self.selected_bbox['id']}...")
                    return
                elif tag.startswith("polygon_"):
                    # Select polygon
                    polygon_id = int(tag.split("_")[1])
                    for polygon in self.polygons:
                        if polygon['id'] == polygon_id:
                            self.selected_polygon = polygon
                            self.selected_bbox = None  # Deselect bbox
                            self.hovered_bbox = None  # Clear hover
                            self.display_image_on_canvas()
                            self.update_status(f"Polygon #{polygon_id} selected | Press Delete/Backspace to remove")
                            # Give canvas focus for keyboard events
                            self.canvas.focus_set()
                            return
        
        # Second priority: Check if clicking inside any bbox area
        for bbox in self.bboxes:
            if (bbox['x'] <= img_x <= bbox['x'] + bbox['width'] and
                bbox['y'] <= img_y <= bbox['y'] + bbox['height']):
                # Select this bbox
                self.selected_bbox = bbox
                self.selected_polygon = None  # Deselect polygon
                # Update input fields with selected bbox size
                self.bbox_width_var.set(str(bbox['width']))
                self.bbox_height_var.set(str(bbox['height']))
                self.display_image_on_canvas()
                self.update_status(f"BBox #{bbox['id']} selected | Size: {bbox['width']}x{bbox['height']}")
                return
        
        # No bbox clicked, create new one
        self.validate_bbox_size()
        
        # Calculate bbox centered on click point
        bbox_x = img_x - self.bbox_width // 2
        bbox_y = img_y - self.bbox_height // 2
        
        # Clamp to image boundaries
        bbox_x = max(0, min(bbox_x, self.image.width - self.bbox_width))
        bbox_y = max(0, min(bbox_y, self.image.height - self.bbox_height))
        
        # Create bbox
        self.bbox_counter += 1
        bbox = {
            'id': self.bbox_counter,
            'x': bbox_x,
            'y': bbox_y,
            'width': self.bbox_width,
            'height': self.bbox_height
        }
        self.bboxes.append(bbox)
        self.selected_bbox = bbox  # Auto-select newly created bbox
        
        # Redraw to show new bbox
        self.display_image_on_canvas()
        self.update_status(f"BBox #{self.bbox_counter} created | Total: {len(self.bboxes)} bboxes")
    
    def on_mouse_move(self, event):
        """Handle mouse hover to highlight bboxes"""
        if not self.image or self.dragging:
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Convert to image coordinates
        img_x = int((canvas_x - self.image_offset_x) / self.zoom_level)
        img_y = int((canvas_y - self.image_offset_y) / self.zoom_level)
        
        # Find bbox under cursor by checking if point is inside bbox area
        found_bbox = None
        for bbox in self.bboxes:
            if (bbox['x'] <= img_x <= bbox['x'] + bbox['width'] and
                bbox['y'] <= img_y <= bbox['y'] + bbox['height']):
                found_bbox = bbox
                break
        
        # Update hover state if changed
        if found_bbox != self.hovered_bbox:
            self.hovered_bbox = found_bbox
            self.display_image_on_canvas()
    
    def on_mouse_drag(self, event):
        """Handle dragging resize handles"""
        if not self.dragging or not self.selected_bbox or not self.drag_handle:
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Calculate delta in image coordinates
        delta_x = int((canvas_x - self.drag_start_x) / self.zoom_level)
        delta_y = int((canvas_y - self.drag_start_y) / self.zoom_level)
        
        # Skip if no movement
        if delta_x == 0 and delta_y == 0:
            return
        
        bbox = self.selected_bbox
        old_x = bbox['x']
        old_y = bbox['y']
        old_width = bbox['width']
        old_height = bbox['height']
        
        # Apply resize based on which handle is being dragged
        if self.drag_handle == 'nw':
            bbox['x'] += delta_x
            bbox['y'] += delta_y
            bbox['width'] -= delta_x
            bbox['height'] -= delta_y
        elif self.drag_handle == 'ne':
            bbox['y'] += delta_y
            bbox['width'] += delta_x
            bbox['height'] -= delta_y
        elif self.drag_handle == 'sw':
            bbox['x'] += delta_x
            bbox['width'] -= delta_x
            bbox['height'] += delta_y
        elif self.drag_handle == 'se':
            bbox['width'] += delta_x
            bbox['height'] += delta_y
        elif self.drag_handle == 'n':
            bbox['y'] += delta_y
            bbox['height'] -= delta_y
        elif self.drag_handle == 's':
            bbox['height'] += delta_y
        elif self.drag_handle == 'w':
            bbox['x'] += delta_x
            bbox['width'] -= delta_x
        elif self.drag_handle == 'e':
            bbox['width'] += delta_x
        
        # Enforce minimum size
        if bbox['width'] < 10:
            bbox['width'] = 10
            bbox['x'] = old_x
        if bbox['height'] < 10:
            bbox['height'] = 10
            bbox['y'] = old_y
        
        # Clamp to image boundaries
        if bbox['x'] < 0:
            bbox['width'] += bbox['x']
            bbox['x'] = 0
        if bbox['y'] < 0:
            bbox['height'] += bbox['y']
            bbox['y'] = 0
        if bbox['x'] + bbox['width'] > self.image.width:
            bbox['width'] = self.image.width - bbox['x']
        if bbox['y'] + bbox['height'] > self.image.height:
            bbox['height'] = self.image.height - bbox['y']
        
        # Update input fields
        self.bbox_width_var.set(str(bbox['width']))
        self.bbox_height_var.set(str(bbox['height']))
        
        # Update drag start position
        self.drag_start_x = canvas_x
        self.drag_start_y = canvas_y
        
        # Redraw
        self.display_image_on_canvas()
    
    def on_mouse_release(self, event):
        """Handle mouse button release"""
        if self.dragging:
            self.dragging = False
            self.drag_handle = None
            self.update_status(f"BBox #{self.selected_bbox['id']} resized to {self.selected_bbox['width']}x{self.selected_bbox['height']}")
    
    def on_delete_key(self, event):
        """Delete selected bbox or polygon with Delete/Backspace key"""
        self.delete_selected_shape()
    
    def on_enter_key(self, event):
        """Complete polygon with Enter key"""
        if self.custom_select_mode.get() and len(self.polygon_points) >= 3:
            self.complete_polygon()
            return
    
    def on_escape_key(self, event):
        """Cancel current polygon"""
        if self.custom_select_mode.get() and self.polygon_points:
            self.polygon_points = []
            self.display_image_on_canvas()
            self.update_status("Polygon cancelled | Click to add points")
            return
    
    def complete_polygon(self):
        """Complete and save the current polygon"""
        if len(self.polygon_points) < 3:
            messagebox.showwarning("Invalid Polygon", "A polygon must have at least 3 points.")
            return
        
        # Save polygon
        self.polygon_counter += 1
        polygon = {
            'id': self.polygon_counter,
            'points': self.polygon_points.copy()
        }
        self.polygons.append(polygon)
        
        # Export polygon as PNG
        self.export_polygon(polygon)
        
        # Clear current points
        self.polygon_points = []
        self.display_image_on_canvas()
        self.update_status(f"Polygon #{self.polygon_counter} completed and exported | Total: {len(self.polygons)} polygons")
    
    def export_polygon(self, polygon):
        """Export a single polygon region as PNG"""
        if not self.image:
            return
        
        points = polygon['points']
        if len(points) < 3:
            return
        
        # Find bounding box of polygon
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Add padding
        padding = 5
        min_x = max(0, min_x - padding)
        min_y = max(0, min_y - padding)
        max_x = min(self.image.width, max_x + padding)
        max_y = min(self.image.height, max_y + padding)
        
        width = max_x - min_x
        height = max_y - min_y
        
        # Create mask
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        
        # Adjust polygon points relative to bounding box
        adjusted_points = [(x - min_x, y - min_y) for x, y in points]
        mask_draw.polygon(adjusted_points, fill=255)
        
        # Crop image to bounding box
        cropped = self.image.crop((min_x, min_y, max_x, max_y))
        
        # Create output image with transparency
        output = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        output.paste(cropped, (0, 0))
        output.putalpha(mask)
        
        # Ask for save location - schedule after current event
        self.root.after(100, lambda: self._save_polygon_file(output, polygon['id']))
    
    def _save_polygon_file(self, output, polygon_id):
        """Helper to save polygon file with dialog"""
        image_name = os.path.splitext(os.path.basename(self.image_path))[0]
        default_filename = f"{image_name}_polygon_{polygon_id}.png"
        
        filepath = filedialog.asksaveasfilename(
            title="Save Polygon Region",
            defaultextension=".png",
            initialfile=default_filename,
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                output.save(filepath)
                messagebox.showinfo("Export Successful", f"Polygon saved to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to save polygon: {e}")

    def on_right_click(self, event):
        """Complete polygon or remove bbox at clicked location"""
        if not self.image:
            return
        
        # If in polygon mode, complete the polygon
        if self.custom_select_mode.get():
            if len(self.polygon_points) >= 3:
                self.complete_polygon()
            return
        
        # BBox mode - remove bbox
        if not self.bboxes:
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Find clicked bbox
        items = self.canvas.find_overlapping(canvas_x, canvas_y, canvas_x, canvas_y)
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("bbox_"):
                    bbox_id = int(tag.split("_")[1])
                    # Remove bbox from list
                    self.bboxes = [b for b in self.bboxes if b['id'] != bbox_id]
                    self.display_image_on_canvas()
                    self.update_status(f"BBox #{bbox_id} removed | Total: {len(self.bboxes)} bboxes")
                    return

    def delete_selected_shape(self):
        """Delete the currently selected bbox or polygon"""
        if self.selected_polygon:
            polygon_id = self.selected_polygon['id']
            self.polygons = [p for p in self.polygons if p['id'] != polygon_id]
            self.selected_polygon = None
            self.display_image_on_canvas()
            self.update_status(f"Polygon #{polygon_id} deleted | Total: {len(self.polygons)} polygons")
        elif self.selected_bbox:
            bbox_id = self.selected_bbox['id']
            self.bboxes = [b for b in self.bboxes if b['id'] != bbox_id]
            self.selected_bbox = None
            self.display_image_on_canvas()
            self.update_status(f"BBox #{bbox_id} deleted | Total: {len(self.bboxes)} bboxes")
        else:
            messagebox.showwarning("Warning", "No shape selected. Click on a bbox or polygon to select it first.")
    
    def apply_size_to_selected(self):
        """Apply current width/height values to selected bbox"""
        if not self.selected_bbox:
            messagebox.showwarning("Warning", "No bbox selected. Click on a bbox to select it first.")
            return
        
        self.validate_bbox_size()
        
        # Update selected bbox size
        old_width = self.selected_bbox['width']
        old_height = self.selected_bbox['height']
        
        self.selected_bbox['width'] = self.bbox_width
        self.selected_bbox['height'] = self.bbox_height
        
        # Re-center bbox to maintain center position
        center_x = self.selected_bbox['x'] + old_width // 2
        center_y = self.selected_bbox['y'] + old_height // 2
        
        self.selected_bbox['x'] = center_x - self.bbox_width // 2
        self.selected_bbox['y'] = center_y - self.bbox_height // 2
        
        # Clamp to image boundaries
        self.selected_bbox['x'] = max(0, min(self.selected_bbox['x'], self.image.width - self.bbox_width))
        self.selected_bbox['y'] = max(0, min(self.selected_bbox['y'], self.image.height - self.bbox_height))
        
        self.display_image_on_canvas()
        self.update_status(f"BBox #{self.selected_bbox['id']} resized to {self.bbox_width}x{self.bbox_height}")

    def clear_all_shapes(self):
        """Clear all bboxes and polygons"""
        total = len(self.bboxes) + len(self.polygons)
        if total == 0:
            return
        
        result = messagebox.askyesno("Confirm", f"Clear all {len(self.bboxes)} bboxes and {len(self.polygons)} polygons?")
        if result:
            self.bboxes = []
            self.bbox_counter = 0
            self.selected_bbox = None
            self.polygons = []
            self.polygon_counter = 0
            self.selected_polygon = None
            self.display_image_on_canvas()
            self.update_status("All shapes cleared")

    def export_bboxes(self):
        """Export all bbox regions as separate images"""
        if not self.image:
            messagebox.showwarning("Warning", "No image loaded.")
            return
        
        if not self.bboxes:
            messagebox.showwarning("Warning", "No bboxes to export.")
            return
        
        folder = filedialog.askdirectory(title="Select Export Folder")
        if not folder:
            return
        
        image_name = os.path.splitext(os.path.basename(self.image_path))[0]
        exported = 0
        
        for bbox in self.bboxes:
            # Crop bbox region from original image
            x1 = bbox['x']
            y1 = bbox['y']
            x2 = x1 + bbox['width']
            y2 = y1 + bbox['height']
            
            cropped = self.image.crop((x1, y1, x2, y2))
            
            # Save with proper naming
            filename = f"{image_name}_bbox_{bbox['id']}.png"
            filepath = os.path.join(folder, filename)
            
            try:
                cropped.save(filepath)
                exported += 1
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save {filename}: {e}")
        
        messagebox.showinfo("Export Complete", f"Exported {exported} bboxes to:\n{folder}")
        self.update_status(f"Exported {exported} bboxes successfully")

    def save_all_shapes(self):
        """Save all shapes (bboxes and polygons) as images and JSON"""
        if not self.image:
            messagebox.showwarning("Warning", "No image loaded.")
            return
        
        total_shapes = len(self.bboxes) + len(self.polygons)
        if total_shapes == 0:
            messagebox.showwarning("Warning", "No shapes to save.")
            return
        
        folder = filedialog.askdirectory(title="Select Save Folder")
        if not folder:
            return
        
        image_name = os.path.splitext(os.path.basename(self.image_path))[0]
        
        # Prepare JSON data
        json_data = {
            "image": os.path.basename(self.image_path),
            "image_width": self.image.width,
            "image_height": self.image.height,
            "bboxes": [],
            "polygons": []
        }
        
        # Export bboxes
        for bbox in self.bboxes:
            # Save bbox data to JSON
            json_data["bboxes"].append({
                "id": bbox['id'],
                "x": bbox['x'],
                "y": bbox['y'],
                "width": bbox['width'],
                "height": bbox['height']
            })
            
            # Crop and save bbox image
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            cropped = self.image.crop((x, y, x + w, y + h))
            filename = f"{image_name}_bbox_{bbox['id']}.png"
            filepath = os.path.join(folder, filename)
            cropped.save(filepath)
        
        # Export polygons
        for polygon in self.polygons:
            points = polygon['points']
            
            # Save polygon data to JSON
            json_data["polygons"].append({
                "id": polygon['id'],
                "points": points
            })
            
            # Find bounding box of polygon
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            # Add padding
            padding = 5
            min_x = max(0, min_x - padding)
            min_y = max(0, min_y - padding)
            max_x = min(self.image.width, max_x + padding)
            max_y = min(self.image.height, max_y + padding)
            
            width = max_x - min_x
            height = max_y - min_y
            
            # Create mask
            mask = Image.new('L', (width, height), 0)
            mask_draw = ImageDraw.Draw(mask)
            adjusted_points = [(x - min_x, y - min_y) for x, y in points]
            mask_draw.polygon(adjusted_points, fill=255)
            
            # Crop and apply mask
            cropped = self.image.crop((min_x, min_y, max_x, max_y))
            output = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            output.paste(cropped, (0, 0))
            output.putalpha(mask)
            
            # Save polygon image
            filename = f"{image_name}_polygon_{polygon['id']}.png"
            filepath = os.path.join(folder, filename)
            output.save(filepath)
        
        # Save JSON file
        json_filename = f"{image_name}_annotations.json"
        json_filepath = os.path.join(folder, json_filename)
        with open(json_filepath, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        messagebox.showinfo("Save Complete", 
                          f"Saved {len(self.bboxes)} bboxes and {len(self.polygons)} polygons to:\n{folder}\n\nJSON file: {json_filename}")
        self.update_status(f"Saved {total_shapes} shapes to {folder}")

    def zoom_in(self):
        """Zoom in by 20%"""
        if self.zoom_level < self.max_zoom:
            self.zoom_level = min(self.zoom_level * 1.2, self.max_zoom)
            self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
            self.display_image_on_canvas()
    
    def zoom_out(self):
        """Zoom out by 20%"""
        if self.zoom_level > self.min_zoom:
            self.zoom_level = max(self.zoom_level / 1.2, self.min_zoom)
            self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
            self.display_image_on_canvas()
    
    def zoom_reset(self):
        """Reset zoom to 100%"""
        self.zoom_level = 1.0
        self.zoom_label.config(text="100%")
        self.display_image_on_canvas()
    
    def on_ctrl_mouse_wheel(self, event):
        """Handle Ctrl + mouse wheel for zooming"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def on_shift_mouse_wheel(self, event):
        """Handle Shift + mouse wheel for horizontal scrolling"""
        if event.delta > 0:
            self.canvas.xview_scroll(-1, "units")
        else:
            self.canvas.xview_scroll(1, "units")
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        else:
            self.canvas.yview_scroll(1, "units")
    
    def on_pan_start(self, event):
        """Start drag scrolling with middle mouse button"""
        self.canvas.scan_mark(event.x, event.y)
    
    def on_pan_motion(self, event):
        """Handle drag scrolling motion"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)
    
    def on_pan_end(self, event):
        """End drag scrolling"""
        pass
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)

if __name__ == "__main__":
    root = tk.Tk()
    app = BBoxSelector(root)
    root.mainloop()
