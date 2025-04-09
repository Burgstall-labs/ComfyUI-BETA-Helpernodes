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
        # --- INPUT_TYPES definition (ensure it's complete) ---
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

        # --- Input Validation Section (as before) ---
        # ... (Ensure full validation logic is here) ...
        waveform_input = None; sample_rate_input = None; valid_input_format = False
        # ... (Logic for tuple, wrapped dict, plain dict) ...
        if not valid_input_format:
             # ... (error logging) ...
             return {}
        print(f"[SaveAudioAdvanced] Input format validated successfully. Sample Rate: {sample_rate_input}")

        # --- Tensor Conversion & Prep (as before) ---
        sample_rate = sample_rate_input
        # ... (numpy conversion, CPU move, empty check) ...
        if isinstance(waveform_input, np.ndarray): # ... (numpy conversion) ...
            try: waveform = torch.from_numpy(waveform_input)
            except Exception as e: print(f"[SaveAudioAdvanced] Error: numpy conversion failed: {e}"); return {}
        elif isinstance(waveform_input, torch.Tensor): waveform = waveform_input
        else: print(f"[SaveAudioAdvanced] Error: Internal validation error."); return {}
        if waveform.numel() == 0: print("[SaveAudioAdvanced] Error: Input waveform tensor is empty."); return {}
        if waveform.device != torch.device('cpu'): waveform = waveform.cpu()


        # --- Shape Handling (as before) ---
        # ... (ndim check, squeeze, unsqueeze) ...
        if waveform.ndim >= 3 and waveform.shape[0] == 1: waveform = waveform.squeeze(0)
        if waveform.ndim == 1: waveform = waveform.unsqueeze(0)
        elif waveform.ndim != 2: print(f"[SaveAudioAdvanced] Error: Cannot handle waveform shape {waveform.shape}"); return {}


        # --- File Naming (as before) ---
        try: # ... (path calculation) ...
            full_output_folder, filename, counter, subfolder, filename_prefix_out = \
                folder_paths.get_save_image_path(filename_prefix, self.output_dir)
            file_extension = f".{format.lower()}"
            filename_with_counter = f"{filename_prefix_out}_{counter:05d}{file_extension}"
            filepath = os.path.join(full_output_folder, filename_with_counter)
            print(f"[SaveAudioAdvanced] Calculated save path: {filepath}")
        except Exception as e: # ... (error handling) ...
             return {}


        # --- Format Specific Parameters & Data Prep ---
        save_kwargs = {} # Reset kwargs for each run

        # --- WAV ---
        if format == 'wav':
            encoding_map = { "PCM_16": {"encoding": "PCM_S", "bits_per_sample": 16}, # ... (rest of map) ...
                           } # ... (rest of WAV logic: get params, update save_kwargs, prep data) ...
            wav_params = encoding_map.get(wav_encoding, encoding_map["PCM_16"]) #...
            save_kwargs.update(wav_params) #...
            # ... (WAV data prep: clamping/normalization/type conversion) ...


        # --- FLAC ---
        elif format == 'flac':
            save_kwargs['compression_level'] = flac_compression
            # ... (FLAC data prep: clamping) ...
            if torch.is_floating_point(waveform): waveform = torch.clamp(waveform, -1.0, 1.0)


        # --- MP3 ---
        elif format == 'mp3':
            # !!! Correction 3: Try passing NO specific kwargs for MP3 !!!
            # Let torchaudio use the backend's default settings.
            print("[SaveAudioAdvanced] Info: Passing no specific kwargs for MP3 format, using backend defaults.")
            # save_kwargs['ab'] = f"{mp3_bitrate}k" # <<< REMOVE/COMMENT THIS LINE
            # save_kwargs['compression'] = ... # <<< Ensure no other MP3-specific kwargs are added here

            # Data prep still needed: Ensure float [-1, 1], float32
            if not torch.is_floating_point(waveform):
                 print("[SaveAudioAdvanced] Warning: Input waveform is not float for MP3 save. Normalizing.")
                 # ... (normalization logic) ...
                 try: # Simplified normalization
                     dtype_info = torch.iinfo(waveform.dtype); max_val = dtype_info.max; min_val = dtype_info.min
                     if min_val < 0: waveform = waveform.float() / max(abs(max_val), abs(min_val))
                     else: waveform = (waveform.float() / max_val) * 2.0 - 1.0
                 except TypeError: waveform = waveform.float() # Fallback
            waveform = torch.clamp(waveform, -1.0, 1.0)
            if waveform.dtype != torch.float32:
                 waveform = waveform.to(torch.float32)


        print(f"[SaveAudioAdvanced] Waveform final dtype for saving: {waveform.dtype}")
        # ... (Waveform stats logging) ...


        # --- Saving ---
        saved = False
        try:
            print("[SaveAudioAdvanced] Ensuring output directory exists...")
            os.makedirs(full_output_folder, exist_ok=True)
            print(f"[SaveAudioAdvanced] Attempting to save with torchaudio...")
            # ... (Log path, format, SR, Shape, Dtype) ...
            print(f"[SaveAudioAdvanced]   - Path: {filepath}")
            print(f"[SaveAudioAdvanced]   - Format: {format}")
            print(f"[SaveAudioAdvanced]   - SR: {sample_rate}")
            print(f"[SaveAudioAdvanced]   - Shape: {waveform.shape}")
            print(f"[SaveAudioAdvanced]   - Dtype: {waveform.dtype}")
            print(f"[SaveAudioAdvanced]   - Kwargs: {save_kwargs}") # Should be empty for MP3 now

            # Call torchaudio.save, passing the potentially empty save_kwargs
            torchaudio.save(filepath, waveform, sample_rate, format=format, **save_kwargs)

            print("[SaveAudioAdvanced] torchaudio.save() completed without raising an exception.") # Added

            # ... (os.path.exists check and associated logging) ...
            if os.path.exists(filepath):
                 print(f"[SaveAudioAdvanced] File check: Confirmed file exists at {filepath}") # Added
                 saved = True
            else:
                 print(f"[SaveAudioAdvanced] File check WARNING: torchaudio.save() completed BUT file does not exist at {filepath}!") # Added
                 # ... (Hints about permissions, disk space, silent backend failure) ...


        except Exception as e:
            print(f"[SaveAudioAdvanced] Error DURING saving audio file: {e}")
            # ... (Exception handling, traceback) ...
            import traceback
            print(traceback.format_exc())

        # --- Result for UI ---
        if saved:
             # ... (Success logging and return) ...
             print(f"[SaveAudioAdvanced] Operation successful. Reporting saved file to UI.")
             result_filename = os.path.basename(filepath)
             results = [{"filename": result_filename, "subfolder": subfolder, "type": self.type}]
             return {"ui": {"audio": results}}
        else:
            print("[SaveAudioAdvanced] Operation finished, but file was not confirmed saved.")
            return {}
