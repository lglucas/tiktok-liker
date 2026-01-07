"""
TikTok Live Liker v4 (Perfis anonimizados)
- 3 Chromes em paralelo
- Cada Chrome usa um user-data-dir separado (sem copiar do seu Chrome principal)
- Envia likes via tecla 'L' usando Selenium (não usa seu teclado real)
"""

import os
import random
import shutil
import subprocess
import threading
import time
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# ============================================
# CONFIGURAÇÕES
# ============================================

PROFILES = {
    "TikTok1": "Default",
    "TikTok2": "Default",
    "TikTok3": "Default",
}

ANON_PROFILE_ROOT = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.dirname(os.path.abspath(__file__))),
    "TikTokLiker",
    "AnonChromeProfiles",
)

# Tempo de ciclo em MINUTOS
CICLO_MIN = 40
CICLO_MAX = 45

# Pausa entre ciclos em SEGUNDOS (curta)
PAUSA_MIN = 5
PAUSA_MAX = 10

# Intervalo entre cada L (quanto menor, mais rápido)
LIKE_INTERVAL = 0.05

# Se True: apaga perfis anonimizados toda vez (vai precisar logar de novo)
CLEAN_ANON_CACHE_ON_START = False

# Tentativas de iniciar navegador por perfil
START_RETRIES = 3
START_RETRY_DELAY_SEC = 5


# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def log(profile, msg):
    """Log simples com timestamp."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{profile}] {msg}")


def _is_process_running(image_name):
    """Verifica se existe algum processo rodando com esse nome (Windows)."""
    try:
        result = subprocess.run(
            ["tasklist", "/fi", f"imagename eq {image_name}"],
            capture_output=True,
            text=True,
            check=False,
        )
        output = (result.stdout or "") + (result.stderr or "")
        return image_name.lower() in output.lower()
    except Exception:
        return False


def _wait_process_exit(image_name, timeout_seconds=30):
    """Aguarda processos encerrarem para evitar lock de perfil do Chrome."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if not _is_process_running(image_name):
            return True
        time.sleep(0.5)
    return not _is_process_running(image_name)


def kill_chrome():
    """Fecha Chrome e chromedriver para evitar locks."""
    subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True, check=False)
    subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], capture_output=True, check=False)
    _wait_process_exit("chrome.exe", timeout_seconds=20)
    _wait_process_exit("chromedriver.exe", timeout_seconds=20)


def clean_anon_profile_cache():
    """Remove a pasta de perfis anonimizados para recriar do zero."""
    if os.path.exists(ANON_PROFILE_ROOT):
        print(f"Limpando perfis anonimizados: {ANON_PROFILE_ROOT}")
        try:
            shutil.rmtree(ANON_PROFILE_ROOT)
            print("Perfis anonimizados removidos!")
        except Exception as e:
            print(f"Erro ao limpar perfis anonimizados: {e}")
    os.makedirs(ANON_PROFILE_ROOT, exist_ok=True)


def _cleanup_singleton_locks(user_data_dir):
    """Remove locks antigos do Chrome dentro do user-data-dir."""
    for filename in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        path = os.path.join(user_data_dir, filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


def ensure_anon_profile(profile_name):
    """Garante um user-data-dir isolado (anônimo) para cada perfil."""
    user_data_dir = os.path.join(ANON_PROFILE_ROOT, profile_name)
    os.makedirs(user_data_dir, exist_ok=True)
    _cleanup_singleton_locks(user_data_dir)
    return user_data_dir


def is_browser_alive(driver):
    """Verifica se o WebDriver ainda responde."""
    try:
        _ = driver.current_url
        return True
    except Exception:
        return False


# ============================================
# CLASSE PRINCIPAL
# ============================================

class TikTokLiker:
    def __init__(self, name, profile_dir, live_url, driver_path):
        """Instância de liker para um perfil."""
        self.name = name
        self.profile_dir = profile_dir
        self.live_url = live_url
        self.driver_path = driver_path
        self.driver = None
        self.likes = 0
        self.running = True

    def start_browser(self):
        """Inicia o Chrome com um perfil anônimo isolado."""
        log(self.name, "Iniciando navegador...")

        options = Options()
        user_data_dir = ensure_anon_profile(self.name)

        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument(f"--profile-directory={self.profile_dir}")
        options.add_argument("--remote-debugging-pipe")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-sync")

        options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        try:
            service = Service(self.driver_path)
            service.log_path = "NUL"

            log(self.name, f"Criando instância Chrome... user-data-dir={user_data_dir}")
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            log(self.name, "Navegador OK!")
            return True
        except Exception as e:
            log(self.name, f"ERRO ao criar navegador: {e}")
            return False

    def go_to_live(self):
        """Abre a URL da live."""
        log(self.name, "Acessando live...")
        try:
            self.driver.get(self.live_url)
            time.sleep(5)
            log(self.name, f"Live carregada: {self.driver.title[:40]}...")
            return True
        except Exception as e:
            log(self.name, f"ERRO ao acessar live: {e}")
            return False

    def focus_on_page(self):
        """Tenta garantir que o foco está na página (e não na barra de endereço)."""
        try:
            self.driver.execute_script("document.body.focus();")
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(0.1)
            return True
        except Exception:
            return False

    def send_L(self):
        """Envia uma tecla L via Selenium (não usa seu teclado real)."""
        try:
            ActionChains(self.driver).send_keys("l").perform()
            self.likes += 1
            return True
        except Exception:
            return False

    def run_cycle(self, duration_minutes):
        """Ciclo de likes - loop rápido de L."""
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

            if self.likes % 500 == 0 and self.likes > 0:
                log(self.name, f"{self.likes} likes")

            time.sleep(LIKE_INTERVAL)

        cycle_likes = self.likes - cycle_start
        log(self.name, f"Fim ciclo: +{cycle_likes} (total: {self.likes})")
        return True

    def run(self):
        """Loop principal - roda em thread separada."""
        log(self.name, "Thread iniciada")
        try:
            while self.running:
                cycle_min = random.randint(CICLO_MIN, CICLO_MAX)
                if not self.run_cycle(cycle_min):
                    break

                if not self.running:
                    break

                pause_sec = random.randint(PAUSA_MIN, PAUSA_MAX)
                log(self.name, f"Pausa de {pause_sec} seg")
                for _ in range(pause_sec):
                    if not self.running:
                        break
                    time.sleep(1)
        except Exception as e:
            log(self.name, f"Erro na thread: {e}")

    def stop(self):
        """Sinaliza para parar a thread."""
        self.running = False

    def close(self):
        """Fecha o navegador e imprime total de likes."""
        self.running = False
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
        log(self.name, f"Total: {self.likes} likes")


# ============================================
# MAIN
# ============================================

def main():
    """Entrada principal do script."""
    print("\n" + "=" * 50)
    print("   TikTok Liker v4 - 3 PERFIS ANONIMIZADOS")
    print("=" * 50 + "\n")

    print("Fechando Chrome...")
    kill_chrome()
    print("OK!\n")

    if CLEAN_ANON_CACHE_ON_START:
        clean_anon_profile_cache()
        print()
    else:
        os.makedirs(ANON_PROFILE_ROOT, exist_ok=True)

    live_url = input("Link da live: ").strip()
    if not live_url:
        print("Link inválido!")
        return

    print(f"\nLink: {live_url}")
    print(f"Perfis anonimizados: {list(PROFILES.keys())}")
    print(f"Intervalo: {LIKE_INTERVAL}s (~{int(1/LIKE_INTERVAL)} L/seg)")
    print(f"Pausa entre ciclos: {PAUSA_MIN}-{PAUSA_MAX} segundos\n")
    time.sleep(2)

    likers = []
    threads = []
    driver_path = ChromeDriverManager().install()

    print(f"\n--- Iniciando {len(PROFILES)} navegadores ---\n")

    for name, profile_dir in PROFILES.items():
        print(f">>> Processando {name} ({profile_dir})...")
        liker = TikTokLiker(name, profile_dir, live_url, driver_path)

        started = False
        for attempt in range(1, START_RETRIES + 1):
            log(name, f"Tentativa {attempt}/{START_RETRIES}")
            if liker.start_browser() and liker.go_to_live():
                likers.append(liker)
                started = True
                print(f">>> {name} OK!\n")
                break
            liker.close()
            time.sleep(START_RETRY_DELAY_SEC)

        if not started:
            print(f">>> {name} falhou ao iniciar\n")

        time.sleep(3)

    print(f"\n--- {len(likers)} de {len(PROFILES)} navegador(es) iniciados ---\n")
    if not likers:
        print("Nenhum navegador iniciou!")
        return

    for liker in likers:
        liker.focus_on_page()

    print("=" * 50)
    print(f"   RODANDO {len(likers)} PERFIS - Ctrl+C pra parar")
    print("=" * 50 + "\n")

    time.sleep(2)

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

