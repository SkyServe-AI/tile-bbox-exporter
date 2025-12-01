"""
Image Tile Selector - Entry Point
Run this script to start the Image Tile Selector application.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def import_tkinter():
    """Ensure tkinter is available, otherwise explain how to install it."""
    try:
        import tkinter as tk
        return tk
    except ModuleNotFoundError as exc:
        hint = (
            "Tkinter (_tkinter) is not available in this Python build.\n"
            "On macOS install the Tcl/Tk frameworks and use a Python build "
            "that links against them (e.g., python.org installers or "
            "Homebrew Python with `brew install tcl-tk`).\n"
            "After installing Tcl/Tk, re-create your venv so that `_tkinter` "
            "can be compiled/linked.\n"
            "Verify by running: python3 -m tkinter"
        )
        print(hint)
        raise SystemExit(1) from exc


tk = import_tkinter()

try:
    from tkinterdnd2 import TkinterDnD
    DND_AVAILABLE = True
except ImportError:
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
