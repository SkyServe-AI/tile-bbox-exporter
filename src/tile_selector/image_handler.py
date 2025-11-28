"""
Image Handler Module for Tile Selector
Manages image loading and navigation operations
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


class ImageHandler:
    """Handles image loading and navigation"""
    
    def __init__(self, app):
        self.app = app
        self._setup_drag_drop()
        
    def is_image_file(self, filepath):
        """Check if file is a supported image format"""
        ext = os.path.splitext(filepath)[1].lower()
        return ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.gif']
    
    def upload_images(self):
        """Upload multiple image files"""
        filetypes = [
            ('Image files', '*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.gif'),
            ('All files', '*.*')
        ]
        filepaths = filedialog.askopenfilenames(title="Select Images", filetypes=filetypes)
        if filepaths:
            self.app.images = []
            self.app.image_tile_selections = {}  # Clear previous selections
            self._clear_classifications()  # Clear LULC classifications
            for filepath in filepaths:
                try:
                    img = Image.open(filepath)
                    self.app.images.append((filepath, img))
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load {filepath}: {e}")
            if self.app.images:
                self.app.update_status(f"Loaded {len(self.app.images)} image(s)")
                self.app.update_image_list()
                self.app.current_image_index = 0
                self.app.apply_tile_size()

    def upload_folder(self):
        """Upload all images from a folder"""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self.app.images = []
            self.app.image_tile_selections = {}  # Clear previous selections
            self._clear_classifications()  # Clear LULC classifications
            for file in os.listdir(folder):
                path = os.path.join(folder, file)
                if os.path.isfile(path) and self.is_image_file(path):
                    try:
                        img = Image.open(path)
                        self.app.images.append((path, img))
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to load {path}: {e}")
            if not self.app.images:
                messagebox.showwarning("Warning", "No valid images found in folder.")
                self.app.update_status("No images found")
            else:
                self.app.update_status(f"Loaded {len(self.app.images)} image(s) from folder")
                self.app.update_image_list()
                self.app.current_image_index = 0
                self.app.apply_tile_size()
    
    def update_image_list(self):
        """Update the image list in side panel"""
        self.app.image_listbox.delete(0, tk.END)
        for i, (path, img) in enumerate(self.app.images):
            filename = os.path.basename(path)
            self.app.image_listbox.insert(tk.END, f"{i+1}. {filename}")
        
        if self.app.images:
            self.app.image_listbox.selection_set(self.app.current_image_index)
            self.app.image_counter_label.config(
                text=f"{self.app.current_image_index + 1} / {len(self.app.images)}")
        else:
            self.app.image_counter_label.config(text="0 / 0")
    
    def on_image_select(self, event):
        """Handle image selection from listbox"""
        selection = self.app.image_listbox.curselection()
        if selection:
            # Save current image's selections before switching
            if self.app.images and self.app.current_image_index < len(self.app.images):
                current_image_path = self.app.images[self.app.current_image_index][0]
                self.app.image_tile_selections[current_image_path] = self.app.selected_tiles.copy()
            
            self.app.current_image_index = selection[0]
            self.app.image_counter_label.config(
                text=f"{self.app.current_image_index + 1} / {len(self.app.images)}")
            self._clear_classifications()  # Clear classifications when switching images
            self.app.apply_tile_size()
    
    def prev_image(self):
        """Show previous image"""
        if not self.app.images:
            return
        
        # Save current image's selections before switching
        current_image_path = self.app.images[self.app.current_image_index][0]
        self.app.image_tile_selections[current_image_path] = self.app.selected_tiles.copy()
        
        self.app.current_image_index = (self.app.current_image_index - 1) % len(self.app.images)
        self.app.image_listbox.selection_clear(0, tk.END)
        self.app.image_listbox.selection_set(self.app.current_image_index)
        self.app.image_listbox.see(self.app.current_image_index)
        self.app.image_counter_label.config(
            text=f"{self.app.current_image_index + 1} / {len(self.app.images)}")
        self._clear_classifications()  # Clear classifications when switching images
        self.app.apply_tile_size()
    
    def next_image(self):
        """Show next image"""
        if not self.app.images:
            return
        
        # Save current image's selections before switching
        current_image_path = self.app.images[self.app.current_image_index][0]
        self.app.image_tile_selections[current_image_path] = self.app.selected_tiles.copy()
        
        self.app.current_image_index = (self.app.current_image_index + 1) % len(self.app.images)
        self.app.image_listbox.selection_clear(0, tk.END)
        self.app.image_listbox.selection_set(self.app.current_image_index)
        self.app.image_listbox.see(self.app.current_image_index)
        self.app.image_counter_label.config(
            text=f"{self.app.current_image_index + 1} / {len(self.app.images)}")
        self._clear_classifications()  # Clear classifications when switching images
        self.app.apply_tile_size()
    
    def _setup_drag_drop(self):
        """Setup drag and drop functionality"""
        # This will be called after canvas is created
        pass
    
    def enable_drag_drop(self):
        """Enable drag and drop on canvas after it's created"""
        if not DND_AVAILABLE:
            return
        
        if hasattr(self.app, 'canvas') and self.app.canvas:
            try:
                self.app.canvas.drop_target_register(DND_FILES)
                self.app.canvas.dnd_bind('<<Drop>>', self.on_drop)
                self.app.canvas.dnd_bind('<<DragEnter>>', self.on_drag_enter)
                self.app.canvas.dnd_bind('<<DragLeave>>', self.on_drag_leave)
            except Exception as e:
                print(f"Could not enable drag and drop: {e}")
    
    def on_drag_enter(self, event):
        """Visual feedback when dragging over canvas"""
        self.app.canvas.config(bg="#2a2a2a")
        self.app.update_status("Drop images or folder here...")
    
    def on_drag_leave(self, event):
        """Reset visual feedback when leaving canvas"""
        self.app.canvas.config(bg="#1e1e1e")
        if self.app.images:
            self.app.update_status(f"Image {self.app.current_image_index + 1}/{len(self.app.images)} | {len(self.app.tiles)} tiles")
        else:
            self.app.update_status("Ready | Upload images to start")
    
    def on_drop(self, event):
        """Handle dropped files/folders"""
        self.app.canvas.config(bg="#1e1e1e")
        
        # Parse dropped data
        files = self._parse_drop_data(event.data)
        
        if not files:
            return
        
        # Process dropped items
        self.app.images = []
        self.app.image_tile_selections = {}  # Clear previous selections
        
        for item in files:
            if os.path.isfile(item):
                # Single file dropped
                if self.is_image_file(item):
                    try:
                        img = Image.open(item)
                        self.app.images.append((item, img))
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to load {item}: {e}")
            elif os.path.isdir(item):
                # Folder dropped
                for file in os.listdir(item):
                    path = os.path.join(item, file)
                    if os.path.isfile(path) and self.is_image_file(path):
                        try:
                            img = Image.open(path)
                            self.app.images.append((path, img))
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to load {path}: {e}")
        
        if not self.app.images:
            messagebox.showwarning("Warning", "No valid images found in dropped items.")
            self.app.update_status("No images found")
        else:
            self.app.update_status(f"Loaded {len(self.app.images)} image(s) via drag & drop")
            self.app.update_image_list()
            self.app.current_image_index = 0
            self._clear_classifications()  # Clear LULC classifications
            self.app.apply_tile_size()
    
    def _parse_drop_data(self, data):
        """Parse dropped file/folder paths from event data"""
        # Handle different formats of dropped data
        if isinstance(data, str):
            # Remove curly braces and split by spaces (Windows format)
            data = data.strip('{}')
            # Split by } { pattern for multiple files
            if '} {' in data:
                files = data.split('} {')
                files = [f.strip('{}') for f in files]
            else:
                files = [data]
            return files
        elif isinstance(data, (list, tuple)):
            return list(data)
        return []
    
    def _clear_classifications(self):
        """Clear LULC classifications and hide legend"""
        self.app.tile_classifications = []
        if hasattr(self.app, 'legend_frame') and self.app.legend_frame:
            if self.app.legend_frame.winfo_ismapped():
                self.app.legend_frame.pack_forget()
        # Reset category counts
        if hasattr(self.app, 'category_counts'):
            from .lulc_classifier import LULCClassifier
            for category in LULCClassifier.CATEGORIES:
                if category in self.app.category_counts:
                    self.app.category_counts[category].config(text=f"{category}: 0")
        
        # Clear preprocessed image
        self.app.preprocessed_image = None
        if hasattr(self.app, 'preprocess_enabled') and self.app.preprocess_enabled:
            self.app.preprocess_enabled.set(False)
