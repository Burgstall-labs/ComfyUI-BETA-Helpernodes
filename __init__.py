"""
Custom Nodes for ComfyUI - BETA Cropnodes
"""

# Import the node classes and mappings from your main file
from .BETA_cropnodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# Optionally, you can add more information here
WEB_DIRECTORY = "./js" # If you were adding custom JS widgets
__version__ = "1.0.0"
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

print(" B E T A  Crop Nodes ") # Simple print statement for confirmation
print("Nodes loaded: Video Crop, Video Stitch")