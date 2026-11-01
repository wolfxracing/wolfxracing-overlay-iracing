# Manual do usuário: WolfxRacing Overlay para iRacing

> Versão do overlay neste pacote: **Fase 20.2.2 + estilos Glass Fumê e Sport (1.1.0)**. Os prints foram gerados no **modo demonstração** (dados simulados); as fontes e as medidas podem variar um pouco no seu Windows.

## Sumário

1. [O que é](#1-o-que-é) · 2. [Instalação](#2-instalação-uma-única-vez) · 3. [Configurar o jogo](#3-configurar-o-iracing) · 4. [Uso diário](#4-uso-diário) · 5. [As 12 janelas](#5-as-janelas) · 6. [Como ler os números](#6-como-ler-os-números) · 7. [Dash e Stream Deck](#7-dash-e-stream-deck) · 8. [Solução de problemas](#8-solução-de-problemas) · 9. [Atualizar](#9-atualizar-para-uma-versão-nova) · 10. [Limites](#10-limites-conhecidos)

## 1. O que é

12 janelas independentes e transparentes, sempre por cima do jogo, que podem ser movidas, redimensionadas e ligadas/desligadas pelo menu do ícone vermelho "i" perto do relógio do Windows. Tudo roda localmente; nenhum dado seu é enviado para a internet.

![Visão geral](imagens/overlay_visao_geral.png)

## 2. Instalação (uma única vez)

1. **Python 3.12.** Instale o *Python Install Manager* em [python.org/downloads](https://www.python.org/downloads/).
2. **Extraia** o `.zip` dentro de `C:\WolfxRacing` (o zip já cria a pasta `wolfxracing-overlay-iracing`; o resultado é `C:\WolfxRacing\wolfxracing-overlay-iracing`). Outra pasta também funciona, mas veja o aviso do Stream Deck em [STREAMDECK.md](STREAMDECK.md).
3. Dê duplo clique em **`overlay\instalar.bat`**. Ele prepara o Python 3.12 e instala `pyirsdk` e `PySide6-Essentials`. Aguarde "Instalação concluída".
4. Teste sem o jogo: **`overlay\testar_demo.bat`** (dados simulados, nomes fictícios). Procure o ícone vermelho "i" perto do relógio do Windows (pode estar na seta `^`).

Instalação manual (alternativa): `py -3.12 -m pip install pyirsdk PySide6-Essentials`.

## 3. Configurar o iRacing

- Vídeo em **janela sem bordas**: no iRacing, aba *Display*, desmarque *Full Screen* e *Border* e reinicie o jogo. Visualmente é idêntico à tela cheia.
- Na tela cheia **exclusiva** o Windows não deixa nenhuma janela de outro programa aparecer sobre o jogo. A única forma de contornar seria injetar código no iRacing, o que **este projeto não faz** (poderia ser tratado como violação das regras do serviço).
- O overlay precisa que o iRacing esteja aberto e **dentro de uma sessão**; antes disso a janela mostra "Aguardando o iRacing..."

## 4. Uso diário

1. Abra **`overlay\iniciar_overlay.bat`** (pode ser antes ou depois do jogo).
2. **Posicionar as janelas:** clique com o botão direito no ícone vermelho "i" e **desmarque "Travar posição"**. Janelas destravadas ganham contorno amarelo: arraste para onde quiser. Ao terminar, marque "Travar posição" (os cliques passam a atravessar o overlay).
3. **Redimensionar:** com a posição destravada, arraste uma **borda** (muda só largura ou só altura) ou um **canto** (muda as duas, mantendo a proporção); ou segure **Ctrl** e gire a roda do mouse. *Restaurar o tamanho das janelas (100%)* volta ao padrão.
4. **Aparecer sozinho:** com a posição travada, as janelas aparecem quando você entra no carro e somem 6 s depois de sair (garagem, menu, replay). Para ficarem sempre visíveis, desmarque *Aparecer sozinho ao entrar no carro*.
5. **Iniciar com o Windows:** `ativar_inicio_automatico.bat` (e `desativar_inicio_automatico.bat` para desfazer).
6. **Perfis de exibição** (menu da bandeja > *Perfil de exibição*): **Treino**, **Classificação** e **Corrida** guardam, para cada janela, posição, tamanho e se aparece. *Automático* troca sozinho pelo tipo de sessão (só depois de 3 s estáveis e nunca com as janelas destravadas).
7. **Visual:** *Visual moderno* (carbono, Bahnschrift), **Estilo Glass Fumê** (vidro escuro translúcido, padrão), **Estilo Sport** (itálico, cantos cortados e detalhes vermelhos, igual ao dash Sport) e *Transparência do fundo* (40 a 100%). Desmarcar *Visual moderno* volta ao visual clássico.
8. **Desempenho:** *Modo economia de CPU* (metade das atualizações) e *Prioridade baixa do overlay* (o jogo tem preferência).
9. **Fechar:** *Sair* no menu da bandeja, `Ctrl+Alt+F22` (Stream Deck) ou, se travar, `overlay\fechar_overlay.bat`.

### Estilos visuais

Os dois estilos usam a tipografia esportiva (itálico; títulos em Sui Generis, se o SimHub estiver instalado). Glass Fumê e Sport não se combinam: ao marcar um, o outro desmarca. A *Transparência do fundo* vale para os dois (no Glass Fumê, valores entre 60% e 80% deixam o vidro mais evidente). O vidro é simulado com transparência e reflexos; o overlay não borra o que está atrás da janela.

![Overlay em Glass Fumê](imagens/estilo_glass_overlay.png)

## 5. As janelas

### 1. Telemetria

![Telemetria](imagens/overlay_telemetria.png)

Marcha, velocidade, RPM, pedais (embreagem, freio, acelerador), volante girando como o real (marcador vermelho no topo; ângulo em graus: + esquerda, - direita) e gráfico de acelerador e freio dos últimos ~10 s.

- O gráfico pode ser escondido pelo menu da bandeja (a janela diminui).
- Barra superior = RPM em relação ao limite do carro.

### 2. Voltas (delta, tempos e combustível)

![Voltas (delta, tempos e combustível)](imagens/overlay_voltas.png)

Delta para a melhor volta, tempos atual / última / melhor e uma faixa de cálculo de combustível.

- **Voltas até o fim**: em corrida por tempo, estima pelo ritmo (mediana das últimas voltas limpas).
- **Necessário (+1 v)** = (voltas até o fim + margem) x consumo médio. **Adicionar**: "OK" = termina com a folga; "+x,x L" amarelo = abastecer; vermelho = não cabe de uma vez.
- A margem (0,5 / 1 / 1,5 / 2 voltas) muda em *bandeja > Margem de segurança do combustível*.

### 3. Relativo

![Relativo](imagens/overlay_relativo.png)

Carros à frente e atrás de você na pista, com classe, licença, iRating e distância em segundos, mais a projeção de iRating e SR.

- Sua linha fica em destaque. Linha apagada = outra classe; nome em vermelho = uma volta ou mais à frente; azul = uma volta ou mais atrás; "BOX" = nos boxes.
- A projeção de iRating/SR é **projetada, não oficial**, e é marcada como provisória até a confirmação.

### 4. Classificação

![Classificação](imagens/overlay_classificacao.png)

Carros agrupados por classe (da mais rápida para a mais lenta), com SOF da classe, número, marca, piloto, país, última e melhor volta.

- Melhor volta em **roxo** = a mais rápida da classe. Última volta em **verde** = igualou a melhor do piloto.
- Na sua classe aparecem o topo e os carros ao seu redor; nas outras, os primeiros. Linha pontilhada = carros omitidos.
- Emblemas de marcas **não vêm no pacote** (marcas registradas): mostra as iniciais até você colocar suas próprias imagens em `overlay/emblemas/`.

### 5. Mapa da pista

![Mapa da pista](imagens/overlay_mapa.png)

Traçado da pista com a posição de todos os carros (bolinhas com número e cor da classe; a sua é amarela e maior).

- O traçado é **aprendido na sua primeira volta limpa** em cada pista e fica salvo localmente.
- Se sair estranho: *bandeja > Refazer o mapa desta pista*.

### 6. Radar de proximidade

![Radar de proximidade](imagens/overlay_radar.png)

Visão de cima com seu carro no centro e os carros ao redor (alcance de ~20 m à frente e atrás).

- Branco = normal; amarelo = atenção; vermelho com brilho lateral = o iRacing avisa carro ao lado.
- O iRacing só informa **se** há carro ao lado, não a posição lateral exata; o radar é para prevenir contato, não para medir centímetros.

### 7. Pneus

![Pneus](imagens/overlay_pneus.png)

Vida útil e temperatura de cada pneu. O iRacing só informa valores reais com o carro parado no box; durante a corrida o overlay **estima**.

- Valor com "~" = estimado. A estimativa se calibra sozinha a cada parada nos boxes.
- Cores de temperatura: azul = frio; verde = ideal; amarelo = quente; vermelho = muito quente. Contorno laranja = pneu mais gasto.

### 8. Setores (vs melhor volta)

![Setores (vs melhor volta)](imagens/overlay_setores.png)

Compara cada setor com o **seu** melhor tempo para o mesmo carro e a mesma pista.

- Verde = mais rápido; vermelho = mais lento; roxo = novo melhor setor.
- A referência fica em `recordes_pessoais.json` (local).

### 9. Clima e vento

![Clima e vento](imagens/overlay_clima.png)

Temperatura da pista e do ar, neblina, chuva (atual + tendência) e bússola do vento vista do carro.

- A seta azul mostra para onde o vento sopra, relativo ao carro (para cima = vento de cauda).
- O iRacing **não** entrega previsão de chuva para programas externos.

### 10. Danos

![Danos](imagens/overlay_danos.png)

Reparo obrigatório/opcional (tempo informado pelo iRacing), incidentes, carro visto de cima com as zonas de impacto, avisos de motor e os últimos impactos.

- O iRacing não informa dano por peça. Direção e força dos impactos são **estimadas**.

### 11. Painel de combustível e pit

![Painel de combustível e pit](imagens/overlay_combustivel.png)

Janela de pit, litros a colocar, tabela de consumo (média, máximo, mínimo), barras de voltas possíveis para parar e tempo/voltas até acabar.

- Caixa colorida: **ABERTA** (verde) = pode parar nessas voltas; **FECHADA** (laranja) = cedo demais; **SEM JANELA** (vermelho) = sem plano viável.
- Estimativa baseada no seu ritmo recente; não prevê bandeira amarela.

### 12. Força G

![Força G](imagens/overlay_forca_g.png)

Círculo de G lateral e longitudinal com rastro, G atual e pico, nome e temperatura da pista.

- Cada anel = 1 g (alcance configurável de 2 a 5 g). Curva à esquerda leva o ponto para a esquerda; freando, o ponto desce.


## 6. Como ler os números: real, calculado, estimado

- **Sem marca** = **real**, entregue pelo iRacing (velocidade, marcha, RPM, pedais, volante, força G, combustível no tanque, clima, reparo e avisos do motor).
- **"~"** = **calculado ou estimado** pelo overlay (consumo por volta, voltas/litros até o fim, tempos de setor, distâncias no radar, temperatura e vida dos pneus durante a corrida, lado e força dos impactos, iRating e SR projetados).
- O iRacing **não informa**: se uma volta foi invalidada, a posição lateral dos outros carros, a previsão de chuva, dano por peça e o iRating/SR oficial durante a sessão. Nada disso é inventado pelo overlay.
- **Delta e setores:** o iRacing não diz se a volta foi invalidada; o overlay usa um critério próprio e conservador.

## 7. Dash e Stream Deck

- **Dash MagicDash 4 Glass Fumê ou Sport** (3 telas): veja [DASH.md](DASH.md).
- **Perfil de Stream Deck XL** (janelas, controles, iniciar/fechar, pasta Suporte): veja [STREAMDECK.md](STREAMDECK.md).

![Dash](imagens/dash_visao_geral.png)

## 8. Solução de problemas

| Sintoma | O que fazer |
|---|---|
| "Falta o arquivo ov_nucleo.py" | Copie **todos** os arquivos de `overlay/` para a mesma pasta. |
| O overlay não abre | Abra `overlay\overlay_log.txt` e anexe-o em uma Issue. |
| "Aguardando o iRacing..." | O jogo precisa estar aberto e dentro de uma sessão. |
| Não aparece sobre o jogo | Use **janela sem bordas** (seção 3). |
| Uma janela mostra "Sem dados" | Normal em menus/garagem. Se persistir na pista, anexe o log em uma Issue. |
| Classificação vazia em treino | Carros sem tempo válido ainda não entram na lista. |
| Esquerda e direita trocadas (pneus, danos, força G) | Com o overlay fechado, ponha `"pneu_lado_invertido": true` no `config.json`. |
| Seta do vento invertida | `"vento_invertido": true` no `config.json`. |
| Um atalho do Stream Deck não funciona | Outro programa pode estar usando a combinação; veja o log (`overlay_log.txt`). |
| Valor estranho | Anote a janela e a situação (treino/corrida/carro) e abra uma Issue com o log. |

## 9. Atualizar para uma versão nova

1. Feche o overlay (*Sair* na bandeja).
2. Baixe o novo `.zip` e **copie por cima** da pasta atual (o `config*.json`, recordes, mapas e logs ficam e continuam valendo, pois não vêm no pacote).
3. Leia o [CHANGELOG](../CHANGELOG.md) para ver o que mudou. Reabra o overlay.

## 10. Limites conhecidos

- A estimativa de temperatura e vida dos pneus é uma **estimativa**: antes da primeira calibração (1ª parada nos boxes) pode errar bastante; depois serve bem para comparar e acompanhar a tendência.
- O radar não conhece a posição lateral dos outros carros (limitação do iRacing).
- Em tela cheia exclusiva nenhum overlay aparece (limitação do Windows).
- Os testes automáticos usam dados simulados; a validação real depende do uso em sessões do iRacing (veja `overlay/ROTEIRO_VALIDACAO.txt`).

Mais detalhes técnicos de cada recurso: [`referencia/GUIA_ORIGINAL.txt`](referencia/GUIA_ORIGINAL.txt) (guia completo escrito durante o desenvolvimento).
