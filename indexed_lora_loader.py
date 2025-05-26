import os
from folder_paths import get_filename_list, get_full_path
import comfy.sd
import comfy.utils

class IndexedLoRALoader:
    MAX_LORA_SLOTS = 20

    @classmethod
    def INPUT_TYPES(cls):
        try:
            lora_list = ["none"] + get_filename_list("loras")
        except Exception as e:
            print(f"[IndexedLoRALoader Warning] Could not fetch LoRA list: {e}. Defaulting to ['none'].")
            lora_list = ["none"]
            
        optional_inputs = {}
        default_lora = lora_list[0]

        for i in range(1, cls.MAX_LORA_SLOTS + 1):
            optional_inputs[f"lora_{i}"] = (lora_list, {"default": default_lora})
        
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "number_of_loras": ("INT", {"default": 1, "min": 1, "max": cls.MAX_LORA_SLOTS, "step": 1}),
                "index": ("INT", {"default": 1, "min": 1, "max": cls.MAX_LORA_SLOTS, "step": 1}),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
                # Add the new field for the trigger suffix
                "trigger_suffix": ("STRING", {"default": "_lora"}), # New input field
            },
            "optional": optional_inputs
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("model", "clip", "trigger_word")
    FUNCTION = "load_indexed_lora"
    CATEGORY = "BETA Nodes"

    # Add 'trigger_suffix' to the method signature
    def load_indexed_lora(self, model, clip, number_of_loras, index, strength_model, strength_clip, trigger_suffix, **kwargs):
        if not (1 <= index <= number_of_loras):
            print(f"[IndexedLoRALoader] Warning: Index {index} is out of the current LoRA range (1-{number_of_loras}). Returning original model and clip.")
            return (model, clip, "")
        
        lora_key = f"lora_{index}"
        selected_lora_name_from_widget = kwargs.get(lora_key)

        if not selected_lora_name_from_widget or selected_lora_name_from_widget.lower() == "none":
            print(f"[IndexedLoRALoader] Info: LoRA slot '{lora_key}' (index {index}) is not configured or set to 'none'. Returning original model and clip.")
            return (model, clip, "")
        
        # Pass the trigger_suffix to _extract_trigger_word
        trigger_word = self._extract_trigger_word(selected_lora_name_from_widget, trigger_suffix)
        
        lora_path = get_full_path("loras", selected_lora_name_from_widget)
        if not lora_path:
            print(f"[IndexedLoRALoader] Error: LoRA file '{selected_lora_name_from_widget}' not found. Returning original model and clip.")
            return (model, clip, trigger_word if trigger_word else "")

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
        
        return (model_lora, clip_lora, trigger_word)
    
    # Add 'suffix_pattern' to the method signature
    def _extract_trigger_word(self, lora_filename_from_widget, suffix_pattern="_lora"):
        """
        Extract trigger word from LoRA filename using a dynamic suffix pattern.
        Handles filenames that might include subfolder paths.
        Takes the part before the last occurrence of 'suffix_pattern' in the actual filename.
        """
        if not lora_filename_from_widget or lora_filename_from_widget.lower() == "none":
            return ""
        if not suffix_pattern: # If suffix_pattern is empty, just return name without extension
            try:
                base_filename = os.path.basename(lora_filename_from_widget)
                name_without_ext = os.path.splitext(base_filename)[0]
                return name_without_ext.strip()
            except Exception as e:
                print(f"[IndexedLoRALoader Warning] Error processing filename '{lora_filename_from_widget}' with empty suffix: {str(e)}")
                return ""

        try:
            base_filename = os.path.basename(lora_filename_from_widget)
            name_without_ext = os.path.splitext(base_filename)[0]
            
            lower_name_without_ext = name_without_ext.lower()
            # Use the dynamic suffix_pattern (converted to lower case for searching)
            lower_suffix_pattern = suffix_pattern.lower()
            
            # Find the last occurrence of the dynamic suffix
            pattern_suffix_index = lower_name_without_ext.rfind(lower_suffix_pattern)

            if pattern_suffix_index != -1:
                # Check if the found pattern is truly at the end of a component or part of the name.
                # This check ensures we don't split "my_lora_character" if suffix is "_lora" but the full name is "my_lora_character_details"
                # A simple check: is the found pattern actually at the end of name_without_ext (considering case)?
                # Or, is what follows it something like an extension or common versioning that was part of name_without_ext by mistake?
                # For now, we will assume if rfind finds it, it's the intended separator.
                trigger_part = name_without_ext[:pattern_suffix_index]
            else:
                trigger_part = name_without_ext # Fallback to full name without extension if pattern not found
            
            return trigger_part.strip()
            
        except Exception as e:
            print(f"[IndexedLoRALoader Warning] Error extracting trigger word from '{lora_filename_from_widget}' using suffix '{suffix_pattern}': {str(e)}")
            return ""

NODE_CLASS_MAPPINGS = {
    "IndexedLoRALoader_BETA": IndexedLoRALoader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IndexedLoRALoader_BETA": "Indexed LoRA Loader 🎯 🅑🅔🅣🅐"
}
