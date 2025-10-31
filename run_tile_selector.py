"""
Image Tile Selector - Entry Point
Run this script to start the Image Tile Selector application.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from tkinterdnd2 import TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    import tkinter as tk
    DND_AVAILABLE = False
    print("Warning: tkinterdnd2 not installed. Drag and drop will not be available.")
    print("Install with: pip install tkinterdnd2")

from tile_selector import ImageTileSelector


def main():
    """Main entry point for the application"""
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = ImageTileSelector(root)
    root.mainloop()


if __name__ == "__main__":
    main()
