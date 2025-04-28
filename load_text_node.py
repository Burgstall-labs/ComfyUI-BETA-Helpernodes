import os

class LoadTextFile:
    """
    A ComfyUI node that loads a specific text file (.txt) from a specified directory,
    based on a given file index.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {"multiline": False, "default": ""}),                
                "file_index": ("INT", {"default": 0, "min": 0, "step": 1}), # New input
            },
            "optional": {
                 "filename_filter": ("STRING", {"multiline": False, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("text", "loaded_filename")
    FUNCTION = "load_file"
    CATEGORY = "BETA Nodes"

    def load_file(self, directory_path, file_index, filename_filter=""):

        selected_filename = "N/A"
        full_file_path = "N/A"
        if not directory_path or not os.path.isdir(directory_path):
            print(f"Warning: Directory path '{directory_path}' is invalid or not found.")
            return ("", "N/A")
        print(f"Scanning directory: {directory_path} with filter: '{filename_filter}'")
        try:
            all_files = [f for f in os.listdir(directory_path)
                         if os.path.isfile(os.path.join(directory_path, f))]
            txt_files = sorted([f for f in all_files if f.lower().endswith('.txt') and (filename_filter.lower() in f.lower() if filename_filter else True)])
        except Exception as e:
            print(f"Error listing files in directory '{directory_path}': {e}")
            return ("", "N/A")

        if not txt_files:
            print(f"Warning: No '.txt' files found in '{directory_path}'" + (f" matching filter '{filename_filter}'." if filename_filter else "."))
            return ("", "N/A")
        num_files = len(txt_files)
        if file_index >= num_files or file_index < 0:
            print(f"Warning: file index {file_index} out of range, it needs to be between 0 and {num_files-1} ")
            return ("", "N/A")
        selected_filename = txt_files[file_index]
        full_file_path = os.path.join(directory_path, selected_filename)
        
        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            print(f"Loaded text file ({file_index + 1}/{num_files}): {selected_filename}")
            return (text_content, selected_filename)
        except Exception as e:
            print(f"Error reading file '{full_file_path}': {e}")
            return ("", selected_filename)

NODE_CLASS_MAPPINGS = {
    "LoadTextFile": LoadTextFile
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadTextFile": "Load Text File 📼 🅑🅔🅣🅐"
}