"""
visual_constants.py - Houses design system colors, structural gap factors,
and animation configurations shared across the application modules.
"""

# Dimensions
NODE_RADIUS  = 28
LEVEL_GAP    = 75

# Core Palette
BG_COLOR     = "#222222"
CANVAS_COLOR = "#1A1A1A"
TEXT_COLOR   = "white"

# Accent & Data Mapping Colors
PUSH_COLOR   = "#00CED1"
POP_COLOR    = "#FF8C00"
GRID_COLOR   = "#333333"
AXIS_COLOR   = "#666666"

# Node Status Themes
COL_DEFAULT     = "#00CED1"   # Default Min-Heap node color
COL_DEFAULT_MAX = "#FF8C00"   # Default Max-Heap node color
COL_ACTIVE      = "#FFD700"   # Node being evaluated (Gold)
COL_COMPARE     = "#FF4444"   # Peer node compared against (Red)
COL_SWAP        = "#00FF88"   # Nodes in transition (Green)
COL_GHOST       = "#444444"   # Faded trace of node position
COL_NEW         = "#FFFFFF"   # Brand new inserted node
COL_REMOVE      = "#FF2222"   # Root node being extracted

# Speed & Tweens
TWEEN_STEPS     = 18          # Frame subdivisions per animation state
TWEEN_MS        = 16          # Target frame interval (~60 FPS)
DEFAULT_STEP_MS = 600         # Pause threshold between animation states