import os
from folder_paths import get_filename_list, get_full_path
import comfy.sd
import comfy.utils

class IndexedLoRALoader:
    """
    A ComfyUI node that loads a specific LoRA from a configurable stack based on an index input.
    Extracts trigger words from LoRA filenames and provides model/clip outputs.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        lora_list = get_filename_list("loras")
        optional_inputs = {}
        
        # Add a default value if lora_list is empty
        if not lora_list:
            lora_list = ["none"]
            
        # Create LoRA slots numbered as "LoRA #1", "LoRA #2", etc.
        for i in range(1, 21):  # Support up to 20 LoRAs
            optional_inputs[f"LoRA #{i}"] = (lora_list, {"default": lora_list[0]})
        
        return {
            "required": {
                "number_of_loras": ("INT", {"default": 5, "min": 1, "max": 20, "step": 1}),
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "index": ("INT", {"default": 1, "min": 1, "max": 20, "step": 1}),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
            },
            "optional": optional_inputs
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("model", "clip", "trigger_word")
    FUNCTION = "load_indexed_lora"
    CATEGORY = "BETA Nodes"

    def load_indexed_lora(self, number_of_loras, model, clip, index, strength_model, strength_clip, **kwargs):
        """
        Load a LoRA based on the provided index from the configured stack.
        """
        
        # Validate index range
        if index < 1 or index > number_of_loras:
            print(f"[IndexedLoRALoader] Warning: Index {index} is out of range (1-{number_of_loras}). Returning original model and clip.")
            return (model, clip, "")
        
        # Collect available LoRAs from kwargs, excluding "none" - following the same pattern as RandomLoraSelector
        # This ensures ComfyUI only shows the fields that are actually being accessed
        available_loras = [
            kwargs[f"LoRA #{i}"] for i in range(1, number_of_loras + 1) 
            if f"LoRA #{i}" in kwargs and kwargs[f"LoRA #{i}"] and kwargs[f"LoRA #{i}"] != "none"
        ]
        
        # Get the specific LoRA at the requested index
        lora_key = f"LoRA #{index}"
        if (lora_key not in kwargs or 
            not kwargs[lora_key] or 
            kwargs[lora_key] == "none"):
            print(f"[IndexedLoRALoader] Info: LoRA #{index} is not configured or set to 'none'. Returning original model and clip.")
            return (model, clip, "")
        
        selected_lora = kwargs[lora_key]
        
        try:
            # Get the full path to the selected LoRA
            lora_path = get_full_path("loras", selected_lora)
            
            if not os.path.exists(lora_path):
                print(f"[IndexedLoRALoader] Error: LoRA file not found at {lora_path}. Returning original model and clip.")
                return (model, clip, "")
            
            # Extract trigger word from filename
            trigger_word = self._extract_trigger_word(selected_lora)
            
            # Load the LoRA file
            lora_data = comfy.utils.load_torch_file(lora_path, safe_load=True)
            
            # Apply the LoRA to model and clip
            model_with_lora, clip_with_lora = comfy.sd.load_lora_for_models(
                model, clip, lora_data, strength_model, strength_clip
            )
            
            print(f"[IndexedLoRALoader] Successfully loaded LoRA #{index}: {selected_lora}")
            print(f"[IndexedLoRALoader] Extracted trigger word: '{trigger_word}'")
            
            return (model_with_lora, clip_with_lora, trigger_word)
            
        except Exception as e:
            print(f"[IndexedLoRALoader] Error loading LoRA #{index} ({selected_lora}): {str(e)}")
            return (model, clip, "")
    
    def _extract_trigger_word(self, lora_filename):
        """
        Extract trigger word from LoRA filename by taking the part before '_lora'.
        Example: 'Snorricam-3434_lora.safetensors' -> 'Snorricam-3434'
        """
        try:
            # Remove file extension first
            name_without_ext = os.path.splitext(lora_filename)[0]
            
            # Split by '_lora' and take the first part
            if '_lora' in name_without_ext.lower():
                trigger_word = name_without_ext.split('_lora')[0]
            else:
                # If no '_lora' pattern found, use the full filename without extension
                trigger_word = name_without_ext
            
            return trigger_word.strip()
            
        except Exception as e:
            print(f"[IndexedLoRALoader] Warning: Could not extract trigger word from '{lora_filename}': {str(e)}")
            return ""

# Node class mappings for ComfyUI registration
NODE_CLASS_MAPPINGS = {
    "IndexedLoRALoader_BETA": IndexedLoRALoader
}

# Display name mappings with BETA branding
NODE_DISPLAY_NAME_MAPPINGS = {
    "IndexedLoRALoader_BETA": "Indexed LoRA Loader 🎯 🅑🅔🅣🅐"
} 