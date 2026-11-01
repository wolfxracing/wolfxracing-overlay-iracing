"""Testes automatizados da Fase 20.2.1 (ajustes finais): ciclo de vida da projecao de iRating/SR e variacao zero.

  pendente -> provisoria -> confirmada | expirada
  1) funcoes puras (ov_nucleo): variacao positiva, negativa, zero, confirmacao posterior, sessao/usuario divergentes
  2) integracao com a Telemetria: arquivos reais (projecao_pendente.json e comparacao_oficial.csv)

Executar: py -3.12 testes\\teste_fase2021.py   (ou executar_testes.bat). Nao precisa do iRacing aberto.
ATENCAO: dados SIMULADOS. Nao substitui a validacao em sessao real do iRacing (ROTEIRO_VALIDACAO.txt)."""
import os, sys, json, tempfile, copy
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.argv = ["x", "--demo"]
PACOTE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACOTE)
from pathlib import Path
import overlay_iracing as o
import ov_nucleo as n
from PySide6.QtWidgets import QApplication

S = Path(tempfile.mkdtemp(prefix="overlay_testes_2021_"))
o.ARQ_LOG = S / "log.txt"; o.ARQ_CONFIG = S / "cfg_inexistente.json"
o.ARQ_PENDENTE = S / "pendente.json"; o.ARQ_COMPARACAO = S / "comparacao.csv"; o.ARQ_HISTORICO = S / "historico.csv"
o.ARQ_RECORDES = S / "recordes.json"; o.ARQ_PNEUS = S / "pneus.json"; o.ARQ_MAPAS = S / "mapas.json"
app = QApplication([]); o.salvar_config = lambda c: None


def log():
    return o.ARQ_LOG.read_text(encoding="utf-8") if o.ARQ_LOG.exists() else ""


T0 = 1_800_000_000.0                      # "agora" fixo para as funcoes puras
DIA = 86400.0

# ====================================================================================================
# 1) FUNCOES PURAS
# ====================================================================================================
ident_corrida = n.identidade_sessao(1001, "Road", 77, True)
assert ident_corrida["forte"]
reg0 = n.novo_registro(ident_corrida, "Road America", 2000, 40, 3.20, 0.10, False, T0)
assert reg0["estado"] == n.PENDENTE and reg0["versao"] == 3 and reg0["provisoria"] is None and reg0["confirmada"] is None
assert n.ESTADOS == ("pendente", "provisoria", "confirmada", "expirada")

# 1a) pendente -> provisoria (uma vez), preservando TODOS os dados originais da projecao
proxima = n.identidade_sessao(1002, "Road", 77, True)
r1, ev, res, mot = n.avaliar_registro(reg0, proxima, 2033, 3.30, T0 + 3600)
assert (ev, mot) == ("provisoria", "ok") and r1["estado"] == "provisoria" and res["status"] == "provisoria"
for k in ("id", "categoria", "usuario", "pista", "quando", "ir_base", "ir_delta_proj", "sr_base", "sr_delta_proj"):
    assert r1[k] == reg0[k], k                                           # identidade e dados originais preservados
assert r1["provisoria"]["ir_real"] == 33 and reg0["estado"] == "pendente"          # nao muta o registro de entrada
# 1b) novos inicios de sessao NAO comparam de novo (sem duplicar linha) e mantem o registro
r1b, ev, res, mot = n.avaliar_registro(r1, proxima, 2040, 3.40, T0 + 7200)
assert (ev, res, mot) == (None, None, "ja_provisoria") and r1b == r1

# 1c) CONFIRMACAO: variacao positiva, negativa e zero (cada metrica e as duas juntas)
def ro(ir_novo=2052, sr_novo=3.18, **kw):
    d = {"subsession_id": 1001, "cust_id": 77, "ir_antigo": 2000, "ir_novo": ir_novo, "sr_antigo": 3.20, "sr_novo": sr_novo}
    d.update(kw); return d

r2, ev, res, mot = n.aplicar_resultado_oficial(reg0, ro(2052, 3.18), T0 + 100)         # positiva IR / negativa SR
assert (ev, mot) == ("confirmada", "ok_confirmada") and res["status"] == "confirmada"
assert res["ir_real"] == 52 and res["ir_erro"] == 40 - 52 and res["sr_real"] == -0.02 and res["sr_erro"] == round(0.10 + 0.02, 2)
assert not res["variacao_nula"] and r2["estado"] == "confirmada" and r2["confirmada"]["ir_real"] == 52
r, ev, res, mot = n.aplicar_resultado_oficial(reg0, ro(1960, 3.05), T0 + 100)           # negativa nas duas
assert mot == "ok_confirmada" and res["ir_real"] == -40 and res["sr_real"] == -0.15 and not res["variacao_nula"]
r, ev, res, mot = n.aplicar_resultado_oficial(reg0, ro(2000, 3.20), T0 + 100)           # ZERO nas duas: confirmado, nao "aguardando"
assert (ev, mot) == ("confirmada", "ok_confirmada") and res["ir_real"] == 0 and res["sr_real"] == 0.0 and res["variacao_nula"]
assert res["ir_erro"] == 40 and res["sr_erro"] == 0.10 and r["estado"] == "confirmada"
r, ev, res, mot = n.aplicar_resultado_oficial(reg0, ro(2000, 3.31), T0 + 100)           # zero so no iRating
assert mot == "ok_confirmada" and res["ir_real"] == 0 and res["sr_real"] == 0.11 and not res["variacao_nula"]
r, ev, res, mot = n.aplicar_resultado_oficial(reg0, ro(2040, 3.20), T0 + 100)           # zero so no SR
assert mot == "ok_confirmada" and res["ir_real"] == 40 and res["sr_real"] == 0.0 and not res["variacao_nula"]
# so iRating no resultado (SR ausente) ou so SR: confirma o que existe
r, ev, res, mot = n.aplicar_resultado_oficial(reg0, ro(2000, None, sr_antigo=None), T0)
assert mot == "ok_confirmada" and res["ir_real"] == 0 and "sr_real" not in res and res["variacao_nula"]
r, ev, res, mot = n.aplicar_resultado_oficial(reg0, ro(None, 3.30, ir_antigo=None), T0)
assert mot == "ok_confirmada" and res["sr_real"] == 0.10 and "ir_real" not in res

# 1d) resultado incompleto: nem iRating nem SR (ou projecao sem previsao): NAO confirma, projecao segue ativa
for incompleto in (ro(None, None, ir_antigo=None, sr_antigo=None), ro(None, None), {"subsession_id": 1001, "cust_id": 77}):
    r, ev, res, mot = n.aplicar_resultado_oficial(reg0, incompleto, T0)
    assert (ev, res, mot) == (None, None, "resultado_incompleto") and r["estado"] == "pendente"
sem_prev = dict(reg0, ir_delta_proj=None, sr_delta_proj=None)
assert n.aplicar_resultado_oficial(sem_prev, ro(), T0)[3] == "resultado_incompleto"

# 1e) REJEICAO de sessao/usuario divergente: nada muda
for errado in (ro(subsession_id=9999), ro(cust_id=78), ro(subsession_id=None), ro(cust_id="x"), {}, None):
    r, ev, res, mot = n.aplicar_resultado_oficial(reg0, errado, T0)
    assert (ev, res, mot) == (None, None, "resultado_divergente") and r == reg0
    rr, ev, res, mot = n.aplicar_resultado_oficial(r1, errado, T0)                      # tambem para a provisoria
    assert mot == "resultado_divergente" and rr["estado"] == "provisoria" and rr["provisoria"] == r1["provisoria"]

# 1f) CONFIRMACAO POSTERIOR a uma comparacao provisoria: mantem a provisoria anterior e mede a divergencia
r3, ev, res, mot = n.aplicar_resultado_oficial(r1, ro(2052, 3.18), T0 + 9000)
assert (ev, mot) == ("confirmada", "ok_confirmada") and r3["estado"] == "confirmada"
assert res["provisoria_anterior"] == {"ir_real": 33, "sr_real": 0.1}                    # a provisoria viu +33 / +0,10
assert res["divergencia_provisoria"] == {"ir_real": 19, "sr_real": -0.12}               # oficial 52 / -0,02
assert res["ir_real"] == 52 and r3["id"] == r1["id"] and r3["provisoria"] == r1["provisoria"]
# a confirmacao nao depende do jogo (ignora outra corrida no meio) nem de a provisoria ter existido
assert n.aplicar_resultado_oficial(reg0, ro(2052, 3.18), T0)[3] == "ok_confirmada"
# idempotente: confirmar de novo (mesmo resultado ou outro) nao altera nada
r4, ev, res, mot = n.aplicar_resultado_oficial(r3, ro(2099, 3.99), T0 + 20000)
assert (ev, res, mot) == (None, None, "ja_confirmada") and r4 == r3
r5, ev, res, mot = n.avaliar_registro(r3, proxima, 2200, 4.0, T0 + 30000)
assert (ev, res, mot) == (None, None, "ja_confirmada") and r5 == r3                     # inicio de sessao tambem nao mexe

# 1g) avaliar_registro sem resultado oficial: ausencia de atualizacao numerica NAO e resultado
r, ev, res, mot = n.avaliar_registro(reg0, proxima, 2000, 3.20, T0 + 60)
assert (ev, res, mot) == (None, None, "sem_atualizacao_numerica") and r["estado"] == "pendente" and r["observacoes_sem_variacao"] == 1
r, _, _, mot = n.avaliar_registro(r, proxima, 2000, 3.20, T0 + 120)
assert mot == "sem_atualizacao_numerica" and r["observacoes_sem_variacao"] == 2         # contado, limitado pelo prazo (14 d)
assert n.avaliar_registro(reg0, n.identidade_sessao(1001, "Road", 77, True), 2033, 3.3, T0)[3] == "mesma_sessao"
assert n.avaliar_registro(reg0, n.identidade_sessao(1002, "Oval", 77, True), 1300, 2.0, T0)[3] == "categoria_diferente"
assert n.avaliar_registro(reg0, n.identidade_sessao(1002, "Road", 78, True), 2033, 3.3, T0)[3] == "usuario_diferente"
assert n.avaliar_registro(reg0, n.identidade_sessao(1002, None, 77, True), 2033, 3.3, T0)[3] == "categoria_desconhecida"
# o resultado oficial CONFIRMA mesmo quando o jogo ainda nao mostra nada (o motivo antigo "aguardando" sumiu)
assert "aguardando_oficial" not in n.MOTIVOS_TEXTO and "sem_atualizacao_numerica" in n.MOTIVOS_TEXTO

# 1h) EXPIRACAO: pendente 14 d; provisoria 60 d; base incerta; terminal nunca reabre
r, ev, res, mot = n.avaliar_registro(reg0, proxima, 2033, 3.30, T0 + 14 * DIA + 1)
assert (ev, mot) == ("expirada", "expirada") and r["estado"] == "expirada" and r["motivo_expirada"] == "prazo"
r, ev, res, mot = n.avaliar_registro(reg0, proxima, 2033, 3.30, T0 + 13 * DIA)
assert ev == "provisoria"                                                                # ainda dentro do prazo
r, ev, res, mot = n.avaliar_registro(r1, proxima, 2040, 3.4, T0 + 59 * DIA)
assert mot == "ja_provisoria" and r["estado"] == "provisoria"
r, ev, res, mot = n.avaliar_registro(r1, proxima, 2040, 3.4, T0 + 60 * DIA + 1)
assert (ev, mot) == ("expirada", "expirada") and r["estado"] == "expirada" and r["provisoria"] == r1["provisoria"]
inc = dict(reg0, base_incerta=True)
r, ev, res, mot = n.avaliar_registro(inc, proxima, 2033, 3.30, T0 + 60)
assert (ev, mot) == ("expirada", "base_incerta") and r["estado"] == "expirada" and r["motivo_expirada"] == "base_incerta"
expirada = r
assert n.aplicar_resultado_oficial(expirada, ro(), T0)[2:] == (None, "ja_expirada")      # nao e reaberta por resultado tardio
assert n.avaliar_registro(expirada, proxima, 2033, 3.3, T0)[3] == "ja_expirada"
# identidade incompleta no registro (corrompido): expira, nunca compara
assert n.avaliar_registro(dict(reg0, categoria=None), proxima, 2033, 3.3, T0)[1:] == ("expirada", None, "pendente_sem_id")

# 1i) sobreposicao: outra corrida da mesma categoria/usuario invalida a PENDENTE anterior (provisoria/confirmada ficam)
nova = n.novo_registro(n.identidade_sessao(1002, "Road", 77, True), "Watkins Glen", 2033, 20, 3.30, 0.05, False, T0 + 5)
outra_cat = n.novo_registro(n.identidade_sessao(900, "Oval", 77, True), "Daytona", 1300, 10, 2.0, 0.0, False, T0)
outro_usr = n.novo_registro(n.identidade_sessao(901, "Road", 78, True), "Monza", 1500, 10, 2.0, 0.0, False, T0)
lista = n.sobrepor_pendentes([reg0, r3, outra_cat, outro_usr], nova, T0 + 5)
assert [x["estado"] for x in lista] == ["expirada", "confirmada", "pendente", "pendente"]
assert lista[0]["motivo_expirada"] == "sobreposta_por_outra_corrida"
assert n.sobrepor_pendentes([r1], nova, T0)[0]["estado"] == "provisoria"

# 1j) poda: terminais antigos saem; limite de tamanho; ativos nunca saem por idade
velho_conf = dict(r3, estado_desde=T0 - 61 * DIA)
velho_exp = dict(expirada, estado_desde=T0 - 61 * DIA, id="1")
recente_exp = dict(expirada, estado_desde=T0 - 5 * DIA, id="2")
ativo_velho = dict(reg0, quando=T0 - 100 * DIA, id="3")                                  # estado pendente: fica (expira na avaliacao)
assert [x["id"] for x in n.podar([velho_conf, velho_exp, recente_exp, ativo_velho], T0)] == ["2", "3"]
muitos = [dict(expirada, id=str(i), estado_desde=T0 - i) for i in range(n.MAX_REGISTROS + 10)] + [dict(reg0, id="ativo")]
podados = n.podar(muitos, T0)
assert len(podados) == n.MAX_REGISTROS and any(x["id"] == "ativo" for x in podados)
assert not any(x["id"] == str(n.MAX_REGISTROS + 9) for x in podados)                    # saem os terminais mais antigos

# 1j-bis) RETENCAO (Fase 20.2.1, correcao): SO confirmadas/expiradas podem ser removidas; ativas nunca
def fabricar(**qtd):
    """Lista com `qtd` de cada estado; ids unicos; estado_desde crescente (indice maior = mais recente)."""
    lista, k = [], 0
    for estado in ("pendente", "provisoria", "confirmada", "expirada"):
        for _ in range(qtd.get(estado, 0)):
            k += 1
            lista.append(dict(reg0, id="%s-%03d" % (estado[:3], k), estado=estado, estado_desde=T0 - 1000 + k, quando=T0 - 1000 + k))
    return lista

ATIVOS = ("pendente", "provisoria")
def ids(lst): return [x["id"] for x in lst]
def ativos_de(lst): return [x for x in lst if x["estado"] in ATIVOS]
assert n.MAX_REGISTROS == 50

# reproducao do defeito reportado: 51 pendentes -> NENHUMA pode ser removida
m = fabricar(pendente=51)
saida = n.podar(m, T0)
assert ids(saida) == ids(m) and len(saida) == 51 and n.excede_capacidade(saida)
# 50 exatos: nada muda e nao ha excesso
m = fabricar(pendente=50)
assert ids(n.podar(m, T0)) == ids(m) and not n.excede_capacidade(n.podar(m, T0))
m = fabricar(pendente=20, provisoria=15, confirmada=10, expirada=5)                          # 50 mistos
assert ids(n.podar(m, T0)) == ids(m)
# 51 com um terminal: sai SO o terminal (o mais antigo), ativas intactas
for terminal in ("confirmada", "expirada"):
    m = fabricar(pendente=30, provisoria=20, **{terminal: 1})
    saida = n.podar(m, T0)
    assert len(saida) == 50 and ids(ativos_de(saida)) == ids(ativos_de(m)) and not any(x["estado"] == terminal for x in saida)
# 51 com 50 terminais + 1 ativa: a ativa fica; sai o terminal mais antigo
m = fabricar(confirmada=25, expirada=25, pendente=1)
saida = n.podar(m, T0)
mais_antigo = min((x for x in m if x["estado"] not in ATIVOS), key=lambda x: x["estado_desde"])
assert len(saida) == 50 and ids(ativos_de(saida)) == ids(ativos_de(m)) and mais_antigo["id"] not in ids(saida)
# 100 so de ativas (mistas): TODAS preservadas, aviso de capacidade
for qtd in (dict(pendente=100), dict(provisoria=100), dict(pendente=60, provisoria=40), dict(pendente=1, provisoria=99)):
    m = fabricar(**qtd)
    saida = n.podar(m, T0)
    assert ids(saida) == ids(m) and len(saida) == 100 and n.excede_capacidade(saida), qtd
# 100 com 50 ativas + 50 terminais: ficam as 50 ativas, saem todos os terminais
m = fabricar(pendente=30, provisoria=20, confirmada=25, expirada=25)
saida = n.podar(m, T0)
assert len(saida) == 50 and ids(saida) == ids(ativos_de(m)) and not n.excede_capacidade(saida)
# 100 com 20 ativas + 80 terminais: ficam as 20 ativas + os 30 terminais MAIS RECENTES
m = fabricar(pendente=10, provisoria=10, confirmada=40, expirada=40)
saida = n.podar(m, T0)
termin_m = [x for x in m if x["estado"] not in ATIVOS]
esperado = ids(ativos_de(m)) + ids(sorted(termin_m, key=lambda x: x["estado_desde"])[-30:])
assert len(saida) == 50 and sorted(ids(saida)) == sorted(esperado) and ids(ativos_de(saida)) == ids(ativos_de(m))
# 100 com 49 ativas + 51 terminais: 49 ativas + 1 terminal (o mais recente)
m = fabricar(pendente=25, provisoria=24, confirmada=26, expirada=25)
saida = n.podar(m, T0)
mais_recente = max((x for x in m if x["estado"] not in ATIVOS), key=lambda x: x["estado_desde"])
assert len(saida) == 50 and sorted(ids(saida)) == sorted(ids(ativos_de(m)) + [mais_recente["id"]])
# 100 com 51 ativas + 49 terminais: todas as ativas ficam (51), nenhum terminal, excesso sinalizado
m = fabricar(pendente=26, provisoria=25, confirmada=24, expirada=25)
saida = n.podar(m, T0)
assert ids(saida) == ids(ativos_de(m)) and len(saida) == 51 and n.excede_capacidade(saida)
# idade: terminal com mais de 60 dias sai mesmo abaixo do limite; ativa muito antiga NUNCA sai por idade
m = fabricar(pendente=2, provisoria=2, confirmada=2, expirada=2)
for x in m: x["estado_desde"] = T0 - 400 * DIA; x["quando"] = T0 - 400 * DIA
saida = n.podar(m, T0)
assert ids(saida) == ids(ativos_de(m)) and len(saida) == 4
# propriedades: idempotente, preserva a ordem, nao muta a entrada, estado desconhecido e tratado como ativo
m = fabricar(pendente=40, provisoria=10, confirmada=30, expirada=30)
copia = copy.deepcopy(m)
um = n.podar(m, T0)
assert m == copia and n.podar(um, T0) == um
ordem = {i: k for k, i in enumerate(ids(m))}
assert [ordem[i] for i in ids(um)] == sorted(ordem[i] for i in ids(um))
estranho = fabricar(pendente=50) + [dict(reg0, id="estranho", estado="algo_novo")]
assert "estranho" in ids(n.podar(estranho, T0)) and len(n.podar(estranho, T0)) == 51
# nenhum dos cenarios acima perde ativa: varredura sistematica de combinacoes 0..100
for p_ in (0, 1, 25, 49, 50, 51, 75):
    for pv in (0, 1, 24, 50, 60):
        for c_ in (0, 30, 60):
            m = fabricar(pendente=p_, provisoria=pv, confirmada=c_, expirada=c_ // 2)
            saida = n.podar(m, T0)
            assert ids(ativos_de(saida)) == ids(ativos_de(m)), (p_, pv, c_)                  # ZERO ativas perdidas
            assert len(saida) == max(min(len(m), n.MAX_REGISTROS), len(ativos_de(m))), (p_, pv, c_)
            assert n.excede_capacidade(saida) == (len(ativos_de(m)) > n.MAX_REGISTROS)

# 1k) migracao de arquivos
lst, av = n.migrar_arquivo({"projecoes": [reg0, {"sem": "id"}]}, T0)
assert lst == [reg0] and av == []
v2 = {"versao": 2, "quando": T0 - DIA, "pista": "X", "id": "55", "categoria": "road", "usuario": 77, "base_incerta": False,
      "ir_base": 2000, "ir_delta_proj": 40, "sr_base": 3.2, "sr_delta_proj": 0.1}
lst, av = n.migrar_arquivo(v2, T0)
assert len(lst) == 1 and lst[0]["estado"] == "pendente" and lst[0]["versao"] == 3 and lst[0]["quando"] == T0 - DIA and av
v1 = {"quando": T0, "pista": "X", "ir_base": 2000, "ir_delta_proj": 40}
lst, av = n.migrar_arquivo(v1, T0)
assert lst == [] and "descartada" in av[0]
assert n.migrar_arquivo({}, T0) == ([], []) and n.migrar_arquivo(None, T0) == ([], []) and n.migrar_arquivo([], T0) == ([], [])
print("1) ciclo de vida (funcoes puras): positiva, negativa, zero, provisoria->confirmada, divergentes, prazos, retencao 50/51/100 OK")

# ====================================================================================================
# 2) INTEGRACAO COM A TELEMETRIA (arquivos reais)
# ====================================================================================================
def limpar():
    for f in S.glob("*"):
        if f.is_file(): f.unlink()

def config(tel, sub, cat, oficial=True):
    tel._subsessao, tel._categoria, tel._oficial = sub, cat, oficial

def estados(tel):
    return [(r["id"], r["estado"]) for r in tel._ler_projecoes()]

def linhas_csv():
    return o.ARQ_COMPARACAO.read_text(encoding="utf-8-sig").splitlines()

def campos(linha):
    cab = linhas_csv()[0].split(";")
    return dict(zip(cab, linha.split(";")))

def fim_de_corrida(tel, sub, ir_base=2000, ir_delta=40, sr_base=3.20, sr_delta=0.10, incerta=False, pista="Road America"):
    """Simula o fim de uma corrida oficial (grava a projecao como PENDENTE)."""
    config(tel, sub, "Road", True)
    tel._nome_pista = pista; tel._sessao_registrada = None
    res = {"tipo": "CORRIDA", "ir": {"novo": ir_base + ir_delta, "delta": ir_delta, "pos": 1, "n": 12},
           "sr": {"novo": sr_base + sr_delta, "delta": sr_delta}, "curvas": 50.0, "inc": 2, "oficial": True}
    base = {"ir": ir_base, "sr": sr_base, "letra": "A", "incerta": incerta}
    tel._registrar_historico(("c", sub), res, {"usuario_id": 77, "marca": "X", "classe_nome": "GT3"}, base)

def resultado(sub=1001, ir_novo=2052, sr_novo=3.18, **kw):
    d = {"subsession_id": sub, "cust_id": 77, "ir_antigo": 2000, "ir_novo": ir_novo, "sr_antigo": 3.20, "sr_novo": sr_novo}
    d.update(kw); return d

# 2a) fluxo completo: pendente -> provisoria (CSV 1 linha) -> varias sessoes depois (nada duplica) -> confirmada (linha SUBSTITUIDA)
limpar(); tel = o.Telemetria(demo=True)
fim_de_corrida(tel, 1001)
assert estados(tel) == [("1001", "pendente")] and not o.ARQ_COMPARACAO.exists()
assert json.loads(o.ARQ_PENDENTE.read_text())["versao"] == 3 and not list(S.glob("*.tmp"))        # gravacao atomica
eu = {"irating": 2033, "sr": 3.30, "usuario_id": 77}
config(tel, 1002, "Road")
assert tel._verificar_oficial(eu) == "ok" and estados(tel) == [("1001", "provisoria")]
assert len(linhas_csv()) == 2 and campos(linhas_csv()[1])["status"] == "provisoria" and campos(linhas_csv()[1])["ir_oficial"] == "33"
original = json.loads(o.ARQ_PENDENTE.read_text())["projecoes"][0]
assert original["ir_base"] == 2000 and original["ir_delta_proj"] == 40 and original["sr_delta_proj"] == 0.1 and original["usuario"] == 77
for sub in (1003, 1004, 1005):                                                  # novas sessoes: sem nova linha, registro intacto
    config(tel, sub, "Road")
    assert tel._verificar_oficial({"irating": 2100, "sr": 3.5, "usuario_id": 77}) == "ja_provisoria"
assert len(linhas_csv()) == 2 and json.loads(o.ARQ_PENDENTE.read_text())["projecoes"][0]["provisoria"] == original["provisoria"]
assert tel._aguardando_oficial is False                                          # a base da proxima corrida NAO e incerta
assert tel.confirmar_resultado_oficial(resultado(ir_novo=2052, sr_novo=3.18)) == "ok_confirmada"
assert estados(tel) == [("1001", "confirmada")]
assert len(linhas_csv()) == 2, linhas_csv()                                      # SUBSTITUIU, nao duplicou
c = campos(linhas_csv()[1])
assert c["corrida_id"] == "1001" and c["status"] == "confirmada" and c["ir_oficial"] == "52" and c["ir_erro"] == "-12"
assert c["sr_oficial"] == "-0.02" and c["sr_erro"] == "0.12"
assert "confirmada pelo resultado oficial" in log() and "divergencia_provisoria" in log()
# idempotente (mesmo resultado, outro resultado, depois de reiniciar a leitura): nenhuma linha nova
assert tel.confirmar_resultado_oficial(resultado(ir_novo=2052, sr_novo=3.18)) == "ja_confirmada"
assert tel.confirmar_resultado_oficial(resultado(ir_novo=2300, sr_novo=4.0)) == "ja_confirmada"
config(tel, 1006, "Road"); tel._verificar_oficial(eu)
assert len(linhas_csv()) == 2 and campos(linhas_csv()[1])["ir_oficial"] == "52"
assert not list(S.glob("*.tmp"))

# 2b) confirmacao SEM comparacao provisoria previa (resultado chega antes de qualquer leitura no jogo)
limpar(); tel = o.Telemetria(demo=True); fim_de_corrida(tel, 1001)
assert tel.confirmar_resultado_oficial(resultado(ir_novo=1965, sr_novo=3.05)) == "ok_confirmada"      # negativa
assert estados(tel) == [("1001", "confirmada")] and len(linhas_csv()) == 2
c = campos(linhas_csv()[1]); assert c["status"] == "confirmada" and c["ir_oficial"] == "-35" and c["sr_oficial"] == "-0.15"

# 2c) VARIACAO ZERO pelo resultado oficial: confirmada (nao fica aguardando) e a base da proxima corrida NAO fica incerta
limpar(); tel = o.Telemetria(demo=True); fim_de_corrida(tel, 1001)
config(tel, 1002, "Road")
assert tel._verificar_oficial({"irating": 2000, "sr": 3.20, "usuario_id": 77}) == "sem_atualizacao_numerica"
assert tel._aguardando_oficial is True and not o.ARQ_COMPARACAO.exists()          # ausencia de atualizacao != resultado oficial
assert estados(tel) == [("1001", "pendente")] and "SEM atualizacao numerica" in log()
assert tel.confirmar_resultado_oficial(resultado(ir_novo=2000, sr_novo=3.20)) == "ok_confirmada"
assert estados(tel) == [("1001", "confirmada")]
c = campos(linhas_csv()[1]); assert c["status"] == "confirmada" and c["ir_oficial"] == "0" and c["sr_oficial"] == "0.0"
assert c["ir_erro"] == "40" and "ZERO confirmada" in log()
config(tel, 1003, "Road"); assert tel._verificar_oficial({"irating": 2000, "sr": 3.20, "usuario_id": 77}) == "ja_confirmada"
assert tel._aguardando_oficial is False                                            # nada mais aguardando

# 2d) provisoria que depois o resultado oficial mostra ZERO (o jogo tinha mudado por outra corrida): linha substituida por 0
limpar(); tel = o.Telemetria(demo=True); fim_de_corrida(tel, 1001)
config(tel, 1002, "Road"); assert tel._verificar_oficial(eu) == "ok" and campos(linhas_csv()[1])["status"] == "provisoria"
assert tel.confirmar_resultado_oficial(resultado(ir_novo=2000, sr_novo=3.31)) == "ok_confirmada"
c = campos(linhas_csv()[1]); assert len(linhas_csv()) == 2 and c["ir_oficial"] == "0" and c["sr_oficial"] == "0.11" and c["status"] == "confirmada"

# 2e) REJEICAO de sessao/usuario divergente: nada muda (nem arquivo, nem CSV)
limpar(); tel = o.Telemetria(demo=True); fim_de_corrida(tel, 1001)
config(tel, 1002, "Road"); tel._verificar_oficial(eu)
antes_json, antes_csv = o.ARQ_PENDENTE.read_text(), o.ARQ_COMPARACAO.read_text(encoding="utf-8-sig")
assert tel.confirmar_resultado_oficial(resultado(sub=9999)) == "resultado_divergente"          # outra corrida
assert tel.confirmar_resultado_oficial(resultado(cust_id=78)) == "resultado_divergente"        # outro usuario
assert tel.confirmar_resultado_oficial({}) == "resultado_divergente" and tel.confirmar_resultado_oficial(None) == "resultado_divergente"
assert tel.confirmar_resultado_oficial(resultado(ir_novo=None, sr_novo=None, ir_antigo=None, sr_antigo=None)) == "resultado_incompleto"
assert o.ARQ_PENDENTE.read_text() == antes_json and o.ARQ_COMPARACAO.read_text(encoding="utf-8-sig") == antes_csv
assert estados(tel) == [("1001", "provisoria")]

# 2f) duas corridas em aberto: o resultado so confirma a sua; nao ha contaminacao entre elas
limpar(); tel = o.Telemetria(demo=True)
fim_de_corrida(tel, 1001); config(tel, 1002, "Road"); tel._verificar_oficial(eu)                 # 1001 -> provisoria
fim_de_corrida(tel, 1002, ir_base=2033, ir_delta=20, sr_base=3.30, sr_delta=0.05, pista="Watkins Glen")
assert estados(tel) == [("1001", "provisoria"), ("1002", "pendente")]
assert tel.confirmar_resultado_oficial(resultado(sub=1002, ir_antigo=2033, ir_novo=2051, sr_antigo=3.30, sr_novo=3.36)) == "ok_confirmada"
assert estados(tel) == [("1001", "provisoria"), ("1002", "confirmada")]
linhas = linhas_csv()[1:]
assert sorted(campos(l)["corrida_id"] for l in linhas) == ["1001", "1002"] and len(linhas) == 2
assert {campos(l)["corrida_id"]: campos(l)["status"] for l in linhas} == {"1001": "provisoria", "1002": "confirmada"}

# 2g) outra corrida da mesma categoria/usuario com a anterior ainda PENDENTE: a pendente e marcada "expirada" (sobreposta)
limpar(); tel = o.Telemetria(demo=True)
fim_de_corrida(tel, 1001); fim_de_corrida(tel, 1002, ir_base=2000, ir_delta=15, incerta=True)
assert estados(tel) == [("1001", "expirada"), ("1002", "pendente")]
assert json.loads(o.ARQ_PENDENTE.read_text())["projecoes"][0]["motivo_expirada"] == "sobreposta_por_outra_corrida"
assert tel.confirmar_resultado_oficial(resultado(sub=1001)) == "ja_expirada" and not o.ARQ_COMPARACAO.exists()
# a mesma corrida registrada de novo (reabrir o overlay no fim): substitui, nao duplica
fim_de_corrida(tel, 1002, ir_base=2000, ir_delta=16)
assert [e for e in estados(tel) if e[0] == "1002"] == [("1002", "pendente")]
# base incerta: ao iniciar a proxima sessao a projecao expira sem comparar
limpar(); tel = o.Telemetria(demo=True); fim_de_corrida(tel, 1001, incerta=True)
config(tel, 1002, "Road"); assert tel._verificar_oficial(eu) == "base_incerta" and estados(tel) == [("1001", "expirada")]
assert not o.ARQ_COMPARACAO.exists()

# 2h) expiracao por prazo no arquivo (pendente 14 d, provisoria 60 d)
limpar(); tel = o.Telemetria(demo=True); fim_de_corrida(tel, 1001)
dados = json.loads(o.ARQ_PENDENTE.read_text()); dados["projecoes"][0]["quando"] = o.time.time() - 15 * DIA
o.ARQ_PENDENTE.write_text(json.dumps(dados)); config(tel, 1002, "Road")
assert tel._verificar_oficial(eu) == "expirada" and estados(tel) == [("1001", "expirada")] and "expirada" in log()
assert tel.confirmar_resultado_oficial(resultado()) == "ja_expirada" and not o.ARQ_COMPARACAO.exists()
limpar(); tel = o.Telemetria(demo=True); fim_de_corrida(tel, 1001); config(tel, 1002, "Road"); tel._verificar_oficial(eu)
dados = json.loads(o.ARQ_PENDENTE.read_text()); dados["projecoes"][0]["quando"] = o.time.time() - 61 * DIA
o.ARQ_PENDENTE.write_text(json.dumps(dados)); config(tel, 1003, "Road")
assert tel._verificar_oficial(eu) == "expirada" and estados(tel) == [("1001", "expirada")]
assert campos(linhas_csv()[1])["status"] == "provisoria" and len(linhas_csv()) == 2            # a linha provisoria permanece, sem duplicar

# 2i) migracao do arquivo da Fase 20.1/20.2 (dict unico) e da Fase 20 (sem id); arquivo ilegivel nao derruba
limpar(); tel = o.Telemetria(demo=True)
v2 = {"versao": 2, "quando": o.time.time(), "pista": "Road America", "id": "1001", "categoria": "road", "usuario": 77,
      "base_incerta": False, "ir_base": 2000, "ir_delta_proj": 40, "sr_base": 3.2, "sr_delta_proj": 0.1}
o.ARQ_PENDENTE.write_text(json.dumps(v2))
config(tel, 1002, "Road"); assert tel._verificar_oficial(eu) == "ok"
assert json.loads(o.ARQ_PENDENTE.read_text())["versao"] == 3 and estados(tel) == [("1001", "provisoria")] and "migrada" in log()
o.ARQ_PENDENTE.write_text(json.dumps({"quando": o.time.time(), "ir_base": 2000, "ir_delta_proj": 40}))
assert tel._verificar_oficial(eu) == "sem_pendente" and estados(tel) == [] and "descartada sem comparar" in log()
o.ARQ_PENDENTE.write_text("{ isto nao e json")
assert tel._verificar_oficial(eu) == "sem_pendente" and tel.confirmar_resultado_oficial(resultado()) == "resultado_divergente"
assert o.ARQ_PENDENTE.read_text() == "{ isto nao e json" and "ilegivel" in log()                # nada foi destruido

# 2j) fim de corrida sem identificacao segura NAO apaga as projecoes ja guardadas
limpar(); tel = o.Telemetria(demo=True); fim_de_corrida(tel, 1001)
fim_de_corrida(tel, 0)                                                            # offline (SubSessionID 0)
assert estados(tel) == [("1001", "pendente")] and "sem identificacao segura" in log()

# 2k) CSV de formato antigo continua sendo preservado; a substituicao por corrida_id respeita o novo formato
limpar(); tel = o.Telemetria(demo=True)
o.ARQ_COMPARACAO.write_text("data;pista;ir_projetado;ir_oficial;ir_erro;sr_projetado;sr_oficial;sr_erro\n2026-01-01 10:00;X;1;2;3;4;5;6\n", encoding="utf-8-sig")
fim_de_corrida(tel, 1001); assert tel.confirmar_resultado_oficial(resultado()) == "ok_confirmada"
antigos = list(S.glob("comparacao_formato_antigo*.csv"))
assert len(antigos) == 1 and "2026-01-01 10:00;X;1;2;3;4;5;6" in antigos[0].read_text(encoding="utf-8-sig")
assert len(linhas_csv()) == 2 and linhas_csv()[0].split(";")[4] == "status"

# 2l) retencao na Telemetria: 51 ativas (usuarios diferentes) ficam todas no arquivo e o excesso e avisado no log
limpar(); tel = o.Telemetria(demo=True)
def ativa(i, estado="pendente", usuario=None):
    return n.novo_registro({"id": str(5000 + i), "categoria": "road", "usuario": usuario or (100 + i), "oficial": True, "forte": True},
                           "Pista %d" % i, 2000, 10, 3.0, 0.1, False, o.time.time() - 100 + i) | {"estado": estado}
tel._gravar_projecoes([ativa(i, "pendente" if i % 2 else "provisoria") for i in range(50)])
assert len(tel._ler_projecoes()) == 50 and "nenhuma foi removida" not in log()               # 50: sem aviso
fim_de_corrida(tel, 7001)                                                                      # 51a ativa (usuario 77, outra das existentes)
saida = tel._ler_projecoes()
assert len(saida) == 51 and {str(5000 + i) for i in range(50)} <= {r["id"] for r in saida} and "7001" in {r["id"] for r in saida}
assert "nenhuma foi removida" in log() and "51 projecoes ativas" in log()
# ate 100 ativas: continua sem perder nenhuma; confirmar uma delas libera espaco e a poda so toca nela depois da retencao
tel._gravar_projecoes([ativa(i) for i in range(100)])
assert len(tel._ler_projecoes()) == 100
alvo = ativa(3)
assert tel.confirmar_resultado_oficial({"subsession_id": "5003", "cust_id": 103, "ir_antigo": 2000, "ir_novo": 2010,
                                        "sr_antigo": 3.0, "sr_novo": 3.1}) == "ok_confirmada"
# acima do limite, a confirmada e o UNICO registro elegivel: sai na hora; as 99 ativas ficam e a linha do CSV foi gravada
estado = {r["id"]: r["estado"] for r in tel._ler_projecoes()}
assert len(estado) == 99 and "5003" not in estado and set(estado.values()) == {"pendente"}
assert any(l.split(";")[1] == "5003" for l in linhas_csv()[1:])
# repetir o resultado de uma corrida ja podada nao duplica nada
assert tel.confirmar_resultado_oficial({"subsession_id": "5003", "cust_id": 103, "ir_antigo": 2000, "ir_novo": 2010,
                                        "sr_antigo": 3.0, "sr_novo": 3.1}) == "resultado_divergente"
assert sum(l.split(";")[1] == "5003" for l in linhas_csv()[1:]) == 1
# _verificar_oficial com 99 ativas nao perde nenhuma (so muda de estado)
config(tel, 9000, "Road"); tel._verificar_oficial({"irating": 2000, "sr": 3.0, "usuario_id": 77})
assert len(tel._ler_projecoes()) == 99

print("2) ciclo de vida (Telemetria + arquivos): fluxo, zero, divergentes, expiracao, migracao OK")

print("TODOS OS TESTES DA FASE 20.2.1 PASSARAM")
print("(dados SIMULADOS: nao substitui a validacao em sessao real; arquivos temporarios: %s)" % S)
