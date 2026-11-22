# -*- coding: utf-8 -*-
"""Build al: importar novo cronograma (PDF/TXT), filtros ao vivo na tela, previa da Central com o cronograma real. Sem o jogo."""
import os, sys, json, shutil, tempfile, time, datetime as dt
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import time as _t
# build az: sem time.tzset() (Windows) usa o fuso fixo POSIX "BRT3" (UTC-3), igual a Brasilia desde 2019.
os.environ["TZ"] = "America/Sao_Paulo" if hasattr(_t, "tzset") else "BRT3"
if hasattr(_t, "tzset"):
    _t.tzset()
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import ov_cronograma as cr
falhas, _ok = [], 0
def confere(c, m):
    global _ok
    if c: _ok += 1
    else: falhas.append(m); print("FALHA", m)
U = dt.timezone.utc
S = tempfile.mkdtemp()
TEM_IMPORTADOR = os.path.exists(os.path.join(RAIZ, "importar_cronograma.py"))
if TEM_IMPORTADOR:
    import importar_cronograma as imp

def texto_serie(nome, carros, cadencia, semanas, indice=True, classe="B"):
    L = ["Current iRacing Race Schedule", "", f"  {classe} Class Series (SPORTS CAR) . . . . . . . . . . . . . . . . . . . . 5",
         f"     {nome} . . . . . . . . . . . . . . . . . . . . . . . . 5", "", "", nome, carros, "Class C 4.0 --> Pro/WC 4.0", cadencia,
         "Min entries for official: 6 | Split at: 28 | Drops: 4"]
    for i, (ini, pista, dur) in enumerate(semanas, 1):
        L.append(f"Week {i} ({ini})   {pista:<40} Rain possible, Rolling start, Local  {dur}")
        L.append("")
    return L

def hoje_terca():
    n = dt.datetime.now(U).replace(hour=0, minute=0, second=0, microsecond=0)
    return (n - dt.timedelta(days=(n.weekday() - 1) % 7)).strftime("%Y-%m-%d")

T0 = hoje_terca()
TXT_A = "\n".join(texto_serie("Serie Alfa - 2026 Season 4", "Mazda MX-5 Cup", "Races every hour at :15 GMT", [(T0, "Spa-Francorchamps - Grand Prix", "20 mins")]) + [""] +
                  texto_serie("Serie Beta - 2026 Season 4", "Porsche 911 GT3 Cup", "Races every hour at :45 GMT", [(T0, "Monza - Grand Prix", "30 mins")]) + ["Fim"])
TXT_B = "\n".join(texto_serie("Serie Alfa - 2026 Season 4", "Mazda MX-5 Cup", "Races every hour at :15 GMT", [(T0, "Imola", "20 mins")]) + ["Fim"])   # so a Alfa (a Beta sumiu)

# ---------------------------------------------------------------- importacao (logica)
if TEM_IMPORTADOR:
    pasta = os.path.join(S, "p1"); os.makedirs(pasta)
    a = os.path.join(S, "a.txt"); open(a, "w", encoding="utf-8").write(TXT_A)
    r = cr.importar_arquivo(a, pasta)
    confere(r["ok"] and not r["precisa_pypdf"] and r["dados"] and len(r["dados"]["series"]) == 2, f"importa .txt: 2 series ({r['msg']})")
    confere(os.path.isfile(os.path.join(pasta, "cronograma.json")) and not os.path.exists(os.path.join(pasta, "cronograma_anterior.json")), "primeira importacao: grava cronograma.json, sem backup")
    confere("2 séries" in r["msg"] and "semanas" in r["msg"], "mensagem resume o que entrou")
    b = os.path.join(S, "b.txt"); open(b, "w", encoding="utf-8").write(TXT_B)
    r2 = cr.importar_arquivo(b, pasta)
    ant = json.load(open(os.path.join(pasta, "cronograma_anterior.json"), encoding="utf-8")); novo = json.load(open(os.path.join(pasta, "cronograma.json"), encoding="utf-8"))
    confere(r2["ok"] and len(ant["series"]) == 2 and len(novo["series"]) == 1 and "cronograma_anterior.json" in r2["msg"], "segunda importacao troca o arquivo e guarda o anterior")
    confere(not os.path.exists(os.path.join(pasta, "cronograma.json.novo")), "nao deixa arquivo temporario")
    # entradas invalidas nunca derrubam nem trocam o cronograma bom
    antes = open(os.path.join(pasta, "cronograma.json"), "rb").read()
    lixo = os.path.join(S, "lixo.txt"); open(lixo, "w").write("nada a ver")
    vazio = os.path.join(S, "vazio.txt"); open(vazio, "w").write("Week 1 (2026-11-17) \n")
    for nome, caminho in (("inexistente", os.path.join(S, "nao_existe.pdf")), ("extensao errada", os.path.join(S, "x.docx")), ("texto sem cronograma", lixo), ("sem series", vazio)):
        if nome == "extensao errada": open(caminho, "w").write("x")
        rr = cr.importar_arquivo(caminho, pasta)
        confere(not rr["ok"] and rr["msg"] and not rr["precisa_pypdf"], f"entrada invalida ({nome}): recusa com mensagem ({rr['msg'][:60]})")
    confere(open(os.path.join(pasta, "cronograma.json"), "rb").read() == antes, "cronograma bom permanece apos as recusas")
    # pasta sem permissao/inexistente
    rr = cr.importar_arquivo(a, os.path.join(S, "nao", "existe"))
    confere(not rr["ok"] and "mantido" in rr["msg"], f"pasta de destino invalida: recusa sem quebrar ({rr['msg'][:70]})")
    # sem leitor de PDF
    pdf_falso = os.path.join(S, "falso.pdf"); open(pdf_falso, "wb").write(b"%PDF-1.4 falso")
    orig = imp.texto_do_pdf
    def sem_pypdf(_c): raise ImportError("pypdf")
    imp.texto_do_pdf = sem_pypdf
    rr = cr.importar_arquivo(pdf_falso, pasta); confere(not rr["ok"] and rr["precisa_pypdf"], "PDF sem leitor: pede o pypdf")
    imp.texto_do_pdf = lambda _c: (_ for _ in ()).throw(RuntimeError("pdf corrompido"))
    rr = cr.importar_arquivo(pdf_falso, pasta); confere(not rr["ok"] and not rr["precisa_pypdf"] and "corrompido" in rr["msg"], "PDF corrompido: mensagem clara")
    imp.texto_do_pdf = orig
    # cronograma ja encerrado
    rr = cr.importar_arquivo(a, os.path.join(S, "p1"), agora_utc=dt.datetime(2040, 1, 1, tzinfo=U)); confere(rr["ok"] and "já terminou" in rr["msg"], "avisa quando o cronograma importado ja terminou")
    # PDF de verdade (se houver reportlab e leitor)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        pdf = os.path.join(S, "SeasonSchedule.pdf"); c = canvas.Canvas(pdf, pagesize=A4); c.setFont("Courier", 7); y = 820
        for ln in TXT_A.splitlines():
            c.drawString(20, y, ln); y -= 9
            if y < 30: c.showPage(); c.setFont("Courier", 7); y = 820
        c.save()
        if cr.leitor_pdf_disponivel():
            p2 = os.path.join(S, "p2"); os.makedirs(p2)
            rr = cr.importar_arquivo(pdf, p2)
            confere(rr["ok"] and len(rr["dados"]["series"]) == 2, f"importa PDF de verdade ({rr['msg'][:80]})")
    except ImportError:
        print("reportlab ausente: teste de PDF real pulado")
    # instalar_pypdf no .exe empacotado
    sys.frozen = True; ok, m = cr.instalar_pypdf(); del sys.frozen
    confere(not ok and "empacotada" in m, "instalar pypdf: recusa no .exe empacotado")
    # fluxo com perguntas (sem janelas)
    import ov_cronograma_ui as ui
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    imp.texto_do_pdf = sem_pypdf
    perguntas = []
    res = ui.importar_com_dialogo(pasta, escolher_arquivo=lambda: pdf_falso, confirmar=lambda t: perguntas.append(t) or False)
    confere(perguntas and not res["ok"] and "cancelada" in res["msg"], "sem pypdf e piloto recusa instalar: mensagem de alternativa")
    orig_inst = cr.instalar_pypdf; cr.instalar_pypdf = lambda: (False, "sem internet")
    res = ui.importar_com_dialogo(pasta, escolher_arquivo=lambda: pdf_falso, confirmar=lambda t: True)
    confere(not res["ok"] and "sem internet" in res["msg"], "instalacao falhou: mostra o motivo")
    chamadas = []
    def inst_ok():
        chamadas.append(1); imp.texto_do_pdf = orig; return True, ""
    cr.instalar_pypdf = inst_ok
    shutil.copy(a, os.path.join(S, "falso2.pdf"))                  # texto valido com extensao .pdf: o leitor 'instalado' (orig) tenta ler como PDF
    imp.texto_do_pdf = sem_pypdf
    res = ui.importar_com_dialogo(pasta, escolher_arquivo=lambda: a, confirmar=lambda t: True)
    confere(res["ok"], "txt nao precisa de leitor")
    cr.instalar_pypdf = orig_inst; imp.texto_do_pdf = orig
    confere(ui.importar_com_dialogo(pasta, escolher_arquivo=lambda: "") is None, "cancelar a escolha do arquivo nao faz nada")

# ---------------------------------------------------------------- funcoes puras novas
D = {"fonte": "t", "gerado_em": "x", "series": [
    {"serie": "S1", "carros": ["Mazda MX-5"], "classe": "R", "classe_serie": "R", "cadencia": {"tipo": "passo", "passo_min": 60, "minutos": [15]},
     "semanas": [{"semana": 1, "inicio": T0, "pista": "Spa", "duracao": {"min": 20.0}, "duracao_txt": ""}]},
    {"serie": "S2", "carros": ["Porsche"], "classe": "C", "classe_serie": "C", "cadencia": {"tipo": "passo", "passo_min": 60, "minutos": [45]},
     "semanas": [{"semana": 1, "inicio": T0, "pista": "Monza", "duracao": {"voltas": 10}, "duracao_txt": ""}]}]}
agora = dt.datetime.now(U)
it, av, al = cr.calendario_do_cronograma(D, "", {"series": ["S1"]}, agora)
confere(it and av == "" and all(i["nome"] == "S1" for i in it), "calendario_do_cronograma: itens do filtro")
it, av, al = cr.calendario_do_cronograma(D, "", {}, agora); confere(it == [] and "filtros" in av.lower() and al is None, "sem filtro: aviso orienta")
it, av, al = cr.calendario_do_cronograma(None, "falta o arquivo", {"series": ["S1"]}, agora); confere(it == [] and av == "falta o arquivo", "sem cronograma: repassa o aviso")
confere(cr.contagem_txt(-5) == "em andamento" and cr.contagem_txt(65 * 60) == "em 1 h 05 min" and cr.contagem_txt(90 * 3600) == "em 3 d 18 h" and cr.contagem_txt(300) == "em 5 min", "contagem regressiva em texto")
lp = cr.linha_previa({"nome": "S1", "pista": "Spa", "duracao": "20 min", "inicio": dt.datetime(2026, 11, 17, 12, 45), "ate_inicio_s": 3900})
confere(lp.startswith("ter 17/11 12:45") and "S1 | Spa | 20 min" in lp and lp.endswith("(em 1 h 05 min)"), f"linha da previa ({lp})")
d1 = cr.dica_vazio(D, {"series": ["S1"], "pistas": ["zzz"]}, agora); confere("Pista" in d1 and "sem ele haveria" in d1, f"dica: o filtro que mais restringe ({d1})")
confere(cr.dica_vazio(D, {"pistas": ["zzz"]}, agora) == "", "dica vazia quando nenhum filtro ajuda")
# desempenho com o cronograma real (162 series)
real, _ = cr.carregar(os.path.join(RAIZ, "cronograma.json"))
if real:
    t = time.perf_counter(); cr.proximas(real, {"classes": ["C"]}, agora, 500); d_cls = time.perf_counter() - t
    t = time.perf_counter(); cr.proximas(real, {"series": [real["series"][0]["serie"]]}, agora, 500); d_ser = time.perf_counter() - t
    confere(d_cls < 1.5 and d_ser < 0.3, f"filtros rapidos o bastante para atualizar ao vivo (classe {d_cls*1000:.0f} ms, serie {d_ser*1000:.0f} ms)")
    nm = real["series"][0]["serie"]
    confere(cr.proximas(real, {"series": [nm]}, agora, 500) == cr.proximas(real, {"series": [nm]}, agora, 500), "resultado deterministico")


# ---------------------------------------------------------------- fuso horario do Windows (build an)
import time as _tm
if hasattr(_tm, "tzset"):
    def local_de(tz, filtros, quando):
        os.environ["TZ"] = tz; _tm.tzset()
        return cr.proximas(D, dict({"series": ["S2"]}, **filtros), quando, 1)[0]["inicio"], cr.fuso_txt(cr.filtros_validos(filtros), quando)
    q = dt.datetime(2026, 11, 17, 12, 0, tzinfo=U)
    ini_sp, txt_sp = local_de("America/Sao_Paulo", {}, q); confere(ini_sp.hour == 8 and ini_sp.minute == 45 and txt_sp == "UTC-03:00", f"fuso do Windows = Brasilia (-3): 11:45 UTC vira 08:45 ({ini_sp}, {txt_sp})")
    ini_t, txt_t = local_de("Asia/Tokyo", {}, q); confere(ini_t.hour == 20 and txt_t == "UTC+09:00", f"fuso do Windows = Toquio (+9) ({ini_t}, {txt_t})")
    os.environ["TZ"] = "Europe/London"; _tm.tzset()
    txt_i = cr.fuso_txt(cr.filtros_validos({}), dt.datetime(2026, 7, 14, 12, 0, tzinfo=U)); txt_i2 = cr.fuso_txt(cr.filtros_validos({}), dt.datetime(2026, 12, 15, 12, 0, tzinfo=U))
    confere(txt_i == "UTC+01:00" and txt_i2 == "UTC+00:00", f"horario de verao acompanha o Windows (Londres: julho {txt_i}, dezembro {txt_i2})")
    ini_m, txt_m = local_de("Asia/Tokyo", {"fuso_auto": False, "fuso_h": -3}, q); confere(ini_m.hour == 8 and txt_m == "UTC-03:00", "fuso fixo manual ignora o Windows")
    confere(cr.filtros_validos({})["fuso_auto"] is True and cr.filtros_validos({"fuso_h": -3})["fuso_auto"] is True, "padrao e usar o fuso do Windows (config antiga tambem)")
    os.environ["TZ"] = "America/Sao_Paulo"; _tm.tzset()
    # janela de horario usa o fuso do Windows
    os.environ["TZ"] = "Asia/Tokyo"; _tm.tzset()
    r = cr.proximas(D, {"series": ["S2"], "janela": True, "ini": "20:00", "fim": "23:00"}, q, 30, horizonte_h=48)
    confere(r and all(20 <= i["inicio"].hour <= 23 for i in r), "janela de horario no fuso do Windows (Toquio)")
    os.environ["TZ"] = "America/Sao_Paulo"; _tm.tzset()
else:
    print("PULADO (build az): verificacoes de fuso/horario de verao dependem de time.tzset(), indisponivel neste Windows; cobertas no Linux/macOS")

# ---------------------------------------------------------------- previa da Central com o cronograma real
import overlay_iracing as o
import ov_v18
from PySide6.QtWidgets import QApplication, QDialog, QListWidget, QPushButton, QLabel, QCheckBox
from PySide6.QtCore import QTimer, Qt
app = QApplication.instance() or QApplication([])
o.ARQ_CONFIG = o.Path(S) / "c.json"; o.ARQ_LOG = o.Path(S) / "l.txt"
cfg = o.carregar_config()
pdem = os.path.join(S, "demo"); os.makedirs(pdem); json.dump(D, open(os.path.join(pdem, "cronograma.json"), "w", encoding="utf-8"))
ov_v18.definir_fonte_cronograma(cfg, pdem)
ex = ov_v18.exemplo(0.0)
confere(ex.get("calendario_fonte") != "cronograma iRacing", "desligado: a previa continua com os exemplos")
cfg["cronograma_ativo"] = True; cfg["cronograma_filtros"] = {"series": ["S1"]}
ex = ov_v18.exemplo(0.0)
confere(ex["calendario_fonte"] == "cronograma iRacing" and ex["calendario"] and all(i["nome"] == "S1" for i in ex["calendario"]), "previa mostra o cronograma real com o filtro de serie")
cfg["cronograma_filtros"] = {"series": ["S2"]}
ex = ov_v18.exemplo(0.0); confere(ex["calendario"] and all(i["nome"] == "S2" for i in ex["calendario"]), "trocar o filtro muda a previa NA HORA")
cfg["cronograma_filtros"] = {"pistas": ["zzz"]}
ex = ov_v18.exemplo(0.0); confere(ex["calendario"] == [] and ex["calendario_aviso"], "filtro sem resultado: previa mostra o aviso, nao corridas de exemplo")
cfg["cronograma_filtros"] = {"series": ["S1"], "antecedencia_min": 240}
ex = ov_v18.exemplo(0.0); confere(ex["calendario_alerta"] is not None, "previa tambem mostra o alerta")
tel = o.Telemetria(demo=True); dd = tel._demo()
confere(dd["v18"]["calendario_fonte"] == "cronograma iRacing", "dados de demo da Telemetria (previa/Central) usam o cronograma")
os.remove(os.path.join(pdem, "cronograma.json")); time.sleep(0.01); ov_v18._FONTE_CRON["t"] = -1e9
ex = ov_v18.exemplo(0.0); confere(ex["calendario"] == [] and ex["calendario_aviso"], "sem cronograma.json: previa avisa")
ov_v18.definir_fonte_cronograma(None, None); cfg["cronograma_ativo"] = False

# ---------------------------------------------------------------- tela ao vivo
import ov_cronograma_ui as ui
if TEM_IMPORTADOR:
    DLG = lambda: next((w for w in QApplication.topLevelWidgets() if isinstance(w, QDialog) and w.isVisible()), None)
    def achar(w, tipo, pred=lambda x: True): return [x for x in w.findChildren(tipo) if pred(x)]
    pastaui = os.path.join(S, "ui"); os.makedirs(pastaui)
    r0 = cr.importar_arquivo(a, pastaui); dados_ui = r0["dados"]
    cfg2 = {"cronograma_filtros": {"series": ["Serie Beta - 2026 Season 4"]}, "cronograma_ativo": False, "mostrar_calendario": False}
    obs = {}
    def passo1():
        w = DLG(); lst = achar(w, QListWidget)[0]; prev = achar(w, QListWidget)[1]
        obs["inicial"] = (lst.count(), prev.count(), [lst.item(i).text() for i in range(lst.count()) if lst.item(i).checkState() == Qt.Checked])
        obs["ativo_aberto"] = cfg2.get("cronograma_ativo")
        # marca a Alfa: o config em memoria e a previa mudam na hora
        for i in range(lst.count()):
            if lst.item(i).text().startswith("Serie Alfa"): lst.item(i).setCheckState(Qt.Checked)
        obs["apos_marcar"] = (list(cfg2["cronograma_filtros"]["series"]), cfg2["cronograma_ativo"], prev.count(), {prev.item(i).text().split("   ")[1].split(" | ")[0] for i in range(prev.count())})
        # pista que nao existe -> previa vazia + dica
        campos = achar(w, __import__("PySide6.QtWidgets", fromlist=["QLineEdit"]).QLineEdit)
        pista = next(c for c in campos if "spa, monza" in (c.placeholderText() or ""))
        pista.setText("zzz")
        rot = [l.text() for l in achar(w, QLabel)]
        obs["vazio"] = (prev.count(), [t for t in rot if "Nenhuma corrida" in t], list(cfg2["cronograma_filtros"]["pistas"]))
        pista.setText("")
        cb = next(c for c in achar(w, QCheckBox) if c.text() == "C"); cb.setChecked(True)
        obs["classe_live"] = list(cfg2["cronograma_filtros"]["classes"])
        w.reject()
    QTimer.singleShot(300, passo1)
    ret = ui.abrir_dialogo(cfg2, dados_ui, lambda c: obs.setdefault("salvou", 1), lambda: None, pasta=pastaui)
    confere(obs["inicial"][0] == 2 and obs["inicial"][1] > 0 and obs["inicial"][2] == ["Serie Beta - 2026 Season 4"], f"tela abre com a previa ja preenchida ({obs['inicial']})")
    confere(obs["ativo_aberto"] is False and obs["apos_marcar"][1] is True, "ao editar, o aviso passa a valer ao vivo (config em memoria)")
    confere(set(obs["apos_marcar"][0]) == {"Serie Alfa - 2026 Season 4", "Serie Beta - 2026 Season 4"} and obs["apos_marcar"][2] > 0 and len(obs["apos_marcar"][3]) == 2, f"marcar uma serie atualiza config e previa na hora ({obs['apos_marcar']})")
    confere(obs["vazio"][0] == 0 and obs["vazio"][1] and obs["vazio"][2] == ["zzz"], f"filtro sem resultado: previa vazia com explicacao ({obs['vazio']})")
    confere(obs["classe_live"] == ["C"], "caixa de classe atualiza ao vivo")
    confere(ret is False and "salvou" not in obs and cfg2["cronograma_filtros"]["series"] == ["Serie Beta - 2026 Season 4"] and cfg2["cronograma_ativo"] is False and cfg2["mostrar_calendario"] is False and not cfg2["cronograma_filtros"].get("pistas") and not cfg2["cronograma_filtros"].get("classes"),
            f"Cancelar desfaz tudo ({cfg2})")
    # salvar
    cfg3 = {"cronograma_filtros": {}, "cronograma_ativo": False, "mostrar_calendario": False}; salv = []
    def passo2():
        w = DLG(); lst = achar(w, QListWidget)[0]
        lst.item(0).setCheckState(Qt.Checked); obs["nome0"] = lst.item(0).text()
        btn = next(b for b in achar(w, QPushButton) if b.text() == "Marcar as visíveis"); btn.click(); obs["marcadas"] = len(cfg3["cronograma_filtros"]["series"])
        next(b for b in achar(w, QPushButton) if b.text() == "Desmarcar todas").click(); obs["zero"] = len(cfg3["cronograma_filtros"]["series"])
        lst.item(1).setCheckState(Qt.Checked)
        next(b for b in achar(w, QPushButton) if b.text().startswith("Save") or b.text() in ("Salvar", "&Save")).click()
    QTimer.singleShot(300, passo2)
    ret = ui.abrir_dialogo(cfg3, dados_ui, lambda c: salv.append("s"), lambda: salv.append("a"), pasta=pastaui)
    confere(ret and obs["marcadas"] == 2 and obs["zero"] == 0 and len(cfg3["cronograma_filtros"]["series"]) == 1 and cfg3["cronograma_ativo"] and cfg3["mostrar_calendario"] and salv == ["s", "a"], f"marcar visiveis / desmarcar todas / salvar ({cfg3}, {obs.get('marcadas')}, {obs.get('zero')})")
    # importar dentro da tela: lista, filtros mantidos, aviso de serie que sumiu
    cfg4 = {"cronograma_filtros": {"series": ["Serie Alfa - 2026 Season 4", "Serie Beta - 2026 Season 4"]}, "cronograma_ativo": True, "mostrar_calendario": True}
    def passo3():
        w = DLG(); lst = achar(w, QListWidget)[0]
        obs["antes_imp"] = lst.count()
        w.importar()
        status = [l.text() for l in achar(w, QLabel) if l.text().startswith("Importado")]
        obs["depois_imp"] = (lst.count(), status, list(cfg4["cronograma_filtros"]["series"]))
        w.reject()
    QTimer.singleShot(300, passo3)
    ui.abrir_dialogo(cfg4, dados_ui, lambda c: None, lambda: None, pasta=pastaui, escolher_arquivo=lambda: b)
    confere(obs["antes_imp"] == 2 and obs["depois_imp"][0] == 1 and obs["depois_imp"][1] and "não existem neste cronograma" in obs["depois_imp"][1][0] and obs["depois_imp"][2] == ["Serie Alfa - 2026 Season 4"],
            f"importar dentro da tela atualiza a lista, mantem as series que existem e avisa as que sumiram ({obs['depois_imp']})")
    confere(len(json.load(open(os.path.join(pastaui, "cronograma.json"), encoding="utf-8"))["series"]) == 1, "o arquivo em disco foi trocado")
    # importar com erro mostra mensagem e nao mexe
    cfg5 = {"cronograma_filtros": {}, "cronograma_ativo": False}
    def passo4():
        w = DLG(); w.importar()
        obs["erro"] = [l.text() for l in achar(w, QLabel) if "não parece" in l.text()]; w.reject()
    QTimer.singleShot(300, passo4)
    ui.abrir_dialogo(cfg5, None, lambda c: None, lambda: None, pasta=pastaui, escolher_arquivo=lambda: lixo)
    confere(obs["erro"], "arquivo errado: a tela explica o motivo")
    def passo6():
        w = DLG(); rot = [l.text() for l in achar(w, QLabel)]
        cbx = next(c for c in achar(w, QCheckBox) if "fuso horário do Windows" in c.text())
        obs["fuso"] = (cbx.isChecked(), [t for t in rot if "relógio deste computador" in t])
        cbx.setChecked(False); rot = [l.text() for l in achar(w, QLabel)]; obs["fuso_fixo"] = ([t for t in rot if t.startswith("Fuso fixo")], cfg6["cronograma_filtros"]["fuso_auto"]); w.reject()
    cfg6 = {"cronograma_filtros": {}, "cronograma_ativo": False}
    QTimer.singleShot(300, passo6); ui.abrir_dialogo(cfg6, dados_ui, lambda c: None, lambda: None, pasta=pastaui)
    confere(obs["fuso"][0] and obs["fuso"][1] and "UTC-03:00" in obs["fuso"][1][0], f"tela mostra o fuso do Windows em uso ({obs['fuso']})")
    confere(obs["fuso_fixo"][0] and obs["fuso_fixo"][1] is False, "desmarcar o fuso do Windows passa para o fixo")
    # sem pasta (importacao indisponivel) nao quebra
    def passo5():
        w = DLG(); obs["btn_off"] = [not b.isEnabled() for b in achar(w, QPushButton) if b.text().startswith("Importar")]; w.reject()
    QTimer.singleShot(300, passo5); ui.abrir_dialogo({}, None, lambda c: None, lambda: None)
    confere(obs["btn_off"] == [True], "sem pasta de dados o botao Importar fica desligado")

# ---------------------------------------------------------------- build ao: auditoria da an (P1 importacao sem horario utilizavel; P2 validacao estrutural)
if TEM_IMPORTADOR:
    pa = os.path.join(S, "pao"); os.makedirs(pa)
    r = cr.importar_arquivo(a, pa); confere(r["ok"], "P1: cronograma bom importado")
    bom = open(os.path.join(pa, "cronograma.json"), "rb").read()
    desc = os.path.join(S, "desc.txt"); open(desc, "w", encoding="utf-8").write("\n".join(texto_serie("Serie Sem Horario - 2026 Season 4", "Mazda MX-5 Cup", "5 Timeslots Per Week", [(T0, "Spa", "20 mins")]) + ["Fim"]))
    r = cr.importar_arquivo(desc, pa)
    confere(not r["ok"] and "nenhuma com horário" in r["msg"] and "mantido" in r["msg"], f"P1: arquivo so com cadencia desconhecida e recusado ({r['msg'][:90]})")
    confere(open(os.path.join(pa, "cronograma.json"), "rb").read() == bom and not os.path.exists(os.path.join(pa, "cronograma_anterior.json")), "P1: cronograma bom e backup preservados na recusa")
    mista = os.path.join(S, "mista.txt"); open(mista, "w", encoding="utf-8").write("\n".join(
        texto_serie("Serie Sem Horario - 2026 Season 4", "Mazda MX-5 Cup", "5 Timeslots Per Week", [(T0, "Spa", "20 mins")]) + [""] +
        texto_serie("Serie Alfa - 2026 Season 4", "Mazda MX-5 Cup", "Races every hour at :15 GMT", [(T0, "Imola", "20 mins")]) + ["Fim"]))
    r = cr.importar_arquivo(mista, pa); confere(r["ok"] and len(r["dados"]["series"]) == 2, "P1: cronograma parcialmente conhecido continua aceito")
    pv = os.path.join(S, "pvazio"); os.makedirs(pv)
    r = cr.importar_arquivo(desc, pv); confere(not r["ok"] and not os.path.exists(os.path.join(pv, "cronograma.json")), "P1: sem cronograma anterior, a recusa tambem nao cria arquivo")
# P2: estrutura
def grava(obj, nome):
    c = os.path.join(S, nome); open(c, "w", encoding="utf-8").write(obj if isinstance(obj, str) else json.dumps(obj)); return c
W = {"semana": 1, "inicio": T0, "pista": "Spa", "duracao": {"min": 20}}
CAD = {"tipo": "passo", "passo_min": 60, "minutos": [15]}
ruins = {
    "series com texto": {"series": ["texto"]},
    "raiz lista": [1, 2],
    "series nao lista": {"series": "x"},
    "serie sem nome": {"series": [{"semanas": [W], "cadencia": CAD}]},
    "serie sem semanas": {"series": [{"serie": "A", "semanas": [], "cadencia": CAD}]},
    "semanas invalidas": {"series": [{"serie": "A", "semanas": ["x", {"inicio": "ontem"}, {"inicio": None}, 5], "cadencia": CAD}]},
}
for nome, obj in ruins.items():
    d_, av = cr.carregar(grava(obj, "r.json"))
    confere(d_ is None and av, f"P2: JSON malformado rejeitado com mensagem ({nome})")
# consulta direta em dados malformados nunca levanta erro
brutos = {"series": ["texto", None, {"serie": "A", "semanas": ["x", {"inicio": "2026-13-45"}], "cadencia": {"tipo": "passo", "passo_min": "oops"}},
                     {"serie": "B", "semanas": [dict(W, inicio=T0)], "cadencia": {"tipo": "passo", "passo_min": "oops", "minutos": "abc"}, "carros": "x"}]}
try:
    cr.proximas(brutos, {"series": ["A", "B"]}, dt.datetime.now(U), 5); cr.sem_horario(brutos); cr.listar_series(brutos); cr.dica_vazio(brutos, {"series": ["B"], "pistas": ["z"]}, dt.datetime.now(U))
    cr.calendario_do_cronograma(brutos, "", {"series": ["B"]}, dt.datetime.now(U)); ok_brutos = True
except Exception as ex:
    ok_brutos = False; print("excecao", repr(ex))
confere(ok_brutos, "P2: consulta em dados malformados nao levanta excecao")
confere(cr.proximas("texto", {"series": ["A"]}, dt.datetime.now(U)) == [] and cr.proximas({"series": 5}, {"series": ["A"]}, dt.datetime.now(U)) == [], "P2: dados que nem sao dicionario")
# cadencia invalida via arquivo: a serie fica (sem aviso), as validas continuam
misto = {"fonte": "x", "series": [{"serie": "Boa", "semanas": [W], "cadencia": CAD, "carros": ["Mazda"]},
                                  {"serie": "Cad Ruim", "semanas": [W], "cadencia": {"tipo": "passo", "passo_min": "oops"}},
                                  {"serie": "Cad Ruim 2", "semanas": [W], "cadencia": {"tipo": "semanal", "horarios": [["x"], [9, 99]]}},
                                  "lixo"]}
d_, av = cr.carregar(grava(misto, "m.json"))
confere(d_ is not None and [s["serie"] for s in d_["series"]] == ["Boa", "Cad Ruim", "Cad Ruim 2"] and d_["_descartadas"] == 1, "P2: serie malformada descartada, as demais mantidas")
confere(set(cr.sem_horario(d_)) == {"Cad Ruim", "Cad Ruim 2"}, "P2: cadencia invalida vira 'desconhecida' (sem aviso, sem erro)")
confere(cr.proximas(d_, {"series": ["Cad Ruim", "Cad Ruim 2"]}, dt.datetime.now(U), 5) == [] and cr.proximas(d_, {"series": ["Boa"]}, dt.datetime.now(U), 5), "P2: consulta ignora as invalidas e atende as validas")
confere(cr.carregar(grava({"series": [{"serie": "A", "semanas": [W], "cadencia": {"tipo": "semanal", "horarios": [[5, 19], [6, 14, 30]]}}]}, "s.json"))[0]["series"][0]["cadencia"]["horarios"] == [[5, 19, 0], [6, 14, 30]], "P2: formato antigo de horarios semanais continua aceito")
if os.path.isfile(os.path.join(RAIZ, "cronograma.json")):
    confere(cr.carregar(os.path.join(RAIZ, "cronograma.json"))[0] is not None and cr.carregar(os.path.join(RAIZ, "cronograma.json"))[0]["_descartadas"] == 0, "P2: o cronograma real (162 series) passa na validacao sem descartes")
else:
    print("PULADO (build az): cronograma.json real ausente (dado do usuario, nao versionado); validacao do cronograma real nao executada")
confere(cr.carregar(grava("{nao json", "j.json"))[0] is None and cr.carregar(os.path.join(S, "nao_existe.json"))[0] is None, "P2: json corrompido/ausente continua com aviso")

print("ok" if not falhas else "FALHAS", _ok); sys.exit(1 if falhas else 0)
