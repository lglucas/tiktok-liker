"""
TikTok Liker v6
- Volta ao padrão Selenium que funcionava mesmo em background/minimizado
- 3 Chromes em paralelo com perfis reais (Profile 3/4/5) copiados para user-data-dir isolado
- Login assistido: o script abre as janelas uma vez, você faz login e confirma no terminal
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
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager


CHROME_USER_DATA = r"C:\Users\lucas\AppData\Local\Google\Chrome\User Data"

PROFILES = {
    "TikTok1": "Profile 3",
    "TikTok2": "Profile 4",
    "TikTok3": "Profile 5",
}

SELENIUM_PROFILE_ROOT = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.dirname(os.path.abspath(__file__))),
    "TikTokLiker",
    "ChromeProfiles_v6",
)

LIKE_INTERVAL = 0.05
LIKE_BURST_PER_TICK = 1

CICLO_MIN = 40
CICLO_MAX = 45
PAUSA_MIN = 5
PAUSA_MAX = 10

KILL_CHROME_ON_START = True
CLEAN_PROFILE_CACHE_ON_START = True

WAIT_AFTER_TIKTOK_HOME_SEC = 4
WAIT_AFTER_LIVE_OPEN_SEC = 5

START_RETRIES = 1
START_RETRY_DELAY_SEC = 0

PROFILE_DIRECTORY = None


def log(profile, msg):
    """Imprime logs com timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{profile}] {msg}")


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
    """Fecha Chrome e ChromeDriver (opcional) para evitar locks."""
    subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True, check=False)
    subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], capture_output=True, check=False)
    _wait_process_exit("chrome.exe", timeout_seconds=20)
    _wait_process_exit("chromedriver.exe", timeout_seconds=20)


def clean_profile_cache():
    """Limpa perfis copiados para forçar recópia."""
    if os.path.exists(SELENIUM_PROFILE_ROOT):
        try:
            shutil.rmtree(SELENIUM_PROFILE_ROOT)
        except Exception:
            pass
    os.makedirs(SELENIUM_PROFILE_ROOT, exist_ok=True)


def _cleanup_singleton_locks(user_data_dir):
    """Remove locks antigos do Chrome dentro do user-data-dir."""
    for filename in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        path = os.path.join(user_data_dir, filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


def validate_profiles():
    """Valida se os perfis configurados existem no Chrome."""
    missing = []
    for name, profile_dir in PROFILES.items():
        source_profile_path = os.path.join(CHROME_USER_DATA, profile_dir)
        if not os.path.isdir(source_profile_path):
            missing.append((name, profile_dir, source_profile_path))

    if missing:
        for name, profile_dir, path in missing:
            print(f"ERRO: {name} -> '{profile_dir}' não encontrado em: {path}")
        raise FileNotFoundError("Um ou mais perfis do Chrome não existem.")


def ensure_profile_copy(profile_name, source_profile_dir):
    """Garante um user-data-dir isolado, copiando o perfil do Chrome uma única vez."""
    source_user_data = os.path.normpath(CHROME_USER_DATA)
    source_profile_path = os.path.join(source_user_data, source_profile_dir)

    target_user_data = os.path.join(SELENIUM_PROFILE_ROOT, profile_name)
    target_profile_path = os.path.join(target_user_data, source_profile_dir)
    os.makedirs(target_user_data, exist_ok=True)

    source_local_state = os.path.join(source_user_data, "Local State")
    target_local_state = os.path.join(target_user_data, "Local State")
    if os.path.isfile(source_local_state) and not os.path.isfile(target_local_state):
        try:
            shutil.copy2(source_local_state, target_local_state)
        except Exception:
            pass

    if not os.path.isdir(target_profile_path):
        ignore_names = shutil.ignore_patterns(
            "Cache",
            "Code Cache",
            "GPUCache",
            "GrShaderCache",
            "ShaderCache",
            "Crashpad",
            "optimization_guide_model_cache",
            "Media Cache",
            "DawnCache",
        )
        log(profile_name, f"Copiando perfil para: {target_profile_path}")
        shutil.copytree(
            source_profile_path,
            target_profile_path,
            ignore=ignore_names,
            symlinks=True,
            ignore_dangling_symlinks=True,
        )

    _cleanup_singleton_locks(target_user_data)
    return target_user_data


def is_browser_alive(driver):
    """Verifica se o WebDriver ainda responde."""
    try:
        _ = driver.current_url
        return True
    except Exception:
        return False


class TikTokLiker:
    def __init__(self, name, profile_dir, live_url, driver_path):
        """Controla um navegador e o loop de likes para um perfil."""
        self.name = name
        self.profile_dir = profile_dir
        self.live_url = live_url
        self.driver_path = driver_path
        self.driver = None
        self.likes = 0
        self.running = True

    def start_browser(self):
        """Inicia o Chrome com um perfil copiado e isolado."""
        log(self.name, "Iniciando navegador...")
        options = Options()

        user_data_dir = ensure_profile_copy(self.name, self.profile_dir)
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument(f"--profile-directory={self.profile_dir}")
        options.add_argument("--remote-debugging-pipe")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
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
            log(self.name, f"ERRO ao criar navegador: {e}")
            return False

    def _needs_login(self):
        """Heurística simples para detectar página pedindo login."""
        try:
            title = (self.driver.title or "").lower()
            url = (self.driver.current_url or "").lower()
            if "entrar" in title:
                return True
            if "login" in url or "signin" in url:
                return True
            return False
        except Exception:
            return False

    def go_to_live(self):
        """Abre tiktok.com e depois a live."""
        if not is_browser_alive(self.driver):
            return False

        try:
            self.driver.get("https://www.tiktok.com/")
            time.sleep(WAIT_AFTER_TIKTOK_HOME_SEC)
            self.driver.get(self.live_url)
            time.sleep(WAIT_AFTER_LIVE_OPEN_SEC)
            log(self.name, f"Página carregada: {(self.driver.title or '')[:60]}...")
            return True
        except Exception as e:
            log(self.name, f"ERRO ao acessar live: {e}")
            return False

    def _send_like_key(self):
        """Envia a tecla 'L' dentro do navegador."""
        try:
            self.driver.execute_script(
                """
                const el = document.activeElement;
                if (el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable)) {
                    el.blur();
                }
                """
            )
        except Exception:
            pass

        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys("l")
            self.likes += 1
            return True
        except Exception:
            try:
                ActionChains(self.driver).send_keys("l").perform()
                self.likes += 1
                return True
            except Exception:
                return False

    def run_cycle(self, duration_minutes):
        """Executa um ciclo de likes."""
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        cycle_start = self.likes
        log(self.name, f"Ciclo de {duration_minutes} min iniciado")

        try:
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        except Exception:
            pass

        while datetime.now() < end_time and self.running:
            if not is_browser_alive(self.driver):
                log(self.name, "Navegador fechou!")
                return False

            for _ in range(LIKE_BURST_PER_TICK):
                self._send_like_key()

            time.sleep(LIKE_INTERVAL)

        cycle_likes = self.likes - cycle_start
        log(self.name, f"Fim ciclo: +{cycle_likes} (total perfil: {self.likes})")
        return True

    def run(self):
        """Loop principal do perfil (thread)."""
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
        """Sinaliza parada."""
        self.running = False

    def close(self):
        """Fecha o navegador."""
        self.running = False
        if self.driver:
            try:
                self.driver.quit()
            except BaseException:
                pass
        log(self.name, f"Total perfil: {self.likes} likes")


def main():
    """Entrada principal do script."""
    print("\n" + "=" * 50)
    print("   TikTok Liker v6 - 3 PERFIS")
    print("=" * 50 + "\n")

    validate_profiles()

    if KILL_CHROME_ON_START:
        print("Fechando Chrome...")
        kill_chrome()
        print("OK!\n")

    if CLEAN_PROFILE_CACHE_ON_START:
        print(f"Limpando cache de perfis v6: {SELENIUM_PROFILE_ROOT}")
        clean_profile_cache()
        print("")
    else:
        os.makedirs(SELENIUM_PROFILE_ROOT, exist_ok=True)

    live_url = input("Link da live: ").strip()
    if not live_url:
        print("Link inválido!")
        return

    print(f"\nLink: {live_url}")
    print(f"Perfis: {list(PROFILES.keys())} -> {list(PROFILES.values())}")
    print(f"Intervalo: {LIKE_INTERVAL}s (~{int(1/LIKE_INTERVAL)} L/seg por perfil)\n")
    time.sleep(1)

    driver_path = ChromeDriverManager().install()
    likers = []
    threads = []

    print(f"\n--- Iniciando {len(PROFILES)} navegadores ---\n")
    for name, profile in PROFILES.items():
        liker = TikTokLiker(name, profile, live_url, driver_path)
        log(name, f"Tentativa 1/{START_RETRIES}")
        if liker.start_browser() and liker.go_to_live():
            likers.append(liker)
        else:
            log(name, "Falhou ao iniciar este perfil, pulando...")
        time.sleep(2)

    if not likers:
        print("\nNenhum navegador iniciou!")
        return

    print("\n" + "=" * 50)
    print("   LOGIN ASSISTIDO")
    print("=" * 50)
    print("1) Em cada janela, faça login (se aparecer).")
    print("2) Garanta que cada janela está na LIVE.")
    input("\nQuando as janelas estiverem prontas, pressione ENTER para iniciar os likes...")

    print("\n" + "=" * 50)
    print(f"   RODANDO {len(likers)} PERFIS - Ctrl+C pra parar")
    print("=" * 50 + "\n")

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

    for liker in likers:
        liker.stop()

    time.sleep(2)
    for liker in likers:
        liker.close()

    print("\nFim!")


if __name__ == "__main__":
    main()

