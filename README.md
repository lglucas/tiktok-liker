# TikTok Liker

[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB)](https://www.python.org/)

Protótipo para fins de estudo: automação para enviar likes em uma live do TikTok com 1–3 perfis em paralelo no Windows.

## Créditos · Credits

PT: Criado por **Lucas L. Galvão** — **Ash Soluções em IA**  
EN: Created by **Lucas L. Galvão** — **Ash AI Solutions**  
Site / Website: https://ash.app.br

## Arquivos (versões) · Files (versions)

- [tiktok_liker.py](./tiktok_liker.py)  
  - PT: v1 — 3 perfis (copiados), threads, pausa curta, base “clássica”  
  - EN: v1 — 3 copied profiles, threads, short pauses, “classic” base

- [tiktok_liker2.py](./tiktok_liker2.py)  
  - PT: v2 — foco e “segurar L” por janelas de tempo  
  - EN: v2 — focus management and “holding L” by time windows

- [tiktok_liker3.py](./tiktok_liker3.py)  
  - PT: v3 — múltiplos navegadores (Chrome/Firefox/Edge)  
  - EN: v3 — multiple browsers (Chrome/Firefox/Edge)

- [tiktok_liker4.py](./tiktok_liker4.py)  
  - PT: v4 — 3 Chromes com perfis anonimizados (isolados)  
  - EN: v4 — 3 Chrome instances with anonymized profiles (isolated)

- [tiktok_liker5.py](./tiktok_liker5.py)  
  - PT: v5 — modo CDP (melhor para background), proxy por perfil e perfis persistentes  
  - EN: v5 — CDP input mode (better in background), per-profile proxy and persistent profiles

Histórico completo / Full history: [CHANGELOG.md](./CHANGELOG.md)

## Qual versão usar? · Which version to use?

| Versão | Arquivo | Perfis | Input | Background/minimizado | Quando usar |
|---:|---|---|---|---|---|
| 1 | `tiktok_liker.py` | Copia perfis do Chrome | ActionChains | Médio | Base estável e simples |
| 2 | `tiktok_liker2.py` | Copia perfis do Chrome | “Segurar L” | Médio | Testar variação “peso no L” |
| 3 | `tiktok_liker3.py` | Navegadores diferentes | Varia por browser | Médio | Testar “separar por browser” |
| 4 | `tiktok_liker4.py` | Anonimizados (isolados) | ActionChains | Médio | Testar isolamento total de perfil |
| 5 | `tiktok_liker5.py` | Copiados ou anonimizados | CDP/ActionChains | Alto (CDP) | Recomendado para usar o PC livre |

## Requisitos · Requirements

- PT: Windows 10/11  
  EN: Windows 10/11
- PT: Python 3 (recomendado: 3.10+)  
  EN: Python 3 (recommended: 3.10+)
- PT: Google Chrome instalado  
  EN: Google Chrome installed

## Instalação (VSCode + PowerShell) · Installation

1) PT: Abra a pasta do projeto no VSCode  
   EN: Open the project folder in VSCode  

`C:\Users\lucas\OneDrive\Documentos\Lucas\TikTokLiker`

2) PT: Crie o ambiente virtual  
   EN: Create the virtual environment

```powershell
python -m venv venv
```

3) PT: Ative o ambiente virtual  
   EN: Activate the virtual environment

```powershell
.\venv\Scripts\Activate.ps1
```

4) PT: Instale as dependências  
   EN: Install dependencies

```powershell
pip install selenium webdriver-manager
```

## Como rodar (recomendado) · How to run (recommended)

```powershell
.\venv\Scripts\Activate.ps1
python .\tiktok_liker5.py
```

- PT: Cole o link da live quando solicitado.  
- EN: Paste the live link when asked.

## Configuração rápida (v5) · Quick config (v5)

Abra / Open [tiktok_liker5.py](./tiktok_liker5.py) e ajuste:

- PT: `PROFILES` — quais perfis do Chrome usar  
  EN: `PROFILES` — which Chrome profiles to use
- PT: `INPUT_MODE = "cdp"` — recomendado para minimizar/usar em background  
  EN: `INPUT_MODE = "cdp"` — recommended for minimized/background use
- PT: `USE_ANON_PROFILES = True` — se quiser perfis isolados  
  EN: `USE_ANON_PROFILES = True` — if you want isolated profiles
- PT: `PROXY_PER_PROFILE` — opcional, para proxy por perfil  
  EN: `PROXY_PER_PROFILE` — optional, per-profile proxy

### Login “não fica salvo” · Login “not persisted”

- PT: Na v5, o perfil copiado agora é reaproveitado por padrão. Se quiser forçar recópia:  
  `REFRESH_PROFILE_COPY_ON_START = True`  
- EN: In v5, the copied profile is reused by default. To force a fresh copy:  
  `REFRESH_PROFILE_COPY_ON_START = True`

- PT: Para apagar o cache e começar do zero:  
  `CLEAN_PROFILE_CACHE_ON_START = True`  
- EN: To wipe cache and start from scratch:  
  `CLEAN_PROFILE_CACHE_ON_START = True`

## Licença (sugestão) · License (suggestion)

- PT: Para repositório público com uso não-comercial, a sugestão é **PolyForm Noncommercial 1.0.0**.  
- EN: For a public, non-commercial repository, the suggestion is **PolyForm Noncommercial 1.0.0**.

## Disclaimer

- PT: Este projeto é um protótipo para fins de estudo. Automação pode violar os Termos de Uso do TikTok. Use por sua conta e risco.  
- EN: This project is a prototype for study purposes. Automation may violate TikTok’s Terms of Service. Use at your own risk.
