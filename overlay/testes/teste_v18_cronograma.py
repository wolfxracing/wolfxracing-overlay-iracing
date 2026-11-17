# -*- coding: utf-8 -*-
"""Cronograma de corridas (build ah): cadencias, semanas, filtros, janela de horario, alerta, painel e tela de filtros. Sem o jogo."""
import os, sys, json, tempfile, datetime as dt
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["TZ"] = "America/Sao_Paulo"          # build an: os horarios seguem o fuso do computador; os testes simulam um PC em Brasilia
try:
    import time as _t; _t.tzset()
except AttributeError:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ov_cronograma as cr
falhas, _ok = [], 0
def confere(c, m):
    global _ok
    if c: _ok += 1
    else: falhas.append(m); print("FALHA", m)
U = dt.timezone.utc
def sr(nome, cad, carros, classe, pista="Spa-Francorchamps - Grand Prix", ini="2026-11-17", dur=None):
    return {"serie": nome, "carros": carros, "classe": classe, "cadencia": cad, "semanas": [{"semana": 10, "inicio": ini, "pista": pista, "duracao": dur or {"min": 20.0}, "duracao_txt": ""}]}
D = {"fonte": "t.pdf", "gerado_em": "x", "series": [
    sr("Serie 2h", {"tipo": "passo", "passo_min": 120, "minutos": [45], "paridade": 0}, ["Porsche 911 Cup (992.2)"], "D 4.0 --> Pro/WC 4.0"),
    sr("Serie 1h", {"tipo": "passo", "passo_min": 60, "minutos": [15]}, ["Mazda MX-5"], "R Rookie", pista="Monza - Grand Prix"),
    sr("Serie 30", {"tipo": "passo", "passo_min": 30, "minutos": [15]}, ["Clio"], "C 4.0 --> Pro"),
    sr("Serie Semanal", {"tipo": "semanal", "horarios": [[5, 19], [6, 14]]}, ["GT3"], "B 4.0 --> Pro"),
    sr("Serie Sem Horario", {"tipo": "desconhecida", "texto": "5 Timeslots Per Week"}, ["X"], "A 4.0 --> Pro")]}
ini = dt.datetime(2026, 11, 17, tzinfo=U)
# cadencias
h2 = cr.horarios_da_semana(D["series"][0]["cadencia"], ini); confere(len(h2) == 12 * 7 and all(t.hour % 2 == 0 and t.minute == 45 for t in h2), "2h: 12 por dia, horas pares aos :45")
h1 = cr.horarios_da_semana(D["series"][1]["cadencia"], ini); confere(len(h1) == 24 * 7 and all(t.minute == 15 for t in h1), "1h: 24 por dia")
h3 = cr.horarios_da_semana(D["series"][2]["cadencia"], ini); confere(len(h3) == 48 * 7 and {t.minute for t in h3} == {15, 45}, "30 min: :15 e :45")
hs = cr.horarios_da_semana(D["series"][3]["cadencia"], ini); confere(len(hs) == 2 and hs[0].weekday() == 5 and hs[0].hour == 19 and hs[1].weekday() == 6, f"semanal: sab 19h e dom 14h ({hs})")
confere(cr.horarios_da_semana(D["series"][4]["cadencia"], ini) == [] and cr.sem_horario(D) == ["Serie Sem Horario"], "serie sem horario nao gera corrida e e listada")
confere(cr.horarios_da_semana(None, ini) == [] and cr.horarios_da_semana({"tipo": "x"}, ini) == [], "cadencia invalida nao quebra")
# filtros
agora = dt.datetime(2026, 11, 17, 12, 0, tzinfo=U)           # 09:00 Brasilia
def nomes(f, **k): return [i["nome"] for i in cr.proximas(D, f, agora, 9999, **k)]
confere(cr.proximas(D, {}, agora) == [] and cr.proximas(D, None, agora) == [] and cr.proximas(None, {"series": ["x"]}, agora) == [], "sem filtro / sem dados = vazio (nunca avisa tudo)")
confere(set(nomes({"series": ["Serie 2h"]})) == {"Serie 2h"}, "filtro por serie")
confere(set(nomes({"pistas": ["MONZA"]})) == {"Serie 1h"} and set(nomes({"pistas": ["monza", "spa"]}, horizonte_h=240)) == {"Serie 1h", "Serie 2h", "Serie 30", "Serie Semanal"}, "filtro por pista (sem acento/maiuscula, OU)")
confere(set(nomes({"carros": ["porsche"]})) == {"Serie 2h"} and set(nomes({"carros": ["mx-5"]})) == {"Serie 1h"}, "filtro por carro")
confere(set(nomes({"classes": ["D"]})) == {"Serie 2h"} and set(nomes({"classes": ["R", "C"]})) == {"Serie 1h", "Serie 30"}, "filtro por classe de licenca")
confere(cr.letra_classe(D["series"][0]) == "D" and cr.letra_classe({"classe": ""}) == "", "letra da classe (cabecalho)")
confere(cr.letra_classe({"classe": "D 4.0 --> Pro", "classe_serie": "C"}) == "C" and cr.letra_classe({"classe": "D 4.0", "classe_serie": "?"}) == "D", "classe da serie (secao do PDF) tem prioridade")
confere(set(nomes({"classes": ["D"], "pistas": ["monza"]})) == set(), "filtros se somam (E)")
# janela de horario (local = UTC-3)
r = cr.proximas(D, {"series": ["Serie 2h"], "janela": True, "ini": "20:00", "fim": "22:00"}, agora, 50, horizonte_h=30)
confere(r and all(20 * 60 <= i["inicio"].hour * 60 + i["inicio"].minute <= 22 * 60 for i in r), f"janela 20-22h local ({[str(i['inicio']) for i in r]})")
r = cr.proximas(D, {"series": ["Serie 2h"], "janela": True, "ini": "22:00", "fim": "02:00"}, agora, 50, horizonte_h=30)
confere(r and all((i["inicio"].hour * 60 + i["inicio"].minute >= 1320) or (i["inicio"].hour * 60 + i["inicio"].minute <= 120) for i in r), "janela que vira a meia-noite")
r = cr.proximas(D, {"series": ["Serie 2h"], "fuso_h": 0, "fuso_auto": False}, agora, 1)
confere(r[0]["inicio"].hour == 12 and r[0]["inicio"].minute == 45, "fuso 0 mantem UTC")
# alerta e andamento
a = dt.datetime(2026, 11, 17, 12, 20, tzinfo=U)               # 25 min antes de 12:45
r = cr.proximas(D, {"series": ["Serie 2h"], "antecedencia_min": 30}, a, 2); confere(r[0]["alerta"] and not r[0]["em_andamento"] and abs(r[0]["ate_inicio_s"] - 1500) < 1, "alerta com 25 min")
r = cr.proximas(D, {"series": ["Serie 2h"], "antecedencia_min": 10}, a, 2); confere(not r[0]["alerta"], "sem alerta fora da antecedencia")
a = dt.datetime(2026, 11, 17, 12, 55, tzinfo=U)
r = cr.proximas(D, {"series": ["Serie 2h"]}, a, 2); confere(r[0]["em_andamento"] and r[0]["ate_inicio_s"] < 0, "corrida de 20 min iniciada ha 10 min = em andamento")
a = dt.datetime(2026, 11, 17, 13, 30, tzinfo=U)
r = cr.proximas(D, {"series": ["Serie 2h"]}, a, 2); confere(not r[0]["em_andamento"] and (r[0]["inicio"].hour, r[0]["inicio"].minute) == (11, 45), "corrida encerrada nao aparece")  # proxima 14:45 UTC = 11:45 local
# virada de semana: so existe a semana 10 (17/11..24/11); depois dela nao ha corridas
fim = dt.datetime(2026, 11, 24, 3, 0, tzinfo=U)
confere(cr.proximas(D, {"series": ["Serie 2h"]}, fim, 5) == [], "sem semana publicada = sem corrida (nao inventa)")
# filtros_validos robusto
v = cr.filtros_validos({"series": "x", "classes": ["Z", "D"], "antecedencia_min": "abc", "fuso_h": 99, "pistas": [None, " "]})
confere(v["series"] == [] and v["classes"] == ["D"] and v["antecedencia_min"] == 30 and v["fuso_h"] == 14.0 and v["pistas"] == ["None"] or v["pistas"] == [], f"filtros invalidos saneados ({v})")
confere(cr.carregar("/nao/existe.json")[0] is None and "nao encontrado" in cr.carregar("/nao/existe.json")[1], "arquivo ausente: aviso")
S = tempfile.mkdtemp(); bad = os.path.join(S, "b.json"); open(bad, "w").write("{nao json"); confere(cr.carregar(bad)[0] is None, "json corrompido: aviso sem erro")
# ---- dados reais (cronograma.json do PDF 2026 S4)
# SEM_DADO: o cronograma.json (dado do usuario, importado do PDF) nao e distribuido; sem ele este teste nao se aplica
if not os.path.isfile(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma.json")):
    print("teste_v18_cronograma: sem cronograma.json (importe o PDF Season Schedule); teste ignorado"); sys.exit(0)
real, av = cr.carregar(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma.json"))
confere(real is not None and len(real["series"]) >= 150, "cronograma.json real carregado")
sc = next(s for s in real["series"] if s["serie"].startswith("Stock Car Brasil"))
confere(all(x.get("classe_serie") in cr.CLASSES for x in real["series"]), "toda serie real tem classe da serie (R/D/C/B/A)")
gs = next(x for x in real["series"] if x["serie"].startswith("GT Sprint")); confere(cr.letra_classe(gs) == "B" and gs["classe"].startswith("C"), "GT Sprint: classe B (secao) com licenca exigida C")
confere(sc["cadencia"]["passo_min"] == 120 and sc["cadencia"]["minutos"] == [45] and any("Lime Rock" in w["pista"] for w in sc["semanas"]), "Stock Car Brasil: a cada 2h aos :45, com Lime Rock")
confere(len(cr.sem_horario(real)) < 30 and not any("Class Series" in s["serie"] for s in real["series"]), "titulos corretos; poucas series sem horario")
ag = dt.datetime(2026, 11, 16, 23, 0, tzinfo=U)
r = cr.proximas(real, {"series": [sc["serie"]], "antecedencia_min": 30}, ag, 3); confere(len(r) == 3 and r[0]["pista"], "Stock Car Brasil proximas corridas no dado real")
r = cr.proximas(real, {"classes": ["B", "A"], "carros": ["gt3"], "janela": True, "ini": "19:00", "fim": "23:59"}, ag, 8, horizonte_h=120)
r = cr.proximas(real, {"classes": ["B"], "carros": ["gt3"]}, ag, 400, horizonte_h=120)
confere(len(r) > 0 and all(i["classe"] == "B" and "gt3" in cr._norm(i["carro"]) for i in r), f"consulta combinada (classe B + carro GT3) no dado real ({len(r)} corridas)")
r = cr.proximas(real, {"classes": ["B", "A"], "carros": ["gt3"], "janela": True, "ini": "19:00", "fim": "23:59"}, ag, 400, horizonte_h=120)
confere(len(r) > 0 and all(i["classe"] in ("A", "B") and 19 * 60 <= i["inicio"].hour * 60 + i["inicio"].minute <= 1439 for i in r), "classe + carro + janela no dado real (o texto do item mostra so os 2 primeiros carros)")
# ---- auditoria build aj: GMT, paridade, minutos semanais
import importar_cronograma as imp
for txt, esperado in (("Races every 2 hours at :45", (120, 45)), ("Races every 2 hours at :45 GMT", (120, 45)), ("Races every hour at :15 GMT", (60, 15)),
                      ("Races every hour at :15", (60, 15)), ("Races hourly at :30 UTC", (60, 30)), ("Races every 2 hours at :15 past GMT", (120, 15)),
                      ("Races every 30 minutes at :15 & :45 GMT", (30, 15)), ("Races every hour on the hour GMT", (60, 0))):
    c = imp.interpretar(txt)
    confere(c["tipo"] == "passo" and (c["passo_min"], c["minutos"][0]) == esperado, f"cadencia com/sem GMT: {txt!r} -> {c}")
c = imp.interpretar("Races on Saturday at 19:30 GMT"); confere(c["tipo"] == "semanal" and [tuple(x) for x in c["horarios"]] == [(5, 19, 30)], f"semanal preserva minutos ({c})")
c = imp.interpretar("Races on Saturday at 7 & 17:00 GMT & Sunday at 0 & 13 GMT")
confere([tuple(x) for x in c["horarios"]] == [(5, 7, 0), (5, 17, 0), (6, 0, 0), (6, 13, 0)], f"semanal misto ({c['horarios']})")
confere(imp.interpretar("Races every other Saturday at 4 & 15 GMT")["tipo"] == "desconhecida", "'every other' continua para revisao")
hh = cr.horarios_da_semana({"tipo": "semanal", "horarios": [[5, 19, 30], [6, 14]]}, ini)
confere([(t.weekday(), t.hour, t.minute) for t in hh] == [(5, 19, 30), (6, 14, 0)], f"agendador semanal com minutos e formato antigo ({hh})")
h120 = cr.horarios_da_semana({"tipo": "passo", "passo_min": 120, "minutos": [45]}, ini)
confere(len(h120) == 84 and all(t.hour % 2 == 0 for t in h120), f"120 min sem paridade: 84/semana em horas pares ({len(h120)})")
h120i = cr.horarios_da_semana({"tipo": "passo", "passo_min": 120, "minutos": [45], "paridade": 1}, ini)
confere(len(h120i) == 84 and all(t.hour % 2 == 1 for t in h120i), "120 min com paridade impar")
confere(cr.horarios_da_semana({"tipo": "semanal", "horarios": [["x"], None, [5]]}, ini) == [], "horarios semanais invalidos sao ignorados")
# ---- parser: tabela que atravessa a quebra de pagina (bug achado na revisao: semanas depois da quebra eram descartadas)
txt = "\n".join(["Current iRacing Race Schedule", "", "  B Class Series (SPORTS CAR) . . . . . . . . . . . . . . . . . . . . 5",
    "     Mini Serie - 2026 Season 4 . . . . . . . . . . . . . . . . . . . . . . . . 5", "", "", "Mini Serie - 2026 Season 4", "Mazda MX-5 Cup", "Class C 4.0 --> Pro/WC 4.0",
    "Races every hour at :15 GMT", "Min entries for official: 6 | Split at: 28 | Drops: 4",
    "Week 1 (2026-11-17)   Spa-Francorchamps - Grand Prix           Rain possible, Rolling start, Local  20 mins",
    "                      (2026-11-21 10:00 1x)                    enforced cautions, Qual scrutiny -", "                                               Strict.", "", "", "",
    "                                                         12", "",
    "Week 2 (2026-11-24)   Monza - Grand Prix                       Rain possible, Rolling start, Local  31 laps",
    "                      (2026-11-28 10:00 1x)                    enforced cautions.", "",
    "Week 3 (2026-12-01)   Imola                                    All dry events, Rolling start        45 mins", "",
    "Some Other Series - 2026 Season 4"])
ser = imp.processar(txt)
confere(len(ser) == 1 and [w["semana"] for w in ser[0]["semanas"]] == [1, 2, 3], f"parser: semanas apos a quebra de pagina ({[w['semana'] for w in ser[0]['semanas']] if ser else ser})")
confere(ser[0]["classe_serie"] == "B" and ser[0]["cadencia"]["passo_min"] == 60 and ser[0]["cadencia"]["minutos"] == [15], f"parser: classe da serie B e cadencia com GMT ({ser[0]['classe_serie']}, {ser[0]['cadencia']})")
confere(ser[0]["semanas"][1]["duracao"] == {"voltas": 31} and ser[0]["semanas"][2]["pista"] == "Imola" and ser[0]["semanas"][0]["pista"].startswith("Spa"), "parser: pista e duracao por semana")
confere(len(cr.proximas({"series": ser}, {"series": ["Mini Serie - 2026 Season 4"]}, dt.datetime(2026, 11, 24, 0, 0, tzinfo=U), 9999, horizonte_h=24)) == 24, "parser + agenda: 24 corridas em 24 h (1 por hora)")
# ---- painel Calendario com alerta + tela de filtros
import overlay_iracing as o
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore import QTimer
app = QApplication.instance() or QApplication([])
o.ARQ_CONFIG = o.Path(S) / "c.json"; o.ARQ_LOG = o.Path(S) / "l.txt"
cfg = o.carregar_config()
confere(cfg.get("cronograma_ativo") is False and cfg.get("cronograma_filtros") == {}, "config padrao do cronograma")
import ov_v18
sv = ov_v18.Servico(o.Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
cfg["cronograma_ativo"] = True
cfg["cronograma_filtros"] = {"series": [sc["serie"]], "antecedencia_min": 600}
r = sv.montar({}, {}, cfg, 100.0)
confere(r["calendario_fonte"] == "cronograma iRacing" and r["calendario"] and r["calendario_alerta"] is not None, "Servico monta o calendario pelo cronograma e sinaliza alerta")
cfg["cronograma_filtros"] = {}
sv._cron_t = -1e9; r = sv.montar({}, {}, cfg, 200.0)
confere(r["calendario"] == [] and "filtros" in r["calendario_aviso"].lower(), "sem filtros: orienta o piloto")
cfg["cronograma_ativo"] = False; sv._cron_t = -1e9; r = sv.montar({}, {}, cfg, 300.0)
confere(r["calendario_alerta"] is None and r["calendario_fonte"] != "cronograma iRacing", "desligado: volta ao CSV")
import ov_cronograma_ui as ui
def aceitar():
    for w in QApplication.topLevelWidgets():
        if isinstance(w, QDialog) and w.isVisible():
            lst = w.findChildren(__import__("PySide6.QtWidgets", fromlist=["QListWidget"]).QListWidget)[0]
            for i in range(lst.count()):
                if lst.item(i).text() == sc["serie"]:
                    from PySide6.QtCore import Qt
                    lst.item(i).setCheckState(Qt.Checked)
            w.accept()
QTimer.singleShot(300, aceitar)
salvos = []
okk = ui.abrir_dialogo(cfg, real, lambda c: salvos.append(1), lambda: salvos.append(2))
confere(okk and cfg["cronograma_ativo"] and cfg["cronograma_filtros"]["series"] == [sc["serie"]] and cfg["mostrar_calendario"] and salvos == [1, 2], f"tela de filtros salva e liga o aviso ({cfg.get('cronograma_filtros')})")
# painel desenha com alerta
import ov_v18_janelas as vj
cls_ = vj.construir(o)
J = cls_["calendario"](cfg); 
agora = dt.datetime.now(); 
itens = [{"nome": "Stock Car Brasil - 2026 Season 4", "classe": "D", "inicio": agora + dt.timedelta(minutes=12), "dur": 20.0, "ate_inicio_s": 720.0, "reg_s": None, "em_andamento": False,
          "pista": "Virginia International Raceway - Full Course", "carro": "x", "alerta": True},
         {"nome": "GT3 Challenge", "classe": "B", "inicio": agora + dt.timedelta(minutes=135), "dur": 40.0, "ate_inicio_s": 8100.0, "reg_s": None, "em_andamento": False, "pista": "Spa", "carro": "y", "alerta": False}]
J.dados = dict(J.dados); J.dados.update({"conectado": True, "v18": {"calendario": itens, "calendario_alerta": itens[0], "calendario_fonte": "cronograma iRacing"}})
img = J.grab().toImage(); confere(not img.isNull(), "painel Calendario desenha com alerta")
img.save(os.path.join(S, "cal.png")); print("png", os.path.join(S, "cal.png"))
print("ok" if not falhas else "FALHAS", _ok); sys.exit(1 if falhas else 0)
