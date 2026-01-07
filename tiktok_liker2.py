"""
TikTok Live Liker
- Tira foco da barra de endereço
- Segura tecla L continuamente
"""

import time
import random
import subprocess
import sys
import os
import shutil
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# ============================================
# CONFIGURAÇÕES
# ============================================

CHROME_USER_DATA = r"C:\Users\lucas\AppData\Local\Google\Chrome\User Data"

PROFILES = {
    "TikTok1": "Profile 3",
    "TikTok2": "Profile 4"
}

SELENIUM_PROFILE_ROOT = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.dirname(os.path.abspath(__file__))),
    "TikTokLiker",
    "ChromeProfiles",
)

CICLO_MIN = 40
CICLO_MAX = 45
PAUSA_MIN = 5
PAUSA_MAX = 10

# Tempo que fica "segurando" a tecla L (em segundos)
HOLD_DURATION = 30

# Intervalo entre "seguradas" (em segundos)  
HOLD_INTERVAL = 2

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def log(profile, msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{profile}] {msg}")

def _is_process_running(image_name):
    try:
        result = subprocess.run(
            ["tasklist", "/fi", f"imagename eq {image_name}"],
            capture_output=True, text=True, check=False,
        )
        output = (result.stdout or "") + (result.stderr or "")
        return image_name.lower() in output.lower()
    except:
        return False

def _wait_process_exit(image_name, timeout_seconds=30):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if not _is_process_running(image_name):
            return True
        time.sleep(0.5)
    return not _is_process_running(image_name)

def kill_chrome():
    subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True, check=False)
    subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], capture_output=True, check=False)
    _wait_process_exit("chrome.exe", timeout_seconds=20)
    _wait_process_exit("chromedriver.exe", timeout_seconds=20)

def _cleanup_singleton_locks(user_data_dir):
    for filename in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        path = os.path.join(user_data_dir, filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except:
            pass

def _ensure_selenium_profile(profile_name, source_profile_dir):
    """Cria user-data-dir isolado por perfil para múltiplos Chromes simultâneos"""
    source_user_data = os.path.normpath(CHROME_USER_DATA)
    source_profile_path = os.path.join(source_user_data, source_profile_dir)
    
    if not os.path.isdir(source_profile_path):
        raise FileNotFoundError(f"Perfil não encontrado: {source_profile_path}")

    target_user_data = os.path.join(SELENIUM_PROFILE_ROOT, profile_name)
    os.makedirs(target_user_data, exist_ok=True)

    # Copia Local State
    source_local_state = os.path.join(source_user_data, "Local State")
    target_local_state = os.path.join(target_user_data, "Local State")
    if os.path.isfile(source_local_state) and not os.path.isfile(target_local_state):
        shutil.copy2(source_local_state, target_local_state)

    # Copia perfil
    target_profile_path = os.path.join(target_user_data, source_profile_dir)
    if not os.path.isdir(target_profile_path):
        ignore_names = shutil.ignore_patterns(
            "Cache", "Code Cache", "GPUCache", "GrShaderCache",
            "ShaderCache", "Crashpad", "optimization_guide_model_cache",
        )
        shutil.copytree(source_profile_path, target_profile_path, ignore=ignore_names)

    _cleanup_singleton_locks(target_user_data)
    return target_user_data

def is_browser_alive(driver):
    try:
        _ = driver.current_url
        return True
    except:
        return False

# ============================================
# CLASSE PRINCIPAL
# ============================================

class TikTokLiker:
    def __init__(self, name, profile_dir, live_url, driver_path):
        self.name = name
        self.profile_dir = profile_dir
        self.live_url = live_url
        self.driver_path = driver_path
        self.driver = None
        self.hold_count = 0

    def start_browser(self):
        log(self.name, "Iniciando navegador...")
        
        options = Options()

        try:
            user_data_dir = _ensure_selenium_profile(self.name, self.profile_dir)
        except Exception as e:
            log(self.name, f"ERRO perfil: {str(e)[:100]}")
            return False
        
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument(f"--profile-directory={self.profile_dir}")
        options.add_argument("--remote-debugging-pipe")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        
        options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        try:
            service = Service(self.driver_path)
            service.log_path = "NUL"
            
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            log(self.name, "Navegador OK!")
            return True
            
        except Exception as e:
            log(self.name, f"ERRO: {str(e)[:100]}")
            return False

    def go_to_live(self):
        log(self.name, "Acessando live...")
        try:
            self.driver.get(self.live_url)
            time.sleep(5)
            log(self.name, f"Live carregada: {self.driver.title[:40]}...")
            return True
        except Exception as e:
            log(self.name, f"ERRO: {str(e)[:80]}")
            return False

    def focus_on_page(self):
        """Tira foco da barra de endereço e coloca na página"""
        try:
            # Método 1: JavaScript pra focar no body
            self.driver.execute_script("document.body.focus();")
            
            # Método 2: Pressiona ESC pra sair da barra de endereço, depois TAB pra ir pro conteúdo
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.ESCAPE)
            actions.perform()
            time.sleep(0.1)
            
            # F6 alterna entre barra de endereço e página
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.F6)
            actions.perform()
            time.sleep(0.1)
            
            log(self.name, "Foco na página")
            return True
        except Exception as e:
            log(self.name, f"Erro foco: {e}")
            return False

    def hold_key_L(self, duration_seconds):
        """Segura a tecla L por X segundos"""
        try:
            actions = ActionChains(self.driver)
            
            # Pressiona L (segura)
            actions.key_down('l')
            actions.perform()
            
            # Mantém pressionado
            time.sleep(duration_seconds)
            
            # Solta L
            actions = ActionChains(self.driver)
            actions.key_up('l')
            actions.perform()
            
            self.hold_count += 1
            return True
        except:
            return False

    def run_cycle(self, duration_minutes):
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        log(self.name, f"Ciclo de {duration_minutes} min (segurando L por {HOLD_DURATION}s cada vez)")
        
        # Garante foco na página antes de começar
        self.focus_on_page()
        time.sleep(1)
        
        while datetime.now() < end_time:
            if not is_browser_alive(self.driver):
                log(self.name, "Navegador fechou!")
                return False
            
            # Segura L
            self.hold_key_L(HOLD_DURATION)
            
            log(self.name, f"Hold #{self.hold_count} concluído")
            
            # Pequeno intervalo entre seguradas
            time.sleep(HOLD_INTERVAL)
            
            # Re-foca na página (caso tenha perdido foco)
            self.focus_on_page()
        
        log(self.name, f"Fim ciclo: {self.hold_count} holds")
        return True

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        log(self.name, f"Total: {self.hold_count} holds")


# ============================================
# MAIN
# ============================================

def main():
    print("\n" + "="*50)
    print("   TikTok Liker - Modo HOLD")
    print("="*50 + "\n")
    
    print("Fechando Chrome...")
    kill_chrome()
    print("OK!\n")
    
    live_url = input("Link da live: ").strip()
    if not live_url:
        print("Link inválido!")
        return
    
    print(f"\nLink: {live_url}")
    print(f"Perfis: {list(PROFILES.keys())}\n")
    time.sleep(2)
    
    likers = []
    driver_path = ChromeDriverManager().install()
    
    for name, profile in PROFILES.items():
        liker = TikTokLiker(name, profile, live_url, driver_path)
        
        if liker.start_browser():
            if liker.go_to_live():
                likers.append(liker)
            else:
                liker.close()
        
        time.sleep(3)
    
    if not likers:
        print("\nNenhum navegador iniciou!")
        return
    
    print(f"\n{len(likers)} navegador(es) OK")
    
    # Foca na página de cada um
    for liker in likers:
        liker.focus_on_page()
    
    print("\n" + "="*50)
    print("   RODANDO - Ctrl+C pra parar")
    print(f"   Segurando L por {HOLD_DURATION}s, pausa de {HOLD_INTERVAL}s")
    print("="*50 + "\n")
    
    time.sleep(3)
    
    try:
        while True:
            cycle_min = random.randint(CICLO_MIN, CICLO_MAX)
            
            active = []
            for liker in likers:
                if is_browser_alive(liker.driver):
                    liker.run_cycle(cycle_min)
                    active.append(liker)
            
            if not active:
                print("\nNavegadores fecharam!")
                break
            
            likers = active
            
            pause_min = random.randint(PAUSA_MIN, PAUSA_MAX)
            log("GERAL", f"Pausa de {pause_min} min")
            time.sleep(pause_min * 60)
                
    except KeyboardInterrupt:
        print("\n\nParando...")
    
    for liker in likers:
        liker.close()
    
    print("\nFim!")


if __name__ == "__main__":
    main()