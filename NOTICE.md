# Avisos e componentes de terceiros

Este projeto é **independente** e **não é afiliado, aprovado ou patrocinado** por iRacing.com Motorsport Simulations, Simagic, Blazing Fast / SimHub, Elgato (Corsair), Microsoft ou Python Software Foundation. Todos os nomes e marcas citados pertencem aos seus donos e são usados apenas para identificar compatibilidade.

## Componentes distribuídos neste repositório

| Componente | Licença | Onde |
|---|---|---|
| [flag-icons](https://github.com/lipis/flag-icons) (bandeiras de países) | MIT | `overlay/bandeiras/` (texto da licença em `LICENSE-flag-icons.txt`) |
| Ícones do Stream Deck, fundos e ícones do dash | MIT (desenhos originais do projeto) | `streamdeck/`, `dash/tools/assets_sport/`, `dash/tools/assets_vidro/` |

## Instalados à parte (não distribuídos aqui)

| Componente | Licença | Observação |
|---|---|---|
| [PySide6 / Qt for Python](https://doc.qt.io/qtforpython/) | LGPLv3 / GPL / comercial | instalado via `pip` |
| [pyirsdk](https://github.com/kutu/pyirsdk) | MIT | instalado via `pip` |
| Fonte **Sui Generis** | distribuída com o SimHub (pasta `DashFonts`) | **não** redistribuída aqui; usada pelo dash e pelos títulos do overlay se estiver instalada |
| Fonte **Bahnschrift** | Microsoft (inclusa no Windows 10/11) | não redistribuída |
| SimHub, aplicativo Stream Deck | proprietários / freeware | necessários para o dash e o perfil |

## O que **não** deve ser adicionado ao repositório

Logos de jogos, de fabricantes de carros ou de equipes; emblemas de marcas (a pasta `overlay/emblemas/` é para o usuário usar localmente); fontes comerciais; dados pessoais (configuração, logs, recordes, mapas).
