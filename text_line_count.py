class TextLineCount:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "count_empty_lines": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("line_count",)
    FUNCTION = "count_lines"
    CATEGORY = "BETA Nodes"

    def count_lines(self, text, count_empty_lines=True):
        if not text:
            return (0,)
        lines = text.splitlines()
        if not count_empty_lines:
            lines = [line for line in lines if line.strip()]
        return (len(lines),)

NODE_CLASS_MAPPINGS = {
    "TextLineCount": TextLineCount
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextLineCount": "Text line count 🅑🅔🅣🅐"
}
