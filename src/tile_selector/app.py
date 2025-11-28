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
        self.canvas.bind("<Motion>", self.canvas_handler.on_mouse_motion)  # Track mouse for hand tool
        self.canvas.bind("<MouseWheel>", self.canvas_handler.on_mouse_wheel)
        self.canvas.bind("<Control-MouseWheel>", self.canvas_handler.on_ctrl_mouse_wheel)
        self.canvas.bind("<Shift-MouseWheel>", self.canvas_handler.on_shift_mouse_wheel)
        self.canvas.bind("<Button-2>", self.canvas_handler.on_drag_start)
        self.canvas.bind("<B2-Motion>", self.canvas_handler.on_drag_motion)
    
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
            self.export_lulc_tiles()
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
            if self.overlay_visible:
                self.overlay_toggle_btn.config(relief=tk.RAISED, bg='#0e639c')
                self.update_status("LULC Overlay Visible")
            else:
                self.overlay_toggle_btn.config(relief=tk.SUNKEN, bg='#555555')
                self.update_status("LULC Overlay Hidden")
        
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
