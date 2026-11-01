# Arquitetura (para quem vai contribuir)

## Visão geral

- **Overlay**: Python 3.12 + PySide6. Janelas transparentes e sempre no topo, desenhadas com `QPainter` (sem imagens por janela). Tudo local.
- **Fluxo**: `iniciar_overlay.bat` → `pyw -3.12 overlay_iracing.py` → `Telemetria.ler()` (SDK ou demo) a até 30 Hz → `dados` (dicionário) → cada janela recebe `atualizar(dados)` e repinta numa taxa própria (`TAXA_HZ`).
- **Visual**: camada central em `overlay_iracing.py` (`TEMA`, `fonte()`, `fonte_titulo()`, `pintar_superficie()`): temas *clássico*, *moderno*, *Sport* e *Glass Fumê* (`TEMA["vidro"]`, `_superficie_vidro()`). Mudar a aparência de todas as janelas = mexer aí.
- **Dash**: scripts em `dash/tools` geram o `.simhubdash` (JSON do Dash Studio + imagens + JavaScript).
- **Stream Deck**: scripts em `streamdeck/gerador` geram ícones e perfil a partir da tabela de atalhos.

## Arquivos do overlay

| Arquivo | Papel |
|---|---|
| `overlay_iracing.py` | Programa principal: leitura do iRacing (pyirsdk), cálculos (combustível, pneus, delta, setores, relativo, radar...), as 12 janelas (`JanelaBase` e derivadas), bandeja, perfis, tema |
| `ov_nucleo.py` | Núcleo testável sem Qt: atalhos globais (tabela `ATALHOS`), perfis, limitador de taxa, ciclo de vida da projeção de iRating/SR |
| `testes/teste_fase*.py` | Testes automáticos por fase (dados simulados) |
| `bandeiras/` | Bandeiras de países (MIT, projeto flag-icons) |
| `emblemas/` | Pasta para emblemas **do usuário** (marcas registradas não são distribuídas) |

## Princípios do projeto

1. **Nada é inventado.** Dado ausente vira `None`/`--`; valor calculado/estimado é marcado com `~`.
2. **Lógica pura separada da interface** sempre que possível (testável sem Qt).
3. **Sem injeção de código** no jogo; só telemetria oficial (SDK / memória compartilhada).
4. **Sem marcas registradas** no repositório (logos de jogos e de fabricantes).
5. **Sem dados pessoais** em arquivos versionados (config, logs, recordes, mapas).

## Testes

`overlay\executar_testes.bat` (ou `py -3.12 overlay/testes/teste_fase2022.py` e as demais fases). Os testes não precisam do jogo; usam um iRacing simulado.

Para renderizar as janelas fora do Windows (CI ou prévias), defina `QT_QPA_PLATFORM=offscreen`. As fontes do Windows (Bahnschrift) não existem em outros sistemas; o layout cai numa fonte substituta.

## Ideias de contribuição

- Calibração real da temperatura dos pneus (e testes com mais carros).
- Novos idiomas (hoje os textos estão em pt-BR).
- Layouts do dash para outras telas e resoluções.
- Testes com mais carros/classes e relatórios de validação no jogo real.
