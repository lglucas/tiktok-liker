## Changelog

O formato é baseado em Keep a Changelog e a numeração segue SemVer.

### [Unreleased]

- Ajustes e melhorias em andamento.

### [5.0.0] - 2026-01-06

- Cria a versão v5 como evolução direta das versões anteriores.
- Adiciona modo de input via CDP (mais consistente em background/minimizado).
- Adiciona opção de proxy por perfil.
- Adiciona dessincronização opcional no start dos perfis para reduzir bursts simultâneos.
- Melhora a inicialização e o fluxo de abrir `tiktok.com` antes do link da live.
- Melhora persistência de login: reaproveita perfil copiado sem sobrescrever sempre.

Arquivos:
- `tiktok_liker5.py`

### [4.0.0] - 2026-01-06

- Introduz perfis anonimizados isolados por `user-data-dir`, sem copiar o Chrome principal.
- Mantém 3 Chromes em paralelo com threads.

Arquivos:
- `tiktok_liker4.py`

### [3.0.0] - 2026-01-06

- Expande para múltiplos navegadores (Chrome/Firefox/Edge) para comparar comportamento.
- Adiciona pastas temporárias separadas por navegador e limpeza antes de iniciar.

Arquivos:
- `tiktok_liker3.py`

### [2.0.0] - 2026-01-06

- Adiciona lógica de foco e tentativa de “segurar a tecla L” por janelas de tempo.
- Mantém perfis copiados e execução por ciclos.

Arquivos:
- `tiktok_liker2.py`

### [1.0.0] - 2026-01-06

- Base inicial com 3 perfis em paralelo, ciclos longos e pausas curtas.
- Copia perfis do Chrome para permitir múltiplas instâncias.
- Envio de likes via tecla `L` com Selenium.

Arquivos:
- `tiktok_liker.py`

