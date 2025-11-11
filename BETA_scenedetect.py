import torch
import numpy as np
import cv2
import tempfile
import os
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector


class BETASceneDetect:
    """
    Detects scenes in a batch of images using PySceneDetect.
    Returns the start and end frames of each detected scene, plus individual scene batches.
    """
    MAX_SCENES = 50  # Maximum number of scene outputs supported
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "threshold": ("FLOAT", {"default": 27.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "max_scenes": ("INT", {"default": 10, "min": 1, "max": cls.MAX_SCENES, "step": 1}),
            },
        }

    # Build return types: 50 scene outputs + 3 standard outputs
    RETURN_TYPES = tuple("IMAGE" for _ in range(50)) + ("IMAGE", "STRING", "INT")
    RETURN_NAMES = tuple(f"scene_{i+1}" for i in range(50)) + ("scene_frames", "scene_summary", "scene_count")
    FUNCTION = "detect_scenes"
    CATEGORY = "Burgstall Enabling The Awesomeness"

    def _images_to_video(self, images, temp_video_path, fps=30.0):
        """
        Convert a batch of images (torch tensor) to a temporary video file.
        
        Args:
            images: torch.Tensor of shape (batch, height, width, channels) in range [0, 1]
            temp_video_path: Path where the temporary video will be saved
            fps: Frames per second for the video
        
        Returns:
            bool: True if successful, False otherwise
        """
        if images is None or images.shape[0] == 0:
            return False
        
        batch_size, height, width, channels = images.shape
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))
        
        if not video_writer.isOpened():
            print(f"Error: Could not open video writer for {temp_video_path}")
            return False
        
        try:
            # Convert each frame and write to video
            for i in range(batch_size):
                frame = images[i]
                
                # Convert from torch tensor to numpy array
                if isinstance(frame, torch.Tensor):
                    frame_np = frame.cpu().numpy()
                else:
                    frame_np = frame
                
                # Ensure the image is in the correct format (0-255, uint8)
                if frame_np.dtype != np.uint8:
                    frame_np = (np.clip(frame_np, 0, 1) * 255).astype(np.uint8)
                
                # Convert RGB to BGR for OpenCV
                if len(frame_np.shape) == 3 and frame_np.shape[2] == 3:
                    frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
                else:
                    frame_bgr = frame_np
                
                video_writer.write(frame_bgr)
            
            video_writer.release()
            return True
            
        except Exception as e:
            print(f"Error writing video: {e}")
            video_writer.release()
            return False

    def detect_scenes(self, images, threshold, max_scenes):
        """
        Detect scenes in a batch of images using PySceneDetect.
        
        Args:
            images: torch.Tensor of shape (batch, height, width, channels)
            threshold: Detection threshold for ContentDetector
            max_scenes: Maximum number of scene outputs to return
        
        Returns:
            tuple: (scene_1, scene_2, ..., scene_50, scene_frames, scene_summary, scene_count)
                - scene_1 through scene_max_scenes: Individual scene batches (or None if not detected)
                - scene_frames: torch.Tensor with start and end frames of each scene (preview)
                - scene_summary: String describing ALL detected scenes
                - scene_count: Integer count of ALL detected scenes (not limited by max_scenes)
        """
        if images is None:
            # Return None for all scene outputs + error message
            return tuple([None] * self.MAX_SCENES) + (None, "No images provided", 0)
        
        batch_size = images.shape[0]
        if batch_size == 0:
            return tuple([None] * self.MAX_SCENES) + (None, "Empty image batch", 0)
        
        # Create temporary video file
        temp_fd, temp_video_path = tempfile.mkstemp(suffix='.mp4', prefix='scenedetect_')
        os.close(temp_fd)  # Close the file descriptor, we'll use the path
        
        try:
            # Convert images to temporary video file
            if not self._images_to_video(images, temp_video_path):
                return tuple([None] * self.MAX_SCENES) + (None, "Failed to create temporary video", 0)
            
            # Use PySceneDetect to detect scenes
            video = open_video(temp_video_path)
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=threshold))
            scene_manager.detect_scenes(video, show_progress=False)
            scene_list = scene_manager.get_scene_list()
            
            # Extract scene boundaries and individual scene batches
            # Note: PySceneDetect returns scenes where end_time is the start of the next scene
            scene_batches = []  # List of individual scene batches
            scene_frame_indices = []  # For preview (start/end frames)
            scene_summary_parts = []  # For summary text
            
            for i, (start_time, end_time) in enumerate(scene_list):
                # Get frame numbers from timecodes
                start_frame = start_time.frame_num
                next_scene_start = end_time.frame_num
                
                # Clamp frame indices to valid range
                start_frame = max(0, min(start_frame, batch_size - 1))
                next_scene_start = max(0, min(next_scene_start, batch_size))
                
                # For the last scene, use the actual last frame of the batch
                if i == len(scene_list) - 1:
                    end_frame = batch_size - 1
                else:
                    # End frame is one before the next scene starts
                    end_frame = max(0, next_scene_start - 1)
                
                # Ensure end_frame is at least start_frame
                end_frame = max(start_frame, end_frame)
                
                # Extract the full scene batch (all frames from start to end inclusive)
                scene_batch = images[start_frame:end_frame + 1]
                scene_batches.append(scene_batch)
                
                # Add start and end frames for preview
                scene_frame_indices.append(start_frame)
                scene_frame_indices.append(end_frame)
                
                scene_summary_parts.append(f"Scene {i + 1}: Frames {start_frame}-{end_frame}")
            
            # Handle case where no scenes detected
            if len(scene_list) == 0:
                # No scenes detected, return all frames as a single scene
                scene_batches = [images]  # All frames as one scene
                scene_frame_indices = [0, batch_size - 1]
                scene_summary_parts = [f"Scene 1: Frames 0-{batch_size - 1} (No scene changes detected)"]
            
            # Remove duplicates from preview indices while preserving order
            seen = set()
            unique_indices = []
            for idx in scene_frame_indices:
                if idx not in seen:
                    seen.add(idx)
                    unique_indices.append(idx)
            
            # Create preview frames (start and end of each scene)
            if len(unique_indices) == 0:
                scene_frames = None
            else:
                scene_frames = images[unique_indices]
            
            # Build scene summary (includes ALL detected scenes)
            scene_summary = " | ".join(scene_summary_parts)
            scene_count = len(scene_list) if len(scene_list) > 0 else 1
            
            # Build return tuple: individual scene outputs + preview + summary + count
            scene_outputs = []
            for i in range(self.MAX_SCENES):
                if i < len(scene_batches):
                    scene_outputs.append(scene_batches[i])
                else:
                    scene_outputs.append(None)
            
            return tuple(scene_outputs) + (scene_frames, scene_summary, scene_count)
            
        except Exception as e:
            print(f"Error in scene detection: {e}")
            import traceback
            traceback.print_exc()
            return tuple([None] * self.MAX_SCENES) + (None, f"Error: {str(e)}", 0)
            
        finally:
            # Clean up temporary video file
            try:
                if os.path.exists(temp_video_path):
                    os.remove(temp_video_path)
            except Exception as e:
                print(f"Warning: Could not delete temporary video file {temp_video_path}: {e}")


# Node Mappings
NODE_CLASS_MAPPINGS = {
    "BETASceneDetect": BETASceneDetect,
}

# Node Display Name Mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "BETASceneDetect": "Scene Detect 🎥 🅑🅔🅣🅐",
}

