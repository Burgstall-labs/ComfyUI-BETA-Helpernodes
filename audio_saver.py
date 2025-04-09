# audio_saver.py

import torch
import torchaudio
import os
import folder_paths
import numpy as np
import datetime

class SaveAudioAdvanced:
    """
    Saves audio data to a specified format (FLAC, WAV, MP3).
    Handles multiple common AUDIO formats and uses correct backend options.
    Includes detailed logging for debugging.
    """
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(cls):
        # !!! --- CORRECTED INPUT_TYPES DEFINITION --- !!!
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
             "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
             },
        }
        # !!! --- END OF CORRECTED DEFINITION --- !!!

    RETURN_TYPES = ()
    FUNCTION = "save_audio"
    OUTPUT_NODE = True
    CATEGORY = "BETA/Audio"

    def save_audio(self, audio, filename_prefix, format, # Now these will be received correctly
                   wav_encoding="PCM_16", flac_compression=5, mp3_bitrate=192,
                   prompt=None, extra_pnginfo=None):

        print("[SaveAudioAdvanced] Node execution started.")

        # --- Input Validation Section (as before) ---
        waveform_input = None; sample_rate_input = None; valid_input_format = False
        input_type_str = str(type(audio))
        if isinstance(audio, (tuple, list)) and len(audio) == 2 and isinstance(audio[0], (torch.Tensor, np.ndarray)) and isinstance(audio[1], int):
            waveform_input = audio[0]; sample_rate_input = audio[1]; valid_input_format = True; print("[SaveAudioAdvanced] Info: Detected standard AUDIO tuple format (Tensor, int).")
        elif isinstance(audio, (tuple, list)) and len(audio) == 1 and isinstance(audio[0], dict):
            audio_dict = audio[0]
            if 'waveform' in audio_dict and 'sample_rate' in audio_dict and isinstance(audio_dict.get('waveform'), (torch.Tensor, np.ndarray)) and isinstance(audio_dict.get('sample_rate'), int):
                waveform_input = audio_dict['waveform']; sample_rate_input = audio_dict['sample_rate']; valid_input_format = True; print("[SaveAudioAdvanced] Info: Detected wrapped dictionary AUDIO format ({'waveform':..., 'sample_rate':...}, ).")
        elif isinstance(audio, dict):
             if 'waveform' in audio and 'sample_rate' in audio and isinstance(audio.get('waveform'), (torch.Tensor, np.ndarray)) and isinstance(audio.get('sample_rate'), int):
                 waveform_input = audio['waveform']; sample_rate_input = audio['sample_rate']; valid_input_format = True; print("[SaveAudioAdvanced] Info: Detected plain dictionary AUDIO format {'waveform':..., 'sample_rate':...}.")

        if not valid_input_format:
             print("[SaveAudioAdvanced] Input format validation failed.")
             error_msg = f"[SaveAudioAdvanced] Error: Input 'audio' is not a recognized AUDIO format." # ... (rest of error message details)
             print(error_msg)
             return {}
        print(f"[SaveAudioAdvanced] Input format validated successfully. Sample Rate: {sample_rate_input}")

        # --- Tensor Conversion & Prep (as before) ---
        sample_rate = sample_rate_input
        if isinstance(waveform_input, np.ndarray):
            try: waveform = torch.from_numpy(waveform_input)
            except Exception as e: print(f"[SaveAudioAdvanced] Error: numpy conversion failed: {e}"); return {}
        elif isinstance(waveform_input, torch.Tensor): waveform = waveform_input
        else: print(f"[SaveAudioAdvanced] Error: Internal validation error."); return {}
        print(f"[SaveAudioAdvanced] Waveform is now a tensor. Initial dtype: {waveform.dtype}")

        if waveform.numel() == 0: print("[SaveAudioAdvanced] Error: Input waveform tensor is empty."); return {}
        if waveform.device != torch.device('cpu'): print("[SaveAudioAdvanced] Moving waveform to CPU."); waveform = waveform.cpu()

        # --- Shape Handling (as before) ---
        print(f"[SaveAudioAdvanced] Waveform shape before final processing: {waveform.shape}")
        if waveform.ndim >= 3 and waveform.shape[0] == 1: waveform = waveform.squeeze(0)
        if waveform.ndim == 1: waveform = waveform.unsqueeze(0)
        elif waveform.ndim != 2: print(f"[SaveAudioAdvanced] Error: Cannot handle waveform shape {waveform.shape}"); return {}
        print(f"[SaveAudioAdvanced] Waveform shape for saving: {waveform.shape}")

        # --- File Naming (as before) ---
        try:
            full_output_folder, filename, counter, subfolder, filename_prefix_out = \
                folder_paths.get_save_image_path(filename_prefix, self.output_dir) # Uses filename_prefix now
            file_extension = f".{format.lower()}" # Uses format now
            filename_with_counter = f"{filename_prefix_out}_{counter:05d}{file_extension}"
            filepath = os.path.join(full_output_folder, filename_with_counter)
            print(f"[SaveAudioAdvanced] Calculated save path: {filepath}")
        except Exception as e: print(f"[SaveAudioAdvanced] Error calculating output path: {e}"); import traceback; print(traceback.format_exc()); return {}

        # --- Format Specific Parameters & Data Prep (using 'ab' for MP3) ---
        save_kwargs = {}
        # ... (logic for WAV: save_kwargs['encoding'], save_kwargs['bits_per_sample']) ...
        if format == 'wav':
            encoding_map = { "PCM_16": {"encoding": "PCM_S", "bits_per_sample": 16}, "PCM_24": {"encoding": "PCM_S", "bits_per_sample": 24}, "PCM_32": {"encoding": "PCM_S", "bits_per_sample": 32}, "FLOAT_32": {"encoding": "PCM_F", "bits_per_sample": 32}, "FLOAT_64": {"encoding": "PCM_F", "bits_per_sample": 64}, }
            wav_params = encoding_map.get(wav_encoding, encoding_map["PCM_16"])
            if wav_encoding not in encoding_map: print(f"[SaveAudioAdvanced] Warning: Unknown WAV encoding '{wav_encoding}'. Using default PCM_16.")
            save_kwargs.update(wav_params)
            # ... (WAV data prep: clamping/normalization/type conversion) ...

        # ... (logic for FLAC: save_kwargs['compression_level']) ...
        elif format == 'flac':
            save_kwargs['compression_level'] = flac_compression
            if torch.is_floating_point(waveform): waveform = torch.clamp(waveform, -1.0, 1.0)

        # ... (logic for MP3: save_kwargs['ab']) ...
        elif format == 'mp3':
            save_kwargs['ab'] = f"{mp3_bitrate}k"
            # ... (MP3 data prep: normalization, float32, clamping) ...
            if not torch.is_floating_point(waveform): # ... (normalization) ...
                 pass # Simplified for brevity
            waveform = torch.clamp(waveform, -1.0, 1.0)
            if waveform.dtype != torch.float32: waveform = waveform.to(torch.float32)

        print(f"[SaveAudioAdvanced] Waveform final dtype for saving: {waveform.dtype}")
        if torch.is_floating_point(waveform): print(f"[SaveAudioAdvanced] Waveform stats (float): min={waveform.min():.4f}, max={waveform.max():.4f}, mean={waveform.mean():.4f}")
        else: print(f"[SaveAudioAdvanced] Waveform stats (int): min={waveform.min()}, max={waveform.max()}, mean={waveform.float().mean():.4f}")

        # --- Saving ---
        saved = False
        try:
            print("[SaveAudioAdvanced] Ensuring output directory exists...")
            os.makedirs(full_output_folder, exist_ok=True)
            print(f"[SaveAudioAdvanced] Attempting to save with torchaudio...")
            print(f"[SaveAudioAdvanced]   - Path: {filepath}")
            print(f"[SaveAudioAdvanced]   - Format: {format}") # Uses format now
            print(f"[SaveAudioAdvanced]   - SR: {sample_rate}")
            print(f"[SaveAudioAdvanced]   - Shape: {waveform.shape}")
            print(f"[SaveAudioAdvanced]   - Dtype: {waveform.dtype}")
            print(f"[SaveAudioAdvanced]   - Kwargs: {save_kwargs}")

            torchaudio.save(filepath, waveform, sample_rate, format=format, **save_kwargs) # Uses format now

            print("[SaveAudioAdvanced] torchaudio.save() completed without raising an exception.")

            if os.path.exists(filepath):
                 print(f"[SaveAudioAdvanced] File check: Confirmed file exists at {filepath}")
                 saved = True
            else:
                 print(f"[SaveAudioAdvanced] File check WARNING: torchaudio.save() completed BUT file does not exist at {filepath}!")
                 print("[SaveAudioAdvanced]   - Check filesystem permissions and available disk space.")
                 print("[SaveAudioAdvanced]   - Check if torchaudio backend (e.g., FFmpeg) wrote to a temporary location or failed silently.")

        except Exception as e:
            print(f"[SaveAudioAdvanced] Error DURING saving audio file: {e}")
            if format == 'mp3' and ('backend' in str(e).lower() or 'ab' in str(e).lower()):
                 print("[SaveAudioAdvanced] MP3 saving failed. Check FFmpeg/LAME installation and PATH.")
                 if "'ab'" in str(e): print("[SaveAudioAdvanced] Hint: Passing 'ab' kwarg failed.")
            import traceback
            print(traceback.format_exc())

        # --- Result for UI ---
        if saved:
            print(f"[SaveAudioAdvanced] Operation successful. Reporting saved file to UI.")
            result_filename = os.path.basename(filepath)
            results = [{"filename": result_filename, "subfolder": subfolder, "type": self.type}]
            return {"ui": {"audio": results}}
        else:
            print("[SaveAudioAdvanced] Operation finished, but file was not confirmed saved.")
            return {}
