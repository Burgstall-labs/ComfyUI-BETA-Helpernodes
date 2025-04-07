# ComfyUI-BETA-Cropnodes

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Custom nodes for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) designed for cropping and stitching video frames (image batches). Part of the "Burgstall Enabling The Awesomeness" suite.

## Nodes

*   **Video Crop 📼 🅑🅔🅣🅐**: Crops a specified rectangular region from each frame in a batch of images (video frames). Includes an option to round the crop dimensions up to the nearest multiple.
*   **Video Stitch 📼 🅑🅔🅣🅐**: Stitches a batch of previously cropped frames back onto a batch of original frames using metadata provided by the Crop node.

## Features

*   Simple cropping of video frame batches.
*   Ability to round crop width and height up to the nearest multiple (e.g., 8, 16, 32) for compatibility with models requiring specific input sizes.
*   Outputs crop information (`BETA_CROPINFO`) needed for precise stitching.
*   Stitches processed crops back into their original positions on the full frames.
*   Handles potential dimension mismatches and boundary conditions gracefully.

## Installation

1.  Navigate to your ComfyUI `custom_nodes` directory:
    *   Example: `ComfyUI/custom_nodes/`
2.  Clone this repository:
    ```bash
    git clone https://github.com/YourUsername/ComfyUI-BETA-Cropnodes.git
    ```
    (Replace `YourUsername` with your actual GitHub username once you create the repository).
3.  Restart ComfyUI.

Alternatively, you can download the `.zip` of this repository and extract the `ComfyUI-BETA-Cropnodes` folder into your `ComfyUI/custom_nodes/` directory.

## Usage

### Video Crop 📼 🅑🅔🅣🅐

This node takes a batch of images and crops them.

**Inputs:**

*   `video_frames` (IMAGE): The batch of images (video frames) to crop.
*   `x` (INT): The horizontal starting coordinate (left edge) of the crop area (0-indexed).
*   `y` (INT): The vertical starting coordinate (top edge) of the crop area (0-indexed).
*   `width` (INT): The desired width of the crop area.
*   `height` (INT): The desired height of the crop area.
*   `round_to_multiple` (INT): Rounds the `width` and `height` *up* to the nearest multiple of this value. Set to `1` to disable rounding. Note: The final dimensions might still be clamped if rounding exceeds image boundaries.

**Outputs:**

*   `cropped_frames` (IMAGE): The batch of cropped images.
*   `crop_info` (BETA_CROPINFO): A dictionary containing information about the crop (`x`, `y`, final `width`, final `height`, original dimensions, etc.), used by the Stitch node.

### Video Stitch 📼 🅑🅔🅣🅐

This node takes original frames and cropped frames and puts the cropped section back.

**Inputs:**

*   `original_frames` (IMAGE): The original, uncropped batch of images. Must match the dimensions from which `crop_info` was generated.
*   `cropped_frames` (IMAGE): The batch of cropped images (e.g., after processing like upscaling or generation). The number of frames should ideally match `original_frames`, but the node will process the minimum of the two.
*   `crop_info` (BETA_CROPINFO): The output from the `Video Crop` node, telling the stitcher where to place the `cropped_frames`.

**Outputs:**

*   `stitched_frames` (IMAGE): The original frames with the `cropped_frames` stitched back into the correct location.

## Example Workflow

[Load Video Frames] -> [Video Crop] -> [Process Cropped Area (e.g., Upscale, RIFE, Style Transfer)] -> [Video Stitch] -> [Save/Preview Video]
| ^
| (original_frames) | (cropped_frames)
+---------------------+
| (crop_info)
+--------------------->

      
## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

*   The ComfyUI team for creating an amazing tool.
*   Kosinkadink for making the awesome VideoHelperSuite (**https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite**) that inspired the naming of this humble effort :D

    
