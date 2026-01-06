"""
TikTok Live Liker v5
- Baseado no tiktok_liker.py (3 perfis + threads)
- Soma total de likes (global) + total por perfil
- Opção de perfis anonimizados (sem copiar seu Chrome principal)
- Inicialização mais robusta (retries)
"""

import os
import random
import shutil
import subprocess
import threading
import time
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager


CHROME_USER_DATA = r"C:\Users\lucas\AppData\Local\Google\Chrome\User Data"

PROFILES = {
    "TikTok1": "Profile 3",
    "TikTok2": "Profile 4",
    "TikTok3": "Profile 5",
}

USE_ANON_PROFILES = False

INPUT_MODE = "cdp"

REFRESH_PROFILE_COPY_ON_START = False

FORCE_RESEED_PROFILES = set()

PROFILE_SEED_ENABLED = True
PROFILE_SEED_FORCE = False
PROFILE_SEED_MARKER_NAME = "tiktok_seed_ok.txt"

PROXY_PER_PROFILE = {
    "TikTok1": None,
    "TikTok2": None,
    "TikTok3": None,
}

USER_AGENT_PER_PROFILE = {
    "TikTok1": None,
    "TikTok2": None,
    "TikTok3": None,
}

SELENIUM_PROFILE_ROOT = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.dirname(os.path.abspath(__file__))),
    "TikTokLiker",
    "ChromeProfiles",
)

ANON_PROFILE_ROOT = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.dirname(os.path.abspath(__file__))),
    "TikTokLiker",
    "AnonChromeProfiles",
)

ANON_PROFILE_DIRECTORY = "Default"
ANON_CLEAN_CACHE_ON_START = False

CLEAN_PROFILE_CACHE_ON_START = False

CICLO_MIN = 40
CICLO_MAX = 45
PAUSA_MIN = 5
PAUSA_MAX = 10
LIKE_INTERVAL = 0.05

START_RETRIES = 3
START_RETRY_DELAY_SEC = 5

SUMMARY_EVERY_SECONDS = 15

SHOW_LOCAL_STATS = False

START_DESYNC_MAX_SEC = 2.0


def log(profile, msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{profile}] {msg}")


def _is_process_running(image_name):
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
        except Exception:
            pass


def clean_profile_cache(root_dir):
    """Apaga o diretório de perfis copiados/anonimizados e recria vazio."""
    if os.path.exists(root_dir):
        try:
            shutil.rmtree(root_dir)
        except Exception as e:
            print(f"Erro ao limpar cache: {e}")
    os.makedirs(root_dir, exist_ok=True)

def _copy_with_retries(profile_name, src, dst, attempts=3, delay_sec=0.3):
    """Copia um arquivo com tentativas (para lidar com locks/transientes no Windows)."""
    last_error = None
    for _ in range(attempts):
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            last_error = e
            time.sleep(delay_sec)
    log(profile_name, f"AVISO: falha ao copiar arquivo: {src} -> {dst} ({last_error})")
    return False


def prepare_profile(profile_name, source_profile_dir):
    user_data_dir = os.path.join(SELENIUM_PROFILE_ROOT, profile_name)
    os.makedirs(user_data_dir, exist_ok=True)
    _cleanup_singleton_locks(user_data_dir)
    return user_data_dir, "Default"


def prepare_anon_profile(profile_name):
    user_data_dir = os.path.join(ANON_PROFILE_ROOT, profile_name)
    os.makedirs(user_data_dir, exist_ok=True)
    _cleanup_singleton_locks(user_data_dir)
    return user_data_dir, ANON_PROFILE_DIRECTORY


def export_tiktok_session(driver_path, chrome_profile_dir):
    """Exporta cookies/localStorage do TikTok usando um perfil real do Chrome (sequencial)."""
    if not os.path.isdir(os.path.join(CHROME_USER_DATA, chrome_profile_dir)):
        return {"cookies": [], "local_storage": {}}

    options = Options()
    options.add_argument(f"--user-data-dir={CHROME_USER_DATA}")
    options.add_argument(f"--profile-directory={chrome_profile_dir}")
    options.add_argument("--remote-debugging-pipe")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-notifications")
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(driver_path)
    service.log_path = "NUL"

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.tiktok.com/")
        time.sleep(4)
        cookies = driver.get_cookies()
        local_storage = driver.execute_script(
            """
            const out = {};
            for (let i = 0; i < localStorage.length; i++) {
              const k = localStorage.key(i);
              out[k] = localStorage.getItem(k);
            }
            return out;
            """
        )
        return {"cookies": cookies, "local_storage": local_storage or {}}
    except Exception:
        return {"cookies": [], "local_storage": {}}
    finally:
        if driver:
            try:
                driver.quit()
            except BaseException:
                pass


def seed_tiktok_session(driver, session_data):
    """Importa cookies/localStorage do TikTok na aba atual (depois de abrir tiktok.com)."""
    cookies = session_data.get("cookies") or []
    local_storage = session_data.get("local_storage") or {}

    for cookie in cookies:
        payload = {}
        for k in ("name", "value", "domain", "path", "secure", "httpOnly", "expiry", "sameSite"):
            if k in cookie:
                payload[k] = cookie[k]
        try:
            driver.add_cookie(payload)
        except Exception:
            continue

    if local_storage:
        try:
            driver.execute_script(
                """
                const data = arguments[0] || {};
                for (const [k, v] of Object.entries(data)) {
                  try { localStorage.setItem(k, v); } catch (e) {}
                }
                """,
                local_storage,
            )
        except Exception:
            pass


def is_browser_alive(driver):
    try:
        _ = driver.current_url
        return True
    except Exception:
        return False


class LikeCounter:
    def __init__(self):
        self._lock = threading.Lock()
        self._total = 0

    def inc(self, amount=1):
        with self._lock:
            self._total += amount
            return self._total

    def get(self):
        with self._lock:
            return self._total


class TikTokLiker:
    def __init__(self, name, profile_dir, live_url, driver_path, counter, session_data=None):
        self.name = name
        self.profile_dir = profile_dir
        self.live_url = live_url
        self.driver_path = driver_path
        self.driver = None
        self.user_data_dir = None
        self.likes = 0
        self.running = True
        self.counter = counter
        self.session_data = session_data or {"cookies": [], "local_storage": {}}

    def start_browser(self):
        log(self.name, "Iniciando navegador...")
        options = Options()

        try:
            if USE_ANON_PROFILES:
                user_data_dir, profile_directory = prepare_anon_profile(self.name)
            else:
                user_data_dir, profile_directory = prepare_profile(self.name, self.profile_dir)
        except Exception as e:
            log(self.name, f"ERRO perfil: {e}")
            return False
        self.user_data_dir = user_data_dir

        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument(f"--profile-directory={profile_directory}")
        options.add_argument("--remote-debugging-pipe")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-sync")

        proxy = PROXY_PER_PROFILE.get(self.name)
        if proxy:
            options.add_argument(f"--proxy-server={proxy}")

        user_agent = USER_AGENT_PER_PROFILE.get(self.name)
        if user_agent:
            options.add_argument(f"--user-agent={user_agent}")

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
            log(self.name, f"ERRO ao criar navegador: {e}")
            return False

    def go_to_live(self):
        log(self.name, "Acessando live...")
        try:
            self.driver.get("https://www.tiktok.com/")
            time.sleep(4)

            marker_path = None
            if self.user_data_dir:
                marker_path = os.path.join(self.user_data_dir, PROFILE_SEED_MARKER_NAME)

            should_seed = PROFILE_SEED_ENABLED and (
                PROFILE_SEED_FORCE
                or (self.name in FORCE_RESEED_PROFILES)
                or (marker_path and not os.path.exists(marker_path))
            )
            if should_seed and self.session_data:
                seed_tiktok_session(self.driver, self.session_data)
                self.driver.get("https://www.tiktok.com/")
                time.sleep(3)
                if marker_path:
                    try:
                        with open(marker_path, "w", encoding="utf-8") as f:
                            f.write("ok\n")
                    except Exception:
                        pass

            self.driver.get(self.live_url)
            time.sleep(5)
            title = (self.driver.title or "")[:60]
            log(self.name, f"Página carregada: {title}...")
            if "Entrar" in (self.driver.title or ""):
                FORCE_RESEED_PROFILES.add(self.name)
                if marker_path and os.path.exists(marker_path):
                    try:
                        os.remove(marker_path)
                    except Exception:
                        pass
                log(self.name, "Detectei tela de login; vou forçar reseed na próxima tentativa.")
                return False
            return True
        except Exception as e:
            log(self.name, f"ERRO ao acessar live: {e}")
            return False

    def focus_on_page(self):
        try:
            self.driver.execute_script("document.body.focus();")
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.1)
            return True
        except Exception:
            return False

    def send_like_cdp(self):
        try:
            self.driver.execute_cdp_cmd(
                "Input.dispatchKeyEvent",
                {
                    "type": "keyDown",
                    "key": "l",
                    "code": "KeyL",
                    "text": "l",
                    "unmodifiedText": "l",
                    "windowsVirtualKeyCode": 76,
                    "nativeVirtualKeyCode": 76,
                },
            )
            self.driver.execute_cdp_cmd(
                "Input.dispatchKeyEvent",
                {
                    "type": "keyUp",
                    "key": "l",
                    "code": "KeyL",
                    "windowsVirtualKeyCode": 76,
                    "nativeVirtualKeyCode": 76,
                },
            )
            self.likes += 1
            self.counter.inc(1)
            return True
        except Exception:
            return False

    def send_L(self):
        try:
            ActionChains(self.driver).send_keys("l").perform()
            self.likes += 1
            self.counter.inc(1)
            return True
        except Exception:
            return False

    def send_like(self):
        if INPUT_MODE == "cdp":
            return self.send_like_cdp()
        return self.send_L()

    def run_cycle(self, duration_minutes):
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        cycle_start = self.likes
        log(self.name, f"Ciclo de {duration_minutes} min iniciado")

        if INPUT_MODE != "cdp":
            self.focus_on_page()
            time.sleep(0.5)

        while datetime.now() < end_time and self.running:
            if not is_browser_alive(self.driver):
                log(self.name, "Navegador fechou!")
                return False

            self.send_like()
            time.sleep(LIKE_INTERVAL)

        cycle_likes = self.likes - cycle_start
        log(self.name, f"Fim ciclo: +{cycle_likes} (total perfil: {self.likes})")
        return True

    def run(self):
        log(self.name, "Thread iniciada")
        try:
            if START_DESYNC_MAX_SEC > 0:
                time.sleep(random.uniform(0, START_DESYNC_MAX_SEC))
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
        self.running = False

    def close(self):
        self.running = False
        if self.driver:
            try:
                self.driver.quit()
            except BaseException:
                pass
        log(self.name, f"Total perfil: {self.likes} likes")


class SummaryPrinter:
    def __init__(self, likers, counter):
        self._likers = likers
        self._counter = counter
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        while not self._stop.is_set():
            time.sleep(SUMMARY_EVERY_SECONDS)
            total = self._counter.get()
            per_profile = ", ".join([f"{l.name}={l.likes}" for l in self._likers])
            log("GERAL", f"Total (soma): {total} | Por perfil: {per_profile}")


def main():
    print("\n" + "=" * 50)
    print("   TikTok Liker v5 - 3 PERFIS")
    print("=" * 50 + "\n")

    print("Fechando Chrome...")
    kill_chrome()
    print("OK!\n")

    if USE_ANON_PROFILES:
        if ANON_CLEAN_CACHE_ON_START:
            print(f"Limpando cache anon: {ANON_PROFILE_ROOT}")
            clean_profile_cache(ANON_PROFILE_ROOT)
        else:
            os.makedirs(ANON_PROFILE_ROOT, exist_ok=True)
    else:
        if CLEAN_PROFILE_CACHE_ON_START:
            print(f"Limpando cache de perfis: {SELENIUM_PROFILE_ROOT}")
            clean_profile_cache(SELENIUM_PROFILE_ROOT)
        else:
            os.makedirs(SELENIUM_PROFILE_ROOT, exist_ok=True)
    print("")

    live_url = input("Link da live: ").strip()
    if not live_url:
        print("Link inválido!")
        return

    print(f"\nLink: {live_url}")
    print(f"Perfis: {list(PROFILES.keys())} -> {list(PROFILES.values())}")
    print(f"Anon: {USE_ANON_PROFILES}")
    print(f"Modo input: {INPUT_MODE}")
    print(f"Intervalo: {LIKE_INTERVAL}s (~{int(1/LIKE_INTERVAL)} L/seg por perfil)")
    print(f"Pausa entre ciclos: {PAUSA_MIN}-{PAUSA_MAX} segundos\n")
    time.sleep(2)

    driver_path = ChromeDriverManager().install()
    counter = LikeCounter()

    likers = []
    threads = []

    sessions = {}
    if PROFILE_SEED_ENABLED:
        print("\n--- Preparando sessões (cookies/localStorage) a partir dos perfis do Chrome ---\n")
        for name, profile in PROFILES.items():
            log(name, f"Exportando sessão do Chrome ({profile})...")
            sessions[name] = export_tiktok_session(driver_path, profile)

    print(f"\n--- Iniciando {len(PROFILES)} navegadores ---\n")

    for name, profile in PROFILES.items():
        print(f">>> Processando {name} ({profile})...")
        liker = TikTokLiker(name, profile, live_url, driver_path, counter, session_data=sessions.get(name))

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

    summary = None
    if SHOW_LOCAL_STATS:
        summary = SummaryPrinter(likers, counter)
        summary.start()

    print("=" * 50)
    print(f"   RODANDO {len(likers)} PERFIS - Ctrl+C pra parar")
    print("=" * 50 + "\n")

    time.sleep(2)

    for liker in likers:
        t = threading.Thread(target=liker.run, daemon=True)
        t.start()
        threads.append(t)

    try:
        while True:
            time.sleep(1)
            if not any(t.is_alive() for t in threads):
                break
    except KeyboardInterrupt:
        print("\n\nParando...")

    if summary:
        summary.stop()

    for liker in likers:
        liker.stop()

    time.sleep(2)
    for liker in likers:
        try:
            liker.close()
        except BaseException:
            pass

    if SHOW_LOCAL_STATS:
        total = counter.get()
        print(f"\nTotal final (soma dos 3 perfis): {total}")
    print("\nFim!")


if __name__ == "__main__":
    main()
