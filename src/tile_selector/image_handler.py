"""
Image Handler Module for Tile Selector
Manages image loading and navigation operations
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image


class ImageHandler:
    """Handles image loading and navigation"""
    
    def __init__(self, app):
        self.app = app
        
    def is_image_file(self, filepath):
        """Check if file is a supported image format"""
        ext = os.path.splitext(filepath)[1].lower()
        return ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']
    
    def upload_images(self):
        """Upload multiple image files"""
        filetypes = [
            ('Image files', '*.png *.jpg *.jpeg *.bmp *.tiff *.gif'),
            ('All files', '*.*')
        ]
        filepaths = filedialog.askopenfilenames(title="Select Images", filetypes=filetypes)
        if filepaths:
            self.app.images = []
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
            self.app.current_image_index = selection[0]
            self.app.image_counter_label.config(
                text=f"{self.app.current_image_index + 1} / {len(self.app.images)}")
            self.app.apply_tile_size()
    
    def prev_image(self):
        """Show previous image"""
        if not self.app.images:
            return
        self.app.current_image_index = (self.app.current_image_index - 1) % len(self.app.images)
        self.app.image_listbox.selection_clear(0, tk.END)
        self.app.image_listbox.selection_set(self.app.current_image_index)
        self.app.image_listbox.see(self.app.current_image_index)
        self.app.image_counter_label.config(
            text=f"{self.app.current_image_index + 1} / {len(self.app.images)}")
        self.app.apply_tile_size()
    
    def next_image(self):
        """Show next image"""
        if not self.app.images:
            return
        self.app.current_image_index = (self.app.current_image_index + 1) % len(self.app.images)
        self.app.image_listbox.selection_clear(0, tk.END)
        self.app.image_listbox.selection_set(self.app.current_image_index)
        self.app.image_listbox.see(self.app.current_image_index)
        self.app.image_counter_label.config(
            text=f"{self.app.current_image_index + 1} / {len(self.app.images)}")
        self.app.apply_tile_size()
