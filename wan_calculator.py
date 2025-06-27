import torch
import math

class WANResolutionCalculator:
    """
    WAN Resolution Calculator - Calculates optimal model-friendly resolution 
    based on desired megapixel target and aspect ratio.
    Outputs dimensions rounded to multiples of 16 for model compatibility.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "target_megapixels": ("FLOAT", {"default": 2.0, "min": 0.1, "max": 100.0, "step": 0.1}),
                "use_custom_aspect_ratio": ("BOOLEAN", {"default": False}),
                "aspect_ratio_preset": (["16:9", "1:1", "4:3", "3:2", "21:9", "9:16", "3:4", "2:3", "9:21", "Custom"], {"default": "16:9"}),
                "custom_aspect_ratio": ("FLOAT", {"default": 1.147, "min": 0.1, "max": 10.0, "step": 0.001}),
                "source_width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 16}),
                "source_height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 16}),
            },
            "optional": {
                "source_image": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("INT", "INT", "STRING")
    RETURN_NAMES = ("width", "height", "info")
    FUNCTION = "calculate_wan_resolution"
    CATEGORY = "Burgstall Enabling The Awesomeness"

    def calculate_wan_resolution(self, target_megapixels, use_custom_aspect_ratio, aspect_ratio_preset, custom_aspect_ratio, source_width, source_height, source_image=None):
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
        
        # Determine aspect ratio to use
        if use_custom_aspect_ratio:
            # Use custom aspect ratio when override is enabled
            aspect_ratio = aspect_ratios[aspect_ratio_preset]
            aspect_ratio_source = f"custom ({aspect_ratio_preset})"
        elif source_width and source_height:
            # Use provided width/height aspect ratio (priority over source image)
            aspect_ratio = source_width / source_height
            aspect_ratio_source = f"source dimensions ({source_width}x{source_height})"
        elif source_image is not None:
            # Use source image aspect ratio as fallback
            batch_size, height, width, channels = source_image.shape
            aspect_ratio = width / height
            aspect_ratio_source = "source image"
        else:
            # Default to 16:9 when no other source is available
            aspect_ratio = aspect_ratios["16:9"]
            aspect_ratio_source = "default (16:9)"
            
        # Calculate target pixels from megapixels
        target_pixels = target_megapixels * 1_000_000
        
        # Calculate dimensions using aspect ratio
        # For aspect ratio (width = height × aspect_ratio)
        # pixels = width × height = height² × aspect_ratio
        # Therefore: height = sqrt(pixels / aspect_ratio)
        height = math.sqrt(target_pixels / aspect_ratio)
        width = height * aspect_ratio
        
        # Round to multiples of 16 (model-friendly)
        final_width = int(width // 16) * 16
        final_height = int(height // 16) * 16
        
        # Calculate actual megapixels after rounding
        actual_megapixels = (final_width * final_height) / 1_000_000
        
        detailed_info = (f"Target: {target_megapixels:.1f}MP, "
                        f"Final: {final_width}x{final_height} ({actual_megapixels:.2f}MP), "
                        f"Aspect: {aspect_ratio:.3f} ({aspect_ratio_source})")
        
        return (final_width, final_height, detailed_info)


# Node Mappings
NODE_CLASS_MAPPINGS = {
    "WANResolutionCalculator": WANResolutionCalculator,
}

# Node Display Name Mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "WANResolutionCalculator": "WAN Resolution Calculator 📏 🅑🅔🅣🅐",
} 