"""
TikTok Live Liker - Chrome + Firefox + Edge
Cada navegador com método otimizado de envio de tecla
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
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# ============================================
# CONFIGURAÇÕES
# ============================================

CHROME_USER_DATA = r"C:\Users\lucas\AppData\Local\Google\Chrome\User Data"
CHROME_PROFILE = "Profile 3"

EDGE_USER_DATA = r"C:\Users\lucas\AppData\Local\Microsoft\Edge\User Data"

TEMP_PROFILES_ROOT = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "TikTokLiker",
    "BrowserProfiles",
)

CICLO_MIN = 40
CICLO_MAX = 45
PAUSA_MIN = 5
PAUSA_MAX = 10
LIKE_INTERVAL = 0.05

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def log(browser, msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{browser}] {msg}")

def kill_browsers():
    browsers = ["chrome.exe", "chromedriver.exe", "firefox.exe", "geckodriver.exe", "msedge.exe", "msedgedriver.exe"]
    for browser in browsers:
        subprocess.run(["taskkill", "/f", "/im", browser], capture_output=True, check=False)
    time.sleep(3)

def clean_temp_profiles():
    if os.path.exists(TEMP_PROFILES_ROOT):
        try:
            shutil.rmtree(TEMP_PROFILES_ROOT)
        except:
            pass
    os.makedirs(TEMP_PROFILES_ROOT, exist_ok=True)

def _cleanup_singleton_locks(user_data_dir):
    for filename in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        path = os.path.join(user_data_dir, filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except:
            pass

def is_browser_alive(driver):
    try:
        _ = driver.current_url
        return True
    except:
        return False

# ============================================
# CRIADORES DE NAVEGADORES
# ============================================

def create_chrome(live_url):
    """Chrome com perfil copiado"""
    log("Chrome", "Preparando perfil...")
    
    source_profile = os.path.join(CHROME_USER_DATA, CHROME_PROFILE)
    if not os.path.isdir(source_profile):
        log("Chrome", f"ERRO: Perfil não encontrado")
        return None
    
    target_user_data = os.path.join(TEMP_PROFILES_ROOT, "Chrome")
    os.makedirs(target_user_data, exist_ok=True)
    
    local_state = os.path.join(CHROME_USER_DATA, "Local State")
    if os.path.isfile(local_state):
        shutil.copy2(local_state, os.path.join(target_user_data, "Local State"))
    
    target_profile = os.path.join(target_user_data, CHROME_PROFILE)
    if not os.path.isdir(target_profile):
        log("Chrome", "Copiando perfil...")
        shutil.copytree(source_profile, target_profile, ignore=shutil.ignore_patterns(
            "Cache", "Code Cache", "GPUCache", "ShaderCache", "Crashpad"
        ))
    
    _cleanup_singleton_locks(target_user_data)
    
    options = ChromeOptions()
    options.add_argument(f"--user-data-dir={target_user_data}")
    options.add_argument(f"--profile-directory={CHROME_PROFILE}")
    options.add_argument("--remote-debugging-pipe")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    
    try:
        log("Chrome", "Iniciando...")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.get(live_url)
        time.sleep(5)
        log("Chrome", "OK!")
        return driver
    except Exception as e:
        log("Chrome", f"ERRO: {str(e)[:80]}")
        return None


def create_firefox(live_url):
    """Firefox limpo"""
    log("Firefox", "Iniciando...")
    
    options = FirefoxOptions()
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    
    try:
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        driver.get(live_url)
        time.sleep(5)
        log("Firefox", "OK!")
        return driver
    except Exception as e:
        log("Firefox", f"ERRO: {str(e)[:80]}")
        return None


def create_edge(live_url):
    """Edge limpo com configuração robusta"""
    log("Edge", "Iniciando...")
    
    edge_data = os.path.join(TEMP_PROFILES_ROOT, "Edge")
    os.makedirs(edge_data, exist_ok=True)
    
    options = EdgeOptions()
    options.add_argument(f"--user-data-dir={edge_data}")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    
    try:
        log("Edge", "Baixando driver...")
        driver_path = EdgeChromiumDriverManager().install()
        log("Edge", "Criando navegador...")
        service = EdgeService(driver_path)
        driver = webdriver.Edge(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        log("Edge", "Acessando URL...")
        driver.get(live_url)
        time.sleep(5)
        log("Edge", "OK!")
        return driver
    except Exception as e:
        log("Edge", f"ERRO: {str(e)[:100]}")
        return None

# ============================================
# CLASSE DO LIKER
# ============================================

class BrowserLiker:
    def __init__(self, name, driver):
        self.name = name
        self.driver = driver
        self.likes = 0
        self.running = True
        self.is_firefox = "firefox" in name.lower()

    def focus_on_page(self):
        """Tira foco da barra de endereço"""
        if not is_browser_alive(self.driver):
            return False
        try:
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.1)
            ActionChains(self.driver).send_keys(Keys.F6).perform()
            time.sleep(0.1)
            for _ in range(3):
                ActionChains(self.driver).send_keys(Keys.TAB).perform()
                time.sleep(0.05)
            self.driver.execute_script("document.body.focus();")
            return True
        except:
            return False

    def send_L_actionchains(self):
        """Método padrão - ActionChains"""
        try:
            ActionChains(self.driver).send_keys('l').perform()
            return True
        except:
            return False

    def send_L_javascript(self):
        """Método alternativo - JavaScript (melhor pra Firefox)"""
        try:
            self.driver.execute_script("""
                var event = new KeyboardEvent('keydown', {
                    key: 'l',
                    code: 'KeyL',
                    keyCode: 76,
                    which: 76,
                    bubbles: true,
                    cancelable: true
                });
                document.dispatchEvent(event);
                document.body.dispatchEvent(event);
                
                var active = document.activeElement;
                if (active) {
                    active.dispatchEvent(event);
                }
                
                // Também tenta keypress e keyup
                var press = new KeyboardEvent('keypress', {
                    key: 'l',
                    code: 'KeyL',
                    keyCode: 76,
                    which: 76,
                    bubbles: true
                });
                document.dispatchEvent(press);
                
                var up = new KeyboardEvent('keyup', {
                    key: 'l',
                    code: 'KeyL',
                    keyCode: 76,
                    which: 76,
                    bubbles: true
                });
                document.dispatchEvent(up);
            """)
            return True
        except:
            return False

    def send_L(self):
        """Envia tecla L usando método apropriado"""
        if not is_browser_alive(self.driver):
            return False
        
        success = False
        
        # Firefox usa JavaScript, outros usam ActionChains
        if self.is_firefox:
            success = self.send_L_javascript() or self.send_L_actionchains()
        else:
            success = self.send_L_actionchains()
        
        if success:
            self.likes += 1
        return success

    def run_cycle(self, duration_minutes):
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        cycle_start = self.likes
        
        log(self.name, f"Ciclo de {duration_minutes} min")
        
        self.focus_on_page()
        time.sleep(0.5)
        
        last_focus = datetime.now()
        
        while datetime.now() < end_time and self.running:
            if not is_browser_alive(self.driver):
                log(self.name, "Navegador fechou!")
                return False
            
            self.send_L()
            
            # Re-foca a cada 60 segundos
            if (datetime.now() - last_focus).seconds >= 60:
                self.focus_on_page()
                last_focus = datetime.now()
            
            if self.likes % 500 == 0 and self.likes > 0:
                log(self.name, f"{self.likes} likes")
            
            time.sleep(LIKE_INTERVAL)
        
        cycle_likes = self.likes - cycle_start
        log(self.name, f"Fim ciclo: +{cycle_likes} (total: {self.likes})")
        return True

    def run(self):
        log(self.name, "Thread iniciada")
        try:
            while self.running:
                cycle_min = random.randint(CICLO_MIN, CICLO_MAX)
                
                if not self.run_cycle(cycle_min):
                    break
                
                if not self.running:
                    break
                
                pause_sec = random.randint(PAUSA_MIN, PAUSA_MAX)
                log(self.name, f"Pausa {pause_sec}s")
                
                for _ in range(pause_sec):
                    if not self.running:
                        break
                    time.sleep(1)
        except Exception as e:
            log(self.name, f"Erro: {e}")

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
    print("   TikTok Liker - Chrome + Firefox + Edge")
    print("="*50 + "\n")
    
    print("Fechando navegadores...")
    kill_browsers()
    print("OK!\n")
    
    print("Limpando perfis temporários...")
    clean_temp_profiles()
    print("OK!\n")
    
    live_url = input("Link da live: ").strip()
    if not live_url:
        print("Link inválido!")
        return
    
    print(f"\nLink: {live_url}\n")
    
    drivers = {}
    
    print("--- Abrindo navegadores ---\n")
    
    # Chrome
    drivers["Chrome"] = create_chrome(live_url)
    time.sleep(2)
    
    # Firefox
    drivers["Firefox"] = create_firefox(live_url)
    time.sleep(2)
    
    # Edge
    drivers["Edge"] = create_edge(live_url)
    
    # Status
    print("\n" + "="*50)
    print("   STATUS")
    print("="*50)
    for name, driver in drivers.items():
        status = "✓ OK" if driver else "✗ Falhou"
        print(f"   {name}: {status}")
    print("="*50 + "\n")
    
    # Conta quantos abriram
    navegadores_ok = sum(1 for d in drivers.values() if d)
    if navegadores_ok == 0:
        print("Nenhum navegador abriu!")
        return
    
    print(f"{navegadores_ok} navegador(es) aberto(s).\n")
    print("FAÇA O LOGIN NOS NAVEGADORES QUE PRECISAM:")
    print("- Firefox: logue no TikTok e navegue até a live")
    print("- Edge: logue no TikTok e navegue até a live")
    print("- Chrome: já deve estar logado")
    print()
    print("NÃO FECHE NENHUM NAVEGADOR!")
    print()
    input("Pressione ENTER quando TODOS estiverem na live...")
    print()
    
    # Verifica quais ainda estão vivos
    likers = []
    for name, driver in drivers.items():
        if driver and is_browser_alive(driver):
            likers.append(BrowserLiker(name, driver))
        elif driver:
            log(name, "Foi fechado durante a espera")
    
    if not likers:
        print("Nenhum navegador disponível!")
        return
    
    # Foca
    print("Ajustando foco...")
    for liker in likers:
        liker.focus_on_page()
    print("OK!\n")
    
    print("="*50)
    print(f"   RODANDO {len(likers)} NAVEGADOR(ES) - Ctrl+C pra parar")
    print("="*50 + "\n")
    
    threads = []
    for liker in likers:
        t = threading.Thread(target=liker.run, daemon=True)
        t.start()
        threads.append(t)
    
    print(f"{len(threads)} thread(s) rodando\n")
    
    try:
        while True:
            time.sleep(1)
            if not any(t.is_alive() for t in threads):
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