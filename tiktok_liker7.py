"""
TikTok Liker v7 (Isolamento tipo VM)

Objetivo: te ajudar a rodar instâncias realmente separadas (tipo “máquinas virtuais”),
quando o TikTok começa a agrupar/limitar likes ou bloquear login em janelas automatizadas.

Este arquivo não automatiza likes por si só. Ele serve como “launcher” e checklist
para iniciar ambientes isolados (VirtualBox/Hyper-V) ou, como alternativa leve,
instâncias isoladas do Chrome com user-data-dir diferente.
"""

import os
import shutil
import subprocess
import sys
import time
from datetime import datetime


MODE = "virtualbox"

VBOX_VMS = [
    "TikTokVM1",
    "TikTokVM2",
    "TikTokVM3",
]

HYPERV_VMS = [
    "TikTokVM1",
    "TikTokVM2",
    "TikTokVM3",
]

OPEN_ISOLATED_CHROME = False
ISOLATED_CHROME_ROOT = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.dirname(os.path.abspath(__file__))),
    "TikTokLiker",
    "IsolatedChrome",
)
ISOLATED_CHROME_COUNT = 3
ISOLATED_CHROME_URL = "https://www.tiktok.com/"


def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")


def command_exists(command_name):
    return shutil.which(command_name) is not None


def run(command):
    return subprocess.run(command, check=False)


def _resolve_vboxmanage_path():
    path = shutil.which("VBoxManage")
    if path:
        return path

    candidates = [
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Oracle", "VirtualBox", "VBoxManage.exe"),
        os.path.join(
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            "Oracle",
            "VirtualBox",
            "VBoxManage.exe",
        ),
    ]

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate

    try:
        import winreg

        for key_path in (
            r"SOFTWARE\Oracle\VirtualBox",
            r"SOFTWARE\WOW6432Node\Oracle\VirtualBox",
        ):
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                    install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                if install_dir:
                    candidate = os.path.join(install_dir, "VBoxManage.exe")
                    if os.path.isfile(candidate):
                        return candidate
            except OSError:
                pass
    except Exception:
        pass

    return None


def start_virtualbox():
    vboxmanage = _resolve_vboxmanage_path()
    if not vboxmanage:
        log("VBoxManage não encontrado. Instale o VirtualBox ou ajuste o PATH.")
        return 1

    log("Iniciando VMs no VirtualBox...")
    for vm in VBOX_VMS:
        log(f"Start VM: {vm}")
        run([vboxmanage, "startvm", vm, "--type", "gui"])
        time.sleep(2)
    return 0


def start_hyperv():
    log("Iniciando VMs no Hyper-V...")
    ps = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        "Start-VM -Name " + ",".join([f"'{vm}'" for vm in HYPERV_VMS]),
    ]
    return run(ps).returncode


def open_isolated_chrome_instances():
    os.makedirs(ISOLATED_CHROME_ROOT, exist_ok=True)
    log("Abrindo Chromes isolados (sem VM)...")

    for i in range(1, ISOLATED_CHROME_COUNT + 1):
        user_data_dir = os.path.join(ISOLATED_CHROME_ROOT, f"Chrome{i}")
        os.makedirs(user_data_dir, exist_ok=True)
        log(f"Abrindo Chrome{i}: {user_data_dir}")
        run(
            [
                "cmd",
                "/c",
                "start",
                "chrome",
                f'--user-data-dir="{user_data_dir}"',
                '--profile-directory="Default"',
                ISOLATED_CHROME_URL,
            ]
        )
        time.sleep(2)

    return 0


def print_recommendation():
    print("")
    print("Recomendação prática (bem direta):")
    print("")
    print("1) Se o seu objetivo é aumentar likes aceitos no contador da live:")
    print("   - VM + proxy por VM tende a ajudar mais do que só perfil/aba.")
    print("")
    print("2) Se o seu objetivo é só parar o TikTok de travar login no Selenium:")
    print("   - Faça login manual dentro de cada ambiente (VM/isolado) e depois rode o bot.")
    print("")
    print("3) O equivalente “mais leve que VM”:")
    print("   - Perfis isolados por user-data-dir (o que a v4 faz).")
    print("")


def main():
    print("")
    print("=" * 50)
    print("TikTok Liker v7 - Isolamento tipo VM")
    print("=" * 50)
    print("")

    print_recommendation()

    if OPEN_ISOLATED_CHROME:
        return open_isolated_chrome_instances()

    if MODE == "virtualbox":
        return start_virtualbox()
    if MODE == "hyperv":
        return start_hyperv()

    log(f"MODE inválido: {MODE}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
