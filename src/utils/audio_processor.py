import time
import numpy as np
import av
import sounddevice as sd
from PyQt6.QtCore import QThread, pyqtSignal

class AudioProcessor(QThread):
    # Signals for UI updates
    rms_level_signal = pyqtSignal(int)
    moo_detected_signal = pyqtSignal()
    alarm_signal = pyqtSignal()
    status_signal = pyqtSignal(str)

    def __init__(self, rtsp_url, sensitivity=50):
        super().__init__()
        self.rtsp_url = rtsp_url
        self._run_flag = True
        
        # Parameters
        self.sensitivity = sensitivity # 0-100
        self.cooldown_until = 0.0 # To prevent self-triggering during alarm
        
        # Moo detection states
        self.high_rms_duration = 0.0
        self.low_rms_duration = 0.0
        self.moo_timestamps = []
        
        # Live playback
        self.is_muted = False
        self.stream_audio = None
        
    def set_sensitivity(self, value):
        self.sensitivity = value

    def set_muted(self, muted: bool):
        self.is_muted = muted
        if muted and self.stream_audio is not None:
            self.stream_audio.stop()
            self.stream_audio.close()
            self.stream_audio = None

    def set_cooldown(self, seconds=10):
        """Mutes analysis for `seconds` to ignore alarm sound."""
        self.cooldown_until = time.time() + seconds
        
    def run(self):
        while self._run_flag:
            try:
                # Open the stream with timeout options
                container = av.open(self.rtsp_url, options={'timeout': '5000000'})
                
                audio_streams = container.streams.audio
                if not audio_streams:
                    self.status_signal.emit("Kamerada Ses Akışı Bulunamadı")
                    time.sleep(5)
                    continue
                
                stream = audio_streams[0]
                
                for frame in container.decode(stream):
                    if not self._run_flag:
                        break
                        
                    now = time.time()
                    
                    # 1. Check Cooldown
                    if now < self.cooldown_until:
                        self.rms_level_signal.emit(0) # Keep UI bar at 0 during cooldown
                        continue
                        
                    # 2. Extract Audio Data
                    # PyAV frame to numpy array
                    audio_data = frame.to_ndarray()
                    
                    # LIVE PLAYBACK
                    if not self.is_muted:
                        try:
                            if self.stream_audio is None:
                                channels = len(frame.layout.channels)
                                self.stream_audio = sd.OutputStream(
                                    samplerate=frame.sample_rate,
                                    channels=channels,
                                    dtype='float32'
                                )
                                self.stream_audio.start()
                            
                            # av to_ndarray gives shape (channels, samples). sd expects (samples, channels).
                            # Normalize typical 16-bit to -1.0..1.0 for float32 playback
                            playback_data = audio_data.astype(np.float32).T / 32768.0
                            self.stream_audio.write(playback_data)
                        except Exception as e:
                            print(f"[AudioProcessor] Playback error: {e}")
                    else:
                        if self.stream_audio is not None:
                            self.stream_audio.stop()
                            self.stream_audio.close()
                            self.stream_audio = None
                    
                    # 3. Calculate RMS
                    if audio_data.size > 0:
                        # RMS = root mean square
                        # We use float32 to prevent overflow during square sum
                        data_f32 = audio_data.astype(np.float32)
                        rms = np.sqrt(np.mean(np.square(data_f32)))
                        
                        # Scale to 0-100% 
                        # Max theoretical RMS for 16-bit PCM is ~23170, but typical loud noises hit 10000-15000
                        rms_percent = min(int((rms / 12000.0) * 100), 100)
                        
                        self.rms_level_signal.emit(rms_percent)
                        
                        # 4. Analyze Moo Logic
                        packet_duration = frame.samples / frame.sample_rate # roughly 0.02 - 0.04 secs
                        
                        if rms_percent >= self.sensitivity:
                            self.high_rms_duration += packet_duration
                            self.low_rms_duration = 0.0
                        else:
                            self.low_rms_duration += packet_duration
                            
                        # If loud noise continues for >= 2.0 seconds, consider it a moo candidate
                        # We trigger it once, and then wait for an interruption
                        if self.high_rms_duration >= 2.0:
                            self.moo_detected_signal.emit()
                            self.moo_timestamps.append(now)
                            # Reset to avoid triggering 100 times per second while still loud
                            self.high_rms_duration = 0.0 
                            # We force a small gap logic by resetting, but actual logic 
                            # requires it to quiet down before registering another.
                            # So we set low_duration = 0 and will only start accumulating high again 
                            # if it stays high. A simpler way is just clearing high_duration here.
                            
                        # If quiet for >0.5s, reset the continuous high noise counter
                        if self.low_rms_duration >= 0.5:
                            self.high_rms_duration = 0.0
                            
                    # 5. Smart Alarm Logic (3 Moos in 10 Mins)
                    # Clean up old timestamps (older than 600s = 10m)
                    self.moo_timestamps = [t for t in self.moo_timestamps if (time.time() - t) <= 600]
                    
                    if len(self.moo_timestamps) >= 3:
                        self.alarm_signal.emit()
                        # Clear to prevent recursive alarms, wait for 3 NEW moos
                        self.moo_timestamps.clear()
                        # Apply default cooldown so it doesn't immediately listen to the alarm
                        self.set_cooldown(10)

            except Exception as e:
                # Connection dropped or timeout
                print(f"[AudioProcessor] Error: {e}")
                if self._run_flag:
                    time.sleep(3) # Wait before reconnect

    def stop(self):
        self._run_flag = False
        if self.stream_audio is not None:
            self.stream_audio.stop()
            self.stream_audio.close()
            self.stream_audio = None
