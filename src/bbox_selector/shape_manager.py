"""
Shape Manager Module
Handles bbox and polygon creation, editing, and export operations
"""
import os
import json
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw


class ShapeManager:
    """Manages bbox and polygon operations"""
    
    def __init__(self, app):
        self.app = app
        
    def save_current_annotations(self):
        """Save current image annotations before switching"""
        if self.app.image_path:
            self.app.image_annotations[self.app.image_path] = {
                'bboxes': self.app.bboxes.copy(),
                'polygons': self.app.polygons.copy(),
                'bbox_counter': self.app.bbox_counter,
                'polygon_counter': self.app.polygon_counter
            }
    
    def validate_bbox_size(self, event=None):
        """Validate bbox size inputs"""
        try:
            width = int(self.app.bbox_width_var.get())
            height = int(self.app.bbox_height_var.get())
            if width <= 0 or height <= 0:
                raise ValueError
            self.app.bbox_width = width
            self.app.bbox_height = height
        except ValueError:
            messagebox.showerror("Error", "BBox dimensions must be positive integers.")
    
    def apply_size_to_selected(self):
        """Apply current size to selected bbox"""
        if not self.app.selected_bbox:
            messagebox.showwarning("Warning", "No bbox selected.")
            return
        
        self.validate_bbox_size()
        self.app.selected_bbox['width'] = self.app.bbox_width
        self.app.selected_bbox['height'] = self.app.bbox_height
        self.app.canvas_handler.display_image_on_canvas(preserve_view=True)
        self.app.update_status(f"Applied size {self.app.bbox_width}x{self.app.bbox_height} to bbox #{self.app.selected_bbox['id']}")
    
    def delete_selected_shape(self):
        """Delete the currently selected bbox or polygon"""
        if self.app.selected_bbox:
            self.app.bboxes = [b for b in self.app.bboxes if b['id'] != self.app.selected_bbox['id']]
            self.app.selected_bbox = None
            self.app.canvas_handler.display_image_on_canvas(preserve_view=True)
            self.app.update_status(f"Deleted bbox | Remaining: {len(self.app.bboxes)} bboxes, {len(self.app.polygons)} polygons")
        elif self.app.selected_polygon:
            self.app.polygons = [p for p in self.app.polygons if p['id'] != self.app.selected_polygon['id']]
            self.app.selected_polygon = None
            self.app.canvas_handler.display_image_on_canvas(preserve_view=True)
            self.app.update_status(f"Deleted polygon | Remaining: {len(self.app.bboxes)} bboxes, {len(self.app.polygons)} polygons")
        else:
            messagebox.showwarning("Warning", "No shape selected to delete.")
    
    def clear_all_shapes(self):
        """Clear all bboxes and polygons"""
        total = len(self.app.bboxes) + len(self.app.polygons)
        if total == 0:
            return
        
        result = messagebox.askyesno("Confirm", f"Clear all {len(self.app.bboxes)} bboxes and {len(self.app.polygons)} polygons?")
        if result:
            self.app.bboxes = []
            self.app.bbox_counter = 0
            self.app.selected_bbox = None
            self.app.polygons = []
            self.app.polygon_counter = 0
            self.app.selected_polygon = None
            self.app.canvas_handler.display_image_on_canvas(preserve_view=True)
            self.app.update_status(f"All shapes cleared | Image {self.app.current_image_index + 1}/{len(self.app.images)}: {os.path.basename(self.app.image_path) if self.app.image_path else 'No image'}")
    
    def export_bboxes(self):
        """Export all bbox regions as separate images"""
        if not self.app.image:
            messagebox.showwarning("Warning", "No image loaded.")
            return
        
        if not self.app.bboxes:
            messagebox.showwarning("Warning", "No bboxes to export.")
            return
        
        folder = filedialog.askdirectory(title="Select Export Folder")
        if not folder:
            return
        
        image_name = os.path.splitext(os.path.basename(self.app.image_path))[0]
        exported = 0
        
        for bbox in self.app.bboxes:
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            cropped = self.app.image.crop((x, y, x + w, y + h))
            filename = f"{image_name}_bbox_{bbox['id']}.png"
            filepath = os.path.join(folder, filename)
            try:
                cropped.save(filepath)
                exported += 1
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save {filename}: {e}")
        
        messagebox.showinfo("Export Complete", f"Exported {exported} bboxes to:\n{folder}")
        self.app.update_status(f"Exported {exported} bboxes successfully")
    
    def save_all_shapes(self):
        """Save all shapes (bboxes and polygons) from all images as images and JSON with augmentation"""
        # Save current image annotations first
        self.save_current_annotations()
        
        # Check if there are any annotations across all images
        total_images_with_annotations = 0
        for path in self.app.image_annotations:
            if self.app.image_annotations[path]['bboxes'] or self.app.image_annotations[path]['polygons']:
                total_images_with_annotations += 1
        
        if total_images_with_annotations == 0:
            messagebox.showwarning("Warning", "No shapes to save across all images.")
            return
        
        # Ask if user wants to apply augmentation
        augment_count = self.app.augmentor.get_augmentation_count()
        if augment_count > 1:
            result = messagebox.askyesno("Apply Augmentation?", 
                                        f"Apply augmentation during export?\n\n"
                                        f"Each bbox will generate {augment_count}x images.\n"
                                        f"(Configure in 🎨 Augment settings)")
            apply_augmentation = result
        else:
            apply_augmentation = False
        
        folder = filedialog.askdirectory(title="Select Save Folder")
        if not folder:
            return
        
        # Get export format
        export_format = self.app.export_format.get()
        
        total_bboxes = 0
        total_polygons = 0
        
        # Prepare data for format exporters
        images_data = {}
        
        # Process each image with annotations
        for image_path, annotations in self.app.image_annotations.items():
            bboxes = annotations['bboxes']
            polygons = annotations['polygons']
            
            if not bboxes and not polygons:
                continue
            
            # Load the image
            try:
                img = Image.open(image_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load {image_path}: {e}")
                continue
            
            image_name = os.path.splitext(os.path.basename(image_path))[0]
            
            # Prepare JSON data for this image
            json_data = {
                "image": os.path.basename(image_path),
                "image_width": img.width,
                "image_height": img.height,
                "bboxes": [],
                "polygons": []
            }
            
            # Export bboxes
            for bbox in bboxes:
                x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
                cropped = img.crop((x, y, x + w, y + h))
                
                # Apply augmentation if enabled
                if apply_augmentation:
                    # Create a simple bbox for the cropped image (covers entire cropped area)
                    cropped_bbox = {
                        'id': bbox['id'],
                        'x': 0,
                        'y': 0,
                        'width': w,
                        'height': h,
                        'class': bbox.get('class', 'Class 1'),
                        'class_color': bbox.get('class_color', '#00ff00')
                    }
                    
                    augmented_images = self.app.augmentor.apply_augmentations(cropped, cropped_bbox)
                    for aug_img, aug_name, aug_bbox in augmented_images:
                        filename = f"{image_name}_bbox_{bbox['id']}_{aug_name}.png"
                        filepath = os.path.join(folder, filename)
                        aug_img.save(filepath)
                        
                        # Add augmented bbox to JSON with updated coordinates
                        if aug_bbox:
                            json_data["bboxes"].append({
                                "id": f"{bbox['id']}_{aug_name}",
                                "x": aug_bbox['x'],
                                "y": aug_bbox['y'],
                                "width": aug_bbox['width'],
                                "height": aug_bbox['height'],
                                "class": aug_bbox.get('class', 'Class 1'),
                                "class_color": aug_bbox.get('class_color', '#00ff00'),
                                "augmentation": aug_name,
                                "original_id": bbox['id']
                            })
                        
                        total_bboxes += 1
                else:
                    # Original bbox without augmentation
                    json_data["bboxes"].append({
                        "id": bbox['id'],
                        "x": bbox['x'],
                        "y": bbox['y'],
                        "width": bbox['width'],
                        "height": bbox['height'],
                        "class": bbox.get('class', 'Class 1'),
                        "class_color": bbox.get('class_color', '#00ff00')
                    })
                    
                    filename = f"{image_name}_bbox_{bbox['id']}.png"
                    filepath = os.path.join(folder, filename)
                    cropped.save(filepath)
                    total_bboxes += 1
            
            # Export polygons
            for polygon in polygons:
                points = polygon['points']
                
                json_data["polygons"].append({
                    "id": polygon['id'],
                    "points": points,
                    "class": polygon.get('class', 'Class 1'),
                    "class_color": polygon.get('class_color', '#00ff00')
                })
                
                # Find bounding box of polygon
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                
                # Add padding
                padding = 5
                min_x = max(0, min_x - padding)
                min_y = max(0, min_y - padding)
                max_x = min(img.width, max_x + padding)
                max_y = min(img.height, max_y + padding)
                
                width = max_x - min_x
                height = max_y - min_y
                
                # Create mask
                mask = Image.new('L', (width, height), 0)
                mask_draw = ImageDraw.Draw(mask)
                adjusted_points = [(x - min_x, y - min_y) for x, y in points]
                mask_draw.polygon(adjusted_points, fill=255)
                
                # Crop and apply mask
                cropped = img.crop((min_x, min_y, max_x, max_y))
                output = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                output.paste(cropped, (0, 0))
                output.putalpha(mask)
                
                # Save polygon image
                filename = f"{image_name}_polygon_{polygon['id']}.png"
                filepath = os.path.join(folder, filename)
                output.save(filepath)
                total_polygons += 1
            
            # Store image data for format exporters
            images_data[image_path] = {
                'image_width': img.width,
                'image_height': img.height,
                'bboxes': bboxes,
                'polygons': polygons
            }
            
            # Save individual JSON file for this image (for JSON format)
            if export_format == 'JSON':
                json_filename = f"{image_name}_annotations.json"
                json_filepath = os.path.join(folder, json_filename)
                with open(json_filepath, 'w') as f:
                    json.dump(json_data, f, indent=2)
        
        # Export in selected format
        format_output = None
        if export_format == 'COCO':
            format_output = self.app.export_formatter.export_coco(images_data, folder)
            format_msg = f"COCO format: {format_output}"
        elif export_format == 'VOC':
            format_output = self.app.export_formatter.export_voc(images_data, folder)
            format_msg = f"VOC format: {format_output}"
        elif export_format == 'YOLO':
            # Get unique class names
            class_names = list(set([cls['name'] for cls in self.app.classes]))
            format_output = self.app.export_formatter.export_yolo(images_data, folder, class_names)
            format_msg = f"YOLO format: {format_output}"
        else:
            format_msg = "JSON format (individual files)"
        
        messagebox.showinfo("Save Complete", 
                          f"Saved annotations from {total_images_with_annotations} image(s):\n"
                          f"- {total_bboxes} bboxes\n"
                          f"- {total_polygons} polygons\n\n"
                          f"Format: {export_format}\n"
                          f"{format_msg}\n\n"
                          f"Location: {folder}")
        self.app.update_status(f"Saved {total_bboxes} bboxes and {total_polygons} polygons in {export_format} format")
    
    def toggle_custom_select(self):
        """Toggle polygon selection mode"""
        if self.app.custom_select_mode.get():
            self.app.update_status("Polygon mode enabled | Click to add points, Right-click to complete")
            self.app.canvas.config(cursor="crosshair")
        else:
            self.app.polygon_points = []
            self.app.update_status("BBox mode enabled | Click to place bboxes")
            self.app.canvas.config(cursor="crosshair")
            self.app.canvas_handler.display_image_on_canvas(preserve_view=True)
    
    def complete_polygon(self):
        """Complete and save the current polygon"""
        if len(self.app.polygon_points) < 3:
            messagebox.showwarning("Warning", "A polygon needs at least 3 points.")
            return
        
        self.app.polygon_counter += 1
        
        # Get current class
        current_class = self.app.classes[self.app.current_class_index]
        
        polygon = {
            'id': self.app.polygon_counter,
            'points': self.app.polygon_points.copy(),
            'class': current_class['name'],
            'class_color': current_class['color']
        }
        self.app.polygons.append(polygon)
        
        # Clear current points
        self.app.polygon_points = []
        self.app.canvas_handler.display_image_on_canvas(preserve_view=True)
        self.app.update_status(f"Polygon #{self.app.polygon_counter} created | Total: {len(self.app.polygons)} polygons")
