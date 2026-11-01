# Histórico de versões

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e [SemVer](https://semver.org/lang/pt-BR/).

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
