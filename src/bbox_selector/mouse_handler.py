"""
Mouse Handler Module
Manages mouse events for bbox and polygon interactions
"""


class MouseHandler:
    """Handles mouse events for shape creation and editing"""
    
    def __init__(self, app):
        self.app = app
        
    def bind_events(self):
        """Bind all mouse events to canvas"""
        self.app.canvas.bind("<Button-1>", self.on_canvas_click)
        self.app.canvas.bind("<Button-3>", self.on_right_click)
        self.app.canvas.bind("<Motion>", self.on_mouse_move)
        self.app.canvas.bind("<B1-Motion>", self.on_drag)
        self.app.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.app.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.app.canvas.focus_set()
        
        # Bind mouse wheel for scrolling and zoom
        self.app.canvas.bind("<MouseWheel>", self.app.canvas_handler.on_mouse_wheel)
        self.app.canvas.bind("<Control-MouseWheel>", self.app.canvas_handler.on_ctrl_mouse_wheel)
        self.app.canvas.bind("<Shift-MouseWheel>", self.app.canvas_handler.on_shift_mouse_wheel)
        
        # Bind middle mouse button for drag scrolling
        self.app.canvas.bind("<Button-2>", self.app.canvas_handler.on_pan_start)
        self.app.canvas.bind("<B2-Motion>", self.app.canvas_handler.on_pan_motion)
        
    def on_canvas_click(self, event):
        """Handle left click on canvas"""
        if not self.app.image:
            return
        
        # Get click position in image coordinates
        canvas_x = self.app.canvas.canvasx(event.x)
        canvas_y = self.app.canvas.canvasy(event.y)
        image_x = int((canvas_x - self.app.image_offset_x) / self.app.zoom_level)
        image_y = int((canvas_y - self.app.image_offset_y) / self.app.zoom_level)
        
        # Check if click is within image bounds
        if image_x < 0 or image_y < 0 or image_x >= self.app.image.width or image_y >= self.app.image.height:
            return
        
        # Polygon mode
        if self.app.custom_select_mode.get():
            self.app.polygon_points.append((image_x, image_y))
            self.app.canvas_handler.display_image_on_canvas()
            self.app.update_status(f"Point {len(self.app.polygon_points)} added | Right-click to complete polygon")
            return
        
        # Check if clicking on existing shape
        clicked_bbox = self._get_bbox_at_position(image_x, image_y)
        clicked_polygon = self._get_polygon_at_position(canvas_x, canvas_y)
        
        if clicked_bbox:
            self.app.selected_bbox = clicked_bbox
            self.app.selected_polygon = None
            self.app.canvas_handler.display_image_on_canvas()
            self.app.update_status(f"Selected bbox #{clicked_bbox['id']} | Size: {clicked_bbox['width']}x{clicked_bbox['height']}")
            return
        
        if clicked_polygon:
            self.app.selected_polygon = clicked_polygon
            self.app.selected_bbox = None
            self.app.canvas_handler.display_image_on_canvas()
            self.app.update_status(f"Selected polygon #{clicked_polygon['id']}")
            return
        
        # Create new bbox
        self.app.bbox_counter += 1
        half_width = self.app.bbox_width // 2
        half_height = self.app.bbox_height // 2
        
        bbox = {
            'id': self.app.bbox_counter,
            'x': max(0, image_x - half_width),
            'y': max(0, image_y - half_height),
            'width': self.app.bbox_width,
            'height': self.app.bbox_height,
            'rect_id': None,
            'text_id': None
        }
        
        # Ensure bbox stays within image bounds
        if bbox['x'] + bbox['width'] > self.app.image.width:
            bbox['x'] = self.app.image.width - bbox['width']
        if bbox['y'] + bbox['height'] > self.app.image.height:
            bbox['y'] = self.app.image.height - bbox['height']
        
        self.app.bboxes.append(bbox)
        self.app.selected_bbox = bbox
        self.app.canvas_handler.display_image_on_canvas()
        self.app.update_status(f"BBox #{bbox['id']} created at ({bbox['x']}, {bbox['y']}) | Total: {len(self.app.bboxes)} bboxes")
    
    def on_right_click(self, event):
        """Handle right click - complete polygon"""
        if self.app.custom_select_mode.get() and len(self.app.polygon_points) >= 3:
            self.app.shape_manager.complete_polygon()
    
    def on_mouse_move(self, event):
        """Handle mouse movement for hover effects"""
        if not self.app.image or self.app.dragging:
            return
        
        canvas_x = self.app.canvas.canvasx(event.x)
        canvas_y = self.app.canvas.canvasy(event.y)
        image_x = int((canvas_x - self.app.image_offset_x) / self.app.zoom_level)
        image_y = int((canvas_y - self.app.image_offset_y) / self.app.zoom_level)
        
        # Check for bbox hover
        hovered = self._get_bbox_at_position(image_x, image_y)
        if hovered != self.app.hovered_bbox:
            self.app.hovered_bbox = hovered
            self.app.canvas_handler.display_image_on_canvas()
    
    def on_drag(self, event):
        """Handle dragging for bbox resize"""
        if not self.app.selected_bbox or not self.app.image:
            return
        
        canvas_x = self.app.canvas.canvasx(event.x)
        canvas_y = self.app.canvas.canvasy(event.y)
        image_x = int((canvas_x - self.app.image_offset_x) / self.app.zoom_level)
        image_y = int((canvas_y - self.app.image_offset_y) / self.app.zoom_level)
        
        if not self.app.dragging:
            # Check if starting drag on handle
            self.app.drag_handle = self._get_handle_at_position(canvas_x, canvas_y)
            if self.app.drag_handle:
                self.app.dragging = True
                self.app.drag_start_x = image_x
                self.app.drag_start_y = image_y
        
        if self.app.dragging and self.app.drag_handle:
            bbox = self.app.selected_bbox
            dx = image_x - self.app.drag_start_x
            dy = image_y - self.app.drag_start_y
            
            # Resize based on handle
            if 'nw' in self.app.drag_handle:
                bbox['x'] += dx
                bbox['y'] += dy
                bbox['width'] -= dx
                bbox['height'] -= dy
            elif 'ne' in self.app.drag_handle:
                bbox['y'] += dy
                bbox['width'] += dx
                bbox['height'] -= dy
            elif 'sw' in self.app.drag_handle:
                bbox['x'] += dx
                bbox['width'] -= dx
                bbox['height'] += dy
            elif 'se' in self.app.drag_handle:
                bbox['width'] += dx
                bbox['height'] += dy
            
            # Ensure minimum size
            bbox['width'] = max(10, bbox['width'])
            bbox['height'] = max(10, bbox['height'])
            
            # Keep within image bounds
            bbox['x'] = max(0, min(bbox['x'], self.app.image.width - bbox['width']))
            bbox['y'] = max(0, min(bbox['y'], self.app.image.height - bbox['height']))
            
            self.app.drag_start_x = image_x
            self.app.drag_start_y = image_y
            self.app.canvas_handler.display_image_on_canvas()
    
    def on_release(self, event):
        """Handle mouse button release"""
        self.app.dragging = False
        self.app.drag_handle = None
    
    def on_double_click(self, event):
        """Handle double click - deselect"""
        self.app.selected_bbox = None
        self.app.selected_polygon = None
        self.app.canvas_handler.display_image_on_canvas()
        self.app.update_status("Deselected all shapes")
    
    def _get_bbox_at_position(self, x, y):
        """Get bbox at given position"""
        for bbox in reversed(self.app.bboxes):
            if (bbox['x'] <= x <= bbox['x'] + bbox['width'] and
                bbox['y'] <= y <= bbox['y'] + bbox['height']):
                return bbox
        return None
    
    def _get_polygon_at_position(self, canvas_x, canvas_y):
        """Get polygon at given canvas position"""
        for polygon in reversed(self.app.polygons):
            items = self.app.canvas.find_overlapping(canvas_x-2, canvas_y-2, canvas_x+2, canvas_y+2)
            for item in items:
                tags = self.app.canvas.gettags(item)
                if f"polygon_{polygon['id']}" in tags:
                    return polygon
        return None
    
    def _get_handle_at_position(self, canvas_x, canvas_y):
        """Get resize handle at given canvas position"""
        if not self.app.selected_bbox:
            return None
        
        items = self.app.canvas.find_overlapping(canvas_x-5, canvas_y-5, canvas_x+5, canvas_y+5)
        for item in items:
            tags = self.app.canvas.gettags(item)
            for tag in tags:
                if tag.startswith('handle_'):
                    return tag
        return None
