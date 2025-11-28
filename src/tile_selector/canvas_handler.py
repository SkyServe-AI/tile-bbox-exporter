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
            
            # If classified, show category color overlay (only if overlay is visible)
            if (hasattr(self.app, 'tile_classifications') and self.app.tile_classifications and 
                hasattr(self.app, 'overlay_visible') and self.app.overlay_visible):
                if i < len(self.app.tile_classifications):
                    category = self.app.tile_classifications[i]
                    if category and category != 'Cloud':
                        from .lulc_classifier import LULCClassifier
                        color = LULCClassifier.CATEGORY_COLORS.get(category, '#FFFFFF')
                        
                        # Check if hand tool is active and this tile is being hovered
                        if self.app.hand_tool_active and self.app.hover_tile_index == i:
                            # Make overlay more transparent for hovered tile
                            self.app.canvas.create_rectangle(x, y, x2, y2, outline=color, width=2, tags=f"tile_{i}")
                        else:
                            # Draw colored overlay with normal transparency
                            self.app.canvas.create_rectangle(x, y, x2, y2, outline=color, width=3, tags=f"tile_{i}")
                            self.app.canvas.create_rectangle(x, y, x2, y2, fill=color, stipple="gray25", tags=f"tile_{i}")
            
            # Highlight selected tiles (for manual adjustment or batch category assignment)
            selected_set = self.app.selected_tiles_for_category if (hasattr(self.app, 'tile_classifications') and self.app.tile_classifications) else self.app.selected_tiles
            
            if i in selected_set:
                self.app.canvas.create_rectangle(x, y, x2, y2, outline="#00ff00", width=3, tags=f"tile_{i}")
                # Add semi-transparent overlay
                self.app.canvas.create_rectangle(x, y, x2, y2, stipple="gray50", tags=f"tile_{i}")
                # Add checkmark
                center_x = (x + x2) // 2
                center_y = (y + y2) // 2
                self.app.canvas.create_text(center_x, center_y, text="✓",  
                                           font=('Arial', int(20 * self.app.zoom_level), 'bold'), tags=f"tile_{i}")
        
        # Update scroll region
        self.app.canvas.config(scrollregion=(0, 0, zoomed_width, zoomed_height))
        
        status_msg = f"Image {self.app.current_image_index + 1}/{len(self.app.images)} | {len(self.app.tiles)} tiles | Zoom: {int(self.app.zoom_level * 100)}%"
        if hasattr(self.app, 'tile_classifications') and self.app.tile_classifications:
            status_msg += " | Classified"
        self.app.update_status(status_msg)

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
        """Handle canvas click to start tile selection"""
        x, y = self.app.canvas.canvasx(event.x), self.app.canvas.canvasy(event.y)
        
        # Start drag selection
        self.app.is_selecting = True
        
        # Find the tile at click position
        tile_index = self._get_tile_at_position(x, y)
        
        if tile_index is not None:
            # If classifications exist, use selected_tiles_for_category for batch assignment
            if hasattr(self.app, 'tile_classifications') and self.app.tile_classifications:
                if tile_index in self.app.selected_tiles_for_category:
                    self.app.selection_mode = 'remove'
                    self.app.selected_tiles_for_category.remove(tile_index)
                else:
                    self.app.selection_mode = 'add'
                    self.app.selected_tiles_for_category.add(tile_index)
            else:
                # Normal tile selection mode
                if tile_index in self.app.selected_tiles:
                    self.app.selection_mode = 'remove'
                    self.app.selected_tiles.remove(tile_index)
                    self.app.tiles[tile_index]['selected'] = False
                else:
                    self.app.selection_mode = 'add'
                    self.app.selected_tiles.add(tile_index)
                    self.app.tiles[tile_index]['selected'] = True
            
            self.display_grid()
            
            if hasattr(self.app, 'tile_classifications') and self.app.tile_classifications:
                self.app.update_status(f"Selected {len(self.app.selected_tiles_for_category)} tiles for batch category assignment | Right-click to assign category")
            else:
                self.app.update_status(f"Displaying {len(self.app.tiles)} tiles | Zoom: {int(self.app.zoom_level * 100)}% | {len(self.app.selected_tiles)} selected")
    
    def on_canvas_drag(self, event):
        """Handle canvas drag to select multiple tiles"""
        if not self.app.is_selecting or self.app.selection_mode is None:
            return
        
        x, y = self.app.canvas.canvasx(event.x), self.app.canvas.canvasy(event.y)
        
        # Find the tile at current position
        tile_index = self._get_tile_at_position(x, y)
        
        if tile_index is not None:
            # If classifications exist, use selected_tiles_for_category
            if hasattr(self.app, 'tile_classifications') and self.app.tile_classifications:
                if self.app.selection_mode == 'add':
                    if tile_index not in self.app.selected_tiles_for_category:
                        self.app.selected_tiles_for_category.add(tile_index)
                        self.display_grid()
                        self.app.update_status(f"Selected {len(self.app.selected_tiles_for_category)} tiles for batch category assignment")
                elif self.app.selection_mode == 'remove':
                    if tile_index in self.app.selected_tiles_for_category:
                        self.app.selected_tiles_for_category.remove(tile_index)
                        self.display_grid()
                        self.app.update_status(f"Selected {len(self.app.selected_tiles_for_category)} tiles for batch category assignment")
            else:
                # Normal selection mode
                if self.app.selection_mode == 'add':
                    if tile_index not in self.app.selected_tiles:
                        self.app.selected_tiles.add(tile_index)
                        self.app.tiles[tile_index]['selected'] = True
                        self.display_grid()
                        self.app.update_status(f"Displaying {len(self.app.tiles)} tiles | Zoom: {int(self.app.zoom_level * 100)}% | {len(self.app.selected_tiles)} selected")
                elif self.app.selection_mode == 'remove':
                    if tile_index in self.app.selected_tiles:
                        self.app.selected_tiles.remove(tile_index)
                        self.app.tiles[tile_index]['selected'] = False
                        self.display_grid()
                        self.app.update_status(f"Displaying {len(self.app.tiles)} tiles | Zoom: {int(self.app.zoom_level * 100)}% | {len(self.app.selected_tiles)} selected")
    
    def on_canvas_release(self, event):
        """Handle mouse button release to end selection"""
        self.app.is_selecting = False
        self.app.selection_mode = None
    
    def _get_tile_at_position(self, x, y):
        """Get tile index at given canvas position"""
        tile_size_zoomed = int(self.app.tile_size * self.app.zoom_level)
        
        for i, tile in enumerate(self.app.tiles):
            tile_x = int(tile['x'] * self.app.zoom_level)
            tile_y = int(tile['y'] * self.app.zoom_level)
            tile_x2 = tile_x + tile_size_zoomed
            tile_y2 = tile_y + tile_size_zoomed
            
            if tile_x <= x <= tile_x2 and tile_y <= y <= tile_y2:
                return i
        
        return None
    
    def on_right_click(self, event):
        """Handle right-click to change tile category"""
        if not hasattr(self.app, 'tile_classifications') or not self.app.tile_classifications:
            return
        
        # Check if there are selected tiles for batch assignment
        if len(self.app.selected_tiles_for_category) > 0:
            self._show_batch_category_menu(event)
        else:
            x, y = self.app.canvas.canvasx(event.x), self.app.canvas.canvasy(event.y)
            tile_index = self._get_tile_at_position(x, y)
            
            if tile_index is not None:
                self._show_category_menu(event, tile_index)
    
    def _show_category_menu(self, event, tile_index):
        """Show category selection menu for a tile"""
        import tkinter as tk
        from .lulc_classifier import LULCClassifier
        
        menu = tk.Menu(self.app.root, tearoff=0, bg="#2d2d2d", fg="white",
                      activebackground="#0e639c", activeforeground="white")
        
        current_category = self.app.tile_classifications[tile_index] if tile_index < len(self.app.tile_classifications) else None
        
        for category in LULCClassifier.CATEGORIES:
            color = LULCClassifier.CATEGORY_COLORS[category]
            label = f"● {category}"
            if category == current_category:
                label = f"✓ {label}"
            
            menu.add_command(
                label=label,
                command=lambda c=category, idx=tile_index: self._change_tile_category(idx, c),
                foreground=color
            )
        
        menu.add_separator()
        menu.add_command(
            label="Mark as Cloud",
            command=lambda idx=tile_index: self._change_tile_category(idx, 'Cloud')
        )
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _change_tile_category(self, tile_index, new_category):
        """Change the category of a specific tile"""
        if tile_index < len(self.app.tile_classifications):
            old_category = self.app.tile_classifications[tile_index]
            self.app.tile_classifications[tile_index] = new_category
            
            # Update category counts
            from collections import Counter
            from .lulc_classifier import LULCClassifier
            
            counts = Counter(self.app.tile_classifications)
            for category in LULCClassifier.CATEGORIES:
                count = counts.get(category, 0)
                if category in self.app.category_counts:
                    self.app.category_counts[category].config(text=f"{category}: {count}")
            
            # Refresh display
            self.app.display_grid()
            self.app.update_status(f"Changed tile category from {old_category} to {new_category}")
    
    def _show_batch_category_menu(self, event):
        """Show category selection menu for batch assignment"""
        import tkinter as tk
        from .lulc_classifier import LULCClassifier
        
        menu = tk.Menu(self.app.root, tearoff=0, bg="#2d2d2d", fg="white",
                      activebackground="#0e639c", activeforeground="white")
        
        menu.add_command(
            label=f"Assign category to {len(self.app.selected_tiles_for_category)} selected tiles:",
            state=tk.DISABLED
        )
        menu.add_separator()
        
        for category in LULCClassifier.CATEGORIES:
            color = LULCClassifier.CATEGORY_COLORS[category]
            label = f"● {category}"
            
            menu.add_command(
                label=label,
                command=lambda c=category: self._batch_assign_category(c),
                foreground=color
            )
        
        menu.add_separator()
        menu.add_command(
            label="Mark all as Cloud",
            command=lambda: self._batch_assign_category('Cloud')
        )
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _batch_assign_category(self, new_category):
        """Assign category to all selected tiles"""
        from collections import Counter
        from .lulc_classifier import LULCClassifier
        
        count = 0
        for tile_index in self.app.selected_tiles_for_category:
            if tile_index < len(self.app.tile_classifications):
                self.app.tile_classifications[tile_index] = new_category
                count += 1
        
        # Update category counts
        counts = Counter(self.app.tile_classifications)
        for category in LULCClassifier.CATEGORIES:
            cat_count = counts.get(category, 0)
            if category in self.app.category_counts:
                self.app.category_counts[category].config(text=f"{category}: {cat_count}")
        
        # Clear selection
        self.app.selected_tiles_for_category.clear()
        
        # Refresh display
        self.app.display_grid()
        self.app.update_status(f"Assigned {count} tiles to category: {new_category}")
    
    def on_mouse_motion(self, event):
        """Handle mouse motion for hand tool hover effect"""
        if not self.app.hand_tool_active:
            return
        
        if not hasattr(self.app, 'tile_classifications') or not self.app.tile_classifications:
            return
        
        x, y = self.app.canvas.canvasx(event.x), self.app.canvas.canvasy(event.y)
        tile_index = self._get_tile_at_position(x, y)
        
        # Only redraw if hover changed
        if tile_index != self.app.hover_tile_index:
            self.app.hover_tile_index = tile_index
            self.display_grid()
