"""
Tile Manager Module for Tile Selector
Handles tile generation and export operations
"""
import os
import math
from tkinter import filedialog, messagebox
from PIL import Image


class TileManager:
    """Manages tile operations"""
    
    def __init__(self, app):
        self.app = app
        
    def validate_tile_size(self, event=None):
        """Validate tile size input"""
        try:
            size = int(self.app.tile_size_var.get())
            if size <= 0:
                raise ValueError
            self.app.tile_size = size
        except ValueError:
            messagebox.showerror("Error", "Tile size must be a positive integer.")
            self.app.tile_size_var.set(str(self.app.tile_size))

    def apply_tile_size(self):
        """Apply tile size and generate tiles"""
        if not self.app.images:
            return
        self.validate_tile_size()
        
        # Clear LULC classifications when tile size changes
        self.app.tile_classifications = []
        if hasattr(self.app, 'legend_frame') and self.app.legend_frame:
            if self.app.legend_frame.winfo_ismapped():
                self.app.legend_frame.pack_forget()
        
        # Get current image (use preprocessed if enabled, otherwise original)
        current_image_path, original_image = self.app.images[self.app.current_image_index]
        
        # Use preprocessed image if preprocessing is enabled
        if hasattr(self.app, 'preprocess_enabled') and self.app.preprocess_enabled and self.app.preprocess_enabled.get():
            if self.app.preprocessed_image is not None:
                current_image = self.app.preprocessed_image
            else:
                current_image = original_image
        else:
            current_image = original_image
        
        # Calculate padding needed
        img_width, img_height = current_image.size
        tile_size = self.app.tile_size
        
        # Calculate how many tiles fit
        tiles_x = math.ceil(img_width / tile_size)
        tiles_y = math.ceil(img_height / tile_size)
        
        # Calculate padded dimensions
        padded_width = tiles_x * tile_size
        padded_height = tiles_y * tile_size
        
        # Create padded image
        padded_image = Image.new('RGB', (padded_width, padded_height), (0, 0, 0))
        padded_image.paste(current_image, (0, 0))
        
        # Store for display
        self.app.current_padded_image = padded_image
        
        # Load saved selections for this image, or start with empty set
        saved_selections = self.app.image_tile_selections.get(current_image_path, set())
        
        self.app.tiles = []
        self.app.selected_tiles = set()
        
        # Generate tiles
        image_name = os.path.splitext(os.path.basename(current_image_path))[0]
        tile_index = 0
        for row in range(tiles_y):
            for col in range(tiles_x):
                x = col * tile_size
                y = row * tile_size
                tile_img = padded_image.crop((x, y, x + tile_size, y + tile_size))
                
                # Check if this tile was previously selected for THIS image
                is_selected = tile_index in saved_selections
                if is_selected:
                    self.app.selected_tiles.add(tile_index)
                
                self.app.tiles.append({
                    'image_name': image_name,
                    'row': row,
                    'col': col,
                    'x': x,
                    'y': y,
                    'tile_img': tile_img,
                    'selected': is_selected
                })
                tile_index += 1
        
        self.app.display_grid()
    
    def export_tiles(self):
        """Export all selected tiles from all images"""
        if not self.app.images:
            messagebox.showwarning("Warning", "No images loaded.")
            return
        
        # Save current image's selections
        if self.app.current_image_index < len(self.app.images):
            current_image_path = self.app.images[self.app.current_image_index][0]
            self.app.image_tile_selections[current_image_path] = self.app.selected_tiles.copy()
        
        folder = filedialog.askdirectory(title="Select Export Folder")
        if not folder:
            return
        
        exported = 0
        total_selected = 0
        
        # Process each image
        for img_path, img in self.app.images:
            # Get selected tiles for this image
            selected_tiles = self.app.image_tile_selections.get(img_path, set())
            if not selected_tiles:
                continue
            
            total_selected += len(selected_tiles)
            
            # Generate tiles for this image
            img_width, img_height = img.size
            tiles_x = math.ceil(img_width / self.app.tile_size)
            tiles_y = math.ceil(img_height / self.app.tile_size)
            padded_width = tiles_x * self.app.tile_size
            padded_height = tiles_y * self.app.tile_size
            
            padded_image = Image.new('RGB', (padded_width, padded_height), (0, 0, 0))
            padded_image.paste(img, (0, 0))
            
            image_name = os.path.splitext(os.path.basename(img_path))[0]
            tile_index = 0
            
            for row in range(tiles_y):
                for col in range(tiles_x):
                    if tile_index in selected_tiles:
                        x = col * self.app.tile_size
                        y = row * self.app.tile_size
                        tile_img = padded_image.crop((x, y, x + self.app.tile_size, y + self.app.tile_size))
                        
                        filename = f"{image_name}_tile_{row}_{col}.png"
                        path = os.path.join(folder, filename)
                        try:
                            tile_img.save(path)
                            exported += 1
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to save {filename}: {e}")
                    tile_index += 1
        
        if exported == 0:
            messagebox.showwarning("Warning", "No tiles selected for export.")
        else:
            messagebox.showinfo("Export Complete", f"Exported {exported} selected tiles to {folder}.")
            self.app.update_status(f"Exported {exported} tiles successfully")
    
    def export_classification(self):
        """Export tiles in classification mode: selected to folder, unselected to no_<folder>"""
        if not self.app.images:
            messagebox.showwarning("Warning", "No images loaded.")
            return
        
        # Save current image's selections
        if self.app.current_image_index < len(self.app.images):
            current_image_path = self.app.images[self.app.current_image_index][0]
            self.app.image_tile_selections[current_image_path] = self.app.selected_tiles.copy()
        
        folder = filedialog.askdirectory(title="Select Export Folder for Selected Tiles")
        if not folder:
            return
        
        # Create "no_" folder for unselected tiles
        folder_name = os.path.basename(folder)
        parent_folder = os.path.dirname(folder)
        no_folder = os.path.join(parent_folder, f"no_{folder_name}")
        
        # Create folders if they don't exist
        os.makedirs(folder, exist_ok=True)
        os.makedirs(no_folder, exist_ok=True)
        
        exported_selected = 0
        exported_unselected = 0
        
        # Process each image
        for img_path, img in self.app.images:
            # Get selected tiles for this image
            selected_tiles = self.app.image_tile_selections.get(img_path, set())
            
            # Generate tiles for this image
            img_width, img_height = img.size
            tiles_x = math.ceil(img_width / self.app.tile_size)
            tiles_y = math.ceil(img_height / self.app.tile_size)
            padded_width = tiles_x * self.app.tile_size
            padded_height = tiles_y * self.app.tile_size
            
            padded_image = Image.new('RGB', (padded_width, padded_height), (0, 0, 0))
            padded_image.paste(img, (0, 0))
            
            image_name = os.path.splitext(os.path.basename(img_path))[0]
            tile_index = 0
            
            for row in range(tiles_y):
                for col in range(tiles_x):
                    x = col * self.app.tile_size
                    y = row * self.app.tile_size
                    tile_img = padded_image.crop((x, y, x + self.app.tile_size, y + self.app.tile_size))
                    
                    filename = f"{image_name}_tile_{row}_{col}.png"
                    
                    if tile_index in selected_tiles:
                        # Export to selected folder
                        path = os.path.join(folder, filename)
                        try:
                            tile_img.save(path)
                            exported_selected += 1
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to save {filename}: {e}")
                    else:
                        # Export to unselected folder
                        path = os.path.join(no_folder, filename)
                        try:
                            tile_img.save(path)
                            exported_unselected += 1
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to save {filename}: {e}")
                    
                    tile_index += 1
        
        messagebox.showinfo("Classification Export Complete", 
                          f"Exported {exported_selected} selected tiles to:\n{folder}\n\n"
                          f"Exported {exported_unselected} unselected tiles to:\n{no_folder}")
        self.app.update_status(f"Classification export: {exported_selected} selected, {exported_unselected} unselected")
