"""
Canvas Handler Module
Manages canvas display, zoom, and mouse interactions
"""
from PIL import ImageTk


class CanvasHandler:
    """Handles canvas display and interactions"""
    
    def __init__(self, app):
        self.app = app
        
    def display_image_on_canvas(self):
        """Display image on canvas with current zoom level"""
        if not self.app.image:
            return
        
        # Calculate zoomed dimensions
        zoomed_width = int(self.app.image.width * self.app.zoom_level)
        zoomed_height = int(self.app.image.height * self.app.zoom_level)
        
        # Resize image
        resized_image = self.app.image.resize((zoomed_width, zoomed_height), resample=1)
        self.app.display_image = ImageTk.PhotoImage(resized_image)
        
        # Clear canvas
        self.app.canvas.delete("all")
        
        # Calculate centering offsets
        canvas_width = self.app.canvas.winfo_width()
        canvas_height = self.app.canvas.winfo_height()
        x_offset = max((canvas_width - zoomed_width) // 2, 0)
        y_offset = max((canvas_height - zoomed_height) // 2, 0)
        
        self.app.image_offset_x = x_offset
        self.app.image_offset_y = y_offset
        
        # Display image
        self.app.canvas.create_image(x_offset, y_offset, anchor='nw', image=self.app.display_image)
        
        # Redraw shapes
        self.redraw_bboxes()
        
        # Update scroll region
        scroll_width = max(zoomed_width + 2 * x_offset, canvas_width)
        scroll_height = max(zoomed_height + 2 * y_offset, canvas_height)
        self.app.canvas.config(scrollregion=(0, 0, scroll_width, scroll_height))
        
        # Center the view
        self.app.canvas.xview_moveto((x_offset - 10) / scroll_width if scroll_width > canvas_width else 0)
        self.app.canvas.yview_moveto((y_offset - 10) / scroll_height if scroll_height > canvas_height else 0)

        # Update status with image info
        if len(self.app.images) > 1:
            self.app.update_status(f"Image {self.app.current_image_index + 1}/{len(self.app.images)}: {self.app.image_path.split('/')[-1] if self.app.image_path else ''} | "
                              f"Size: {self.app.image.size[0]}x{self.app.image.size[1]} | Zoom: {int(self.app.zoom_level * 100)}% | "
                              f"BBoxes: {len(self.app.bboxes)} | Polygons: {len(self.app.polygons)}")
        else:
            self.app.update_status(f"Loaded: {self.app.image_path.split('/')[-1] if self.app.image_path else ''} | Size: {self.app.image.size[0]}x{self.app.image.size[1]} | "
                              f"Zoom: {int(self.app.zoom_level * 100)}% | BBoxes: {len(self.app.bboxes)} | Polygons: {len(self.app.polygons)}")

    def redraw_bboxes(self):
        """Redraw all bboxes and polygons with current zoom level"""
        # Draw polygon points and lines if in polygon mode
        if self.app.custom_select_mode.get() and self.app.polygon_points:
            for i in range(len(self.app.polygon_points)):
                x1 = self.app.image_offset_x + int(self.app.polygon_points[i][0] * self.app.zoom_level)
                y1 = self.app.image_offset_y + int(self.app.polygon_points[i][1] * self.app.zoom_level)
                
                # Draw point
                self.app.canvas.create_oval(x1-4, y1-4, x1+4, y1+4, fill="#00ff00", outline="white", width=2)
                
                # Draw line to next point
                if i < len(self.app.polygon_points) - 1:
                    x2 = self.app.image_offset_x + int(self.app.polygon_points[i+1][0] * self.app.zoom_level)
                    y2 = self.app.image_offset_y + int(self.app.polygon_points[i+1][1] * self.app.zoom_level)
                    self.app.canvas.create_line(x1, y1, x2, y2, fill="#00ff00", width=2)
            
            # Draw closing line
            if len(self.app.polygon_points) > 2:
                x1 = self.app.image_offset_x + int(self.app.polygon_points[-1][0] * self.app.zoom_level)
                y1 = self.app.image_offset_y + int(self.app.polygon_points[-1][1] * self.app.zoom_level)
                x2 = self.app.image_offset_x + int(self.app.polygon_points[0][0] * self.app.zoom_level)
                y2 = self.app.image_offset_y + int(self.app.polygon_points[0][1] * self.app.zoom_level)
                self.app.canvas.create_line(x1, y1, x2, y2, fill="#00ff00", width=2, dash=(5, 5))
        
        # Draw completed polygons
        for polygon in self.app.polygons:
            points = polygon['points']
            if len(points) >= 3:
                canvas_points = []
                for x, y in points:
                    canvas_x = self.app.image_offset_x + int(x * self.app.zoom_level)
                    canvas_y = self.app.image_offset_y + int(y * self.app.zoom_level)
                    canvas_points.extend([canvas_x, canvas_y])
                
                is_selected = self.app.selected_polygon and self.app.selected_polygon['id'] == polygon['id']
                outline_color = "#ffcc00" if is_selected else "#00ffff"
                text_color = "#ffcc00" if is_selected else "#00ffff"
                line_width = 3 if is_selected else 2
                
                # Draw polygon outline
                self.app.canvas.create_polygon(canvas_points, outline=outline_color, fill="", width=line_width, tags=f"polygon_{polygon['id']}")
                
                # Draw label
                if canvas_points:
                    label_text = f"P#{polygon['id']}" + (" [SELECTED]" if is_selected else "")
                    self.app.canvas.create_text(canvas_points[0] + 5, canvas_points[1] + 5, 
                                          text=label_text, fill=text_color, 
                                          font=('Segoe UI', self.app.base_font_size, 'bold'), anchor='nw', tags=f"polygon_{polygon['id']}")
        
        # Draw bboxes
        for bbox in self.app.bboxes:
            x1 = self.app.image_offset_x + int(bbox['x'] * self.app.zoom_level)
            y1 = self.app.image_offset_y + int(bbox['y'] * self.app.zoom_level)
            x2 = x1 + int(bbox['width'] * self.app.zoom_level)
            y2 = y1 + int(bbox['height'] * self.app.zoom_level)
            
            is_selected = self.app.selected_bbox and self.app.selected_bbox['id'] == bbox['id']
            is_hovered = self.app.hovered_bbox and self.app.hovered_bbox['id'] == bbox['id']
            
            outline_color = "#ffcc00" if is_selected else ("#00ff00" if is_hovered else "#ff0000")
            text_color = "#ffcc00" if is_selected else "#ff0000"
            line_width = 3 if is_selected else (2 if is_hovered else 2)
            
            # Draw rectangle
            rect_id = self.app.canvas.create_rectangle(x1, y1, x2, y2, outline=outline_color, width=line_width, 
                                                   fill="", tags=f"bbox_{bbox['id']}")
            
            # Draw label
            label_text = f"#{bbox['id']}"
            if is_selected:
                label_text += " [SELECTED]"
            text_id = self.app.canvas.create_text(x1 + 5, y1 + 5, text=label_text, fill=text_color, 
                                             font=('Segoe UI', self.app.base_font_size, 'bold'), anchor='nw', tags=f"bbox_{bbox['id']}")
            
            bbox['rect_id'] = rect_id
            bbox['text_id'] = text_id
            
            # Draw resize handles for selected bbox
            if is_selected:
                handle_size = 10
                # Corner handles
                self.app.canvas.create_rectangle(x1-handle_size//2, y1-handle_size//2, x1+handle_size//2, y1+handle_size//2, 
                                            fill="#ffcc00", outline="white", width=2, tags=f"handle_nw_{bbox['id']}")
                self.app.canvas.create_rectangle(x2-handle_size//2, y1-handle_size//2, x2+handle_size//2, y1+handle_size//2, 
                                            fill="#ffcc00", outline="white", width=2, tags=f"handle_ne_{bbox['id']}")
                self.app.canvas.create_rectangle(x1-handle_size//2, y2-handle_size//2, x1+handle_size//2, y2+handle_size//2, 
                                            fill="#ffcc00", outline="white", width=2, tags=f"handle_sw_{bbox['id']}")
                self.app.canvas.create_rectangle(x2-handle_size//2, y2-handle_size//2, x2+handle_size//2, y2+handle_size//2, 
                                            fill="#ffcc00", outline="white", width=2, tags=f"handle_se_{bbox['id']}")
    
    def zoom_in(self):
        """Zoom in by 20%"""
        if self.app.zoom_level < self.app.max_zoom:
            self.app.zoom_level = min(self.app.zoom_level * 1.2, self.app.max_zoom)
            self.app.zoom_label.config(text=f"{int(self.app.zoom_level * 100)}%")
            self.display_image_on_canvas()
    
    def zoom_out(self):
        """Zoom out by 20%"""
        if self.app.zoom_level > self.app.min_zoom:
            self.app.zoom_level = max(self.app.zoom_level / 1.2, self.app.min_zoom)
            self.app.zoom_label.config(text=f"{int(self.app.zoom_level * 100)}%")
            self.display_image_on_canvas()
    
    def zoom_reset(self):
        """Reset zoom to 100%"""
        self.app.zoom_level = 1.0
        self.app.zoom_label.config(text="100%")
        self.display_image_on_canvas()
    
    def on_mouse_wheel(self, event):
        """Handle vertical scrolling"""
        self.app.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def on_ctrl_mouse_wheel(self, event):
        """Handle zoom with Ctrl+MouseWheel"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def on_shift_mouse_wheel(self, event):
        """Handle horizontal scrolling"""
        self.app.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
    
    def on_pan_start(self, event):
        """Start drag scrolling"""
        self.app.canvas.scan_mark(event.x, event.y)
    
    def on_pan_motion(self, event):
        """Handle drag scrolling motion"""
        self.app.canvas.scan_dragto(event.x, event.y, gain=1)
