"""
LULC Classifier Integration Module
Handles automatic tile classification with visual preview
"""
import numpy as np
import cv2
from PIL import Image


class LULCClassifier:
    """Integrated LULC classifier for tile selector"""
    
    # LULC Categories
    CATEGORIES = [
        'AnnualCrop',
        'Forest',
        'HerbaceousVegetation',
        'Highway',
        'Industrial',
        'Pasture',
        'PermanentCrop',
        'Residential',
        'River',
        'SeaLake'
    ]
    
    # Color mapping for each category (RGB format for display)
    CATEGORY_COLORS = {
        'AnnualCrop': '#FFD700',        # Gold
        'Forest': '#228B22',            # Forest Green
        'HerbaceousVegetation': '#90EE90',  # Light Green
        'Highway': '#696969',           # Dim Gray
        'Industrial': '#8B4513',        # Saddle Brown
        'Pasture': '#7CFC00',           # Lawn Green
        'PermanentCrop': '#FF8C00',     # Dark Orange
        'Residential': '#FF1493',       # Deep Pink
        'River': '#1E90FF',             # Dodger Blue
        'SeaLake': '#000080'            # Navy Blue
    }
    
    def __init__(self, apply_color_correction=True, filter_clouds=True, cloud_threshold=0.7):
        """Initialize LULC classifier"""
        self.apply_color_correction = apply_color_correction
        self.filter_clouds = filter_clouds
        self.cloud_threshold = cloud_threshold
    
    def analyze_image_bands(self, img_array):
        """Analyze RGB bands and return statistics"""
        b, g, r = cv2.split(img_array)
        
        stats = {
            'blue': {'mean': np.mean(b), 'std': np.std(b)},
            'green': {'mean': np.mean(g), 'std': np.std(g)},
            'red': {'mean': np.mean(r), 'std': np.std(r)}
        }
        
        total_mean = stats['blue']['mean'] + stats['green']['mean'] + stats['red']['mean']
        stats['ratios'] = {
            'blue': stats['blue']['mean'] / total_mean,
            'green': stats['green']['mean'] / total_mean,
            'red': stats['red']['mean'] / total_mean
        }
        
        stats['green_bias'] = stats['ratios']['green'] > 0.40
        return stats
    
    def apply_band_correction(self, img_array, stats):
        """Apply color correction to balance bands"""
        corrected = img_array.copy().astype(np.float32)
        
        b, g, r = cv2.split(corrected.astype(np.uint8))
        
        # Apply CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        b = clahe.apply(b)
        g = clahe.apply(g)
        r = clahe.apply(r)
        
        corrected = cv2.merge([b, g, r]).astype(np.float32)
        
        # Green bias correction
        if stats.get('green_bias', False):
            green_ratio = stats['ratios']['green']
            reduction_factor = 0.33 / green_ratio
            corrected[:, :, 1] = corrected[:, :, 1] * reduction_factor
        
        corrected = np.clip(corrected, 0, 255).astype(np.uint8)
        return corrected
    
    def detect_cloud(self, tile_array):
        """Detect if tile contains clouds"""
        hsv = cv2.cvtColor(tile_array, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        bright_pixels = (v > 200) & (s < 40)
        cloud_pixel_ratio = np.sum(bright_pixels) / (tile_array.shape[0] * tile_array.shape[1])
        
        is_cloud = cloud_pixel_ratio > self.cloud_threshold
        return is_cloud, cloud_pixel_ratio
    
    def classify_tile(self, tile_array):
        """
        Classify a tile into LULC category
        
        Args:
            tile_array: numpy array of tile (BGR format)
            
        Returns:
            category name string
        """
        # Convert to different color spaces
        hsv = cv2.cvtColor(tile_array, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(tile_array, cv2.COLOR_BGR2GRAY)
        
        # Calculate features
        mean_color = np.mean(tile_array, axis=(0, 1))
        std_color = np.std(tile_array, axis=(0, 1))
        mean_hsv = np.mean(hsv, axis=(0, 1))
        
        # Texture features
        edges = cv2.Canny(gray, 50, 150)
        tile_size = tile_array.shape[0]
        edge_density = np.sum(edges > 0) / (tile_size * tile_size)
        
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        texture_variance = np.var(laplacian)
        
        color_variance = np.mean(std_color)
        
        # Calculate NDVI-like index
        b, g, r = mean_color
        nir_proxy = g
        red = r
        if (nir_proxy + red) > 0:
            ndvi = (nir_proxy - red) / (nir_proxy + red)
        else:
            ndvi = 0
        
        h, s, v = mean_hsv
        
        # Normalized RGB ratios
        total_rgb = b + g + r
        if total_rgb > 0:
            b_ratio = b / total_rgb
            g_ratio = g / total_rgb
            r_ratio = r / total_rgb
        else:
            b_ratio = g_ratio = r_ratio = 0.33
        
        brightness = v
        saturation = s
        
        # Classification logic
        
        # WATER DETECTION
        if (b > g and b > r and b > 80) or (b_ratio > 0.38 and brightness < 150):
            if edge_density < 0.08 and color_variance < 25:
                return 'SeaLake'
            elif edge_density >= 0.08 or color_variance >= 25:
                return 'River'
        
        # RESIDENTIAL DETECTION
        if edge_density > 0.10 and color_variance > 22 and texture_variance > 60:
            if g_ratio < 0.40 or saturation < 70:
                return 'Residential'
        
        # HIGHWAY DETECTION
        if saturation < 35 and edge_density > 0.08 and edge_density < 0.20:
            if color_variance < 28 and brightness < 130:
                return 'Highway'
        
        # FOREST DETECTION
        if (g > r and g > b and brightness < 140 and ndvi > 0.1 and 
            (edge_density > 0.12 or texture_variance > 100)):
            return 'Forest'
        
        # ANNUAL CROP DETECTION
        if g > r and g > b and edge_density > 0.08:
            if saturation > 35 and color_variance > 12 and brightness > 90:
                return 'AnnualCrop'
        
        # PERMANENT CROP DETECTION
        if g > r and g > b and saturation > 30:
            if edge_density < 0.10 and brightness > 100 and color_variance < 25:
                return 'PermanentCrop'
        
        # VEGETATION (Pasture, Herbaceous)
        if g_ratio > 0.35 and ndvi > 0.05:
            if color_variance < 20 and saturation < 60:
                return 'Pasture'
            elif color_variance >= 20 or saturation >= 60:
                return 'HerbaceousVegetation'
        
        # INDUSTRIAL DETECTION
        if color_variance < 30 and saturation < 50 and edge_density < 0.10:
            return 'Industrial'
        
        # DEFAULT CLASSIFICATION
        scores = {
            'Pasture': 0,
            'HerbaceousVegetation': 0,
            'Industrial': 0,
            'Forest': 0,
            'AnnualCrop': 0
        }
        
        if g_ratio > 0.34:
            scores['Pasture'] += 2
            scores['HerbaceousVegetation'] += 1
        
        if edge_density > 0.10:
            scores['AnnualCrop'] += 1
            scores['Forest'] += 1
        else:
            scores['Pasture'] += 1
            scores['Industrial'] += 1
        
        if brightness > 120:
            scores['Pasture'] += 1
            scores['HerbaceousVegetation'] += 1
        else:
            scores['Forest'] += 1
            scores['Industrial'] += 1
        
        return max(scores, key=scores.get)
    
    def classify_tiles(self, tiles, progress_callback=None):
        """
        Classify multiple tiles
        
        Args:
            tiles: List of tile dictionaries with 'tile_img' (PIL Image)
            progress_callback: Optional callback function(current, total)
            
        Returns:
            List of classifications (category names)
        """
        classifications = []
        total = len(tiles)
        
        for i, tile_info in enumerate(tiles):
            # Convert PIL to numpy array (BGR)
            pil_img = tile_info['tile_img']
            img_array = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            # Apply color correction if enabled
            if self.apply_color_correction:
                stats = self.analyze_image_bands(img_array)
                img_array = self.apply_band_correction(img_array, stats)
            
            # Check for clouds
            if self.filter_clouds:
                is_cloud, _ = self.detect_cloud(img_array)
                if is_cloud:
                    classifications.append('Cloud')
                    if progress_callback:
                        progress_callback(i + 1, total)
                    continue
            
            # Classify tile
            category = self.classify_tile(img_array)
            classifications.append(category)
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return classifications
