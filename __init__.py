"""
Custom Nodes for ComfyUI - BETA Helpernodes (includes Crop and Audio nodes)
"""

# 1. Import mappings from the original crop nodes file
# Use aliases to avoid name conflicts if you define mappings directly here later
from .BETA_cropnodes import NODE_CLASS_MAPPINGS as CROP_CLASS_MAPPINGS
from .BETA_cropnodes import NODE_DISPLAY_NAME_MAPPINGS as CROP_DISPLAY_MAPPINGS

# 2. Import the new node class(es) from your new file(s)
from .audio_saver import SaveAudioAdvanced

# 3. Define the mappings for the NEW node(s)
# Ensure the keys are unique across your entire node pack
NEW_CLASS_MAPPINGS = {
    "SaveAudioAdvanced_BETA": SaveAudioAdvanced,
    # Add mappings for other new nodes here if you create more files
}

NEW_DISPLAY_NAME_MAPPINGS = {
    "SaveAudioAdvanced_BETA": "Save Audio Advanced 📼 🅑🅔🅣🅐",
    # Add display names for other new nodes here
}

# 4. Combine the mappings from all sources
# Start with the mappings from the imported files, then update with the new ones
NODE_CLASS_MAPPINGS = {**CROP_CLASS_MAPPINGS, **NEW_CLASS_MAPPINGS}
NODE_DISPLAY_NAME_MAPPINGS = {**CROP_DISPLAY_MAPPINGS, **NEW_DISPLAY_NAME_MAPPINGS}

# --- Optional Metadata and Exports ---

# If you have custom web UI elements, uncomment and point to the correct directory
# WEB_DIRECTORY = "./js"

__version__ = "1.1.0" # Updated version since we added a node

# __all__ is important for ComfyUI to find the node mappings
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

# --- Print confirmation message ---
print("--------------------------------------")
print("--- ComfyUI-BETA-Helpernodes ---") # Updated Name Reflecting Broader Scope
print(f"--- Version: {__version__} ---")
print("--------------------------------------")
# List loaded nodes dynamically from the final mappings
loaded_node_names = list(NODE_DISPLAY_NAME_MAPPINGS.values()) # Get display names
# Or use keys if you prefer the internal names: loaded_node_names = list(NODE_CLASS_MAPPINGS.keys())
print(f"Nodes loaded: {', '.join(loaded_node_names)}")
print("--------------------------------------")
