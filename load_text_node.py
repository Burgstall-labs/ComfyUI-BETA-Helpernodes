import os

class LoadTextFromIndex:
    """
      A ComfyUI node that loads a specific text file from a specified directory,
      based on a given file index. Supports configurable file extension and encoding.
      """
    def __init__(self):
      pass

    @classmethod
    def INPUT_TYPES(cls):
      return {
          "required": {
            "directory_path": ("STRING", {"multiline": False, "default": ""}),
            "file_index": ("INT", {"default": 0, "min": 0, "step": 1}),
        },
        "optional": {
             "filename_filter": ("STRING", {"multiline": False, "default": ""}),
             "file_extension": ("STRING", {"multiline": False, "default": ".txt"}),
             "encoding": (["utf-8", "latin-1", "ascii", "utf-16"], {"default": "utf-8"}),
        }
      }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("text", "loaded_filename", "file_count")
    FUNCTION = "load_file"
    CATEGORY = "BETA Nodes"

    def load_file(self, directory_path, file_index, filename_filter="", file_extension=".txt", encoding="utf-8"):
      selected_filename = "N/A"
      if not directory_path or not os.path.isdir(directory_path):
        print(f"Warning: Directory path '{directory_path}' is invalid or not found.")
        return ("", "N/A", 0)
      print(f"Scanning directory: {directory_path} with filter: '{filename_filter}', extension: '{file_extension}'")
      try:
          all_files = [f for f in os.listdir(directory_path)
                        if os.path.isfile(os.path.join(directory_path, f))]
          # Ensure extension starts with a dot
          ext = file_extension if file_extension.startswith('.') else f".{file_extension}"
          matched_files = sorted([f for f in all_files if f.lower().endswith(ext.lower()) and (filename_filter.lower() in f.lower() if filename_filter else True)])
      except Exception as e:
          print(f"Error listing files in directory '{directory_path}': {e}")
          return ("", "N/A", 0)

      num_files = len(matched_files)
      if not matched_files:
          print(f"Warning: No '{ext}' files found in '{directory_path}'" + (f" matching filter '{filename_filter}'." if filename_filter else "."))
          return ("", "N/A", 0)
      if file_index >= num_files or file_index < 0:
        print(f"Warning: file index {file_index} out of range, it needs to be between 0 and {num_files-1} ")
        return ("", "N/A", num_files)
      selected_filename = matched_files[file_index]
      full_file_path = os.path.join(directory_path, selected_filename)

      try:
          with open(full_file_path, 'r', encoding=encoding) as f:
              text_content = f.read()
          print(f"Loaded text file ({file_index + 1}/{num_files}): {selected_filename}")
          return (text_content, selected_filename, num_files)
      except Exception as e:
          print(f"Error reading file '{full_file_path}': {e}")
          return ("", selected_filename, num_files)

NODE_CLASS_MAPPINGS = {
    "LoadTextFromIndex": LoadTextFromIndex
 }

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadTextFromIndex": "Load Text from index 📼 🅑🅔🅣🅐"
}
