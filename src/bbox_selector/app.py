"""
BBox Selector - Main Application
Modular architecture with separated concerns
"""
import tkinter as tk

from .ui_components import UIComponents
from .image_handler import ImageHandler
from .shape_manager import ShapeManager
from .canvas_handler import CanvasHandler
from .mouse_handler import MouseHandler


class BBoxSelector:
    """Main application class for BBox Selector"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("SkyServe BBox Selector - Beta Edition")
        
        # Initialize responsive sizing
        self._init_responsive_sizing()
        
        # Initialize variables
        self._init_variables()
        
        # Initialize handlers
        self._init_handlers()
        
        # Setup GUI
        self.ui.setup_gui()
        
        # Bind mouse events
        self.mouse_handler.bind_events()
        
        # Enable drag and drop after canvas is created
        self.image_handler.enable_drag_drop()
    
    def _init_responsive_sizing(self):
        """Initialize responsive window sizing and fonts"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window size based on screen (85% of screen for 13"+ displays)
        window_width = min(int(screen_width * 0.85), 1600)
        window_height = min(int(screen_height * 0.85), 1000)
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.configure(bg="#1e1e1e")
        
        # Calculate responsive font sizes based on screen width
        self.base_font_size = 10 if screen_width >= 1366 else 9
        self.heading_font_size = self.base_font_size + 2
        self.button_font_size = self.base_font_size
        self.status_font_size = self.base_font_size - 1
    
    def _init_variables(self):
        """Initialize all application variables"""
        # Image management
        self.images = []  # List of (image_path, PIL.Image)
        self.current_image_index = 0
        self.image = None
        self.image_path = None
        self.display_image = None
        
        # Zoom settings
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
        # BBox settings
        self.bbox_width = 64
        self.bbox_height = 64
        
        # Annotations storage per image
        self.image_annotations = {}
        
        # Current image annotations
        self.bboxes = []
        self.bbox_counter = 0
        self.selected_bbox = None
        self.hovered_bbox = None
        
        # Dragging state
        self.dragging = False
        self.drag_handle = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Polygon mode
        self.custom_select_mode = tk.BooleanVar(value=False)
        self.polygon_points = []
        self.polygon_counter = 0
        self.polygons = []
        self.selected_polygon = None
        
        # Canvas offsets
        self.image_offset_x = 0
        self.image_offset_y = 0
        
        # UI elements (will be set by UIComponents)
        self.canvas = None
        self.zoom_label = None
        self.status_label = None
        self.side_panel = None
        self.image_listbox = None
        self.image_counter_label = None
        self.prev_btn = None
        self.next_btn = None
        self.bbox_width_var = None
        self.bbox_height_var = None
    
    def _init_handlers(self):
        """Initialize all handler modules"""
        self.ui = UIComponents(self.root, self)
        self.image_handler = ImageHandler(self)
        self.shape_manager = ShapeManager(self)
        self.canvas_handler = CanvasHandler(self)
        self.mouse_handler = MouseHandler(self)
    
    # Delegate methods to handlers
    def load_image(self):
        """Load a single image"""
        self.image_handler.load_image()
    
    def upload_folder(self):
        """Load images from folder"""
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
    
    def display_image_on_canvas(self):
        """Display image on canvas"""
        self.canvas_handler.display_image_on_canvas()
    
    def zoom_in(self):
        """Zoom in"""
        self.canvas_handler.zoom_in()
    
    def zoom_out(self):
        """Zoom out"""
        self.canvas_handler.zoom_out()
    
    def zoom_reset(self):
        """Reset zoom"""
        self.canvas_handler.zoom_reset()
    
    def validate_bbox_size(self, event=None):
        """Validate bbox size"""
        self.shape_manager.validate_bbox_size(event)
    
    def apply_size_to_selected(self):
        """Apply size to selected bbox"""
        self.shape_manager.apply_size_to_selected()
    
    def delete_selected_shape(self):
        """Delete selected shape"""
        self.shape_manager.delete_selected_shape()
    
    def clear_all_shapes(self):
        """Clear all shapes"""
        self.shape_manager.clear_all_shapes()
    
    def save_all_shapes(self):
        """Save all shapes"""
        self.shape_manager.save_all_shapes()
    
    def toggle_custom_select(self):
        """Toggle polygon mode"""
        self.shape_manager.toggle_custom_select()
    
    def update_status(self, message):
        """Update status bar message"""
        if self.status_label:
            self.status_label.config(text=message)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = BBoxSelector(root)
    root.mainloop()


if __name__ == "__main__":
    main()
