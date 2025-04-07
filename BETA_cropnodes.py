import torch
import numpy as np
import math # Needed for ceiling calculation in rounding

class BETACrop:
    """
    Crops a region from each frame of a video (batch of images),
    with an option to round the width and height up to the nearest multiple.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_frames": ("IMAGE",),
                "x": ("INT", {"default": 0, "min": 0, "max": 8192, "step": 1}),
                "y": ("INT", {"default": 0, "min": 0, "max": 8192, "step": 1}),
                "width": ("INT", {"default": 256, "min": 1, "max": 8192, "step": 1}),
                "height": ("INT", {"default": 256, "min": 1, "max": 8192, "step": 1}),
                "round_to_multiple": ("INT", {"default": 1, "min": 1, "max": 256, "step": 1}), # New input for rounding
            },
        }

    RETURN_TYPES = ("IMAGE", "BETA_CROPINFO")
    RETURN_NAMES = ("cropped_frames", "crop_info")
    FUNCTION = "crop_video"
    CATEGORY = "Burgstall Enabling The Awesomeness" # Updated Category

    # Helper function to round up to the nearest multiple
    def _round_up_to_multiple(self, value, multiple):
        if multiple <= 0: # Avoid division by zero or negative multiples
            return value
        return math.ceil(value / multiple) * multiple

    # Alternative integer-only rounding up function
    def _round_up_to_multiple_int(self, value, multiple):
         if multiple <= 0:
             return value
         if value == 0: # Handle edge case
             return 0
         # Formula: ((value - 1) // multiple + 1) * multiple
         # Or simpler: (value + multiple - 1) // multiple * multiple
         return ((value + multiple - 1) // multiple) * multiple


    def crop_video(self, video_frames, x, y, width, height, round_to_multiple):
        if video_frames is None:
            return (None, None)

        batch_size, full_height, full_width, channels = video_frames.shape

        # --- Initial Validation and Clamping ---
        # Ensure x, y are within bounds [0, max_dim - 1]
        x = max(0, min(x, full_width - 1))
        y = max(0, min(y, full_height - 1))

        # Ensure initial width and height are at least 1 and don't exceed boundaries
        width = max(1, min(width, full_width - x))
        height = max(1, min(height, full_height - y))

        # --- Rounding Logic ---
        final_width = width
        final_height = height

        # Only apply rounding if multiple is greater than 1
        if round_to_multiple > 1:
            # Round the desired width and height *up*
            rounded_width = self._round_up_to_multiple_int(width, round_to_multiple)
            rounded_height = self._round_up_to_multiple_int(height, round_to_multiple)

            # --- IMPORTANT: Re-Clamp after rounding ---
            # Ensure the *rounded* dimensions do not exceed image boundaries from the starting (x, y)
            final_width = min(rounded_width, full_width - x)
            final_height = min(rounded_height, full_height - y)

            # As a safeguard, ensure width/height are still at least 1 after potential clamping
            final_width = max(1, final_width)
            final_height = max(1, final_height)


        # Calculate end coordinates (exclusive) using the final dimensions
        end_x = x + final_width
        end_y = y + final_height

        # Perform the crop using tensor slicing with final dimensions
        cropped_frames = video_frames[:, y:end_y, x:end_x, :]

        # Create crop info dictionary using the *final* dimensions used for cropping
        crop_info = {
            "x": x,
            "y": y,
            "width": final_width,
            "height": final_height,
            "original_width": full_width,
            "original_height": full_height,
            "requested_width": width, # Optionally store original request before rounding
            "requested_height": height, # Optionally store original request before rounding
            "rounded_to_multiple": round_to_multiple
        }
        # print(f"Debug Crop: Input Shape={video_frames.shape}, Req=(x={x},y={y},w={width},h={height}), RoundTo={round_to_multiple}, Final=(w={final_width},h={final_height}), Output Shape={cropped_frames.shape}")

        return (cropped_frames, crop_info)

class BETAStitch:
    """
    Stitches cropped video frames back onto the original video frames based on crop info.
    """
    def __init__(self):
      pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                 "original_frames": ("IMAGE",),
                 "cropped_frames": ("IMAGE",),
                 "crop_info": ("BETA_CROPINFO",), # Use the custom type
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("stitched_frames",)
    FUNCTION = "stitch_video"
    CATEGORY = "Burgstall Enabling The Awesomeness" # Updated Category

    def stitch_video(self, original_frames, cropped_frames, crop_info):
        if cropped_frames is None or crop_info is None or original_frames is None:
            print("Warning: BETAStitch missing required inputs. Returning None.")
            return (None,)

        try:
            x = crop_info["x"]
            y = crop_info["y"]
            # Crop info width/height *should* match the cropped_frames dimensions
            # We rely on cropped_frames.shape for the actual dimensions to stitch
        except KeyError as e:
            print(f"Error: BETAStitch missing key in crop_info: {e}. Returning original frames.")
            return (original_frames,)
        except TypeError:
             print(f"Error: BETAStitch expects crop_info to be a dictionary. Got {type(crop_info)}. Returning original frames.")
             return (original_frames,)

        num_original_frames, full_height, full_width, _ = original_frames.shape
        num_cropped_frames, cropped_height, cropped_width, _ = cropped_frames.shape

        num_frames = min(num_original_frames, num_cropped_frames)

        if num_frames == 0:
             print("Warning: BETAStitch received zero frames to process. Returning None.")
             return (None,)

        # Validate stitch coordinates using the actual cropped frame dimensions
        if x < 0 or y < 0 or (x + cropped_width) > full_width or (y + cropped_height) > full_height:
            print(f"Error: BETAStitch - Crop dimensions derived from input tensor [{cropped_width}x{cropped_height}] at ({x},{y}) would exceed original dimensions [{full_width}x{full_height}]. Returning original frames.")
            return (original_frames[:num_frames].clone(),)

        end_x = x + cropped_width
        end_y = y + cropped_height

        stitched_frames = original_frames[:num_frames].clone()
        stitched_frames[:, y:end_y, x:end_x, :] = cropped_frames[:num_frames]

        # print(f"Debug Stitch: Original Shape={original_frames.shape}, Cropped Shape={cropped_frames.shape}, x={x}, y={y}, Stitch Shape={stitched_frames.shape}")

        return (stitched_frames,)


# Node Mappings
NODE_CLASS_MAPPINGS = {
    "BETACrop": BETACrop,       # Using updated class name
    "BETAStitch": BETAStitch,   # Using updated class name
}

# Node Display Name Mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "BETACrop": "Video Crop 📼 🅑🅔🅣🅐",       # Use new display name and emojis
    "BETAStitch": "Video Stitch 📼 🅑🅔🅣🅐",   # Use new display name and emojis
}
