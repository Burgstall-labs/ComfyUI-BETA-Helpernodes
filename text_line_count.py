class TextLineCount:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("line_count",)
    FUNCTION = "count_lines"
    CATEGORY = "BETA Nodes"

    def count_lines(self, text):
        if not text:
            return (0,)
        # Split by newline characters, including \r\n, \n, and \r
        lines = text.splitlines()
        return (len(lines),)

NODE_CLASS_MAPPINGS = {
    "TextLineCount": TextLineCount
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextLineCount": "Text line count 🅑🅔🅣🅐"
} 