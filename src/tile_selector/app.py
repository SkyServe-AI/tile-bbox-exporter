"""
Tile Selector - Main Application
Modular architecture with separated concerns
"""
import tkinter as tk

from .ui_components import UIComponents
from .image_handler import ImageHandler
from .tile_manager import TileManager
from .canvas_handler import CanvasHandler


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
        if self.is_classification.get():
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


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ImageTileSelector(root)
    root.mainloop()


if __name__ == "__main__":
    main()
