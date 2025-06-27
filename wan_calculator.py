import torch
import math

class WANResolutionCalculator:
    """
    WAN Resolution Calculator - Calculates optimal model-friendly resolution 
    based on VRAM limitations, frame count, and desired megapixel target.
    Uses the WAN model's VRAM efficiency formula.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "vram_gb": ("INT", {"default": 24, "min": 1, "max": 128, "step": 1}),
                "frame_count": ("INT", {"default": 16, "min": 1, "max": 1000, "step": 1}),
                "target_mode": (["Max", "Custom MP"], {"default": "Max"}),
                "target_megapixels": ("FLOAT", {"default": 2.0, "min": 0.1, "max": 100.0, "step": 0.1}),
                "use_custom_aspect_ratio": ("BOOLEAN", {"default": False}),
                "aspect_ratio_preset": (["16:9", "1:1", "4:3", "3:2", "21:9", "9:16", "3:4", "2:3", "9:21", "WAN (1.147:1)", "Custom"], {"default": "WAN (1.147:1)"}),
                "custom_aspect_ratio": ("FLOAT", {"default": 1.147, "min": 0.1, "max": 10.0, "step": 0.001}),
            },
            "optional": {
                "source_image": ("IMAGE",),
                "source_width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 16}),
                "source_height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 16}),
            },
        }

    RETURN_TYPES = ("INT", "INT", "INT", "STRING")
    RETURN_NAMES = ("width", "height", "frame_count", "info")
    FUNCTION = "calculate_wan_resolution"
    CATEGORY = "Burgstall Enabling The Awesomeness"

    def calculate_wan_resolution(self, vram_gb, frame_count, target_mode, target_megapixels, use_custom_aspect_ratio, aspect_ratio_preset, custom_aspect_ratio, source_image=None, source_width=None, source_height=None):
        # Determine actual frame count and aspect ratio
        actual_frame_count = frame_count
        
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
            "WAN (1.147:1)": 1.147,  # 1.147
            "Custom": custom_aspect_ratio
        }
        
        # Determine aspect ratio to use
        if source_image is not None and not use_custom_aspect_ratio:
            # Use source image aspect ratio when available and custom override is disabled
            batch_size, height, width, channels = source_image.shape
            actual_frame_count = batch_size
            aspect_ratio = width / height
            aspect_ratio_source = "source image"
        elif source_width is not None and source_height is not None and not use_custom_aspect_ratio:
            # Use provided width/height aspect ratio when available and custom override is disabled
            aspect_ratio = source_width / source_height
            aspect_ratio_source = f"source dimensions ({source_width}x{source_height})"
        elif use_custom_aspect_ratio:
            # Use custom aspect ratio when override is enabled
            aspect_ratio = aspect_ratios[aspect_ratio_preset]
            aspect_ratio_source = f"custom ({aspect_ratio_preset})"
        else:
            # Default to WAN aspect ratio when no source and no custom override
            aspect_ratio = aspect_ratios["WAN (1.147:1)"]
            aspect_ratio_source = "default (WAN 1.147:1)"
            
        # WAN model VRAM efficiency formula
        wan_efficiency_factor = 6.1
        max_pixels_total = vram_gb * wan_efficiency_factor * 1_000_000
        max_pixels_per_frame = max_pixels_total / actual_frame_count
        
        # Determine target pixels per frame
        if target_mode == "Custom MP":
            # User specified target megapixels
            target_pixels_per_frame = target_megapixels * 1_000_000
            
            # Check if target is achievable within VRAM limit
            if target_pixels_per_frame > max_pixels_per_frame:
                # Cap at VRAM limit
                final_pixels_per_frame = max_pixels_per_frame
                info_message = f"Target {target_megapixels:.1f}MP exceeds VRAM limit. Capped to {final_pixels_per_frame/1_000_000:.2f}MP per frame."
            else:
                final_pixels_per_frame = target_pixels_per_frame
                info_message = f"Target {target_megapixels:.1f}MP achieved within VRAM limit."
        else:  # target_mode == "Max"
            # Use maximum possible based on VRAM
            final_pixels_per_frame = max_pixels_per_frame
            info_message = f"Maximum resolution calculated: {final_pixels_per_frame/1_000_000:.2f}MP per frame."
        
        # Calculate dimensions using aspect ratio
        # For aspect ratio (width = height × aspect_ratio)
        # pixels = width × height = height² × aspect_ratio
        # Therefore: height = sqrt(pixels / aspect_ratio)
        height = math.sqrt(final_pixels_per_frame / aspect_ratio)
        width = height * aspect_ratio
        
        # Round to multiples of 16 (model-friendly)
        final_width = int(width // 16) * 16
        final_height = int(height // 16) * 16
        
        # Add additional info about the calculation
        actual_megapixels = (final_width * final_height) / 1_000_000
        total_megapixels = actual_megapixels * actual_frame_count
        vram_usage_estimate = total_megapixels / wan_efficiency_factor
        
        detailed_info = (f"{info_message} "
                        f"Final: {final_width}x{final_height} ({actual_megapixels:.2f}MP), "
                        f"{actual_frame_count} frames, "
                        f"Aspect: {aspect_ratio:.3f} ({aspect_ratio_source}), "
                        f"Total: {total_megapixels:.1f}MP, "
                        f"Est. VRAM: {vram_usage_estimate:.1f}GB")
        
        return (final_width, final_height, actual_frame_count, detailed_info)


# Node Mappings
NODE_CLASS_MAPPINGS = {
    "WANResolutionCalculator": WANResolutionCalculator,
}

# Node Display Name Mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "WANResolutionCalculator": "WAN Resolution Calculator 📏 🅑🅔🅣🅐",
} 