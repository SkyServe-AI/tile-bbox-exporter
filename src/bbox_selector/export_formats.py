"""
Export Formats Module
Handles exporting annotations in COCO, VOC (Pascal VOC), and YOLO formats
"""
import json
import os
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom


class ExportFormatter:
    """Handles different annotation export formats"""
    
    def __init__(self):
        self.format_type = 'json'  # Default format
    
    def export_coco(self, images_data, output_folder):
        """
        Export annotations in COCO format
        COCO format structure:
        {
            "images": [...],
            "annotations": [...],
            "categories": [...]
        }
        """
        coco_data = {
            "info": {
                "description": "BBox Selector Annotations",
                "version": "1.0",
                "year": datetime.now().year,
                "date_created": datetime.now().isoformat()
            },
            "images": [],
            "annotations": [],
            "categories": []
        }
        
        # Build categories from unique classes
        categories_dict = {}
        category_id = 1
        
        annotation_id = 1
        
        for image_idx, (image_path, annotations) in enumerate(images_data.items(), start=1):
            img_width = annotations.get('image_width', 0)
            img_height = annotations.get('image_height', 0)
            
            # Add image info
            coco_data["images"].append({
                "id": image_idx,
                "file_name": os.path.basename(image_path),
                "width": img_width,
                "height": img_height
            })
            
            # Process bboxes
            for bbox in annotations.get('bboxes', []):
                class_name = bbox.get('class', 'Class 1')
                
                # Add category if not exists
                if class_name not in categories_dict:
                    categories_dict[class_name] = category_id
                    coco_data["categories"].append({
                        "id": category_id,
                        "name": class_name,
                        "supercategory": "object"
                    })
                    category_id += 1
                
                # COCO bbox format: [x, y, width, height]
                coco_data["annotations"].append({
                    "id": annotation_id,
                    "image_id": image_idx,
                    "category_id": categories_dict[class_name],
                    "bbox": [bbox['x'], bbox['y'], bbox['width'], bbox['height']],
                    "area": bbox['width'] * bbox['height'],
                    "iscrowd": 0
                })
                annotation_id += 1
            
            # Process polygons
            for polygon in annotations.get('polygons', []):
                class_name = polygon.get('class', 'Class 1')
                
                # Add category if not exists
                if class_name not in categories_dict:
                    categories_dict[class_name] = category_id
                    coco_data["categories"].append({
                        "id": category_id,
                        "name": class_name,
                        "supercategory": "object"
                    })
                    category_id += 1
                
                # Flatten polygon points for COCO format
                points = polygon['points']
                segmentation = []
                for x, y in points:
                    segmentation.extend([x, y])
                
                # Calculate bbox from polygon
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                x_min, x_max = min(xs), max(xs)
                y_min, y_max = min(ys), max(ys)
                width = x_max - x_min
                height = y_max - y_min
                
                coco_data["annotations"].append({
                    "id": annotation_id,
                    "image_id": image_idx,
                    "category_id": categories_dict[class_name],
                    "segmentation": [segmentation],
                    "bbox": [x_min, y_min, width, height],
                    "area": width * height,
                    "iscrowd": 0
                })
                annotation_id += 1
        
        # Save COCO JSON
        output_file = os.path.join(output_folder, "annotations_coco.json")
        with open(output_file, 'w') as f:
            json.dump(coco_data, f, indent=2)
        
        return output_file
    
    def export_voc(self, images_data, output_folder):
        """
        Export annotations in Pascal VOC XML format
        Creates one XML file per image
        """
        annotations_folder = os.path.join(output_folder, "Annotations")
        os.makedirs(annotations_folder, exist_ok=True)
        
        exported_files = []
        
        for image_path, annotations in images_data.items():
            img_width = annotations.get('image_width', 0)
            img_height = annotations.get('image_height', 0)
            image_filename = os.path.basename(image_path)
            
            # Create XML structure
            annotation = ET.Element('annotation')
            
            # Folder
            folder = ET.SubElement(annotation, 'folder')
            folder.text = 'images'
            
            # Filename
            filename = ET.SubElement(annotation, 'filename')
            filename.text = image_filename
            
            # Path
            path = ET.SubElement(annotation, 'path')
            path.text = image_path
            
            # Source
            source = ET.SubElement(annotation, 'source')
            database = ET.SubElement(source, 'database')
            database.text = 'BBox Selector'
            
            # Size
            size = ET.SubElement(annotation, 'size')
            width = ET.SubElement(size, 'width')
            width.text = str(img_width)
            height = ET.SubElement(size, 'height')
            height.text = str(img_height)
            depth = ET.SubElement(size, 'depth')
            depth.text = '3'
            
            # Segmented
            segmented = ET.SubElement(annotation, 'segmented')
            segmented.text = '0'
            
            # Add bboxes as objects
            for bbox in annotations.get('bboxes', []):
                obj = ET.SubElement(annotation, 'object')
                
                name = ET.SubElement(obj, 'name')
                name.text = bbox.get('class', 'Class 1')
                
                pose = ET.SubElement(obj, 'pose')
                pose.text = 'Unspecified'
                
                truncated = ET.SubElement(obj, 'truncated')
                truncated.text = '0'
                
                difficult = ET.SubElement(obj, 'difficult')
                difficult.text = '0'
                
                bndbox = ET.SubElement(obj, 'bndbox')
                xmin = ET.SubElement(bndbox, 'xmin')
                xmin.text = str(bbox['x'])
                ymin = ET.SubElement(bndbox, 'ymin')
                ymin.text = str(bbox['y'])
                xmax = ET.SubElement(bndbox, 'xmax')
                xmax.text = str(bbox['x'] + bbox['width'])
                ymax = ET.SubElement(bndbox, 'ymax')
                ymax.text = str(bbox['y'] + bbox['height'])
            
            # Add polygons as objects (using bounding box)
            for polygon in annotations.get('polygons', []):
                points = polygon['points']
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                
                obj = ET.SubElement(annotation, 'object')
                
                name = ET.SubElement(obj, 'name')
                name.text = polygon.get('class', 'Class 1')
                
                pose = ET.SubElement(obj, 'pose')
                pose.text = 'Unspecified'
                
                truncated = ET.SubElement(obj, 'truncated')
                truncated.text = '0'
                
                difficult = ET.SubElement(obj, 'difficult')
                difficult.text = '0'
                
                bndbox = ET.SubElement(obj, 'bndbox')
                xmin = ET.SubElement(bndbox, 'xmin')
                xmin.text = str(int(min(xs)))
                ymin = ET.SubElement(bndbox, 'ymin')
                ymin.text = str(int(min(ys)))
                xmax = ET.SubElement(bndbox, 'xmax')
                xmax.text = str(int(max(xs)))
                ymax = ET.SubElement(bndbox, 'ymax')
                ymax.text = str(int(max(ys)))
            
            # Pretty print XML
            xml_str = minidom.parseString(ET.tostring(annotation)).toprettyxml(indent="  ")
            
            # Save XML file
            xml_filename = os.path.splitext(image_filename)[0] + '.xml'
            xml_path = os.path.join(annotations_folder, xml_filename)
            
            with open(xml_path, 'w') as f:
                f.write(xml_str)
            
            exported_files.append(xml_path)
        
        return annotations_folder
    
    def export_yolo(self, images_data, output_folder, class_names):
        """
        Export annotations in YOLO format
        Format: <class_id> <x_center> <y_center> <width> <height> (normalized 0-1)
        Creates one .txt file per image + classes.txt
        """
        labels_folder = os.path.join(output_folder, "labels")
        os.makedirs(labels_folder, exist_ok=True)
        
        # Create class mapping
        class_to_id = {name: idx for idx, name in enumerate(class_names)}
        
        # Save classes.txt
        classes_file = os.path.join(output_folder, "classes.txt")
        with open(classes_file, 'w') as f:
            for class_name in class_names:
                f.write(f"{class_name}\n")
        
        exported_files = []
        
        for image_path, annotations in images_data.items():
            img_width = annotations.get('image_width', 1)
            img_height = annotations.get('image_height', 1)
            image_filename = os.path.basename(image_path)
            
            # Create label file
            label_filename = os.path.splitext(image_filename)[0] + '.txt'
            label_path = os.path.join(labels_folder, label_filename)
            
            with open(label_path, 'w') as f:
                # Process bboxes
                for bbox in annotations.get('bboxes', []):
                    class_name = bbox.get('class', 'Class 1')
                    class_id = class_to_id.get(class_name, 0)
                    
                    # Convert to YOLO format (normalized center coordinates)
                    x_center = (bbox['x'] + bbox['width'] / 2) / img_width
                    y_center = (bbox['y'] + bbox['height'] / 2) / img_height
                    width = bbox['width'] / img_width
                    height = bbox['height'] / img_height
                    
                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                
                # Process polygons (convert to bounding box)
                for polygon in annotations.get('polygons', []):
                    class_name = polygon.get('class', 'Class 1')
                    class_id = class_to_id.get(class_name, 0)
                    
                    points = polygon['points']
                    xs = [p[0] for p in points]
                    ys = [p[1] for p in points]
                    
                    x_min, x_max = min(xs), max(xs)
                    y_min, y_max = min(ys), max(ys)
                    
                    # Convert to YOLO format
                    x_center = ((x_min + x_max) / 2) / img_width
                    y_center = ((y_min + y_max) / 2) / img_height
                    width = (x_max - x_min) / img_width
                    height = (y_max - y_min) / img_height
                    
                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
            
            exported_files.append(label_path)
        
        return labels_folder
