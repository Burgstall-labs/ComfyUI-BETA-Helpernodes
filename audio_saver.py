# audio_saver.py

import torch
import torchaudio
import os
import folder_paths
import numpy as np
import datetime

# (tensor_to_audio function remains unchanged if you have it)

class SaveAudioAdvanced:
    """
    Saves audio data to a specified format (FLAC, WAV, MP3).
    Handles standard ComfyUI AUDIO tuple (Tensor, int) AND
    the wrapped dictionary format ({'waveform': Tensor, 'sample_rate': int},)
    often output by TTS nodes.
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
        # Style 1: Standard tuple (Tensor, int)
        if isinstance(audio, (tuple, list)) and len(audio) == 2 and \
           isinstance(audio[0], (torch.Tensor, np.ndarray)) and \
           isinstance(audio[1], int):
            waveform_input = audio[0]
            sample_rate_input = audio[1]
            valid_input_format = True
            print("[SaveAudioAdvanced] Info: Received standard AUDIO tuple format (Tensor, int).")

        # Style 2: Wrapped dictionary ({'waveform': Tensor, 'sample_rate': int}, )
        elif isinstance(audio, (tuple, list)) and len(audio) == 1 and \
             isinstance(audio[0], dict):
            audio_dict = audio[0]
            if 'waveform' in audio_dict and 'sample_rate' in audio_dict and \
               isinstance(audio_dict['waveform'], (torch.Tensor, np.ndarray)) and \
               isinstance(audio_dict['sample_rate'], int):
                waveform_input = audio_dict['waveform']
                sample_rate_input = audio_dict['sample_rate']
                valid_input_format = True
                print("[SaveAudioAdvanced] Info: Received wrapped dictionary AUDIO format ({'waveform':..., 'sample_rate':...}).")
            else:
                # Dictionary structure is wrong
                print(f"[SaveAudioAdvanced] Error: Received a wrapped dictionary, but keys/types are incorrect. Expected {{'waveform': Tensor, 'sample_rate': int}}. Got keys: {list(audio_dict.keys())}")
                # Optionally print types too for detailed debugging:
                # print(f"Value types: waveform={type(audio_dict.get('waveform'))}, sample_rate={type(audio_dict.get('sample_rate'))}")
                return {}

        # Handle other invalid formats
        if not valid_input_format:
            print(f"[SaveAudioAdvanced] Error: Input 'audio' is not a recognized AUDIO format. Expected (Tensor, int) or ({{\'waveform\': Tensor, \'sample_rate\': int}},). Received type: {type(audio)}")
            # Help debug by showing the structure if it's a tuple/list
            if isinstance(audio, (tuple, list)):
                 print(f"Received data structure (first element type): {type(audio[0]) if len(audio) > 0 else 'Empty'}")
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
            # It's already a tensor
            waveform = waveform_input
        else:
             # This case should technically be caught by validation, but as a safeguard:
             print(f"[SaveAudioAdvanced] Error: Internal validation error - waveform is neither Tensor nor ndarray after validation. Type: {type(waveform_input)}")
             return {}

        # --- REST OF THE SAVING LOGIC (remains the same as the previous version) ---

        # Ensure waveform is on CPU before saving
        if waveform.device != torch.device('cpu'):
            waveform = waveform.cpu()
            
        # Added: Squeeze potential extra batch dimension often added by TTS nodes
        if waveform.ndim == 3 and waveform.shape[0] == 1:
             print(f"[SaveAudioAdvanced] Info: Input waveform has shape {waveform.shape}. Squeezing batch dimension.")
             waveform = waveform.squeeze(0) # Shape becomes [C, T] or [T]

        # Ensure correct shape (Channels, Time)
        if waveform.ndim == 1:
            print(f"[SaveAudioAdvanced] Info: Input waveform is 1D (mono). Adding channel dimension.")
            waveform = waveform.unsqueeze(0) # Shape becomes [1, T]
        elif waveform.ndim == 2:
             # Shape is already [C, T], good to go.
             pass
        elif waveform.ndim > 2:
             # This should have been handled by the squeeze above, but as a fallback
             print(f"[SaveAudioAdvanced] Warning: Waveform still has more than 2 dimensions ({waveform.shape}) after initial squeeze, attempting general squeeze.")
             waveform = waveform.squeeze()
             if waveform.ndim == 1: # Check if it became mono
                  waveform = waveform.unsqueeze(0)
             if waveform.ndim != 2:
                 print(f"[SaveAudioAdvanced] Error: Could not reshape waveform to [C, T]. Final shape: {waveform.shape}")
                 return {}

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

            # Data range/type adjustments (simplified - torchaudio handles a lot, but clamping is good)
            if target_encoding == "PCM_S":
                if torch.is_floating_point(waveform): waveform = torch.clamp(waveform, -1.0, 1.0) # Torchaudio scales float->int
                # Torchaudio should handle int->int conversion if needed
            elif target_encoding == "PCM_F":
                if not torch.is_floating_point(waveform):
                    print("[SaveAudioAdvanced] Warning: Input waveform is not float for WAV FLOAT save. Normalizing.")
                    if waveform.dtype == torch.int16: waveform = waveform.float() / 32768.0
                    elif waveform.dtype == torch.int32: waveform = waveform.float() / 2147483648.0
                    elif waveform.dtype == torch.int64: waveform = waveform.float() / 9223372036854775808.0
                    elif waveform.dtype == torch.uint8: waveform = (waveform.float() / 127.5) - 1.0
                    else: max_val = torch.iinfo(waveform.dtype).max; waveform = waveform.float() / max_val
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
                 if waveform.dtype == torch.int16: waveform = waveform.float() / 32768.0
                 elif waveform.dtype == torch.int32: waveform = waveform.float() / 2147483648.0
                 elif waveform.dtype == torch.int64: waveform = waveform.float() / 9223372036854775808.0
                 elif waveform.dtype == torch.uint8: waveform = (waveform.float() / 127.5) - 1.0
                 else: max_val = torch.iinfo(waveform.dtype).max; waveform = waveform.float() / max_val
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
            print(traceback.format_exc())

        # --- Result for UI ---
        if saved:
            print(f"[SaveAudioAdvanced] Saved audio to: {filepath}")
            result_filename = os.path.basename(filepath)
            results = [{"filename": result_filename, "subfolder": subfolder, "type": self.type}]
            return {"ui": {"audio": results}}
        else:
            return {}
