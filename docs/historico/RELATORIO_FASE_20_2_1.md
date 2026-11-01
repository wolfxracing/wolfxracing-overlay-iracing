# Overlay iRacing — Relatório dos ajustes finais da Fase 20.2 (versão 20.2.1)

**Arquivos alterados:** `overlay_iracing.py`, `ov_nucleo.py`, `executar_testes.bat`, `LEIA-ME.txt`, `ROTEIRO_VALIDACAO.txt`; novo `testes/teste_fase2021.py`; testes `teste_fase20/201/202` ajustados (item 5).
**Situação:** implementado e testado **apenas com dados simulados**. A homologação real no Windows/iRacing continua **obrigatória** e não foi feita. Fase 21 e integração com a Data API **não foram iniciadas**. Nenhuma funcionalidade nova foi adicionada: 12 janelas, 3 perfis, layouts e configurações preservados.

## 1. Resumo executivo

- **Item 1 resolvido:** a projeção de iRating/SR deixou de ser apagada após a primeira comparação. Ela tem agora um ciclo de vida explícito — **pendente → provisória → confirmada | expirada** — com identidade (SubSessionID, usuário, categoria) e valores originais preservados, e uma única linha por corrida no `comparacao_oficial.csv`.
- **Item 2 resolvido:** resultado oficial da mesma corrida e usuário com variação **zero** passa a ser **confirmado** (erro = projetado − 0). “Valores iguais aos do início, lidos no jogo” deixou de ser tratado como “aguardando oficial” e virou outro fato: **sem atualização numérica** (não é resultado oficial; nada vai ao CSV).
- **Limite que precisa ficar claro:** a confirmação existe e está testada (`confirmar_resultado_oficial`), mas **nenhuma fonte a alimenta** (Data API fora do escopo). Na prática, até essa integração, as linhas reais seguem “provisória”. O ganho é que passam a poder ser confirmadas depois, sem perder dados, sem duplicar e sem contaminar a calibração.

## 2. Ciclo de vida

| Estado | Como entra | Como sai | Efeito no CSV |
|---|---|---|---|
| **pendente** | fim de uma corrida oficial com identidade forte | provisória, confirmada ou expirada | nenhuma linha |
| **provisória** | início de sessão seguinte: mesma categoria e usuário, outra sessão, rating diferente do início | confirmada (resultado oficial) ou expirada (60 dias) | 1 linha, `status=provisoria`, gravada uma vez |
| **confirmada** | resultado oficial com `subsession_id` e `cust_id` iguais (de pendente **ou** provisória) | terminal | a linha provisória é **substituída** (chave `corrida_id`) por `status=confirmada` |
| **expirada** | pendente > 14 dias; base de iRating/SR incerta; outra corrida da mesma categoria/usuário registrada antes (“sobreposta”); provisória > 60 dias | terminal | nada é apagado; linha provisória, se existir, permanece |

Regras adicionais: estados terminais são idempotentes (confirmar duas vezes não muda nada; resultado tardio não reabre expirada); sessões seguintes sobre uma provisória não comparam de novo.

**Retenção (corrigida após a auditoria):** somente registros **confirmados ou expirados** podem ser removidos automaticamente — com mais de 60 dias, ou (os mais antigos primeiro) quando a lista passa de 50. **Pendentes e provisórias nunca são removidas.** Se o limite de 50 for excedido exclusivamente por projeções ativas, todas são preservadas e o log registra o aviso de capacidade (“nenhuma foi removida”). Estado desconhecido é tratado como ativo. Defeito original: `podar()` removia a projeção ativa mais antiga quando não havia terminais (51 pendentes ⇒ 1 perdida).

**Armazenamento:** o mesmo `projecao_pendente.json`, agora `{"versao":3,"projecoes":[...]}`, gravado de forma atômica (arquivo temporário + `os.replace`). Arquivos das Fases 20.1/20.2 (um único dicionário) são migrados para “pendente” com aviso no log; o da Fase 20 (sem SubSessionID) é descartado com aviso, pois não há como associá-lo com segurança. Arquivo ilegível é ignorado **sem ser destruído**.

## 3. Variação zero

- Com resultado oficial associado, `comparar_resultado_oficial()` calcula pelos valores do resultado (`ir_novo − ir_antigo`), nunca pelo jogo, e aceita 0. `variacao_nula=True` quando todas as variações comparadas são zero; o log registra “ZERO confirmada pelo resultado oficial”.
- Resultado sem nenhum par iRating/SR (ou projeção sem previsão): `resultado_incompleto` — não confirma, a projeção segue ativa.
- Sem resultado oficial, valores iguais aos do início: `sem_atualizacao_numerica` (contador `observacoes_sem_variacao`, limitado pelo prazo de 14 dias; a base da próxima corrida continua marcada como incerta, como antes). O motivo antigo `aguardando_oficial` foi removido.

## 4. Pontos de extensão (sem integração externa)

`Telemetria.confirmar_resultado_oficial(resultado)` com o contrato `{"subsession_id","cust_id","ir_antigo","ir_novo","sr_antigo","sr_novo"}`. Não é chamado por nada hoje; é o ponto onde uma futura fonte (Data API ou conferência manual) se encaixa sem alterar o núcleo. Quando houver provisória anterior, o log mostra a divergência entre provisório e oficial.

## 5. Testes (dados simulados)

**Novo `testes/teste_fase2021.py`** (também incluído no `executar_testes.bat`):
- Variação **positiva**, **negativa** e **zero** (zero nas duas métricas, só iRating, só SR; só uma métrica presente).
- **Confirmação posterior a provisória:** dados originais preservados, `provisoria_anterior` e divergência calculadas, CSV com **1 linha** por corrida (substituída, não duplicada), idempotência.
- **Rejeição** de SubSessionID/usuário divergentes (inclui `None`, texto inválido, vazio) em registro pendente e provisório; nenhum arquivo muda.
- Resultado incompleto; resultado tardio para projeção expirada; provisória preservada por várias sessões; duas corridas em aberto sem contaminação; sobreposição; expiração (14/60 dias, base incerta); poda; migração v2/v1; arquivo ilegível preservado; fim de corrida sem identificação segura não apaga projeções existentes; CSV de formato antigo continua sendo preservado; gravação atômica sem sobras `.tmp`.
- **Retenção (50/51/100):** 51 pendentes preservadas e capacidade sinalizada; 50 sem alteração; 100 só de ativas (pendentes, provisórias, mistas) preservadas; 51 e 100 com terminais (sai só o terminal mais antigo; 50 ativas + 50 terminais ⇒ ficam as 50 ativas; 20 ativas + 80 terminais ⇒ 20 + os 30 terminais mais recentes; 51 ativas + 49 terminais ⇒ 51 ativas); idade (terminal antigo sai, ativa antiga fica); idempotência, ordem, entrada não mutada, estado desconhecido; varredura de 105 combinações sem nenhuma ativa perdida; integração com a Telemetria (arquivo e aviso no log). A reintrodução proposital do defeito é detectada.
- **Verificação dos testes:** três mutações propositais no código (não aceitar zero; anexar em vez de substituir no CSV; apagar a projeção após a provisória) foram todas detectadas.

**Testes antigos ajustados, com justificativa** (só onde codificavam o comportamento corrigido):
- `teste_fase20.py`: lê o arquivo no formato v3; passa a esperar que a projeção **permaneça** como “provisória” (antes: arquivo removido); cabeçalho de versão 20.2.1.
- `teste_fase201.py`: `aguardando_oficial` → `sem_atualizacao_numerica`; casos “descartada” (sem id, base incerta, prazo) agora verificam o estado `expirada`/descarte com aviso em vez de arquivo removido; fim de corrida sem identidade segura não apaga mais a projeção de outra corrida; sobreposição passa a ser testada.
- `teste_fase202.py`: variação zero com resultado oficial passa a ser `ok_confirmada` (antes: `aguardando_oficial`).

**Regressão:** Fases 2 a 19 (cópias de trabalho) e `testes/teste_fase20`, `201`, `202`, `2021`: todos verdes.

## 6. Limitações e riscos

1. **Nada foi validado no iRacing real.** Sem o `ROTEIRO_VALIDACAO.txt` (teste 7 atualizado) não há homologação.
2. **Confirmação sem fonte:** enquanto nada chamar `confirmar_resultado_oficial`, nenhuma linha real vira “confirmada”; trate o CSV como indício, não como calibração definitiva.
3. **Provisória pode estar contaminada** (outra corrida fora do overlay entre as sessões); o novo ciclo não resolve isso, apenas preserva a chance de corrigir depois.
4. **Capacidade:** com mais de 50 projeções ativas (cenário improvável: exige muitas corridas sem resultado em categorias/usuários distintos) o arquivo cresce além de 50 e só o aviso no log sinaliza; nada é apagado.
5. **Expiração:** provisória que não for confirmada em 60 dias permanece no CSV como provisória (não é removida).
6. **Janela de atualização do iRacing** (quanto tempo até o rating mudar no jogo) é desconhecida: o teste 7 pede que você anote isso.

## 7. Próximos passos

1. Copiar `overlay_iracing.py` e `ov_nucleo.py` (ambos mudaram), rodar `executar_testes.bat` (deve terminar com “TODOS OS TESTES PASSARAM”).
2. Executar o `ROTEIRO_VALIDACAO.txt`, começando pelos testes 1, 7 e 10; enviar `overlay_log.txt`, `comparacao_oficial.csv`, `projecao_pendente.json` e `historico_projecoes.csv`.
3. Somente após a homologação, decidir sobre a Data API (decisões de autenticação e segurança descritas no relatório 20.2) e sobre a Fase 21.
