import os
import folder_paths

class LoadTextIncremental:
    """
    A ComfyUI node that loads text files (.txt) sequentially from a specified directory.
    It uses an internal index that increments each time the node is executed,
    cycling through the available text files.
    """
    def __init__(self):
        self.index = 0
        self.cached_files = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {"multiline": False, "default": ""}),
            },
            "optional": {
                 "reset_index": ("INT", {"default": -1, "min": -1, "max": 1, "step": 1}),
                 "filename_filter": ("STRING", {"multiline": False, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("text", "loaded_filename", "current_index")
    FUNCTION = "load_text"
    CATEGORY = "BETA Nodes" # Or any category you prefer (e.g., "loaders", "utils")

    def load_text(self, directory_path, reset_index=-1, filename_filter=""):

        cache_key = f"{directory_path}||{filename_filter}"

        if cache_key not in self.cached_files:
            print(f"Scanning directory: {directory_path} with filter: '{filename_filter}'")
            try:
                all_files = [f for f in os.listdir(directory_path)
                             if os.path.isfile(os.path.join(directory_path, f))]
                txt_files = sorted([
                    f for f in all_files
                    if f.lower().endswith('.txt') and (filename_filter.lower() in f.lower() if filename_filter else True)
                ])
                self.cached_files[cache_key] = txt_files
            except Exception as e:
                print(f"Error listing files in directory '{directory_path}': {e}")
                return ("", "N/A", self.index)
        else:
             txt_files = self.cached_files[cache_key]

        if not directory_path or not os.path.isdir(directory_path):
            print(f"Warning: Directory path '{directory_path}' is invalid or not found.")
            return ("", "N/A", self.index)

        num_files = len(txt_files)

        if reset_index == 0:
            print(f"Resetting index for directory: {directory_path}")
            self.index = 0
        elif reset_index == 1:
             self.index += 10
        current_file_index = self.index % num_files
        if not txt_files:
            print(f"Warning: No '.txt' files found in '{directory_path}'" + (f" matching filter '{filename_filter}'." if filename_filter else "."))
            if cache_key in self.cached_files:
                del self.cached_files[cache_key]
            return ("", "N/A", self.index)

        num_files = len(txt_files)
        full_file_path = os.path.join(directory_path, selected_filename)

        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            print(f"Loaded text file ({current_file_index + 1}/{num_files}): {selected_filename}")
            self.index += 1
            return (text_content, selected_filename, current_file_index)

        except FileNotFoundError:
            print(f"Error: File suddenly not found (shouldn't happen if listing worked): {full_file_path}")
            if cache_key in self.cached_files:
                 del self.cached_files[cache_key]
            return ("", "N/A", self.index)
        except Exception as e:
            print(f"Error reading file '{full_file_path}': {e}")
            return ("", selected_filename, current_file_index)

NODE_CLASS_MAPPINGS = {
    "LoadTextIncremental": LoadTextIncremental
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadTextIncremental": "Load Text Incrementally 📼 🅑🅔🅣🅐"
}