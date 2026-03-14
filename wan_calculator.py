import math

class WANResolutionCalculator:
    """
    WAN Resolution Calculator - Calculates optimal model-friendly resolution
    based on desired megapixel target and aspect ratio.
    Outputs dimensions rounded to a configurable multiple for model compatibility.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "frame_count": ("INT", {"default": 16, "min": 1, "max": 1000, "step": 1}),
                "target_megapixels": ("FLOAT", {"default": 2.0, "min": 0.1, "max": 100.0, "step": 0.1}),
                "use_custom_aspect_ratio": ("BOOLEAN", {"default": False}),
                "aspect_ratio_preset": (["16:9", "1:1", "4:3", "3:2", "21:9", "9:16", "3:4", "2:3", "9:21", "Custom"], {"default": "16:9"}),
                "custom_aspect_ratio": ("FLOAT", {"default": 1.147, "min": 0.1, "max": 10.0, "step": 0.001}),
                "source_width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 16}),
                "source_height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 16}),
            },
            "optional": {
                "source_image": ("IMAGE",),
                "rounding_multiple": ([8, 16, 32, 64], {"default": 16}),
            },
        }

    RETURN_TYPES = ("INT", "INT", "INT", "STRING")
    RETURN_NAMES = ("width", "height", "frame_count", "info")
    FUNCTION = "calculate_wan_resolution"
    CATEGORY = "BETA Nodes"

    def calculate_wan_resolution(self, frame_count, target_megapixels, use_custom_aspect_ratio, aspect_ratio_preset, custom_aspect_ratio, source_width, source_height, source_image=None, rounding_multiple=16):
        # Define aspect ratio presets
        aspect_ratios = {
            "16:9": 16/9,      # 1.778
            "1:1": 1.0,        # 1.000
            "4:3": 4/3,        # 1.333
            "3:2": 3/2,        # 1.500
            "21:9": 21/9,      # 2.333
            "9:16": 9/16,      # 0.563
            "3:4": 3/4,        # 0.750
            "2:3": 2/3,        # 0.667
            "9:21": 9/21,      # 0.429
            "Custom": custom_aspect_ratio
        }

        # Determine actual frame count and aspect ratio
        actual_frame_count = frame_count

        # Determine aspect ratio to use - prioritize source image first
        if source_image is not None and not use_custom_aspect_ratio:
            batch_size, height, width, channels = source_image.shape
            actual_frame_count = batch_size
            aspect_ratio = width / height
            aspect_ratio_source = "source image"
        elif not use_custom_aspect_ratio and source_width and source_height:
            aspect_ratio = source_width / source_height
            aspect_ratio_source = f"source dimensions ({source_width}x{source_height})"
        elif use_custom_aspect_ratio:
            aspect_ratio = aspect_ratios[aspect_ratio_preset]
            aspect_ratio_source = f"custom ({aspect_ratio_preset})"
        else:
            aspect_ratio = aspect_ratios["16:9"]
            aspect_ratio_source = "default (16:9)"

        # Calculate target pixels from megapixels
        target_pixels = target_megapixels * 1_000_000

        # Calculate dimensions using aspect ratio
        height = math.sqrt(target_pixels / aspect_ratio)
        width = height * aspect_ratio

        # Round to configurable multiple (model-friendly)
        m = rounding_multiple
        final_width = int(width // m) * m
        final_height = int(height // m) * m

        # Calculate actual megapixels after rounding
        actual_megapixels = (final_width * final_height) / 1_000_000

        detailed_info = (f"Target: {target_megapixels:.1f}MP, "
                        f"Final: {final_width}x{final_height} ({actual_megapixels:.2f}MP), "
                        f"{actual_frame_count} frames, "
                        f"Aspect: {aspect_ratio:.3f} ({aspect_ratio_source}), "
                        f"Rounded to: {m}px")

        return (final_width, final_height, actual_frame_count, detailed_info)


# Node Mappings
NODE_CLASS_MAPPINGS = {
    "WANResolutionCalculator": WANResolutionCalculator,
}

# Node Display Name Mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "WANResolutionCalculator": "WAN Resolution Calculator 📏 🅑🅔🅣🅐",
}
