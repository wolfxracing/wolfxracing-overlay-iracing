# Overlay iRacing — Relatório da Fase 20.2

**Arquivos alterados:** `overlay_iracing.py` e `ov_nucleo.py` (mais `testes/teste_fase202.py` novo, `LEIA-ME.txt`, `ROTEIRO_VALIDACAO.txt` e `executar_testes.bat`).
**Situação:** implementado e testado **apenas com dados simulados**. A homologação real continua **obrigatória** e não foi feita. A Fase 21 não foi iniciada.

## 1. Resumo executivo

- **iRating/SR:** a comparação projeção × oficial passa a sair sempre **provisória**. Só poderá ser **confirmada** quando houver o resultado oficial da mesma corrida (SubSessionID) e do mesmo usuário; esse caminho existe como contrato testado, mas **não está ligado a nenhuma fonte** (sem rede, sem alterar a arquitetura).
- **Combustível:** o campo `reabastecer` deixou de dividir o total igualmente. Ele agora é a quantidade da **primeira parada**: capacidade do tanque menos o combustível projetado na chegada aos boxes (parada “até o topo”) quando ainda há outra parada depois; apenas o que falta quando é a única/última.
- 12 janelas, 3 perfis, layouts e demais funcionalidades preservados.

## 2. Item 1 — Comparação de iRating e Safety Rating

**Problema confirmado:** a comparação é a diferença entre o valor visto no jogo antes e depois. Categoria, usuário e sessão diferente reduzem o risco, mas não provam que **só** a corrida projetada alterou o rating (outra corrida fora do overlay, ajuste do iRacing etc.). A 20.1 registrava a linha como se fosse definitiva.

**Solução:**
- `avaliar_comparacao()` devolve `status = "provisoria"` em toda comparação por diferença.
- Coluna `status` no `comparacao_oficial.csv` e aviso no log (“PROVISORIA: sem confirmacao pelo SubSessionID”). O CSV no formato da 20.1 é preservado como `comparacao_oficial_formato_antigo.csv`.
- Novo parâmetro opcional `resultado_oficial` (`resultado_confere()`): só com `subsession_id` e `cust_id` iguais aos da projeção o status vira `confirmada`, e os valores reais vêm do resultado oficial, não da diferença. Resultado de outra corrida/usuário é rejeitado (`resultado_divergente`).

### Avaliação da integração futura com a Data API do iRacing (nada implementado)

| Aspecto | Avaliação |
|---|---|
| Valor | Alto: o resultado de uma corrida por `subsession_id` traz, por piloto, `oldi_rating`, `newi_rating`, `old_sub_level`, `new_sub_level` e `cust_id` — exatamente o que falta para a confirmação. |
| Confiança nesta informação | **Média.** Os nomes dos campos vieram dos tipos de uma biblioteca de terceiros ([iracing-node-api](https://app.unpkg.com/iracing-node-api@1.0.7/files/dist/mjs/types.d.ts)); não consultei a documentação oficial. A escala de `*_sub_level` (SR) precisa ser confirmada antes de converter. |
| Autenticação | Ponto crítico. Uma biblioteca Python ([iracingdataapi](https://pypi.org/project/iracingdataapi/)) descreve login por usuário/senha (contas com 2FA não funcionam) ou token OAuth2 sem renovação automática. **Não validei as regras atuais de autenticação do iRacing**; precisam ser confirmadas na documentação oficial antes de qualquer decisão. |
| Segurança | Guardar credenciais no PC de jogo é risco a decidir (você, como gestor de TI): conta dedicada? token com validade curta? |
| Operação | Há limite de requisições, latência até o resultado ser publicado e dependência de rede; falha deve manter a comparação “provisória”, nunca derrubar o overlay. |
| Arquitetura sugerida | Módulo opcional e **desligado por padrão** (ex.: `ov_dataapi.py`), executado fora do ciclo de 33 ms, uma consulta por projeção pendente, devolvendo o dicionário do contrato. Nenhuma mudança no núcleo: `avaliar_comparacao(..., resultado_oficial=...)` já aceita. |
| Decisões necessárias | Método de autenticação aceitável para a empresa; onde guardar o segredo; se vale o esforço (a comparação só calibra o modelo de projeção). |

**Recomendação:** manter provisório agora; tratar a Data API como projeto próprio, depois de validar a escala dos campos e a autenticação com uma consulta manual de teste.

## 3. Item 2 — Combustível por parada

**Problema confirmado:** o planejamento (Fase 20.1) assume reabastecimento até o topo, mas `reabastecer` era `total / paradas`. Exemplo: 30 L no tanque, tanque de 60 L, 3 L/volta, margem de 2 voltas, 46 voltas ⇒ 3 paradas, total 114 L. O painel indicava **38 L**; na chegada ao box (27 L) só cabiam **33 L**. Em outros casos, divisão igual também sub-reabastece paradas intermediárias.

**Solução:** `detalhar_paradas()` calcula o cronograma:
- combustível projetado na chegada à 1ª parada = nível − consumo × (resto da volta + voltas até a parada);
- litros = capacidade − chegada (até o topo) nas paradas intermediárias; a última recebe só o restante, de modo que a soma é sempre o total e a bandeirada termina exatamente com a margem;
- `reabastecer` = 1ª parada na primeira volta da janela; `parada1` traz volta, chegada, litros, “até o topo” e os litros se parar na última volta da janela (chega mais vazio); `plano` lista todas as paradas;
- cada linha MED/MAX/MIN da tabela usa a mesma regra; `primeira_parada` também vai para o cálculo da janela Voltas;
- tela: rótulo “COLOCAR NA V22” (+ “· ATÉ O TOPO” quando enche); sem plano viável continua “--”.

O número mínimo de paradas e a janela (Fase 20.1) não mudaram.

## 4. Testes executados (dados simulados)

- **`testes/teste_fase202.py` (novo):**
  - Item 1: status provisória/confirmada, resultado de outra corrida/usuário rejeitado, resultado confirmado independe da sessão atual, CSV/log com status, CSV da 20.1 preservado.
  - Item 2: caso 38 L × 33 L; uma parada; faixa na janela; capacidade desconhecida; sem parada; sem plano; faixa Voltas; **4.400 casos sorteados executados volta a volta** (soma de litros = total, nunca acima da capacidade disponível, chegada ≥ margem em cada parada, bandeirada = margem, paradas intermediárias cheias, nº de paradas igual ao da 20.1); linhas MED/MAX/MIN; textos desenhados na janela.
- **`teste_fase201.py` e `teste_fase20.py`:** ajustados só onde codificavam o comportamento corrigido (cabeçalho do CSV, divisão igual, versão no log). **Regressão das Fases 2 a 20: verde** (Fase 17 ajustada no item de divisão igual).

## 5. Limitações

1. **Nada foi validado no iRacing real.** Sem a execução do `ROTEIRO_VALIDACAO.txt` (testes 7 e 10 atualizados) não há homologação.
2. **Capacidade:** o painel usa a capacidade informada pelo SDK. Regras da série (limite de abastecimento, taxa de reabastecimento, tempo de box) não são modeladas; se o limite real for menor, o valor “até o topo” pode não ser aceito.
3. **Chegada aos boxes:** o cálculo assume a entrada nos boxes na passagem pela linha; o box fica a alguma distância dela, e o consumo até lá pode diferir em fração de volta (a margem cobre).
4. **Projeção:** consumo constante; as paradas posteriores à primeira são projeção e se recalculam a cada volta.
5. **Comparação provisória:** as linhas do CSV são indício, não calibração definitiva, enquanto não houver confirmação oficial.
6. Testes rodaram em Python 3.13 no ambiente de desenvolvimento; o alvo é Python 3.12.

## 6. Recomendação e próximos passos

1. Copiar os dois arquivos, rodar `executar_testes.bat` (“TODOS OS TESTES PASSARAM”).
2. Executar a homologação real: testes 3, 7, 10, 11 e 12 do roteiro. No teste 10, conferir se o valor “até o topo” é aceito pelo iRacing; no teste 7, confirmar `status = provisoria` e comparar com o resultado no site do iRacing.
3. Decidir, depois da homologação, se a Data API entra como projeto separado (decisões na seção 2).
