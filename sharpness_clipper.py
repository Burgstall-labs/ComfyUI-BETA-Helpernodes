import torch
import numpy as np
import cv2

class SharpestFrameClipper:
    """
    Analyzes trailing frames in an image batch to find the sharpest one,
    and clips the batch to include frames up to and including that frame.
    Uses the variance of the Laplacian method to measure image sharpness.
    Optionally skips frames with text overlays or mostly black/white content.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "last_n_frames": ("INT", {"default": 10, "min": 1, "max": 1000, "step": 1}),
                "skip_text_frames": ("BOOLEAN", {"default": False}),
                "skip_black_white_frames": ("BOOLEAN", {"default": False}),
                "black_white_threshold": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.01}),
                "show_debug": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("clipped_images", "sharpest_frame_index")
    FUNCTION = "clip_to_sharpest"
    CATEGORY = "Burgstall Enabling The Awesomeness"

    def _image_to_numpy(self, image):
        """Convert image to numpy array in uint8 format."""
        if isinstance(image, torch.Tensor):
            img_np = image.cpu().numpy()
        else:
            img_np = image
        
        if img_np.dtype != np.uint8:
            img_np = (np.clip(img_np, 0, 1) * 255).astype(np.uint8)
        
        return img_np
    
    def _to_grayscale(self, img_np):
        """Convert image to grayscale."""
        if len(img_np.shape) == 3 and img_np.shape[2] == 3:
            return cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        return img_np
    
    def has_text_features(self, image):
        """
        Detect if an image has significant text-like features.
        Uses edge detection and horizontal/vertical line detection as heuristics.
        """
        img_np = self._image_to_numpy(image)
        gray = self._to_grayscale(img_np)
        
        # Use Canny edge detection to find edges
        edges = cv2.Canny(gray, 50, 150)
        
        # Detect horizontal and vertical lines (common in text)
        # Use HoughLinesP for line detection
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
        
        if lines is None or len(lines) == 0:
            return False
        
        # Count horizontal and vertical lines
        horizontal_count = 0
        vertical_count = 0
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # Check if line is mostly horizontal or vertical
            if abs(y2 - y1) < abs(x2 - x1) * 0.3:  # Horizontal
                horizontal_count += 1
            elif abs(x2 - x1) < abs(y2 - y1) * 0.3:  # Vertical
                vertical_count += 1
        
        # Text typically has many horizontal and vertical lines
        # Threshold: if we have many lines, likely text
        total_lines = len(lines)
        if total_lines > 20 and (horizontal_count > 5 or vertical_count > 5):
            return True
        
        return False
    
    def is_mostly_black_or_white(self, image, threshold):
        """
        Check if an image is mostly black or white.
        threshold: proportion of pixels that must be black/white (0.0 to 1.0)
        """
        img_np = self._image_to_numpy(image)
        gray = self._to_grayscale(img_np)
        
        # Count pixels that are very dark (black) or very bright (white)
        black_pixels = np.sum(gray < 10)  # Very dark
        white_pixels = np.sum(gray > 245)  # Very bright
        total_pixels = gray.size
        
        black_ratio = black_pixels / total_pixels
        white_ratio = white_pixels / total_pixels
        
        # Check if either black or white pixels exceed threshold
        return (black_ratio >= threshold) or (white_ratio >= threshold)
    
    def calculate_sharpness(self, image):
        """
        Calculate the sharpness of an image using the variance of the Laplacian.
        Higher values indicate sharper images.
        """
        img_np = self._image_to_numpy(image)
        gray = self._to_grayscale(img_np)
        
        # Calculate the Laplacian of the image and return the variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return laplacian.var()

    def clip_to_sharpest(self, images, last_n_frames, skip_text_frames, skip_black_white_frames, black_white_threshold, show_debug):
        """
        Analyze trailing frames to find the sharpest one, then clip the batch
        to include frames from the beginning up to and including the sharpest frame.
        """
        if images is None:
            return (None, -1)

        batch_size = images.shape[0]
        if batch_size == 0:
            return (None, -1)
        
        # Determine the range of frames to analyze (last N frames)
        analysis_start = max(0, batch_size - last_n_frames)
        analysis_end = batch_size
        
        if show_debug:
            print(f"[Clip to Sharpest Frame] Analyzing frames {analysis_start} to {analysis_end-1} (last {last_n_frames} frames)")
        
        # Calculate sharpness for frames in the analysis window
        sharpness_scores = []
        frame_info = []
        
        for i in range(analysis_start, analysis_end):
            frame = images[i]
            
            # Check if we should skip this frame
            skip_frame = False
            skip_reason = None
            
            if skip_text_frames:
                if self.has_text_features(frame):
                    skip_frame = True
                    skip_reason = "text"
            
            if not skip_frame and skip_black_white_frames:
                if self.is_mostly_black_or_white(frame, black_white_threshold):
                    skip_frame = True
                    skip_reason = "black/white"
            
            if skip_frame:
                if show_debug:
                    print(f"[Clip to Sharpest Frame] Skipping frame {i} (reason: {skip_reason})")
                continue
            
            # Calculate sharpness for this frame
            sharpness = self.calculate_sharpness(frame)
            sharpness_scores.append(sharpness)
            frame_info.append((i, sharpness))
            
            if show_debug:
                print(f"[Clip to Sharpest Frame] Frame {i}: sharpness = {sharpness:.2f}")
        
        # Check if we have any valid frames
        if len(sharpness_scores) == 0:
            if show_debug:
                print(f"[Clip to Sharpest Frame] No valid frames found after filtering")
            return (None, -1)
        
        # Find the index of the sharpest frame (within the analysis window)
        sharpest_idx_in_window = np.argmax(sharpness_scores)
        sharpest_frame_index = frame_info[sharpest_idx_in_window][0]  # Get original frame index
        
        if show_debug:
            print(f"[Clip to Sharpest Frame] Sharpest frame found at index {sharpest_frame_index} (sharpness: {sharpness_scores[sharpest_idx_in_window]:.2f})")
            print(f"[Clip to Sharpest Frame] Clipping batch to include frames 0 to {sharpest_frame_index} (inclusive)")
        
        # Return the clipped batch: frames from 0 to sharpest_frame_index (inclusive)
        clipped_images = images[:sharpest_frame_index + 1]
        
        return (clipped_images, sharpest_frame_index)


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

    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("selected_frames", "rejected_frames")
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
            return (None, None)

        batch_size = images.shape[0]
        if batch_size == 0:
            return (None, None)

        selected_frames = []
        rejected_frames = []
        
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
            window_frames = []
            
            for i in range(window_start, window_end):
                frame = images[i]
                sharpness = self.calculate_sharpness(frame)
                window_frames.append((i, frame, sharpness))
                if sharpness > best_sharpness:
                    best_sharpness = sharpness
                    best_frame_idx = i
            
            # Add the sharpest frame from this window to selected
            selected_frames.append(images[best_frame_idx])
            
            # Add all other frames from this window to rejected
            for frame_idx, frame, sharpness in window_frames:
                if frame_idx != best_frame_idx:
                    rejected_frames.append(frame)
            
            # Move to the next interval
            current_frame += interval

        # Handle empty results
        if len(selected_frames) == 0:
            return (None, None)
        
        # Stack the selected frames into a batch
        selected_result = torch.stack(selected_frames, dim=0)
        
        # Stack rejected frames if any exist
        if len(rejected_frames) > 0:
            rejected_result = torch.stack(rejected_frames, dim=0)
        else:
            # Return an empty tensor with the same dimensions as selected but 0 batch size
            rejected_result = torch.empty((0,) + selected_result.shape[1:], dtype=selected_result.dtype, device=selected_result.device)
        
        return (selected_result, rejected_result)


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