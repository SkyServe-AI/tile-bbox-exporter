"""
BBox Selector - Main Application
Modular architecture with separated concerns
"""
import tkinter as tk
from tkinter import ttk

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
        
        # Multi-class annotation system
        self.classes = [
            {'name': 'Class 1', 'color': '#00ff00'},
            {'name': 'Class 2', 'color': '#ff0000'},
            {'name': 'Class 3', 'color': '#0000ff'},
            {'name': 'Class 4', 'color': '#ffff00'},
            {'name': 'Class 5', 'color': '#ff00ff'},
        ]
        self.current_class_index = 0  # Currently selected class for new annotations
        
        # Image augmentation system
        from .augmentation import ImageAugmentor
        self.augmentor = ImageAugmentor()
        
        # Export format system
        from .export_formats import ExportFormatter
        self.export_formatter = ExportFormatter()
        self.export_format = tk.StringVar(value='JSON')  # Default format
        
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
    
    def manage_classes(self):
        """Open class management dialog"""
        from tkinter import simpledialog, colorchooser
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Manage Classes")
        dialog.geometry("500x400")
        dialog.configure(bg="#2d2d2d")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Class list frame
        list_frame = tk.Frame(dialog, bg="#2d2d2d")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(list_frame, text="Classes:", bg="#2d2d2d", fg="white",
                font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        
        # Listbox with scrollbar
        listbox_frame = tk.Frame(list_frame, bg="#2d2d2d")
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        class_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set,
                                   bg="#404040", fg="white", font=('Segoe UI', 10),
                                   selectmode=tk.SINGLE, height=10)
        class_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=class_listbox.yview)
        
        def refresh_list():
            class_listbox.delete(0, tk.END)
            for cls in self.classes:
                class_listbox.insert(tk.END, f"{cls['name']} ({cls['color']})")
        
        refresh_list()
        
        # Buttons frame
        btn_frame = tk.Frame(dialog, bg="#2d2d2d")
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def add_class():
            name = simpledialog.askstring("Add Class", "Enter class name:", parent=dialog)
            if name:
                color = colorchooser.askcolor(title="Choose class color", parent=dialog)
                if color[1]:
                    self.classes.append({'name': name, 'color': color[1]})
                    refresh_list()
                    self._update_class_dropdown()
        
        def edit_class():
            selection = class_listbox.curselection()
            if not selection:
                return
            idx = selection[0]
            
            name = simpledialog.askstring("Edit Class", "Enter new class name:",
                                        initialvalue=self.classes[idx]['name'], parent=dialog)
            if name:
                color = colorchooser.askcolor(title="Choose class color",
                                             initialcolor=self.classes[idx]['color'], parent=dialog)
                if color[1]:
                    self.classes[idx]['name'] = name
                    self.classes[idx]['color'] = color[1]
                    refresh_list()
                    self._update_class_dropdown()
        
        def delete_class():
            selection = class_listbox.curselection()
            if not selection:
                return
            idx = selection[0]
            if len(self.classes) <= 1:
                tk.messagebox.showwarning("Warning", "Must have at least one class!", parent=dialog)
                return
            del self.classes[idx]
            refresh_list()
            self._update_class_dropdown()
        
        tk.Button(btn_frame, text="➕ Add Class", command=add_class,
                 bg="#107c10", fg="white", font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="✏️ Edit Class", command=edit_class,
                 bg="#8764b8", fg="white", font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Delete Class", command=delete_class,
                 bg="#d13438", fg="white", font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=dialog.destroy,
                 bg="#505050", fg="white", font=('Segoe UI', 9)).pack(side=tk.RIGHT, padx=5)
    
    def _update_class_dropdown(self):
        """Update the class dropdown with current classes"""
        if hasattr(self, 'class_var'):
            current = self.class_var.get()
            self.class_var.set(self.classes[0]['name'] if self.classes else '')
            # Update combobox values - need to find the combobox widget
            for widget in self.root.winfo_children():
                self._update_combobox_recursive(widget, [c['name'] for c in self.classes])
    
    def _update_combobox_recursive(self, widget, values):
        """Recursively find and update combobox"""
        if isinstance(widget, ttk.Combobox):
            widget['values'] = values
        for child in widget.winfo_children():
            self._update_combobox_recursive(child, values)
    
    def open_augmentation_settings(self):
        """Open augmentation settings dialog"""
        from tkinter import messagebox
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Augmentation Settings")
        dialog.geometry("550x700")
        dialog.configure(bg="#2d2d2d")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create canvas with scrollbar for scrollable content
        canvas_container = tk.Frame(dialog, bg="#2d2d2d")
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(canvas_container, bg="#2d2d2d", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#2d2d2d")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        dialog.protocol("WM_DELETE_WINDOW", lambda: (canvas.unbind_all("<MouseWheel>"), dialog.destroy()))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main frame inside scrollable area
        main_frame = tk.Frame(scrollable_frame, bg="#2d2d2d")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(main_frame, text="Image Augmentation Options", bg="#2d2d2d", fg="white",
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(0, 10))
        
        # Current settings info
        current_count = self.augmentor.get_augmentation_count()
        info_label = tk.Label(main_frame, 
                             text=f"Current: {current_count}x augmentation per bbox" if current_count > 1 else "Current: No augmentation enabled",
                             bg="#2d2d2d", fg="#00ff00" if current_count > 1 else "#ff9900",
                             font=('Segoe UI', 9, 'bold'))
        info_label.pack(anchor='w', pady=(0, 10))
        
        # Augmentation options
        options_frame = tk.Frame(main_frame, bg="#2d2d2d")
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        # Rotation
        rotation_frame = tk.LabelFrame(options_frame, text="Rotation", bg="#2d2d2d", fg="white",
                                      font=('Segoe UI', 10, 'bold'), padx=10, pady=5)
        rotation_frame.pack(fill=tk.X, pady=5)
        
        rotation_var = tk.BooleanVar(value=self.augmentor.augmentation_options.get('rotation', False))
        tk.Checkbutton(rotation_frame, text="Enable rotation (90°, 180°, 270°)", 
                      variable=rotation_var, bg="#2d2d2d", fg="white", 
                      selectcolor="#404040", font=('Segoe UI', 9)).pack(anchor='w')
        
        # Flipping
        flip_frame = tk.LabelFrame(options_frame, text="Flipping", bg="#2d2d2d", fg="white",
                                  font=('Segoe UI', 10, 'bold'), padx=10, pady=5)
        flip_frame.pack(fill=tk.X, pady=5)
        
        hflip_var = tk.BooleanVar(value=self.augmentor.augmentation_options.get('horizontal_flip', False))
        tk.Checkbutton(flip_frame, text="Horizontal flip", variable=hflip_var, 
                      bg="#2d2d2d", fg="white", selectcolor="#404040", 
                      font=('Segoe UI', 9)).pack(anchor='w')
        
        vflip_var = tk.BooleanVar(value=self.augmentor.augmentation_options.get('vertical_flip', False))
        tk.Checkbutton(flip_frame, text="Vertical flip", variable=vflip_var, 
                      bg="#2d2d2d", fg="white", selectcolor="#404040", 
                      font=('Segoe UI', 9)).pack(anchor='w')
        
        # Brightness
        brightness_frame = tk.LabelFrame(options_frame, text="Brightness", bg="#2d2d2d", fg="white",
                                        font=('Segoe UI', 10, 'bold'), padx=10, pady=5)
        brightness_frame.pack(fill=tk.X, pady=5)
        
        brightness_var = tk.BooleanVar(value=self.augmentor.augmentation_options.get('brightness', False))
        tk.Checkbutton(brightness_frame, text="Random brightness adjustment (0.7x - 1.3x)", 
                      variable=brightness_var, bg="#2d2d2d", fg="white", 
                      selectcolor="#404040", font=('Segoe UI', 9)).pack(anchor='w')
        
        # Contrast
        contrast_frame = tk.LabelFrame(options_frame, text="Contrast", bg="#2d2d2d", fg="white",
                                      font=('Segoe UI', 10, 'bold'), padx=10, pady=5)
        contrast_frame.pack(fill=tk.X, pady=5)
        
        contrast_var = tk.BooleanVar(value=self.augmentor.augmentation_options.get('contrast', False))
        tk.Checkbutton(contrast_frame, text="Random contrast adjustment (0.8x - 1.2x)", 
                      variable=contrast_var, bg="#2d2d2d", fg="white", 
                      selectcolor="#404040", font=('Segoe UI', 9)).pack(anchor='w')
        
        # Blur
        blur_frame = tk.LabelFrame(options_frame, text="Blur", bg="#2d2d2d", fg="white",
                                  font=('Segoe UI', 10, 'bold'), padx=10, pady=5)
        blur_frame.pack(fill=tk.X, pady=5)
        
        blur_var = tk.BooleanVar(value=self.augmentor.augmentation_options.get('blur', False))
        tk.Checkbutton(blur_frame, text="Gaussian blur (radius 0.5 - 2.0)", 
                      variable=blur_var, bg="#2d2d2d", fg="white", 
                      selectcolor="#404040", font=('Segoe UI', 9)).pack(anchor='w')
        
        # Noise
        noise_frame = tk.LabelFrame(options_frame, text="Noise", bg="#2d2d2d", fg="white",
                                   font=('Segoe UI', 10, 'bold'), padx=10, pady=5)
        noise_frame.pack(fill=tk.X, pady=5)
        
        noise_var = tk.BooleanVar(value=self.augmentor.augmentation_options.get('noise', False))
        tk.Checkbutton(noise_frame, text="Random noise (±5 to ±25 intensity)", 
                      variable=noise_var, bg="#2d2d2d", fg="white", 
                      selectcolor="#404040", font=('Segoe UI', 9)).pack(anchor='w')
        
        # Saturation
        saturation_frame = tk.LabelFrame(options_frame, text="Saturation", bg="#2d2d2d", fg="white",
                                        font=('Segoe UI', 10, 'bold'), padx=10, pady=5)
        saturation_frame.pack(fill=tk.X, pady=5)
        
        saturation_var = tk.BooleanVar(value=self.augmentor.augmentation_options.get('saturation', False))
        tk.Checkbutton(saturation_frame, text="Random saturation (0.8x - 1.2x)", 
                      variable=saturation_var, bg="#2d2d2d", fg="white", 
                      selectcolor="#404040", font=('Segoe UI', 9)).pack(anchor='w')
        
        # Sharpness
        sharpness_frame = tk.LabelFrame(options_frame, text="Sharpness", bg="#2d2d2d", fg="white",
                                       font=('Segoe UI', 10, 'bold'), padx=10, pady=5)
        sharpness_frame.pack(fill=tk.X, pady=5)
        
        sharpness_var = tk.BooleanVar(value=self.augmentor.augmentation_options.get('sharpness', False))
        tk.Checkbutton(sharpness_frame, text="Random sharpness (0.8x - 1.2x)", 
                      variable=sharpness_var, bg="#2d2d2d", fg="white", 
                      selectcolor="#404040", font=('Segoe UI', 9)).pack(anchor='w')
        
        # Info label
        info_frame = tk.Frame(main_frame, bg="#2d2d2d")
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        count_label = tk.Label(info_frame, text="", bg="#2d2d2d", fg="#00ff00",
                              font=('Segoe UI', 9, 'bold'))
        count_label.pack(anchor='w')
        
        def update_count():
            # Temporarily update options to calculate count
            temp_options = {
                'rotation': rotation_var.get(),
                'horizontal_flip': hflip_var.get(),
                'vertical_flip': vflip_var.get(),
                'brightness': brightness_var.get(),
                'contrast': contrast_var.get(),
                'blur': blur_var.get(),
                'noise': noise_var.get(),
                'saturation': saturation_var.get(),
                'sharpness': sharpness_var.get(),
            }
            count = 1  # Original
            if temp_options['rotation']: count += 3
            if temp_options['horizontal_flip']: count += 1
            if temp_options['vertical_flip']: count += 1
            if temp_options['brightness']: count += 1
            if temp_options['contrast']: count += 1
            if temp_options['blur']: count += 1
            if temp_options['noise']: count += 1
            if temp_options['saturation']: count += 1
            if temp_options['sharpness']: count += 1
            
            count_label.config(text=f"📊 Total augmented images per bbox: {count}x")
        
        # Bind checkboxes to update count
        for var in [rotation_var, hflip_var, vflip_var, brightness_var, contrast_var, 
                   blur_var, noise_var, saturation_var, sharpness_var]:
            var.trace('w', lambda *args: update_count())
        
        update_count()
        
        # Buttons
        btn_frame = tk.Frame(main_frame, bg="#2d2d2d")
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        def save_settings():
            self.augmentor.augmentation_options['rotation'] = rotation_var.get()
            self.augmentor.augmentation_options['horizontal_flip'] = hflip_var.get()
            self.augmentor.augmentation_options['vertical_flip'] = vflip_var.get()
            self.augmentor.augmentation_options['brightness'] = brightness_var.get()
            self.augmentor.augmentation_options['contrast'] = contrast_var.get()
            self.augmentor.augmentation_options['blur'] = blur_var.get()
            self.augmentor.augmentation_options['noise'] = noise_var.get()
            self.augmentor.augmentation_options['saturation'] = saturation_var.get()
            self.augmentor.augmentation_options['sharpness'] = sharpness_var.get()
            
            count = self.augmentor.get_augmentation_count()
            messagebox.showinfo("Success", 
                              f"Augmentation settings saved!\n\nEach bbox will generate {count}x images during export.", 
                              parent=dialog)
            dialog.destroy()
        
        tk.Button(btn_frame, text="💾 Save Settings", command=save_settings,
                 bg="#107c10", fg="white", font=('Segoe UI', 9, 'bold'),
                 padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg="#505050", fg="white", font=('Segoe UI', 9),
                 padx=10, pady=5).pack(side=tk.RIGHT, padx=5)
    
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
