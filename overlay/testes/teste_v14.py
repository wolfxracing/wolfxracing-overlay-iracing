"""Testes automatizados da versao 1.4.0 no iRacing (janela Curvas: velocidade minima por curva).
Executar: py -3.12 testes\\teste_v14.py   (ou executar_testes.bat). Nao precisa do iRacing aberto.
Dados SIMULADOS: nao substitui a validacao em pista real (ROTEIRO_VALIDACAO.txt)."""
import math
import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.argv = ["x", "--demo"]
PACOTE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACOTE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import overlay_iracing as o
import ov_nucleo as n
from PySide6.QtWidgets import QApplication
import teste_curvas as tc

S = Path(tempfile.mkdtemp(prefix="overlay_testes_v14_"))
o.ARQ_LOG = S / "log_v14.txt"; o.ARQ_CONFIG = S / "cfg_inexistente_v14.json"
for nome in ("ARQ_PENDENTE", "ARQ_COMPARACAO", "ARQ_HISTORICO", "ARQ_RECORDES", "ARQ_PNEUS", "ARQ_MAPAS"):
    setattr(o, nome, S / (nome.lower() + ".tmp"))
app = QApplication([]); o.salvar_config = lambda c: None

# ---- 1) configuracao
cfg = o.carregar_config()
for chave in ("x_curvas", "y_curvas", "mostrar_curvas", "escala_curvas", "escala_x_curvas", "escala_y_curvas"):
    assert chave in cfg, chave
assert {"x_curvas", "y_curvas", "mostrar_curvas", "escala_curvas"} <= set(n.chaves_de_layout(cfg))     # entra nos perfis
print("1) configuracao da janela Curvas e perfis Treino/Classificacao/Corrida OK")


class IRFalso:
    is_initialized = True; is_connected = True
    def __init__(self, vv): self.v = vv
    def __getitem__(self, k): return self.v.get(k)
    def startup(self): return True
    def freeze_var_buffer_latest(self): pass
    def unfreeze_var_buffer_latest(self): pass
    def shutdown(self): pass


N = 3
drivers = [{"CarIdx": i, "UserName": f"Piloto {i}", "CarNumber": str(i), "CarClassID": 1, "CarClassShortName": "GT3",
            "CarClassColor": 0xffda59, "IRating": 2000, "LicString": "A 3.20", "LicColor": 0x0153db,
            "CarScreenName": "Porsche 911 GT3 R", "CarPath": "porsche992rgt3", "CarIsPaceCar": 0, "IsSpectator": 0,
            "UserID": 500 + i} for i in range(N)]
sdk = {"PlayerCarIdx": 0, "Speed": 40.0, "Gear": 3, "RPM": 6000.0, "Lap": 1, "LapCompleted": 0, "LapDistPct": 0.0,
       "FuelLevel": 50.0, "OnPitRoad": False, "IsOnTrack": True, "SessionNum": 0, "SessionUniqueID": 1, "SessionState": 4,
       "Throttle": 1.0, "Brake": 0.0, "Clutch": 1.0, "ThrottleRaw": 1.0, "BrakeRaw": 0.0, "ClutchRaw": 1.0,
       "BrakeABSactive": False, "SteeringWheelAngle": 0.0, "EngineWarnings": 0,
       "PlayerTrackSurface": 3, "CarIdxLapDistPct": [0.0, 0.5, 0.7], "CarIdxTrackSurface": [3] * N,
       "CarIdxOnPitRoad": [False] * N, "CarIdxClassPosition": [1, 2, 3], "CarIdxLapCompleted": [0] * N,
       "CarIdxLap": [1] * N, "CarIdxTireCompound": [0] * N, "CarIdxLastLapTime": [0.0] * N, "CarLeftRight": 1,
       "LatAccel": 0.0, "LongAccel": 0.0, "TrackTemp": 25.0, "TrackWetness": 1, "Precipitation": 0.0,
       "PitSvFlags": 0, "PitSvTireCompound": 0,
       "DriverInfo": {"Drivers": drivers, "DriverTires": [{"TireIndex": 0, "TireCompoundType": "Dry"}]},
       "WeekendInfo": {"TrackDisplayName": "Pista Simulada", "TrackLength": "5.00 km", "Official": 1, "SubSessionID": 1,
                       "Category": "Road"},
       "SessionInfo": {"Sessions": [{"SessionType": "Race"}]}}
tel = o.Telemetria(demo=False); tel.conectado = True; tel.ir = IRFalso(sdk)
relogio = [1000.0]; real_mono = o.time.monotonic; o.time.monotonic = lambda: relogio[0]


def volta_sdk(ajuste=None, hz=30, **extra):
    """Uma volta inteira passando pelo Telemetria.ler() (o caminho real do overlay)."""
    pct, dd = 0.0, None
    while pct < 1.0:
        v = tc.velocidade(pct, ajuste)
        sdk.update(extra)
        sdk["Speed"] = v / 3.6
        sdk["LapDistPct"] = pct
        sdk["CarIdxLapDistPct"] = [pct, 0.5, 0.7]
        sdk["SteeringWheelAngle"] = math.radians(120.0 if v < 150 else 4.0)
        relogio[0] += 1.0 / hz
        dd = tel.ler()
        pct += (v / 3.6) / hz / tc.COMP
    return dd


def fechar():
    sdk["LapDistPct"] = 0.01
    sdk["CarIdxLapDistPct"] = [0.01, 0.5, 0.7]
    relogio[0] += 0.03
    return tel.ler()


try:
    # ---- 2) o caminho real: ler() alimenta a janela
    dd = volta_sdk()
    assert dd["curvas"] is not None and dd["curvas"]["estado"] == "aprendendo"
    volta_sdk()
    dd = fechar()
    c = dd["curvas"]
    assert c["estado"] == "ok" and c["n"] == 5, c
    assert tel.v14_curvas.voltas_validas == 2
    print("2) Telemetria.ler(): primeira volta aprende, 5 curvas mapeadas OK")
    volta_sdk({0: 7.0, 1: -9.0})
    dd = fechar()
    c = dd["curvas"]
    assert c["volta_anterior"]["pior_n"] == 2 and c["volta_anterior"]["perda"] > 8.0, c["volta_anterior"]
    # ao vivo na proxima volta: depois da C2 aparece o cartao com o delta e o volante
    pct = 0.02
    while pct < 0.45:
        v = tc.velocidade(pct, {1: -12.0})
        sdk.update({"Speed": v / 3.6, "LapDistPct": pct, "SteeringWheelAngle": math.radians(120.0 if v < 150 else 4.0)})
        relogio[0] += 1 / 30.0
        dd = tel.ler()
        pct += (v / 3.6) / 30.0 / tc.COMP
    ult = dd["curvas"]["ultima"]
    assert ult["n"] in (2, 3) and dd["curvas"]["lista"], ult
    c2 = [r for r in dd["curvas"]["lista"] if r["n"] == 2][0]
    assert -14.0 < c2["delta"] < -8.0 and abs(abs(c2["volante"]) - 120.0) < 1.0, c2
    print("3) cartao ao vivo: C2 mais lenta aparece com DELTA negativo e o volante OK")

    # ---- 4) boxes e fora da pista invalidam; replay nao alimenta; nova sessao zera
    validas = tel.v14_curvas.voltas_validas
    volta_sdk(OnPitRoad=True)
    volta_sdk(OnPitRoad=False)
    fechar()
    assert tel.v14_curvas.voltas_validas == validas + 1, (validas, tel.v14_curvas.voltas_validas)   # so a volta limpa conta
    antes = tel.v14_curvas.voltas_validas
    volta_sdk(PlayerTrackSurface=0)
    volta_sdk(PlayerTrackSurface=3)
    fechar()
    assert tel.v14_curvas.voltas_validas == antes + 1, (antes, tel.v14_curvas.voltas_validas)   # so a volta limpa conta
    sdk["SessionUniqueID"] = 2
    relogio[0] += 1.0
    dd = tel.ler()
    assert not tel.v14_curvas.curvas and dd["curvas"]["estado"] == "aprendendo"
    print("4) boxes e fora da pista nao contam; sessao nova zera o aprendizado OK")
finally:
    o.time.monotonic = real_mono

# ---- 5) demo e janela
d = o.Telemetria(demo=True).ler()
assert d["curvas"] and d["curvas"]["estado"] == "ok" and d["curvas"]["lista"] and d["curvas"]["ultima"]
cfg["travado"] = True


def alfa_total(janela):
    img = janela.grab().toImage()
    soma = 0
    for y in range(0, img.height(), 3):
        for x in range(0, img.width(), 3):
            soma += img.pixelColor(x, y).alpha()
    return soma


j = o.JanelaCurvas(dict(cfg)); j.show()
assert j.size().width() == 360 and j.size().height() == 252
casos = {"sem dados": dict(o.Telemetria._vazio(), conectado=True, curvas=None),
         "aprendendo": dict(o.Telemetria._vazio(), conectado=True, curvas={"estado": "aprendendo", "voltas_validas": 0, "n": 0,
                                                                          "ultima": None, "lista": [], "volta_anterior": None}),
         "desconectado": dict(o.Telemetria._vazio(), conectado=False),
         "demo": d,
         "sem primeira curva": dict(d, curvas=dict(d["curvas"], ultima=None, lista=[])),
         "sem BEST": dict(d, curvas=dict(d["curvas"], lista=[{"n": 1, "min": 90.0, "best": None, "delta": None, "volante": 0.0}],
                                         ultima={"n": 1, "min": 90.0, "best": None, "delta": None, "volante": 0.0}, volta_anterior=None))}
for nome, dados in casos.items():
    j.atualizar(dados)
    j.repaint()
    assert alfa_total(j) > 0, nome
j2 = o.JanelaCurvas(dict(cfg, travado=False)); j2.show()                    # destravada: mostra o exemplo para posicionar
j2.atualizar(casos["sem dados"]); j2.repaint()
assert alfa_total(j2) > alfa_total(j) * 0.0
j.atualizar(casos["desconectado"]); j.repaint()
vazio = alfa_total(j)
j.atualizar(casos["demo"]); j.repaint()
assert alfa_total(j) > vazio * 0.9
cor = o.JanelaCurvas._cor_delta
assert cor(2.0) == o.COR_VERDE and cor(-4.0) == o.COR_VERMELHO and cor(-1.0) == o.COR_LARANJA and cor(None) == o.COR_CINZA
tx = o.JanelaCurvas._texto_volante
assert tx(118.0).startswith("E 118") and tx(-64.0).startswith("D 64") and tx(0.2) == "0°" and tx(None) == "0°"
print("5) demo, janela (6 estados, destravada, cores, volante E/D) OK")

# ---- 6) log sem erro de curvas
log = o.ARQ_LOG.read_text(encoding="utf-8") if o.ARQ_LOG.exists() else ""
assert "curvas" not in log.lower() or "erro" not in log.lower().split("curvas")[1][:80], log[-400:]
print("6) log sem erro de curvas OK")
print("\nTODOS OS TESTES DA 1.4.0 (iRacing) PASSARAM")
