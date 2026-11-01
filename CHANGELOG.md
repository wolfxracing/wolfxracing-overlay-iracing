# Histórico de versões

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e [SemVer](https://semver.org/lang/pt-BR/).

## [1.1.0] - 2026-11-01

- **Novo:** estilo visual **Glass Fumê** (vidro escuro translúcido, reflexo suave, bordas finas, com tipografia esportiva itálica). É o novo padrão do overlay; o Sport continua disponível em *bandeja > Estilo Sport* (os dois são excludentes).
- **Novo:** dash **MagicDash 4 iRacing Glass** (3 telas) ao lado do Sport; gerado com `build_sport.py --vidro`.
- Config: nova chave `tema_vidro` (padrão ligado). Quem já tinha o Sport ligado passa a ver o Glass Fumê e pode voltar ao Sport pela bandeja.
- Sem mudanças na leitura de telemetria nem no perfil do Stream Deck.

## [1.0.0] - 2026-11-01

- Primeira versão pública. Base: overlay iRacing **Fase 20.2.2** (12 janelas, perfis Treino/Classificação/Corrida, atalhos globais para Stream Deck, projeção de iRating/SR com ciclo de vida, painel de combustível e pit, pneus estimados com calibração, mapa aprendido, radar, setores, clima, danos, força G).
- **Novo:** estilo visual **Sport** (itálico, cantos cortados, carbono em sarja, detalhes vermelhos; títulos em Sui Generis se instalada). Desmarcável em *bandeja > Estilo Sport*.
- **Novo:** dash **MagicDash 4 Sport** (3 telas) para o Simagic MagicDash 4, com 6 luzes de aviso dentro do tacômetro.
- **Novo:** perfil de Stream Deck XL com caminho ajustável (`ajustar_perfil.py`).
- Pacote limpo de dados pessoais e de marcas registradas; documentação e manual com prints.

O histórico detalhado de desenvolvimento (relatórios por fase) está em [docs/historico](docs/historico).
