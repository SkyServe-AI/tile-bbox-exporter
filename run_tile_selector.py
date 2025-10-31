"""
Image Tile Selector - Entry Point
Run this script to start the Image Tile Selector application.
"""

import tkinter as tk
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tile_selector import ImageTileSelector


def main():
    """Main entry point for the application"""
    root = tk.Tk()
    app = ImageTileSelector(root)
    root.mainloop()


if __name__ == "__main__":
    main()
