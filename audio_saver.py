# audio_saver.py

import torch
import torchaudio
import os
import folder_paths
import numpy as np
import datetime

class SaveAudioAdvanced:
    # ... (class definition, __init__, INPUT_TYPES remain the same) ...
    @classmethod
    def INPUT_TYPES(cls):
       # ... (Make sure the full INPUT_TYPES dictionary is here) ...
        return {
            "required": {
                "audio": ("AUDIO", ),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "format": (["flac", "wav", "mp3"], {"default": "flac"}),
            },
            "optional": {
                "wav_encoding": (["PCM_16", "PCM_24", "PCM_32", "FLOAT_32", "FLOAT_64"], {"default": "PCM_16"}),
                "flac_compression": ("INT", {"default": 5, "min": 0, "max": 8, "step": 1}), # Level 0-8
                "mp3_bitrate": ("INT", {"default": 192, "min": 8, "max": 320, "step": 8}), # Bitrate in kbps
            },
             "hidden": { "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO" },
        }


    RETURN_TYPES = ()
    FUNCTION = "save_audio"
    OUTPUT_NODE = True
    CATEGORY = "BETA/Audio"

    def save_audio(self, audio, filename_prefix, format,
                   wav_encoding="PCM_16", flac_compression=5, mp3_bitrate=192,
                   prompt=None, extra_pnginfo=None):

        print("[SaveAudioAdvanced] Node execution started.")

        # --- ADDED DEBUG PRINT ---
        print(f"[SaveAudioAdvanced] DEBUG: Received 'audio' type: {type(audio)}")
        if isinstance(audio, (list, tuple)):
             print(f"[SaveAudioAdvanced] DEBUG: Is list/tuple. Length: {len(audio)}")
             if len(audio) > 0: print(f"[SaveAudioAdvanced] DEBUG: First element type: {type(audio[0])}")
        elif isinstance(audio, dict):
             print(f"[SaveAudioAdvanced] DEBUG: Is dict. Keys: {list(audio.keys())}")
             print(f"[SaveAudioAdvanced] DEBUG: Dict value types: waveform={type(audio.get('waveform'))}, sample_rate={type(audio.get('sample_rate'))}")
        try:
             # Try to print shape if it looks like the dict format
             if isinstance(audio, dict) and isinstance(audio.get('waveform'), (torch.Tensor, np.ndarray)):
                  print(f"[SaveAudioAdvanced] DEBUG: Waveform shape (if tensor/ndarray): {audio['waveform'].shape}")
             elif isinstance(audio, (list,tuple)) and len(audio) > 0 and isinstance(audio[0], dict) and isinstance(audio[0].get('waveform'), (torch.Tensor, np.ndarray)):
                  print(f"[SaveAudioAdvanced] DEBUG: Waveform shape (if tensor/ndarray in wrapped dict): {audio[0]['waveform'].shape}")
             elif isinstance(audio, (list,tuple)) and len(audio) > 0 and isinstance(audio[0], (torch.Tensor, np.ndarray)):
                 print(f"[SaveAudioAdvanced] DEBUG: Waveform shape (if tensor/ndarray in tuple): {audio[0].shape}")
             else:
                  print(f"[SaveAudioAdvanced] DEBUG: Received 'audio' content (partial str): {str(audio)[:500]}")
        except Exception as e:
             print(f"[SaveAudioAdvanced] DEBUG: Could not print detailed audio content/shape: {e}")
        # --- END ADDED DEBUG PRINT ---


        # --- Input Validation Section (as before) ---
        waveform_input = None; sample_rate_input = None; valid_input_format = False
        input_type_str = str(type(audio)) # Keep this for error logging later

        # Style 1: Standard tuple (Tensor, int)
        if isinstance(audio, (tuple, list)) and len(audio) == 2 and isinstance(audio[0], (torch.Tensor, np.ndarray)) and isinstance(audio[1], int):
            waveform_input = audio[0]; sample_rate_input = audio[1]; valid_input_format = True; print("[SaveAudioAdvanced] Info: Detected standard AUDIO tuple format (Tensor, int).")

        # Style 2: Wrapped dictionary tuple ( {'waveform':..., 'sample_rate':...}, )
        elif isinstance(audio, (tuple, list)) and len(audio) == 1 and isinstance(audio[0], dict):
            audio_dict = audio[0]
            if 'waveform' in audio_dict and 'sample_rate' in audio_dict and isinstance(audio_dict.get('waveform'), (torch.Tensor, np.ndarray)) and isinstance(audio_dict.get('sample_rate'), int):
                waveform_input = audio_dict['waveform']; sample_rate_input = audio_dict['sample_rate']; valid_input_format = True; print("[SaveAudioAdvanced] Info: Detected wrapped dictionary AUDIO format ({'waveform':..., 'sample_rate':...}, ).")

        # Style 3: Plain dictionary { 'waveform':..., 'sample_rate':... }
        elif isinstance(audio, dict):
            if 'waveform' in audio and 'sample_rate' in audio and isinstance(audio.get('waveform'), (torch.Tensor, np.ndarray)) and isinstance(audio.get('sample_rate'), int):
                waveform_input = audio['waveform']; sample_rate_input = audio['sample_rate']; valid_input_format = True; print("[SaveAudioAdvanced] Info: Detected plain dictionary AUDIO format {'waveform':..., 'sample_rate':...}.")

        # Handle invalid formats
        if not valid_input_format:
             print("[SaveAudioAdvanced] Input format validation failed.") # This log now comes AFTER the debug prints
             error_msg = f"[SaveAudioAdvanced] Error: Input 'audio' is not a recognized AUDIO format." # ... (rest of the detailed error message using input_type_str etc.)
             # Add the debug info to the error message
             error_msg += f"\n   DEBUG INFO: Type={type(audio)}"
             if isinstance(audio, (list, tuple)): error_msg += f", Len={len(audio)}"
             if isinstance(audio, dict): error_msg += f", Keys={list(audio.keys())}"
             # ... add more detail from debug prints if helpful ...
             print(error_msg)
             return {} # Exit point

        # --- IF VALIDATION PASSES, THIS LOG SHOULD APPEAR ---
        print(f"[SaveAudioAdvanced] Input format validated successfully. Sample Rate: {sample_rate_input}")

        # ... (Rest of the function as in the previous step - Tensor conversion, shape handling, path calculation, saving logic, etc.) ...
        # Make sure all the print statements from the previous step are still present below this point.
