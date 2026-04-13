import datetime
import os

class Logger:
    @staticmethod
    def log(message, filename="app_events.log"):
        """Logs a message with a timestamp to the specified file."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        try:
            with open(filename, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Logging error: {e}")

    @staticmethod
    def log_sound_event(rms_level, status="Detected"):
        """Specialized logger for sound events."""
        Logger.log(f"Sound Level: {rms_level}% - {status}", "sound_events.log")
