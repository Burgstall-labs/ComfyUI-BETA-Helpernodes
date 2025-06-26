import torch
import numpy as np
import cv2

class SharpestFrameClipper:
    """
    Analyzes a batch of images and returns only the single sharpest frame.
    Uses the variance of the Laplacian method to measure image sharpness.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("sharpest_frame",)
    FUNCTION = "clip_to_sharpest"
    CATEGORY = "Burgstall Enabling The Awesomeness"

    def calculate_sharpness(self, image):
        """
        Calculate the sharpness of an image using the variance of the Laplacian.
        Higher values indicate sharper images.
        """
        # Convert from tensor to numpy array if needed
        if isinstance(image, torch.Tensor):
            # Convert from (H, W, C) torch tensor to numpy array
            img_np = image.cpu().numpy()
        else:
            img_np = image

        # Ensure the image is in the correct format (0-255, uint8)
        if img_np.dtype != np.uint8:
            img_np = (img_np * 255).astype(np.uint8)

        # Convert to grayscale for sharpness calculation
        if len(img_np.shape) == 3 and img_np.shape[2] == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np

        # Calculate the Laplacian of the image and return the variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return laplacian.var()

    def clip_to_sharpest(self, images):
        if images is None:
            return (None,)

        batch_size = images.shape[0]
        if batch_size == 0:
            return (None,)

        # Calculate sharpness for each frame
        sharpness_scores = []
        for i in range(batch_size):
            frame = images[i]
            sharpness = self.calculate_sharpness(frame)
            sharpness_scores.append(sharpness)

        # Find the index of the sharpest frame
        sharpest_idx = np.argmax(sharpness_scores)

        # Return the sharpest frame as a batch of size 1
        sharpest_frame = images[sharpest_idx:sharpest_idx+1]

        return (sharpest_frame,)


class SelectSharpestFrames:
    """
    Selects frames at regular intervals, but chooses the sharpest frame 
    from a window around each interval point.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "interval": ("INT", {"default": 5, "min": 1, "max": 1000, "step": 1}),
                "window_size": ("INT", {"default": 3, "min": 1, "max": 20, "step": 1}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("selected_frames",)
    FUNCTION = "select_sharpest_frames"
    CATEGORY = "Burgstall Enabling The Awesomeness"

    def calculate_sharpness(self, image):
        """
        Calculate the sharpness of an image using the variance of the Laplacian.
        Higher values indicate sharper images.
        """
        # Convert from tensor to numpy array if needed
        if isinstance(image, torch.Tensor):
            # Convert from (H, W, C) torch tensor to numpy array
            img_np = image.cpu().numpy()
        else:
            img_np = image

        # Ensure the image is in the correct format (0-255, uint8)
        if img_np.dtype != np.uint8:
            img_np = (img_np * 255).astype(np.uint8)

        # Convert to grayscale for sharpness calculation
        if len(img_np.shape) == 3 and img_np.shape[2] == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np

        # Calculate the Laplacian of the image and return the variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return laplacian.var()

    def select_sharpest_frames(self, images, interval, window_size):
        if images is None:
            return (None,)

        batch_size = images.shape[0]
        if batch_size == 0:
            return (None,)

        selected_frames = []
        
        # Start from frame 0 and iterate by interval
        current_frame = 0
        
        while current_frame < batch_size:
            # Calculate the window around the current frame
            # We want exactly window_size frames centered around current_frame
            half_window = window_size // 2
            
            # Calculate ideal window boundaries
            ideal_start = current_frame - half_window
            ideal_end = current_frame + half_window + (window_size % 2)
            
            # Clamp to valid frame indices
            window_start = max(0, ideal_start)
            window_end = min(batch_size, ideal_end)
            
            # Calculate sharpness for each frame in the window
            best_sharpness = -1
            best_frame_idx = current_frame
            
            for i in range(window_start, window_end):
                frame = images[i]
                sharpness = self.calculate_sharpness(frame)
                if sharpness > best_sharpness:
                    best_sharpness = sharpness
                    best_frame_idx = i
            
            # Add the sharpest frame from this window
            selected_frames.append(images[best_frame_idx])
            
            # Move to the next interval
            current_frame += interval

        if len(selected_frames) == 0:
            return (None,)

        # Stack the selected frames into a batch
        result = torch.stack(selected_frames, dim=0)
        
        return (result,)


# Node Mappings
NODE_CLASS_MAPPINGS = {
    "SharpestFrameClipper": SharpestFrameClipper,
    "SelectSharpestFrames": SelectSharpestFrames,
}

# Node Display Name Mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "SharpestFrameClipper": "Clip to Sharpest Frame ✂️ 🅑🅔🅣🅐",
    "SelectSharpestFrames": "Select Sharpest Frames 🎯 🅑🅔🅣🅐",
}