import os
from folder_paths import get_filename_list, get_full_path
import comfy.sd
import comfy.utils

class IndexedLoRALoader:
    MAX_LORA_SLOTS = 20  # Define this as a class constant for clarity

    @classmethod
    def INPUT_TYPES(cls):
        lora_list = get_filename_list("loras")
        optional_inputs = {}
        
        # Add a default value if lora_list is empty
        if not lora_list:
            lora_list = ["none"]
            
        # Define optional LoRA slots using the "lora_i" naming convention
        # The frontend JS should pick up on "number_of_loras" controlling "lora_1", "lora_2", ...
        for i in range(1, cls.MAX_LORA_SLOTS + 1):
            optional_inputs[f"lora_{i}"] = (lora_list, {"default": lora_list[0] if lora_list else "none"})
        
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                # This input name "number_of_loras" is key.
                # Its "max" should match the number of lora_i inputs defined.
                "number_of_loras": ("INT", {"default": 1, "min": 1, "max": cls.MAX_LORA_SLOTS, "step": 1}),
                "index": ("INT", {"default": 1, "min": 1, "max": cls.MAX_LORA_SLOTS, "step": 1}), # Max index can go up to total slots
                "strength_model": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
            },
            "optional": optional_inputs
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("model", "clip", "trigger_word")
    FUNCTION = "load_indexed_lora"
    CATEGORY = "BETA Nodes" # Or your desired category

    def load_indexed_lora(self, model, clip, number_of_loras, index, strength_model, strength_clip, **kwargs):
        # Validate index against the dynamically set number_of_loras
        if not (1 <= index <= number_of_loras):
            print(f"[IndexedLoRALoader] Warning: Index {index} is out of the current LoRA range (1-{number_of_loras}). Returning original model and clip.")
            return (model, clip, "")
        
        # Construct the key for the specific LoRA slot
        lora_key = f"lora_{index}"
        
        # Check if the selected LoRA slot is actually provided in kwargs and is not "none"
        # kwargs should ideally only contain active inputs up to number_of_loras if the UI behaves
        if lora_key not in kwargs or not kwargs[lora_key] or kwargs[lora_key] == "none":
            print(f"[IndexedLoRALoader] Info: LoRA slot '{lora_key}' (index {index}) is not configured, not provided, or set to 'none'. This can happen if index > number_of_loras or the slot was left empty. Returning original model and clip.")
            return (model, clip, "")
        
        selected_lora_name = kwargs[lora_key]
        
        # Extract trigger word (if any)
        trigger_word = self._extract_trigger_word(selected_lora_name)
        
        # Get the full path to the selected LoRA
        lora_path = get_full_path("loras", selected_lora_name)
        if not lora_path: # Check if lora_path is None or empty
            print(f"[IndexedLoRALoader] Error: LoRA file '{selected_lora_name}' not found at path. Returning original model and clip.")
            return (model, clip, "")

        # Load the LoRA file
        try:
            lora_data = comfy.utils.load_torch_file(lora_path, safe_load=True)
        except Exception as e:
            print(f"[IndexedLoRALoader] Error loading LoRA file '{selected_lora_name}': {e}. Returning original model and clip.")
            return (model, clip, "")
            
        # Apply the LoRA
        model_lora, clip_lora = comfy.sd.load_lora_for_models(model, clip, lora_data, strength_model, strength_clip)
        
        print(f"[IndexedLoRALoader] Successfully loaded LoRA from slot '{lora_key}' (index {index}): {selected_lora_name}")
        if trigger_word:
            print(f"[IndexedLoRALoader] Extracted trigger word: '{trigger_word}'")
        
        return (model_lora, clip_lora, trigger_word)
    
    def _extract_trigger_word(self, lora_filename):
        if lora_filename == "none" or not lora_filename:
            return ""
        try:
            name_without_ext = os.path.splitext(lora_filename)[0]
            
            # More robust check for '_lora' as a suffix
            # Check case-insensitively and ensure it's at the end.
            lower_name = name_without_ext.lower()
            if lower_name.endswith('_lora'):
                trigger_word = name_without_ext[:-5] # Remove last 5 chars ('_lora')
            else:
                trigger_word = name_without_ext # Fallback to full name without extension
            
            return trigger_word.strip()
            
        except Exception as e:
            print(f"[IndexedLoRALoader] Warning: Could not extract trigger word from '{lora_filename}': {str(e)}")
            return ""

NODE_CLASS_MAPPINGS = {
    "IndexedLoRALoader_BETA": IndexedLoRALoader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IndexedLoRALoader_BETA": "Indexed LoRA Loader 🎯 🅑🅔🅣🅐"
}
