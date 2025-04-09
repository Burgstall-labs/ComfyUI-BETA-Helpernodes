import torch
import torchaudio
import os
import folder_paths
import numpy as np
import datetime

# (Keep the tensor_to_audio function if you still need it elsewhere,
# but the main check will happen inside the node now)

class SaveAudioAdvanced:
    """
    Saves audio data (waveform, sample_rate) to a specified format (FLAC, WAV, MP3)
    with options for quality/compression. Expects standard ComfyUI AUDIO input.
    """
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output" # Indicate it's an output node

    @classmethod
    def INPUT_TYPES(cls):
        # --- Keep INPUT_TYPES the same ---
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

        # --- INPUT VALIDATION ---
        if not isinstance(audio, (tuple, list)) or len(audio) != 2:
            print(f"[SaveAudioAdvanced] Error: Input 'audio' is not a valid tuple/list of length 2. Received type: {type(audio)}")
            return {} # Return empty on critical error

        waveform_input, sample_rate_input = audio

        # Validate waveform type explicitly
        if not isinstance(waveform_input, (torch.Tensor, np.ndarray)):
            print(f"[SaveAudioAdvanced] Error: Expected waveform input (1st element of AUDIO tuple) to be a torch.Tensor or numpy.ndarray, but received {type(waveform_input)}.")
            # You could optionally print part of the bad data for debugging:
            # print(f"Received data snippet: {str(waveform_input)[:100]}")
            return {} # Stop execution

        # Validate sample_rate type
        if not isinstance(sample_rate_input, int):
            print(f"[SaveAudioAdvanced] Warning: Expected sample_rate (2nd element of AUDIO tuple) to be an integer, but received {type(sample_rate_input)}. Attempting conversion.")
            try:
                sample_rate = int(sample_rate_input)
            except (ValueError, TypeError) as e:
                 print(f"[SaveAudioAdvanced] Error: Could not convert sample_rate '{sample_rate_input}' to integer: {e}")
                 return {}
        else:
            sample_rate = sample_rate_input # It was already an int

        # --- END VALIDATION ---

        # Now, we know waveform_input is either Tensor or ndarray
        if isinstance(waveform_input, np.ndarray):
             print(f"[SaveAudioAdvanced] Info: Input waveform was numpy.ndarray, converting to tensor.")
             try:
                 waveform = torch.from_numpy(waveform_input)
             except Exception as e:
                 # This conversion is less likely to fail now, but keep safeguard
                 print(f"[SaveAudioAdvanced] Error: Could not convert numpy waveform to tensor: {e}")
                 return {}
        else:
            # It must be a tensor
            waveform = waveform_input


        # --- REST OF THE SAVING LOGIC (remains the same) ---

        # Ensure waveform is on CPU before saving
        if waveform.device != torch.device('cpu'):
            waveform = waveform.cpu()

        # Ensure correct shape (Channels, Time)
        if waveform.ndim == 1:
            waveform = waveform.unsqueeze(0)
        elif waveform.ndim > 2:
            print(f"[SaveAudioAdvanced] Warning: Waveform has more than 2 dimensions ({waveform.shape}), attempting to use first two.")
            # Try to intelligently handle common extra dimensions (e.g., batch)
            if waveform.shape[0] == 1 and waveform.ndim == 3: # Shape like [1, C, T]?
                waveform = waveform.squeeze(0)
            elif waveform.shape[-1] == 1 or waveform.shape[-1] == 2 and waveform.ndim == 3: # Shape like [B, T, C]? -> Needs transpose
                 print(f"[SaveAudioAdvanced] Warning: Waveform might be in [B, T, C] format. Attempting transpose.")
                 try:
                      waveform = waveform.permute(0, 2, 1)[0] # Take first batch item, transpose C and T
                      if waveform.ndim == 1: # If it became mono after transpose/select
                           waveform = waveform.unsqueeze(0)
                 except Exception as e:
                      print(f"[SaveAudioAdvanced] Error: Failed to reshape potential [B, T, C] waveform: {e}")
                      return {}
            else: # General squeeze attempt
                 waveform = waveform.squeeze()
            # Re-check dimensions after attempting fixes
            if waveform.ndim == 1:
                 waveform = waveform.unsqueeze(0)
            if waveform.ndim != 2:
                 print(f"[SaveAudioAdvanced] Error: Could not reshape waveform to [C, T] after handling extra dimensions. Final shape: {waveform.shape}")
                 return {}


        # --- File Naming ---
        full_output_folder, filename, counter, subfolder, filename_prefix_out = \
            folder_paths.get_save_image_path(filename_prefix, self.output_dir) # Reusing image path logic is fine

        file_extension = f".{format.lower()}"
        # Use the dynamically generated filename part
        filename_with_counter = f"{filename_prefix_out}_{counter:05d}{file_extension}"
        filepath = os.path.join(full_output_folder, filename) # folder_paths handles subfolder creation
        # Correct the final filepath to use the counter filename
        filepath = os.path.join(full_output_folder, filename_with_counter)

        # --- Format Specific Parameters ---
        save_kwargs = {}
        if format == 'wav':
            encoding_map = {
                "PCM_16": {"encoding": "PCM_S", "bits_per_sample": 16},
                "PCM_24": {"encoding": "PCM_S", "bits_per_sample": 24},
                "PCM_32": {"encoding": "PCM_S", "bits_per_sample": 32},
                "FLOAT_32": {"encoding": "PCM_F", "bits_per_sample": 32},
                "FLOAT_64": {"encoding": "PCM_F", "bits_per_sample": 64},
            }
            if wav_encoding in encoding_map:
                 save_kwargs.update(encoding_map[wav_encoding])
            else:
                 print(f"[SaveAudioAdvanced] Warning: Unknown WAV encoding '{wav_encoding}'. Using default PCM_16.")
                 save_kwargs.update(encoding_map["PCM_16"])

            # Data range adjustments based on target encoding
            target_encoding = save_kwargs.get('encoding', 'PCM_S') # Default check just in case
            bits_per_sample = save_kwargs.get('bits_per_sample', 16)
            
            if target_encoding == "PCM_S": # Integer target
                if torch.is_floating_point(waveform):
                     # Scale float [-1, 1] to integer range
                     max_val = 2**(bits_per_sample - 1)
                     waveform = torch.clamp(waveform * max_val, -max_val, max_val -1).to(getattr(torch, f"int{bits_per_sample}")) # Convert to target int type
                elif waveform.dtype != getattr(torch, f"int{bits_per_sample}"):
                     print(f"[SaveAudioAdvanced] Warning: Input waveform is integer but not {bits_per_sample}-bit. Attempting conversion. Ensure range is correct.")
                     # Needs careful range handling if converting between int types
                     # For simplicity, let torchaudio handle it, but warn the user.
                     pass # Torchaudio might handle this, but explicit conversion is safer if needed
            
            elif target_encoding == "PCM_F": # Float target
                if not torch.is_floating_point(waveform):
                      print("[SaveAudioAdvanced] Warning: Input waveform is not float for WAV FLOAT save. Converting and normalizing.")
                      # Normalize integer types to float [-1.0, 1.0]
                      if waveform.dtype == torch.int16: waveform = waveform.float() / 32768.0
                      elif waveform.dtype == torch.int32: waveform = waveform.float() / 2147483648.0
                      elif waveform.dtype == torch.int64: waveform = waveform.float() / 9223372036854775808.0
                      elif waveform.dtype == torch.uint8: waveform = (waveform.float() / 127.5) - 1.0
                      else:
                           print(f"[SaveAudioAdvanced] Warning: Unknown integer type {waveform.dtype} for float conversion. Attempting max value normalization.")
                           max_val = torch.iinfo(waveform.dtype).max
                           waveform = waveform.float() / max_val
                # Clamp float to [-1.0, 1.0] just in case, torchaudio expects this range for float save
                waveform = torch.clamp(waveform, -1.0, 1.0)
                # Ensure correct float type (float32 or float64)
                target_dtype = torch.float32 if bits_per_sample == 32 else torch.float64
                if waveform.dtype != target_dtype:
                     waveform = waveform.to(target_dtype)


        elif format == 'flac':
            save_kwargs['compression_level'] = flac_compression # torchaudio uses compression_level
            # FLAC generally expects data that can be losslessly converted to int.
            # Torchaudio handles conversion from float [-1, 1] by default.
            if torch.is_floating_point(waveform):
                 waveform = torch.clamp(waveform, -1.0, 1.0) # Ensure range for float input
            else:
                 print("[SaveAudioAdvanced] Info: Input waveform is integer type for FLAC save. Ensure range is appropriate.")

        elif format == 'mp3':
            save_kwargs['compression'] = mp3_bitrate # torchaudio uses compression for MP3 bitrate
             # MP3 encoders usually expect float input in [-1.0, 1.0]
            if not torch.is_floating_point(waveform):
                 print("[SaveAudioAdvanced] Warning: Input waveform is not float for MP3 save. Converting and normalizing.")
                 # Normalize integer types to float [-1.0, 1.0] (similar to WAV Float)
                 if waveform.dtype == torch.int16: waveform = waveform.float() / 32768.0
                 elif waveform.dtype == torch.int32: waveform = waveform.float() / 2147483648.0
                 elif waveform.dtype == torch.int64: waveform = waveform.float() / 9223372036854775808.0
                 elif waveform.dtype == torch.uint8: waveform = (waveform.float() / 127.5) - 1.0
                 else:
                      print(f"[SaveAudioAdvanced] Warning: Unknown integer type {waveform.dtype} for float conversion. Attempting max value normalization.")
                      max_val = torch.iinfo(waveform.dtype).max
                      waveform = waveform.float() / max_val
            # Clamp float to [-1.0, 1.0]
            waveform = torch.clamp(waveform, -1.0, 1.0)

        # --- Saving ---
        saved = False
        try:
            # Ensure the directory exists (folder_paths.get_save_image_path should handle the base, but maybe not subfolder?)
            os.makedirs(full_output_folder, exist_ok=True) # Ensure final subfolder exists
            print(f"[SaveAudioAdvanced] Attempting to save to: {filepath} | Format: {format} | Sample Rate: {sample_rate} | Shape: {waveform.shape} | Dtype: {waveform.dtype}")
            
            # Provide explicit format argument to torchaudio.save
            torchaudio.save(filepath, waveform, sample_rate, format=format, **save_kwargs)
            saved = True
        except Exception as e:
            print(f"[SaveAudioAdvanced] Error saving audio file: {e}")
            # Add specific backend check for MP3
            if format == 'mp3' and ('backend' in str(e).lower() or 'encoder' in str(e).lower() or 'lame' in str(e).lower()):
                 print("[SaveAudioAdvanced] MP3 saving failed. Ensure FFmpeg (with libmp3lame) is installed and in your system PATH.")
            import traceback
            print(traceback.format_exc())

        # --- Result for UI ---
        if saved:
            print(f"[SaveAudioAdvanced] Saved audio to: {filepath}")
            # Extract just the filename for the UI result
            result_filename = os.path.basename(filepath)
            results = [{"filename": result_filename, "subfolder": subfolder, "type": self.type}]
            return {"ui": {"audio": results}} # Using "audio" key might enable future ComfyUI previews
        else:
            return {}
