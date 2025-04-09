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
    Handles multiple common AUDIO formats:
    1. Standard ComfyUI AUDIO tuple: (Tensor, int)
    2. Wrapped dictionary tuple: ({'waveform': Tensor, 'sample_rate': int},)
    3. Plain dictionary: {'waveform': Tensor, 'sample_rate': int}
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
                "flac_compression": ("INT", {"default": 5, "min": 0, "max": 8, "step": 1}),
                "mp3_bitrate": ("INT", {"default": 192, "min": 8, "max": 320, "step": 8}),
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

        waveform_input = None
        sample_rate_input = None
        valid_input_format = False

        # --- INPUT VALIDATION ---
        input_type_str = str(type(audio)) # For logging

        # Style 1: Standard tuple (Tensor, int)
        if isinstance(audio, (tuple, list)) and len(audio) == 2 and \
           isinstance(audio[0], (torch.Tensor, np.ndarray)) and \
           isinstance(audio[1], int):
            waveform_input = audio[0]
            sample_rate_input = audio[1]
            valid_input_format = True
            print("[SaveAudioAdvanced] Info: Detected standard AUDIO tuple format (Tensor, int).")

        # Style 2: Wrapped dictionary tuple ( {'waveform':..., 'sample_rate':...}, )
        elif isinstance(audio, (tuple, list)) and len(audio) == 1 and \
             isinstance(audio[0], dict):
            audio_dict = audio[0]
            if 'waveform' in audio_dict and 'sample_rate' in audio_dict and \
               isinstance(audio_dict.get('waveform'), (torch.Tensor, np.ndarray)) and \
               isinstance(audio_dict.get('sample_rate'), int):
                waveform_input = audio_dict['waveform']
                sample_rate_input = audio_dict['sample_rate']
                valid_input_format = True
                print("[SaveAudioAdvanced] Info: Detected wrapped dictionary AUDIO format ({'waveform':..., 'sample_rate':...}, ).")
            # else: dictionary structure is wrong (handled by final error message)

        # Style 3: Plain dictionary { 'waveform':..., 'sample_rate':... }
        elif isinstance(audio, dict):
            if 'waveform' in audio and 'sample_rate' in audio and \
               isinstance(audio.get('waveform'), (torch.Tensor, np.ndarray)) and \
               isinstance(audio.get('sample_rate'), int):
                waveform_input = audio['waveform']
                sample_rate_input = audio['sample_rate']
                valid_input_format = True
                print("[SaveAudioAdvanced] Info: Detected plain dictionary AUDIO format {'waveform':..., 'sample_rate':...}.")
            # else: dictionary structure is wrong (handled by final error message)

        # Handle invalid formats / structure errors within dicts
        if not valid_input_format:
            error_msg = f"[SaveAudioAdvanced] Error: Input 'audio' is not a recognized AUDIO format."
            error_msg += f"\n   Expected one of: (Tensor, int) OR ({{'waveform': T/np, 'sample_rate': int}},) OR {{'waveform': T/np, 'sample_rate': int}}"
            error_msg += f"\n   Received type: {input_type_str}"
            # Add more detail based on type
            if isinstance(audio, (tuple, list)):
                error_msg += f"\n   - Tuple/List length: {len(audio)}"
                if len(audio) > 0: error_msg += f"\n   - First element type: {type(audio[0])}"
            elif isinstance(audio, dict):
                error_msg += f"\n   - Dictionary keys: {list(audio.keys())}"
                error_msg += f"\n   - Value types: waveform={type(audio.get('waveform'))}, sample_rate={type(audio.get('sample_rate'))}"
            print(error_msg)
            return {}

        # --- Assign validated inputs ---
        sample_rate = sample_rate_input # Already validated as int

        # Convert numpy to tensor if necessary
        if isinstance(waveform_input, np.ndarray):
             print(f"[SaveAudioAdvanced] Info: Input waveform was numpy.ndarray, converting to tensor.")
             try:
                 waveform = torch.from_numpy(waveform_input)
             except Exception as e:
                 print(f"[SaveAudioAdvanced] Error: Could not convert numpy waveform to tensor: {e}")
                 return {}
        elif isinstance(waveform_input, torch.Tensor):
            waveform = waveform_input # It's already a tensor
        else:
             # Should not happen if validation passed, but safeguard.
             print(f"[SaveAudioAdvanced] Error: Internal validation error - waveform type mismatch. Got {type(waveform_input)}")
             return {}

        # --- REST OF THE SAVING LOGIC (remains the same) ---

        # Ensure waveform is on CPU
        if waveform.device != torch.device('cpu'):
            waveform = waveform.cpu()

        # Squeeze potential extra batch dimension often added by TTS nodes
        if waveform.ndim >= 3 and waveform.shape[0] == 1:
             print(f"[SaveAudioAdvanced] Info: Input waveform has shape {waveform.shape}. Squeezing batch dimension.")
             waveform = waveform.squeeze(0) # Shape becomes [C, T] or [T] or [C, T, ...] if >3D initially

        # Ensure correct shape (Channels, Time) - Target is [C, T]
        if waveform.ndim == 1:
            print(f"[SaveAudioAdvanced] Info: Input waveform is 1D (mono). Adding channel dimension.")
            waveform = waveform.unsqueeze(0) # Shape becomes [1, T]
        elif waveform.ndim == 2:
             # Shape is already [C, T], good.
             pass
        else: # If still > 2D after potential batch squeeze
             print(f"[SaveAudioAdvanced] Warning: Waveform still has >2 dimensions ({waveform.shape}) after squeeze. Attempting to select first channel pair/slice.")
             # Example: take first 2 channels if shape is like [C>2, T] -> waveform = waveform[:2, :]
             # Example: take first element if shape is like [N, C, T] -> waveform = waveform[0] (should have been caught by batch squeeze?)
             # Let's just try a general squeeze again as a simple fallback, might fail gracefully later if shape is unusable.
             original_shape = waveform.shape
             waveform = waveform.squeeze()
             if waveform.ndim == 1: waveform = waveform.unsqueeze(0) # Add channel dim if squeeze made it mono
             if waveform.ndim != 2:
                 print(f"[SaveAudioAdvanced] Error: Could not reduce waveform from {original_shape} to 2 dimensions ([C, T]). Final shape: {waveform.shape}")
                 return {}
             else:
                 print(f"[SaveAudioAdvanced] Info: Reduced waveform shape from {original_shape} to {waveform.shape}.")


        # --- File Naming ---
        full_output_folder, filename, counter, subfolder, filename_prefix_out = \
            folder_paths.get_save_image_path(filename_prefix, self.output_dir)

        file_extension = f".{format.lower()}"
        filename_with_counter = f"{filename_prefix_out}_{counter:05d}{file_extension}"
        filepath = os.path.join(full_output_folder, filename_with_counter)

        # --- Format Specific Parameters ---
        save_kwargs = {}
        # ... (wav_encoding, flac_compression, mp3_bitrate logic remains the same) ...
        # --- WAV ---
        if format == 'wav':
            encoding_map = { "PCM_16": {"encoding": "PCM_S", "bits_per_sample": 16}, "PCM_24": {"encoding": "PCM_S", "bits_per_sample": 24}, "PCM_32": {"encoding": "PCM_S", "bits_per_sample": 32}, "FLOAT_32": {"encoding": "PCM_F", "bits_per_sample": 32}, "FLOAT_64": {"encoding": "PCM_F", "bits_per_sample": 64}, }
            wav_params = encoding_map.get(wav_encoding, encoding_map["PCM_16"])
            if wav_encoding not in encoding_map: print(f"[SaveAudioAdvanced] Warning: Unknown WAV encoding '{wav_encoding}'. Using default PCM_16.")
            save_kwargs.update(wav_params)
            target_encoding = wav_params['encoding']
            bits_per_sample = wav_params['bits_per_sample']
            target_dtype = None
            if target_encoding == "PCM_S": target_dtype = getattr(torch, f"int{bits_per_sample}", torch.int16)
            elif target_encoding == "PCM_F": target_dtype = getattr(torch, f"float{bits_per_sample}", torch.float32)

            # Data range/type adjustments
            if target_encoding == "PCM_S":
                if torch.is_floating_point(waveform): waveform = torch.clamp(waveform, -1.0, 1.0) # Torchaudio scales float->int
            elif target_encoding == "PCM_F":
                if not torch.is_floating_point(waveform):
                    print("[SaveAudioAdvanced] Warning: Input waveform is not float for WAV FLOAT save. Normalizing.")
                    # Simplified normalization (more robust needed for edge cases)
                    try:
                        dtype_info = torch.iinfo(waveform.dtype)
                        max_val = dtype_info.max
                        min_val = dtype_info.min
                        if min_val < 0: # Signed int -> normalize to [-1, 1]
                            waveform = waveform.float() / max(abs(max_val), abs(min_val))
                        else: # Unsigned int -> normalize to [-1, 1] assuming range starts at 0
                            waveform = (waveform.float() / max_val) * 2.0 - 1.0
                    except TypeError: # Handle if dtype isn't int (e.g., already float but wrong type)
                         print(f"[SaveAudioAdvanced] Warning: Could not get integer info for dtype {waveform.dtype}, attempting simple cast to float.")
                         waveform = waveform.float() # Attempt direct cast, might not be normalized
                waveform = torch.clamp(waveform, -1.0, 1.0)
                if waveform.dtype != target_dtype: waveform = waveform.to(target_dtype)

        # --- FLAC ---
        elif format == 'flac':
            save_kwargs['compression_level'] = flac_compression
            if torch.is_floating_point(waveform): waveform = torch.clamp(waveform, -1.0, 1.0)

        # --- MP3 ---
        elif format == 'mp3':
            save_kwargs['compression'] = mp3_bitrate
            if not torch.is_floating_point(waveform):
                 print("[SaveAudioAdvanced] Warning: Input waveform is not float for MP3 save. Normalizing.")
                 # Simplified normalization (reuse WAV logic)
                 try:
                     dtype_info = torch.iinfo(waveform.dtype)
                     max_val = dtype_info.max; min_val = dtype_info.min
                     if min_val < 0: waveform = waveform.float() / max(abs(max_val), abs(min_val))
                     else: waveform = (waveform.float() / max_val) * 2.0 - 1.0
                 except TypeError: waveform = waveform.float()
            waveform = torch.clamp(waveform, -1.0, 1.0)


        # --- Saving ---
        saved = False
        try:
            os.makedirs(full_output_folder, exist_ok=True)
            print(f"[SaveAudioAdvanced] Attempting to save to: {filepath} | Format: {format} | SR: {sample_rate} | Shape: {waveform.shape} | Dtype: {waveform.dtype}")
            torchaudio.save(filepath, waveform, sample_rate, format=format, **save_kwargs)
            saved = True
        except Exception as e:
            print(f"[SaveAudioAdvanced] Error saving audio file: {e}")
            if format == 'mp3' and ('backend' in str(e).lower() or 'encoder' in str(e).lower() or 'lame' in str(e).lower()):
                 print("[SaveAudioAdvanced] MP3 saving failed. Ensure FFmpeg (with libmp3lame) is installed and in your system PATH.")
            import traceback
            print(traceback.format_exc()) # Print full traceback for debugging unexpected errors

        # --- Result for UI ---
        if saved:
            print(f"[SaveAudioAdvanced] Saved audio to: {filepath}")
            result_filename = os.path.basename(filepath)
            results = [{"filename": result_filename, "subfolder": subfolder, "type": self.type}]
            return {"ui": {"audio": results}}
        else:
            return {}
