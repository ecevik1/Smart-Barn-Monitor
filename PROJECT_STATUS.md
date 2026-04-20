# Smart Barn Monitor — Proje Durum Belgesi

**Son Güncelleme:** 2026-04-20  
**Platform:** Windows 11 | Python 3.x | PyQt6  
**Durum:** Aktif Geliştirme

---

## Genel Bakış

Ahır güvenliği ve hayvan sağlığı izleme uygulaması. IP kamera bağlantısı, yapay zeka destekli anomali tespiti ve Telegram bildirimleri tek bir masaüstü arayüzünde birleştirilmiştir.

---

## Mimari

```
main.py
└── MainWindow (PyQt6)
    ├── DeviceCard[]          → Kayıtlı kamera listesi
    ├── VideoWidget           → Canlı yayın + ses izleme
    │   ├── VideoThread       → RTSP akışı + YOLOv8 tespiti
    │   ├── AudioProcessor    → Ses RMS analizi + böğürme tespiti
    │   └── HybridAIWorker    → Gemini analizi + Telegram bildirimi
    ├── PTZPanel              → Kamera yön/zoom kontrolü
    └── ConfigManager         → config.json okuma/yazma
```

---

## Modüller ve Sorumlulukları

| Dosya | Sorumluluk |
|---|---|
| `main.py` | Uygulama başlatma, global hata yakalama |
| `src/ui/main_window.py` | Ana pencere, cihaz yönetimi, UI düzeni |
| `src/ui/video_widget.py` | Görüntü gösterimi, ses paneli, alarm tetikleme |
| `src/ui/device_card.py` | Tek kamera kartı (bağlan / düzenle / sil) |
| `src/ui/ptz_panel.py` | Yön tuşları, zoom, preset kaydetme/yükleme |
| `src/ui/add_device_dialog.py` | Kamera ekleme / düzenleme formu |
| `src/ui/telegram_dialog.py` | Telegram bot token ve chat ID yapılandırması |
| `src/ui/gemini_dialog.py` | Gemini API anahtarı ve model seçimi |
| `src/ui/theme.py` | Koyu tema QSS stil tanımları |
| `src/utils/video_thread.py` | RTSP akışı, YOLOv8 görsel anomali tespiti |
| `src/utils/audio_processor.py` | PyAV ses akışı, RMS analizi, böğürme sayacı |
| `src/utils/hybrid_ai_worker.py` | Gemini görsel analizi + Telegram gönderimi |
| `src/utils/ptz_manager.py` | ONVIF PTZ komutları (async) |
| `src/utils/config_manager.py` | Cihaz, Telegram, Gemini yapılandırma CRUD |
| `src/utils/network.py` | TCP bağlantı testi |
| `src/utils/security.py` | Base64 şifre kodlama/çözme |
| `src/utils/logger.py` | Zaman damgalı dosya loglama |

---

## Temel Özellikler ve İşleyiş

### 1. Kamera Bağlantısı (RTSP)
- Kullanıcı IP, port, kullanıcı adı, şifre, RTSP yolu girer
- URL formatı: `rtsp://[user:pass@]ip:port/path`
- OpenCV ile akış açılır, `CAP_PROP_BUFFERSIZE=1` ile düşük gecikme sağlanır
- Bağlantı kopunca otomatik yeniden bağlanma döngüsü devreye girer

### 2. Görsel Anomali Tespiti (YOLOv8)
- YOLOv8 Nano modeli 5 FPS'de çalışır
- Kişi (sınıf 0) veya köpek (sınıf 16) tespit edilirse anomali sinyali üretilir
- CUDA varsa GPU üzerinde; yoksa CPU'da çalışır
- Tespit sonrası Gemini analizi ve Telegram bildirimi tetiklenir

### 3. Ses Anomali Tespiti (Böğürme)
- PyAV ile RTSP akışından ses çıkarılır
- RMS (Root Mean Square) ile ses şiddeti 0–100% ölçeğinde izlenir
- Hassasiyet kaydırıcısı (varsayılan: 60) eşik değerini belirler
- Bir böğürme: RMS ≥ eşik değeri, 2 saniye sürekli
- **Alarm koşulu:** 10 dakika içinde 3 böğürme → alarm tetikler
- Alarm tetiklenince: 10 saniyelik soğuma süresi başlar

### 4. Gemini AI Analizi
- Tetikleyici: görsel anomali veya ses alarmı
- **5 dakika soğuma** (istek patlamasını önler)
- Kamera karesi PIL.Image'a dönüştürülür
- Gemini modeline Türkçe prompt ile gönderilir:  
  *"Veteriner gözüyle durumu analiz et ve çok kısa bir rapor çıkar."*
- 503 hatalarında üstel geri çekilme ile yeniden deneme (5 denemeye kadar)

### 5. Telegram Bildirimi
- Bot Token ve Chat ID kullanıcı tarafından yapılandırılır
- HybridAIWorker: `sendPhoto` endpoint'i ile snapshot + Gemini analizi gönderir
- Timeout: 15 saniye
- 503 hatalarında üstel geri çekilme (1→2→4→8→16 sn)

### 6. PTZ Kamera Kontrolü
- ONVIF protokolü (`onvif-zeep`)
- Yön tuşlarında `ContinuousMove`, bırakınca `Stop`
- Pan/Tilt/Zoom değer aralığı: −1.0 ile +1.0
- 3 preset yuvası: kaydet / yükle modlu geçiş
- Bağlantı hataları UI'da durum etiketi ile gösterilir

---

## Veri Akışı (Anomali Senaryosu)

```
VideoThread (YOLOv8 @ 5 FPS)
  → anomaly_signal(cv_image)
    → VideoWidget.trigger_ai_analysis(cv_image, "Görsel Anomali")
      → HybridAIWorker (ayrı thread)
          1. BGR → RGB → PIL dönüşümü
          2. snapshot.jpg kaydet
          3. Gemini API çağrısı (image + prompt)
          4. Telegram sendPhoto (snapshot + analiz metni)

AudioProcessor (sürekli RMS ölçümü)
  → moo_detected_signal()  [tekil böğürme]
  → alarm_signal()         [3 böğürme / 10 dk]
    → VideoWidget.trigger_alarm()
        1. Uyarı etiketi yanıp söner (500 ms)
        2. Alarm sesi çalar
        3. trigger_ai_analysis() tetiklenir
```

---

## Yapılandırma Dosyası (config.json)

```json
{
  "devices": [
    {
      "id": "<UUID>",
      "name": "Ahır Kamerası 1",
      "ip": "192.168.1.x",
      "username": "admin",
      "password": "<base64>",
      "rtsp_port": 554,
      "onvif_port": 80,
      "rtsp_path": "/stream"
    }
  ],
  "telegram": {
    "bot_token": "...",
    "chat_id": "..."
  },
  "gemini": {
    "api_key": "...",
    "model": "gemini-2.5-flash"
  }
}
```

> `config.json` git'e eklenmez. `config_template.json` ile şablon sağlanır.

---

## Bağımlılıklar

| Paket | Kullanım |
|---|---|
| PyQt6 6.8.0 | UI çerçevesi |
| opencv-python ≥4.8 | RTSP akışı, kare işleme |
| ultralytics ≥8.1 | YOLOv8 hayvan/kişi tespiti |
| av ≥11.0 | RTSP ses çıkarma |
| sounddevice ≥0.4.6 | Anlık ses çalma |
| onvif-zeep ≥0.2.12 | PTZ kamera protokolü |
| google-genai ≥1.0 | Gemini AI API istemcisi |
| requests ≥2.31 | Telegram HTTP istekleri |
| numpy ≥1.26 | Dizi/matris işlemleri |

---

## Derleme

```bash
# Geliştirme
pip install -r requirements.txt
python main.py

# PyInstaller ile tek dosya EXE
python build.py
```

---

## Güvenlik Notları

- Şifreler Base64 ile kodlanır (şifreleme değil, obfüskasyon).
- `config.json` `.gitignore`'da tutulmalıdır.
- API anahtarları (Gemini, Telegram) yalnızca yerel `config.json`'da saklanır.

---

## Bilinen Kısıtlar / Geliştirme Alanları

- Görsel anomali tespiti yalnızca **insan** ve **köpek** sınıflarını tanır; inek/at gibi çiftlik hayvanları için özel model eğitimi gerekmektedir.
- Ses tespiti RMS eşiğine dayalıdır; hayvan seslerini gürültüden ayırt eden bir model eklenmesi hassasiyeti artırır.
- Şifreler Base64 ile saklanmaktadır; üretim ortamı için gerçek şifreleme (örn. `cryptography` paketi) önerilir.
- Tek kamera aynı anda aktif akış yapabilir; çoklu eşzamanlı akış desteği henüz yoktur.
