"""
Custom Nodes for ComfyUI - BETA Helpernodes (includes Crop, Audio, Image nodes)
"""

# 1. Import mappings from existing node files (Crop, Audio)
from .BETA_cropnodes import NODE_CLASS_MAPPINGS as CROP_CLASS_MAPPINGS
from .BETA_cropnodes import NODE_DISPLAY_NAME_MAPPINGS as CROP_DISPLAY_MAPPINGS
# Assuming audio saver is in audio_saver.py and defines its own mappings or class
try:
    # Import class directly if mappings aren't exported from audio_saver
    from .audio_saver import SaveAudioAdvanced
    AUDIO_CLASS_MAPPINGS = {"SaveAudioAdvanced_BETA": SaveAudioAdvanced}
    AUDIO_DISPLAY_MAPPINGS = {"SaveAudioAdvanced_BETA": "Save Audio Advanced 🔊 🅑🅔🅣🅐"}
except ImportError:
    print("[ComfyUI-BETA-Helpernodes] Warning: Could not import audio_saver node.")
    AUDIO_CLASS_MAPPINGS = {}
    AUDIO_DISPLAY_MAPPINGS = {}


# 2. Import the new node class(es) from your new file(s)
try:
    from .sharpness_clipper import SharpestFrameClipper # Import the new class
except ImportError:
    print("[ComfyUI-BETA-Helpernodes] Warning: Could not import sharpness_clipper node.")
    SharpestFrameClipper = None # Define as None if import fails

try:
    from .load_text_node import LoadTextIncremental
except ImportError:
    print("[ComfyUI-BETA-Helpernodes] Warning: Could not import load_text_node.")
    LoadTextIncremental = None


# 3. Define the mappings for the NEW node(s) added in THIS __init__.py
# Ensure the keys are unique across your entire node pack
NEW_CLASS_MAPPINGS = {}
NEW_DISPLAY_NAME_MAPPINGS = {}

# Add sharpness clipper if imported successfully
if SharpestFrameClipper:
    NEW_CLASS_MAPPINGS["SharpestFrameClipper_BETA"] = SharpestFrameClipper
    # Applying naming convention: Use scissors emoji ✂️
    NEW_DISPLAY_NAME_MAPPINGS["SharpestFrameClipper_BETA"] = "Clip to Sharpest Frame ✂️ 🅑🅔🅣🅐"
if LoadTextIncremental:
    NEW_CLASS_MAPPINGS["LoadTextIncremental_BETA"] = LoadTextIncremental
    NEW_DISPLAY_NAME_MAPPINGS["LoadTextIncremental_BETA"] = "Load Text Incrementally 📼 🅑🅔🅣🅐"
# 4. Combine the mappings from all sources
NODE_CLASS_MAPPINGS = {
    **CROP_CLASS_MAPPINGS,
    **AUDIO_CLASS_MAPPINGS,
    **NEW_CLASS_MAPPINGS # Add mappings defined here
}
NODE_DISPLAY_NAME_MAPPINGS = {
    **CROP_DISPLAY_MAPPINGS,
    **AUDIO_DISPLAY_MAPPINGS,
    **NEW_DISPLAY_NAME_MAPPINGS # Add display names defined here
}

# --- Optional Metadata and Exports ---
# WEB_DIRECTORY = "./js"
__version__ = "1.2.0" # Incremented version

# __all__ is important for ComfyUI to find the node mappings
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

# --- Print confirmation message ---
print("--------------------------------------")
print("--- ComfyUI-BETA-Helpernodes ---")
print(f"--- Version: {__version__} ---")
print("--------------------------------------")
# List loaded nodes dynamically from the final mappings
loaded_node_names = list(NODE_DISPLAY_NAME_MAPPINGS.values())
print(f"Nodes loaded ({len(loaded_node_names)}): {', '.join(loaded_node_names)}")
print("--------------------------------------")
