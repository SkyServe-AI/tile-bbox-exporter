"""
Image Augmentation Module
Provides various augmentation techniques for dataset enhancement
"""
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import random


class ImageAugmentor:
    """Handles image augmentation operations"""
    
    def __init__(self):
        self.augmentation_options = {
            'rotation': False,
            'rotation_angles': [90, 180, 270],
            'horizontal_flip': False,
            'vertical_flip': False,
            'brightness': False,
            'brightness_range': (0.7, 1.3),
            'contrast': False,
            'contrast_range': (0.8, 1.2),
            'blur': False,
            'blur_radius': (0.5, 2.0),
            'noise': False,
            'noise_amount': (5, 25),
            'saturation': False,
            'saturation_range': (0.8, 1.2),
            'sharpness': False,
            'sharpness_range': (0.8, 1.2),
        }
    
    def apply_augmentations(self, image, bbox_data=None):
        """
        Apply selected augmentations to an image
        Returns list of (augmented_image, augmentation_name, bbox_data) tuples
        """
        augmented_images = []
        
        # Original image
        augmented_images.append((image.copy(), 'original', bbox_data))
        
        # Rotation
        if self.augmentation_options['rotation']:
            for angle in self.augmentation_options['rotation_angles']:
                rotated_img, rotated_bbox = self._rotate_image(image, angle, bbox_data)
                augmented_images.append((rotated_img, f'rot{angle}', rotated_bbox))
        
        # Horizontal flip
        if self.augmentation_options['horizontal_flip']:
            flipped_img, flipped_bbox = self._flip_horizontal(image, bbox_data)
            augmented_images.append((flipped_img, 'hflip', flipped_bbox))
        
        # Vertical flip
        if self.augmentation_options['vertical_flip']:
            flipped_img, flipped_bbox = self._flip_vertical(image, bbox_data)
            augmented_images.append((flipped_img, 'vflip', flipped_bbox))
        
        # Brightness
        if self.augmentation_options['brightness']:
            bright_img = self._adjust_brightness(image)
            augmented_images.append((bright_img, 'bright', bbox_data))
        
        # Contrast
        if self.augmentation_options['contrast']:
            contrast_img = self._adjust_contrast(image)
            augmented_images.append((contrast_img, 'contrast', bbox_data))
        
        # Blur
        if self.augmentation_options['blur']:
            blurred_img = self._apply_blur(image)
            augmented_images.append((blurred_img, 'blur', bbox_data))
        
        # Noise
        if self.augmentation_options['noise']:
            noisy_img = self._add_noise(image)
            augmented_images.append((noisy_img, 'noise', bbox_data))
        
        # Saturation
        if self.augmentation_options['saturation']:
            saturated_img = self._adjust_saturation(image)
            augmented_images.append((saturated_img, 'saturate', bbox_data))
        
        # Sharpness
        if self.augmentation_options['sharpness']:
            sharp_img = self._adjust_sharpness(image)
            augmented_images.append((sharp_img, 'sharp', bbox_data))
        
        return augmented_images
    
    def _rotate_image(self, image, angle, bbox_data):
        """Rotate image and adjust bbox coordinates"""
        rotated_img = image.rotate(angle, expand=True)
        
        if bbox_data is None:
            return rotated_img, None
        
        # Adjust bbox coordinates based on rotation
        width, height = image.size
        new_width, new_height = rotated_img.size
        
        rotated_bbox = bbox_data.copy()
        x, y, w, h = bbox_data['x'], bbox_data['y'], bbox_data['width'], bbox_data['height']
        
        if angle == 90:
            rotated_bbox['x'] = y
            rotated_bbox['y'] = width - x - w
            rotated_bbox['width'] = h
            rotated_bbox['height'] = w
        elif angle == 180:
            rotated_bbox['x'] = width - x - w
            rotated_bbox['y'] = height - y - h
        elif angle == 270:
            rotated_bbox['x'] = height - y - h
            rotated_bbox['y'] = x
            rotated_bbox['width'] = h
            rotated_bbox['height'] = w
        
        return rotated_img, rotated_bbox
    
    def _flip_horizontal(self, image, bbox_data):
        """Flip image horizontally and adjust bbox"""
        flipped_img = image.transpose(Image.FLIP_LEFT_RIGHT)
        
        if bbox_data is None:
            return flipped_img, None
        
        width = image.width
        flipped_bbox = bbox_data.copy()
        flipped_bbox['x'] = width - bbox_data['x'] - bbox_data['width']
        
        return flipped_img, flipped_bbox
    
    def _flip_vertical(self, image, bbox_data):
        """Flip image vertically and adjust bbox"""
        flipped_img = image.transpose(Image.FLIP_TOP_BOTTOM)
        
        if bbox_data is None:
            return flipped_img, None
        
        height = image.height
        flipped_bbox = bbox_data.copy()
        flipped_bbox['y'] = height - bbox_data['y'] - bbox_data['height']
        
        return flipped_img, flipped_bbox
    
    def _adjust_brightness(self, image):
        """Adjust image brightness"""
        min_val, max_val = self.augmentation_options['brightness_range']
        factor = random.uniform(min_val, max_val)
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)
    
    def _adjust_contrast(self, image):
        """Adjust image contrast"""
        min_val, max_val = self.augmentation_options['contrast_range']
        factor = random.uniform(min_val, max_val)
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)
    
    def _apply_blur(self, image):
        """Apply Gaussian blur"""
        min_val, max_val = self.augmentation_options['blur_radius']
        radius = random.uniform(min_val, max_val)
        return image.filter(ImageFilter.GaussianBlur(radius))
    
    def _add_noise(self, image):
        """Add random noise to image"""
        img_array = np.array(image)
        min_val, max_val = self.augmentation_options['noise_amount']
        noise_amount = random.randint(min_val, max_val)
        
        noise = np.random.randint(-noise_amount, noise_amount, img_array.shape, dtype=np.int16)
        noisy_img = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        return Image.fromarray(noisy_img)
    
    def _adjust_saturation(self, image):
        """Adjust color saturation"""
        min_val, max_val = self.augmentation_options['saturation_range']
        factor = random.uniform(min_val, max_val)
        enhancer = ImageEnhance.Color(image)
        return enhancer.enhance(factor)
    
    def _adjust_sharpness(self, image):
        """Adjust image sharpness"""
        min_val, max_val = self.augmentation_options['sharpness_range']
        factor = random.uniform(min_val, max_val)
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(factor)
    
    def get_augmentation_count(self):
        """Calculate total number of augmented images that will be generated"""
        count = 1  # Original
        
        if self.augmentation_options['rotation']:
            count += len(self.augmentation_options['rotation_angles'])
        if self.augmentation_options['horizontal_flip']:
            count += 1
        if self.augmentation_options['vertical_flip']:
            count += 1
        if self.augmentation_options['brightness']:
            count += 1
        if self.augmentation_options['contrast']:
            count += 1
        if self.augmentation_options['blur']:
            count += 1
        if self.augmentation_options['noise']:
            count += 1
        if self.augmentation_options['saturation']:
            count += 1
        if self.augmentation_options['sharpness']:
            count += 1
        
        return count
