import os
import glob
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Tuple, Dict
import cv2
from tqdm import tqdm
import matplotlib.pyplot as plt
from collections import defaultdict


class LULCTileClassifier:
    """
    Automated LULC (Land Use Land Cover) Tile Classifier
    Extracts 256x256 tiles from large images and classifies them into categories
    """
    
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
    
    def __init__(self, source_folder: str, output_folder: str, tile_size: int = 256, 
                 apply_color_correction: bool = True, filter_clouds: bool = True,
                 cloud_threshold: float = 0.7):
        """
        Initialize the LULC Tile Classifier
        
        Args:
            source_folder: Path to folder containing source images
            output_folder: Path to output folder for classified tiles
            tile_size: Size of tiles to extract (default: 256x256)
            apply_color_correction: Apply band adjustment and color correction
            filter_clouds: Filter out tiles with cloud coverage
            cloud_threshold: Threshold for cloud detection (0-1)
        """
        self.source_folder = Path(source_folder)
        self.output_folder = Path(output_folder)
        self.tile_size = tile_size
        self.apply_color_correction = apply_color_correction
        self.filter_clouds = filter_clouds
        self.cloud_threshold = cloud_threshold
        self.tile_counts = {category: 0 for category in self.CATEGORIES}
        self.cloud_filtered_count = 0
        self.band_stats = defaultdict(list)
        
        # Create output directory structure
        self._create_directory_structure()
    
    def _create_directory_structure(self):
        """Create folders for each LULC category"""
        print("Creating directory structure...")
        for category in self.CATEGORIES:
            category_path = self.output_folder / category
            category_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created: {category}")
        
        # Create analysis folder for band statistics
        analysis_path = self.output_folder / "analysis"
        analysis_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created: analysis")
        print("Directory structure ready!\n")
    
    def analyze_image_bands(self, img: np.ndarray, image_name: str) -> Dict:
        """
        Analyze the color bands of an image to detect imbalances
        
        Args:
            img: Input image array (BGR format)
            image_name: Name of the image for reporting
            
        Returns:
            Dictionary with band statistics
        """
        # Split into BGR channels
        b, g, r = cv2.split(img)
        
        # Calculate statistics for each band
        stats = {
            'blue': {'mean': np.mean(b), 'std': np.std(b), 'median': np.median(b)},
            'green': {'mean': np.mean(g), 'std': np.std(g), 'median': np.median(g)},
            'red': {'mean': np.mean(r), 'std': np.std(r), 'median': np.median(r)}
        }
        
        # Calculate band ratios
        total_mean = stats['blue']['mean'] + stats['green']['mean'] + stats['red']['mean']
        stats['ratios'] = {
            'blue': stats['blue']['mean'] / total_mean,
            'green': stats['green']['mean'] / total_mean,
            'red': stats['red']['mean'] / total_mean
        }
        
        # Detect green bias
        green_bias = stats['ratios']['green'] > 0.40  # More than 40% is considered biased
        stats['green_bias'] = green_bias
        
        # Print analysis
        print(f"\n  Band Analysis for {image_name}:")
        print(f"    Blue  - Mean: {stats['blue']['mean']:.2f}, Ratio: {stats['ratios']['blue']:.3f}")
        print(f"    Green - Mean: {stats['green']['mean']:.2f}, Ratio: {stats['ratios']['green']:.3f}")
        print(f"    Red   - Mean: {stats['red']['mean']:.2f}, Ratio: {stats['ratios']['red']:.3f}")
        if green_bias:
            print(f"    ⚠️  Green bias detected! (Ratio: {stats['ratios']['green']:.3f})")
        
        return stats
    
    def apply_band_correction(self, img: np.ndarray, stats: Dict) -> np.ndarray:
        """
        Apply color correction to balance bands
        
        Args:
            img: Input image array (BGR format)
            stats: Band statistics from analyze_image_bands
            
        Returns:
            Color-corrected image
        """
        corrected = img.copy().astype(np.float32)
        
        # Apply histogram equalization per channel for better contrast
        b, g, r = cv2.split(corrected.astype(np.uint8))
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        b = clahe.apply(b)
        g = clahe.apply(g)
        r = clahe.apply(r)
        
        corrected = cv2.merge([b, g, r]).astype(np.float32)
        
        # If green bias detected, reduce green channel intensity
        if stats.get('green_bias', False):
            green_ratio = stats['ratios']['green']
            reduction_factor = 0.33 / green_ratio  # Target 33% for balanced RGB
            corrected[:, :, 1] = corrected[:, :, 1] * reduction_factor
            print(f"    ✓ Applied green bias correction (factor: {reduction_factor:.3f})")
        
        # Normalize to 0-255 range
        corrected = np.clip(corrected, 0, 255).astype(np.uint8)
        
        return corrected
    
    def detect_cloud(self, tile: np.ndarray) -> Tuple[bool, float]:
        """
        Detect if a tile contains clouds
        
        Args:
            tile: Input tile array (BGR format)
            
        Returns:
            Tuple of (is_cloud, cloud_score)
        """
        # Convert to RGB and HSV
        rgb = cv2.cvtColor(tile, cv2.COLOR_BGR2RGB)
        hsv = cv2.cvtColor(tile, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
        
        # Cloud characteristics:
        # 1. High brightness (V channel in HSV)
        # 2. Low saturation (S channel in HSV)
        # 3. White/light gray color (high RGB values, similar across channels)
        
        h, s, v = cv2.split(hsv)
        
        # Calculate cloud indicators
        high_brightness = np.mean(v) > 200  # Very bright
        low_saturation = np.mean(s) < 30    # Very low color saturation
        
        # Check if colors are similar (white/gray has similar RGB values)
        r, g, b = cv2.split(rgb)
        color_variance = np.std([np.mean(r), np.mean(g), np.mean(b)])
        low_color_variance = color_variance < 15
        
        # Calculate percentage of bright, low-saturation pixels
        bright_pixels = (v > 200) & (s < 40)
        cloud_pixel_ratio = np.sum(bright_pixels) / (self.tile_size * self.tile_size)
        
        # Cloud score (0-1)
        cloud_score = cloud_pixel_ratio
        
        # Determine if it's a cloud tile
        is_cloud = (cloud_pixel_ratio > self.cloud_threshold) or \
                   (high_brightness and low_saturation and low_color_variance)
        
        return is_cloud, cloud_score
    
    def extract_tiles(self, image_path: Path) -> List[Tuple[np.ndarray, int, int]]:
        """
        Extract 256x256 tiles from a large image with optional color correction
        
        Args:
            image_path: Path to the source image
            
        Returns:
            List of tuples (tile_array, row_index, col_index)
        """
        # Load image
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"Warning: Could not load {image_path}")
            return []
        
        image_name = image_path.stem
        height, width = img.shape[:2]
        print(f"  Image dimensions: {width}x{height}")
        
        # Analyze bands
        # img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        if self.apply_color_correction:
            stats = self.analyze_image_bands(img, image_name)
            img = self.apply_band_correction(img, stats)
            # Save corrected image for reference
            corrected_path = self.output_folder / "analysis" / f"{image_name}_corrected.tif"
            cv2.imwrite(str(corrected_path), img)
            print(f"    ✓ Saved corrected image to analysis folder")
        
        tiles = []
        
        # Calculate number of tiles
        rows = height // self.tile_size
        cols = width // self.tile_size
        
        # Extract tiles
        for i in range(rows):
            for j in range(cols):
                y_start = i * self.tile_size
                x_start = j * self.tile_size
                y_end = y_start + self.tile_size
                x_end = x_start + self.tile_size
                
                tile = img[y_start:y_end, x_start:x_end]
                tiles.append((tile, i, j))
        
        return tiles
    
    def classify_tile(self, tile: np.ndarray) -> str:
        """
        Classify a tile into one of the LULC categories
        Uses color-based and texture-based heuristics
        
        Args:
            tile: 256x256 numpy array representing the tile
            
        Returns:
            Category name
        """
        # Convert to different color spaces for analysis
        hsv = cv2.cvtColor(tile, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
        rgb = cv2.cvtColor(tile, cv2.COLOR_BGR2RGB)
        
        # Calculate features
        mean_color = np.mean(tile, axis=(0, 1))
        std_color = np.std(tile, axis=(0, 1))
        mean_hsv = np.mean(hsv, axis=(0, 1))
        std_hsv = np.std(hsv, axis=(0, 1))
        
        # Calculate texture features
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (self.tile_size * self.tile_size)
        
        # Calculate additional texture features
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        texture_variance = np.var(laplacian)
        
        # Calculate color variance
        color_variance = np.mean(std_color)
        
        # Calculate NDVI-like index (vegetation index)
        b, g, r = mean_color
        nir_proxy = g  # Green as proxy for NIR in RGB images
        red = r
        if (nir_proxy + red) > 0:
            ndvi = (nir_proxy - red) / (nir_proxy + red)
        else:
            ndvi = 0
        
        # HSV values
        h, s, v = mean_hsv
        
        # Normalized RGB ratios
        total_rgb = b + g + r
        if total_rgb > 0:
            b_ratio = b / total_rgb
            g_ratio = g / total_rgb
            r_ratio = r / total_rgb
        else:
            b_ratio = g_ratio = r_ratio = 0.33
        
        # Calculate brightness and saturation metrics
        brightness = v
        saturation = s
        
        # WATER DETECTION (River, SeaLake)
        # Water: blue dominant, low saturation variance, darker
        if (b > g and b > r and b > 80) or (b_ratio > 0.38 and brightness < 150):
            if edge_density < 0.08 and color_variance < 25:
                return 'SeaLake'
            elif edge_density >= 0.08 or color_variance >= 25:
                return 'River'
        
        # RESIDENTIAL DETECTION (check early - high priority)
        # Residential: high texture, mixed colors, varied structures
        if edge_density > 0.10 and color_variance > 22 and texture_variance > 60:
            # Additional check: not too green (to avoid vegetation)
            if g_ratio < 0.40 or saturation < 70:
                return 'Residential'
        
        # HIGHWAY DETECTION (check early - distinct features)
        # Highway: uniform gray/dark, moderate edges, linear structures
        if saturation < 35 and edge_density > 0.08 and edge_density < 0.20:
            if color_variance < 28 and brightness < 130:
                return 'Highway'
        
        # FOREST DETECTION
        # Forest: dark green, high texture, high NDVI, low brightness
        if (g > r and g > b and brightness < 140 and ndvi > 0.1 and 
            (edge_density > 0.12 or texture_variance > 100)):
            return 'Forest'
        
        # ANNUAL CROP DETECTION (more sensitive)
        # AnnualCrop: green with visible structure/rows, medium brightness
        if g > r and g > b and edge_density > 0.08:
            if saturation > 35 and color_variance > 12 and brightness > 90:
                return 'AnnualCrop'
        
        # PERMANENT CROP DETECTION
        # PermanentCrop: green, less structured than annual, uniform
        if g > r and g > b and saturation > 30:
            if edge_density < 0.10 and brightness > 100 and color_variance < 25:
                return 'PermanentCrop'
        
        # VEGETATION (Pasture, Herbaceous)
        # Light green, lower saturation than crops
        if g_ratio > 0.35 and ndvi > 0.05:
            if color_variance < 20 and saturation < 60:
                return 'Pasture'
            elif color_variance >= 20 or saturation >= 60:
                return 'HerbaceousVegetation'
        
        # INDUSTRIAL DETECTION
        # Industrial: uniform, low texture, gray/brown, low saturation
        if color_variance < 30 and saturation < 50 and edge_density < 0.10:
            return 'Industrial'
        
        # DEFAULT CLASSIFICATION based on dominant characteristics
        # Use a scoring system for ambiguous cases
        scores = {
            'Pasture': 0,
            'HerbaceousVegetation': 0,
            'Industrial': 0,
            'Forest': 0,
            'AnnualCrop': 0
        }
        
        # Score based on greenness
        if g_ratio > 0.34:
            scores['Pasture'] += 2
            scores['HerbaceousVegetation'] += 1
        
        # Score based on texture
        if edge_density > 0.10:
            scores['AnnualCrop'] += 1
            scores['Forest'] += 1
        else:
            scores['Pasture'] += 1
            scores['Industrial'] += 1
        
        # Score based on brightness
        if brightness > 120:
            scores['Pasture'] += 1
            scores['HerbaceousVegetation'] += 1
        else:
            scores['Forest'] += 1
            scores['Industrial'] += 1
        
        # Return category with highest score
        return max(scores, key=scores.get)
    
    def save_tile(self, tile: np.ndarray, category: str, image_name: str, row: int, col: int):
        """
        Save a classified tile to the appropriate category folder
        
        Args:
            tile: The tile image array
            category: LULC category
            image_name: Original image name
            row: Row index of the tile
            col: Column index of the tile
        """
        output_path = self.output_folder / category
        filename = f"{image_name}_tile_r{row:03d}_c{col:03d}.png"
        filepath = output_path / filename
        
        cv2.imwrite(str(filepath), tile)
        self.tile_counts[category] += 1
    
    def process_image(self, image_path: Path):
        """
        Process a single image: extract tiles, classify, and save
        
        Args:
            image_path: Path to the image file
        """
        print(f"Processing: {image_path.name}")
        image_name = image_path.stem
        
        # Extract tiles (with optional color correction)
        tiles = self.extract_tiles(image_path)
        print(f"  Extracted {len(tiles)} tiles")
        
        # Classify and save each tile
        tiles_processed = 0
        clouds_filtered = 0
        
        for tile, row, col in tqdm(tiles, desc="  Classifying tiles", leave=False):
            # Check for clouds if filtering is enabled
            if self.filter_clouds:
                is_cloud, cloud_score = self.detect_cloud(tile)
                if is_cloud:
                    clouds_filtered += 1
                    self.cloud_filtered_count += 1
                    continue
            
            category = self.classify_tile(tile)
            self.save_tile(tile, category, image_name, row, col)
            tiles_processed += 1
        
        print(f"  ✓ Processed: {tiles_processed} tiles, Filtered clouds: {clouds_filtered}\n")
    
    def process_all_images(self):
        """
        Process all images in the source folder
        """
        # Find all image files
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.tif', '*.tiff', '*.bmp']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(self.source_folder.glob(ext))
            image_files.extend(self.source_folder.glob(ext.upper()))
        
        if not image_files:
            print(f"No images found in {self.source_folder}")
            return
        
        print(f"Found {len(image_files)} images to process\n")
        print("=" * 60)
        
        # Process each image
        for image_path in image_files:
            self.process_image(image_path)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print classification summary"""
        print("=" * 60)
        print("CLASSIFICATION SUMMARY")
        print("=" * 60)
        total_tiles = sum(self.tile_counts.values())
        
        for category in self.CATEGORIES:
            count = self.tile_counts[category]
            percentage = (count / total_tiles * 100) if total_tiles > 0 else 0
            print(f"{category:25s}: {count:6d} tiles ({percentage:5.2f}%)")
        
        print("-" * 60)
        print(f"{'TOTAL CLASSIFIED':25s}: {total_tiles:6d} tiles")
        if self.filter_clouds:
            print(f"{'CLOUD FILTERED':25s}: {self.cloud_filtered_count:6d} tiles")
            grand_total = total_tiles + self.cloud_filtered_count
            print(f"{'GRAND TOTAL':25s}: {grand_total:6d} tiles")
        print("=" * 60)


def main():
    """
    Main function to run the LULC tile classifier
    """
    # Configuration
    SOURCE_FOLDER = "C:\\Users\\sreek\\Downloads\\loft_caiman_all_images\\images"  # Folder containing 3072x4096 images
    OUTPUT_FOLDER = "dataset"       # Output folder for classified tiles
    TILE_SIZE = 256                  # Tile size (256x256)
    APPLY_COLOR_CORRECTION = True   # Apply band adjustment and color correction
    FILTER_CLOUDS = True            # Filter out cloud-covered tiles
    CLOUD_THRESHOLD = 0.7           # Cloud detection threshold (0-1)
    
    print("=" * 60)
    print("LULC TILE CLASSIFIER WITH BAND ANALYSIS")
    print("=" * 60)
    print(f"Source Folder: {SOURCE_FOLDER}")
    print(f"Output Folder: {OUTPUT_FOLDER}")
    print(f"Tile Size: {TILE_SIZE}x{TILE_SIZE}")
    print(f"Color Correction: {'Enabled' if APPLY_COLOR_CORRECTION else 'Disabled'}")
    print(f"Cloud Filtering: {'Enabled' if FILTER_CLOUDS else 'Disabled'}")
    if FILTER_CLOUDS:
        print(f"Cloud Threshold: {CLOUD_THRESHOLD}")
    print("=" * 60)
    print()
    
    # Create classifier instance
    classifier = LULCTileClassifier(
        source_folder=SOURCE_FOLDER,
        output_folder=OUTPUT_FOLDER,
        tile_size=TILE_SIZE,
        apply_color_correction=APPLY_COLOR_CORRECTION,
        filter_clouds=FILTER_CLOUDS,
        cloud_threshold=CLOUD_THRESHOLD
    )
    
    # Process all images
    classifier.process_all_images()
    
    print("\n✓ Processing complete!")
    print(f"\nCorrected images saved in: {OUTPUT_FOLDER}/analysis/")


if __name__ == "__main__":
    main()
