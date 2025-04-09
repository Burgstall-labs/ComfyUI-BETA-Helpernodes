# ComfyUI-BETA-Helpernodes

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Custom utility nodes for [ComfyUI](https://github.com/comfyanonymous/ComfyUI), providing helpers for tasks like video frame manipulation and advanced audio saving. Part of the "Burgstall Enabling The Awesomeness" suite.

*(Previously known as ComfyUI-BETA-Cropnodes)*

## Nodes

*   **Video Crop 📼 🅑🅔🅣🅐**: Crops a specified rectangular region from each frame in a batch of images (video frames). Includes an option to round the crop dimensions up to the nearest multiple.
*   **Video Stitch 📼 🅑🅔🅣🅐**: Stitches a batch of previously cropped frames back onto a batch of original frames using metadata provided by the Crop node.
*   **Save Audio Advanced 🔊 🅑🅔🅣🅐**: Saves audio data (received in ComfyUI's standard AUDIO format) to disk as FLAC, WAV, or MP3, with format-specific quality/compression options.

## Features

*   Simple cropping of video frame batches.
*   Ability to round crop width and height up to the nearest multiple (e.g., 8, 16, 32).
*   Outputs crop information (`BETA_CROPINFO`) needed for precise stitching.
*   Stitches processed crops back into their original positions on the full frames.
*   Advanced audio saving to **FLAC**, **WAV**, or **MP3**.
*   Configurable options for WAV encoding (bit depth), FLAC compression level, and MP3 bitrate.
*   Uses ComfyUI's standard output directory and filename prefixing for saved audio.
*   Handles potential dimension mismatches and boundary conditions gracefully (for video nodes).

## Installation

1.  Navigate to your ComfyUI `custom_nodes` directory:
    *   Example: `ComfyUI/custom_nodes/`
2.  Clone this repository:
    ```bash
    git clone https://github.com/Burgstall-labs/ComfyUI-BETA-Helpernodes.git
    ```
    *(Assuming this is the final repository location)*
3.  Restart ComfyUI.

Alternatively, you can download the `.zip` of this repository and extract the `ComfyUI-BETA-Helpernodes` folder into your `ComfyUI/custom_nodes/` directory.

## Usage

### Video Crop 📼 🅑🅔🅣🅐

This node takes a batch of images and crops them.

**Inputs:**

*   `video_frames` (IMAGE): The batch of images (video frames) to crop.
*   `x` (INT): The horizontal starting coordinate (left edge) of the crop area (0-indexed).
*   `y` (INT): The vertical starting coordinate (top edge) of the crop area (0-indexed).
*   `width` (INT): The desired width of the crop area.
*   `height` (INT): The desired height of the crop area.
*   `round_to_multiple` (INT): Rounds the `width` and `height` *up* to the nearest multiple of this value. Set to `1` to disable rounding.

**Outputs:**

*   `cropped_frames` (IMAGE): The batch of cropped images.
*   `crop_info` (BETA_CROPINFO): Metadata used by the Stitch node.

### Video Stitch 📼 🅑🅔🅣🅐

This node takes original frames and cropped frames and puts the cropped section back.

**Inputs:**

*   `original_frames` (IMAGE): The original, uncropped batch of images.
*   `cropped_frames` (IMAGE): The batch of cropped images (e.g., after processing).
*   `crop_info` (BETA_CROPINFO): The output from the `Video Crop` node.

**Outputs:**

*   `stitched_frames` (IMAGE): The original frames with the `cropped_frames` stitched back.

### Save Audio Advanced 🔊 🅑🅔🅣🅐

Saves audio data (waveform and sample rate) to a file in the chosen format.

**Inputs:**

*   `audio` (AUDIO): The audio data tuple `(waveform, sample_rate)` coming from another node (e.g., TTS, Load Audio).
*   `filename_prefix` (STRING): Prefix for the output filename (e.g., "output_audio"). ComfyUI adds date/counters automatically.
*   `format` (STRING): The desired output format. Choose from `flac`, `wav`, `mp3`.
*   `wav_encoding` (STRING, *optional*): For `wav` format. Selects the encoding and bit depth (e.g., `PCM_16`, `PCM_24`, `FLOAT_32`). Defaults to `PCM_16`.
*   `flac_compression` (INT, *optional*): For `flac` format. Sets the compression level (0=fastest, lowest compression; 8=slowest, highest compression). Defaults to `5`.
*   `mp3_bitrate` (INT, *optional*): For `mp3` format. Sets the target bitrate in kbps (e.g., `128`, `192`, `320`). Defaults to `192`. Higher means better quality and larger file size.

**Outputs:**

*   *(Saves file to disk in the ComfyUI `output` directory. No direct data output from the node)*

**Note on MP3 Saving:** Saving to `.mp3` format often requires an external audio encoding library like **LAME**. The easiest way to provide this is usually by installing **FFmpeg** (which typically includes `libmp3lame`) and ensuring it's accessible in your system's PATH environment variable. If MP3 saving fails, check your FFmpeg installation.

## Example Workflows

**Video Cropping/Stitching:**
