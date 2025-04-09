import torch
import torchaudio
import os
import folder_paths
import numpy as np
import datetime

# Tensor to Audio Conversion (if needed, often handled by upstream nodes)
def tensor_to_audio(tensor):
    # Assuming tensor is in the shape [C, T] or [T]
    # Convert to numpy array if it's not already
    if hasattr(tensor, 'cpu'): # Check if it's a PyTorch tensor
        tensor = tensor.cpu().numpy()
    
    # Ensure it's float32 and potentially normalize if necessary (depends on source)
    # Torchaudio save expects [-1.0, 1.0] for float, or integer types
    if tensor.dtype == np.float64:
        tensor = tensor.astype(np.float32)
    elif tensor.dtype == np.int32:
         # Convert int32 to int16 if necessary for some formats, or keep as is
         # Let torchaudio handle appropriate conversion based on encoding request
         pass 
    elif tensor.dtype == np.int16:
         pass # Already int16
    elif tensor.dtype == np.uint8:
        # Convert uint8 (often 0-255) to float32 [-1.0, 1.0]
        tensor = (tensor.astype(np.float32) / 127.5) - 1.0
    
    # Ensure shape is [C, T] - Torchaudio prefers channels first
    if tensor.ndim == 1:
        tensor = np.expand_dims(tensor, axis=0) # Add channel dimension

    return torch.from_numpy(tensor) # Return as torch tensor

class SaveAudioAdvanced:
    """
    Saves audio data (waveform, sample_rate) to a specified format (FLAC, WAV, MP3)
    with options for quality/compression.
    """
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output" # Indicate it's an output node

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO", ),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "format": (["flac", "wav", "mp3"], {"default": "flac"}),
            },
            "optional": {
                # WAV specific options
                "wav_encoding": (["PCM_16", "PCM_24", "PCM_32", "FLOAT_32", "FLOAT_64"], {"default": "PCM_16"}),
                # FLAC specific options
                "flac_compression": ("INT", {"default": 5, "min": 0, "max": 8, "step": 1}),
                # MP3 specific options
                "mp3_bitrate": ("INT", {"default": 192, "min": 8, "max": 320, "step": 8}), # Common MP3 bitrates
            },
             "hidden": { # Hidden inputs for prompt details
                "prompt": "PROMPT", 
                "extra_pnginfo": "EXTRA_PNGINFO"
             },
        }

    RETURN_TYPES = () # No data output from this node
    FUNCTION = "save_audio"
    OUTPUT_NODE = True
    # Let's categorize it clearly within the pack
    CATEGORY = "BETA/Audio" 

    def save_audio(self, audio, filename_prefix, format, 
                   wav_encoding="PCM_16", flac_compression=5, mp3_bitrate=192, 
                   prompt=None, extra_pnginfo=None):
        
        waveform, sample_rate = audio
        
        # Ensure waveform is a PyTorch tensor
        if not isinstance(waveform, torch.Tensor):
             print(f"[SaveAudioAdvanced] Warning: Input waveform was not a tensor, attempting conversion.")
             # Add more robust conversion if needed, assuming it might be numpy
             try:
                 waveform = torch.from_numpy(waveform)
             except Exception as e:
                 print(f"[SaveAudioAdvanced] Error: Could not convert input waveform to tensor: {e}")
                 return {} # Return empty on critical error

        # Ensure waveform is on CPU before saving
        if waveform.device != torch.device('cpu'):
            waveform = waveform.cpu()

        # Ensure correct shape (Channels, Time)
        if waveform.ndim == 1:
            waveform = waveform.unsqueeze(0) # Add channel dimension if mono
        elif waveform.ndim > 2:
            print(f"[SaveAudioAdvanced] Warning: Waveform has more than 2 dimensions ({waveform.shape}), attempting to use first two.")
            waveform = waveform.squeeze() # Try squeezing extra dims
            if waveform.ndim > 2 : # If still too many dims, take first element
                 waveform = waveform[0]
            if waveform.ndim == 1: # Check if it became mono after squeeze
                 waveform = waveform.unsqueeze(0)
            if waveform.ndim != 2:
                 print(f"[SaveAudioAdvanced] Error: Could not reshape waveform to [C, T]. Shape is {waveform.shape}")
                 return {}


        # --- File Naming ---
        # Use ComfyUI's utility to create unique filenames/subfolders
        full_output_folder, filename, counter, subfolder, filename_prefix_out = \
            folder_paths.get_save_image_path(filename_prefix, self.output_dir)
        
        # Ensure the selected format is the extension
        file_extension = f".{format.lower()}"
        filename = f"{filename_prefix_out}_{counter:05d}{file_extension}"
        filepath = os.path.join(full_output_folder, filename)

        # --- Format Specific Parameters ---
        save_kwargs = {}
        if format == 'wav':
            # Map user string to torchaudio encoding parameters if necessary
            # Note: torchaudio often infers bits_per_sample from encoding
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
                 print(f"[SaveAudioAdvanced] Warning: Unknown WAV encoding '{wav_encoding}'. Using default.")
                 # Default to PCM_16 if mapping fails
                 save_kwargs.update(encoding_map["PCM_16"])
            
            # Ensure waveform is in the correct range for the target encoding
            if save_kwargs['encoding'] == "PCM_S":
                 # Integer formats expect data in range [-2^(bits-1), 2^(bits-1)-1]
                 # Usually torchaudio handles scaling from float [-1, 1] automatically,
                 # but let's check if input is already integer - if so, it might need clamping/scaling.
                 if not torch.is_floating_point(waveform):
                      print("[SaveAudioAdvanced] Warning: Input waveform is integer type for WAV PCM save. Ensure it's scaled correctly.")
                      # Optional: Add explicit scaling/clamping here if issues arise
            elif save_kwargs['encoding'] == "PCM_F":
                 # Float formats typically expect [-1.0, 1.0]
                 if not torch.is_floating_point(waveform):
                      print("[SaveAudioAdvanced] Warning: Input waveform is not float for WAV FLOAT save. Converting.")
                      # Convert integer types to float. Assume standard ranges.
                      if waveform.dtype == torch.int16:
                           waveform = waveform.float() / 32768.0
                      elif waveform.dtype == torch.int32:
                            waveform = waveform.float() / 2147483648.0
                      elif waveform.dtype == torch.uint8: # Less common for audio processing output
                           waveform = (waveform.float() / 127.5) - 1.0
                      else: # Other int types - use a sensible default scaling
                           print(f"[SaveAudioAdvanced] Warning: Unknown integer type {waveform.dtype}. Attempting generic scaling.")
                           max_val = torch.iinfo(waveform.dtype).max
                           waveform = waveform.float() / max_val
                 # Clamp float to [-1.0, 1.0] just in case
                 waveform = torch.clamp(waveform, -1.0, 1.0)


        elif format == 'flac':
            save_kwargs['compression'] = flac_compression
            # FLAC usually uses integer formats internally, but torchaudio handles conversion from float
            # Ensure input float waveform is in [-1.0, 1.0] range
            if torch.is_floating_point(waveform):
                 waveform = torch.clamp(waveform, -1.0, 1.0)
            else:
                 # If input is already int, torchaudio *should* handle it, maybe warn
                 print("[SaveAudioAdvanced] Warning: Input waveform is integer type for FLAC save. Ensure range is appropriate.")


        elif format == 'mp3':
            save_kwargs['bitrate'] = mp3_bitrate
            # MP3 encoders usually expect float input in [-1.0, 1.0]
            if not torch.is_floating_point(waveform):
                 print("[SaveAudioAdvanced] Warning: Input waveform is not float for MP3 save. Converting.")
                 # Similar conversion as for WAV FLOAT
                 if waveform.dtype == torch.int16:
                      waveform = waveform.float() / 32768.0
                 elif waveform.dtype == torch.int32:
                      waveform = waveform.float() / 2147483648.0
                 elif waveform.dtype == torch.uint8:
                      waveform = (waveform.float() / 127.5) - 1.0
                 else:
                      print(f"[SaveAudioAdvanced] Warning: Unknown integer type {waveform.dtype}. Attempting generic scaling.")
                      max_val = torch.iinfo(waveform.dtype).max
                      waveform = waveform.float() / max_val
            # Clamp float to [-1.0, 1.0]
            waveform = torch.clamp(waveform, -1.0, 1.0)

        # --- Saving ---
        saved = False
        try:
            torchaudio.save(filepath, waveform, sample_rate, format=format, **save_kwargs)
            saved = True
        except Exception as e:
            # Provide more specific feedback if possible
            if format == 'mp3' and ('backend' in str(e) or 'sox' in str(e) or 'LAME' in str(e)):
                print(f"[SaveAudioAdvanced] Error saving MP3: {e}")
                print("[SaveAudioAdvanced] This often means the required MP3 encoder (like LAME) or backend (like FFmpeg/SoX) is not installed or not found by torchaudio.")
                print("[SaveAudioAdvanced] Please ensure FFmpeg (with libmp3lame enabled) or SoX is installed and accessible in your system's PATH.")
            else:
                print(f"[SaveAudioAdvanced] Error saving audio file: {e}")
                import traceback
                print(traceback.format_exc()) # Print detailed traceback for debugging

        # --- Result for UI ---
        if saved:
            print(f"[SaveAudioAdvanced] Saved audio to: {filepath}")
            results = [{"filename": filename, "subfolder": subfolder, "type": self.type}]
            return {"ui": {"audio": results}} # Use "audio" key for potential preview if ComfyUI supports it
        else:
            # Return an empty dict or signal error if saving failed
            return {} # Indicate failure / no file saved

# 3. Node Registration (see next step)