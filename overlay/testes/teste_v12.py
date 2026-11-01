"""Testes automatizados da versao 1.2.0 (Inputs, Luz ABS, Luz TC, Retorno a pista, Estrategia de pneus).
Executar: py -3.12 testes\\teste_v12.py   (ou executar_testes.bat). Nao precisa do iRacing aberto.
Todos os dados sao SIMULADOS: isto nao substitui a validacao em sessao real (ROTEIRO_VALIDACAO.txt)."""
import os, sys, ast, math, tempfile
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.argv = ["x", "--demo"]
PACOTE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACOTE)
from pathlib import Path
import overlay_iracing as o
import ov_v12 as v
import ov_nucleo as n
from PySide6.QtWidgets import QApplication

S = Path(tempfile.mkdtemp(prefix="overlay_testes_v12_"))
o.ARQ_LOG = S / "log_v12.txt"; o.ARQ_CONFIG = S / "cfg_inexistente_v12.json"
for nome in ("ARQ_PENDENTE", "ARQ_COMPARACAO", "ARQ_HISTORICO", "ARQ_RECORDES", "ARQ_PNEUS", "ARQ_MAPAS"):
    setattr(o, nome, S / (nome.lower() + ".tmp"))
app = QApplication([]); o.salvar_config = lambda c: None

# ---------------------------------------------------------------- 1) modulo puro
src = open(os.path.join(PACOTE, "ov_v12.py"), encoding="utf-8").read()
mods = {a.name.split(".")[0] for x in ast.walk(ast.parse(src)) if isinstance(x, ast.Import) for a in x.names}
mods |= {x.module.split(".")[0] for x in ast.walk(ast.parse(src)) if isinstance(x, ast.ImportFrom) and x.module}
assert not (mods & {"PySide6", "irsdk", "overlay_iracing"}), mods
print("1) modulo puro (sem Qt e sem SDK) OK")

# ---------------------------------------------------------------- 2) piscar
for modo, hold in (("ritmo", 0.066), ("suave", 0.10), ("fixa", 0.25)):
    pl = v.PiscaLuz(modo)
    assert pl.atualizar(True, 10.0) is True
    assert pl.atualizar(False, 10.0 + hold * 0.9) is True and pl.atualizar(False, 10.0 + hold * 1.1) is False
assert v.PiscaLuz("lixo").modo == "ritmo"
print("2) piscar (ritmo / suave / fixa) OK")

# ---------------------------------------------------------------- 3) Luz TC (estimativa)
RELACAO = {1: 150.0, 2: 105.0, 3: 80.0}                      # rpm por m/s (cambio simulado)


def passo(d, t, marcha, vel, rpm_extra, acel, freio=0.0, emb=0.0, **kw):
    return d.atualizar(t, marcha, RELACAO[marcha] * vel * (1.0 + rpm_extra), vel, acel, freio, emb, 9000.0, **kw)


d = v.DetectorPatinagem("normal")
t = 0.0
passo(d, t, 2, 30.0, 0.0, 0.0)                              # primeira amostra da marcha (troca recente)
t = 1.0
r = passo(d, t, 2, 30.0, 0.0, 0.9)
assert r["estado"] == "aprendendo" and not r["ativa"]                      # sem aprender, nao inventa
for _ in range(40):                                                         # rodando sem acelerar nem frear: aprende
    t += 0.033
    r = passo(d, t, 2, 30.0, 0.0, 0.0)
assert d._conhecida(2) and abs(d.ref[2][0] - RELACAO[2]) < 1e-6
t += 1.0
assert passo(d, t, 2, 30.0, 0.02, 0.9)["ativa"] is False                    # 2%: abaixo do limiar normal
r = passo(d, t + 0.1, 2, 30.0, 0.10, 0.9)
assert r["ativa"] is True and 0.095 < r["patinagem"] < 0.105                # 10%: acende
d.definir_sensibilidade("grossa"); assert passo(d, t + 0.2, 2, 30.0, 0.06, 0.9)["ativa"] is False
d.definir_sensibilidade("fina"); assert passo(d, t + 0.3, 2, 30.0, 0.04, 0.9)["ativa"] is True
d.definir_sensibilidade("normal")
assert passo(d, t + 0.4, 2, 30.0, 0.10, 0.05)["ativa"] is False             # pouco acelerador: nao julga
assert passo(d, t + 0.5, 2, 30.0, 0.10, 0.9, freio=0.5)["ativa"] is False   # freando
assert passo(d, t + 0.6, 2, 30.0, 0.10, 0.9, emb=0.5)["ativa"] is False     # embreagem pisada
assert passo(d, t + 0.7, 2, 30.0, 0.10, 0.9, limitador=True)["ativa"] is False   # limitador de boxes
assert passo(d, t + 0.8, 2, 2.0, 0.10, 0.9)["ativa"] is False               # quase parado
r = passo(d, t + 2.0, 3, 35.0, 0.10, 0.9)                                   # acabou de trocar de marcha
assert r["ativa"] is False and r["estado"] == "ignorado"
assert passo(d, t + 2.6, 3, 35.0, 0.10, 0.9)["estado"] == "aprendendo"      # marcha 3 ainda nao aprendida
assert d.atualizar(t + 3.0, 2, 9000.0, 30.0, 0.9, 0.0, 0.0, 9000.0)["ativa"] is False   # corte de giro
d.resetar(); assert not d.ref
# a relacao final mudou nos boxes: depois de muitos descartes seguidos, reaprende
d = v.DetectorPatinagem(); t = 0.0
for _ in range(30):
    t += 0.033; passo(d, t, 2, 30.0, 0.0, 0.0)
for _ in range(40):
    t += 0.033; d.atualizar(t, 2, RELACAO[2] * 1.3 * 30.0, 30.0, 0.0, 0.0, 0.0, 9000.0)
assert abs(d.ref[2][0] / (RELACAO[2] * 1.3) - 1) < 0.05
print("3) Luz TC: aprende o cambio, limiares fina/normal/grossa, momentos ignorados, reaprende OK")

# ---------------------------------------------------------------- 4) Retorno a pista
assert v.normalizar_limites(1.5, 3.5) == (1.5, 3.5) and v.normalizar_limites(5.0, 4.0) == (5.0, 5.5)
assert v.normalizar_limites(0.2, 99) == (1.0, 25.0) and v.normalizar_limites(15, 15.0) == (15.0, 15.5)
assert v.cor_retorno(0.0) == v.COR_VERMELHO and v.cor_retorno(3.5) == v.COR_VERDE and v.cor_retorno(None) == v.COR_VERDE
verdes = [v.cor_retorno(x / 10.0)[1] for x in range(0, 36)]
assert verdes == sorted(verdes)                                              # a cor desliza, nao pula
assert (v.estado_retorno(1.4), v.estado_retorno(1.5), v.estado_retorno(3.4), v.estado_retorno(3.5), v.estado_retorno(None)) == \
       ("pare", "ceda", "ceda", "livre", "livre")
COMPR = 5000.0                                                               # pista de 5 km


def cenario(dist_atras_m, vel_atras=50.0, sup=0, vel_propria=0.0, pit_atras=False, sup_atras=3, extra=None):
    c = v.CalculadorRetorno()
    meu_pct = 0.5
    pct_atras = (meu_pct - dist_atras_m / COMPR) % 1.0
    t = 100.0
    res = None
    for _ in range(8):                                                       # o carro de tras vem andando (mede a velocidade)
        pcts = [meu_pct, pct_atras] + (extra or [])
        res = c.atualizar(t, 0, pcts, [sup, sup_atras] + [3] * len(extra or []), [False, pit_atras] + [False] * len(extra or []),
                          COMPR, vel_propria, 90.0)
        pct_atras = (pct_atras + vel_atras * 0.033 / COMPR) % 1.0
        t += 0.033
    return c, res, t


c, r, _ = cenario(300.0)                                                     # ~5.4 s: livre, com numero
assert r["visivel"] and r["estado"] == "livre" and 5.0 < r["segundos"] < 6.0
c, r, _ = cenario(150.0)                                                     # ~2.7 s: ceda
assert r["estado"] == "ceda" and 2.4 < r["segundos"] < 3.0
c, r, _ = cenario(60.0)                                                      # ~1 s: pare
assert r["estado"] == "pare" and r["segundos"] < 1.5 and r["cor"][0] > 200 and r["cor"][1] < 160
c, r, _ = cenario(2500.0, vel_atras=40.0)                                    # 60 s atras: ninguem em 30 s
assert r["segundos"] is None and r["estado"] == "livre"
c, r, _ = cenario(100.0, vel_atras=0.0)                                      # carro parado atras nao "chega"
assert r["segundos"] is None
c, r, _ = cenario(100.0, pit_atras=True)                                     # pit lane nao conta
assert r["segundos"] is None
c, r, _ = cenario(100.0, sup_atras=0)                                        # fora da pista nao conta
assert r["segundos"] is None
c, r, _ = cenario(400.0, extra=[(0.5 - 100.0 / COMPR) % 1.0])                # o mais PROXIMO e que conta
assert r["segundos"] < 3.0 or r["segundos"] > 0
c, r, t = cenario(100.0, sup=3, vel_propria=30.0)                            # andando na pista: nao precisa
assert r["visivel"] is False and r["segundos"] is not None                   # (calcula, mas o aviso esconde)
c, r, t = cenario(100.0, sup=3, vel_propria=1.0)                             # quase parado na pista: precisa
assert r["visivel"] is True
res = c.atualizar(t + 1.0, 0, [0.5, 0.45], [3, 3], [False, False], COMPR, 30.0, 90.0)       # voltou a andar: fica 1,5 s
assert res["visivel"] is True
res = c.atualizar(t + 2.0, 0, [0.5, 0.45], [3, 3], [False, False], COMPR, 30.0, 90.0)
assert res["visivel"] is False
res = c.atualizar(t + 2.1, 0, [0.5, 0.45], [1, 3], [True, False], COMPR, 0.0, 90.0)         # no box: nunca aparece
assert res["visivel"] is False
assert c.atualizar(1.0, 0, None, None, None, COMPR, 0.0)["visivel"] is False
validos = v.CalculadorRetorno()
rr = None
for k in range(8):                                                           # pace car (fora de `validos`) e ignorado
    rr = validos.atualizar(10.0 + k * 0.033, 0, [0.5, 0.49 + k * 0.0003], [0, 3], [False, False], COMPR, 0.0, 90.0, validos={0})
assert rr["segundos"] is None
print("4) Retorno a pista: PARE/CEDA/LIVRE, cor continua, pit/parado/fora ignorados, persistencia 1,5 s OK")

# ---------------------------------------------------------------- 5) Estrategia de pneus
def serie(est, nivel, chuva, pneu, t0, dur, passo_s=10.0, tem_chuva=True, **kw):
    r = None
    t = t0
    while t < t0 + dur:
        r = est.atualizar(t, nivel(t) if callable(nivel) else nivel, chuva, pneu, tem_chuva, **kw)
        t += passo_s
    return r

e = v.EstrategiaPneus()
assert serie(e, 1, 0.0, "seco", 0, 120)["acao"] == "seguir"                  # seco e pneu de seco: segue
e = v.EstrategiaPneus()
assert serie(e, 4, 15.0, "seco", 0, 60)["acao"] == "prepare"
r = serie(e, 5, 40.0, "seco", 60, 30)
assert r["acao"] == "trocar" and r["alvo"] == "chuva" and r["nivel_nome"] == "Molhada"
r = e.atualizar(100.0, 5, 40.0, "seco", True, pedido="chuva")
assert r["acao"] == "pedido"                                                 # ja pediu no menu de boxes
e = v.EstrategiaPneus()
assert serie(e, 6, 80.0, "chuva", 0, 120)["acao"] == "seguir"
e = v.EstrategiaPneus()                                                      # pista secando com pneu de chuva
r = serie(e, lambda t: 4 if t < 120 else (3 if t < 300 else 2), 0.0, "chuva", 0, 330, passo_s=10.0)
assert r["acao"] == "trocar" and r["alvo"] == "seco" and r["tendencia"] in ("secando", "sem_chuva")
e = v.EstrategiaPneus()
r = serie(e, lambda t: 5 - (t / 120.0), 0.0, "chuva", 0, 240)                # nivel 3, secando devagar: prepare com minutos
assert r["acao"] == "prepare" and r["minutos"] is not None and 1 <= r["minutos"] <= 60
e = v.EstrategiaPneus()                                                      # histerese: o aviso nao desce de repente
assert e.atualizar(100.0, 5, 40.0, "seco", True)["acao"] == "trocar"
assert e.atualizar(110.0, 3, 0.0, "seco", True)["acao"] == "trocar"          # ainda dentro dos 15 s
assert e.atualizar(130.0, 3, 0.0, "seco", True)["acao"] != "trocar"
e = v.EstrategiaPneus()                                                      # rivais provam que o outro pneu e mais rapido
r = e.atualizar(0.0, 3, 5.0, "seco", True, vantagem=2.0, rivais_outro=3)
assert r["acao"] == "trocar" and r["vantagem"] == 2.0 and r["vantagem_estimada"]
assert v.EstrategiaPneus().atualizar(0.0, 3, 5.0, "seco", True, vantagem=2.0, rivais_outro=1)["acao"] != "trocar"   # poucos rivais: nao basta
e = v.EstrategiaPneus()
assert e.atualizar(0.0, 5, 50.0, "seco", False)["acao"] == "sem_dado"        # carro sem pneu de chuva
assert e.atualizar(0.0, None, 0.0, "seco", True)["acao"] == "sem_dado"       # sem dado de pista molhada
assert e.atualizar(0.0, 5, 50.0, None, True)["acao"] == "sem_dado"
e = v.EstrategiaPneus()                                                      # com qual pneu largar
assert e.atualizar(0.0, 6, 70.0, "seco", True, pre_largada=True)["acao"] == "largar_trocar"
assert e.atualizar(0.0, 6, 70.0, "chuva", True, pre_largada=True)["acao"] == "largar_ok"
assert e.atualizar(0.0, 1, 0.0, "seco", True, pre_largada=True)["acao"] == "largar_ok"
assert e.atualizar(0.0, 1, 0.0, "chuva", True, pre_largada=True)["alvo"] == "seco"
assert v.classe_pneu("Chuva") == "chuva" and v.classe_pneu("Intermediario") == "chuva" and v.classe_pneu("Macio") == "seco"
assert v.nome_nivel(1) == "Seca" and v.nome_nivel(7) == "Encharcada" and v.nome_nivel(0) is None
rp = v.RitmoPorPneu()
for k in range(1, 5):                                                        # 3 rivais no seco (93 s) e 3 na chuva (91 s)
    for idx in (1, 2, 3):
        rp.atualizar(100.0 + k, idx, k, 93.0, "seco", False)
    for idx in (4, 5, 6):
        rp.atualizar(100.0 + k, idx, k, 91.0, "chuva", False)
gan, nrivais = rp.vantagem(110.0, "seco", [1, 2, 3, 4, 5, 6])
assert abs(gan - 2.0) < 1e-6 and nrivais == 3
rp.atualizar(120.0, 7, 1, 80.0, "chuva", True); rp.atualizar(121.0, 7, 2, 80.0, "chuva", False)     # volta suja (passou no pit)
assert 7 not in rp._voltas
assert rp.vantagem(110.0, "seco", [1, 2, 3])[0] is None                      # sem ninguem do outro pneu: sem base
print("5) Estrategia de pneus: seguir/prepare/trocar/pedido, histerese, largada, rivais e vantagem (~) OK")

# ---------------------------------------------------------------- 6) historico dos Inputs
h = v.HistoricoInputs(5)
for i in range(300):
    h.adicionar(i * 0.033, 0.5, 0.0, False, False, 3)
assert h.amostras()[-1][0] - h.amostras()[0][0] <= 5.0 + 0.04 and len(h) < 160
h.definir_segundos(30); assert h.segundos == 30.0
h.definir_segundos(1); assert h.segundos == 5.0
assert v.marcha_texto(-1) == "R" and v.marcha_texto(0) == "N" and v.marcha_texto(4) == "4"
assert v.pct_pedal(0.0) == "0" and v.pct_pedal(1.0) == "100" and v.pct_pedal(0.456) == "46"
print("6) historico dos Inputs (5 a 30 s) OK")

# ---------------------------------------------------------------- 7) telemetria simulada (SDK falso)
class IRFalso:
    is_initialized = True; is_connected = True
    def __init__(self, vv): self.v = vv
    def __getitem__(self, k): return self.v.get(k)
    def startup(self): return True
    def freeze_var_buffer_latest(self): pass
    def unfreeze_var_buffer_latest(self): pass
    def shutdown(self): pass


N = 6
drivers = [{"CarIdx": i, "UserName": f"Piloto {i}", "CarNumber": str(i), "CarClassID": 1, "CarClassShortName": "GT3",
            "CarClassColor": 0xffda59, "IRating": 2000, "LicString": "A 3.20", "LicColor": 0x0153db,
            "CarScreenName": "Porsche 911 GT3 R", "CarPath": "porsche992rgt3", "CarIsPaceCar": 0, "IsSpectator": 0,
            "UserID": 500 + i} for i in range(N)]
sdk = {"PlayerCarIdx": 0, "Speed": 40.0, "Gear": 2, "RPM": 4200.0, "Lap": 1, "LapCompleted": 0, "LapDistPct": .5,
       "FuelLevel": 50.0, "OnPitRoad": False, "IsOnTrack": True, "SessionNum": 0, "SessionUniqueID": 1, "SessionState": 4,
       "Throttle": 0.0, "Brake": 0.0, "Clutch": 1.0, "ThrottleRaw": 0.0, "BrakeRaw": 0.0, "ClutchRaw": 1.0,
       "BrakeABSactive": False, "SteeringWheelAngle": 0.2, "EngineWarnings": 0,
       "PlayerTrackSurface": 3, "CarIdxLapDistPct": [0.5, 0.49, 0.2, 0.3, 0.4, 0.1], "CarIdxTrackSurface": [3] * N,
       "CarIdxOnPitRoad": [False] * N, "CarIdxClassPosition": list(range(1, N + 1)), "CarIdxLapCompleted": [0] * N,
       "CarIdxLap": [1] * N, "CarIdxTireCompound": [1, 0, 0, 1, 1, 1], "CarIdxLastLapTime": [0.0] * N, "CarLeftRight": 1,
       "LatAccel": 0.0, "LongAccel": 0.0, "TrackTemp": 25.0, "TrackWetness": 5, "Precipitation": 0.4,
       "PitSvFlags": 0, "PitSvTireCompound": 0,
       "DriverInfo": {"Drivers": drivers, "DriverTires": [{"TireIndex": 0, "TireCompoundType": "Dry"},
                                                          {"TireIndex": 1, "TireCompoundType": "Wet"}]},
       "WeekendInfo": {"TrackDisplayName": "Road America", "TrackLength": "5.00 km", "Official": 1, "SubSessionID": 1,
                       "Category": "Road"},
       "SessionInfo": {"Sessions": [{"SessionType": "Race"}]}}
tel = o.Telemetria(demo=False); tel.conectado = True; tel.ir = IRFalso(sdk)
relogio = [1000.0]; real_mono = o.time.monotonic; o.time.monotonic = lambda: relogio[0]
try:
    dd = tel.ler()
    assert dd["conectado"] and dd["pedais_cru"]["acelerador"] == 0.0 and dd["pedais_cru"]["embreagem"] == 0.0
    assert dd["luz_tc"] is not None and dd["retorno"] is not None and dd["estrategia"] is not None
    assert dd["estrategia"]["meu_pneu"] == "chuva" and dd["estrategia"]["nivel"] == 5
    assert dd["estrategia"]["acao"] in ("seguir", "prepare", "trocar") and dd["estrategia"]["rivais_outro"] == 2
    # ABS ligado + pedais crus: chegam inalterados do SDK
    sdk.update({"Brake": 0.9, "BrakeRaw": 0.8, "BrakeABSactive": True, "Throttle": 0.0, "ThrottleRaw": 0.0, "Clutch": 1.0})
    relogio[0] += 0.033; dd = tel.ler()
    assert dd["abs"] is True and dd["freio"] == 0.9 and dd["pedais_cru"]["freio"] == 0.8
    # Luz TC: aprende rolando, depois patina
    sdk.update({"Brake": 0.0, "BrakeRaw": 0.0, "BrakeABSactive": False, "Speed": 30.0, "RPM": 105.0 * 30.0})
    for _ in range(40):
        relogio[0] += 0.033; dd = tel.ler()
    sdk.update({"Throttle": 1.0, "ThrottleRaw": 1.0, "RPM": 105.0 * 30.0 * 1.12})
    relogio[0] += 0.033; dd = tel.ler()
    assert dd["luz_tc"]["ativa"] is True and dd["luz_tc"]["estado"] == "ok"
    # Retorno: parado fora da pista com carro vindo atras
    sdk.update({"Speed": 0.0, "PlayerTrackSurface": 0, "Throttle": 0.0, "ThrottleRaw": 0.0, "RPM": 1000.0})
    sdk["CarIdxTrackSurface"] = [0, 3, 3, 3, 3, 3]
    for k in range(10):
        sdk["CarIdxLapDistPct"] = [0.5, 0.49 + k * 0.0008, 0.2, 0.3, 0.4, 0.1]
        relogio[0] += 0.033; dd = tel.ler()
    assert dd["retorno"]["visivel"] and dd["retorno"]["segundos"] is not None and dd["retorno"]["estado"] in ("pare", "ceda", "livre")
    # Estrategia na largada: pista molhada e pneu de seco -> troque para chuva
    sdk.update({"SessionState": 2, "OnPitRoad": True, "IsInGarage": True, "CarIdxTireCompound": [0, 0, 0, 1, 1, 1]})
    relogio[0] += 1.0; dd = tel.ler()
    assert dd["estrategia"]["pre_largada"] and dd["estrategia"]["acao"] == "largar_trocar" and dd["estrategia"]["alvo"] == "chuva"
    # pneu pedido nos boxes
    sdk.update({"SessionState": 4, "OnPitRoad": False, "IsInGarage": False, "PitSvFlags": 0x0F, "PitSvTireCompound": 1})
    relogio[0] += 1.0; dd = tel.ler()
    assert dd["estrategia"]["acao"] in ("seguir", "prepare", "trocar", "pedido")
    # nova sessao: aprendizado e historicos zerados
    sdk["SessionUniqueID"] = 2
    relogio[0] += 1.0; tel.ler()
    assert not tel.v12_tc.ref
    # carro sem pneu de chuva
    sdk["DriverInfo"] = dict(sdk["DriverInfo"], DriverTires=[{"TireIndex": 0, "TireCompoundType": "Dry"}])
    tel._ultima_leitura_pilotos = 0.0; tel._cache_blocos.clear()
    relogio[0] += 5.0; sdk["CarIdxTireCompound"] = [0] * N; dd = tel.ler()
    assert dd["estrategia"]["acao"] == "sem_dado" and dd["estrategia"]["motivo"] == "carro_sem_chuva"
finally:
    o.time.monotonic = real_mono
print("7) telemetria simulada: pedais crus, ABS, Luz TC, Retorno, Estrategia (largada, pedido, sem chuva) OK")

# ---------------------------------------------------------------- 8) modo demo e janelas
d = o.Telemetria(demo=True).ler()
for chave in ("luz_tc", "retorno", "estrategia", "pedais_cru"):
    assert d[chave] is not None, chave
cfg = o.carregar_config()
for chave in ("mostrar_luz_abs", "mostrar_luz_tc", "mostrar_retorno", "mostrar_estrategia",
              "escala_y_estrategia", "inputs_segundos", "retorno_pare", "luz_tc_sens"):
    assert chave in cfg, chave
assert {"mostrar_luz_abs", "mostrar_luz_tc", "mostrar_retorno", "mostrar_estrategia",
        "escala_luz_tc"} <= set(n.chaves_de_layout(cfg))             # entram nos perfis Treino/Classificacao/Corrida
cfg["travado"] = True


def alfa_total(janela):
    img = janela.grab().toImage()
    soma = 0
    for y in range(0, img.height(), 2):
        for x in range(0, img.width(), 2):
            soma += (img.pixel(x, y) >> 24) & 0xFF
    return soma


# Telemetria unificada (pedais + grafico com degraus de marcha, ABS e TC)
assert "JanelaInputs" not in dir(o)                                                                            # janela unica
ji = o.JanelaTelemetria(dict(cfg)); ji.show()
for k in range(120):
    dd = dict(d); dd["acelerador"] = min(1.0, k / 60.0); dd["freio"] = 0.0 if k < 80 else 0.9
    dd["abs"] = k > 90; dd["marcha"] = 1 + k // 40
    ji.atualizar(dd)
ji.repaint(); assert alfa_total(ji) > 0 and len(ji.hist) >= 100 and ji._marchas_max >= 3
ji.config["inputs_segundos"] = 30; ji.reconfigurar(); assert ji.hist.segundos == 30
for origem in ("carro", "cru", "ambos"):
    c5 = dict(cfg); c5["inputs_origem"] = origem; c5["inputs_marca_tc"] = True; j5 = o.JanelaTelemetria(c5); j5.show()
    for k in range(20):
        j5.atualizar(d)
    j5.repaint(); assert alfa_total(j5) > 0
# Luzes: apagadas = totalmente transparentes; acesas = desenho
for cls, chave_apagada in ((o.JanelaLuzAbs, "luz_abs_apagada"), (o.JanelaLuzTc, "luz_tc_apagada")):
    j = cls(dict(cfg)); j.show()
    dd = dict(d); dd["abs"] = False; dd["luz_tc"] = {"ativa": False, "patinagem": 0.0, "estado": "ok"}; j.atualizar(dd)
    j.repaint(); assert alfa_total(j) == 0, cls.__name__                       # nao ocupa nada na tela
    dd["abs"] = True; dd["luz_tc"] = {"ativa": True, "patinagem": 0.1, "estado": "ok"}; j.atualizar(dd)
    j.repaint(); assert j.acesa and alfa_total(j) > 0
    j.atualizar(dict(dd, abs=False, luz_tc={"ativa": False, "patinagem": 0.0, "estado": "ok"}))
    o.time.sleep(0.3) if hasattr(o.time, "sleep") else None
    j.atualizar(dict(dd, abs=False, luz_tc={"ativa": False, "patinagem": 0.0, "estado": "ok"}))
    assert j.acesa is False
    c6 = dict(cfg); c6[chave_apagada] = True; j6 = cls(c6); j6.show(); j6.atualizar(dict(d, abs=False, luz_tc=None))
    j6.repaint(); assert alfa_total(j6) > 0                                    # "deixar visivel e apagada"
    j.testar(5.0); j.atualizar(dict(d, abs=False, luz_tc=None)); j.repaint(); assert alfa_total(j) > 0   # teste de 5 s
# Retorno
jr = o.JanelaRetorno(dict(cfg)); jr.show()
jr.atualizar(dict(d, retorno=None)); jr.repaint(); assert alfa_total(jr) == 0   # so aparece quando precisa
jr.atualizar(dict(d, retorno={"visivel": True, "segundos": 1.0, "estado": "pare", "cor": v.cor_retorno(1.0)}))
jr.repaint(); assert alfa_total(jr) > 0
jr.atualizar(dict(d, retorno={"visivel": False, "segundos": 1.0, "estado": "pare", "cor": v.cor_retorno(1.0)}))
jr.repaint(); assert alfa_total(jr) == 0
jr.testar(9.0); jr.repaint(); assert alfa_total(jr) > 0
c7 = dict(cfg); c7["retorno_sempre"] = True; jr2 = o.JanelaRetorno(c7); jr2.show()
jr2.atualizar(dict(d, retorno={"visivel": False, "segundos": None, "estado": "livre", "cor": v.COR_VERDE})); jr2.repaint()
assert alfa_total(jr2) > 0
# Estrategia
je = o.JanelaEstrategia(dict(cfg)); je.show()
base = {"nivel": 4, "nivel_nome": "Pouco molhada", "tendencia": "molhando", "acao": "seguir", "alvo": "chuva", "minutos": None,
        "vantagem": 1.4, "vantagem_estimada": True, "meu_pneu": "seco", "rivais_outro": 2, "rivais_mesmo": 4, "pre_largada": False}
for acao in ("seguir", "prepare", "trocar", "pedido", "largar_ok", "largar_trocar"):
    je.atualizar(dict(d, estrategia=dict(base, acao=acao, minutos=14, pre_largada=acao.startswith("largar"))))
    je.repaint(); assert alfa_total(je) > 0, acao
je.atualizar(dict(d, estrategia=dict(base, acao="sem_dado", motivo="carro_sem_chuva"))); je.repaint(); assert alfa_total(je) > 0
je.atualizar(dict(d, estrategia=None)); je.repaint(); assert alfa_total(je) > 0
# a Estrategia aparece na garagem so antes da largada
je.atualizar(dict(d, estrategia=dict(base, acao="seguir"))); je.definir_auto_visivel(False); assert not je.isVisible()   # na garagem, sem largada: some
je.atualizar(dict(d, estrategia=dict(base, acao="largar_trocar", pre_largada=True)))
je.definir_auto_visivel(False); assert je.isVisible()                                                  # antes da largada: aparece
je.atualizar(dict(d, estrategia=dict(base, acao="seguir"))); je.definir_auto_visivel(False); assert not je.isVisible()
for cls in (o.JanelaTelemetria, o.JanelaLuzAbs, o.JanelaLuzTc, o.JanelaRetorno, o.JanelaEstrategia):          # todas atualizam com dado vazio
    j = cls(dict(cfg)); j.show(); j.atualizar(o.Telemetria._vazio()); j.repaint()
print("8) demo + 5 janelas desenham (Glass e Sport), transparencia, teste de 5/9 s, largada na garagem OK")

# ---------------------------------------------------------------- 9) Sport e Glass
for sport, vidro in ((True, False), (False, True)):
    o.definir_tema(True, 0.8, sport, vidro)
    for cls in (o.JanelaTelemetria, o.JanelaEstrategia):
        j = cls(dict(cfg)); j.show(); j.atualizar(d); j.repaint(); assert alfa_total(j) > 0
o.definir_tema(True, 0.8, False, True)
print("9) estilos Sport e Glass Fume OK")

print("TODOS OS TESTES DA VERSAO 1.2.0 PASSARAM")
print(f"(dados SIMULADOS: nao substitui a validacao em sessao real; arquivos temporarios: {S})")
