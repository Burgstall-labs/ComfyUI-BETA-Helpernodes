# CLAUDE.md

## Project Overview

ComfyUI-BETA-Helpernodes is a custom nodes package for [ComfyUI](https://github.com/comfyanonymous/ComfyUI), part of the "Burgstall Enabling The Awesomeness" (BETA) suite. It provides utility nodes for video manipulation, audio processing, image analysis, and workflow automation.

**Version**: 1.3.0
**License**: MIT

## Repository Structure

```
ComfyUI-BETA-Helpernodes/
├── __init__.py                 # Node registration (combines all node mappings)
├── BETA_cropnodes.py           # Video Crop & Stitch nodes
├── BETA_scenedetect.py         # Scene detection & splitting
├── audio_saver.py              # Advanced audio saving (FLAC/WAV/MP3)
├── sharpness_clipper.py        # Frame sharpness analysis (2 nodes)
├── wan_calculator.py           # WAN model resolution calculator
├── load_text_node.py           # Text file loader by index
├── indexed_lora_loader.py      # LoRA stack/index loader (up to 20 slots)
├── text_line_count.py          # Text line counter
├── js/
│   └── betaHelperNodes.js      # Frontend JS (dynamic widget management)
├── requirements.txt            # numpy, opencv-python, scenedetect[opencv]
├── readme.md                   # User-facing documentation
└── LICENSE                     # MIT
```

## Node Registration Pattern

Every node file follows this pattern — **maintain it when adding new nodes**:

1. Define a class with:
   - `INPUT_TYPES()` classmethod returning `{"required": {...}, "optional": {...}}`
   - `RETURN_TYPES` tuple
   - `RETURN_NAMES` tuple
   - `FUNCTION` string (method name to call)
   - `CATEGORY` string (use `"Burgstall Enabling The Awesomeness"` or `"BETA Nodes"`)
   - The execution method itself

2. At module level, export:
   - `NODE_CLASS_MAPPINGS = {"InternalName": ClassName}`
   - `NODE_DISPLAY_NAME_MAPPINGS = {"InternalName": "Display Name"}`

3. In `__init__.py`, add a try-except import block:
   ```python
   try:
       from .module_name import NODE_CLASS_MAPPINGS as X_MAPPINGS
       from .module_name import NODE_DISPLAY_NAME_MAPPINGS as X_NAME_MAPPINGS
   except ImportError as e:
       print(f"[BETA Helper Nodes] Failed to import ...: {e}")
   ```
   Then merge into the combined dictionaries.

## Dependencies

**Python** (in `requirements.txt`):
- `numpy` — array operations
- `opencv-python` — image processing (Laplacian, edge detection)
- `scenedetect[opencv]` — scene boundary detection

**ComfyUI internals** (available at runtime):
- `torch`, `torchaudio` — tensor and audio operations
- `folder_paths` — ComfyUI path management
- `comfy.sd`, `comfy.utils` — LoRA loading, utilities

**System-level**:
- FFmpeg with libmp3lame (required only for MP3 audio export)

## Development Conventions

### Code Style
- **No formatter/linter configured** — follow existing style
- Snake_case for functions and variables, CamelCase for classes
- Use `print()` with `[BETA Helper Nodes]` or similar prefix for debug/error logging
- No type hints currently used — don't add them to unchanged code
- Keep inline comments for complex logic

### Key Patterns
- **Input validation**: Always validate and clamp user inputs (coordinates, indices, dimensions)
- **Graceful degradation**: Return sensible defaults on error rather than crashing
- **Multiple input formats**: Some ComfyUI types (e.g., AUDIO) come in different shapes — handle all variants (see `audio_saver.py` for an example)
- **Round to multiples**: Dimensions for AI models often need rounding to 8 or 16
- **Custom data types**: Use dictionaries for passing metadata between nodes (e.g., `BETA_CROPINFO`)

### Frontend (JavaScript)
- `js/betaHelperNodes.js` handles dynamic widget visibility for the Indexed LoRA Loader
- Uses ComfyUI's `app.registerExtension()` API
- `WEB_DIRECTORY = "./js"` in `__init__.py` serves these files

## Testing

No formal test suite exists. Nodes are tested manually within ComfyUI workflows. When modifying nodes:

1. Verify `INPUT_TYPES` and `RETURN_TYPES` are correct
2. Ensure the node loads without import errors (`__init__.py` try-except will catch these)
3. Test with ComfyUI by running a workflow that uses the node

## Common Tasks

### Adding a new node
1. Create a new `.py` file following the registration pattern above
2. Add the import block to `__init__.py`
3. Add any new dependencies to `requirements.txt`
4. Update `readme.md` with node documentation

### Modifying an existing node
- Changing `INPUT_TYPES` or `RETURN_TYPES` can break existing workflows — be cautious
- Adding optional inputs is safe; removing or renaming inputs is breaking

## Nodes Reference (10 total)

| File | Node(s) | Purpose |
|---|---|---|
| `BETA_cropnodes.py` | BETACrop, BETAStitch | Crop/stitch video frame regions |
| `BETA_scenedetect.py` | BETASceneDetect | Detect scene changes, split into segments |
| `audio_saver.py` | SaveAudioAdvanced | Save audio in FLAC/WAV/MP3 formats |
| `sharpness_clipper.py` | SharpestFrameClipper, SelectSharpestFrames | Analyze frame sharpness, select/clip frames |
| `wan_calculator.py` | WANResolutionCalculator | Calculate optimal WAN model dimensions |
| `load_text_node.py` | LoadTextFromIndex | Load text file from directory by index |
| `indexed_lora_loader.py` | IndexedLoRALoader | Load LoRA from configurable 20-slot stack |
| `text_line_count.py` | TextLineCount | Count lines in text input |
