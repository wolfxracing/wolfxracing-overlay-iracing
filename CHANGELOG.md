# Histórico de versões

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e [SemVer](https://semver.org/lang/pt-BR/).

## [1.6.2] - 2026-11-03

- **Corrigido:** **Corvette** passa a usar o emblema próprio (`corvette.png`) em vez do da Chevrolet quando o carro é um Corvette ("Chevrolet Corvette Z06 GT3.R" no LMU, "Chevrolet Corvette C8.R" no iRacing). A Camaro e outros Chevrolet continuam com `chevrolet.png`.
- **Novo:** a marca **Duqueine** (LMP3 do LMU) é reconhecida e procura `duqueine.png`.
- **Corrigido:** a lista `emblemas_faltando.txt` (`emblemas_faltando_lmu.txt` no LMU) é apagada ao abrir o overlay e passa a listar só as marcas que aparecerem na sessão. Evita sobras de versões antigas, como nomes de equipe do LMU (13, CLX, Manthey...), que já não são tratados como marca desde a 1.5: no LMU a marca vem do modelo do carro, nunca da primeira palavra.
- Novo teste automático `testes/teste_marcas.py` (marcas de iRacing e LMU, nomes de equipe e limpeza da lista).
- Os emblemas das montadoras continuam fora do pacote público (marcas registradas): cada usuário coloca os seus em `emblemas/`.

## [1.6.1] - 2026-11-02

- **Novo:** **Classificação no layout de transmissão** (arquivo novo `ov_classif_foto.py`). Barra superior com sessão (RACE...), volta atual/total (corrida por tempo: "4/∞ = 34.66" = estimativa de voltas até o fim), tempo decorrido/duração, AIR, TRACK, HUM, INC (incidentes/limite) e estado da pista (Dry/Damp/Wet/Rain). Colunas: POS, +/-, #, círculo do pneu (H/M/S/W/I/D), LIC · iR com a **variação de iRating projetada de cada piloto** (só em corrida), marca, bandeira, DRIVER, GAP, INT, BEST, LAST, PIT (paradas) e STINT (voltas desde a última parada). Seu carro em roxo. Janela de 846 px.
- **Estimativas:** GAP e INT **na corrida** são estimados (diferença de posição na pista × tempo de volta típico da classe; "+1L" = volta(s) atrás); em treino e qualificação são a diferença das melhores voltas. A variação de iRating é uma projeção pelo mesmo modelo da janela Relativo.
- **Configuração (opcional):** `classificacao_layout` = `"classico"` volta à janela antiga (1.6.0); `classificacao_idioma` = `"pt"` traduz os rótulos. Sem o `ov_classif_foto.py`, o overlay usa a janela antiga.
- **Novo:** **versão EXE, sem precisar de Python.** Cada release traz `WolfxRacing_iRacing_vX.Y.Z_EXE.zip` (pasta única; config, logs, emblemas e bandeiras ficam ao lado do `.exe`). Também dá para gerar no seu PC com `overlay\gerar_exe.bat`. O EXE não tem assinatura digital paga: o Windows SmartScreen pode avisar ("Mais informações" > "Executar assim mesmo"). Os emblemas das montadoras não vão no pacote público.
- Novos arquivos: `ov_classif_foto.py`, `wolfx_iracing.spec`, `gerar_exe.bat`, `exe_modelo/`, `wolfxracing.ico`, `tools/notas_release.py` e o fluxo `.github/workflows/release.yml`.

## [1.6.0] - 2026-11-02

- **Novo:** **Central de configurações**: janela interativa (duplo clique no ícone da bandeja, ou "Abrir configurações…"). Cartões com prévia, liga/desliga, busca e filtros; "Personalizar" abre o tamanho, as opções do painel e a prévia ao vivo; páginas de Aparência e sistema e de Perfis. Usa os mesmos itens do menu: atalhos do Stream Deck e perfis continuam valendo. O menu da bandeja ficou curto (Abrir configurações, Travar posição, Todas as opções, Sair); o menu completo é o submenu "Todas as opções (avançado)".
- **Novo:** janela **Último contato**: quem você tocou por último (pontos 0x/1x/2x/4x do iRacing, volta, há quanto tempo e onde o piloto está agora em segundos). O contato é detectado pelo contador de incidentes e pelo pico de aceleração com um carro encostado (até 7 m): é uma estimativa.
- **Novo:** janela **Entrada do pit**: distância até a entrada dos boxes, aviso FREIE (distância de frenagem estimada até o limite) e, na pit lane, velocidade contra o limite e distância até o seu box. A entrada é aprendida na primeira vez que você entra por pista (arquivo `pit_entradas.json`); aparece com parada pedida ou com a opção "mostrar sempre".
- **Novo:** Classificação com colunas **SR** (licença e SR) e **iR** (iRating) de cada piloto. Janela 112 px mais larga (678 px). O LMU não tem iRating/SR.
- Visual da Central e ícone da bandeja com a marca WolfxRacing (pasta `overlay/marca/`: logos originais, sem alteração, e imagens de cenário). A marca é identidade do projeto; veja o NOTICE.
- **Novo:** janela **Tendência de ritmo**: últimas voltas limpas (sem boxes, sem bandeira de perigo e até 130% da melhor), ritmo médio das 5 últimas, inclinação do stint em s/volta, previsão da próxima volta e consistência, com gráfico e reta de tendência. A inclinação e a previsão (~) são estimativas por regressão linear; aparecem com 4 voltas limpas no stint.
- **Corrigido:** **Minimapa rotativo** travando (iRacing e LMU). O desenho agora roda a 60 quadros por segundo no relógio próprio, a posição entre duas leituras do jogo é estimada pela velocidade na pista, a rotação e o zoom são aplicados pelo Qt sobre um caminho montado uma única vez (antes eram recalculados 360 pontos em Python a cada ciclo) e o rumo vem da tangente interpolada, que gira de forma contínua (antes mudava em degraus a cada trecho). No modo economia de CPU desenha a metade dos quadros.
- 24 janelas no total. Novos arquivos: `ov_v16.py`, `ov_central.py`, pasta `marca/`.

## [1.5.0] - 2026-11-02

- **Novo:** **Bandeiras**: faixa com a bandeira da pista (verde por 6 s, amarela, amarela de pista inteira, azul, branca, quadriculada, preta/desclassificado, vermelha). Só aparece quando há bandeira.
- **Novo:** **Tráfego de outras classes**: só aparece com carro de outra classe a até ~6 s, com a diferença em segundos (▼ atrás / ▲ à frente; vermelho quando uma classe mais rápida chega por trás). Os segundos são calculados pelo overlay.
- **Novo:** **Minimapa rotativo**: trecho da pista ao redor do seu carro, girando para ele apontar sempre para cima, com os carros na cor da classe e o "N". Alcance 150/260/400 m no menu. O traçado é aprendido na primeira volta (a partir da posição na volta, como o Mapa); é uma inferência.
- **Novo:** **Auxiliar de sessão**: etapa (grid, volta de apresentação, luzes), contagem/duração e tempo restante ao fim. Durante a sessão só aparece com "Auxiliar: também durante a sessão". No iRacing a contagem antes da largada vem marcada com ~ (estimada).
- **Corrigido:** o radar da 1.4.2 podia piscar no modo automático (conflito com o laço principal). Todas as janelas automáticas (radar, bandeiras, tráfego, auxiliar) usam agora a mesma lógica sem piscar.
- 21 janelas no total; sem atalhos de Stream Deck para as novas nesta versão.

## [1.4.2] - 2026-11-02

- **Novo:** **radar automático**: a janela só aparece com carro a até 16 m (ou carro ao lado confirmado pelo SDK) e some ~1,5 s depois. Menu da bandeja: "Radar automático"; destravado, fica sempre visível.
- **Corrigido:** carro ao lado. Faixa vermelha de alerta (esquerda, direita ou dos dois lados), carro desenhado encostado no seu (o SDK não informa a distância lateral; o desenho não sugere mais um espaço que pode não existir), texto **AO LADO** no lugar de "<0,5 m" (que era a distância longitudinal) e luz lateral que some com fade em vez de piscar.
- **Novo:** classificação com coluna **+/−**: posições ganhas (▲ verde) e perdidas (▼ vermelha) desde a largada, por classe, só em corrida. Janela 36 px mais larga.
- **Melhorado:** Telemetria em barra mais compacta (620 × 88 px; 292 px sem o gráfico) com colunas de pedal finas.

## [1.4.1] - 2026-11-02

- **Novo:** layout opcional **em barra horizontal** para a janela Telemetria (menu da bandeja: "Layout em barra horizontal"). Uma linha só, 620 × 88 px (compacta, colunas de pedal finas): volante, marcha, velocidade, pedais com o valor numérico e gráfico. Cores: embreagem azul, freio laranja, acelerador verde. Sem o gráfico a barra tem 292 px. O painel de antes continua sendo o padrão.

## [1.4.0] - 2026-11-02

- **Novo:** janela **Curvas** (a 17ª): velocidade mínima em cada curva, comparada com a sua melhor passagem por ela. Mostra MIN, BEST, DELTA (verde = mais rápido que a melhor passagem, vermelho = perdeu 3 km/h ou mais) e o ângulo do volante no ponto da velocidade mínima, mais as últimas curvas da volta e o que a volta anterior ganhou e perdeu.
- As curvas são achadas sozinhas a partir da velocidade em cada trecho da pista (a primeira volta válida cria o mapa; três voltas o refinam e ele congela). Volta válida = sem boxes, fora da pista, parada ou muito lenta. Tudo vem do carro; o mapa de curvas é uma inferência (curvas muito suaves não aparecem).
- Valores só da sessão (sem gravar por pista); sem atalho de Stream Deck nesta versão. Menu da bandeja: ligar/desligar, escala e "reiniciar o aprendizado desta pista".
- Inclui tudo da 1.3.1 (montadoras pelo modelo, `preparar_emblemas`, recortes).
- Montadoras reconhecidas também: Holden, Caterham e Ginetta (somente o nome; os emblemas continuam fora do repositório).

## [1.3.1] - 2026-11-02

- **Novo:** `preparar_emblemas.bat` / `preparar_emblemas.py`: pega imagens soltas (PNG, JPG, WEBP, SVG) da pasta `emblemas\novos`, corta as bordas, centraliza num PNG quadrado transparente de 256 px e salva em `emblemas` com o nome certo; logos pretos viram brancos (fundo do overlay é escuro; `--nao-clarear` desliga). Para logos que vêm com o nome escrito junto, um `recortes.json` na pasta `novos` diz que parte da imagem guardar (só o símbolo) e quais marcas clarear.
- Reconhecimento de montadora ampliado (também pelo modelo do carro; Corvette, Alpine, Glickenhaus, Vanwall e Isotta Fraschini na lista). O iRacing continua usando a primeira palavra quando nenhuma marca é reconhecida.
- Os emblemas continuam **fora do repositório** (são marcas registradas).

## [1.3.0] - 2026-11-01

- **Novo:** botões de **Stream Deck** para as quatro janelas da 1.2.0: **Luz ABS**, **Luz TC**, **Retorno** e **Estratégia** (linha de baixo da página principal, posições 3,3 a 6,3). O perfil `Overlay iRacing.streamDeckProfile` foi regenerado (30 botões na página principal) e os quatro ícones ficam na biblioteca, com as variantes "desligada".
- **Novo:** atalhos globais `Alt+F13` (Luz ABS), `Alt+F14` (Luz TC), `Alt+F15` (Retorno) e `Alt+F16` (Estratégia). Entram no fim da tabela `ATALHOS`, então os 22 atalhos antigos não mudam; são 26 no total. Não colidem com os do overlay de LMU.
- Corrigido: `streamdeck/gerador/gerar_perfil_v3.py` importava um módulo que não vinha no repositório (`icones_base`); as constantes do Stream Deck XL agora estão no próprio script.
- Quem já importou o perfil antigo: importe de novo (ou crie os quatro botões na mão com a ação *Hotkey*); os demais botões não mudam.
- Sem mudança nas janelas, nos dados nem na configuração. Testes de atalhos atualizados para 26.

## [1.2.0] - 2026-11-01

- **Alterado:** a janela **Telemetria** passou a ser a única janela de pedais: o gráfico agora é rolante por tempo (5 a 30 s), com degraus da marcha, marca do ABS (amarelo) e (opcional) do TC (azul), e pedais calibrados, crus ou os dois. Não existe janela Inputs separada (16 janelas no total).
- **Novo:** **Luz do ABS** (ícone solto que acende quando o ABS atua; cor, modo de piscar e teste de 5 s).
- **Novo:** **Luz do TC** (perda de tração). **Estimativa**: o iRacing não informa o corte do TC; o overlay aprende a relação rpm/velocidade de cada marcha e acende quando o motor sobe além disso. Sensibilidade fina, normal ou grossa.
- **Novo:** **Retorno à pista**: PARE / CEDA / LIVRE e os segundos até o carro mais próximo que vem atrás chegar até você; limites ajustáveis, aparece só quando precisa.
- **Novo:** **Estratégia de pneus** (chuva x seco): SEGUIR / PREPARE-SE / TROCAR, vantagem estimada em s/volta com base nos rivais da sua classe, e qual pneu usar na largada.
- Novo arquivo `overlay/ov_v12.py` (lógica pura, sem Qt e sem SDK) e suíte `testes/teste_v12.py`. Novas chaves de configuração (`mostrar_luz_abs`, `mostrar_luz_tc`, `mostrar_retorno`, `mostrar_estrategia` e opções de cada uma); entram nos perfis Treino/Classificação/Corrida.
- Sem atalhos de Stream Deck para as janelas novas nesta versão (use o menu da bandeja). Só iRacing; o LMU fica para uma próxima versão.
- Dados simulados nos testes: a validação em sessão real (principalmente chuva e Luz do TC) está no `ROTEIRO_VALIDACAO.txt`, teste 14.

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
