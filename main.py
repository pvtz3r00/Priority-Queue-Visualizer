import os
import sys
import tkinter as tk

# Automatically add subfolders to the Python path to keep modular imports working
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'config'))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'core'))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'tracker'))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'ui'))

# Now Python can seamlessly resolve imports from any folder
from visualizer_tab import VisualizerTab

def main():
    root = tk.Tk()
    root.title("Manual Priority Queue (Binary Heap)")
    root.geometry("1300x700")

    tab = VisualizerTab(root)
    tab.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()