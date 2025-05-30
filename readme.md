# ComfyUI-BETA-Helpernodes

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Custom utility nodes for [ComfyUI](https://github.com/comfyanonymous/ComfyUI), providing helpers for tasks like video frame manipulation and advanced audio saving. Part of the "Burgstall Enabling The Awesomeness" suite.

*(Previously known as ComfyUI-BETA-Cropnodes)*

## Nodes

*   **Video Crop 📼 🅑🅔🅣🅐**: Crops a specified rectangular region from each frame in a batch of images (video frames). Includes an option to round the crop dimensions up to the nearest multiple.
*   **Video Stitch 📼 🅑🅔🅣🅐**: Stitches a batch of previously cropped frames back onto a batch of original frames using metadata provided by the Crop node.
*   **Save Audio Advanced 🔊 🅑🅔🅣🅐**: Saves audio data (received in ComfyUI's standard AUDIO format, or common dictionary formats) to disk as FLAC, WAV, or MP3, with format-specific quality/compression options.
*   **Clip to Sharpest Frame ✂️ 🅑🅔🅣🅐**: Analyzes the last N frames of an image batch for sharpness and clips the batch to include frames up to the sharpest one found (optionally skipping text/blank frames). !!!NOTE!!! The logic for this node was borrowed from somewhere on the internet, but as I had no intention of publishing this until it was requested, I didn't bookmark where I got it. If it's yours, please let me know and I will link and credit accordingly.
*   **Load Text from index 📼 🅑🅔🅣🅐**: Loads a text file (.txt) from a specified directory based on its index in the sorted list of files.
*   **Indexed LoRA Loader 🎯 🅑🅔🅣🅐**: Loads a specific LoRA from a configurable stack based on an index input. Automatically extracts trigger words from LoRA filenames and applies the LoRA to model and CLIP.
*   **Text line count 🅑🅔🅣🅐**: Counts the number of lines in a given multiline text input.
## Features

### Video Crop 📼 🅑🅔🅣🅐
*   Simple cropping of video frame batches with precise coordinate control
*   Ability to round crop width and height up to the nearest multiple (e.g., 8, 16, 32)
*   Outputs crop information (`BETA_CROPINFO`) needed for precise stitching
*   Handles potential dimension mismatches and boundary conditions gracefully

### Video Stitch 📼 🅑🅔🅣🅐
*   Stitches processed crops back into their original positions on the full frames
*   Uses metadata from Video Crop node for pixel-perfect alignment
*   Handles frame count mismatches between original and cropped batches

### Save Audio Advanced 🔊 🅑🅔🅣🅐
*   Advanced audio saving to **FLAC**, **WAV**, or **MP3** formats
*   Configurable options for WAV encoding (bit depth) and FLAC compression level
*   MP3 saving uses the backend's default bitrate settings (user bitrate input currently ignored due to backend API limitations)
*   Handles multiple common AUDIO input formats (standard tuple, wrapped dictionary, plain dictionary)
*   Uses ComfyUI's standard output directory and filename prefixing for saved audio

### Clip to Sharpest Frame ✂️ 🅑🅔🅣🅐
*   Analyzes image batch sharpness using Laplacian variance
*   Clips image batches based on the sharpest frame within a specified trailing window
*   Optionally skips frames with significant text-like features or mostly black/white content during sharpness analysis
*   Outputs the clipped image batch and the index of the sharpest frame identified

### Load Text from Index 📼 🅑🅔🅣🅐
*   Loads text files from a directory based on file index
*   Optional filename filtering for selective file loading
*   Handles .txt file sorting and indexing automatically

### Indexed LoRA Loader 🎯 🅑🅔🅣🅐
*   Loads specific LoRAs from a configurable stack (up to 20 LoRAs) based on index input
*   Automatically extracts trigger words from LoRA filenames (text before "_lora")
*   Applies LoRA to both model and CLIP with configurable strength values
*   Robust error handling with fallback to original model/clip if LoRA fails to load
*   Support for "none" selection to skip LoRA loading

### Text line count 🅑🅔🅣🅐
*   Takes a multiline text string as input.
*   Returns the total number of lines in the text.
*   Handles different newline characters (\n, \r\n, \r).

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

## Dependencies

*   Requires a standard ComfyUI installation (PyTorch, Torchaudio).
*   **OpenCV:** The `Clip to Sharpest Frame` node requires `opencv-python`. Install it via pip: `pip install opencv-python` (or ensure it's in your environment).
*   **MP3 Saving Requirement:** Saving to `.mp3` requires **FFmpeg** (usually including `libmp3lame`) to be installed on your system and accessible in the system's PATH. WAV and FLAC saving do not require external dependencies beyond torchaudio.

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

*   `audio` (AUDIO): The audio data coming from another node (e.g., TTS, Load Audio). Accepts standard `(tensor, rate)` tuple or common `{'waveform': tensor, 'sample_rate': rate}` dictionary formats.
*   `filename_prefix` (STRING): Prefix for the output filename (e.g., "output_audio"). ComfyUI adds date/counters automatically.
*   `format` (STRING): The desired output format. Choose from `flac`, `wav`, `mp3`.
*   `wav_encoding` (STRING, *optional*): For `wav` format. Selects the encoding and bit depth (e.g., `PCM_16`, `PCM_24`, `FLOAT_32`). Defaults to `PCM_16`.
*   `flac_compression` (INT, *optional*): For `flac` format. Sets the compression level (0=fastest, lowest compression; 8=slowest, highest compression). Defaults to `5`.
*   `mp3_bitrate` (INT, *optional*): *(Currently ignored)* Intended to set MP3 bitrate. Uses backend default due to API issues.

**Outputs:**

*   *(Saves file to disk in the ComfyUI `output` directory. Provides UI feedback with filename.)*

### Clip to Sharpest Frame ✂️ 🅑🅔🅣🅐

Analyzes trailing frames in an image batch (e.g., from video) to find the sharpest one, potentially useful for selecting a good frame after motion or transitions. Returns the batch clipped up to that frame.

**Inputs:**

*   `images` (IMAGE): The input batch of images.
*   `last_n_frames` (INT): How many frames from the *end* of the batch to analyze for sharpness.
*   `skip_text_frames` (BOOLEAN): If True, attempts to detect and ignore frames containing significant text overlays during sharpness calculation.
*   `skip_black_white_frames` (BOOLEAN): If True, ignores frames that are mostly black or white during sharpness calculation.
*   `black_white_threshold` (FLOAT): The threshold (proportion of pixels) used to determine if a frame is mostly black or white.
*   `show_debug` (BOOLEAN): If True, prints detailed analysis information to the console.

**Outputs:**

*   `clipped_images` (IMAGE): The image batch containing frames from the beginning up to and including the identified sharpest frame.
*   `sharpest_frame_index` (INT): The index (0-based) within the *original* input batch corresponding to the sharpest frame used for clipping. Returns -1 if no frames were processed (e.g., empty input).

### Load Text Incrementally 📼 🅑🅔🅣🅐
Loads a text file (.txt) from a specified directory based on the provided file index.

**Inputs:**

*   `directory_path` (STRING): The directory path where the text files are located.
*   `file_index` (INT): The index of the file to load from the sorted list of .txt files.
*   `filename_filter` (STRING, *optional*): An optional filter to only load files containing this text (e.g. to only load files containing 'prompt_').

**Outputs:**

*   `text` (STRING): The full text content of the loaded text file.
*   `loaded_filename` (STRING): The filename of the loaded text file.

### Indexed LoRA Loader 🎯 🅑🅔🅣🅐

Loads a specific LoRA from a configurable stack based on an index input. Perfect for batch processing or iterating through different LoRAs systematically.

**Inputs:**

*   `model` (MODEL): The base model to apply the LoRA to.
*   `clip` (CLIP): The CLIP model to apply the LoRA to.
*   `index` (INT): The index (1-based) of the LoRA to load from your configured stack.
*   `number_of_loras` (INT): How many LoRA slots to make available (1-20). Only slots 1 through this number will be visible.
*   `strength_model` (FLOAT): The strength to apply the LoRA to the model (-100.0 to 100.0, default 1.0).
*   `strength_clip` (FLOAT): The strength to apply the LoRA to the CLIP (-100.0 to 100.0, default 1.0).
*   `LoRA #1` through `LoRA #20` (STRING, *optional*): The LoRA files to assign to each slot. Only slots up to `number_of_loras` are shown.

**Outputs:**

*   `model` (MODEL): The model with the selected LoRA applied.
*   `clip` (CLIP): The CLIP with the selected LoRA applied.
*   `trigger_word` (STRING): The extracted trigger word from the LoRA filename (text before "_lora").

**Usage Notes:**

*   Set `number_of_loras` to control how many LoRA slots appear in the interface.
*   LoRA filenames like "Snorricam-3434_lora.safetensors" will extract "Snorricam-3434" as the trigger word.
*   If the specified index is out of range or the LoRA fails to load, the original model and clip are returned unchanged.
*   Set any LoRA slot to "none" to skip loading for that position.

### Text line count 🅑🅔🅣🅐

Counts the number of lines in a multiline text input.

**Inputs:**

*   `text` (STRING): The multiline text to count lines from.

**Outputs:**

*   `line_count` (INT): The total number of lines in the input text.

**Usage Notes:**

*   This node is useful for counting the number of lines in a text input, which can be useful for various text processing tasks.

## Example Workflows

### Save Audio Advanced Example

This workflow demonstrates using the `Save Audio Advanced` node to save the output of a TTS (Text-to-Speech) node.

![Save Audio Advanced Workflow Example](workflow.png)

*(workflow.png located in the repository root)*

### Video Crop / Stitch Example (Face Analysis / Latent Sync)

This example shows how `Video Crop` and `Video Stitch` can be used in a more complex workflow, such as isolating a face identified by FaceAnalysis, processing it (e.g., with IPAdapter or LatentSync techniques), and then stitching the modified face back into the original video frames.

![Video Crop/Stitch Workflow Example](workflow(1).png)

*(workflow(1).png located in the repository root)*


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

*   The ComfyUI team for creating an amazing tool.
*   Kosinkadink for making the awesome VideoHelperSuite (**https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite**) that inspired the naming of the original crop nodes.
