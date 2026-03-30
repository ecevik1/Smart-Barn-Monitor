import time
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool

class PTZWorker(QRunnable):
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            self.func(*self.args, **self.kwargs)
        except Exception as e:
            print(f"[PTZ Worker] Error in {self.func.__name__}: {e}")

class PTZManager(QObject):
    connection_status_signal = pyqtSignal(bool, str) # success, message text
    
    def __init__(self, ip, port, user, password):
        super().__init__()
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        
        self.cam = None
        self.ptz = None
        self.media = None
        self.profile_token = None
        
        self.thread_pool = QThreadPool.globalInstance()
        
    def connect_async(self):
        worker = PTZWorker(self._connect)
        self.thread_pool.start(worker)

    def _connect(self):
        try:
            from onvif import ONVIFCamera
            # Using defaults for wsdl directory resolution handled by onvif-zeep
            self.cam = ONVIFCamera(self.ip, self.port, self.user, self.password)
            self.media = self.cam.create_media_service()
            
            # Check if PTZ is supported
            try:
                self.ptz = self.cam.create_ptz_service()
            except Exception as e:
                self.connection_status_signal.emit(False, "PTZ Desteği Yok")
                return

            profiles = self.media.GetProfiles()
            if not profiles:
                self.connection_status_signal.emit(False, "Profil Bulunamadı")
                return

            self.profile_token = profiles[0].token
            self.connection_status_signal.emit(True, "Bağlı")
        except Exception as e:
            print(f"[ONVIF Connection Error] {e}")
            error_str = str(e)
            if "urllib3.connection" in error_str.lower() or "timeout" in error_str.lower() or "refused" in error_str.lower():
                self.connection_status_signal.emit(False, "ONVIF Port/IP Hatası")
            elif "401" in error_str:
                self.connection_status_signal.emit(False, "ONVIF Şifre Hatası")
            else:
                self.connection_status_signal.emit(False, "ONVIF Desteklemiyor")

    def continuous_move(self, pan, tilt, zoom):
        worker = PTZWorker(self._do_continuous_move, pan, tilt, zoom)
        self.thread_pool.start(worker)

    def _do_continuous_move(self, pan, tilt, zoom):
        if not self.ptz or not self.profile_token:
            return
            
        try:
            # Ensure both PanTilt and Zoom vectors exist for strict WSDL schemas
            velocity = {
                'PanTilt': {'x': pan, 'y': tilt},
                'Zoom': {'x': zoom}
            }
                
            request = {
                'ProfileToken': self.profile_token,
                'Velocity': velocity
            }
            self.ptz.ContinuousMove(request)
        except Exception as e:
            print(f"[PTZ] Move Error: {e}")

    def stop(self):
        worker = PTZWorker(self._do_stop)
        self.thread_pool.start(worker)

    def _do_stop(self):
        if not self.ptz or not self.profile_token:
            return
        # Standard stop for PanTilt and Zoom separately to avoid rejecting the whole command if Zoom is unsupported
        try:
            self.ptz.Stop({'ProfileToken': self.profile_token, 'PanTilt': True})
        except Exception as e:
            print(f"[PTZ] Stop Error (PanTilt): {e}")
            
        try:
            self.ptz.Stop({'ProfileToken': self.profile_token, 'Zoom': True})
        except Exception:
            pass

        # Ultimate Fallback: send ContinuousMove with zero velocity (for cheap cameras that don't implement Stop)
        try:
            self.ptz.ContinuousMove({
                'ProfileToken': self.profile_token,
                'Velocity': {'PanTilt': {'x': 0.0, 'y': 0.0}, 'Zoom': {'x': 0.0}}
            })
        except Exception:
            pass
        
    # Presets logic
    def goto_preset(self, preset_idx):
        worker = PTZWorker(self._do_goto_preset, preset_idx)
        self.thread_pool.start(worker)

    def _do_goto_preset(self, preset_idx):
        if not self.ptz or not self.profile_token: return
        try:
            preset_name = f"P{preset_idx}"
            presets = self.ptz.GetPresets({'ProfileToken': self.profile_token})
            
            target_token = None
            if presets:
                for p in presets:
                    # Match by Name 'P1', 'P2' etc or raw string '1', '2'
                    if p.Name == preset_name or p.Name == str(preset_idx) or p.token == str(preset_idx):
                        target_token = p.token
                        break

            if target_token:
                self.ptz.GotoPreset({'ProfileToken': self.profile_token, 'PresetToken': target_token})
            else:
                print(f"[PTZ] Preset {preset_name} bulunamadı.")
        except Exception as e:
            print(f"[PTZ] GotoPreset Error: {e}")
        
    def set_preset(self, preset_name, preset_idx):
        worker = PTZWorker(self._do_set_preset, preset_name)
        self.thread_pool.start(worker)

    def _do_set_preset(self, preset_name):
        if not self.ptz or not self.profile_token: return
        try:
            # To avoid "ter:NoToken", we only pass the PresetName. 
            # The camera will automatically generate a valid token.
            self.ptz.SetPreset({'ProfileToken': self.profile_token, 'PresetName': preset_name})
        except Exception as e:
            print(f"[PTZ] SetPreset Error: {e}")
