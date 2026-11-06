# Mapa de comandos × ícones — Overlay iRacing (Stream Deck XL)

Fonte dos comandos: tabela `ATALHOS` do `ov_nucleo.py` (28 atalhos: 22 da fase 20.2.2 + 4 da v1.3.0 + 2 do pit na v1.7.0). Nenhum comando novo foi inventado.
Chave de posição no Stream Deck = **coluna,linha** (0,0 = canto superior esquerdo; XL: 0..7 × 0..3).

## 1. Janelas (16) — um único comando cada: alternar mostrar/ocultar
| Pos. | Janela | Atalho | Ícone (ligado) | Ícone (desligado, opcional) |
|---|---|---|---|---|
| 0,0 | Telemetria | Ctrl+Alt+Shift+F13 | janela_telemetria | janela_telemetria_desligada |
| 1,0 | Voltas | Ctrl+Alt+Shift+F14 | janela_voltas | janela_voltas_desligada |
| 2,0 | Relativo | Ctrl+Alt+Shift+F15 | janela_relativo | janela_relativo_desligada |
| 3,0 | Classificação | Ctrl+Alt+Shift+F16 | janela_classificacao | janela_classificacao_desligada |
| 4,0 | Mapa | Ctrl+Alt+Shift+F17 | janela_mapa | janela_mapa_desligada |
| 5,0 | Radar | Ctrl+Alt+Shift+F18 | janela_radar | janela_radar_desligada |
| 6,0 | Pneus | Ctrl+Alt+Shift+F19 | janela_pneus | janela_pneus_desligada |
| 7,0 | Setores | Ctrl+Alt+Shift+F20 | janela_setores | janela_setores_desligada |
| 0,1 | Clima | Ctrl+Alt+Shift+F21 | janela_clima | janela_clima_desligada |
| 1,1 | Danos | Ctrl+Alt+Shift+F22 | janela_danos | janela_danos_desligada |
| 2,1 | Combustível | Ctrl+Alt+Shift+F23 | janela_combustivel | janela_combustivel_desligada |
| 3,1 | Força G | Ctrl+Alt+Shift+F24 | janela_forca_g | janela_forca_g_desligada |
| 3,3 | Luz ABS | Alt+F13 | janela_luz_abs | janela_luz_abs_desligada |
| 4,3 | Luz TC (estimada) | Alt+F14 | janela_luz_tc | janela_luz_tc_desligada |
| 5,3 | Retorno à pista | Alt+F15 | janela_retorno | janela_retorno_desligada |
| 6,3 | Estratégia de pneus | Alt+F16 | janela_estrategia | janela_estrategia_desligada |

**Limite técnico:** o Stream Deck não lê o estado do overlay. O botão alterna (liga/desliga), mas não muda de ícone sozinho. Os ícones "desligada" ficam na biblioteca para uso manual ou para uma fase futura (exigiria sincronismo de estado, fora do escopo atual). Não existem comandos separados "mostrar" e "ocultar".

## 2. Perfis e controles
| Pos. | Função | Atalho | Ícone |
|---|---|---|---|
| 4,1 | Perfil Automático | Ctrl+Alt+F13 | perfil_auto |
| 5,1 | Perfil Treino | Ctrl+Alt+F14 | perfil_treino |
| 6,1 | Perfil Classificação | Ctrl+Alt+F15 | perfil_classificacao |
| 7,1 | Perfil Corrida | Ctrl+Alt+F16 | perfil_corrida |
| 0,2 | Economia de CPU (alterna) | Ctrl+Alt+F17 | ctrl_economia_cpu (+ _desligado) |
| 1,2 | Aparecer sozinho (alterna) | Ctrl+Alt+F18 | ctrl_aparecer_sozinho (+ _desligado) |
| 2,2 | Travar posição (alterna) | Ctrl+Alt+F19 | ctrl_travar_posicao (+ _desligado) |
| 3,2 | Zerar pico de G | Ctrl+Alt+F20 | ctrl_zerar_pico_g |
| 4,2 | Limpar impactos | Ctrl+Alt+F21 | ctrl_limpar_impactos |
| 5,2 | **Pit: PEDIR a entrada** (liga o aviso de entrada dos boxes) | Ctrl+Alt+F23 | ctrl_pit_pedir |
| 6,2 | **Pit: CANCELAR o pedido** | Ctrl+Alt+F24 | ctrl_pit_cancelar |
| 1,3 | Fechar overlay (sair) | Ctrl+Alt+F22 | ctrl_fechar |

## 3. Ações que não usam atalho (abrem arquivos/programas do Windows)
| Pos. | Função | Ícone |
|---|---|---|
| 0,3 | Iniciar overlay (abre o iniciar) | ctrl_iniciar |
| 2,3 | Forçar fechamento (`fechar_overlay.bat`) | ctrl_forcar_fechamento |
| 7,2 | Pasta do overlay | sup_pasta_overlay |
| 7,3 | Pasta "Suporte" (abre a subpágina) | sup_pasta_suporte |

## 4. Pasta Suporte (tecla 0,0 reservada ao Voltar)
sup_voltar (0,0), sup_demo (2,1: Modo Demo), sup_log (3,1: Abrir log), sup_atalhos, sup_testes, sup_emblemas, sup_historico, sup_guia, sup_roteiro, sup_recordes, sup_inicio_windows_on, sup_inicio_windows_off.

## 5. Opções que existem só no menu da bandeja (sem atalho)
Sub-opções dentro de cada janela (tamanho, opacidade, modos de exibição etc.) e demais itens do menu **não têm atalho global**. Criar botões para elas exige **alterar o código do overlay** — não implementado e **não será feito sem sua aprovação**.

## 6. Padrão visual
Fundo fibra de carbono grafite; acento âmbar (padrão), vermelho (fechar/perigo), verde (iniciar/ligado), roxo (melhor setor); traço 6 px (contorno) / 3,5 px (detalhe); rótulo em caixa alta, itálico condensado, sombra; 144×144 px. Desenhos 100% originais, inspirados apenas no estilo do pacote que você usa (nenhum arquivo do pacote foi copiado ou alterado).

## 7. Pit (v1.7.0)
Os botões **Pedir pit** e **Cancelar pit** ocupam as posições 5,2 e 6,2 da página principal; **Modo Demo** e **Abrir log** foram para a pasta Suporte (2,1 e 3,1). Para usar junto com a macro do iRacing ("Pitting In"), crie no seu perfil um **Multi Action** com 2 ações: a macro de chat do iRacing e o atalho **Ctrl+Alt+F23**. O aviso de entrada só liga quando o pedido é feito.


## 8. Telas novas (build q)
Pagina principal: `sup_telas_novas` em (7,2) abre a pasta **Telas novas**: `sup_voltar` (0,0), `janela_consumo` (1,0, Alt+F17), `janela_delta_trace` (2,0, Alt+F18), `janela_curvas` (3,0, Alt+F19). `sup_pasta_overlay` passou para a pasta Suporte (4,1).
