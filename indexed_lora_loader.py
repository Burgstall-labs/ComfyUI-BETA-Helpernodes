import os
from folder_paths import get_filename_list, get_full_path
import comfy.sd
import comfy.utils

class IndexedLoRALoader:
    @classmethod
    def INPUT_TYPES(cls):
        lora_list = get_filename_list("loras")
        optional_inputs = {}
        
        # Add a default value if lora_list is empty
        if not lora_list:
            lora_list = ["none"] # Keep "none" as a valid option
            
        # Change the naming convention for LoRA slots to lora_1, lora_2, etc.
        for i in range(1, 21): # Defines up to lora_20
            optional_inputs[f"lora_{i}"] = (lora_list, {"default": lora_list[0] if lora_list else "none"})
        
        return {
            "required": {
                "number_of_loras": ("INT", {"default": 1, "min": 1, "max": 20, "step": 1}), # Defaulted to 1, consistent with one slot shown initially
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "index": ("INT", {"default": 1, "min": 1, "max": 20, "step": 1}), # Max for index should ideally be number_of_loras, but UI won't update this dynamically. Runtime check is important.
                "strength_model": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
            },
            "optional": optional_inputs
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("model", "clip", "trigger_word")
    FUNCTION = "load_indexed_lora"
    CATEGORY = "BETA Nodes" # Or your desired category

    def load_indexed_lora(self, number_of_loras, model, clip, index, strength_model, strength_clip, **kwargs):
        # No need to collect available_loras this way if we're just picking one by index.
        # The UI will handle showing the correct number of slots.
        
        # Validate index against the number_of_loras actually configured to be potentially active
        if not (1 <= index <= number_of_loras):
            print(f"[IndexedLoRALoader] Warning: Index {index} is out of the configured LoRA range (1-{number_of_loras}). Returning original model and clip.")
            return (model, clip, "")
        
        # Get the specific LoRA at the requested index using the new naming convention
        lora_key = f"lora_{index}" # Changed from "LoRA #{index}"
        
        # Check if the indexed LoRA slot exists in kwargs and is not "none"
        if lora_key not in kwargs or not kwargs[lora_key] or kwargs[lora_key] == "none":
            print(f"[IndexedLoRALoader] Info: LoRA slot {lora_key} (index {index}) is not configured or set to 'none'. Returning original model and clip.")
            return (model, clip, "")
        
        selected_lora_name = kwargs[lora_key]
        
        # Extract trigger word from filename
        trigger_word = self._extract_trigger_word(selected_lora_name)
        
        # Get the full path to the selected LoRA
        lora_path = get_full_path("loras", selected_lora_name)
        if not lora_path:
            print(f"[IndexedLoRALoader] Error: LoRA file '{selected_lora_name}' not found. Returning original model and clip.")
            return (model, clip, "")

        # Load the LoRA file
        try:
            lora_data = comfy.utils.load_torch_file(lora_path, safe_load=True)
        except Exception as e:
            print(f"[IndexedLoRALoader] Error loading LoRA file '{selected_lora_name}': {e}. Returning original model and clip.")
            return (model, clip, "")
            
        # Apply the LoRA
        model_lora, clip_lora = comfy.sd.load_lora_for_models(model, clip, lora_data, strength_model, strength_clip)
        
        print(f"[IndexedLoRALoader] Successfully loaded LoRA from slot {lora_key} (index {index}): {selected_lora_name}")
        if trigger_word:
            print(f"[IndexedLoRALoader] Extracted trigger word: '{trigger_word}'")
        
        return (model_lora, clip_lora, trigger_word)
    
    def _extract_trigger_word(self, lora_filename):
        """
        Extract trigger word from LoRA filename by taking the part before '_lora'.
        Example: 'Snorricam-3434_lora.safetensors' -> 'Snorricam-3434'
        """
        if lora_filename == "none": # Handle "none" case explicitly
            return ""
        try:
            name_without_ext = os.path.splitext(lora_filename)[0]
            
            # Split by '_lora' (case-insensitive) and take the first part
            parts = name_without_ext.split('_lora')
            if len(parts) > 1 and name_without_ext.lower().rfind('_lora') == len(parts[0]): # Ensure it's a suffix
                 trigger_word = parts[0]
            else: # If no '_lora' pattern found as a suffix, use the full filename without extension
                trigger_word = name_without_ext
            
            return trigger_word.strip()
            
        except Exception as e:
            print(f"[IndexedLoRALoader] Warning: Could not extract trigger word from '{lora_filename}': {str(e)}")
            return ""

# Node class mappings for ComfyUI registration
NODE_CLASS_MAPPINGS = {
    "IndexedLoRALoader_BETA": IndexedLoRALoader # Ensure this matches your registration
}

# Display name mappings with BETA branding
NODE_DISPLAY_NAME_MAPPINGS = {
    "IndexedLoRALoader_BETA": "Indexed LoRA Loader 🎯" # Removed beta symbols for cleaner example, add back if desired
}
