# audio_saver.py

import torch
import torchaudio
# import torchaudio.io # No longer strictly needed for this approach
import os
import folder_paths
import numpy as np
import datetime

class SaveAudioAdvanced:
    # ... (class definition, __init__, INPUT_TYPES remain the same) ...
    @classmethod
    def INPUT_TYPES(cls):
        # --- INPUT_TYPES remains unchanged ---
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

    RETURN_TYPES = ()
    FUNCTION = "save_audio"
    OUTPUT_NODE = True
    CATEGORY = "BETA/Audio"


    def save_audio(self, audio, filename_prefix, format,
                   wav_encoding="PCM_16", flac_compression=5, mp3_bitrate=192,
                   prompt=None, extra_pnginfo=None):

        # --- Input Validation Section (remains the same) ---
        waveform_input = None; sample_rate_input = None; valid_input_format = False # ... (rest of validation logic) ...
        # --- End Input Validation --- # (Make sure the full validation block is present here)
        if not valid_input_format: # Add this check if it was missing
             # ... (error logging for invalid format) ...
             return {}

        sample_rate = sample_rate_input
        if isinstance(waveform_input, np.ndarray): # ... (numpy conversion) ...
             pass
        elif isinstance(waveform_input, torch.Tensor): waveform = waveform_input
        else: # ... (error handling) ...
             return {}

        if waveform.device != torch.device('cpu'): waveform = waveform.cpu()
        if waveform.ndim >= 3 and waveform.shape[0] == 1: waveform = waveform.squeeze(0)
        if waveform.ndim == 1: waveform = waveform.unsqueeze(0)
        elif waveform.ndim != 2: # ... (error handling) ...
             return {}

        # --- File Naming (remains the same) ---
        full_output_folder, filename, counter, subfolder, filename_prefix_out = \
            folder_paths.get_save_image_path(filename_prefix, self.output_dir)
        file_extension = f".{format.lower()}"
        filename_with_counter = f"{filename_prefix_out}_{counter:05d}{file_extension}"
        filepath = os.path.join(full_output_folder, filename_with_counter)

        # --- Format Specific Parameters & Data Prep ---
        save_kwargs = {} # Store format-specific kwargs here

        # --- WAV ---
        if format == 'wav':
            encoding_map = { "PCM_16": {"encoding": "PCM_S", "bits_per_sample": 16}, # ... (rest of map) ...
                             }
            wav_params = encoding_map.get(wav_encoding, encoding_map["PCM_16"])
            if wav_encoding not in encoding_map: print(f"[SaveAudioAdvanced] Warning: Unknown WAV encoding '{wav_encoding}'. Using default PCM_16.")
            save_kwargs.update(wav_params) # Add 'encoding' and 'bits_per_sample' to kwargs
            # ... (WAV data prep: clamping/normalization/type conversion) ...
            target_encoding = wav_params['encoding']; bits_per_sample = wav_params['bits_per_sample']
            target_dtype = getattr(torch, f"int{bits_per_sample}", torch.int16) if target_encoding == "PCM_S" else getattr(torch, f"float{bits_per_sample}", torch.float32)
            if target_encoding == "PCM_S" and torch.is_floating_point(waveform): waveform = torch.clamp(waveform, -1.0, 1.0)
            elif target_encoding == "PCM_F":
                if not torch.is_floating_point(waveform): # ... (normalization logic) ...
                    pass
                waveform = torch.clamp(waveform, -1.0, 1.0)
                if waveform.dtype != target_dtype: waveform = waveform.to(target_dtype)


        # --- FLAC ---
        elif format == 'flac':
            # Torchaudio uses 'compression_level' for FLAC
            save_kwargs['compression_level'] = flac_compression # Add 'compression_level' to kwargs
            if torch.is_floating_point(waveform): waveform = torch.clamp(waveform, -1.0, 1.0)


        # --- MP3 ---
        elif format == 'mp3':
            # !!! Correction 2: Try passing bitrate via a direct kwarg 'ab'
            # This corresponds to the common FFmpeg command-line arg '-ab'
            # Format bitrate like "192k"
            save_kwargs['ab'] = f"{mp3_bitrate}k" # Add 'ab' to kwargs

            # Data prep: Ensure float [-1, 1], float32
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


        # --- Saving ---
        saved = False
        try:
            os.makedirs(full_output_folder, exist_ok=True)
            print(f"[SaveAudioAdvanced] Attempting to save to: {filepath} | Format: {format} | SR: {sample_rate} | Shape: {waveform.shape} | Dtype: {waveform.dtype}")
            # Log the specific arguments being passed
            print(f"[SaveAudioAdvanced] Using save kwargs: {save_kwargs}")

            # Call torchaudio.save, passing the collected kwargs.
            # Do NOT specify backend="ffmpeg" explicitly here, let torchaudio choose.
            # Do NOT pass encoder_options.
            torchaudio.save(filepath, waveform, sample_rate, format=format, **save_kwargs)

            saved = True
        except Exception as e:
            print(f"[SaveAudioAdvanced] Error saving audio file: {e}")
            # Keep the specific MP3 backend error hint
            if format == 'mp3' and ('backend' in str(e).lower() or 'encoder' in str(e).lower() or 'lame' in str(e).lower() or 'ffmpeg' in str(e).lower() or 'ab' in str(e).lower()):
                 print("[SaveAudioAdvanced] MP3 saving failed. Check FFmpeg/LAME installation and PATH.")
                 # If the error specifically mentions 'ab', this approach might be wrong for this version too.
                 if "'ab'" in str(e):
                      print("[SaveAudioAdvanced] Hint: Passing 'ab' kwarg failed. Torchaudio version might expect a different parameter for MP3 bitrate.")
            import traceback
            print(traceback.format_exc())

        # --- Result for UI (remains the same) ---
        if saved:
            # ... (success logging and return) ...
             print(f"[SaveAudioAdvanced] Saved audio to: {filepath}")
             result_filename = os.path.basename(filepath)
             results = [{"filename": result_filename, "subfolder": subfolder, "type": self.type}]
             return {"ui": {"audio": results}}

        else:
            return {} # Indicate failure / no file saved
