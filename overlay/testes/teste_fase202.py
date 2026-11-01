"""Testes automatizados da Fase 20.2: (1) comparacao de iRating/SR PROVISORIA x confirmada; (2) litros por parada.
Executar: py -3.12 testes\\teste_fase202.py   (ou executar_testes.bat). Nao precisa do iRacing aberto.

ATENCAO: dados SIMULADOS. Nao substitui a validacao em sessao real do iRacing (ROTEIRO_VALIDACAO.txt)."""
import os, sys, json, math, random, tempfile
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.argv = ["x", "--demo"]
PACOTE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACOTE)
from pathlib import Path
import overlay_iracing as o
import ov_nucleo as n
from PySide6.QtGui import QPainter, QImage
from PySide6.QtWidgets import QApplication

S = Path(tempfile.mkdtemp(prefix="overlay_testes_202_"))
o.ARQ_LOG = S / "log.txt"; o.ARQ_CONFIG = S / "cfg_inexistente.json"
o.ARQ_PENDENTE = S / "pendente.json"; o.ARQ_COMPARACAO = S / "comparacao.csv"; o.ARQ_HISTORICO = S / "historico.csv"
o.ARQ_RECORDES = S / "recordes.json"; o.ARQ_PNEUS = S / "pneus.json"; o.ARQ_MAPAS = S / "mapas.json"
app = QApplication([]); o.salvar_config = lambda c: None
cfg = o.carregar_config()


def log():
    return o.ARQ_LOG.read_text(encoding="utf-8") if o.ARQ_LOG.exists() else ""


class Gravador(QPainter):
    def __init__(self, *a):
        super().__init__(*a); self.textos = []
    def drawText(self, *args):
        self.textos.append(next((x for x in args if isinstance(x, str)), ""))
        return super().drawText(*args)


def desenhar(janela, dados):
    img = QImage(janela.tamanho()[0] * 2, janela.tamanho()[1] * 2, QImage.Format_ARGB32); img.fill(0)
    g = Gravador(img)
    janela._pintor = lambda: (g.scale(janela.escala_x, janela.escala_y), g)[1]
    janela.dados = dados; janela.paintEvent(None); g.end()
    return g.textos


# ====================================================================================================
# 1) iRATING / SR: comparacao PROVISORIA ate haver resultado oficial confirmado pelo SubSessionID
# ====================================================================================================
pend = {"versao": 2, "id": "1001", "categoria": "road", "usuario": 77, "ir_base": 2000, "ir_delta_proj": 40,
        "sr_base": 3.20, "sr_delta_proj": 0.10}
atual = n.identidade_sessao(1002, "Road", 77, True)

# 1a) pela diferenca dos valores vistos no jogo: SEMPRE provisoria
res, mot = n.avaliar_comparacao(pend, atual, 2033, 3.30)
assert mot == "ok" and res["status"] == n.STATUS_PROVISORIA == "provisoria"
assert "PROVISORIA" in n.MOTIVOS_TEXTO["ok"]
assert "status" in res and res["ir_real"] == 33 and res["ir_erro"] == 7                    # numeros inalterados

# 1b) resultado oficial da MESMA corrida e usuario: confirmada; os valores vem do resultado, nao da diferenca
ro = {"subsession_id": 1001, "cust_id": 77, "ir_antigo": 2000, "ir_novo": 2052, "sr_antigo": 3.20, "sr_novo": 3.18}
assert n.resultado_confere(pend, ro)
res, mot = n.avaliar_comparacao(pend, atual, 2033, 3.30, resultado_oficial=ro)
assert mot == "ok_confirmada" and res["status"] == "confirmada"
assert res["ir_real"] == 52 and res["ir_erro"] == 40 - 52 and res["sr_real"] == -0.02       # ignora outra corrida no meio (2033)
# mesmo que a categoria/sessao atual nao sirvam, o resultado oficial confirmado ja basta (nao depende do jogo)
res, mot = n.avaliar_comparacao(pend, n.identidade_sessao(1003, "Oval", 77, True), 1350, 2.1, resultado_oficial=ro)
assert mot == "ok_confirmada" and res["ir_real"] == 52

# 1c) resultado de OUTRA corrida ou OUTRO usuario nunca confirma
for errado in (dict(ro, subsession_id=9999), dict(ro, cust_id=78), dict(ro, subsession_id=None), dict(ro, cust_id="x"), {}):
    assert not n.resultado_confere(pend, errado)
    assert n.avaliar_comparacao(pend, atual, 2033, 3.30, resultado_oficial=errado) == (None, "resultado_divergente")
assert not n.resultado_confere(None, ro) and not n.resultado_confere(pend, None)
assert n.avaliar_comparacao(None, atual, 1, 1, resultado_oficial=ro) == (None, "sem_pendente")
# Fase 20.2.1: variacao ZERO com o resultado oficial da mesma corrida e resultado CONFIRMADO (nao fica aguardando)
res0, mot0 = n.avaliar_comparacao(pend, atual, 2000, 3.20, resultado_oficial=dict(ro, ir_novo=2000, sr_novo=3.20))
assert mot0 == "ok_confirmada" and res0["status"] == "confirmada" and res0["ir_real"] == 0 and res0["sr_real"] == 0.0 and res0["variacao_nula"]
assert n.avaliar_comparacao(pend, atual, 2033, 3.3, resultado_oficial=None)[1] == "ok"       # sem resultado: comportamento da 20.1
assert "ok_confirmada" in n.MOTIVOS_TEXTO and "resultado_divergente" in n.MOTIVOS_TEXTO

# 1d) integracao: CSV e log marcam o status; hoje (sem Data API) toda comparacao real sai "provisoria"
tel = o.Telemetria(demo=True)
tel._subsessao, tel._categoria, tel._oficial = 1002, "Road", True
o.ARQ_PENDENTE.write_text(json.dumps(dict(pend, quando=o.time.time(), pista="Road America")), encoding="utf-8")
assert tel._verificar_oficial({"irating": 2033, "sr": 3.30, "usuario_id": 77}) == "ok"
linhas = o.ARQ_COMPARACAO.read_text(encoding="utf-8-sig").splitlines()
cab = linhas[0].split(";"); lin = linhas[1].split(";")
assert cab[:5] == ["data", "corrida_id", "categoria", "pista", "status"] and lin[cab.index("status")] == "provisoria", linhas
assert lin[cab.index("ir_erro")] == "7"
assert "PROVISORIA" in log() and "projecao x OFICIAL" in log()
# CSV no formato da 20.1 (sem status): preservado, nunca misturado
o.ARQ_COMPARACAO.unlink()
o.ARQ_COMPARACAO.write_text("data;corrida_id;categoria;pista;ir_projetado;ir_oficial;ir_erro;sr_projetado;sr_oficial;sr_erro\n"
                            "2026-10-30 10:00;1;road;X;1;2;3;4;5;6\n", encoding="utf-8-sig")
o.ARQ_PENDENTE.write_text(json.dumps(dict(pend, quando=o.time.time(), pista="Road America")), encoding="utf-8")
assert tel._verificar_oficial({"irating": 2033, "sr": 3.30, "usuario_id": 77}) == "ok"
antigos = list(S.glob("comparacao_formato_antigo*.csv"))
assert len(antigos) == 1 and "2026-10-30 10:00;1;road;X" in antigos[0].read_text(encoding="utf-8-sig")
assert o.ARQ_COMPARACAO.read_text(encoding="utf-8-sig").splitlines()[0].split(";")[4] == "status"
print("1) iRating/SR: provisoria x confirmada OK")

# ====================================================================================================
# 2) COMBUSTIVEL: litros da PRIMEIRA parada = capacidade disponivel na chegada ao box
# ====================================================================================================
def somar(plano): return sum(d["adicionar_l"] for d in plano)

# 2a) o caso que expunha a divergencia: 3 paradas, tanque 60 L, margem 2 voltas, 3 L/volta, 30 L no tanque
pn = o.calcular_painel_combustivel(30.0, 60.0, 3.0, 3.0, 3.0, 46.0, 1, 0.0, 2.0, 90.0, None, [])
total = pn["linhas"]["med"]["total"]
assert abs(total - 114.0) < 1e-9 and pn["janela"]["paradas"] == 3
p1 = pn["parada1"]
assert p1["volta"] == 1 and abs(p1["chegada_l"] - 27.0) < 1e-9                      # 30 L - 1 volta (3 L) ate a linha
assert abs(p1["adicionar_l"] - 33.0) < 1e-9 and p1["ate_o_topo"]                     # 60 L (tanque) - 27 L (chegada)
assert abs(pn["reabastecer"] - 33.0) < 1e-9 and abs(pn["linhas"]["med"]["reabast"] - 33.0) < 1e-9
assert total / 3 > 60.0 - p1["chegada_l"]                                              # a divisao igual (38 L) NAO cabia no tanque
assert abs(somar(pn["plano"]) - total) < 1e-9 and len(pn["plano"]) == 3
assert [d["ate_o_topo"] for d in pn["plano"]] == [True, True, False]                  # so a ultima nao enche
assert abs(pn["plano"][1]["chegada_l"] - 6.0) < 1e-9                                   # chega com a margem (2 voltas x 3 L)
# 1 parada: so o que falta (lap-independente)
pn = o.calcular_painel_combustivel(10.0, 88.0, 3.4, 3.4, 3.4, 21.5, 22, 0.0, 0.0, 92.0, None, [])
assert pn["janela"]["paradas"] == 1 and abs(pn["reabastecer"] - (21.5 * 3.4 - 10.0)) < 1e-9 and not pn["parada1"]["ate_o_topo"]
# a faixa na janela: parar mais tarde com varias paradas exige MAIS litros (chega mais vazio)
pn = o.calcular_painel_combustivel(30.0, 60.0, 3.0, 3.0, 3.0, 46.0, 1, 0.0, 2.0, 90.0, None, [])
assert pn["parada1"]["adicionar_ultima_volta_l"] > pn["parada1"]["adicionar_l"] and pn["parada1"]["volta_ultima"] == pn["janela"]["ultima"]

# 2b) capacidade desconhecida: uma parada com o total; sem parada: 0; sem plano: None
pn = o.calcular_painel_combustivel(10.0, None, 2.0, 2.0, 2.0, 20.0, 5, 0.0, 0.0, 90.0, None, [])
assert abs(pn["reabastecer"] - 30.0) < 1e-9 and pn["parada1"]["ate_o_topo"] is False
pn = o.calcular_painel_combustivel(50.0, 88.0, 2.0, 2.0, 2.0, 10.0, 3, 0.0, 0.0, 90.0, None, [])
assert pn["reabastecer"] == 0.0 and pn["parada1"] is None and pn["plano"] == []
pn = o.calcular_painel_combustivel(1.0, 60.0, 2.0, 2.0, 2.0, 20.0, 10, 0.2, 0.0, 90.0, None, [])
assert pn["reabastecer"] is None and pn["parada1"] is None and pn["janela"]["estado"] == "sem_janela"

# 2c) Voltas (faixa pequena): primeira_parada
r = o.calcular_combustivel(30.0, 3.0, 46, None, 90.0, 0.0, 2.0, 60.0)
assert r["paradas"] == 3 and abs(r["primeira_parada"] - 33.0) < 1e-9 and abs(r["adicionar"] - 114.0) < 1e-9
r = o.calcular_combustivel(25.0, 3.0, 11, None, 90.0, 0.0, 0.0, 100.0)
assert r["paradas"] == 1 and abs(r["primeira_parada"] - 8.0) < 1e-9
r = o.calcular_combustivel(100.0, 3.0, 30, None, 90.0, 0.0, 0.0, 100.0)
assert r["paradas"] == 0 and r["primeira_parada"] is None
r = o.calcular_combustivel(40.0, 3.0, 50, None, 90.0, 0.0, 20.0, 60.0)
assert r["paradas"] is None and r["primeira_parada"] is None

# 2d) propriedades em milhares de casos: o plano e executavel volta a volta
random.seed(202); verificados = 0
for _ in range(5000):
    c = random.choice([2.0, 2.5, 3.1, 4.0, 5.0]); cap = random.choice([20, 40, 60, 88, 100]); m = random.choice([0, 0.5, 1, 2])
    nivel = random.uniform(0.5, cap); pct = random.choice([0, 0.3, 0.8]); va = random.randint(1, 20); vf = random.uniform(2, 100)
    pn = o.calcular_painel_combustivel(nivel, cap, c, c, c, vf, va, pct, m, 90.0, None, [])
    j = pn["janela"]
    if not pn["plano"]:
        continue
    plano = pn["plano"]; total = pn["linhas"]["med"]["total"]; resto = 1.0 - pct
    assert len(plano) == j["paradas"] and abs(somar(plano) - total) < 1e-6          # litros somam o total
    combustivel, pos = nivel, 0.0                                                    # simulacao em litros, parada a parada
    for k, d in enumerate(plano):
        queimado_ate = resto + d["j"]
        chegada = combustivel - c * (queimado_ate - pos)
        assert abs(chegada - d["chegada_l"]) < 1e-6
        assert d["adicionar_l"] >= -1e-9 and d["adicionar_l"] <= cap - chegada + 1e-6    # nunca passa da capacidade disponivel
        if k < len(plano) - 1:
            assert d["ate_o_topo"]                                                   # paradas intermediarias enchem
        if not j["urgente"]:
            assert chegada >= m * c - 1e-6, (chegada, m * c)                         # chega com a margem a CADA parada
        combustivel, pos = chegada + d["adicionar_l"], queimado_ate
    fim = combustivel - c * (vf - pos)
    assert abs(fim - m * c) < 1e-6                                                   # termina exatamente com a margem
    assert abs(pn["reabastecer"] - plano[0]["adicionar_l"]) < 1e-9 and pn["parada1"]["adicionar_l"] <= cap - pn["parada1"]["chegada_l"] + 1e-6
    verificados += 1
assert verificados > 1500, verificados

# 2e) o numero de paradas do plano nao mudou (a Fase 20.1 continua valendo)
conferidos = 0
for _ in range(500):
    c = random.choice([2.0, 3.0, 4.0]); cap = random.choice([30, 60, 100]); m = random.choice([0, 1, 2])
    nivel = random.uniform(1, cap); vf = random.uniform(2, 90); va = random.randint(1, 20)
    pn = o.calcular_painel_combustivel(nivel, cap, c, c, c, vf, va, 0.0, m, 90.0, None, [])
    pl = o.planejar_paradas(nivel, c, cap, m, vf, 1.0)
    if pl["viavel"] and pl["n"]:
        assert pn["janela"]["paradas"] == pl["n"] and len(pn["plano"]) == pl["n"]
        conferidos += 1
assert conferidos > 100

# 2f) tabela MED/MAX/MIN: cada linha traz os litros da SUA primeira parada
pn = o.calcular_painel_combustivel(30.0, 60.0, 3.0, 3.4, 2.7, 46.0, 1, 0.0, 2.0, 90.0, None, [])
for chave in ("med", "max", "min"):
    ln = pn["linhas"][chave]
    assert ln["reabast"] is not None and 0 < ln["reabast"] <= 60.0
    ref = o.calcular_painel_combustivel(30.0, 60.0, ln["uso"], ln["uso"], ln["uso"], 46.0, 1, 0.0, 2.0, 90.0, None, [])
    assert abs(ln["reabast"] - ref["reabastecer"]) < 1e-9

# 2g) tela: rotulo diz a volta e "ate o topo"; sem plano nao mostra litros
jc = o.JanelaCombustivel(dict(cfg)); jc.show()
pn = o.calcular_painel_combustivel(30.0, 60.0, 3.0, 3.0, 3.0, 46.0, 1, 0.0, 2.0, 90.0, None, [])
tx = desenhar(jc, {"conectado": True, "painel_combustivel": pn})
assert any(t.startswith("COLOCAR NA V1") and "TOPO" in t for t in tx) and "+33,0 L" in tx, tx
pn = o.calcular_painel_combustivel(10.0, 88.0, 3.4, 3.4, 3.4, 21.5, 22, 0.0, 0.0, 92.0, None, [])
tx = desenhar(jc, {"conectado": True, "painel_combustivel": pn})
assert any(t == "COLOCAR NA V22" for t in tx) and not any("TOPO" in t for t in tx), tx
pn = o.calcular_painel_combustivel(1.0, 60.0, 2.0, 2.0, 2.0, 20.0, 10, 0.2, 0.0, 90.0, None, [])
tx = desenhar(jc, {"conectado": True, "painel_combustivel": pn})
assert "COLOCAR NA PARADA" in tx and "--" in tx and "SEM JANELA" in tx, tx
print("2) combustivel: litros da 1a parada OK (%d casos executados volta a volta)" % verificados)

print("TODOS OS TESTES DA FASE 20.2 PASSARAM")
print("(dados SIMULADOS: nao substitui a validacao em sessao real; arquivos temporarios: %s)" % S)
