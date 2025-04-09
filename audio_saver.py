# audio_saver.py

import torch
import torchaudio
import torchaudio.io # Import for CodecConfig if needed later, though not for bitrate here
import os
import folder_paths
import numpy as np
import datetime

class SaveAudioAdvanced:
    """
    Saves audio data to a specified format (FLAC, WAV, MP3).
    Handles multiple common AUDIO formats and uses correct backend options.
    """
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

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

        # --- Input Validation Section (remains the same as previous version) ---
        waveform_input = None
        sample_rate_input = None
        valid_input_format = False
        input_type_str = str(type(audio))

        if isinstance(audio, (tuple, list)) and len(audio) == 2 and \
           isinstance(audio[0], (torch.Tensor, np.ndarray)) and \
           isinstance(audio[1], int):
            waveform_input = audio[0]; sample_rate_input = audio[1]; valid_input_format = True
            print("[SaveAudioAdvanced] Info: Detected standard AUDIO tuple format (Tensor, int).")
        elif isinstance(audio, (tuple, list)) and len(audio) == 1 and isinstance(audio[0], dict):
            audio_dict = audio[0]
            if 'waveform' in audio_dict and 'sample_rate' in audio_dict and \
               isinstance(audio_dict.get('waveform'), (torch.Tensor, np.ndarray)) and \
               isinstance(audio_dict.get('sample_rate'), int):
                waveform_input = audio_dict['waveform']; sample_rate_input = audio_dict['sample_rate']; valid_input_format = True
                print("[SaveAudioAdvanced] Info: Detected wrapped dictionary AUDIO format ({'waveform':..., 'sample_rate':...}, ).")
        elif isinstance(audio, dict):
            if 'waveform' in audio and 'sample_rate' in audio and \
               isinstance(audio.get('waveform'), (torch.Tensor, np.ndarray)) and \
               isinstance(audio.get('sample_rate'), int):
                waveform_input = audio['waveform']; sample_rate_input = audio['sample_rate']; valid_input_format = True
                print("[SaveAudioAdvanced] Info: Detected plain dictionary AUDIO format {'waveform':..., 'sample_rate':...}.")

        if not valid_input_format:
            error_msg = f"[SaveAudioAdvanced] Error: Input 'audio' is not a recognized AUDIO format." # ... (rest of error message) ...
            print(error_msg) # (Keep the detailed error logging)
            return {}
        # --- End Input Validation ---

        sample_rate = sample_rate_input
        if isinstance(waveform_input, np.ndarray):
             try: waveform = torch.from_numpy(waveform_input)
             except Exception as e: print(f"[SaveAudioAdvanced] Error: numpy conversion failed: {e}"); return {}
        elif isinstance(waveform_input, torch.Tensor): waveform = waveform_input
        else: print(f"[SaveAudioAdvanced] Error: Internal validation error."); return {}

        if waveform.device != torch.device('cpu'): waveform = waveform.cpu()
        if waveform.ndim >= 3 and waveform.shape[0] == 1: waveform = waveform.squeeze(0)
        if waveform.ndim == 1: waveform = waveform.unsqueeze(0)
        elif waveform.ndim != 2:
             print(f"[SaveAudioAdvanced] Error: Cannot handle waveform shape {waveform.shape}"); return {}

        # --- File Naming (remains the same) ---
        full_output_folder, filename, counter, subfolder, filename_prefix_out = \
            folder_paths.get_save_image_path(filename_prefix, self.output_dir)
        file_extension = f".{format.lower()}"
        filename_with_counter = f"{filename_prefix_out}_{counter:05d}{file_extension}"
        filepath = os.path.join(full_output_folder, filename_with_counter)

        # --- Format Specific Parameters & Data Prep ---
        save_kwargs = {}
        encoder_options = None # Specific for MP3/FFmpeg

        # --- WAV ---
        if format == 'wav':
            encoding_map = { "PCM_16": {"encoding": "PCM_S", "bits_per_sample": 16}, "PCM_24": {"encoding": "PCM_S", "bits_per_sample": 24}, "PCM_32": {"encoding": "PCM_S", "bits_per_sample": 32}, "FLOAT_32": {"encoding": "PCM_F", "bits_per_sample": 32}, "FLOAT_64": {"encoding": "PCM_F", "bits_per_sample": 64}, }
            wav_params = encoding_map.get(wav_encoding, encoding_map["PCM_16"])
            if wav_encoding not in encoding_map: print(f"[SaveAudioAdvanced] Warning: Unknown WAV encoding '{wav_encoding}'. Using default PCM_16.")
            save_kwargs.update(wav_params)
            # ... (WAV data prep remains the same - clamping/normalization) ...
            target_encoding = wav_params['encoding']; bits_per_sample = wav_params['bits_per_sample']
            target_dtype = getattr(torch, f"int{bits_per_sample}", torch.int16) if target_encoding == "PCM_S" else getattr(torch, f"float{bits_per_sample}", torch.float32)
            if target_encoding == "PCM_S" and torch.is_floating_point(waveform): waveform = torch.clamp(waveform, -1.0, 1.0)
            elif target_encoding == "PCM_F":
                if not torch.is_floating_point(waveform):
                    # ... (normalization logic) ...
                    try:
                        dtype_info = torch.iinfo(waveform.dtype); max_val = dtype_info.max; min_val = dtype_info.min
                        if min_val < 0: waveform = waveform.float() / max(abs(max_val), abs(min_val))
                        else: waveform = (waveform.float() / max_val) * 2.0 - 1.0
                    except TypeError: waveform = waveform.float() # Fallback
                waveform = torch.clamp(waveform, -1.0, 1.0)
                if waveform.dtype != target_dtype: waveform = waveform.to(target_dtype)


        # --- FLAC ---
        elif format == 'flac':
            # Torchaudio uses 'compression_level' for FLAC
            save_kwargs['compression_level'] = flac_compression
            if torch.is_floating_point(waveform): waveform = torch.clamp(waveform, -1.0, 1.0)


        # --- MP3 ---
        elif format == 'mp3':
            # !!! Correction: Use encoder_options for FFmpeg backend bitrate !!!
            # Format bitrate as string "XXXk" which FFmpeg understands
            encoder_options = {'audio_bitrate': f"{mp3_bitrate}k"}
            # Remove the incorrect 'compression' kwarg for mp3
            # save_kwargs['compression'] = mp3_bitrate # <<< REMOVE THIS LINE / DON'T ADD IT

            # Data prep: Ensure float [-1, 1]
            if not torch.is_floating_point(waveform):
                 print("[SaveAudioAdvanced] Warning: Input waveform is not float for MP3 save. Normalizing.")
                 # ... (normalization logic) ...
                 try:
                     dtype_info = torch.iinfo(waveform.dtype); max_val = dtype_info.max; min_val = dtype_info.min
                     if min_val < 0: waveform = waveform.float() / max(abs(max_val), abs(min_val))
                     else: waveform = (waveform.float() / max_val) * 2.0 - 1.0
                 except TypeError: waveform = waveform.float() # Fallback
            waveform = torch.clamp(waveform, -1.0, 1.0)
            # Ensure float32, common for MP3 encoding input
            if waveform.dtype != torch.float32:
                 waveform = waveform.to(torch.float32)


        # --- Saving ---
        saved = False
        try:
            os.makedirs(full_output_folder, exist_ok=True)
            print(f"[SaveAudioAdvanced] Attempting to save to: {filepath} | Format: {format} | SR: {sample_rate} | Shape: {waveform.shape} | Dtype: {waveform.dtype}")
            
            # Call torchaudio.save, passing encoder_options if defined
            if encoder_options:
                 print(f"[SaveAudioAdvanced] Using encoder options: {encoder_options}")
                 torchaudio.save(filepath, waveform, sample_rate, format=format, backend="ffmpeg", encoder_options=encoder_options, **save_kwargs)
            else:
                 # For WAV/FLAC, don't specify backend unless needed, let torchaudio choose.
                 # Pass only the relevant kwargs (e.g., compression_level for FLAC, encoding/bits for WAV)
                 torchaudio.save(filepath, waveform, sample_rate, format=format, **save_kwargs)

            saved = True
        except Exception as e:
            print(f"[SaveAudioAdvanced] Error saving audio file: {e}")
            # Keep the specific MP3 backend error hint
            if format == 'mp3' and ('backend' in str(e).lower() or 'encoder' in str(e).lower() or 'lame' in str(e).lower() or 'ffmpeg' in str(e).lower()):
                 print("[SaveAudioAdvanced] MP3 saving failed. Ensure FFmpeg (with libmp3lame) is installed and in your system PATH.")
            import traceback
            print(traceback.format_exc())

        # --- Result for UI (remains the same) ---
        if saved:
            print(f"[SaveAudioAdvanced] Saved audio to: {filepath}")
            result_filename = os.path.basename(filepath)
            results = [{"filename": result_filename, "subfolder": subfolder, "type": self.type}]
            return {"ui": {"audio": results}}
        else:
            return {}
