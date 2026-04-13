import os
import json
import sys
from google import genai

# Enable UTF-8 for Windows Console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode('ascii'))

def list_available_models(client):
    """Debug function to see what models this API key can access."""
    try:
        safe_print("\n--- Erişilebilir Modeller ---")
        for m in client.models.list():
            # The attribute is usually 'supported_generation_methods' or similar, 
            # but let's just print the name to be safe and robust.
            safe_print(f" - {m.name}")
        safe_print("---------------------------\n")
    except Exception as e:
        safe_print(f"Modeller listelenemedi: {e}")

def test_gemini_console():
    config_path = "config.json"
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except:
            pass

    g_conf = config.get("gemini", {})
    api_key = g_conf.get("api_key")
    
    if not api_key:
        api_key = input("Lütfen Gemini API Key giriniz: ").strip()
        if not api_key:
            safe_print("HATA: API Key gerekli.")
            return

    try:
        client = genai.Client(api_key=api_key)
        
        # DEBUG: List models to help user pick the right one
        list_available_models(client)

        # Common model names to try if listing is too long or fails
        suggested_models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-2.0-flash-exp"
        ]
        
        selected_model = input(f"Kullanılacak model ismini yazın (Örn: {suggested_models[0]}): ").strip()
        if not selected_model:
            selected_model = suggested_models[0]

        safe_print(f"\n--- Gemini Test Paneli ({selected_model}) ---")
        safe_print("Çıkmak için 'exit' yazın.\n")

        while True:
            prompt = input("Siz: ").strip()
            if not prompt: continue
            if prompt.lower() in ["exit", "quit", "cikis"]: break
                
            try:
                safe_print(f"Gemini {selected_model} düşünüyor...")
                
                # Exponential Backoff Retry Loop
                max_retries = 3
                response = None
                for attempt in range(max_retries):
                    try:
                        # Ensure we use the full 'models/' prefix if user didn't provide it
                        model_name = selected_model if selected_model.startswith("models/") else f"models/{selected_model}"
                        
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt
                        )
                        break
                    except Exception as e:
                        err_msg = str(e)
                        if "503" in err_msg and attempt < max_retries - 1:
                            import time
                            wait_time = (2 ** attempt)
                            safe_print(f"  > Meşgul (503)... {wait_time}s sonra tekrar deneniyor.")
                            time.sleep(wait_time)
                        else:
                            raise e

                if response and response.text:
                    safe_print(f"\nGemini: {response.text}\n")
            except Exception as e:
                safe_print(f"\nAPI Hatası: {str(e)}\n")
                
    except Exception as e:
        safe_print(f"Bağlantı Hatası: {str(e)}")

if __name__ == "__main__":
    test_gemini_console()
