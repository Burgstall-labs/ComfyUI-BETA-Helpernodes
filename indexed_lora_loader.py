import os
from folder_paths import get_filename_list, get_full_path
import comfy.sd
import comfy.utils

class IndexedLoRALoader:
    MAX_LORA_SLOTS = 20  # Define this as a class constant for clarity

    @classmethod
    def INPUT_TYPES(cls):
        try:
            # Prepend "none" to the list and handle empty list case
            lora_list = ["none"] + get_filename_list("loras")
        except Exception as e:
            print(f"[IndexedLoRALoader Warning] Could not fetch LoRA list: {e}. Defaulting to ['none'].")
            lora_list = ["none"]
            
        optional_inputs = {}
        default_lora = lora_list[0] # Will be "none" if list fetching failed or list was empty

        for i in range(1, cls.MAX_LORA_SLOTS + 1):
            optional_inputs[f"lora_{i}"] = (lora_list, {"default": default_lora})
        
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "number_of_loras": ("INT", {"default": 1, "min": 1, "max": cls.MAX_LORA_SLOTS, "step": 1}),
                "index": ("INT", {"default": 1, "min": 1, "max": cls.MAX_LORA_SLOTS, "step": 1}),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}), # Your original range
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}), # Your original range
            },
            "optional": optional_inputs
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("model", "clip", "trigger_word")
    FUNCTION = "load_indexed_lora"
    CATEGORY = "BETA Nodes"

    def load_indexed_lora(self, model, clip, number_of_loras, index, strength_model, strength_clip, **kwargs):
        if not (1 <= index <= number_of_loras):
            print(f"[IndexedLoRALoader] Warning: Index {index} is out of the current LoRA range (1-{number_of_loras}). Returning original model and clip.")
            return (model, clip, "")
        
        lora_key = f"lora_{index}"
        
        selected_lora_name_from_widget = kwargs.get(lora_key) # Use .get() for slightly safer access

        if not selected_lora_name_from_widget or selected_lora_name_from_widget.lower() == "none":
            print(f"[IndexedLoRALoader] Info: LoRA slot '{lora_key}' (index {index}) is not configured, not provided, or set to 'none'. Returning original model and clip.")
            return (model, clip, "")
        
        # DEBUG: To see the raw value from the widget
        # print(f"[IndexedLoRALoader Debug] Value from widget '{lora_key}': {selected_lora_name_from_widget}")

        trigger_word = self._extract_trigger_word(selected_lora_name_from_widget)
        
        lora_path = get_full_path("loras", selected_lora_name_from_widget)
        if not lora_path:
            print(f"[IndexedLoRALoader] Error: LoRA file '{selected_lora_name_from_widget}' not found. Returning original model and clip.")
            return (model, clip, trigger_word if trigger_word else "") # Return extracted trigger word even if path fails

        try:
            lora_data = comfy.utils.load_torch_file(lora_path, safe_load=True)
        except Exception as e:
            print(f"[IndexedLoRALoader] Error loading LoRA file '{selected_lora_name_from_widget}' from path '{lora_path}': {e}. Returning original model and clip.")
            return (model, clip, trigger_word if trigger_word else "")

        try:
            model_lora, clip_lora = comfy.sd.load_lora_for_models(model, clip, lora_data, strength_model, strength_clip)
        except Exception as e:
            print(f"[IndexedLoRALoader] Error applying LoRA '{selected_lora_name_from_widget}' to models: {e}. Returning original model and clip.")
            return (model, clip, trigger_word if trigger_word else "")
        
        # print(f"[IndexedLoRALoader] Successfully loaded LoRA from slot '{lora_key}': {selected_lora_name_from_widget}")
        # if trigger_word:
        #     print(f"[IndexedLoRALoader] Extracted trigger word: '{trigger_word}'")
        
        return (model_lora, clip_lora, trigger_word)
    
    def _extract_trigger_word(self, lora_filename_from_widget):
        """
        Extract trigger word from LoRA filename.
        Handles filenames that might include subfolder paths.
        Takes the part before the last '_lora' suffix in the actual filename.
        """
        if not lora_filename_from_widget or lora_filename_from_widget.lower() == "none":
            return ""
        try:
            # Get only the filename part, discarding any subfolder paths
            base_filename = os.path.basename(lora_filename_from_widget)
            
            # Remove the file extension (e.g., .safetensors, .pt, .bin)
            name_without_ext = os.path.splitext(base_filename)[0]
            
            # Find the last occurrence of '_lora' (case-insensitive search for the pattern)
            # We operate on name_without_ext for this search
            lower_name_without_ext = name_without_ext.lower()
            lora_suffix_index = lower_name_without_ext.rfind("_lora") # rfind finds the last occurrence

            if lora_suffix_index != -1:
                # Take the part of the original-case 'name_without_ext' before this found suffix
                trigger_part = name_without_ext[:lora_suffix_index]
            else:
                # If no '_lora' pattern found as a suffix, use the full 'name_without_ext'
                trigger_part = name_without_ext
            
            return trigger_part.strip()
            
        except Exception as e:
            print(f"[IndexedLoRALoader Warning] Error extracting trigger word from '{lora_filename_from_widget}': {str(e)}")
            return "" # Return empty string on error

NODE_CLASS_MAPPINGS = {
    "IndexedLoRALoader_BETA": IndexedLoRALoader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IndexedLoRALoader_BETA": "Indexed LoRA Loader 🎯 🅑🅔🅣🅐"
}
