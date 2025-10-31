"""
BBox Selector - Entry Point
Run this script to start the BBox Selector application.
"""

import tkinter as tk
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bbox_selector import BBoxSelector


def main():
    """Main entry point for the application"""
    root = tk.Tk()
    app = BBoxSelector(root)
    root.mainloop()


if __name__ == "__main__":
    main()
