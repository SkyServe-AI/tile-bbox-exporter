"""
Canvas Handler Module for Tile Selector
Manages canvas display, zoom, and tile rendering
"""
from PIL import ImageTk


class CanvasHandler:
    """Handles canvas display and interactions"""
    
    def __init__(self, app):
        self.app = app
        
    def display_grid(self):
        """Display tile grid on canvas"""
        self.app.canvas.delete("all")
        if not hasattr(self.app, 'current_padded_image') or not self.app.current_padded_image:
            return
        
        # Calculate zoomed dimensions
        padded_width = self.app.current_padded_image.width
        padded_height = self.app.current_padded_image.height
        zoomed_width = int(padded_width * self.app.zoom_level)
        zoomed_height = int(padded_height * self.app.zoom_level)
        
        # Resize padded image for display
        display_image = self.app.current_padded_image.resize((zoomed_width, zoomed_height), resample=1)
        self.app.display_image_tk = ImageTk.PhotoImage(display_image)
        
        # Display image
        self.app.canvas.create_image(0, 0, anchor='nw', image=self.app.display_image_tk)
        
        # Draw grid lines and tile overlays
        tile_size_zoomed = int(self.app.tile_size * self.app.zoom_level)
        
        for i, tile in enumerate(self.app.tiles):
            x = int(tile['x'] * self.app.zoom_level)
            y = int(tile['y'] * self.app.zoom_level)
            x2 = x + tile_size_zoomed
            y2 = y + tile_size_zoomed
            
            # Draw grid lines
            self.app.canvas.create_rectangle(x, y, x2, y2, outline="#555555", width=1, tags=f"tile_{i}")
            
            # Highlight selected tiles
            if i in self.app.selected_tiles:
                self.app.canvas.create_rectangle(x, y, x2, y2, outline="#00ff00", width=3, tags=f"tile_{i}")
                # Add semi-transparent overlay
                self.app.canvas.create_rectangle(x, y, x2, y2, fill="#00ff00", stipple="gray50", tags=f"tile_{i}")
                # Add checkmark
                center_x = (x + x2) // 2
                center_y = (y + y2) // 2
                self.app.canvas.create_text(center_x, center_y, text="✓", fill="#00ff00", 
                                           font=('Arial', int(20 * self.app.zoom_level), 'bold'), tags=f"tile_{i}")
        
        # Update scroll region
        self.app.canvas.config(scrollregion=(0, 0, zoomed_width, zoomed_height))
        
        self.app.update_status(f"Image {self.app.current_image_index + 1}/{len(self.app.images)} | {len(self.app.tiles)} tiles | Zoom: {int(self.app.zoom_level * 100)}% | {len(self.app.selected_tiles)} selected")

    def zoom_in(self):
        """Zoom in by 20%"""
        if self.app.zoom_level < self.app.max_zoom:
            # Get current center position
            x_center = (self.app.canvas.canvasx(0) + self.app.canvas.canvasx(self.app.canvas.winfo_width())) / 2
            y_center = (self.app.canvas.canvasy(0) + self.app.canvas.canvasy(self.app.canvas.winfo_height())) / 2
            
            old_zoom = self.app.zoom_level
            self.app.zoom_level = min(self.app.zoom_level * 1.2, self.app.max_zoom)
            self.app.zoom_label.config(text=f"{int(self.app.zoom_level * 100)}%")
            self.display_grid()
            
            # Recenter on the same point
            zoom_ratio = self.app.zoom_level / old_zoom
            new_x_center = x_center * zoom_ratio
            new_y_center = y_center * zoom_ratio
            self.app.canvas.xview_moveto((new_x_center - self.app.canvas.winfo_width() / 2) / (self.app.current_padded_image.width * self.app.zoom_level))
            self.app.canvas.yview_moveto((new_y_center - self.app.canvas.winfo_height() / 2) / (self.app.current_padded_image.height * self.app.zoom_level))
    
    def zoom_out(self):
        """Zoom out by 20%"""
        if self.app.zoom_level > self.app.min_zoom:
            # Get current center position
            x_center = (self.app.canvas.canvasx(0) + self.app.canvas.canvasx(self.app.canvas.winfo_width())) / 2
            y_center = (self.app.canvas.canvasy(0) + self.app.canvas.canvasy(self.app.canvas.winfo_height())) / 2
            
            old_zoom = self.app.zoom_level
            self.app.zoom_level = max(self.app.zoom_level / 1.2, self.app.min_zoom)
            self.app.zoom_label.config(text=f"{int(self.app.zoom_level * 100)}%")
            self.display_grid()
            
            # Recenter on the same point
            zoom_ratio = self.app.zoom_level / old_zoom
            new_x_center = x_center * zoom_ratio
            new_y_center = y_center * zoom_ratio
            self.app.canvas.xview_moveto((new_x_center - self.app.canvas.winfo_width() / 2) / (self.app.current_padded_image.width * self.app.zoom_level))
            self.app.canvas.yview_moveto((new_y_center - self.app.canvas.winfo_height() / 2) / (self.app.current_padded_image.height * self.app.zoom_level))
    
    def zoom_reset(self):
        """Reset zoom to 100%"""
        self.app.zoom_level = 1.0
        self.app.zoom_label.config(text="100%")
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
            self.app.canvas.xview_scroll(-1, "units")
        else:
            self.app.canvas.xview_scroll(1, "units")
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling (touchpad two-finger scroll)"""
        if event.delta > 0:
            self.app.canvas.yview_scroll(-1, "units")
        else:
            self.app.canvas.yview_scroll(1, "units")
    
    def on_drag_start(self, event):
        """Start drag scrolling with middle mouse button"""
        self.app.canvas.scan_mark(event.x, event.y)
        self.app.drag_start_x = event.x
        self.app.drag_start_y = event.y
    
    def on_drag_motion(self, event):
        """Handle drag scrolling motion"""
        self.app.canvas.scan_dragto(event.x, event.y, gain=1)
    
    def on_canvas_click(self, event):
        """Handle canvas click to select/deselect tiles"""
        x, y = self.app.canvas.canvasx(event.x), self.app.canvas.canvasy(event.y)
        
        # Calculate which tile was clicked based on position
        tile_size_zoomed = int(self.app.tile_size * self.app.zoom_level)
        
        # Find the tile by calculating grid position
        for i, tile in enumerate(self.app.tiles):
            tile_x = int(tile['x'] * self.app.zoom_level)
            tile_y = int(tile['y'] * self.app.zoom_level)
            tile_x2 = tile_x + tile_size_zoomed
            tile_y2 = tile_y + tile_size_zoomed
            
            # Check if click is within this tile's bounds
            if tile_x <= x <= tile_x2 and tile_y <= y <= tile_y2:
                # Toggle selection
                if i in self.app.selected_tiles:
                    self.app.selected_tiles.remove(i)
                    self.app.tiles[i]['selected'] = False
                else:
                    self.app.selected_tiles.add(i)
                    self.app.tiles[i]['selected'] = True
                
                self.display_grid()
                self.app.update_status(f"Displaying {len(self.app.tiles)} tiles | Zoom: {int(self.app.zoom_level * 100)}% | {len(self.app.selected_tiles)} selected")
                return  # Exit after handling the clicked tile
