"""Testes automatizados da Fase 20.1 (revisao tecnica): radar, projecao x oficial, combustivel, mapa e pneus.
Executar: py -3.12 testes\\teste_fase201.py   (ou executar_testes.bat). Nao precisa do iRacing aberto.

ATENCAO: tudo aqui usa dados SIMULADOS. Estes testes provam a logica; NAO substituem a validacao em sessao
real do iRacing (ver ROTEIRO_VALIDACAO.txt)."""
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

S = Path(tempfile.mkdtemp(prefix="overlay_testes_201_"))
o.ARQ_LOG = S / "log.txt"; o.ARQ_CONFIG = S / "cfg_inexistente.json"
o.ARQ_PENDENTE = S / "pendente.json"; o.ARQ_COMPARACAO = S / "comparacao.csv"; o.ARQ_HISTORICO = S / "historico.csv"
o.ARQ_RECORDES = S / "recordes.json"; o.ARQ_PNEUS = S / "pneus.json"; o.ARQ_MAPAS = S / "mapas.json"
app = QApplication([]); o.salvar_config = lambda c: None
cfg = o.carregar_config()


def log():
    return o.ARQ_LOG.read_text(encoding="utf-8") if o.ARQ_LOG.exists() else ""


def limpar():
    for f in (o.ARQ_LOG, o.ARQ_PENDENTE, o.ARQ_COMPARACAO, o.ARQ_HISTORICO):
        if f.exists():
            f.unlink()
    for f in S.glob("comparacao_formato_antigo*.csv"):
        f.unlink()


class Gravador(QPainter):
    """QPainter que registra todos os textos desenhados (para testar o que aparece na tela)."""
    def __init__(self, *a):
        super().__init__(*a)
        self.textos = []

    def drawText(self, *args):
        self.textos.append(next((x for x in args if isinstance(x, str)), ""))
        return super().drawText(*args)


def desenhar(janela, dados):
    """Pinta a janela num QImage e devolve os textos desenhados."""
    img = QImage(janela.tamanho()[0] * 2, janela.tamanho()[1] * 2, QImage.Format_ARGB32)
    img.fill(0)
    gravador = Gravador(img)
    janela._pintor = lambda: (gravador.scale(janela.escala_x, janela.escala_y), gravador)[1]
    janela.dados = dados
    janela.paintEvent(None)
    gravador.end()
    return gravador.textos


# ====================================================================================================
# 1) RADAR: ocupacao lateral (SDK) x identidade (inferida) x posicao longitudinal (calculada)
# ====================================================================================================
L = 4000.0
pil = {i: {"numero": str(i), "classe_cor": (150, 150, 160)} for i in range(6)}
def pcts(*metros): return [0.5] + [0.5 + m / L for m in metros]
def radar(metros, lado, mem=None, t=1.0, n=None):
    p = pcts(*metros)
    return o.montar_radar(pil, 0, p, [3] * len(p), [False] * len(p), lado, L, memoria={} if mem is None else mem, agora=t)

# 1a) SDK diz "1 carro a esquerda" e ha DOIS candidatos dentro de 8 m: identidade AMBIGUA, nunca "confirmada"
rd = radar([3.0, -5.0], 2)
c1, c2 = (next(c for c in rd["carros"] if c["idx"] == i) for i in (1, 2))
assert rd["ocupacao_sdk"] == {"esq": 1, "dir": 0} and (rd["esq"], rd["dir"]) == (1, 0)
assert c1["lado_fonte"] == "inferido" and c2["lado_fonte"] == "indef"           # o mais proximo e assumido; o outro NAO
assert c1["ident"] == "ambigua" and c2["ident"] == "ambigua"
assert all(c["lado_fonte"] != "sdk" for c in rd["carros"])                       # nenhum CarIdx e "confirmado pelo SDK"
assert c1["urgencia"] == 3 and c2["urgencia"] <= 1                               # so a ocupacao confirmada vira perigo
# 1b) exatamente os candidatos necessarios: identidade "unica" (ainda INFERIDA)
rd = radar([3.0, 22.0], 2)
c1 = next(c for c in rd["carros"] if c["idx"] == 1)
assert c1["lado_fonte"] == "inferido" and c1["ident"] == "unica" and c1["faixa"] == -1.0
# 1c) SDK diz "livre": carro a 3 m NAO vira perigo (lateral desconhecida) e nao e posto num lado
rd = radar([3.0], 1)
c1 = rd["carros"][0]
assert rd["ocupacao_sdk"] == {"esq": 0, "dir": 0} and c1["lado_fonte"] == "indef" and c1["faixa"] == 0.0 and c1["urgencia"] <= 1
# 1d) SDK acusa mas ninguem proximo: sem inventar carro (sem_par)
rd = radar([20.0, 24.0], 2)
assert rd["sem_par"] == (1, 0) and all(c["lado_fonte"] == "indef" and c["urgencia"] <= 1 for c in rd["carros"])
# 1e) dois lados ocupados, um candidato so: o outro lado fica sem_par
rd = radar([2.0], 4)
assert rd["ocupacao_sdk"] == {"esq": 1, "dir": 1} and rd["sem_par"][0] + rd["sem_par"][1] == 1

# 2) TTC / aproximacao: aproximacao longitudinal NAO e previsao de colisao
mem, t, historico = {}, 0.0, []
for k in range(400):                                     # carro vindo de tras a 30 m/s mais rapido, lateral desconhecida
    d = -25.0 + 30.0 * t                                 # entra no alcance do radar (26 m) e fecha ate 3 m
    if d > 3.0:
        break
    rd = radar([d], 1, mem=mem, t=t)
    c = rd["carros"][0]
    historico.append((d, c["urgencia"], c["alcance_s"], c["lado_fonte"], c["gap"]))
    t += 0.033
assert "ttc" not in rd["carros"][0] and "alcance_s" in rd["carros"][0]               # nome honesto: nao e TTC
assert max(u for _, u, _, _, _ in historico) == 1, "aproximacao longitudinal nao pode gerar alerta de colisao (2/3)"
assert any(a is not None and a < 3.5 for _, _, a, _, _ in historico)                 # o alcance continua calculado
assert all(f == "indef" for _, _, _, f, _ in historico)
assert all(u in (0, 1) for _, u, _, _, _ in historico)
# ... mas com ocupacao lateral CONFIRMADA e o carro ao lado, o perigo (3) continua
mem = {}
rd = radar([1.0], 2, mem=mem, t=0.0)
assert rd["carros"][0]["urgencia"] == 3
# resumo (frente/tras) usa alcance_s
for k in range(20):
    rd = radar([-30.0 + 15.0 * k * 0.033], 1, mem=mem, t=1.0 + k * 0.033)
assert rd["tras"] is not None and "alcance_s" in rd["tras"] and "ttc" not in rd["tras"]

# 2b) o que aparece na tela: rotulos honestos
jr = o.JanelaRadar(dict(cfg)); jr.show()
mem = {}
for k in range(40):
    rdw = radar([-30.0 + 15.0 * k * 0.033], 1, mem=mem, t=k * 0.033)
dd = {"conectado": True, "radar": rdw}
textos = desenhar(jr, dd)
assert any("ocup" in x and "SDK" in x and "estimado" in x for x in textos), textos        # legenda: o que e SDK e o que e estimado
assert any(x.startswith("~") and x.endswith(" s") for x in textos), textos                  # alcance sempre com "~"
assert not any(x.endswith(" s") and not x.startswith("~") for x in textos)
rd2 = radar([3.0, -5.0], 2)
desenhar(jr, {"conectado": True, "radar": rd2})                                               # ambigua: desenha sem erro
print("1) radar: ocupacao SDK x identidade inferida x alcance longitudinal OK")

# ====================================================================================================
# 2) PROJECAO de iRating/SR x resultado OFICIAL: so compara com a corrida certa
# ====================================================================================================
sess = n.identidade_sessao(1001, "Road", 77, True)
assert sess == {"id": "1001", "categoria": "road", "usuario": 77, "oficial": True, "forte": True}
assert not n.identidade_sessao(0, "Road", 77, True)["forte"]            # offline (SubSessionID 0)
assert not n.identidade_sessao(1001, None, 77, True)["forte"]           # categoria desconhecida
assert not n.identidade_sessao(1001, "Road", None, True)["forte"]       # usuario desconhecido
assert not n.identidade_sessao(1001, "Road", 77, False)["forte"]        # nao oficial: nao gera resultado
assert not n.identidade_sessao(None, "Road", 77, True)["forte"] and not n.identidade_sessao("x", "Road", 77, True)["forte"]

pend = {"versao": 2, "id": "1001", "categoria": "road", "usuario": 77, "ir_base": 2000, "ir_delta_proj": 40,
        "sr_base": 3.20, "sr_delta_proj": 0.10}
agora_ok = n.identidade_sessao(1002, "Road", 77, True)
res, mot = n.avaliar_comparacao(pend, agora_ok, 2033, 3.30)
assert mot == "ok" and res["ir_real"] == 33 and res["ir_proj"] == 40 and res["ir_erro"] == 7 and res["sr_erro"] == 0.0
assert n.avaliar_comparacao(pend, agora_ok, 2000, 3.20) == (None, "sem_atualizacao_numerica")      # nada mudou ainda (Fase 20.2.1: nao e resultado oficial)
assert n.avaliar_comparacao(pend, n.identidade_sessao(1001, "Road", 77, True), 2033, 3.3) == (None, "mesma_sessao")
assert n.avaliar_comparacao(pend, n.identidade_sessao(1002, "Oval", 77, True), 1350, 2.1) == (None, "categoria_diferente")
assert n.avaliar_comparacao(pend, n.identidade_sessao(1002, None, 77, True), 2033, 3.3) == (None, "categoria_desconhecida")
assert n.avaliar_comparacao(pend, n.identidade_sessao(1002, "Road", 78, True), 2033, 3.3) == (None, "usuario_diferente")
assert n.avaliar_comparacao(pend, None, 2033, 3.3) == (None, "categoria_desconhecida")
assert n.avaliar_comparacao({"ir_base": 2000, "ir_delta_proj": 40}, agora_ok, 2033, 3.3) == (None, "pendente_sem_id")   # formato da Fase 20
assert n.avaliar_comparacao(dict(pend, base_incerta=True), agora_ok, 2033, 3.3) == (None, "base_incerta")
assert n.avaliar_comparacao(None, agora_ok, 1, 1) == (None, "sem_pendente")
assert set(n.MOTIVOS_DESCARTE) == {"pendente_sem_id", "base_incerta"} and all(m in n.MOTIVOS_TEXTO for m in n.MOTIVOS_DESCARTE)

# 2b) integracao com a Telemetria (escrita e leitura dos arquivos)
limpar()
tel = o.Telemetria(demo=True)
eu = {"irating": 2033, "sr": 3.30, "usuario_id": 77}
def configurar(sub, cat, oficial=True):
    tel._subsessao, tel._categoria, tel._oficial = sub, cat, oficial
def gravar_pendente(**extra):
    """Grava uma pendente no formato v2 (Fase 20.1/20.2): a leitura migra para o ciclo de vida atual."""
    p = dict(pend, quando=o.time.time(), pista="Road America"); p.update(extra)
    o.ARQ_PENDENTE.write_text(json.dumps(p), encoding="utf-8")
def estados():
    return [(r["id"], r["estado"]) for r in tel._ler_projecoes()]      # le (e migra) qualquer versao do arquivo

# categoria diferente (ex.: iRating de oval): nao compara, nao apaga, nao escreve CSV
gravar_pendente(); configurar(1002, "Oval")
assert tel._verificar_oficial({"irating": 1350, "sr": 2.1, "usuario_id": 77}) == "categoria_diferente"
assert o.ARQ_PENDENTE.exists() and not o.ARQ_COMPARACAO.exists() and "NAO comparada" in log()
# mesma sessao: aguarda
configurar(1001, "Road")
assert tel._verificar_oficial(eu) == "mesma_sessao" and o.ARQ_PENDENTE.exists() and not o.ARQ_COMPARACAO.exists()
# ainda sem resultado oficial: aguarda e avisa que a base da proxima corrida e incerta
configurar(1002, "Road")
assert tel._verificar_oficial({"irating": 2000, "sr": 3.20, "usuario_id": 77}) == "sem_atualizacao_numerica" and estados() == [("1001", "pendente")]
assert tel._aguardando_oficial is True                                  # a base da proxima corrida e incerta
# categoria certa, outra corrida, oficial atualizado: compara e registra no CSV com a identificacao
assert tel._verificar_oficial(eu) == "ok" and tel._aguardando_oficial is False
assert estados() == [("1001", "provisoria")]                            # Fase 20.2.1: preservada, nao apagada
linhas = o.ARQ_COMPARACAO.read_text(encoding="utf-8-sig").splitlines()
assert linhas[0] == "data;corrida_id;categoria;pista;status;ir_projetado;ir_oficial;ir_erro;sr_projetado;sr_oficial;sr_erro", linhas[0]
assert ";1001;road;Road America;provisoria;40;33;7;0.1;0.1;0.0" in linhas[1], linhas[1]
# formato da Fase 20 (sem id): nao ha como associar; descartado sem comparar, uma unica vez
gravar_pendente(); p0 = json.loads(o.ARQ_PENDENTE.read_text()); [p0.pop(k) for k in ("id", "categoria", "usuario", "versao")]
o.ARQ_PENDENTE.write_text(json.dumps(p0)); n_linhas = len(linhas)
assert tel._verificar_oficial(eu) == "sem_pendente" and "descartada sem comparar" in log() and estados() == []
assert len(o.ARQ_COMPARACAO.read_text(encoding="utf-8-sig").splitlines()) == n_linhas
# base incerta (pendente de uma corrida anterior ainda nao resolvida): nao compara; fica registrada como EXPIRADA
gravar_pendente(base_incerta=True)
assert tel._verificar_oficial(eu) == "base_incerta" and estados() == [("1001", "expirada")]
# pendente expirada por prazo
gravar_pendente(quando=o.time.time() - 15 * 86400)
assert tel._verificar_oficial(eu) == "expirada" and estados() == [("1001", "expirada")]
# CSV de formato antigo: preservado (renomeado), nunca misturado nem apagado
antigo = S / "comparacao.csv"
antigo.write_text("data;pista;ir_projetado;ir_oficial;ir_erro;sr_projetado;sr_oficial;sr_erro\n2026-01-01 10:00;X;1;2;3;4;5;6\n", encoding="utf-8-sig")
gravar_pendente(); configurar(1003, "Road")
assert tel._verificar_oficial(eu) == "ok"
preservado = list(S.glob("comparacao_formato_antigo*.csv"))
assert len(preservado) == 1 and "2026-01-01 10:00;X;1;2;3;4;5;6" in preservado[0].read_text(encoding="utf-8-sig")
assert o.ARQ_COMPARACAO.read_text(encoding="utf-8-sig").splitlines()[0].startswith("data;corrida_id;categoria")

# 2c) fim de corrida SEM identificacao segura: nao grava projecao nova; as ja guardadas (outras corridas) ficam intactas
limpar(); gravar_pendente()
res_proj = {"tipo": "CORRIDA", "ir": {"novo": 2040, "delta": 40, "pos": 1, "n": 12}, "sr": {"novo": 3.3, "delta": 0.1},
            "curvas": 50.0, "inc": 2, "oficial": False}
tel._nome_pista = "Road America"; tel._sessao_registrada = None
configurar(0, "Road", oficial=True)                                    # offline: SubSessionID 0
base = {"ir": 2000, "sr": 3.2, "letra": "A", "incerta": False}
tel._registrar_historico(("a", 1), res_proj, eu, base)
assert estados() == [("1001", "pendente")] and "sem identificacao segura" in log()
assert o.ARQ_HISTORICO.exists()                                         # o historico continua sendo gravado
# com identificacao forte: grava pendente completa, com a base marcada como incerta quando for o caso
tel._sessao_registrada = None; configurar(2001, "Road", oficial=True)
tel._registrar_historico(("a", 2), res_proj, eu, dict(base, incerta=True))
assert estados() == [("1001", "expirada"), ("2001", "pendente")]       # a 1001 (mesma categoria/usuario) foi sobreposta
pg = json.loads(o.ARQ_PENDENTE.read_text())["projecoes"][1]
assert pg["id"] == "2001" and pg["categoria"] == "road" and pg["usuario"] == 77 and pg["base_incerta"] is True and pg["versao"] == 3
print("2) projecao x oficial: associacao segura OK")

# ====================================================================================================
# 3) COMBUSTIVEL
# ====================================================================================================
def oraculo(nivel, c, cap, m, L_, resto):
    """Referencia INDEPENDENTE (programacao dinamica sobre as passagens pela linha): (paradas minimas, (1a, ultima))."""
    f0, C, eps = nivel / c, cap / c, 1e-9
    cruz, i = [], 0
    while resto + i < L_ - eps:
        cruz.append(resto + i); i += 1
    if f0 >= L_ + m - eps:
        return 0, None
    INF = 10 ** 9
    chega = lambda f, b0, b1: f - (b1 - b0) >= m - eps
    g = [INF] * len(cruz)
    for i in range(len(cruz) - 1, -1, -1):
        if C - (L_ - cruz[i]) >= m - eps:
            g[i] = 0
            continue
        for k in range(i + 1, len(cruz)):
            if chega(C, cruz[i], cruz[k]) and g[k] < INF:
                g[i] = min(g[i], 1 + g[k])
    tot = {i: 1 + g[i] for i in range(len(cruz)) if chega(f0, 0.0, cruz[i]) and g[i] < INF}
    if not tot:
        return None
    kmin = min(tot.values()); js = [i for i, v in tot.items() if v == kmin]
    return kmin, (min(js), max(js))

random.seed(201)
comparados = divergentes = 0
for _ in range(4000):
    c = random.choice([2.0, 2.5, 3.1, 3.4, 4.0, 5.0]); cap = random.choice([20, 40, 60, 88, 100, 106])
    m = random.choice([0, 0.5, 1.0, 1.5, 2.0]); Lf = random.uniform(1, 120); pct = random.choice([0, 0.1, 0.5, 0.9])
    nivel = random.uniform(0, cap)
    pl = o.planejar_paradas(nivel, c, cap, m, Lf, 1 - pct)
    if pl["urgente"]:
        continue
    ref = oraculo(nivel, c, cap, m, Lf, 1 - pct)
    comparados += 1
    if ref is None:
        ok = not pl["viavel"] and pl["n"] is None and pl["motivo"] in ("nao_chega_ao_box", "tanque_insuficiente", "sem_janela")
    elif ref[0] == 0:
        ok = pl["n"] == 0 and pl["viavel"]
    else:
        ok = pl["viavel"] and (pl["n"], (pl["primeira"], pl["ultima"])) == ref
    divergentes += 0 if ok else 1
assert comparados > 2500 and divergentes == 0, (comparados, divergentes)

# 3a) a margem vale em CADA parada (a formula antiga 'ceil(adicionar/capacidade)' subestimava)
# tanque 60 L (20 voltas a 3 L), margem 2: cada parada rende 14 voltas, nao 20. 45 voltas, 30 L (10 voltas) agora.
r = o.calcular_combustivel(30.0, 3.0, 46, None, 90.0, 0.0, 2.0, 60.0)
assert r["voltas_fim"] == 46.0 and abs(r["adicionar"] - ((46 + 2) * 3.0 - 30.0)) < 1e-9
assert math.ceil(r["adicionar"] / 60.0) == 2 and r["paradas"] == 3, r            # antes: 2 (insuficiente)
pn = o.calcular_painel_combustivel(30.0, 60.0, 3.0, 3.0, 3.0, 46.0, 1, 0.0, 2.0, 90.0, None, [])
assert pn["janela"]["paradas"] == 3 and abs(sum(d["adicionar_l"] for d in pn["plano"]) - r["adicionar"]) < 1e-9   # Fase 20.2: litros por parada ver teste_fase202
assert pn["reabastecer"] <= 60.0 - 2 * 3.0 + 1e-9                                  # cada parada cabe no tanque descontada a reserva

# 3b) tanque parcialmente cheio e capacidade maxima
r = o.calcular_combustivel(25.0, 3.0, 11, None, 90.0, 0.0, 0.0, 100.0)             # 11 voltas x 3 = 33 L, tem 25
assert abs(r["adicionar"] - 8.0) < 1e-9 and r["paradas"] == 1 and abs(r["livre_tanque"] - 75.0) < 1e-9
r = o.calcular_combustivel(100.0, 3.0, 30, None, 90.0, 0.0, 0.0, 100.0)            # tanque cheio (100 L = 33,3 voltas), 30 voltas
assert r["adicionar"] == 0.0 and r["paradas"] == 0 and r["livre_tanque"] == 0.0
r = o.calcular_combustivel(100.0, 3.0, 80, None, 90.0, 0.0, 0.0, 100.0)            # 240 L: cheio e ainda precisa de paradas
assert r["adicionar"] > r["livre_tanque"] and r["paradas"] == 2 and r["motivo"] is None     # 240 L: 140 L alem do tanque cheio = 2 paradas
r = o.calcular_combustivel(40.0, 3.0, 20, None, 90.0, 0.0, 0.0, None)              # capacidade desconhecida: 1 parada, sem inventar
assert r["paradas"] == 1 and r["livre_tanque"] is None

# 3c) abastecimento apos consumo adicional: a volta de reabastecimento NAO entra na media
cb = o.ConsumoCombustivel()
nivel = 50.0; cb.atualizar(0, nivel, False)
for volta, uso in ((1, 3.0), (2, 3.0), (3, 3.9)):                                    # volta 3 com consumo extra (trafego)
    nivel -= uso; cb.atualizar(volta, nivel, False)
assert [round(u, 1) for _, u in cb.registros] == [3.0, 3.9]          # a 1a volta (parcial) nao entra
nivel -= 3.0; cb.atualizar(4, nivel, False)                                         # volta 4 normal
nivel -= 1.5; cb.atualizar(4, nivel, True)                                          # na volta 5: entra na box
nivel += 40.0; cb.atualizar(4, nivel, True)                                         # reabastece +40 L
nivel -= 0.5; cb.atualizar(5, nivel, False)                                         # fecha a volta 5 (a do pit): fica de fora
n_antes = len(cb.registros)
assert 5 not in [v for v, _ in cb.registros]
for volta in (6, 7):
    nivel -= 3.0; cb.atualizar(volta, nivel, False)
assert len(cb.registros) == n_antes + 2 and all(2.9 < u < 4.0 for _, u in cb.registros), list(cb.registros)
usos = [u for _, u in cb.registros]
c_med, c_max, c_min = sum(usos) / len(usos), max(usos), min(usos)
assert abs(c_max - 3.9) < 1e-9 and abs(c_min - 3.0) < 1e-9
pn = o.calcular_painel_combustivel(nivel, 88.0, c_med, c_max, c_min, 30.0, 8, 0.0, 1.0, 90.0, None, list(cb.registros))
assert pn["linhas"]["max"]["total"] > pn["linhas"]["med"]["total"] > pn["linhas"]["min"]["total"]
assert pn["linhas"]["max"]["paradas"] >= pn["linhas"]["med"]["paradas"] >= pn["linhas"]["min"]["paradas"]

# 3d) uma ou mais paradas; margem; janela
pn = o.calcular_painel_combustivel(30.0, 60.0, 2.0, 2.0, 2.0, 20.0, 10, 0.0, 0.0, 90.0, None, [])
assert pn["janela"]["ultima"] == 24 and pn["janela"]["primeira"] == 10 and pn["janela"]["estado"] == "aberta" and pn["janela"]["paradas"] == 1
pm = o.calcular_painel_combustivel(30.0, 60.0, 2.0, 2.0, 2.0, 20.0, 10, 0.0, 2.0, 90.0, None, [])
assert pm["janela"]["ultima"] == pn["janela"]["ultima"] - 2                            # margem encurta o fim da janela
ant = None
for margem in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0):                                          # mais margem nunca reduz paradas
    r = o.calcular_combustivel(30.0, 3.0, 46, None, 90.0, 0.0, margem, 60.0)
    assert r["paradas"] is not None and (ant is None or r["paradas"] >= ant); ant = r["paradas"]

# 3e) corridas por tempo
r = o.calcular_combustivel(30.0, 3.0, 32767, 3600.0, 90.0, 0.0, 0.0, 88.0)           # sem limite de voltas: 40 voltas de 90 s
assert r["fonte"] == "tempo" and r["voltas_fim"] == 40.0
r = o.calcular_combustivel(30.0, 3.0, 32767, 3600.0, 90.0, 0.5, 0.0, 88.0)           # a meio da volta: termina na 41a passagem
assert r["voltas_fim"] == 40.5, r["voltas_fim"]
r = o.calcular_combustivel(30.0, 3.0, 32767, 3590.0, 90.0, 0.0, 0.0, 88.0)           # 39,9 voltas: ainda cruza a linha 40 vezes
assert r["voltas_fim"] == 40.0
r = o.calcular_combustivel(30.0, 3.0, 32767, 20.0, 90.0, 0.7, 0.0, 88.0)             # falta 0,3 volta (27 s) e o relogio acaba antes: 1 passagem
assert abs(r["voltas_fim"] - 0.3) < 1e-9
r = o.calcular_combustivel(30.0, 3.0, 32767, 30.0, 90.0, 0.7, 0.0, 88.0)             # a linha vem aos 27 s, o relogio ainda tem 3 s: mais uma volta
assert abs(r["voltas_fim"] - 1.3) < 1e-9
r = o.calcular_combustivel(30.0, 3.0, 32767, 0.0, 90.0, 0.0, 0.0, 88.0)              # relogio zerado, na linha: acabou
assert r["voltas_fim"] == 0.0 and r["paradas"] == 0
r = o.calcular_combustivel(30.0, 3.0, 20, 3600.0, 90.0, 0.0, 0.0, 88.0)              # limite de voltas E de tempo: vale o que acaba antes
assert r["fonte"] == "voltas" and r["voltas_fim"] == 20.0
r = o.calcular_combustivel(30.0, 3.0, 50, 1800.0, 90.0, 0.0, 0.0, 88.0)
assert r["fonte"] == "tempo" and r["voltas_fim"] == 20.0
r = o.calcular_combustivel(30.0, 3.0, 32767, None, 90.0, 0.0, 0.0, 88.0)             # nenhum limite conhecido
assert r["voltas_fim"] is None and r["paradas"] is None
r = o.calcular_combustivel(30.0, 3.0, 32767, 3600.0, None, 0.0, 0.0, 88.0)           # tempo sem ritmo: nao inventa
assert r["voltas_fim"] is None

# 3f) NAO existe janela de pit viavel
pn = o.calcular_painel_combustivel(1.0, 60.0, 2.0, 2.0, 2.0, 20.0, 10, 0.2, 0.0, 90.0, None, [])      # 0,5 volta; faltam 0,8 para a linha
j = pn["janela"]
assert j["estado"] == "sem_janela" and j["motivo"] == "nao_chega_ao_box" and j["primeira"] is None and j["ultima"] is None
pn = o.calcular_painel_combustivel(40.0, 60.0, 3.0, 3.0, 3.0, 50.0, 5, 0.0, 20.0, 90.0, None, [])     # margem >= tanque inteiro (20 voltas)
assert pn["janela"]["estado"] == "sem_janela" and pn["janela"]["motivo"] == "tanque_insuficiente"
r = o.calcular_combustivel(40.0, 3.0, 50, None, 90.0, 0.0, 20.0, 60.0)
assert r["paradas"] is None and r["motivo"] == "tanque_insuficiente"
pn = o.calcular_painel_combustivel(3.0, 60.0, 2.0, 2.0, 2.0, 20.0, 10, 0.2, 1.0, 90.0, None, [])      # chega a linha, mas sem a margem: urgente
assert pn["janela"]["urgente"] and pn["janela"]["estado"] == "aberta" and pn["janela"]["ultima"] == 10
# janela coerente em qualquer caso (propriedade)
random.seed(7)
for _ in range(1500):
    c = random.choice([2.0, 3.0, 4.0]); cap = random.choice([30, 60, 100]); m = random.choice([0, 1, 2])
    nivel = random.uniform(0.5, cap); pct = random.choice([0, 0.4]); va = random.randint(1, 30); vf = random.uniform(2, 70)
    pn = o.calcular_painel_combustivel(nivel, cap, c, c, c, vf, va, pct, m, 90.0, None, [])
    j = pn["janela"]
    if j is None or j["estado"] in ("sem_parada", "sem_janela"):
        continue
    assert j["primeira"] <= j["ultima"] and j["ultima"] >= va and j["paradas"] >= 1
    assert j["estado"] == ("fechada" if va < j["primeira"] else "aberta")
    assert pn["reabastecer"] <= cap + 1e-9

# 3g) a janela mostra o motivo (texto) quando nao ha janela
jc = o.JanelaCombustivel(dict(cfg)); jc.show()
for painel, esperado in (
        (o.calcular_painel_combustivel(1.0, 60.0, 2.0, 2.0, 2.0, 20.0, 10, 0.2, 0.0, 90.0, None, []), "n\u00e3o chega ao box"),
        (o.calcular_painel_combustivel(40.0, 60.0, 3.0, 3.0, 3.0, 50.0, 5, 0.0, 20.0, 90.0, None, []), "tanque insuficiente")):
    tx = desenhar(jc, {"conectado": True, "painel_combustivel": painel})
    assert "SEM JANELA" in tx and esperado in tx, tx
    assert "reabaste\u00e7a j\u00e1" not in tx                       # nao manda "reabastecer ja" quando nem chega ao box
print("3) combustivel: paradas minimas, margem por parada, tempo e janela OK  (oraculo: %d casos, 0 divergencias)" % comparados)

# ====================================================================================================
# 4) MAPA de 360 pontos: velocidade x frequencia de amostragem
# ====================================================================================================
def volta_mapa(comp, v, hz, voltas=1.0, jit=0.0, seed=0):
    random.seed(seed)
    m = o.MapaPista(S / "m.json"); m._cache = {}; m.definir_pista("t")
    R = comp / (2 * math.pi); t = tot = 0.0; passos = 0
    while tot < voltas * comp and passos < 400000:
        dt = 1.0 / hz * (1 + random.uniform(-jit, jit)); t += dt; tot += v * dt; pct = (tot / comp) % 1.0
        ang = 2 * math.pi * pct
        m.atualizar(pct, 48 + R * math.sin(ang) / 110540, -90 + R * math.cos(ang) / (111320 * math.cos(math.radians(48))),
                    True, v, None, agora=t)
        passos += 1
        if m.completo:
            break
    return m, tot / comp, R

# frequencias realistas (>= 10 Hz; o overlay le a 30 Hz) fecham a volta com 1 volta, em qualquer pista/velocidade
falhas = []
for comp in (1500, 2500, 4000, 6500, 13000, 20800):
    for v in (15, 40, 60, 85):
        for hz in (10, 20, 30, 60):
            for jit in (0.0, 0.3):
                m, voltas_feitas, R = volta_mapa(comp, v, hz, 1.1, jit)
                if not m.completo:
                    falhas.append((comp, v, hz, jit, m.preenchidos))
assert not falhas, falhas
# frequencias baixas (4-5 Hz, ex.: PC sobrecarregado): fecha em ate 1,1 volta apos interpolar entre amostras seguidas
for comp in (1500, 2500, 4000, 6500, 13000, 20800):
    for v in (15, 40, 60, 85):
        for hz in (4, 5):
            m, voltas_feitas, R = volta_mapa(comp, v, hz, 1.1)
            assert m.completo, (comp, v, hz, m.preenchidos)
# 2 Hz com velocidade alta: pode precisar de mais de uma volta, mas fecha (nunca fica preso por aliasing)
for comp, v in ((1500, 60), (2500, 85), (6500, 85)):
    m, voltas_feitas, R = volta_mapa(comp, v, 2, 6.0)
    assert m.completo, (comp, v, m.preenchidos)
# o desenho fica fiel (pista circular simulada): erro radial pequeno mesmo com amostragem lenta
for comp, v, hz in ((4000, 85, 5), (4000, 40, 30), (13000, 85, 10)):
    m, _, R = volta_mapa(comp, v, hz, 1.1)
    raios = [math.hypot(x, y) for x, y in m.pontos]
    cx = sum(x for x, _ in m.pontos) / len(m.pontos); cy = sum(y for _, y in m.pontos) / len(m.pontos)
    raios = [math.hypot(x - cx, y - cy) for x, y in m.pontos]
    assert max(abs(r_ - R) for r_ in raios) < 0.02 * R, (comp, v, hz, max(abs(r_ - R) for r_ in raios) / R)
# interpolacao so entre amostras REAIS e seguidas: quebra de continuidade nao inventa pontos
m = o.MapaPista(S / "m2.json"); m._cache = {}; m.definir_pista("t2")
def amostra(pct, t, na_pista=True, v=50.0):
    m.atualizar(pct, 48 + pct * 0.01, -90 + pct * 0.01, na_pista, v, None, agora=t)
amostra(0.100, 0.0); amostra(0.130, 0.1)                       # salto de 10 pontos em 0,1 s: interpola os 9 do meio
assert m.interpolados == 9 and m.preenchidos == 11
amostra(0.400, 0.2)                                            # salto de ~97 pontos (teleporte/reset): NAO interpola
assert m.interpolados == 9
amostra(0.420, 3.0)                                            # 2,8 s depois: amostra anterior velha, NAO interpola
assert m.interpolados == 9
amostra(0.430, 3.05, na_pista=False); amostra(0.460, 3.1)      # box/fora da pista no meio: quebra a continuidade
assert m.interpolados == 9
amostra(0.470, 3.2, v=1.0); amostra(0.500, 3.3)                # parado (<3 m/s) tambem quebra
assert m.interpolados == 9
assert m.lacuna_maxima() > 100 and not m.completo
# mapa guardado em disco continua carregando (compatibilidade com a Fase 20)
cache = S / "mapas_antigos.json"
cache.write_text(json.dumps({"pista-x": [[i * 1.0, i * 0.5] for i in range(o.N_PONTOS_MAPA)]}), encoding="utf-8")
mc = o.MapaPista(cache); mc.definir_pista("pista-x")
assert mc.completo and len(mc.pontos) == o.N_PONTOS_MAPA and mc.exibicao()["progresso"] == 1.0
print("4) mapa: preenchimento x velocidade x frequencia OK")

# ====================================================================================================
# 5) PNEUS: real x estimado sempre distinguiveis
# ====================================================================================================
real = (90.0, 91.0, 92.0)
ult = {"temp": (88.0, 89.0, 90.0), "idade": 300.0, "hora": "14:03", "local": "boxes"}
assert n.origem_pneu(real, ult, 95.0, {"vida": 0.8, "tipo": "real"}) == {
    "temp_cabecalho": "real", "temp_corpo": "real_ao_vivo", "vida": "real", "rotulo_vida": "VIDA"}
assert n.origem_pneu(None, ult, 95.0, {"vida": 0.8, "tipo": "est"}) == {
    "temp_cabecalho": "estimada", "temp_corpo": "real_antiga", "vida": "estimada", "rotulo_vida": "VIDA~"}
assert n.origem_pneu(None, ult, None, {"vida": 0.8, "tipo": "est"})["temp_cabecalho"] is None        # sem estimativa: nao inventa
assert n.origem_pneu(None, None, 95.0, None) == {"temp_cabecalho": None, "temp_corpo": "estimada", "vida": "nenhuma", "rotulo_vida": "VIDA"}
assert n.origem_pneu(None, None, None, {"vida": None, "tipo": "est"}) == {
    "temp_cabecalho": None, "temp_corpo": "nenhuma", "vida": "nenhuma", "rotulo_vida": "VIDA"}
assert n.origem_pneu(None, {"temp": None}, 95.0, {"vida": 0.5, "tipo": "real"})["temp_corpo"] == "estimada"

jp = o.JanelaPneus(dict(cfg)); jp.show()
def cartao(temp_real, ultima, info):
    img = QImage(400, 300, QImage.Format_ARGB32); img.fill(0)
    g = Gravador(img)
    jp._cartao(g, 10, 10, "LF", info, temp_real, 80.0, 105.0, False, ultima)
    g.end()
    return g.textos
# a) temperatura real ao vivo: sem "~"; vida real: rotulo sem "~"
tx = cartao(real, ult, {"temp": 95.0, "vida": 0.8, "tipo": "real", "perda_volta": None, "voltas": 0})
assert "91°C" in tx and not any(t.startswith("~") for t in tx) and "VIDA" in tx and "VIDA~" not in tx, tx
# b) so estimativa: toda temperatura com "~", rotulo "temperatura estimada" e vida com "VIDA~"
tx = cartao(None, None, {"temp": 95.0, "vida": 0.8, "tipo": "est", "perda_volta": 0.01, "voltas": 3})
assert "~95°C" in tx and "temperatura estimada" in tx and "VIDA~" in tx and "91°C" not in tx, tx
assert not any(t.endswith("°C") and not t.startswith("~") for t in tx), tx
# c) ultima leitura real (jogo parou de atualizar): valores antigos + idade; cabecalho = estimativa com "~"
tx = cartao(None, ult, {"temp": 97.0, "vida": 0.7, "tipo": "est", "perda_volta": 0.01, "voltas": 3})
assert "~97°C" in tx and any(t.startswith("real, h") for t in tx) and "88" in tx, tx
assert not any(t.endswith("°C") and not t.startswith("~") for t in tx), tx
# d) nada: "--", sem numero inventado
tx = cartao(None, None, {"temp": None, "vida": None, "tipo": "est", "perda_volta": None, "voltas": 0})
assert "--" in tx and not any("°C" in t for t in tx), tx
print("5) pneus: real x estimado OK")

print("TODOS OS TESTES DA FASE 20.1 PASSARAM")
print("(dados SIMULADOS: nao substitui a validacao em sessao real; arquivos temporarios: %s)" % S)
