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
                "vram_gb": ("FLOAT", {"default": 24.0, "min": 1.0, "max": 128.0, "step": 0.1}),
                "frame_count": ("INT", {"default": 16, "min": 1, "max": 1000, "step": 1}),
                "target_megapixels": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "override_aspect_ratio": ("FLOAT", {"default": 1.147, "min": 0.1, "max": 10.0, "step": 0.001}),
            },
            "optional": {
                "source_image": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("INT", "INT", "INT", "STRING")
    RETURN_NAMES = ("width", "height", "frame_count", "info")
    FUNCTION = "calculate_wan_resolution"
    CATEGORY = "Burgstall Enabling The Awesomeness"

    def calculate_wan_resolution(self, vram_gb, frame_count, target_megapixels, override_aspect_ratio, source_image=None):
        # Determine actual frame count and aspect ratio
        actual_frame_count = frame_count
        aspect_ratio = override_aspect_ratio
        
        # If source image is provided, extract info from it
        if source_image is not None:
            batch_size, height, width, channels = source_image.shape
            actual_frame_count = batch_size
            source_aspect_ratio = width / height
            aspect_ratio = source_aspect_ratio
            
        # WAN model VRAM efficiency formula
        wan_efficiency_factor = 6.1
        max_pixels_total = vram_gb * wan_efficiency_factor * 1_000_000
        max_pixels_per_frame = max_pixels_total / actual_frame_count
        
        # Determine target pixels per frame
        if target_megapixels > 0:
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
        else:
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