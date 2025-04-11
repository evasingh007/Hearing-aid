import numpy as np
import sounddevice as sd
import tkinter as tk
from tkinter import ttk, filedialog
import threading
from scipy.signal import butter, lfilter
from scipy.io import wavfile
import os
import time
import queue

class SimpleHearingAid:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Hearing Aid")
        self.root.geometry("550x500")
        
        self.frame = ttk.Frame(root, padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Simple controls
        ttk.Label(self.frame, text="Hearing Aid Controls", font=("Arial", 14)).pack(pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Live audio tab
        self.live_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.live_frame, text="Live Audio")
        
        # Pre-recorded tab
        self.recorded_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.recorded_frame, text="Pre-recorded Audio")
        
        # Recording tab
        self.recording_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.recording_frame, text="Record Audio")
        
        # === Live Audio Tab Controls ===
        # Volume control
        ttk.Label(self.live_frame, text="Volume:").pack(anchor="w")
        self.gain_var = tk.DoubleVar(value=2.0)
        ttk.Scale(self.live_frame, from_=0.5, to=5.0, variable=self.gain_var).pack(fill="x")
        
        # Clarity control
        ttk.Label(self.live_frame, text="Speech Clarity:").pack(anchor="w")
        self.clarity_var = tk.DoubleVar(value=0.7)
        ttk.Scale(self.live_frame, from_=0.0, to=1.0, variable=self.clarity_var).pack(fill="x")
        
        # Start/Stop button
        self.is_processing = False
        self.button = ttk.Button(self.live_frame, text="Start Hearing Aid", command=self.toggle_processing)
        self.button.pack(pady=20)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.live_frame, textvariable=self.status_var).pack()
        
        # === Pre-recorded Audio Tab Controls ===
        # File selection
        ttk.Label(self.recorded_frame, text="Audio File:").pack(anchor="w")
        
        self.file_frame = ttk.Frame(self.recorded_frame)
        self.file_frame.pack(fill="x", pady=5)
        
        self.file_path_var = tk.StringVar(value="No file selected")
        ttk.Label(self.file_frame, textvariable=self.file_path_var, width=40).pack(side=tk.LEFT)
        ttk.Button(self.file_frame, text="Browse...", command=self.browse_file).pack(side=tk.RIGHT)
        
        # Volume control for recorded audio
        ttk.Label(self.recorded_frame, text="Volume:").pack(anchor="w")
        self.recorded_gain_var = tk.DoubleVar(value=2.0)
        ttk.Scale(self.recorded_frame, from_=0.5, to=5.0, variable=self.recorded_gain_var).pack(fill="x")
        
        # Clarity control for recorded audio
        ttk.Label(self.recorded_frame, text="Speech Clarity:").pack(anchor="w")
        self.recorded_clarity_var = tk.DoubleVar(value=0.7)
        ttk.Scale(self.recorded_frame, from_=0.0, to=1.0, variable=self.recorded_clarity_var).pack(fill="x")
        
        # Playback control buttons
        self.playback_frame = ttk.Frame(self.recorded_frame)
        self.playback_frame.pack(pady=20)
        
        self.play_button = ttk.Button(self.playback_frame, text="Play", command=self.play_audio, state="disabled")
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(self.playback_frame, text="Stop", command=self.stop_audio, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Status for recorded playback
        self.recorded_status_var = tk.StringVar(value="No file loaded")
        ttk.Label(self.recorded_frame, textvariable=self.recorded_status_var).pack()
        
        # === Recording Tab Controls ===
        # Recording controls
        ttk.Label(self.recording_frame, text="Record New Audio").pack(anchor="w", pady=5)
        
        # Duration frame
        self.duration_frame = ttk.Frame(self.recording_frame)
        self.duration_frame.pack(fill="x", pady=5)
        
        ttk.Label(self.duration_frame, text="Recording Duration (sec):").pack(side=tk.LEFT)
        self.duration_var = tk.IntVar(value=10)
        ttk.Spinbox(self.duration_frame, from_=1, to=60, textvariable=self.duration_var, width=5).pack(side=tk.LEFT, padx=5)
        
        # File name frame
        self.record_file_frame = ttk.Frame(self.recording_frame)
        self.record_file_frame.pack(fill="x", pady=5)
        
        ttk.Label(self.record_file_frame, text="Save As:").pack(side=tk.LEFT)
        self.record_filename_var = tk.StringVar(value="recording.wav")
        ttk.Entry(self.record_file_frame, textvariable=self.record_filename_var).pack(side=tk.LEFT, padx=5, fill="x", expand=True)
        
        # Recording buttons
        self.record_buttons_frame = ttk.Frame(self.recording_frame)
        self.record_buttons_frame.pack(pady=10)
        
        self.record_button = ttk.Button(self.record_buttons_frame, text="Start Recording", command=self.start_recording)
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        # Playback controls for recorded audio
        ttk.Separator(self.recording_frame, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(self.recording_frame, text="Recorded Audio Playback").pack(anchor="w", pady=5)
        
        # Volume control for custom recording
        ttk.Label(self.recording_frame, text="Volume:").pack(anchor="w")
        self.custom_gain_var = tk.DoubleVar(value=2.0)
        ttk.Scale(self.recording_frame, from_=0.5, to=5.0, variable=self.custom_gain_var).pack(fill="x")
        
        # Clarity control for custom recording
        ttk.Label(self.recording_frame, text="Speech Clarity:").pack(anchor="w")
        self.custom_clarity_var = tk.DoubleVar(value=0.7)
        ttk.Scale(self.recording_frame, from_=0.0, to=1.0, variable=self.custom_clarity_var).pack(fill="x")
        
        # Custom recording playback buttons
        self.custom_playback_frame = ttk.Frame(self.recording_frame)
        self.custom_playback_frame.pack(pady=10)
        
        self.custom_play_button = ttk.Button(self.custom_playback_frame, text="Play Recording", 
                                           command=self.play_custom_recording, state="disabled")
        self.custom_play_button.pack(side=tk.LEFT, padx=5)
        
        self.custom_stop_button = ttk.Button(self.custom_playback_frame, text="Stop", 
                                           command=self.stop_custom_playback, state="disabled")
        self.custom_stop_button.pack(side=tk.LEFT, padx=5)
        
        # Recording status
        self.recording_status_var = tk.StringVar(value="Ready to record")
        ttk.Label(self.recording_frame, textvariable=self.recording_status_var).pack()
        
        # Audio file data
        self.audio_file = None
        self.audio_fs = None
        self.is_playing = False
        
        # Recording data
        self.is_recording = False
        self.recorded_audio = None
        self.record_fs = 44100
        self.recording_queue = queue.Queue()
        self.is_custom_playing = False
        
    def browse_file(self):
        filetypes = [("WAV files", "*.wav"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select Audio File", filetypes=filetypes)
        
        if filename:
            try:
                self.audio_fs, self.audio_file = wavfile.read(filename)
                # Convert to float and normalize
                self.audio_file = self.audio_file.astype(np.float32)
                if self.audio_file.ndim > 1:  # Stereo to mono
                    self.audio_file = np.mean(self.audio_file, axis=1)
                self.audio_file = self.audio_file / np.max(np.abs(self.audio_file))
                
                # Update UI
                basename = os.path.basename(filename)
                self.file_path_var.set(basename)
                self.recorded_status_var.set(f"Loaded: {basename}")
                self.play_button.config(state="normal")
                
            except Exception as e:
                self.recorded_status_var.set(f"Error loading file: {str(e)}")
                self.audio_file = None
                self.audio_fs = None
                self.play_button.config(state="disabled")
    
    def start_recording(self):
        if self.is_recording:
            return
            
        duration = self.duration_var.get()
        filename = self.record_filename_var.get()
        
        # Validate filename
        if not filename.endswith('.wav'):
            filename += '.wav'
            self.record_filename_var.set(filename)
        
        self.is_recording = True
        self.record_button.config(text="Recording...", state="disabled")
        self.recording_status_var.set(f"Recording... ({duration} seconds)")
        
        # Clear the queue
        while not self.recording_queue.empty():
            try:
                self.recording_queue.get_nowait()
            except queue.Empty:
                break
        
        # Start recording in a separate thread
        threading.Thread(target=self.record_audio, args=(duration, filename), daemon=True).start()
    
    def record_audio(self, duration, filename):
        fs = self.record_fs
        channels = 1
        
        # Calculate total frames to record
        total_frames = int(fs * duration)
        recorded_frames = []
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Recording status: {status}")
            self.recording_queue.put(indata.copy())
        
        try:
            # Start recording
            with sd.InputStream(samplerate=fs, channels=channels, callback=audio_callback):
                # Update countdown timer
                for remaining in range(duration, 0, -1):
                    if not self.root.winfo_exists():
                        return
                    self.root.after(0, lambda r=remaining: self.recording_status_var.set(f"Recording... ({r} seconds remaining)"))
                    sd.sleep(1000)  # Sleep for 1 second
            
            # Process recorded audio
            while not self.recording_queue.empty():
                try:
                    recorded_frames.append(self.recording_queue.get_nowait())
                except queue.Empty:
                    break
            
            if not recorded_frames:
                self.root.after(0, lambda: self.recording_status_var.set("Error: No audio recorded"))
                self.root.after(0, self.reset_recording_ui)
                return
                
            # Concatenate all frames
            recorded_data = np.concatenate(recorded_frames, axis=0)
            if recorded_data.ndim > 1:
                recorded_data = recorded_data[:, 0]  # Use only first channel if stereo
            
            # Normalize
            recorded_data = recorded_data / np.max(np.abs(recorded_data)) if np.max(np.abs(recorded_data)) > 0 else recorded_data
            
            # Save to file
            try:
                wavfile.write(filename, fs, (recorded_data * 32767).astype(np.int16))
                self.recorded_audio = recorded_data
                self.root.after(0, lambda: self.recording_status_var.set(f"Recording saved as {filename}"))
                self.root.after(0, lambda: self.custom_play_button.config(state="normal"))
            except Exception as e:
                self.root.after(0, lambda: self.recording_status_var.set(f"Error saving recording: {str(e)}"))
        
        except Exception as e:
            self.root.after(0, lambda: self.recording_status_var.set(f"Recording error: {str(e)}"))
        
        finally:
            self.root.after(0, self.reset_recording_ui)
    
    def reset_recording_ui(self):
        self.is_recording = False
        self.record_button.config(text="Start Recording", state="normal")
    
    def play_custom_recording(self):
        if self.recorded_audio is None or self.is_custom_playing:
            return
            
        self.is_custom_playing = True
        self.custom_play_button.config(state="disabled")
        self.custom_stop_button.config(state="normal")
        self.recording_status_var.set("Playing recorded audio...")
        
        # Start playback in a separate thread
        threading.Thread(target=self.process_custom_recording, daemon=True).start()
    
    def stop_custom_playback(self):
        self.is_custom_playing = False
        self.custom_play_button.config(state="normal")
        self.custom_stop_button.config(state="disabled")
        self.recording_status_var.set("Playback stopped")
    
    def process_custom_recording(self):
        fs = self.record_fs
        blocksize = 1024
        b, a = self.design_bandpass_filter(fs=fs)
        
        # Process the entire audio recording in chunks
        audio_len = len(self.recorded_audio)
        pos = 0
        
        try:
            def callback(outdata, frames, time, status):
                nonlocal pos
                if status:
                    print(f"Status: {status}")
                
                if pos >= audio_len or not self.is_custom_playing or not self.root.winfo_exists():
                    # End of recording or stopped
                    if self.is_custom_playing and pos >= audio_len:
                        # Auto-stop at end of recording
                        self.root.after(0, self.stop_custom_playback)
                        self.recording_status_var.set("Playback complete")
                    
                    # Provide silence if we're still playing
                    outdata.fill(0)
                    return
                
                # Calculate how many frames to read
                chunk_size = min(frames, audio_len - pos)
                
                # Get chunk and apply processing
                chunk = self.recorded_audio[pos:pos+chunk_size]
                gain = self.custom_gain_var.get()
                clarity = self.custom_clarity_var.get()
                
                processed = self.apply_processing(chunk, gain, clarity, b, a)
                
                # Output processed audio
                if len(processed) < frames:
                    outdata[:len(processed), 0] = processed
                    outdata[len(processed):, 0] = 0
                else:
                    outdata[:, 0] = processed
                
                # If stereo output, duplicate to all channels
                if outdata.shape[1] > 1:
                    for i in range(1, outdata.shape[1]):
                        outdata[:, i] = outdata[:, 0]
                
                # Move position forward
                pos += chunk_size
            
            # Start streaming
            with sd.OutputStream(samplerate=fs, channels=1, callback=callback, 
                               blocksize=blocksize, finished_callback=None):
                while self.is_custom_playing and self.root.winfo_exists():
                    sd.sleep(100)
                    
        except Exception as e:
            print(f"Error in custom playback: {e}")
            self.root.after(0, lambda: self.recording_status_var.set(f"Error: {str(e)}"))
            self.root.after(0, self.stop_custom_playback)
    
    def play_audio(self):
        if self.audio_file is None or self.is_playing:
            return
            
        self.is_playing = True
        self.play_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.recorded_status_var.set("Playing...")
        
        # Start playback in a separate thread
        threading.Thread(target=self.process_recorded_audio, daemon=True).start()
    
    def stop_audio(self):
        self.is_playing = False
        self.play_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.recorded_status_var.set("Stopped")
    
    def toggle_processing(self):
        if self.is_processing:
            self.is_processing = False
            self.button.config(text="Start Hearing Aid")
            self.status_var.set("Stopped")
        else:
            self.is_processing = True
            self.button.config(text="Stop Hearing Aid")
            self.status_var.set("Processing audio...")
            threading.Thread(target=self.process_audio, daemon=True).start()
    
    def design_bandpass_filter(self, lowcut=300, highcut=5000, fs=44100):
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(4, [low, high], btype='band')
        return b, a
    
    def apply_processing(self, audio_in, gain, clarity, b, a):
        # Apply bandpass filter
        filtered = lfilter(b, a, audio_in)
        
        # Apply speech clarity enhancement
        if clarity > 0:
            speech_b, speech_a = butter(2, [1000/22050, 3000/22050], btype='band')
            enhanced = lfilter(speech_b, speech_a, filtered)
            # Blend original and enhanced based on clarity setting
            filtered = (1-clarity) * filtered + clarity * enhanced * 1.5
        
        # Apply gain and prevent clipping
        processed = np.clip(filtered * gain, -0.99, 0.99)
        return processed
    
    def process_audio(self):
        fs = 44100
        blocksize = 1024
        b, a = self.design_bandpass_filter()
        
        def audio_callback(indata, outdata, frames, time, status):
            if status:
                print(f"Status: {status}")
            
            audio_in = indata[:, 0] if indata.ndim > 1 else indata[:]
            gain = self.gain_var.get()
            clarity = self.clarity_var.get()
            
            processed = self.apply_processing(audio_in, gain, clarity, b, a)
            
            # Output to all channels
            if outdata.ndim > 1:
                for i in range(outdata.shape[1]):
                    outdata[:, i] = processed
            else:
                outdata[:] = processed
        
        try:
            with sd.Stream(channels=1, callback=audio_callback, 
                          samplerate=fs, blocksize=blocksize,
                          latency='low'):
                while self.is_processing and self.root.winfo_exists():
                    sd.sleep(100)
        except Exception as e:
            print(f"Error: {e}")
            self.is_processing = False
            self.status_var.set(f"Error: {str(e)}")
            self.button.config(text="Start Hearing Aid")

    def process_recorded_audio(self):
        fs = self.audio_fs
        blocksize = 1024
        b, a = self.design_bandpass_filter(fs=fs)
        
        # Process the entire audio file in chunks
        audio_len = len(self.audio_file)
        pos = 0
        
        try:
            def callback(outdata, frames, time, status):
                nonlocal pos
                if status:
                    print(f"Status: {status}")
                
                if pos >= audio_len or not self.is_playing or not self.root.winfo_exists():
                    # End of file or stopped
                    if self.is_playing and pos >= audio_len:
                        # Auto-stop at end of file
                        self.root.after(0, self.stop_audio)
                        self.recorded_status_var.set("Playback complete")
                    
                    # Provide silence if we're still playing
                    outdata.fill(0)
                    return
                
                # Calculate how many frames to read
                chunk_size = min(frames, audio_len - pos)
                
                # Get chunk and apply processing
                chunk = self.audio_file[pos:pos+chunk_size]
                gain = self.recorded_gain_var.get()
                clarity = self.recorded_clarity_var.get()
                
                processed = self.apply_processing(chunk, gain, clarity, b, a)
                
                # Output processed audio
                if len(processed) < frames:
                    outdata[:len(processed), 0] = processed
                    outdata[len(processed):, 0] = 0
                else:
                    outdata[:, 0] = processed
                
                # If stereo output, duplicate to all channels
                if outdata.shape[1] > 1:
                    for i in range(1, outdata.shape[1]):
                        outdata[:, i] = outdata[:, 0]
                
                # Move position forward
                pos += chunk_size
            
            # Start streaming
            with sd.OutputStream(samplerate=fs, channels=1, callback=callback, 
                               blocksize=blocksize, finished_callback=None):
                while self.is_playing and self.root.winfo_exists():
                    sd.sleep(100)
                    
        except Exception as e:
            print(f"Error in playback: {e}")
            self.root.after(0, lambda: self.recorded_status_var.set(f"Error: {str(e)}"))
            self.root.after(0, self.stop_audio)

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleHearingAid(root)
    root.mainloop()