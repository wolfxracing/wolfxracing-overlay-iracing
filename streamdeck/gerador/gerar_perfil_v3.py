#!/usr/bin/env python3
"""Perfil Stream Deck XL 'Overlay iRacing': layout aprovado, chaves "coluna,linha", icones da biblioteca streamdeck_icons."""
import io, json, os, random, string, sys, uuid, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from icones_base import DEVICE_UUID, MODEL
BIB, PACOTE, OUT_DIR = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, PACOTE)
import ov_nucleo as nu
BASE = r"C:\WolfxRacing\wolfxracing-overlay-iracing\overlay"
LAY = json.load(open(f"{BIB}/layout_proposto.json"))

# icone -> (tipo, alvo)
ACAO = {
 "perfil_auto": ("tecla", "perfil_auto"), "perfil_treino": ("tecla", "perfil_treino"),
 "perfil_classificacao": ("tecla", "perfil_classificacao"), "perfil_corrida": ("tecla", "perfil_corrida"),
 "ctrl_economia_cpu": ("tecla", "economia_cpu"), "ctrl_aparecer_sozinho": ("tecla", "aparecer_sozinho"),
 "ctrl_travar_posicao": ("tecla", "travar_posicao"), "ctrl_zerar_pico_g": ("tecla", "zerar_pico_g"),
 "ctrl_limpar_impactos": ("tecla", "limpar_impactos"), "ctrl_fechar": ("tecla", "sair"),
 "ctrl_iniciar": ("abrir", "iniciar_overlay.bat"), "ctrl_forcar_fechamento": ("abrir", "fechar_overlay.bat"),
 "sup_demo": ("abrir", "testar_demo.bat"), "sup_log": ("abrir", "overlay_log.txt"), "sup_pasta_overlay": ("abrir", ""),
 "sup_pasta_suporte": ("pasta", ""), "sup_voltar": ("voltar", ""),
 "sup_atalhos": ("abrir", "ATALHOS_STREAM_DECK.txt"), "sup_testes": ("abrir", "executar_testes.bat"),
 "sup_emblemas": ("abrir", "abrir_pasta_emblemas.bat"), "sup_historico": ("abrir", "historico_projecoes.csv"),
 "sup_guia": ("abrir", "LEIA-ME.txt"), "sup_roteiro": ("abrir", "ROTEIRO_VALIDACAO.txt"),
 "sup_inicio_windows_on": ("abrir", "ativar_inicio_automatico.bat"), "sup_inicio_windows_off": ("abrir", "desativar_inicio_automatico.bat"),
 "sup_recordes": ("abrir", "recordes_pessoais.json"),
}
for n in ("telemetria","voltas","relativo","classificacao","mapa","radar","pneus","setores","clima","danos","combustivel","forca_g"):
    ACAO[f"janela_{n}"] = ("tecla", f"janela_{n}")

def rid(): return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(26)) + "Z"
def estado(img): return {"FontFamily": "", "FontSize": 11, "FontStyle": "", "FontUnderline": False, "Image": img,
        "OutlineThickness": 2, "ShowTitle": False, "Title": "", "TitleAlignment": "bottom", "TitleColor": "#ffffff"}
VAZIO = {"KeyCmd": False, "KeyCtrl": False, "KeyModifiers": 0, "KeyOption": False, "KeyShift": False, "NativeCode": 146, "QTKeyCode": 33554431, "VKeyCode": -1}
def a_abrir(alvo, img):
    cam = BASE if not alvo else BASE + "\\" + alvo
    return {"ActionID": str(uuid.uuid4()), "LinkedTitle": True, "Name": "Open", "Plugin": {"Name": "Open", "UUID": "com.elgato.streamdeck.system.open", "Version": "1.0"},
            "Resources": None, "Settings": {"path": '"' + cam + '"'}, "State": 0, "States": [estado(img)], "UUID": "com.elgato.streamdeck.system.open"}
def a_tecla(at, img):
    sh, ct, al = bool(at.mods & nu.MOD_SHIFT), bool(at.mods & nu.MOD_CONTROL), bool(at.mods & nu.MOD_ALT)
    km = (1 if sh else 0) | (2 if ct else 0) | (4 if al else 0)
    t = {"KeyCmd": False, "KeyCtrl": ct, "KeyModifiers": km, "KeyOption": al, "KeyShift": sh, "NativeCode": at.vk, "QTKeyCode": 0x01000030 + (at.fn - 1), "VKeyCode": at.vk}
    return {"ActionID": str(uuid.uuid4()), "LinkedTitle": True, "Name": "Hotkey", "Plugin": {"Name": "Activate a Key Command", "UUID": "com.elgato.streamdeck.system.hotkey", "Version": "1.0"},
            "Resources": None, "Settings": {"Coalesce": True, "Hotkeys": [t, dict(VAZIO), dict(VAZIO), dict(VAZIO)]}, "State": 0, "States": [estado(img)], "UUID": "com.elgato.streamdeck.system.hotkey"}
def a_pasta(filha, img):
    return {"ActionID": str(uuid.uuid4()), "LinkedTitle": True, "Name": "Create Folder", "Plugin": {"Name": "Create Folder", "UUID": "com.elgato.streamdeck.profile.openchild", "Version": "1.0"},
            "Resources": None, "Settings": {"ProfileUUID": filha.lower()}, "State": 0, "States": [estado(img)], "UUID": "com.elgato.streamdeck.profile.openchild"}
def a_voltar(img):
    return {"ActionID": str(uuid.uuid4()), "LinkedTitle": True, "Name": "Parent Folder", "Plugin": {"Name": "Open Parent Folder", "UUID": "com.elgato.streamdeck.profile.backtoparent", "Version": "1.0"},
            "Resources": None, "Settings": {}, "State": 0, "States": [{"Image": img}], "UUID": "com.elgato.streamdeck.profile.backtoparent"}

def pagina(lay, raiz, pid, arq, filha=None):
    acoes = {}
    for pos, ic in lay.items():                      # pos = "coluna,linha"
        tipo, alvo = ACAO[ic]
        nome = rid() + ".png"
        arq[f"{raiz}/Profiles/{pid}/Images/{nome}"] = open(f"{BIB}/png/{ic}.png", "rb").read()
        img = "Images/" + nome
        if tipo == "tecla":
            at = nu.atalho_por_id(alvo); assert at is not None, alvo; a = a_tecla(at, img)
        elif tipo == "abrir": a = a_abrir(alvo, img)
        elif tipo == "pasta": a = a_pasta(filha, img)
        else: a = a_voltar(img)
        acoes[pos] = a
    return {"Controllers": [{"Actions": acoes, "Type": "Keypad"}], "Icon": "", "Name": ""}

def main():
    assert nu.validar_atalhos() == []
    random.seed(20261031)
    prof, pg, padrao, filha = (str(uuid.uuid4()).upper() for _ in range(4))
    raiz = f"Profiles/{prof}.sdProfile"; arq = {}
    mp = pagina(LAY["principal"], raiz, pg, arq, filha)
    ms = pagina(LAY["suporte"], raiz, filha, arq)
    vazio = {"Controllers": [{"Actions": None, "Type": "Keypad"}], "Icon": "", "Name": ""}
    mprof = {"Device": {"Model": MODEL, "UUID": DEVICE_UUID}, "Name": "Overlay iRacing", "Pages": {"Current": pg.lower(), "Default": padrao.lower(), "Pages": [pg.lower()]}, "Version": "3.0"}
    pac = {"AppVersion": "7.4.2.22730", "DeviceModel": MODEL, "DeviceSettings": None, "FormatVersion": 1, "OSType": "Windows", "OSVersion": "10.0.26200",
           "RequiredPlugins": ["com.elgato.streamdeck.system.open", "com.elgato.streamdeck.system.hotkey", "com.elgato.streamdeck.profile.openchild", "com.elgato.streamdeck.profile.backtoparent"]}
    os.makedirs(OUT_DIR, exist_ok=True)
    saida = os.path.join(OUT_DIR, "Overlay iRacing.streamDeckProfile")
    dump = lambda o: json.dumps(o, separators=(",", ":"))
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("package.json", dump(pac)); z.writestr(f"{raiz}/manifest.json", dump(mprof))
        z.writestr(f"{raiz}/Profiles/{padrao}/manifest.json", dump(vazio))
        z.writestr(f"{raiz}/Profiles/{pg}/manifest.json", dump(mp)); z.writestr(f"{raiz}/Profiles/{filha}/manifest.json", dump(ms))
        for p, b in arq.items(): z.writestr(p, b)
    print(saida)
main()
