# Overlay iRacing — Relatório da Revisão Técnica Fase 20.1

**Arquivos alterados:** `overlay_iracing.py` e `ov_nucleo.py` (mais `testes/teste_fase201.py` novo, `LEIA-ME.txt`, `ROTEIRO_VALIDACAO.txt` e `executar_testes.bat`).
**Situação:** correções implementadas e testadas **apenas com dados simulados**. **Não há homologação real.** A homologação só pode ser declarada depois de o `ROTEIRO_VALIDACAO.txt` (testes 3, 7, 10, 11 e 12) ser executado numa sessão real do iRacing e anotado como PASSOU.

## 1. Resumo executivo

Os cinco pontos da auditoria foram confirmados com reprodução antes de qualquer alteração. Todos foram corrigidos sem mexer nas 12 janelas, nos 3 perfis, nas configurações salvas nem no visual (exceções listadas na seção 5). Cada correção tem teste automatizado; a regressão das Fases 2 a 20 continua verde.

## 2. Problemas confirmados, impacto e correção

| # | Problema confirmado no código | Impacto | Correção |
|---|---|---|---|
| 1 | `montar_radar()` marcava como `lado_fonte="sdk"` o carro **inferido** como o mais próximo longitudinalmente. O SDK só confirma *quantos* carros há de cada lado, não *qual* `CarIdx`. | O overlay apresentava como fato do SDK algo que é inferência; com dois candidatos (um 3 m à frente, outro 5 m atrás, aviso de 1 carro) podia apontar o carro errado como "confirmado". | Separação explícita: `ocupacao_sdk` (confirmada), `lado_fonte="inferido"` + `ident` `unica`/`ambigua` (identidade estimada), distância longitudinal (calculada, "~"), lado dos demais `indef` (desconhecido). Legenda do radar atualizada; candidato ambíguo desenhado com borda distinta. |
| 2 | `ttc = gap/aprox` e urgência 2/3 por aproximação longitudinal, mesmo com lado desconhecido. | Alerta laranja/vermelho de "contato" sem saber se os carros se sobrepõem lateralmente (falso alarme ou falsa confiança). | `ttc` → `alcance_s` (exibido como "~x,x s"). Urgência 3 só com ocupação lateral do SDK; sem lateral conhecida o máximo é 1 (atenção, amarelo). Urgência 2 deixou de ser usada. |
| 3 | `comparar_oficial()` comparava sempre que o iRating atual diferia da base, sem identificar a corrida. O iRating exibido vale para a **categoria da sessão atual**. | Uma sessão de outra categoria (ex.: oval depois de asfalto) gerava "erro de projeção" falso e contaminava a calibração. | Identidade da corrida (`SubSessionID` + categoria + usuário + oficial) gravada na pendente; `avaliar_comparacao()` só compara com outra sessão, mesma categoria e usuário, base válida e valor oficial já atualizado. Pendente de formato antigo e com base incerta é descartada; sem identidade forte não grava pendente. Motivo de cada "não comparada" vai ao log. CSV ganhou `corrida_id` e `categoria`; o CSV antigo é preservado renomeado. |
| 4 | Combustível: `paradas = ceil(adicionar/capacidade)` ignorava que a margem se aplica na chegada de **cada** parada; janela marcava "aberta/urgente" mesmo quando o combustível não chegava nem à próxima linha; corrida por voltas+tempo usava só voltas. | Subestimava paradas (284 de 4.000 casos sorteados divergiam do simulador); "box AGORA" para quem não chega ao box; margem maior que o tanque não era detectada. | `planejar_paradas()`: nº mínimo de paradas em voltas inteiras (margem em cada parada, reabastecimento até o topo) e janela da 1ª parada; "SEM JANELA" com motivo (`nao_chega_ao_box`, `tanque_insuficiente`); fim da corrida = o que acabar primeiro (voltas/tempo); tolerância numérica no teto de voltas. Litros por parada = total/paradas; sem plano viável não mostra litros. |
| 5a | Mapa de 360 pontos exigia 359 pontos amostrados; amostragem lenta × velocidade alta saltava pontos e a volta nunca fechava (4 de 96 combinações; aliasing). | Mapa preso em "Aprendendo…" ou nunca concluído. | Interpolação linear **só entre duas amostras reais seguidas** (≤ 12 pontos, ≤ 1 s, sem box/parada/reset) e fechamento por maior lacuna ≤ 3 pontos. Mapas salvos continuam válidos. |
| 5b | Pneus: sem defeito de dados; a distinção real × estimado estava espalhada no desenho. | Risco de regressão futura sem teste. | Regra única `nucleo.origem_pneu()` usada pelo cartão (visual idêntico) e coberta por testes que leem os textos realmente desenhados. |

## 3. Testes executados

Todos com dados simulados (`QT_QPA_PLATFORM=offscreen`, sem iRacing):

- **`testes/teste_fase201.py` (novo, 113 verificações):**
  - Radar: ambiguidade de identidade, "livre" não vira perigo, `sem_par`, dois lados, aproximação 25 m → 3 m a 30 m/s nunca passa de urgência 1, perigo 3 só com aviso do SDK, textos desenhados (legenda e "~x,x s").
  - Projeção × oficial: identidade forte/fraca; 9 motivos de `avaliar_comparacao`; integração com arquivos (categoria diferente, mesma sessão, aguardando, ok com CSV, pendente antiga, base incerta, expirada, CSV antigo preservado, fim de corrida sem identidade).
  - Combustível: **3.729 casos aleatórios contra um simulador independente (programação dinâmica), 0 divergências** em nº de paradas e janela; cenários nomeados para tanque parcial, reabastecimento após consumo extra (volta de box fora da média), uma e várias paradas, corridas por tempo (limites e arredondamento), voltas+tempo, margem (monotonia), capacidade máxima, sem janela viável (3 motivos) e propriedades da janela em 1.500 sorteios.
  - Mapa: 192 combinações (6 pistas × 4 velocidades × 4 frequências de 10–60 Hz × com/sem jitter) fecham em 1,1 volta; 48 combinações a 4–5 Hz fecham em 1,1 volta; 2 Hz fecha em até 6 voltas; fidelidade geométrica (erro radial < 2 %); interpolação bloqueada em teletransporte, intervalo longo, box e parado; cache antigo carrega.
  - Pneus: tabela da regra e 4 cenários renderizados (real ao vivo sem "~"; só estimado com "~" e "VIDA~"; última leitura real com idade; sem dado "--").
- **`testes/teste_fase20.py`:** 104 verificações; ajustadas apenas as que codificavam o comportamento corrigido (`lado_fonte`, identidade na projeção, cabeçalho do CSV, versão no log).
- **Regressão Fases 2 a 20:** todas passam. Ajustes justificados somente na Fase 7 (`ttc`→`alcance_s`; urgência por aproximação limitada a 1) e na Fase 17 ("sem janela" quando o combustível não chega à linha).
- Desempenho: `ler()` com 40 carros segue em ~0,3 ms/ciclo (orçamento 5 ms).

## 4. Limitações (leia antes de homologar)

1. **Nada foi validado no iRacing real.** Simulação prova a lógica, não o comportamento do SDK.
2. **Campo `WeekendInfo.Category`:** assumido presente. Se o seu iRacing não o informar, a comparação projeção × oficial simplesmente não ocorre (log `categoria_desconhecida`) — falha segura, mas sem calibração. O roteiro (teste 7) verifica isso.
3. **Projeção × oficial:** o overlay não enxerga corridas feitas sem ele aberto (outro PC, site). Se houver uma, a diferença de iRating/SR inclui essa corrida e a comparação sai errada sem como detectar.
4. **Radar:** a identidade do carro ao lado continua uma heurística (agora rotulada como tal). A posição lateral dos demais carros continua desconhecida; o radar serve para atenção, não para medir contato.
5. **Combustível:** modelo assume consumo médio constante, paradas só na passagem pela linha, reabastecimento até o topo, divisão igual entre paradas e nenhum tempo de box; não prevê bandeira amarela. Em corrida por tempo, assume ritmo de volta constante. O simulador de conferência foi escrito pela mesma autoria da correção (independente em método, não em autoria).
6. **Mapa:** a interpolação é linear entre amostras vizinhas; em curva fechada com amostragem muito lenta pode "cortar" a curva. Validado em pista circular simulada, não em traçados reais (GPS do iRacing).
7. **Pneus:** a distinção real × estimado foi testada nos textos desenhados; cores/opacidade não têm teste automatizado (conferidas visualmente).
8. Testes rodaram em Python 3.13 no ambiente de desenvolvimento; o alvo é Python 3.12 (sem recursos exclusivos da 3.13 no código).

## 5. Compatibilidade e mudanças visíveis

- **Preservado:** 12 janelas, 3 perfis, `config.json`, recordes, mapas, calibração de pneus e histórico.
- **Mudanças visíveis (todas decorrentes das correções):** legenda do rodapé do radar; "~x,x s" no lugar de "x,x s"; cor laranja de perigo e brilho laranja deixaram de existir no radar (amarelo = atenção; vermelho = aviso lateral do SDK); carro ambíguo com borda distinta; subtítulos do painel de combustível quando "SEM JANELA"; "--" no lugar de litros quando não há plano viável.
- **Efeito único de migração:** uma projeção pendente gravada pela Fase 20 (sem identidade da corrida) é descartada sem comparar — perde-se no máximo uma comparação em andamento.
- `comparacao_oficial.csv` no formato antigo é renomeado para `comparacao_oficial_formato_antigo.csv`, nunca apagado.

## 6. Recomendação e próximos passos

Recomendação: **não homologar ainda**. Copiar os dois arquivos, rodar `executar_testes.bat` (deve terminar com "TODOS OS TESTES PASSARAM") e executar no iRacing os testes 3 (radar), 7 (projeção × oficial, incluindo a variante de outra categoria), 10 (combustível), 11 (mapa) e 12 (pneus). Enviar `overlay_log.txt`, `comparacao_oficial.csv` e as anotações PASSOU/FALHOU/DUVIDA.
