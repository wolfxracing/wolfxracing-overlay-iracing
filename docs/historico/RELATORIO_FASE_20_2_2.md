# Overlay iRacing — Relatório da Fase 20.2.2 (teclas de atalho globais para o Stream Deck)

**Arquivos alterados:** `overlay_iracing.py`, `ov_nucleo.py`, `executar_testes.bat`, `LEIA-ME.txt`, `ROTEIRO_VALIDACAO.txt`, `testes/teste_fase20.py` (só a conferência do número da versão no log).
**Arquivos novos:** `testes/teste_fase2022.py`, `fechar_overlay.bat`, `ATALHOS_STREAM_DECK.txt`, este relatório, e a pasta `streamdeck/` (perfil e ícones).
**Situação:** implementado e testado **apenas com dados simulados e com uma simulação da API do Windows**. A homologação real (Stream Deck apertando o atalho com o overlay aberto e o iRacing em primeiro plano) está no **teste 13** do `ROTEIRO_VALIDACAO.txt` e **não foi feita**. As janelas, os cálculos, os perfis, os layouts e os arquivos de dados **não foram alterados**. Fase 21 e integração com a Data API **não foram iniciadas**.

## 1. Resumo executivo

- O overlay passa a aceitar **22 atalhos globais** (Ctrl+Alt+Shift+F13…F24 e Ctrl+Alt+F13…F22), registrados no Windows com `RegisterHotKey`, sem instalar nada e **sem injetar código no iRacing** (o anti-cheat não é tocado).
- Cada atalho **chama o mesmo item do menu da bandeja** (ou a mesma função), então o comportamento é o já conhecido: ligar/desligar as 12 janelas, escolher o perfil (Automático/Treino/Classificação/Corrida), economia de CPU, aparecer sozinho, travar posição, zerar pico de G, limpar impactos e **fechar o overlay**.
- Há uma saída de emergência: `fechar_overlay.bat` encerra à força **somente** processos Python cujo comando contém `overlay_iracing.py`.
- Perfil do Stream Deck **Overlay iRacing** gerado (página principal + pasta “Suporte”), com 38 botões e ícones próprios.

## 2. Como funciona

| Peça | Onde | Função |
|---|---|---|
| Tabela `ATALHOS` | `ov_nucleo.py` | Única fonte da verdade: id, combinação, tipo (`alternar`, `perfil`, `chamar`) e alvo. O perfil do Stream Deck e o `ATALHOS_STREAM_DECK.txt` saem dela. |
| `EscutaTeclas` | `ov_nucleo.py` | Thread própria registra os atalhos e espera `WM_HOTKEY`; entrega os códigos numa fila. Desligar libera todos os atalhos. |
| `ApiTeclasWindows` | `ov_nucleo.py` | Única parte que toca no Windows (`ctypes`, `user32`). Substituível por uma API falsa nos testes. |
| `DespachanteTeclas` | `ov_nucleo.py` | Ignora repetição em menos de 0,2 s, ignora códigos desconhecidos e isola qualquer erro (um atalho com defeito não derruba o overlay). |
| Integração | `overlay_iracing.py` (`principal`) | Timer de 40 ms lê a fila no thread da interface e chama o item do menu (`toggle`) ou a função equivalente. |

Novo item no menu da bandeja: **“Teclas de atalho para o Stream Deck”** (ligado por padrão; a escolha fica salva em `teclas_globais`).

## 3. Riscos e decisões

| Risco | Tratamento |
|---|---|
| Conflito com atalhos do iRacing ou de plugins (iRaceDeck, iRacingSFX…) | F13…F24 com Ctrl+Alt(+Shift). Se uma combinação já estiver em uso, só ela falha; o log e a bandeja avisam quais. |
| Toque duplo no Stream Deck ligar e desligar a janela | Intervalo mínimo de 0,2 s por atalho e `MOD_NOREPEAT`. |
| Fechar o overlay sem querer durante a corrida | Botão separado e em vermelho; não há confirmação (o Stream Deck não oferece). Reabrir leva um toque em “Iniciar Overlay”. |
| Overlay travado | `fechar_overlay.bat`, restrito ao processo do overlay. **Não testado em Windows real.** |
| Botão não mostra se a janela está ligada | Limite do Stream Deck (não lê o estado do overlay). Conferir na tela. |
| Dois overlays abertos (normal e demo) | O segundo não consegue registrar as mesmas combinações; o log informa. |

## 4. Testes (dados simulados)

**Novo `testes/teste_fase2022.py`** (incluído no `executar_testes.bat`):
- Mapa: 22 atalhos, sem combinação repetida, F13…F24, todo alvo existe na configuração do overlay; o validador acusa duplicado, tecla fora da faixa, falta de modificador e tipo inválido.
- Despachante: repetição rápida, código desconhecido, erro dentro do atalho.
- Escuta com API falsa: 22 registros com `MOD_NOREPEAT`, ordem da fila, combinação ocupada por outro programa (só ela falha), falha ao preparar, parar e liberar todos.
- **Integração com o overlay inteiro** (`principal()` com a API falsa): as 12 janelas (cada atalho muda só a sua chave e volta ao estado anterior), 4 perfis (incluindo a janela ligada só dentro de um perfil), economia de CPU, aparecer sozinho, travar posição, zerar G, limpar impactos, atalho inexistente sem efeito colateral, **fechar** (chama o mesmo `quit` do menu), desligar e religar as teclas pelo menu, e teclas desligadas na configuração.
- Arquivos de apoio: `fechar_overlay.bat` (nunca mata Python em geral; quebra de linha do Windows) e `ATALHOS_STREAM_DECK.txt` em sincronia com o mapa.

**Regressão:** as suítes das fases 20, 20.1, 20.2 e 20.2.1 passam sem alteração, exceto a conferência do número da versão no log (`teste_fase20.py`), atualizada de 20.2.1 para 20.2.2.

## 5. O que **não** foi validado

- `RegisterHotKey` no Windows real (a API do Windows foi simulada) e o `fechar_overlay.bat` (PowerShell) — **teste 13**.
- A importação do perfil no aplicativo do Stream Deck: o formato foi copiado de um perfil exportado seu e conferido estruturalmente, mas as teclas F13…F24 nunca foram vistas por ele nesse arquivo.
- O comportamento do iRacing em primeiro plano ao receber os atalhos (esperado: nenhum efeito no jogo).

## 6. Pendências

1. Executar o teste 13 e anotar PASSOU/FALHOU.
2. Os testes 3, 7, 10, 11 e 12 (Fases 20.1 a 20.2.1) continuam pendentes; a Fase 21 só depois deles.
