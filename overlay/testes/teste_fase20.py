"""Testes automatizados da Fase 20 (calculos criticos, perfis, log, desempenho).
Executar: py -3.12 testes\\teste_fase20.py   (ou executar_testes.bat). Nao precisa do iRacing aberto."""
import os, sys, ast, json, math, time as _time
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.argv = ["x", "--demo"]
PACOTE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACOTE)
from pathlib import Path
import overlay_iracing as o
import ov_nucleo as n
from PySide6.QtWidgets import QApplication
import tempfile
S = Path(tempfile.mkdtemp(prefix="overlay_testes_"))   # arquivos de teste ficam numa pasta temporaria
o.ARQ_LOG = S / "log_fase20.txt"; o.ARQ_CONFIG = S / "cfg_inexistente_f20.json"
o.ARQ_PENDENTE = S / "pend_f20.json"; o.ARQ_COMPARACAO = S / "comp_f20.csv"; o.ARQ_HISTORICO = S / "hist_f20.csv"
o.ARQ_RECORDES = S / "rec_f20.json"; o.ARQ_PNEUS = S / "pn_f20.json"; o.ARQ_MAPAS = S / "map_f20.json"
for f in (o.ARQ_LOG, o.ARQ_PENDENTE, o.ARQ_COMPARACAO, o.ARQ_HISTORICO, o.ARQ_RECORDES, o.ARQ_PNEUS, o.ARQ_MAPAS):
    if f.exists(): f.unlink()
app = QApplication([]); o.salvar_config = lambda c: None

def log():
    return o.ARQ_LOG.read_text(encoding="utf-8") if o.ARQ_LOG.exists() else ""

# ---------------------------------------------------------------- 1) nucleo isolado
src = open(os.path.join(PACOTE, "ov_nucleo.py"), encoding="utf-8").read()
mods = {a.name.split(".")[0] for x in ast.walk(ast.parse(src)) if isinstance(x, ast.Import) for a in x.names}
mods |= {x.module.split(".")[0] for x in ast.walk(ast.parse(src)) if isinstance(x, ast.ImportFrom) and x.module}
assert not (mods & {"PySide6", "irsdk", "overlay_iracing"}), mods          # sem Qt e sem SDK
assert all(v[0] in (n.REAL, n.CALCULADO, n.ESTIMADO) and v[1] for v in n.PROVENIENCIA.values())
assert n.tipo_do_dado("radar: lado lembrado") == n.ESTIMADO and n.tipo_do_dado("velocidade") == n.REAL
print("nucleo isolado + proveniencia OK")

# ---------------------------------------------------------------- 2) registro (log)
rel = [1000.0]
arq = S / "reg_f20.txt"
for f in (arq, Path(str(arq) + ".1")):
    if f.exists(): f.unlink()
r = n.Registro(lambda: arq, limite_bytes=400, relogio=lambda: rel[0])
assert r.aviso("a") and not r.aviso("a")                                    # aviso uma vez so
assert r.erro("x", "Traceback\nValueError: boom") and not r.erro("x", "Traceback\nValueError: boom")
assert r.calculo("c", 10, valor=1.5, nome="z") and not r.calculo("c", 10, valor=2)
rel[0] += 11; assert r.calculo("c", 10, valor=3)
assert "valor=1.500" in arq.read_text() and "calculo c" in arq.read_text()
for i in range(20): r.info("linha de enchimento %d" % i)                      # passa de 400 bytes -> rotaciona
assert Path(str(arq) + ".1").exists() and arq.stat().st_size < 1500
r.cabecalho({"overlay": "Fase 20", "python": "3.12"}); assert "overlay Fase 20 | python 3.12" in arq.read_text()
r2 = n.Registro(lambda: Path("/nao/existe/pasta/log.txt")); assert r2.info("x") is False   # nunca levanta excecao
assert n.variaveis_ausentes(lambda k: k != "B", ["A", "B", "C"]) == ["B"]
assert n.variaveis_ausentes(lambda k: 1 / 0, ["A"]) == ["A"]
print("registro OK")

# ---------------------------------------------------------------- 3) volta suja
f = n.motivo_volta_suja
assert f() is None and f(superficie=3) is None and f(superficie=None, reboque_s=0) is None
assert f(na_box=True) == "boxes" and f(superficie=0) == "fora da pista" and f(superficie=1) == "boxes"
assert f(superficie=2) == "boxes" and f(superficie=-1) == "fora do mundo" and f(reboque_s=12.0) == "reboque"
assert f(replay=True) == "replay" and f(superficie="x") is None
print("criterio de volta suja OK")

# ---------------------------------------------------------------- 4) limitador e desempenho
lim = n.Limitador()
assert lim.deve("a", 1.0, 0.0) and not lim.deve("a", 1.0, 0.5) and lim.deve("a", 1.0, 1.0) and lim.deve("b", 1.0, 0.1)
assert lim.deve("a", 1.0, 0.2)                                                # relogio voltou atras: libera
d = n.Desempenho(amostras=100, orcamento_ms=5.0)
for i in range(100): d.medir("ciclo", 1.0 if i < 94 else 20.0)
st = d.estatistica("ciclo"); assert st["n"] == 100 and abs(st["media"] - (94 + 120) / 100) < 1e-9 and st["max"] == 20.0
assert d.alerta(0.0) is None                                                   # media 2,14 < 5
for i in range(100): d.medir("ciclo", 9.0)
txt = d.alerta(10.0); assert txt and "lento" in txt and d.alerta(11.0) is None  # avisa uma vez
d.medir("pintura:radar", 2.0); d.medir("pintura:mapa", 4.0)
assert abs(d.custo_por_segundo({"radar": 30, "mapa": 10}) - (2 * 30 + 4 * 10)) < 1e-9
print("limitador e desempenho OK")

# ---------------------------------------------------------------- 5) perfis
g = n.GerenciadorPerfis()
cfg0 = {"x": 10, "y": 20, "escala": 1.0, "escala_x": None, "mostrar_radar": True, "x_radar": 5, "y_radar": 6,
        "classificacao_todas": True, "travado": False, "tema_moderno": True, "opacidade_fundo": .8, "pneu_lado_invertido": False}
ks = n.chaves_de_layout(cfg0)
assert set(ks) == {"x", "y", "escala", "escala_x", "mostrar_radar", "x_radar", "y_radar", "classificacao_todas"}, ks
g.inicializar(cfg0)
assert set(cfg0["perfis"]) == {"Treino", "Classificacao", "Corrida"}
assert all(cfg0["perfis"][p]["x_radar"] == 5 for p in n.PERFIS) and cfg0["perfil_modo"] == "auto"
assert "tema_moderno" not in cfg0["perfis"]["Treino"] and "travado" not in cfg0["perfis"]["Treino"]   # globais ficam fora
cfg0["x_radar"], cfg0["mostrar_radar"] = 500, False                              # edita no perfil ativo (Corrida)
assert g.trocar(cfg0, "Treino") and cfg0["x_radar"] == 5 and cfg0["mostrar_radar"] is True   # Treino = layout original
assert cfg0["perfis"]["Corrida"]["x_radar"] == 500 and cfg0["perfis"]["Corrida"]["mostrar_radar"] is False  # Corrida guardou
cfg0["x_radar"] = 77; assert g.trocar(cfg0, "Corrida") and cfg0["x_radar"] == 500 and cfg0["perfis"]["Treino"]["x_radar"] == 77
assert not g.trocar(cfg0, "Corrida") and not g.trocar(cfg0, "Inexistente")
assert n.perfil_da_sessao("CORRIDA") == "Corrida" and n.perfil_da_sessao("QUALIFICACAO") == "Classificacao"
assert n.perfil_da_sessao("AQUECIMENTO") == "Treino" and n.perfil_da_sessao("TESTE") == "Treino" and n.perfil_da_sessao(None) is None
sel = n.SeletorPerfil(g, 3.0)
cfg0["perfil_ativo"] = "Treino"
assert sel.decidir(cfg0, "CORRIDA", 0.0) is None and sel.decidir(cfg0, "CORRIDA", 2.0) is None   # ainda estabilizando
assert sel.decidir(cfg0, "CORRIDA", 3.1) == "Corrida"
assert sel.decidir(cfg0, "QUALIFICACAO", 10.0) is None and sel.decidir(cfg0, "CORRIDA", 11.0) is None  # oscilou: recomeca
assert sel.decidir(cfg0, "CORRIDA", 20.0, editando=True) is None                 # destravado: nao troca sozinho
cfg0["perfil_modo"] = "Treino"; cfg0["perfil_ativo"] = "Corrida"; assert g.escolher(cfg0, "CORRIDA") == "Treino"   # manual vence
cfg0["perfil_modo"] = "invalido"; g.inicializar(cfg0); assert cfg0["perfil_modo"] == "auto"
print("perfis (logica) OK")

# perfis + config real + janelas
cfg = o.carregar_config()
assert set(cfg["perfis"]) == {"Treino", "Classificacao", "Corrida"} and cfg["perfil_ativo"] == "Corrida"
assert cfg["x_radar"] == 60 and cfg["perfis"]["Treino"]["x_radar"] == 60 and cfg["mostrar_forca_g"] is True   # layout da Fase 18/19 intacto
classes = [o.JanelaTelemetria, o.JanelaVoltas, o.JanelaRelativo, o.JanelaClassificacao, o.JanelaMapa, o.JanelaRadar,
           o.JanelaPneus, o.JanelaSetores, o.JanelaClima, o.JanelaDanos, o.JanelaCombustivel, o.JanelaForcaG]
for C in classes:                                                              # TODA janela tem posicao/escala no perfil
    j = C(dict(cfg)); c = j.CHAVE
    for k in (j._chave("x"), j._chave("y"), j._chave("escala")):
        assert k in cfg["perfis"]["Treino"], (C.__name__, k)
    if C.CHAVE_ATIVO: assert C.CHAVE_ATIVO in cfg["perfis"]["Treino"], C.CHAVE_ATIVO
jr = o.JanelaRadar(cfg); jc = o.JanelaClima(cfg); jr.show(); jc.show()
o._PERFIS.trocar(cfg, "Treino")
cfg["x_radar"], cfg["y_radar"], cfg["escala_radar"], cfg["escala_x_radar"], cfg["mostrar_clima"] = 700, 300, 1.5, None, False
assert o._PERFIS.trocar(cfg, "Classificacao")                                  # volta ao layout padrao (copia original)
jr.recarregar_layout(); jc.recarregar_layout()
assert (jr.x(), jr.y()) == (60, 420) and jr.width() == 200 and jc.ativo and jc.isVisible()
assert o._PERFIS.trocar(cfg, "Treino")                                         # o Treino lembra o layout editado
jr.recarregar_layout(); jc.recarregar_layout()
assert (jr.x(), jr.y()) == (700, 300) and (jr.width(), jr.height()) == (300, 456) and not jc.ativo and not jc.isVisible()
# persistencia: salva em arquivo e relê
o.ARQ_CONFIG = S / "cfg_f20.json"
if o.ARQ_CONFIG.exists(): o.ARQ_CONFIG.unlink()
def salvar_real(c):
    o._PERFIS.capturar(c); o.ARQ_CONFIG.write_text(json.dumps(c, indent=2), encoding="utf-8")
salvar_real(cfg)
cfg2 = o.carregar_config()
assert cfg2["perfil_ativo"] == "Treino" and cfg2["x_radar"] == 700 and cfg2["perfis"]["Classificacao"]["x_radar"] == 60
assert cfg2["perfis"]["Treino"]["mostrar_clima"] is False and cfg2["perfis"]["Corrida"]["mostrar_clima"] is True
o.ARQ_CONFIG = S / "cfg_inexistente_f20.json"
print("perfis (config + janelas + persistencia) OK")

# ---------------------------------------------------------------- 6) comparar oficial
pend = {"ir_base": 2000, "ir_delta_proj": 40, "sr_base": 3.20, "sr_delta_proj": 0.10}
assert n.comparar_oficial(pend, 2000, 3.20) is None and n.comparar_oficial(None, 1, 1) is None
res = n.comparar_oficial(pend, 2025, 3.31)
assert res == {"ir_real": 25, "ir_proj": 40, "ir_erro": 15, "sr_real": 0.11, "sr_proj": 0.10, "sr_erro": -0.01}, res
assert n.comparar_oficial(pend, 2025, 3.20) == {"ir_real": 25, "ir_proj": 40, "ir_erro": 15}
print("comparacao com o oficial OK")

# ---------------------------------------------------------------- 7) delta: validacao
_ult = {}
def volta(dp, total, k, chave, motivo=None, na_box=False, inicio=0.0, pulo_em=None, saltos=100):
    """Simula a volta k (100 amostras, pct 0..0.99). Na 1a amostra, ultima_volta = tempo da volta ANTERIOR."""
    res = None
    for i in range(saltos):
        pct = i / saltos
        if pulo_em is not None and i >= pulo_em: pct = min(0.99, pct + 0.08)
        res = dp.atualizar(pct, pct * total, k, na_box, _ult.get(id(dp)), chave, motivo)
    _ult[id(dp)] = total
    return res
def completa(total):  # 1a volta so para inicializar o contador
    return total
A = (("s", 1), "pista", "carro")
dp = o.DeltaProprio()
volta(dp, 90.0, 0, A)                                  # volta 0 (saida)
volta(dp, 90.0, 1, A)                                  # fecha a volta 0? (ultima_volta=90 na transicao seguinte)
assert dp.pronto and abs(dp.ref_tempo - 90.0) < 1e-9                       # referencia criada com a volta limpa
volta(dp, 91.0, 2, A); assert abs(dp.ref_tempo - 90.0) < 1e-9              # mais lenta nao substitui
volta(dp, 89.0, 3, A, motivo="fora da pista")                              # volta MAIS RAPIDA mas suja
volta(dp, 92.0, 4, A); assert abs(dp.ref_tempo - 90.0) < 1e-9, dp.ref_tempo   # a suja nao virou referencia
assert "fora da pista" in log()
volta(dp, 88.0, 5, A, na_box=True); volta(dp, 95.0, 6, A)                  # volta de box mais rapida (fictica): nao vale
assert abs(dp.ref_tempo - 90.0) < 1e-9
volta(dp, 88.5, 7, A, pulo_em=50); volta(dp, 95.0, 8, A); assert abs(dp.ref_tempo - 90.0) < 1e-9   # salto de posicao
assert "salto" in log()
volta(dp, 88.0, 9, A); volta(dp, 95.0, 10, A); assert abs(dp.ref_tempo - 88.0) < 1e-9             # limpa e mais rapida: vale
# troca de sessao / pista / carro: descarta, mesmo com o mesmo contador de voltas
B = (("s", 2), "pista", "carro")
dp.atualizar(0.5, 40.0, 10, False, 95.0, B); assert not dp.pronto and dp._chave == B
dp2 = o.DeltaProprio(); volta(dp2, 90.0, 0, A); volta(dp2, 90.0, 1, A); assert dp2.pronto
dp2.atualizar(0.2, 18.0, 1, False, 90.0, (("s", 1), "outra pista", "carro")); assert not dp2.pronto
volta(dp2, 90.0, 0, A); volta(dp2, 90.0, 1, A); assert dp2.pronto
dp2.atualizar(0.2, 18.0, 1, False, 90.0, (("s", 1), "pista", "outro carro")); assert not dp2.pronto
assert "referencia descartada" in log() and "troca de sessao, pista ou carro" in log()
# sem chave = comportamento antigo (compatibilidade)
dp3 = o.DeltaProprio(); volta(dp3, 90.0, 0, None); volta(dp3, 90.0, 1, None); assert dp3.pronto
print("delta: validacao OK")

# ---------------------------------------------------------------- 8) setores: sessao e volta suja
rec = o.RecordesPessoais(S / "rec2_f20.json")
if (S / "rec2_f20.json").exists(): (S / "rec2_f20.json").unlink()
rec = o.RecordesPessoais(S / "rec2_f20.json")
an = o.AnaliseSetores(); an.definir_setores([0.0, 0.4, 0.7])
def volta_set(k, total, chave, motivo=None, sessao=("s", 1), na_box=False):
    for i in range(100):
        pct = i / 100
        an.atualizar(pct, pct * total, k, na_box, _ult.get(id(an)), chave, rec, motivo=motivo, sessao=sessao)
    _ult[id(an)] = total
volta_set(0, 80.0, "p|c"); volta_set(1, 80.0, "p|c"); volta_set(2, 80.0, "p|c")
assert an.ultima and an.ultima["valida"] and abs(an.ultima["tempo"] - 80.0) < 1e-9
volta_set(3, 70.0, "p|c", motivo="fora da pista"); volta_set(4, 81.0, "p|c")
assert an.ultima["valida"] is False and abs(an.ultima["tempo"] - 70.0) < 1e-9   # a volta suja (70 s) aparece, mas SEM setores
assert an.ultima["setores"] is None
reg = rec.obter("p|c"); assert abs(reg["melhor"] - 80.0) < 1e-9, reg
assert "volta nao registrada como recorde: motivo=fora da pista" in log()
an.atualizar(0.5, 10.0, 5, False, 81.0, "p|c", rec, sessao=("s", 2))        # sessao nova: estado reiniciado
assert an.ultima is None and an.observadas == 0 and abs(rec.obter("p|c")["melhor"] - 80.0) < 1e-9   # recorde em arquivo preservado
print("setores: validacao OK")

# ---------------------------------------------------------------- 9) radar: real x estimado
cfg = o.carregar_config()
pil = {i: {"numero": str(i), "classe_cor": (150, 150, 160)} for i in range(5)}
L = 4000.0
def pcts(*metros): return [0.5] + [0.5 + m / L for m in metros]
mem = {}
rd = o.montar_radar(pil, 0, pcts(3.0, 22.0), [3, 3, 3], [False] * 3, 2, L, memoria=mem, agora=100.0)
c1 = next(c for c in rd["carros"] if c["idx"] == 1); c2 = next(c for c in rd["carros"] if c["idx"] == 2)
assert c1["lado_fonte"] == "inferido" and c1["ident"] == "unica" and c1["faixa"] == -1.0 and c2["lado_fonte"] == "indef" and rd["sem_par"] == (0, 0)
rd = o.montar_radar(pil, 0, pcts(14.0, 22.0), [3, 3, 3], [False] * 3, 1, L, memoria=mem, agora=101.0)   # saiu da zona lateral
c1 = next(c for c in rd["carros"] if c["idx"] == 1)
assert c1["lado_fonte"] == "lembrado" and c1["faixa"] < 0, c1                                           # lado lembrado
rd = o.montar_radar(pil, 0, pcts(14.0, 22.0), [3, 3, 3], [False] * 3, 1, L, memoria=mem, agora=105.0)   # memoria expirou
assert next(c for c in rd["carros"] if c["idx"] == 1)["lado_fonte"] == "indef"
rd = o.montar_radar(pil, 0, pcts(20.0, 24.0), [3, 3, 3], [False] * 3, 2, L, memoria={}, agora=1.0)       # SDK acusa, ninguem perto
assert rd["sem_par"] == (1, 0) and all(c["lado_fonte"] == "indef" for c in rd["carros"])
assert o.fmt_dist_aprox(3.2) == "~3,0 m" and o.fmt_dist_aprox(3.3) == "~3,5 m" and o.fmt_dist_aprox(12.4) == "~12 m" and o.fmt_dist_aprox(None) == "--"
jr = o.JanelaRadar(dict(cfg)); jr.show()
d = o.Telemetria(demo=True).ler()
for t in range(40):
    d = o.Telemetria(demo=True)._demo_radar(float(t) * 0.4) if False else d
jr.atualizar(d); jr.grab().save(str(S / "f20_radar.png"))
d2 = dict(d); d2["radar"] = rd; jr.atualizar(d2); jr.grab()                    # com 'sem_par' desenha o aviso SDK
assert (jr.width(), jr.height()) == (o.LARGURA_RADAR, o.ALTURA_RADAR)
print("radar: SDK x estimado OK")

# ---------------------------------------------------------------- 10) telemetria real simulada (pneus, projecao, perfis, bloco lento, relatorio)
class IRFalso:
    is_initialized = True; is_connected = True
    def __init__(self, v): self.v = v
    def __getitem__(self, k): return self.v.get(k)
    def startup(self): return True
    def freeze_var_buffer_latest(self): pass
    def unfreeze_var_buffer_latest(self): pass
    def shutdown(self): pass
N = 12
drivers = [{"CarIdx": i, "UserName": f"Piloto {i}", "CarNumber": str(i), "CarClassID": 1, "CarClassShortName": "GT3", "CarClassColor": 0xffda59,
            "IRating": 2000 + i * 100, "LicString": "A 3.20", "LicColor": 0x0153db, "CarScreenName": "Porsche 911 GT3 R", "CarPath": "porsche992rgt3",
            "CarIsPaceCar": 0, "IsSpectator": 0, "UserID": 500 + i} for i in range(N)]
v = {"PlayerCarIdx": 0, "Speed": 0.0, "Gear": 1, "RPM": 1000.0, "Lap": 1, "LapCompleted": 0, "LapDistPct": .05, "LapCurrentLapTime": 5.0,
     "FuelLevel": 50.0, "OnPitRoad": True, "IsOnTrack": True, "SessionNum": 0, "SessionUniqueID": 1, "SessionState": 4,
     "PlayerTrackSurface": 1, "CarIdxLapDistPct": [(.05 + i * .01) % 1 for i in range(N)], "CarIdxTrackSurface": [3] * N,
     "CarIdxOnPitRoad": [False] * N, "CarIdxClassPosition": [i + 1 for i in range(N)], "CarIdxLapCompleted": [0] * N, "CarIdxLap": [1] * N,
     "CarIdxTireCompound": [0] * N, "CarIdxLastLapTime": [0.0] * N, "CarIdxBestLapTime": [0.0] * N, "CarLeftRight": 1,
     "LatAccel": 0.0, "LongAccel": 0.0, "TrackTemp": 30.0,
     "DriverInfo": {"Drivers": drivers, "DriverTires": [{"TireIndex": 0, "TireCompoundType": "Dry"}]},
     "WeekendInfo": {"TrackDisplayName": "Road America", "TrackLength": "6.52 km", "Official": 1, "SubSessionID": 777001, "Category": "Road"},
     "SessionInfo": {"Sessions": [{"SessionType": "Race"}]},
     "LFtempCL": 90.0, "LFtempCM": 91.0, "LFtempCR": 92.0, "LFwearL": 0.95, "LFwearM": 0.96, "LFwearR": 0.97}
tel = o.Telemetria(demo=False); tel.conectado = True; tel.ir = IRFalso(v)
relogio = [1000.0]; real_mono = o.time.monotonic; o.time.monotonic = lambda: relogio[0]
try:
    dd = tel.ler()
    assert dd["tipo_sessao"] == "CORRIDA"
    u = dd["pneus"]["ultima"]["LF"]
    assert u["temp"] == (90.0, 91.0, 92.0) and u["local"] == "boxes" and u["ao_vivo"] is True and u["vida_idade"] is not None
    assert dd["pneus"]["ultima"]["RF"]["temp"] is None                                # sem leitura: sem inventar
    v["Speed"], v["OnPitRoad"], v["PlayerTrackSurface"] = 50.0, False, 3               # saiu dos boxes; sensor parado
    for _ in range(5):
        relogio[0] += 1.0; dd = tel.ler()
    relogio[0] += 120.0; dd = tel.ler()
    u = dd["pneus"]["ultima"]["LF"]; assert dd["pneus"]["temp"]["LF"] is None and u["ao_vivo"] is False
    assert u["temp"] == (90.0, 91.0, 92.0) and 120 <= u["idade"] <= 135 and u["hora"] and u["local"] == "boxes"   # ultima real, com idade
    assert 120 <= u["vida_idade"] <= 135
    # janela mostra a ultima leitura esmaecida, com idade
    jp = o.JanelaPneus(dict(cfg)); jp.show(); jp.atualizar(dd); jp.grab().save(str(S / "f20_pneus_antiga.png"))
    # nova sessao: medicoes descartadas
    v["SessionUniqueID"] = 2; dd = tel.ler()
    assert dd["pneus"]["ultima"]["LF"]["idade"] is None or dd["pneus"]["ultima"]["LF"]["idade"] < 5
    assert "medicoes reais descartadas" in log()
    # bloco lento: classificacao calculada no maximo a cada 0,5 s
    chamadas = [0]; orig = tel._montar_classificacao
    def contar():
        chamadas[0] += 1; return orig()
    tel._montar_classificacao = contar; tel._cache_blocos.clear(); tel._limitador.esquecer()
    for _ in range(20):
        relogio[0] += 0.033; tel.ler()                                                # ~0,66 s em 20 ciclos
    assert 1 <= chamadas[0] <= 3, chamadas
    # variaveis ausentes registradas no log (uma vez por conexao/alteracao)
    assert "sdk: variaveis indisponiveis agora" in log() and "PitRepairLeft" in log()
    # SDK informou projecao: fim da corrida grava pendente; sessao seguinte compara com o oficial
    v["SessionUniqueID"] = 3; v["SessionState"] = 4
    tel.ler()
    v["SessionState"] = 5; v["CarIdxClassPosition"] = [1] + [i + 1 for i in range(1, N)]
    tel.ler()
    assert o.ARQ_PENDENTE.exists(), "pendente nao gravada"
    pen = json.loads(o.ARQ_PENDENTE.read_text())["projecoes"][0]; assert pen["estado"] == "pendente" and pen["ir_base"] == 2000 and pen["ir_delta_proj"] is not None
    assert "projecao: final da corrida (PROJETADA, nao oficial)" in log()
    drivers[0]["IRating"] = 2000 + int(pen["ir_delta_proj"]) - 7                       # oficial veio 7 pontos abaixo da projecao
    v["SessionUniqueID"] = 4; v["SessionState"] = 4; tel._pilotos = {}; tel._ultima_leitura_pilotos = 0.0
    v["WeekendInfo"]["SubSessionID"] = 777002                                          # Fase 20.1: outra corrida
    tel.ler()
    # Fase 20.2.1: a projecao NAO e mais apagada ao comparar; fica "provisoria" ate o resultado oficial
    assert o.ARQ_COMPARACAO.exists() and json.loads(o.ARQ_PENDENTE.read_text())["projecoes"][0]["estado"] == "provisoria"
    linhas = o.ARQ_COMPARACAO.read_text(encoding="utf-8-sig").splitlines()
    assert linhas[0].startswith("data;corrida_id;categoria;pista;status;ir_projetado") and ";7;" in linhas[1] + ";", linhas
    assert "projecao x OFICIAL" in log()
finally:
    o.time.monotonic = real_mono
print("telemetria (pneus, projecao x oficial, bloco lento, relatorio de variaveis) OK")

# faixa PROJETADO na janela Relativo
jrel = o.JanelaRelativo(dict(cfg)); jrel.show(); demo = o.Telemetria(demo=True).ler(); jrel.atualizar(demo)
jrel.grab().save(str(S / "f20_relativo.png"))
print("relativo com PROJETADO OK")

# ---------------------------------------------------------------- 11) repintura por taxa
class JanelaTeste(o.JanelaBase):
    CHAVE = "forca_g"; CHAVE_ATIVO = "mostrar_forca_g"; TAXA_HZ = 10.0
    def tamanho(self): return (100, 100)
    def paintEvent(self, e): pass
jt = JanelaTeste(dict(cfg))
cont = [0]; jt.update = lambda: cont.__setitem__(0, cont[0] + 1)
relogio = [50.0]; o.time.monotonic = lambda: relogio[0]
try:
    for i in range(300):                                     # 10 s a 30 ciclos/s
        relogio[0] += 1 / 30.0; jt.atualizar({"conectado": True})
    assert 95 <= cont[0] <= 105, cont[0]                     # ~10 Hz, nao 30 Hz
    o.JanelaBase.MULT_TAXA = 0.5; cont[0] = 0
    for i in range(300):
        relogio[0] += 1 / 30.0; jt.atualizar({"conectado": True})
    assert 45 <= cont[0] <= 55, cont[0]                      # modo economia: metade
finally:
    o.JanelaBase.MULT_TAXA = 1.0; o.time.monotonic = real_mono
assert {C.__name__: C.TAXA_HZ for C in classes}["JanelaClassificacao"] == 2.0
antes = sum(30.0 for _ in classes); depois = sum(C.TAXA_HZ for C in classes)
assert depois < antes * 0.5, (antes, depois)                  # menos da metade das repinturas por segundo
print("repintura por taxa OK (repinturas/s: %.0f -> %.0f)" % (antes, depois))

# medicao de pintura registrada
jx = o.JanelaForcaG(dict(cfg)); jx.show(); jx.atualizar(demo); jx.grab()
assert o.DESEMPENHO.estatistica("pintura:forca_g")["n"] >= 1

# ---------------------------------------------------------------- 12) cabecalho, prioridade
o.registrar_cabecalho(); assert "inicio: overlay 1.6.2 (base Fase 20.2.2) | nucleo 20.2.2" in log() and "PySide6" in log()
assert o.definir_prioridade_baixa(True) is False              # so atua no Windows
# ---------------------------------------------------------------- 13) orcamento: leitura e calculo com 40 carros
N = 40
drivers = [{"CarIdx": i, "UserName": f"P{i}", "CarNumber": str(i), "CarClassID": 1 + i % 2, "CarClassShortName": "GT3", "CarClassColor": 0xffda59,
            "IRating": 2000 + i * 30, "LicString": "A 3.20", "LicColor": 0x0153db, "CarScreenName": "Porsche", "CarPath": "p992",
            "CarIsPaceCar": 0, "IsSpectator": 0} for i in range(N)]
v.update({"DriverInfo": {"Drivers": drivers}, "CarIdxLapDistPct": [(.3 + i * .012) % 1 for i in range(N)], "CarIdxTrackSurface": [3] * N,
          "CarIdxOnPitRoad": [False] * N, "CarIdxClassPosition": [i // 2 + 1 for i in range(N)], "CarIdxLapCompleted": [4] * N, "CarIdxLap": [5] * N,
          "CarIdxTireCompound": [0] * N, "CarIdxLastLapTime": [100.0] * N, "CarIdxBestLapTime": [99.0] * N, "Speed": 60.0, "SessionUniqueID": 9})
tel2 = o.Telemetria(demo=False); tel2.conectado = True; tel2.ir = IRFalso(v)
for _ in range(30): tel2.ler()
t0 = _time.perf_counter()
for i in range(300): v["LapDistPct"] = (.3 + i * .0003) % 1; tel2.ler()
ms = (_time.perf_counter() - t0) / 300 * 1000
assert ms < 5.0, ms
print("ler() com 40 carros: %.2f ms/ciclo (orcamento 5 ms) OK" % ms)
assert "erro em" not in log(), [l for l in log().splitlines() if "erro em" in l]
print("TODOS OS TESTES DA FASE 20 PASSARAM")
print("(arquivos temporarios dos testes: %s)" % S)
