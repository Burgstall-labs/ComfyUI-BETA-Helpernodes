"""
Custom Nodes for ComfyUI - BETA Helpernodes (includes Crop, Audio, Image nodes)
"""

# 3. Define the mappings for the NEW node(s) added in THIS __init__.py
NEW_CLASS_MAPPINGS = {}
NEW_DISPLAY_NAME_MAPPINGS = {}


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
try: # Import the new class
    from .sharpness_clipper import SharpestFrameClipper
except ImportError:
    print("[ComfyUI-BETA-Helpernodes] Warning: Could not import sharpness_clipper node.")
    SharpestFrameClipper = None

# Import and define LoadTextFromIndex before using it
try:
    from .load_text_node import LoadTextFromIndex
except ImportError:
    print("[ComfyUI-BETA-Helpernodes] Warning: Could not import load text node.")
    LoadTextFromIndex = None

# Import the IndexedLoRALoader node
try:
    from .indexed_lora_loader import IndexedLoRALoader
except ImportError:
    print("[ComfyUI-BETA-Helpernodes] Warning: Could not import indexed lora loader node.")
    IndexedLoRALoader = None

# Import the TextLineCount node
try:
    from .text_line_count import TextLineCount
except ImportError:
    print("[ComfyUI-BETA-Helpernodes] Warning: Could not import text_line_count node.")
    TextLineCount = None

# Add TextLineCount if imported successfully
if TextLineCount:
    NEW_CLASS_MAPPINGS["TextLineCount_BETA"] = TextLineCount
    NEW_DISPLAY_NAME_MAPPINGS["TextLineCount_BETA"] = "Text line count 🅑🅔🅣🅐"

# Add sharpness clipper  if imported successfully
if SharpestFrameClipper:
    NEW_CLASS_MAPPINGS["SharpestFrameClipper_BETA"] = SharpestFrameClipper
    # Applying naming convention: Use scissors emoji ✂️
    NEW_DISPLAY_NAME_MAPPINGS["SharpestFrameClipper_BETA"] = "Clip to Sharpest Frame ✂️ 🅑🅔🅣🅐"

if LoadTextFromIndex:
    NEW_CLASS_MAPPINGS["LoadTextFromIndex_BETA"] = LoadTextFromIndex
    NEW_DISPLAY_NAME_MAPPINGS["LoadTextFromIndex_BETA"] = "Load Text from index 📼 🅑🅔🅣🅐"

if IndexedLoRALoader:
    NEW_CLASS_MAPPINGS["IndexedLoRALoader_BETA"] = IndexedLoRALoader
    NEW_DISPLAY_NAME_MAPPINGS["IndexedLoRALoader_BETA"] = "Indexed LoRA Loader 🎯 🅑🅔🅣🅐"


# 4. Combine the mappings from all sources
NODE_CLASS_MAPPINGS ={
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
WEB_DIRECTORY = "./js"
__version__ = "1.3.0" # Incremented version for IndexedLoRALoader

# __all__ is important for ComfyUI to find the node mappings
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

# --- Print confirmation message ---
print("--------------------------------------")
print("--- ComfyUI-BETA-Helpernodes ---")
print(f"--- Version: {__version__} ---")
print("--------------------------------------")
# List loaded nodes dynamically from the final mappings
loaded_node_names = list(NODE_DISPLAY_NAME_MAPPINGS.values())
print(f"Nodes loaded ({len(loaded_node_names)}): {', '.join(loaded_node_names)}")
print("--------------------------------------")
