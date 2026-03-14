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
    Returns the first 5 detected scenes as individual batches, plus remaining frames for chaining.
    """
    MAX_SCENES = 5  # Fixed maximum number of scene outputs

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "threshold": ("FLOAT", {
                    "default": 27.0,
                    "min": 0.0,
                    "max": 100.0,
                    "step": 0.1,
                    "tooltip": "Detection sensitivity threshold. Lower values (e.g., 15-20) detect more scene changes (more sensitive). Higher values (e.g., 30-40) detect fewer scene changes (less sensitive). Default: 27.0"
                }),
            },
            "optional": {
                "fps": ("FLOAT", {
                    "default": 30.0,
                    "min": 1.0,
                    "max": 120.0,
                    "step": 0.1,
                    "tooltip": "Frames per second for scene detection analysis. Match to your source material for accurate timecodes. Default: 30.0"
                }),
                "minimum_scene_length": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 1000,
                    "step": 1,
                    "tooltip": "Minimum number of frames for a scene to be included. Scenes shorter than this are merged with adjacent scenes. Set to 0 to disable. Default: 0"
                }),
            },
        }

    # Build return types: 5 scene outputs + remaining_frames + scene_frames + scene_summary + scene_count
    RETURN_TYPES = tuple("IMAGE" for _ in range(5)) + ("IMAGE", "IMAGE", "STRING", "INT")
    RETURN_NAMES = tuple(f"scene_{i+1}" for i in range(5)) + ("remaining_frames", "scene_frames", "scene_summary", "scene_count")
    FUNCTION = "detect_scenes"
    CATEGORY = "BETA Nodes"

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

    def detect_scenes(self, images, threshold, fps=30.0, minimum_scene_length=0):
        """
        Detect scenes in a batch of images using PySceneDetect.

        Args:
            images: torch.Tensor of shape (batch, height, width, channels)
            threshold: Detection threshold for ContentDetector
            fps: Frames per second for video creation
            minimum_scene_length: Minimum frames per scene (scenes shorter than this are filtered out)

        Returns:
            tuple: (scene_1, ..., scene_5, remaining_frames, scene_frames, scene_summary, scene_count)
        """
        if images is None:
            return tuple([None] * 5) + (None, None, "No images provided", 0)

        batch_size = images.shape[0]
        if batch_size == 0:
            return tuple([None] * 5) + (None, None, "Empty image batch", 0)

        # Create temporary video file
        temp_fd, temp_video_path = tempfile.mkstemp(suffix='.mp4', prefix='scenedetect_')
        os.close(temp_fd)

        try:
            # Convert images to temporary video file using configured fps
            if not self._images_to_video(images, temp_video_path, fps=fps):
                return tuple([None] * 5) + (None, None, "Failed to create temporary video", 0)

            # Use PySceneDetect to detect scenes
            video = open_video(temp_video_path)
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=threshold))
            scene_manager.detect_scenes(video, show_progress=False)
            scene_list = scene_manager.get_scene_list()

            # Extract scene boundaries and individual scene batches
            scene_batches = []
            scene_frame_indices = []
            scene_summary_parts = []

            for i, (start_time, end_time) in enumerate(scene_list):
                start_frame = start_time.frame_num
                next_scene_start = end_time.frame_num

                # Clamp frame indices to valid range
                start_frame = max(0, min(start_frame, batch_size - 1))
                next_scene_start = max(0, min(next_scene_start, batch_size))

                # For the last scene, use the actual last frame of the batch
                if i == len(scene_list) - 1:
                    end_frame = batch_size - 1
                else:
                    end_frame = max(0, next_scene_start - 1)

                end_frame = max(start_frame, end_frame)
                frame_count = end_frame - start_frame + 1

                # Filter by minimum scene length
                if minimum_scene_length > 0 and frame_count < minimum_scene_length:
                    continue

                scene_batch = images[start_frame:end_frame + 1]
                scene_batches.append(scene_batch)

                scene_frame_indices.append(start_frame)
                scene_frame_indices.append(end_frame)

                scene_summary_parts.append(f"Scene {len(scene_batches)}: Frames {start_frame}-{end_frame} [{frame_count} frames]")

            # Handle case where no scenes detected (or all filtered out)
            if len(scene_batches) == 0:
                scene_batches = [images]
                scene_frame_indices = [0, batch_size - 1]
                frame_count = batch_size
                scene_summary_parts = [f"Scene 1: Frames 0-{batch_size - 1} [{frame_count} frames] (No scene changes detected)"]

            # Calculate remaining frames
            last_output_scene_idx = min(self.MAX_SCENES - 1, len(scene_batches) - 1)
            if last_output_scene_idx >= 0 and len(scene_frame_indices) > 0:
                end_frame_idx = last_output_scene_idx * 2 + 1
                if end_frame_idx < len(scene_frame_indices):
                    last_scene_end_frame = scene_frame_indices[end_frame_idx]
                    remaining_start_frame = last_scene_end_frame + 1

                    if remaining_start_frame < batch_size:
                        remaining_frames = images[remaining_start_frame:]
                    else:
                        remaining_frames = None
                else:
                    remaining_frames = None
            else:
                remaining_frames = None

            # Remove duplicates from preview indices while preserving order
            seen = set()
            unique_indices = []
            for idx in scene_frame_indices:
                if idx not in seen:
                    seen.add(idx)
                    unique_indices.append(idx)

            # Create preview frames
            if len(unique_indices) == 0:
                scene_frames = None
            else:
                scene_frames = images[unique_indices]

            # Calculate statistics for summary
            total_scenes_detected = len(scene_list) if len(scene_list) > 0 else 1
            total_scenes_after_filter = len(scene_batches)
            scenes_output = min(self.MAX_SCENES, total_scenes_after_filter)
            remaining_frames_count = remaining_frames.shape[0] if remaining_frames is not None else 0

            # Build enhanced scene summary
            summary_lines = []
            summary_lines.append(f"Processed: {batch_size} frames @ {fps:.1f}fps | Detected: {total_scenes_detected} scenes | After filtering: {total_scenes_after_filter} | Output: {scenes_output} scenes")
            if minimum_scene_length > 0:
                filtered_count = total_scenes_detected - total_scenes_after_filter
                if filtered_count > 0:
                    summary_lines.append(f"Filtered: {filtered_count} scenes shorter than {minimum_scene_length} frames")
            if remaining_frames_count > 0:
                summary_lines.append(f"Remaining: {remaining_frames_count} frames (for chaining)")
            summary_lines.append("---")
            summary_lines.extend(scene_summary_parts[:scenes_output])
            if total_scenes_after_filter > self.MAX_SCENES:
                summary_lines.append(f"... ({total_scenes_after_filter - self.MAX_SCENES} more scenes detected but not output)")

            scene_summary = "\n".join(summary_lines)
            scene_count = total_scenes_after_filter

            # Build return tuple
            scene_outputs = []
            for i in range(self.MAX_SCENES):
                if i < len(scene_batches):
                    scene_outputs.append(scene_batches[i])
                else:
                    scene_outputs.append(None)

            return tuple(scene_outputs) + (remaining_frames, scene_frames, scene_summary, scene_count)

        except Exception as e:
            print(f"Error in scene detection: {e}")
            import traceback
            traceback.print_exc()
            return tuple([None] * 5) + (None, None, f"Error: {str(e)}", 0)

        finally:
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
    "BETASceneDetect": "Scene detect & split 🎥 🅑🅔🅣🅐",
}
