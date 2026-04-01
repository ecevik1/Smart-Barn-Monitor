import json
import os
import uuid
from typing import List, Dict, Optional
from src.utils.security import encode_password, decode_password

CONFIG_FILE = "config.json"

class ConfigManager:
    @staticmethod
    def load_full_config() -> Dict:
        default_config = {
            "devices": [],
            "telegram": {"bot_token": "", "chat_id": ""}
        }
        
        if not os.path.exists(CONFIG_FILE):
            return default_config
            
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # MIGRATION: Old format was a list of devices
            if isinstance(data, list):
                migrated_config = default_config.copy()
                migrated_config["devices"] = data
                data = migrated_config
                
            # Ensure keys exist
            if "devices" not in data: data["devices"] = []
            if "telegram" not in data: data["telegram"] = {"bot_token": "", "chat_id": ""}
            
            return data
        except Exception as e:
            print(f"Error loading full config: {e}")
            return default_config

    @staticmethod
    def save_full_config(data: Dict) -> bool:
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving full config: {e}")
            return False

    @staticmethod
    def load_config() -> List[Dict]:
        full_config = ConfigManager.load_full_config()
        devices = full_config["devices"]
        
        # Decode passwords before returning
        for device in devices:
            if 'password' in device:
                device['password'] = decode_password(device['password'])
        return devices

    @staticmethod
    def save_config(devices: List[Dict]) -> bool:
        full_config = ConfigManager.load_full_config()
        
        data_to_save = []
        for device in devices:
            device_copy = device.copy()
            if 'password' in device_copy:
                device_copy['password'] = encode_password(device_copy['password'])
            data_to_save.append(device_copy)
            
        full_config["devices"] = data_to_save
        return ConfigManager.save_full_config(full_config)
        
    @staticmethod
    def get_telegram_config() -> Dict:
        return ConfigManager.load_full_config()["telegram"]
        
    @staticmethod
    def save_telegram_config(bot_token: str, chat_id: str) -> bool:
        full_config = ConfigManager.load_full_config()
        full_config["telegram"]["bot_token"] = bot_token
        full_config["telegram"]["chat_id"] = chat_id
        return ConfigManager.save_full_config(full_config)

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
