"""
TikTok Live Liker
- 3 perfis em PARALELO
- Pausas curtas (segundos)
- Limpa cache de perfis antes de rodar
"""

import time
import random
import subprocess
import sys
import os
import shutil
import threading
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
    "TikTok2": "Profile 4",
    "TikTok3": "Profile 5"
}

SELENIUM_PROFILE_ROOT = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.dirname(os.path.abspath(__file__))),
    "TikTokLiker",
    "ChromeProfiles",
)

# Tempo de ciclo em MINUTOS
CICLO_MIN = 40
CICLO_MAX = 45

# Pausa entre ciclos em SEGUNDOS (curta)
PAUSA_MIN = 5
PAUSA_MAX = 10

# Intervalo entre cada L (quanto menor, mais rápido)
LIKE_INTERVAL = 0.05

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

def clean_profile_cache():
    """Limpa toda a pasta de perfis copiados pra forçar cópia fresh"""
    if os.path.exists(SELENIUM_PROFILE_ROOT):
        print(f"Limpando cache de perfis: {SELENIUM_PROFILE_ROOT}")
        try:
            shutil.rmtree(SELENIUM_PROFILE_ROOT)
            print("Cache limpo!")
        except Exception as e:
            print(f"Erro ao limpar cache: {e}")
    os.makedirs(SELENIUM_PROFILE_ROOT, exist_ok=True)

def _cleanup_singleton_locks(user_data_dir):
    for filename in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        path = os.path.join(user_data_dir, filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except:
            pass

def _ensure_selenium_profile(profile_name, source_profile_dir):
    source_user_data = os.path.normpath(CHROME_USER_DATA)
    source_profile_path = os.path.join(source_user_data, source_profile_dir)
    
    log(profile_name, f"Verificando perfil: {source_profile_path}")
    
    if not os.path.isdir(source_profile_path):
        raise FileNotFoundError(f"Perfil não encontrado: {source_profile_path}")

    target_user_data = os.path.join(SELENIUM_PROFILE_ROOT, profile_name)
    os.makedirs(target_user_data, exist_ok=True)

    source_local_state = os.path.join(source_user_data, "Local State")
    target_local_state = os.path.join(target_user_data, "Local State")
    if os.path.isfile(source_local_state):
        shutil.copy2(source_local_state, target_local_state)

    target_profile_path = os.path.join(target_user_data, source_profile_dir)
    if not os.path.isdir(target_profile_path):
        log(profile_name, f"Copiando perfil...")
        ignore_names = shutil.ignore_patterns(
            "Cache", "Code Cache", "GPUCache", "GrShaderCache",
            "ShaderCache", "Crashpad", "optimization_guide_model_cache",
        )
        shutil.copytree(source_profile_path, target_profile_path, ignore=ignore_names)

    _cleanup_singleton_locks(target_user_data)
    log(profile_name, f"Perfil OK!")
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
        self.likes = 0
        self.running = True

    def start_browser(self):
        log(self.name, "Iniciando navegador...")
        
        options = Options()

        try:
            user_data_dir = _ensure_selenium_profile(self.name, self.profile_dir)
        except Exception as e:
            log(self.name, f"ERRO perfil: {str(e)}")
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
            
            log(self.name, "Criando instância Chrome...")
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            log(self.name, "Navegador OK!")
            return True
            
        except Exception as e:
            log(self.name, f"ERRO ao criar navegador: {str(e)}")
            return False

    def go_to_live(self):
        log(self.name, "Acessando live...")
        try:
            self.driver.get(self.live_url)
            time.sleep(5)
            log(self.name, f"Live carregada: {self.driver.title[:40]}...")
            return True
        except Exception as e:
            log(self.name, f"ERRO ao acessar live: {str(e)[:80]}")
            return False

    def focus_on_page(self):
        """Tira foco da barra de endereço"""
        try:
            self.driver.execute_script("document.body.focus();")
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(0.1)
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.F6).perform()
            return True
        except:
            return False

    def send_L(self):
        """Envia uma tecla L"""
        try:
            ActionChains(self.driver).send_keys('l').perform()
            self.likes += 1
            return True
        except:
            return False

    def run_cycle(self, duration_minutes):
        """Ciclo de likes - loop rápido de L"""
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        cycle_start = self.likes
        
        log(self.name, f"Ciclo de {duration_minutes} min iniciado")
        
        self.focus_on_page()
        time.sleep(0.5)
        
        while datetime.now() < end_time and self.running:
            if not is_browser_alive(self.driver):
                log(self.name, "Navegador fechou!")
                return False
            
            self.send_L()
            
            # Log a cada 500 likes
            if self.likes % 500 == 0:
                log(self.name, f"{self.likes} likes")
            
            time.sleep(LIKE_INTERVAL)
        
        cycle_likes = self.likes - cycle_start
        log(self.name, f"Fim ciclo: +{cycle_likes} (total: {self.likes})")
        return True

    def run(self):
        """Loop principal - roda em thread separada"""
        log(self.name, "Thread iniciada")
        try:
            while self.running:
                cycle_min = random.randint(CICLO_MIN, CICLO_MAX)
                
                if not self.run_cycle(cycle_min):
                    break
                
                if not self.running:
                    break
                
                # Pausa CURTA em segundos
                pause_sec = random.randint(PAUSA_MIN, PAUSA_MAX)
                log(self.name, f"Pausa de {pause_sec} seg")
                
                for _ in range(pause_sec):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except Exception as e:
            log(self.name, f"Erro na thread: {e}")

    def stop(self):
        self.running = False

    def close(self):
        self.running = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        log(self.name, f"Total: {self.likes} likes")


# ============================================
# MAIN
# ============================================

def main():
    print("\n" + "="*50)
    print("   TikTok Liker - 3 PERFIS")
    print("="*50 + "\n")
    
    print("Fechando Chrome...")
    kill_chrome()
    print("OK!\n")
    
    # LIMPA CACHE DE PERFIS
    clean_profile_cache()
    print()
    
    live_url = input("Link da live: ").strip()
    if not live_url:
        print("Link inválido!")
        return
    
    print(f"\nLink: {live_url}")
    print(f"Perfis configurados: {list(PROFILES.keys())} -> {list(PROFILES.values())}")
    print(f"Intervalo: {LIKE_INTERVAL}s (~{int(1/LIKE_INTERVAL)} L/seg)")
    print(f"Pausa entre ciclos: {PAUSA_MIN}-{PAUSA_MAX} segundos\n")
    time.sleep(2)
    
    likers = []
    threads = []
    driver_path = ChromeDriverManager().install()
    
    print(f"\n--- Iniciando {len(PROFILES)} navegadores ---\n")
    
    for name, profile in PROFILES.items():
        print(f">>> Processando {name} ({profile})...")
        
        liker = TikTokLiker(name, profile, live_url, driver_path)
        
        if liker.start_browser():
            if liker.go_to_live():
                likers.append(liker)
                print(f">>> {name} OK!\n")
            else:
                print(f">>> {name} falhou ao acessar live\n")
                liker.close()
        else:
            print(f">>> {name} falhou ao iniciar navegador\n")
        
        time.sleep(3)
    
    print(f"\n--- {len(likers)} de {len(PROFILES)} navegador(es) iniciados ---\n")
    
    if not likers:
        print("Nenhum navegador iniciou!")
        return
    
    # Foca na página de cada um
    for liker in likers:
        liker.focus_on_page()
    
    print("="*50)
    print(f"   RODANDO {len(likers)} PERFIS - Ctrl+C pra parar")
    print("="*50 + "\n")
    
    time.sleep(2)
    
    # Inicia cada liker em thread separada
    for liker in likers:
        log(liker.name, "Criando thread...")
        t = threading.Thread(target=liker.run, daemon=True)
        t.start()
        threads.append(t)
        log(liker.name, "Thread criada e iniciada")
    
    print(f"\n{len(threads)} threads rodando\n")
    
    try:
        while True:
            time.sleep(1)
            alive = [t.is_alive() for t in threads]
            if not any(alive):
                break
                
    except KeyboardInterrupt:
        print("\n\nParando...")
    
    for liker in likers:
        liker.stop()
    
    time.sleep(2)
    
    for liker in likers:
        liker.close()
    
    print("\nFim!")


if __name__ == "__main__":
    main()