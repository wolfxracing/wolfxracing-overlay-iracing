# -*- coding: utf-8 -*-
"""Converte o PDF "Season Schedule" do iRacing em cronograma.json (usado pelo overlay).

Uso:  python importar_cronograma.py SeasonSchedule.pdf [saida.json]
Precisa do utilitario 'pdftotext' (poppler) OU do pacote 'pypdf'. Tambem aceita o .txt ja extraido com `pdftotext -layout`.
Tudo e interpretado em UTC (o iRacing publica as cadencias em UTC/GMT); o overlay converte para o horario do piloto.
"""
import json, re, subprocess, sys, datetime as dt

DIAS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def texto_do_pdf(caminho):
    if caminho.lower().endswith(".txt"):
        return open(caminho, encoding="utf-8").read()
    try:
        return subprocess.run(["pdftotext", "-layout", caminho, "-"], capture_output=True, text=True, check=True).stdout
    except Exception:
        from pypdf import PdfReader
        return "\n".join((p.extract_text(extraction_mode="layout") or "") for p in PdfReader(caminho).pages)


def cadencia(txt):
    """'Races every 2 hours at :45' -> {'tipo':'passo','passo_min':120,'minutos':[45]} ; semanal -> {'tipo':'semanal','horarios':[(dow,h,m)]}.
    Retorna None se nao entendeu (a serie fica sem alerta ate ser corrigida)."""
    t = " ".join(txt.replace("–", "-").split())
    low = t.lower()
    low = low.split("|")[0]                                   # 'Qualifying ...' depois da barra nao e corrida
    if re.search(r"every 30 minutes|every thirty minutes|every half hour", low):
        mins = [int(m) for m in re.findall(r":(\d\d)", low)] or [0, 30]
        base = sorted({m % 30 for m in mins}) or [0]
        return {"tipo": "passo", "passo_min": 30, "minutos": [base[0]], "texto": t}
    m = re.search(r"every (even |odd )?(?:(\d+) )?hours?|hourly|every other hour", low)
    # 'GMT'/'UTC' so indicam o fuso e NAO tornam a cadencia semanal; semanal = tem dia da semana ou data (ex.: 11/21)
    dia_ou_data = re.search(r"\b(?:mon|tue|tues|wed|weds|thu|thur|thurs|fri|sat|sun)[a-z]*\b|\d+/\d+", low)
    if dia_ou_data:
        return _semanal(low, t)
    if m or re.search(r"every hour|on the hour|at :|past every|every 2 hours|45 past|half past|top of the hour", low):
        passo = 120 if re.search(r"every (even |odd )?2 hours|every other hour|every odd 2|every even 2|past every 2 hours|past every 2", low) else 60
        mm = re.search(r":(\d\d)", low) or re.search(r"\b(\d\d?) past", low)
        if mm:
            minuto = int(mm.group(1))
        elif "half past" in low:
            minuto = 30
        else:
            minuto = 0
        par = 1 if "odd" in low else 0                          # horas pares por padrao (premissa; confirmar no iRacing)
        return {"tipo": "passo", "passo_min": passo, "minutos": [minuto], "paridade": par if passo == 120 else None, "texto": t}
    return None


def _semanal(low, t):
    return None  # horarios fixos por dia da semana: ver _semanal_texto (precisa de revisao manual por serie)


def _semanal_texto(t):
    """Horarios 'Saturday at 19:30 GMT' -> lista (dia_da_semana, hora, minuto). So aceita formatos simples; o resto vai para revisao."""
    low = " ".join(t.lower().split()).split("|")[0]
    if "every other" in low or re.search(r"\d+/\d+", low) or " et" in low:
        return None
    dias = {"mon": "mon", "tue": "tue", "wed": "wed", "weds": "wed", "thu": "thu", "thur": "thu", "fri": "fri", "sat": "sat", "sun": "sun"}
    partes = re.split(r"\bgmt\b|\butc\b", low)
    out = []
    for seg in partes:
        ds = re.findall(r"\b(mon|tue|wed|weds|thu|thur|fri|sat|sun)[a-z]*\b", seg)
        limpo = re.sub(r"races|every|\bat\b", " ", seg)
        hs = [(int(h), int(mn or 0)) for h, mn in re.findall(r"\b(\d{1,2})(?::(\d{2}))?\b", limpo)]
        hs = [(h, mn) for h, mn in hs if 0 <= h <= 23 and 0 <= mn <= 59]
        if not ds and not hs:
            continue
        for d in ds:
            for h, mn in hs:
                out.append((DIAS[dias[d]], h, mn))
    return out or None


def interpretar(txt):
    c = cadencia(txt)
    if c is not None:
        return c
    h = _semanal_texto(txt)
    if h:
        return {"tipo": "semanal", "horarios": sorted(set(h)), "texto": " ".join(txt.split())}
    return {"tipo": "desconhecida", "texto": " ".join(txt.split())}


def duracao(txt):
    t = txt.strip().lower()
    m = re.match(r"(\d+(?:\.\d+)?)\s*(mins?|laps?|hrs?|hours?)", t)
    if not m:
        return None, t
    v, u = float(m.group(1)), m.group(2)
    if u.startswith("min"):
        return {"min": v}, t
    if u.startswith("lap"):
        return {"voltas": int(v)}, t
    return {"min": v * 60}, t


def nomes_do_indice(linhas):
    """Nomes das series do indice (TOC) e a classe de cada uma, dada pela secao 'B Class Series (...)' em que aparece."""
    nomes, classe_serie, atual = set(), {}, ""
    for l in linhas[:400]:
        m = re.match(r"^\s*(.*?)\s*(?:\. ?){4,}\s*\d+\s*$", l)
        if m and m.group(1):
            nome = " ".join(m.group(1).split())
            nomes.add(nome)
            sec = re.match(r"^([RDCBA]) Class Series", nome)
            if sec:
                atual = sec.group(1)
            elif atual:
                classe_serie.setdefault(nome, atual)
    nomes_do_indice.classe_serie = classe_serie
    return nomes


_CLIMA = re.compile(r"\s{2,}|\s(?=\d{2,3}\u00b0F/)|\s(?=(?:Rain possible|All dry|Forecast|Dry events|Rain likely))")
_DUR = re.compile(r"(\d+(?:\.\d+)?)\s*(mins?|laps?|hrs?|hours?)\s*$", re.I)


def _linha_semana(resto):
    mdur = _DUR.search(resto)
    dur = None
    if mdur:
        dur, _ = duracao(mdur.group(0))
    pista = _CLIMA.split(resto.strip(), maxsplit=1)[0].strip()
    return pista, dur, (mdur.group(0) if mdur else "")


def processar(texto):
    linhas = texto.splitlines()
    nomes = nomes_do_indice(linhas)
    series, n = [], len(linhas)
    idx_w1 = [k for k, l in enumerate(linhas) if re.match(r"^Week 1 \(", l)]
    ult_fim = 0
    for w1 in idx_w1:
        k, cab = w1 - 1, []
        while k >= ult_fim and len(cab) < 16 and linhas[k].strip():
            t = linhas[k].strip()
            if not re.fullmatch(r"\d{1,3}", t):
                cab.append(t)
            k -= 1
        cab.reverse()
        it = next((i for i, c in enumerate(cab) if c in nomes and not re.match(r"^[RDCBA] Class Series", c)), 0)
        titulo = cab[it] if cab else "?"
        ic = next((i for i, c in enumerate(cab) if re.match(r"^(Races?\b|Every\b)", c)), None)
        classe_i = next((i for i, c in enumerate(cab) if "-->" in c), None)
        fim_carros = classe_i if classe_i is not None else (ic if ic is not None else len(cab))
        carros = " ".join(cab[it + 1:fim_carros])
        classe = cab[classe_i] if classe_i is not None else ""
        rac = ""
        if ic is not None:
            rac = cab[ic]
            if ic + 1 < len(cab) and not cab[ic + 1].startswith(("Min ", "Penalty", "Forecast", "No incident", "DQ")):
                rac += " " + cab[ic + 1]
        semanas, p = [], w1
        while p < n:
            m = re.match(r"^Week (\d+) \((\d{4}-\d\d-\d\d)\)\s+(.*)$", linhas[p])
            if m:
                pista, dur, dtxt = _linha_semana(m.group(3))
                prox = linhas[p + 1] if p + 1 < n else ""
                st = prox.strip()
                if st and not st.startswith("(") and prox.startswith(" " * 10) and len(_CLIMA.split(st, maxsplit=1)[0]) == len(st) \
                        and len(st) < 45 and not re.match(r"^(Start|Local|Full|Cautions|Rain|All|Dog|-|\d)", st):
                    pista += " " + st
                semanas.append({"semana": int(m.group(1)), "inicio": m.group(2), "pista": pista, "duracao": dur, "duracao_txt": dtxt})
                ult_fim = p + 1
            elif linhas[p].strip() == "" and semanas:
                q = p + 1                                 # linhas em branco e o numero da pagina nao encerram a tabela
                while q < n and (linhas[q].strip() == "" or re.fullmatch(r"\s*\d{1,3}\s*", linhas[q])):
                    q += 1
                if q >= n or not re.match(r"^Week \d+ \(", linhas[q]):
                    if not re.match(r"^\s", linhas[q] if q < n else ""):
                        break
            elif semanas and re.match(r"^[A-Z].{3,}", linhas[p]) and not linhas[p].startswith(("Week", " ")):
                break
            p += 1
        if semanas:
            series.append({"serie": titulo, "carros": [c.strip() for c in carros.split(",") if c.strip()],
                           "classe": classe.replace("Class ", ""), "classe_serie": nomes_do_indice.classe_serie.get(titulo, ""),
                           "cadencia": interpretar(rac), "semanas": semanas})
    return series


def converter_texto(texto, fonte):
    """Texto extraido do PDF -> dicionario do cronograma.json (usado pelo overlay e por esta linha de comando)."""
    return {"gerado_em": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "fonte": fonte, "series": [x for x in processar(texto) if x.get("serie") != "?"]}   # "?" = semanas soltas, sem cabecalho de serie


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    dados = converter_texto(texto_do_pdf(sys.argv[1]), sys.argv[1].replace("\\", "/").split("/")[-1])
    series = dados["series"]
    saida = sys.argv[2] if len(sys.argv) > 2 else "cronograma.json"
    json.dump(dados, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    por = {}
    for s in series:
        por[s["cadencia"]["tipo"]] = por.get(s["cadencia"]["tipo"], 0) + 1
    print(f"{len(series)} series, {sum(len(s['semanas']) for s in series)} semanas; cadencias: {por}")


if __name__ == "__main__":
    main()
