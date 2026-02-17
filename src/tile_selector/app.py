"""
Tile Selector - Main Application
Modular architecture with separated concerns
"""
import tkinter as tk
import cv2
import numpy as np

from .ui_components import UIComponents
from .image_handler import ImageHandler
from .tile_manager import TileManager
from .canvas_handler import CanvasHandler
from .lulc_classifier import LULCClassifier


class ImageTileSelector:
    """Main application class for Tile Selector"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("SkyServe Image Tile Selector and Exporter - Beta Edition")
        
        # Get screen dimensions for responsive sizing
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Set window size based on screen (85% of screen for 13"+ displays)
        window_width = min(int(screen_width * 0.85), 1600)
        window_height = min(int(screen_height * 0.85), 1000)
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.configure(bg="#1e1e1e")
        
        # Calculate responsive font sizes
        self.base_font_size = 10 if screen_width >= 1366 else 9
        self.button_font_size = self.base_font_size
        self.status_font_size = self.base_font_size - 1

        # Initialize variables
        self._init_variables()
        
        # Initialize handlers
        self._init_handlers()
        
        # Setup GUI
        self.ui.setup_gui()
        
        # Bind events
        self._bind_events()
        
        # Enable drag and drop after canvas is created
        self.image_handler.enable_drag_drop()
    
    def _init_variables(self):
        """Initialize all application variables"""
        # Image management
        self.images = []  # List of (image_path, PIL.Image)
        self.current_image_index = 0
        
        # Tile management
        self.tiles = []  # List of tile info
        self.tile_size = 100
        self.selected_tiles = set()
        self.current_padded_image = None
        self.display_image_tk = None
        
        # Per-image tile selections storage
        self.image_tile_selections = {}  # {image_path: set of selected tile indices}
        
        # LULC Classification
        self.tile_classifications = []  # List of category names for each tile
        self.lulc_classifier = None
        self.legend_frame = None
        self.category_counts = {}
        self.selected_tiles_for_category = set()  # Tiles selected for batch category assignment
        
        # LULC Category value mapping (category name -> integer value for mask export)
        self.category_values = {cat: i for i, cat in enumerate(LULCClassifier.CATEGORIES)}
        self.category_value_vars = {}  # Will hold StringVar for each category (set by UI)
        
        # Hand tool for transparent overlay
        self.hand_tool_active = False
        self.hover_tile_index = None
        
        # Overlay visibility toggle
        self.overlay_visible = True
        
        # Preprocessing toggle
        self.preprocess_enabled = None  # Will be set by UI (BooleanVar)
        self.preprocessed_image = None  # Store preprocessed version
        
        # Zoom settings
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.canvas_center_x = 0
        self.canvas_center_y = 0
        
        # Classification mode
        self.is_classification = None  # Will be set by UI
        
        # Drag state
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.secondary_button_dragging = False
        
        # Tile selection drag state
        self.is_selecting = False
        self.selection_mode = None  # 'add' or 'remove'
        
        # UI elements (will be set by UIComponents)
        self.canvas = None
        self.zoom_label = None
        self.status_label = None
        self.side_panel = None
        self.image_listbox = None
        self.image_counter_label = None
        self.prev_btn = None
        self.next_btn = None
        self.tile_size_var = None
    
    def _init_handlers(self):
        """Initialize all handler modules"""
        self.ui = UIComponents(self.root, self)
        self.image_handler = ImageHandler(self)
        self.tile_manager = TileManager(self)
        self.canvas_handler = CanvasHandler(self)
    
    def _bind_events(self):
        """Bind canvas events"""
        self.canvas.bind("<Button-1>", self.canvas_handler.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.canvas_handler.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_handler.on_canvas_release)
        self.canvas.bind("<Button-3>", self.canvas_handler.on_right_click)  # Right-click for category menu
        self.canvas.bind("<Control-Button-1>", self.canvas_handler.on_right_click)  # Control+click for mac trackpads
        self.canvas.bind("<Motion>", self.canvas_handler.on_mouse_motion)  # Track mouse for hand tool
        self.canvas.bind("<MouseWheel>", self.canvas_handler.on_mouse_wheel)
        self.canvas.bind("<Control-MouseWheel>", self.canvas_handler.on_ctrl_mouse_wheel)
        self.canvas.bind("<Shift-MouseWheel>", self.canvas_handler.on_shift_mouse_wheel)
        self.canvas.bind("<Button-2>", self.canvas_handler.on_drag_start)
        self.canvas.bind("<B2-Motion>", self.canvas_handler.on_drag_motion)
        self.canvas.bind("<ButtonRelease-2>", self.canvas_handler.on_secondary_release)
    
    # Delegate methods to handlers
    def upload_images(self):
        """Upload images"""
        self.image_handler.upload_images()
    
    def upload_folder(self):
        """Upload folder"""
        self.image_handler.upload_folder()
    
    def prev_image(self):
        """Navigate to previous image"""
        self.image_handler.prev_image()
    
    def next_image(self):
        """Navigate to next image"""
        self.image_handler.next_image()
    
    def on_image_select(self, event):
        """Handle image selection from listbox"""
        self.image_handler.on_image_select(event)
    
    def update_image_list(self):
        """Update image list display"""
        self.image_handler.update_image_list()
    
    def validate_tile_size(self, event=None):
        """Validate tile size"""
        self.tile_manager.validate_tile_size(event)
    
    def apply_tile_size(self):
        """Apply tile size"""
        self.tile_manager.apply_tile_size()
    
    def export_tiles_wrapper(self):
        """Export tiles based on mode"""
        # Check if LULC classification is active
        if hasattr(self, 'tile_classifications') and self.tile_classifications:
            # Show export options menu
            menu = tk.Menu(self.root, tearoff=0, bg="#2d2d2d", fg="white",
                          activebackground="#0e639c", activeforeground="white")
            menu.add_command(label="📁 Export Tiles by Category", command=self.export_lulc_tiles)
            menu.add_command(label="🖼️ Save Image with Mask", command=self.save_mask_image)
            menu.add_command(label="🎭 Export Mask Only", command=self.save_mask_only)
            menu.add_separator()
            menu.add_command(label="📊 Accuracy Matrix", command=self.compute_accuracy_matrix)
            
            # Position menu near the export button
            try:
                menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
            finally:
                menu.grab_release()
        elif self.is_classification.get():
            self.tile_manager.export_classification()
        else:
            self.tile_manager.export_tiles()
    
    def display_grid(self):
        """Display grid on canvas"""
        self.canvas_handler.display_grid()
    
    def zoom_in(self):
        """Zoom in"""
        self.canvas_handler.zoom_in()
    
    def zoom_out(self):
        """Zoom out"""
        self.canvas_handler.zoom_out()
    
    def zoom_reset(self):
        """Reset zoom"""
        self.canvas_handler.zoom_reset()
    
    def update_status(self, message):
        """Update status bar message"""
        if self.status_label:
            self.status_label.config(text=message)
    
    def toggle_hand_tool(self):
        """Toggle hand tool mode for transparent overlay on hover"""
        self.hand_tool_active = not self.hand_tool_active
        if self.hand_tool_active:
            self.canvas.config(cursor="hand2")
            self.update_status("Hand Tool Active - Hover over tiles to see through overlay")
        else:
            self.canvas.config(cursor="")
            self.hover_tile_index = None
            self.display_grid()
            self.update_status("Hand Tool Deactivated")
    
    def toggle_overlay(self):
        """Toggle LULC overlay visibility"""
        self.overlay_visible = not self.overlay_visible
        
        # Update button appearance
        if hasattr(self, 'overlay_toggle_btn'):
            style_name = "Sky.OverlayVisible.TButton" if self.overlay_visible else "Sky.OverlayHidden.TButton"
            self.overlay_toggle_btn.configure(style=style_name)
            visibility_msg = "LULC Overlay Visible" if self.overlay_visible else "LULC Overlay Hidden"
            self.update_status(visibility_msg)
        
        # Refresh display
        self.display_grid()
    
    def toggle_preprocessing(self):
        """Toggle preprocessing and update display"""
        if self.preprocess_enabled.get():
            # Preprocessing enabled - apply it
            self.update_status("Applying preprocessing...")
            self.root.update()
            self._apply_preprocessing()
            self.update_status("Preprocessing enabled - Displaying processed image")
        else:
            # Preprocessing disabled - use original
            self.preprocessed_image = None
            self.update_status("Preprocessing disabled - Displaying original image")
        
        # Regenerate tiles with current image (original or preprocessed)
        self.apply_tile_size()
    
    def classify_tiles_lulc(self):
        """Classify tiles using LULC classifier"""
        if not self.tiles:
            import tkinter.messagebox as messagebox
            messagebox.showwarning("Warning", "No tiles to classify. Please load an image and apply tile size first.")
            return
        
        # Initialize classifier if not already done
        if not self.lulc_classifier:
            self.lulc_classifier = LULCClassifier(
                apply_color_correction=True,
                filter_clouds=True,
                cloud_threshold=0.7
            )
        
        # Show progress
        self.update_status("Classifying tiles...")
        self.root.update()
        
        # Save preprocessed image if color correction is enabled
        if self.lulc_classifier.apply_color_correction and self.images:
            self._save_preprocessed_image()
        
        # Classify tiles
        def progress_callback(current, total):
            self.update_status(f"Classifying tiles... {current}/{total}")
            self.root.update()
        
        self.tile_classifications = self.lulc_classifier.classify_tiles(self.tiles, progress_callback)
        
        # Update category counts
        from collections import Counter
        counts = Counter(self.tile_classifications)
        
        for category in LULCClassifier.CATEGORIES:
            count = counts.get(category, 0)
            if category in self.category_counts:
                self.category_counts[category].config(text=f"{category}: {count}")
        
        # Show legend
        if self.legend_frame and not self.legend_frame.winfo_ismapped():
            self.legend_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Refresh display
        self.display_grid()
        
        self.update_status(f"Classification complete! {len(self.tiles)} tiles classified into {len(counts)} categories")
    
    def export_lulc_tiles(self):
        """Export tiles to category directories"""
        if not self.tile_classifications:
            import tkinter.messagebox as messagebox
            messagebox.showwarning("Warning", "Please classify tiles first using 'Classify LULC' button.")
            return
        
        from tkinter import filedialog, messagebox
        import os
        
        # Select base output folder
        base_folder = filedialog.askdirectory(title="Select Base Output Folder for LULC Categories")
        if not base_folder:
            return
        
        # Create category directories
        for category in LULCClassifier.CATEGORIES:
            category_path = os.path.join(base_folder, category)
            os.makedirs(category_path, exist_ok=True)
        
        # Export tiles
        exported_counts = {cat: 0 for cat in LULCClassifier.CATEGORIES}
        cloud_count = 0
        
        for i, (tile_info, category) in enumerate(zip(self.tiles, self.tile_classifications)):
            if category == 'Cloud':
                cloud_count += 1
                continue
            
            if category in LULCClassifier.CATEGORIES:
                # Save tile to category folder
                category_path = os.path.join(base_folder, category)
                filename = f"{tile_info['image_name']}_tile_r{tile_info['row']:03d}_c{tile_info['col']:03d}.png"
                filepath = os.path.join(category_path, filename)
                
                try:
                    tile_info['tile_img'].save(filepath)
                    exported_counts[category] += 1
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save {filename}: {e}")
        
        # Show summary
        summary = "LULC Export Summary:\n\n"
        for category in LULCClassifier.CATEGORIES:
            count = exported_counts[category]
            if count > 0:
                summary += f"{category}: {count} tiles\n"
        
        if cloud_count > 0:
            summary += f"\nCloud filtered: {cloud_count} tiles"
        
        summary += f"\n\nTotal exported: {sum(exported_counts.values())} tiles"
        summary += f"\nOutput folder: {base_folder}"
        
        messagebox.showinfo("Export Complete", summary)
        self.update_status(f"Exported {sum(exported_counts.values())} tiles to category folders")
    
    def update_category_value(self, category, value_var):
        """Update category integer value from UI entry"""
        try:
            val = int(value_var.get())
            self.category_values[category] = val
        except ValueError:
            pass
    
    def save_mask_only(self):
        """Export a single-channel mask image where each pixel has the integer value of its tile's category"""
        if not self.tile_classifications:
            import tkinter.messagebox as messagebox
            messagebox.showwarning("Warning", "Please classify tiles first using 'Classify LULC' button.")
            return
        
        if not self.current_padded_image:
            import tkinter.messagebox as messagebox
            messagebox.showwarning("Warning", "No image loaded.")
            return
        
        from tkinter import filedialog, messagebox
        from PIL import Image
        import os
        
        # Sync category values from UI entries
        for category, var in self.category_value_vars.items():
            self.update_category_value(category, var)
        
        # Get current image name for default filename
        current_image_path = self.images[self.current_image_index][0]
        image_name = os.path.splitext(os.path.basename(current_image_path))[0]
        
        # Ask user where to save
        save_path = filedialog.asksaveasfilename(
            title="Export LULC Mask Only",
            defaultextension=".tif",
            initialfile=f"{image_name}_lulc_mask_only.tif",
            filetypes=[("TIFF files", "*.tif"), ("PNG files", "*.png"), ("All files", "*.*")]
        )
        if not save_path:
            return
        
        self.update_status("Exporting mask...")
        self.root.update()
        
        width = self.current_padded_image.width
        height = self.current_padded_image.height
        tile_size = self.tile_size
        
        # Default value for unclassified / cloud pixels
        default_value = 255
        
        # Create single-channel mask with numpy for speed
        mask_array = np.full((height, width), default_value, dtype=np.uint8)
        
        for i, tile_info in enumerate(self.tiles):
            if i >= len(self.tile_classifications):
                break
            
            category = self.tile_classifications[i]
            if not category or category == 'Cloud':
                continue
            
            val = self.category_values.get(category, default_value)
            
            x1 = tile_info['x']
            y1 = tile_info['y']
            x2 = min(x1 + tile_size, width)
            y2 = min(y1 + tile_size, height)
            
            mask_array[y1:y2, x1:x2] = val
        
        # Save as grayscale image
        mask_image = Image.fromarray(mask_array, mode='L')
        
        try:
            mask_image.save(save_path)
            
            # Build value mapping summary
            summary = "LULC Mask Value Mapping:\n\n"
            for cat in LULCClassifier.CATEGORIES:
                summary += f"{cat}: {self.category_values.get(cat, '?')}\n"
            summary += f"\nUnclassified/Cloud: {default_value}"
            summary += f"\n\nSaved to: {save_path}"
            
            self.update_status(f"Saved mask to: {save_path}")
            messagebox.showinfo("Mask Export Complete", summary)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save mask: {e}")
    
    def compute_accuracy_matrix(self):
        """Compare a predicted mask with a ground truth mask and show confusion matrix"""
        from tkinter import filedialog, messagebox
        from PIL import Image
        
        # Ask user to select predicted mask
        pred_path = filedialog.askopenfilename(
            title="Select Predicted Mask (TIF/PNG)",
            filetypes=[("TIFF files", "*.tif"), ("PNG files", "*.png"), ("All files", "*.*")]
        )
        if not pred_path:
            return
        
        # Ask user to select ground truth mask
        gt_path = filedialog.askopenfilename(
            title="Select Ground Truth Mask (TIF/PNG)",
            filetypes=[("TIFF files", "*.tif"), ("PNG files", "*.png"), ("All files", "*.*")]
        )
        if not gt_path:
            return
        
        self.update_status("Loading masks...")
        self.root.update()
        
        try:
            pred_img = np.array(Image.open(pred_path).convert('L'))
            gt_img = np.array(Image.open(gt_path).convert('L'))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load masks: {e}")
            return
        
        if pred_img.shape != gt_img.shape:
            messagebox.showerror("Error",
                f"Mask dimensions do not match!\n"
                f"Predicted: {pred_img.shape[1]}x{pred_img.shape[0]}\n"
                f"Ground Truth: {gt_img.shape[1]}x{gt_img.shape[0]}")
            return
        
        # Find all unique values in both masks
        all_values = sorted(set(np.unique(pred_img)) | set(np.unique(gt_img)))
        
        if not all_values:
            messagebox.showwarning("Warning", "No pixel values found in the masks.")
            return
        
        # Show mapping dialog so user can define what each value represents
        self._show_value_mapping_dialog(all_values, pred_img, gt_img)
    
    def _show_value_mapping_dialog(self, all_values, pred_img, gt_img):
        """Show a dialog where user maps each pixel value to a class/category name"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Define Value-to-Class Mapping")
        dialog.geometry("480x500")
        dialog.configure(bg="#1e1e1e")
        dialog.resizable(True, True)
        dialog.grab_set()
        
        # Header
        tk.Label(dialog, text="Assign a class name to each mask value",
                bg="#1e1e1e", fg="#cccccc", font=('Segoe UI', 11, 'bold'),
                pady=8).pack(side=tk.TOP, fill=tk.X, padx=10)
        
        tk.Label(dialog, text="Values found in the masks are listed below.\n"
                 "Enter a class/category name for each value you want to include.\n"
                 "Leave blank or type 'ignore' to skip a value.",
                bg="#1e1e1e", fg="#888888", font=('Segoe UI', 9),
                justify='left', anchor='w').pack(side=tk.TOP, fill=tk.X, padx=15, pady=(0, 8))
        
        # Scrollable mapping area
        map_frame = tk.Frame(dialog, bg="#1e1e1e")
        map_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        map_canvas = tk.Canvas(map_frame, bg="#1e1e1e", highlightthickness=0)
        map_scroll = tk.Scrollbar(map_frame, orient=tk.VERTICAL, command=map_canvas.yview)
        map_inner = tk.Frame(map_canvas, bg="#1e1e1e")
        
        map_inner.bind("<Configure>", lambda e: map_canvas.configure(scrollregion=map_canvas.bbox("all")))
        cw = map_canvas.create_window((0, 0), window=map_inner, anchor="nw")
        map_canvas.configure(yscrollcommand=map_scroll.set)
        map_canvas.bind("<Configure>", lambda e: map_canvas.itemconfig(cw, width=e.width))
        
        def _mw(event):
            map_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        map_canvas.bind("<MouseWheel>", _mw)
        map_inner.bind("<MouseWheel>", _mw)
        
        map_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        map_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Build reverse mapping from current legend values as defaults
        current_val_to_cat = {}
        for cat, val in self.category_values.items():
            current_val_to_cat[val] = cat
        
        # Table header
        hdr = tk.Frame(map_inner, bg="#333333")
        hdr.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))
        tk.Label(hdr, text="Pixel Value", bg="#333333", fg="#aaaaaa",
                font=('Segoe UI', 9, 'bold'), width=12).pack(side=tk.LEFT, padx=5)
        tk.Label(hdr, text="Class / Category Name", bg="#333333", fg="#aaaaaa",
                font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        name_vars = {}
        for val in all_values:
            row = tk.Frame(map_inner, bg="#1e1e1e")
            row.pack(side=tk.TOP, fill=tk.X, pady=2, padx=5)
            row.bind("<MouseWheel>", _mw)
            
            # Pixel value label
            tk.Label(row, text=str(val), bg="#1e1e1e", fg="#00ff00",
                    font=('Segoe UI', 10, 'bold'), width=12, anchor='center').pack(side=tk.LEFT, padx=5)
            
            # Pre-fill with known category name if available
            default_name = current_val_to_cat.get(val, "")
            if val == 255:
                default_name = "ignore"
            
            name_var = tk.StringVar(value=default_name)
            entry = tk.Entry(row, textvariable=name_var, font=('Segoe UI', 10),
                           bg="#3c3c3c", fg="white", insertbackground="white",
                           relief=tk.FLAT)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            entry.bind("<MouseWheel>", _mw)
            
            name_vars[val] = name_var
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg="#1e1e1e")
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        def on_compute():
            # Build value_to_cat from user input
            value_to_cat = {}
            known_values = []
            for val in all_values:
                name = name_vars[val].get().strip()
                if name and name.lower() != 'ignore':
                    value_to_cat[val] = name
                    known_values.append(val)
            
            if len(known_values) < 2:
                from tkinter import messagebox
                messagebox.showwarning("Warning",
                    "Please assign class names to at least 2 values to compute the matrix.",
                    parent=dialog)
                return
            
            dialog.destroy()
            self._compute_and_show_matrix(pred_img, gt_img, known_values, value_to_cat)
        
        tk.Button(btn_frame, text="Compute Accuracy Matrix", command=on_compute,
                 bg="#0d7d3a", fg="white", font=('Segoe UI', 10, 'bold'),
                 relief=tk.FLAT, padx=20, pady=6, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg="#555555", fg="white", font=('Segoe UI', 10),
                 relief=tk.FLAT, padx=20, pady=6, cursor='hand2').pack(side=tk.RIGHT, padx=5)
    
    def _compute_and_show_matrix(self, pred_img, gt_img, known_values, value_to_cat):
        """Compute confusion matrix and show results after user defines mapping"""
        from collections import OrderedDict
        
        self.update_status("Computing accuracy matrix...")
        self.root.update()
        
        n = len(known_values)
        
        # Build confusion matrix
        confusion = np.zeros((n, n), dtype=np.int64)
        
        for i, gt_val in enumerate(known_values):
            gt_mask = (gt_img == gt_val)
            for j, pred_val in enumerate(known_values):
                confusion[i][j] = np.sum(pred_img[gt_mask] == pred_val)
        
        # Compute metrics
        total_pixels = np.sum(confusion)
        correct_pixels = np.trace(confusion)
        overall_accuracy = (correct_pixels / total_pixels * 100) if total_pixels > 0 else 0
        
        per_class = OrderedDict()
        for i, val in enumerate(known_values):
            cat_name = value_to_cat.get(val, f"Value_{val}")
            tp = confusion[i][i]
            row_sum = np.sum(confusion[i, :])
            col_sum = np.sum(confusion[:, i])
            
            recall = (tp / row_sum * 100) if row_sum > 0 else 0
            precision = (tp / col_sum * 100) if col_sum > 0 else 0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
            
            per_class[cat_name] = {
                'value': val, 'tp': tp, 'gt_total': row_sum, 'pred_total': col_sum,
                'recall': recall, 'precision': precision, 'f1': f1
            }
        
        self._show_accuracy_window(confusion, known_values, value_to_cat, per_class, overall_accuracy, pred_img, gt_img)
        self.update_status(f"Accuracy matrix computed | Overall accuracy: {overall_accuracy:.2f}%")
    
    def _colorize_mask(self, mask_array, known_values, value_to_cat, preview_max=400):
        """Convert a grayscale mask to a colorized RGB image for preview"""
        from PIL import Image
        
        h, w = mask_array.shape
        
        # Generate distinct colors for each class
        color_map = {}
        # Use LULC colors if category name matches, otherwise generate colors
        palette = [
            (46, 139, 87), (220, 20, 60), (30, 144, 255), (255, 165, 0),
            (148, 103, 189), (255, 215, 0), (0, 206, 209), (255, 105, 180),
            (124, 252, 0), (210, 105, 30), (70, 130, 180), (244, 164, 96)
        ]
        for idx, val in enumerate(known_values):
            cat_name = value_to_cat.get(val, "")
            hex_color = LULCClassifier.CATEGORY_COLORS.get(cat_name, None)
            if hex_color:
                r = int(hex_color[1:3], 16)
                g = int(hex_color[3:5], 16)
                b = int(hex_color[5:7], 16)
                color_map[val] = (r, g, b)
            else:
                color_map[val] = palette[idx % len(palette)]
        
        # Build RGB array
        rgb = np.full((h, w, 3), 40, dtype=np.uint8)  # dark gray background
        for val in known_values:
            mask = (mask_array == val)
            rgb[mask] = color_map[val]
        
        # Resize for preview
        img = Image.fromarray(rgb, mode='RGB')
        scale = min(preview_max / w, preview_max / h, 1.0)
        if scale < 1.0:
            new_w = max(int(w * scale), 1)
            new_h = max(int(h * scale), 1)
            img = img.resize((new_w, new_h), Image.NEAREST)
        
        return img, color_map
    
    def _show_accuracy_window(self, confusion, known_values, value_to_cat, per_class, overall_accuracy, pred_img=None, gt_img=None):
        """Display accuracy matrix results in a new window with mask previews"""
        from PIL import ImageTk
        
        win = tk.Toplevel(self.root)
        win.title("LULC Accuracy Matrix")
        win.geometry("900x700")
        win.configure(bg="#1e1e1e")
        win.resizable(True, True)
        
        # Keep references to PhotoImages so they don't get garbage collected
        win._photo_refs = []
        
        # Header
        header = tk.Label(win, text=f"Overall Accuracy: {overall_accuracy:.2f}%",
                         bg="#1e1e1e", fg="#00ff00", font=('Segoe UI', 14, 'bold'), pady=10)
        header.pack(side=tk.TOP, fill=tk.X)
        
        # Close button at bottom (pack first so it stays visible)
        close_btn = tk.Button(win, text="Close", command=win.destroy,
                             bg="#0e639c", fg="white", font=('Segoe UI', 10),
                             relief=tk.FLAT, padx=20, pady=5, cursor='hand2')
        close_btn.pack(side=tk.BOTTOM, pady=10)
        
        # Main scrollable area for all content
        main_canvas = tk.Canvas(win, bg="#1e1e1e", highlightthickness=0)
        main_scroll = tk.Scrollbar(win, orient=tk.VERTICAL, command=main_canvas.yview)
        main_inner = tk.Frame(main_canvas, bg="#1e1e1e")
        
        main_inner.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        cw = main_canvas.create_window((0, 0), window=main_inner, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scroll.set)
        main_canvas.bind("<Configure>", lambda e: main_canvas.itemconfig(cw, width=e.width))
        
        def _mw(event):
            main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        main_canvas.bind("<MouseWheel>", _mw)
        main_inner.bind("<MouseWheel>", _mw)
        
        main_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # === MASK PREVIEW SECTION ===
        if pred_img is not None and gt_img is not None:
            preview_section = tk.Frame(main_inner, bg="#1e1e1e")
            preview_section.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
            preview_section.bind("<MouseWheel>", _mw)
            
            tk.Label(preview_section, text="Mask Preview", bg="#1e1e1e", fg="#cccccc",
                    font=('Segoe UI', 10, 'bold'), anchor='w').pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
            
            # Container for side-by-side masks + legend
            preview_row = tk.Frame(preview_section, bg="#1e1e1e")
            preview_row.pack(side=tk.TOP, fill=tk.X)
            preview_row.bind("<MouseWheel>", _mw)
            
            # Predicted mask preview
            pred_color_img, color_map = self._colorize_mask(pred_img, known_values, value_to_cat, preview_max=300)
            pred_photo = ImageTk.PhotoImage(pred_color_img)
            win._photo_refs.append(pred_photo)
            
            pred_frame = tk.Frame(preview_row, bg="#1e1e1e")
            pred_frame.pack(side=tk.LEFT, padx=(0, 10))
            pred_frame.bind("<MouseWheel>", _mw)
            tk.Label(pred_frame, text="Predicted Mask", bg="#1e1e1e", fg="#aaaaaa",
                    font=('Segoe UI', 9, 'bold')).pack(side=tk.TOP)
            pred_lbl = tk.Label(pred_frame, image=pred_photo, bg="#1e1e1e", relief=tk.GROOVE, bd=2)
            pred_lbl.pack(side=tk.TOP, pady=3)
            pred_lbl.bind("<MouseWheel>", _mw)
            
            # Ground truth mask preview
            gt_color_img, _ = self._colorize_mask(gt_img, known_values, value_to_cat, preview_max=300)
            gt_photo = ImageTk.PhotoImage(gt_color_img)
            win._photo_refs.append(gt_photo)
            
            gt_frame = tk.Frame(preview_row, bg="#1e1e1e")
            gt_frame.pack(side=tk.LEFT, padx=(0, 10))
            gt_frame.bind("<MouseWheel>", _mw)
            tk.Label(gt_frame, text="Ground Truth Mask", bg="#1e1e1e", fg="#aaaaaa",
                    font=('Segoe UI', 9, 'bold')).pack(side=tk.TOP)
            gt_lbl = tk.Label(gt_frame, image=gt_photo, bg="#1e1e1e", relief=tk.GROOVE, bd=2)
            gt_lbl.pack(side=tk.TOP, pady=3)
            gt_lbl.bind("<MouseWheel>", _mw)
            
            # Color legend
            legend_frame = tk.Frame(preview_row, bg="#2d2d2d", relief=tk.GROOVE, bd=1)
            legend_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
            legend_frame.bind("<MouseWheel>", _mw)
            tk.Label(legend_frame, text="Legend", bg="#2d2d2d", fg="white",
                    font=('Segoe UI', 9, 'bold'), pady=4).pack(side=tk.TOP, fill=tk.X)
            
            for val in known_values:
                cat_name = value_to_cat.get(val, f"Value_{val}")
                rgb = color_map.get(val, (128, 128, 128))
                hex_c = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
                
                leg_row = tk.Frame(legend_frame, bg="#2d2d2d")
                leg_row.pack(side=tk.TOP, fill=tk.X, padx=4, pady=1)
                leg_row.bind("<MouseWheel>", _mw)
                
                tk.Label(leg_row, bg=hex_c, width=2, height=1, relief=tk.RAISED, bd=1).pack(side=tk.LEFT, padx=2)
                tk.Label(leg_row, text=f"{val}: {cat_name}", bg="#2d2d2d", fg="white",
                        font=('Segoe UI', 8), anchor='w').pack(side=tk.LEFT, padx=3)
            
            # Separator
            tk.Frame(main_inner, bg="#444444", height=1).pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)
        
        # === CONFUSION MATRIX TABLE ===
        cm_section = tk.Frame(main_inner, bg="#1e1e1e")
        cm_section.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        cm_section.bind("<MouseWheel>", _mw)
        
        tk.Label(cm_section, text="Confusion Matrix (rows=Ground Truth, cols=Predicted)",
                bg="#1e1e1e", fg="#cccccc", font=('Segoe UI', 9, 'bold'), anchor='w').pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        
        # Matrix grid
        cm_grid = tk.Frame(cm_section, bg="#1e1e1e")
        cm_grid.pack(side=tk.TOP, anchor='w')
        cm_grid.bind("<MouseWheel>", _mw)
        
        n = len(known_values)
        
        # Header row
        tk.Label(cm_grid, text="GT \\ Pred", bg="#333333", fg="#aaaaaa",
                font=('Segoe UI', 8, 'bold'), width=14, relief=tk.RIDGE, bd=1).grid(row=0, column=0, sticky='nsew')
        for j, val in enumerate(known_values):
            cat_name = value_to_cat.get(val, f"V{val}")
            short_name = cat_name[:8]
            color = LULCClassifier.CATEGORY_COLORS.get(cat_name, '#ffffff')
            lbl = tk.Label(cm_grid, text=f"{short_name}\n({val})", bg="#333333", fg=color,
                    font=('Segoe UI', 7, 'bold'), width=9, relief=tk.RIDGE, bd=1)
            lbl.grid(row=0, column=j+1, sticky='nsew')
            lbl.bind("<MouseWheel>", _mw)
        
        # Data rows
        for i, gt_val in enumerate(known_values):
            gt_cat = value_to_cat.get(gt_val, f"V{gt_val}")
            gt_color = LULCClassifier.CATEGORY_COLORS.get(gt_cat, '#ffffff')
            row_lbl = tk.Label(cm_grid, text=f"{gt_cat[:10]} ({gt_val})", bg="#333333", fg=gt_color,
                    font=('Segoe UI', 7, 'bold'), width=14, anchor='w', padx=4,
                    relief=tk.RIDGE, bd=1)
            row_lbl.grid(row=i+1, column=0, sticky='nsew')
            row_lbl.bind("<MouseWheel>", _mw)
            
            row_max = np.max(confusion[i, :]) if np.max(confusion[i, :]) > 0 else 1
            for j in range(n):
                count = confusion[i][j]
                if i == j:
                    bg_color = "#1a3a1a"
                    fg_color = "#00ff00"
                elif count > 0:
                    intensity = min(int(count / row_max * 180), 180)
                    bg_color = f"#{intensity:02x}2020"
                    fg_color = "#ffaaaa"
                else:
                    bg_color = "#1e1e1e"
                    fg_color = "#555555"
                
                cell = tk.Label(cm_grid, text=str(count), bg=bg_color, fg=fg_color,
                        font=('Segoe UI', 8), width=9, relief=tk.RIDGE, bd=1)
                cell.grid(row=i+1, column=j+1, sticky='nsew')
                cell.bind("<MouseWheel>", _mw)
        
        # Separator
        tk.Frame(main_inner, bg="#444444", height=1).pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)
        
        # === PER-CLASS STATISTICS ===
        stats_section = tk.Frame(main_inner, bg="#1e1e1e")
        stats_section.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        stats_section.bind("<MouseWheel>", _mw)
        
        tk.Label(stats_section, text="Per-Class Statistics",
                bg="#1e1e1e", fg="#cccccc", font=('Segoe UI', 9, 'bold'), anchor='w').pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        
        stats_grid = tk.Frame(stats_section, bg="#1e1e1e")
        stats_grid.pack(side=tk.TOP, anchor='w')
        stats_grid.bind("<MouseWheel>", _mw)
        
        headers = ["Category", "Val", "Precision%", "Recall%", "F1%", "GT Pixels", "Pred Pixels"]
        for col_i, h in enumerate(headers):
            lbl = tk.Label(stats_grid, text=h, bg="#333333", fg="#aaaaaa",
                    font=('Segoe UI', 8, 'bold'), relief=tk.RIDGE, bd=1, padx=4, pady=2)
            lbl.grid(row=0, column=col_i, sticky='nsew')
            lbl.bind("<MouseWheel>", _mw)
        
        for row_i, (cat_name, stats) in enumerate(per_class.items()):
            color = LULCClassifier.CATEGORY_COLORS.get(cat_name, '#ffffff')
            values = [
                cat_name[:12],
                str(stats['value']),
                f"{stats['precision']:.1f}",
                f"{stats['recall']:.1f}",
                f"{stats['f1']:.1f}",
                str(stats['gt_total']),
                str(stats['pred_total'])
            ]
            for col_i, v in enumerate(values):
                fg = color if col_i == 0 else "#ffffff"
                cell = tk.Label(stats_grid, text=v, bg="#1e1e1e", fg=fg,
                        font=('Segoe UI', 8), relief=tk.RIDGE, bd=1, padx=4, pady=2)
                cell.grid(row=row_i+1, column=col_i, sticky='nsew')
                cell.bind("<MouseWheel>", _mw)
    
    def save_mask_image(self):
        """Save the current image with LULC classification mask overlay"""
        if not self.tile_classifications:
            import tkinter.messagebox as messagebox
            messagebox.showwarning("Warning", "Please classify tiles first using 'Classify LULC' button.")
            return
        
        if not self.current_padded_image:
            import tkinter.messagebox as messagebox
            messagebox.showwarning("Warning", "No image loaded.")
            return
        
        from tkinter import filedialog, messagebox
        from PIL import Image, ImageDraw
        import os
        
        # Get current image name for default filename
        current_image_path = self.images[self.current_image_index][0]
        image_name = os.path.splitext(os.path.basename(current_image_path))[0]
        
        # Ask user where to save
        save_path = filedialog.asksaveasfilename(
            title="Save Image with LULC Mask",
            defaultextension=".png",
            initialfile=f"{image_name}_lulc_mask.png",
            filetypes=[("PNG files", "*.png"), ("TIFF files", "*.tif"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        if not save_path:
            return
        
        self.update_status("Saving mask image...")
        self.root.update()
        
        # Create a copy of the padded image to draw on
        base_image = self.current_padded_image.copy().convert("RGBA")
        
        # Create a transparent overlay for the mask
        overlay = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        tile_size = self.tile_size
        
        for i, tile_info in enumerate(self.tiles):
            if i >= len(self.tile_classifications):
                break
            
            category = self.tile_classifications[i]
            if not category or category == 'Cloud':
                continue
            
            color_hex = LULCClassifier.CATEGORY_COLORS.get(category, '#FFFFFF')
            # Convert hex to RGBA with semi-transparency
            r = int(color_hex[1:3], 16)
            g = int(color_hex[3:5], 16)
            b = int(color_hex[5:7], 16)
            alpha = 80  # Semi-transparent overlay
            
            x1 = tile_info['x']
            y1 = tile_info['y']
            x2 = x1 + tile_size
            y2 = y1 + tile_size
            
            # Draw filled rectangle with transparency
            draw.rectangle([x1, y1, x2, y2], fill=(r, g, b, alpha), outline=(r, g, b, 200), width=2)
        
        # Composite overlay onto base image
        result = Image.alpha_composite(base_image, overlay)
        
        # Convert to RGB if saving as JPEG
        if save_path.lower().endswith(('.jpg', '.jpeg')):
            result = result.convert("RGB")
        else:
            result = result.convert("RGB")
        
        try:
            result.save(save_path)
            self.update_status(f"Saved mask image to: {save_path}")
            messagebox.showinfo("Save Complete", f"LULC mask image saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save mask image: {e}")
    
    def _apply_preprocessing(self):
        """Apply preprocessing to current image"""
        if not self.images or self.current_image_index >= len(self.images):
            return
        
        # Initialize classifier if needed
        if not self.lulc_classifier:
            self.lulc_classifier = LULCClassifier(
                apply_color_correction=True,
                filter_clouds=True,
                cloud_threshold=0.7
            )
        
        current_image_path, current_image = self.images[self.current_image_index]
        
        # Convert PIL to numpy array (BGR)
        img_array = cv2.cvtColor(np.array(current_image), cv2.COLOR_RGB2BGR)
        
        # Apply preprocessing
        stats = self.lulc_classifier.analyze_image_bands(img_array)
        corrected_img = self.lulc_classifier.apply_band_correction(img_array, stats)
        
        # Convert back to PIL RGB
        corrected_rgb = cv2.cvtColor(corrected_img, cv2.COLOR_BGR2RGB)
        from PIL import Image
        self.preprocessed_image = Image.fromarray(corrected_rgb)
    
    def _save_preprocessed_image(self):
        """Save preprocessed image with CLAHE and color correction"""
        import os
        from tkinter import filedialog
        
        if not self.images or self.current_image_index >= len(self.images):
            return
        
        current_image_path, current_image = self.images[self.current_image_index]
        image_name = os.path.splitext(os.path.basename(current_image_path))[0]
        
        # Convert PIL to numpy array (BGR)
        img_array = cv2.cvtColor(np.array(current_image), cv2.COLOR_RGB2BGR)
        
        # Apply preprocessing
        if not self.lulc_classifier:
            self.lulc_classifier = LULCClassifier(
                apply_color_correction=True,
                filter_clouds=True,
                cloud_threshold=0.7
            )
        
        stats = self.lulc_classifier.analyze_image_bands(img_array)
        corrected_img = self.lulc_classifier.apply_band_correction(img_array, stats)
        
        # Ask user where to save
        default_name = f"{image_name}_preprocessed.tif"
        save_path = filedialog.asksaveasfilename(
            title="Save Preprocessed Image",
            defaultextension=".tif",
            initialfile=default_name,
            filetypes=[("TIFF files", "*.tif"), ("All files", "*.*")]
        )
        
        if save_path:
            cv2.imwrite(save_path, corrected_img)
            self.update_status(f"Saved preprocessed image to: {save_path}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ImageTileSelector(root)
    root.mainloop()


if __name__ == "__main__":
    main()
