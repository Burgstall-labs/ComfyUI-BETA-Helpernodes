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
        # --- INPUT_TYPES remains unchanged ---
        return { # ... (inputs defined here) ...
             }

    RETURN_TYPES = ()
    FUNCTION = "save_audio"
    OUTPUT_NODE = True
    CATEGORY = "BETA/Audio"

    def save_audio(self, audio, filename_prefix, format,
                   wav_encoding="PCM_16", flac_compression=5, mp3_bitrate=192,
                   prompt=None, extra_pnginfo=None):

        print("[SaveAudioAdvanced] Node execution started.") # Added

        # --- Input Validation Section (as before) ---
        waveform_input = None; sample_rate_input = None; valid_input_format = False
        # ... (logic to handle tuple, wrapped dict, plain dict) ...
        if not valid_input_format: # Add this check if it was missing
             print("[SaveAudioAdvanced] Input format validation failed.") # Added detail
             # ... (full error logging) ...
             return {}
        print(f"[SaveAudioAdvanced] Input format validated successfully. Sample Rate: {sample_rate_input}") # Added

        # --- Tensor Conversion & Prep (as before) ---
        sample_rate = sample_rate_input
        if isinstance(waveform_input, np.ndarray): # ... (numpy conversion) ...
            try: waveform = torch.from_numpy(waveform_input)
            except Exception as e: print(f"[SaveAudioAdvanced] Error: numpy conversion failed: {e}"); return {}
        elif isinstance(waveform_input, torch.Tensor): waveform = waveform_input
        else: print(f"[SaveAudioAdvanced] Error: Internal validation error."); return {}
        print(f"[SaveAudioAdvanced] Waveform is now a tensor. Initial dtype: {waveform.dtype}") # Added

        if waveform.numel() == 0: # Added check for empty tensor
             print("[SaveAudioAdvanced] Error: Input waveform tensor is empty. Cannot save.")
             return {}

        if waveform.device != torch.device('cpu'):
             print("[SaveAudioAdvanced] Moving waveform to CPU.") # Added
             waveform = waveform.cpu()

        # --- Shape Handling (as before) ---
        print(f"[SaveAudioAdvanced] Waveform shape before final processing: {waveform.shape}") # Added
        if waveform.ndim >= 3 and waveform.shape[0] == 1: waveform = waveform.squeeze(0)
        if waveform.ndim == 1: waveform = waveform.unsqueeze(0)
        elif waveform.ndim != 2:
             print(f"[SaveAudioAdvanced] Error: Cannot handle waveform shape {waveform.shape}"); return {}
        print(f"[SaveAudioAdvanced] Waveform shape for saving: {waveform.shape}") # Added


        # --- File Naming (as before) ---
        try: # Added try/except around path generation
            full_output_folder, filename, counter, subfolder, filename_prefix_out = \
                folder_paths.get_save_image_path(filename_prefix, self.output_dir)
            file_extension = f".{format.lower()}"
            filename_with_counter = f"{filename_prefix_out}_{counter:05d}{file_extension}"
            filepath = os.path.join(full_output_folder, filename_with_counter)
            print(f"[SaveAudioAdvanced] Calculated save path: {filepath}") # Added
        except Exception as e:
             print(f"[SaveAudioAdvanced] Error calculating output path: {e}")
             import traceback
             print(traceback.format_exc())
             return {}


        # --- Format Specific Parameters & Data Prep (as before) ---
        save_kwargs = {}
        # ... (logic for WAV, FLAC, MP3 including setting save_kwargs['ab'] for MP3) ...
        # --- Data Prep (ensure waveform range/dtype for chosen format) ---
        # ... (clamping/normalization/type conversion logic for WAV/FLAC/MP3) ...
        print(f"[SaveAudioAdvanced] Waveform final dtype for saving: {waveform.dtype}") # Added
        # Add stats check
        if torch.is_floating_point(waveform):
             print(f"[SaveAudioAdvanced] Waveform stats (float): min={waveform.min():.4f}, max={waveform.max():.4f}, mean={waveform.mean():.4f}")
        else:
             print(f"[SaveAudioAdvanced] Waveform stats (int): min={waveform.min()}, max={waveform.max()}, mean={waveform.float().mean():.4f}")


        # --- Saving ---
        saved = False
        try:
            print("[SaveAudioAdvanced] Ensuring output directory exists...") # Added
            os.makedirs(full_output_folder, exist_ok=True)
            print(f"[SaveAudioAdvanced] Attempting to save with torchaudio...") # Added
            print(f"[SaveAudioAdvanced]   - Path: {filepath}")
            print(f"[SaveAudioAdvanced]   - Format: {format}")
            print(f"[SaveAudioAdvanced]   - SR: {sample_rate}")
            print(f"[SaveAudioAdvanced]   - Shape: {waveform.shape}")
            print(f"[SaveAudioAdvanced]   - Dtype: {waveform.dtype}")
            print(f"[SaveAudioAdvanced]   - Kwargs: {save_kwargs}")

            # The actual save call
            torchaudio.save(filepath, waveform, sample_rate, format=format, **save_kwargs)

            print("[SaveAudioAdvanced] torchaudio.save() completed without raising an exception.") # Added

            # Check if file *actually* exists after save attempt
            if os.path.exists(filepath):
                 print(f"[SaveAudioAdvanced] File check: Confirmed file exists at {filepath}") # Added
                 saved = True
            else:
                 # This is the critical case - save didn't error, but file isn't there.
                 print(f"[SaveAudioAdvanced] File check WARNING: torchaudio.save() completed BUT file does not exist at {filepath}!") # Added
                 print("[SaveAudioAdvanced]   - Check filesystem permissions and available disk space.")
                 print("[SaveAudioAdvanced]   - Check if torchaudio backend (e.g., FFmpeg) wrote to a temporary location or failed silently.")

        except Exception as e:
            # This block remains the same - handles explicit errors during save
            print(f"[SaveAudioAdvanced] Error DURING saving audio file: {e}")
            # ... (rest of exception handling) ...
            if format == 'mp3' and ('backend' in str(e).lower() or 'ab' in str(e).lower()): #...
                 print("[SaveAudioAdvanced] MP3 saving failed...") #...
            import traceback
            print(traceback.format_exc())


        # --- Result for UI ---
        if saved:
            print(f"[SaveAudioAdvanced] Operation successful. Reporting saved file to UI.") # Added
            result_filename = os.path.basename(filepath)
            results = [{"filename": result_filename, "subfolder": subfolder, "type": self.type}]
            return {"ui": {"audio": results}}
        else:
            # This will be reached if 'saved' remains False (e.g., due to the file existence check failing)
            print("[SaveAudioAdvanced] Operation finished, but file was not confirmed saved.") # Added
            return {} # Indicate failure / no file saved
