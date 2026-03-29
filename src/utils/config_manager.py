import json
import os
import uuid
from typing import List, Dict, Optional
from src.utils.security import encode_password, decode_password

CONFIG_FILE = "config.json"

class ConfigManager:
    @staticmethod
    def load_config() -> List[Dict]:
        if not os.path.exists(CONFIG_FILE):
            return []
        
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Decode passwords before returning
                for device in data:
                    if 'password' in device:
                        device['password'] = decode_password(device['password'])
                return data
        except Exception as e:
            print(f"Error loading config: {e}")
            return []

    @staticmethod
    def save_config(data: List[Dict]) -> bool:
        try:
            # We must encode passwords before writing them to file
            # Make a copy to avoid altering the running state
            data_to_save = []
            for device in data:
                device_copy = device.copy()
                if 'password' in device_copy:
                    device_copy['password'] = encode_password(device_copy['password'])
                data_to_save.append(device_copy)

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    @staticmethod
    def add_device(device_info: Dict) -> bool:
        devices = ConfigManager.load_config()
        # Add a unique ID to manage devices easily
        if 'id' not in device_info:
            device_info['id'] = str(uuid.uuid4())
        
        devices.append(device_info)
        return ConfigManager.save_config(devices)

    @staticmethod
    def update_device(device_id: str, updated_info: Dict) -> bool:
        devices = ConfigManager.load_config()
        for i, device in enumerate(devices):
            if device.get('id') == device_id:
                updated_info['id'] = device_id # Ensure ID is not overwritten
                devices[i] = updated_info
                return ConfigManager.save_config(devices)
        return False

    @staticmethod
    def delete_device(device_id: str) -> bool:
        devices = ConfigManager.load_config()
        new_devices = [d for d in devices if d.get('id') != device_id]
        if len(new_devices) == len(devices):
            return False # Device not found
        return ConfigManager.save_config(new_devices)

    @staticmethod
    def get_device(device_id: str) -> Optional[Dict]:
        devices = ConfigManager.load_config()
        for device in devices:
            if device.get('id') == device_id:
                return device
        return None
