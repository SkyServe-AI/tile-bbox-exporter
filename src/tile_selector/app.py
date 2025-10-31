import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import math

class ImageTileSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("SkyServe Image Tile Selector and Exporter - Beta Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1e1e1e")

        # Variables
        self.images = []  # List of (image_path, PIL.Image)
        self.tiles = []   # List of tile info: {'image_name': str, 'row': int, 'col': int, 'x': int, 'y': int, 'image': PIL.Image, 'selected': bool}
        self.tile_size = 100  # Default tile size
        self.selected_tiles = set()  # Set of indices in self.tiles
        self.zoom_level = 1.0  # Current zoom level
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.current_image_index = 0  # Currently displayed image index
        self.canvas_center_x = 0  # For center-focused zoom
        self.canvas_center_y = 0
        self.is_classification = tk.BooleanVar(value=False)  # Classification mode

        # GUI Elements
        self.setup_gui()

    def setup_gui(self):
        # Modern styled control panel
        control_frame = tk.Frame(self.root, bg="#2d2d2d", relief=tk.FLAT, bd=0)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
        
        # Left section - File operations
        left_section = tk.Frame(control_frame, bg="#2d2d2d")
        left_section.pack(side=tk.LEFT, padx=15, pady=12)
        
        # Upload buttons with modern styling
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
        
        upload_file_btn = tk.Button(left_section, text="📁 Upload Images", command=self.upload_images, **btn_style)
        upload_file_btn.pack(side=tk.LEFT, padx=5)

        upload_folder_btn = tk.Button(left_section, text="📂 Upload Folder", command=self.upload_folder, **btn_style)
        upload_folder_btn.pack(side=tk.LEFT, padx=5)
        
        # Middle section - Tile size
        middle_section = tk.Frame(control_frame, bg="#2d2d2d")
        middle_section.pack(side=tk.LEFT, padx=15, pady=12)
        
        tk.Label(middle_section, text="Tile Size:", bg="#2d2d2d", fg="white", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        self.tile_size_var = tk.StringVar(value=str(self.tile_size))
        tile_size_entry = tk.Entry(middle_section, textvariable=self.tile_size_var, width=10, 
                                   font=('Segoe UI', 10), relief=tk.FLAT, bg="#3c3c3c", fg="white",
                                   insertbackground="white")
        tile_size_entry.pack(side=tk.LEFT, padx=5)
        tile_size_entry.bind("<FocusOut>", self.validate_tile_size)

        apply_btn = tk.Button(middle_section, text="✓ Apply", command=self.apply_tile_size, **btn_style)
        apply_btn.pack(side=tk.LEFT, padx=5)
        
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

        # Right section - Export
        right_section = tk.Frame(control_frame, bg="#2d2d2d")
        right_section.pack(side=tk.RIGHT, padx=15, pady=12)
        
        # Classification checkbox
        classification_check = tk.Checkbutton(right_section, text="Is classification", 
                                             variable=self.is_classification,
                                             bg="#2d2d2d", fg="white", 
                                             selectcolor="#3c3c3c",
                                             activebackground="#2d2d2d",
                                             activeforeground="white",
                                             font=('Segoe UI', 10),
                                             cursor='hand2')
        classification_check.pack(side=tk.LEFT, padx=10)
        
        export_style = btn_style.copy()
        export_style['bg'] = '#0d7d3a'
        export_style['activebackground'] = '#0e9647'
        
        export_btn = tk.Button(right_section, text="💾 Export Selected", command=self.export_tiles, **export_style)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg="#252525", relief=tk.FLAT, bd=0)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(status_frame, text="Ready | No images loaded", 
                                     bg="#252525", fg="#aaaaaa", font=('Segoe UI', 9),
                                     anchor='w', padx=10, pady=5)
        self.status_label.pack(fill=tk.X)

        # Main content area with side panel and canvas
        content_frame = tk.Frame(self.root, bg="#1e1e1e")
        content_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        # Side panel for image navigation
        self.side_panel = tk.Frame(content_frame, bg="#2d2d2d", width=200)
        self.side_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.side_panel.pack_propagate(False)
        
        # Navigation controls in side panel
        nav_header = tk.Label(self.side_panel, text="Images", bg="#2d2d2d", fg="white", 
                             font=('Segoe UI', 11, 'bold'), pady=10)
        nav_header.pack(side=tk.TOP, fill=tk.X)
        
        # Navigation buttons
        nav_btn_frame = tk.Frame(self.side_panel, bg="#2d2d2d")
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
        
        self.prev_btn = tk.Button(nav_btn_frame, text="◄ Prev", command=self.prev_image, **nav_btn_style)
        self.prev_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.next_btn = tk.Button(nav_btn_frame, text="Next ►", command=self.next_image, **nav_btn_style)
        self.next_btn.pack(side=tk.RIGHT, padx=2, expand=True, fill=tk.X)
        
        # Image counter
        self.image_counter_label = tk.Label(self.side_panel, text="0 / 0", bg="#2d2d2d", 
                                           fg="#aaaaaa", font=('Segoe UI', 9))
        self.image_counter_label.pack(side=tk.TOP, pady=5)
        
        # Scrollable list of images
        list_frame = tk.Frame(self.side_panel, bg="#2d2d2d")
        list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        list_scroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.image_listbox = tk.Listbox(list_frame, bg="#3c3c3c", fg="white", 
                                        font=('Segoe UI', 9), relief=tk.FLAT,
                                        selectbackground="#0e639c", selectforeground="white",
                                        yscrollcommand=list_scroll.set, activestyle='none')
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.image_listbox.yview)
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)

        # Canvas frame for scrollbars
        canvas_frame = tk.Frame(content_frame, bg="#1e1e1e")
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Canvas for displaying tiles
        self.canvas = tk.Canvas(canvas_frame, bg="#0a0a0a", highlightthickness=0)
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

        # Bind mouse click on canvas
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Bind mouse wheel for scrolling and zoom (with Ctrl)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_mouse_wheel)
        
        # Bind Shift + mouse wheel for horizontal scrolling
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_mouse_wheel)
        
        # Bind middle mouse button for drag scrolling
        self.canvas.bind("<Button-2>", self.on_drag_start)
        self.canvas.bind("<B2-Motion>", self.on_drag_motion)
        self.canvas.bind("<ButtonRelease-2>", self.on_drag_end)
        
        self.drag_start_x = 0
        self.drag_start_y = 0

    def is_image_file(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        return ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']

    def upload_images(self):
        filetypes = [
            ('Image files', '*.png *.jpg *.jpeg *.bmp *.tiff *.gif'),
            ('All files', '*.*')
        ]
        filenames = filedialog.askopenfilenames(title="Select Images", filetypes=filetypes)
        if filenames:
            self.images = []
            for path in filenames:
                try:
                    img = Image.open(path)
                    self.images.append((path, img))
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load {path}: {e}")
            self.update_status(f"Loaded {len(self.images)} image(s)")
            self.update_image_list()
            self.current_image_index = 0
            self.apply_tile_size()

    def upload_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self.images = []
            for file in os.listdir(folder):
                path = os.path.join(folder, file)
                if os.path.isfile(path) and self.is_image_file(path):
                    try:
                        img = Image.open(path)
                        self.images.append((path, img))
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to load {path}: {e}")
            if not self.images:
                messagebox.showwarning("Warning", "No valid images found in the folder.")
                self.update_status("No images found")
            else:
                self.update_status(f"Loaded {len(self.images)} image(s) from folder")
                self.update_image_list()
                self.current_image_index = 0
                self.apply_tile_size()

    def validate_tile_size(self, event=None):
        try:
            size = int(self.tile_size_var.get())
            if size <= 0:
                raise ValueError
            self.tile_size = size
        except ValueError:
            messagebox.showerror("Error", "Tile size must be a positive integer.")
            self.tile_size_var.set(str(self.tile_size))

    def apply_tile_size(self):
        if not self.images:
            return
        self.validate_tile_size()
        
        # Only process current image
        if self.current_image_index >= len(self.images):
            self.current_image_index = 0
        
        path, img = self.images[self.current_image_index]
        w, h = img.size
        
        # Check validation
        if self.tile_size >= w or self.tile_size >= h:
            messagebox.showerror("Error", f"Tile size {self.tile_size} is >= image size ({w}x{h})")
            return
        
        # Generate tiles and padded image for current image only
        self.tiles = []
        self.selected_tiles = set()
        
        image_name = os.path.splitext(os.path.basename(path))[0]
        num_cols = math.ceil(w / self.tile_size)
        num_rows = math.ceil(h / self.tile_size)
        
        # Create padded image with black background
        padded_w = num_cols * self.tile_size
        padded_h = num_rows * self.tile_size
        padded_img = Image.new('RGB', (padded_w, padded_h), (0, 0, 0))
        padded_img.paste(img, (0, 0))
        
        self.current_padded_image = {
            'image_name': image_name,
            'padded_img': padded_img,
            'original_size': (w, h),
            'num_cols': num_cols,
            'num_rows': num_rows
        }
        
        for r in range(num_rows):
            for c in range(num_cols):
                x = c * self.tile_size
                y = r * self.tile_size
                tile_img = padded_img.crop((x, y, x + self.tile_size, y + self.tile_size))
                self.tiles.append({
                    'image_name': image_name,
                    'row': r,
                    'col': c,
                    'tile_img': tile_img,
                    'selected': False
                })
        self.display_grid()

    def display_grid(self):
        self.canvas.delete("all")
        if not hasattr(self, 'current_padded_image') or not self.current_padded_image:
            return
        
        img_data = self.current_padded_image
        padded_img = img_data['padded_img']
        num_cols = img_data['num_cols']
        num_rows = img_data['num_rows']
        
        # Apply zoom to image
        zoomed_width = int(padded_img.width * self.zoom_level)
        zoomed_height = int(padded_img.height * self.zoom_level)
        zoomed_img = padded_img.resize((zoomed_width, zoomed_height), Image.LANCZOS)
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Center the image on canvas
        x_offset = max(10, (canvas_width - zoomed_width) // 2)
        y_offset = max(10, (canvas_height - zoomed_height) // 2)
        
        # Display the full padded image with zoom
        tk_img = ImageTk.PhotoImage(zoomed_img)
        img_id = self.canvas.create_image(x_offset, y_offset, anchor='nw', image=tk_img)
        # Keep reference to prevent garbage collection
        self.canvas.tk_img_refs = [tk_img]
        
        # Draw grid lines over the image (scaled)
        scaled_tile_size = int(self.tile_size * self.zoom_level)
        
        # Vertical lines
        for c in range(num_cols + 1):
            x = x_offset + c * scaled_tile_size
            self.canvas.create_line(x, y_offset, x, y_offset + zoomed_height, fill="#555555", width=1)
        
        # Horizontal lines
        for r in range(num_rows + 1):
            y = y_offset + r * scaled_tile_size
            self.canvas.create_line(x_offset, y, x_offset + zoomed_width, y, fill="#555555", width=1)
        
        # Create invisible rectangles for tile selection
        tile_index = 0
        for r in range(num_rows):
            for c in range(num_cols):
                x1 = x_offset + c * scaled_tile_size
                y1 = y_offset + r * scaled_tile_size
                x2 = x1 + scaled_tile_size
                y2 = y1 + scaled_tile_size
                
                tile = self.tiles[tile_index]
                # Selection rectangle
                if tile['selected']:
                    rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline="#ffcc00", width=2, tags=f"rect_{tile_index}")
                else:
                    rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline="", width=0, tags=f"rect_{tile_index}")
                
                # Invisible clickable area
                click_rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline="", fill="", tags=f"tile_{tile_index}")
                
                tile['rect_id'] = rect_id
                tile['click_rect'] = click_rect
                tile_index += 1
        
        # Update scroll region
        scroll_width = max(zoomed_width + 2 * x_offset, canvas_width)
        scroll_height = max(zoomed_height + 2 * y_offset, canvas_height)
        self.canvas.config(scrollregion=(0, 0, scroll_width, scroll_height))
        
        # Center the view
        self.canvas.xview_moveto((x_offset - 10) / scroll_width if scroll_width > canvas_width else 0)
        self.canvas.yview_moveto((y_offset - 10) / scroll_height if scroll_height > canvas_height else 0)
        
        self.update_status(f"Image {self.current_image_index + 1}/{len(self.images)} | {len(self.tiles)} tiles | Zoom: {int(self.zoom_level * 100)}% | {len(self.selected_tiles)} selected")

    def zoom_in(self):
        """Zoom in by 20%"""
        if self.zoom_level < self.max_zoom:
            self.zoom_level = min(self.zoom_level * 1.2, self.max_zoom)
            self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
            self.display_grid()
    
    def zoom_out(self):
        """Zoom out by 20%"""
        if self.zoom_level > self.min_zoom:
            self.zoom_level = max(self.zoom_level / 1.2, self.min_zoom)
            self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
            self.display_grid()
    
    def zoom_reset(self):
        """Reset zoom to 100%"""
        self.zoom_level = 1.0
        self.zoom_label.config(text="100%")
        self.display_grid()
    
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
        """Handle mouse wheel scrolling (touchpad two-finger scroll)"""
        # Vertical scroll
        if event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        else:
            self.canvas.yview_scroll(1, "units")
    
    def on_drag_start(self, event):
        """Start drag scrolling with middle mouse button"""
        self.canvas.scan_mark(event.x, event.y)
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def on_drag_motion(self, event):
        """Handle drag scrolling motion"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)
    
    def on_drag_end(self, event):
        """End drag scrolling"""
        pass
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
    
    def update_image_list(self):
        """Update the image list in side panel"""
        self.image_listbox.delete(0, tk.END)
        for i, (path, img) in enumerate(self.images):
            filename = os.path.basename(path)
            self.image_listbox.insert(tk.END, f"{i+1}. {filename}")
        
        if self.images:
            self.image_listbox.selection_set(self.current_image_index)
            self.image_counter_label.config(text=f"{self.current_image_index + 1} / {len(self.images)}")
        else:
            self.image_counter_label.config(text="0 / 0")
    
    def on_image_select(self, event):
        """Handle image selection from listbox"""
        selection = self.image_listbox.curselection()
        if selection:
            self.current_image_index = selection[0]
            self.image_counter_label.config(text=f"{self.current_image_index + 1} / {len(self.images)}")
            self.apply_tile_size()
    
    def prev_image(self):
        """Show previous image"""
        if not self.images:
            return
        self.current_image_index = (self.current_image_index - 1) % len(self.images)
        self.image_listbox.selection_clear(0, tk.END)
        self.image_listbox.selection_set(self.current_image_index)
        self.image_listbox.see(self.current_image_index)
        self.image_counter_label.config(text=f"{self.current_image_index + 1} / {len(self.images)}")
        self.apply_tile_size()
    
    def next_image(self):
        """Show next image"""
        if not self.images:
            return
        self.current_image_index = (self.current_image_index + 1) % len(self.images)
        self.image_listbox.selection_clear(0, tk.END)
        self.image_listbox.selection_set(self.current_image_index)
        self.image_listbox.see(self.current_image_index)
        self.image_counter_label.config(text=f"{self.current_image_index + 1} / {len(self.images)}")
        self.apply_tile_size()
    
    def on_canvas_click(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        items = self.canvas.find_overlapping(x, y, x, y)
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("tile_"):
                    idx = int(tag.split("_")[1])
                    self.tiles[idx]['selected'] = not self.tiles[idx]['selected']
                    if self.tiles[idx]['selected']:
                        self.selected_tiles.add(idx)
                    else:
                        self.selected_tiles.discard(idx)
                    # Update the selection rectangle
                    outline_color = "#ffcc00" if self.tiles[idx]['selected'] else ""
                    outline_width = 2 if self.tiles[idx]['selected'] else 0
                    self.canvas.itemconfig(self.tiles[idx]['rect_id'], outline=outline_color, width=outline_width)
                    self.update_status(f"Displaying {len(self.tiles)} tiles | Zoom: {int(self.zoom_level * 100)}% | {len(self.selected_tiles)} selected")
                    break

    def export_tiles(self):
        if not self.tiles:
            messagebox.showwarning("Warning", "No tiles to export.")
            return
        
        # Check if classification mode is enabled
        if self.is_classification.get():
            self.export_classification()
        else:
            # Normal export mode - only selected tiles
            if not self.selected_tiles:
                messagebox.showwarning("Warning", "No tiles selected.")
                return
            folder = filedialog.askdirectory(title="Select Export Folder")
            if not folder:
                return
            exported = 0
            for i in self.selected_tiles:
                tile = self.tiles[i]
                filename = f"{tile['image_name']}_tile_{tile['row']}_{tile['col']}.png"
                path = os.path.join(folder, filename)
                try:
                    tile['tile_img'].save(path)
                    exported += 1
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save {filename}: {e}")
            messagebox.showinfo("Export Complete", f"Exported {exported} tiles to {folder}.")
            self.update_status(f"Exported {exported} tiles successfully")
    
    def export_classification(self):
        """Export tiles in classification mode: selected to folder, unselected to no_<folder>"""
        if not self.selected_tiles and len(self.selected_tiles) == len(self.tiles):
            messagebox.showwarning("Warning", "Please select some tiles for classification.")
            return
        
        # Ask user to select folder for selected tiles
        folder = filedialog.askdirectory(title="Select Folder for Selected Tiles (Positive Class)")
        if not folder:
            return
        
        # Get folder name and parent directory
        folder_name = os.path.basename(folder)
        parent_dir = os.path.dirname(folder)
        
        # Create no_<folder_name> directory for unselected tiles
        no_folder = os.path.join(parent_dir, f"no_{folder_name}")
        if not os.path.exists(no_folder):
            try:
                os.makedirs(no_folder)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create directory {no_folder}: {e}")
                return
        
        exported_selected = 0
        exported_unselected = 0
        
        # Export all tiles
        for i, tile in enumerate(self.tiles):
            filename = f"{tile['image_name']}_tile_{tile['row']}_{tile['col']}.png"
            
            if i in self.selected_tiles:
                # Save selected tiles to the chosen folder
                path = os.path.join(folder, filename)
                try:
                    tile['tile_img'].save(path)
                    exported_selected += 1
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save {filename}: {e}")
            else:
                # Save unselected tiles to no_<folder>
                path = os.path.join(no_folder, filename)
                try:
                    tile['tile_img'].save(path)
                    exported_unselected += 1
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save {filename}: {e}")
        
        messagebox.showinfo("Classification Export Complete", 
                          f"Exported {exported_selected} selected tiles to:\n{folder}\n\n"
                          f"Exported {exported_unselected} unselected tiles to:\n{no_folder}")
        self.update_status(f"Classification export: {exported_selected} selected, {exported_unselected} unselected")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageTileSelector(root)
    root.mainloop()
