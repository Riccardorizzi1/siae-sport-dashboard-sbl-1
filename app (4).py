import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import base64
from pathlib import Path

# =========================
# FORMATTAZIONE NUMERI ITALIANA
# =========================

import math
import re
import pandas as pd

def normalizza_numero(value):
    """
    Converte un valore numerico in float senza confondere:
    - 27192.0
    - 175574380.99
    - 27,192.00
    - 27.192
    - 175.574.380,99
    - 306,16
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        try:
            if pd.isna(value):
                return None
            return float(value)
        except Exception:
            return None

    if isinstance(value, str):
        s = value.strip()

        if s == "" or s.lower() in ["nan", "none", "-"]:
            return None

        s = s.replace("€", "").replace("%", "").strip()

        # Formato US con migliaia: 27,192.00 oppure 175,574,380.99
        if re.fullmatch(r"[-+]?\d{1,3}(,\d{3})+(\.\d+)?", s):
            return float(s.replace(",", ""))

        # Formato IT con migliaia: 27.192 oppure 175.574.380,99
        if re.fullmatch(r"[-+]?\d{1,3}(\.\d{3})+(,\d+)?", s):
            return float(s.replace(".", "").replace(",", "."))

        # Formato Python standard: 27192.0 oppure 175574380.99
        if re.fullmatch(r"[-+]?\d+(\.\d+)?", s):
            return float(s)

        # Decimale italiano semplice: 306,16
        if re.fullmatch(r"[-+]?\d+,\d+", s):
            return float(s.replace(",", "."))

    return None


def format_num_it(value, decimals=2, euro=False, percent=False):
    """
    Formato italiano:
    - punto per migliaia
    - virgola per decimali
    - massimo 2 decimali
    - nessun ,00 quando il numero è intero
    """
    n = normalizza_numero(value)

    if n is None:
        return "-"

    try:
        if math.isnan(n) or math.isinf(n):
            return "-"
    except Exception:
        return "-"

    if abs(n - round(n)) < 1e-9:
        out = f"{int(round(n)):,}"
    else:
        out = f"{n:,.{decimals}f}"

    out = out.replace(",", "X").replace(".", ",").replace("X", ".")

    if euro:
        out = "€ " + out

    if percent:
        out = out + "%"

    return out


def token_gia_formattato_it(token):
    """
    Evita doppia formattazione.
    Esempi da NON ritoccare:
    - 27.192
    - 8.325.231
    - 175.574.380,99
    - 306,16
    """
    token = str(token).strip()

    if re.fullmatch(r"[-+]?\d{1,3}(\.\d{3})+(,\d{1,2})?", token):
        return True

    if re.fullmatch(r"[-+]?\d+,\d{1,2}", token):
        return True

    return False


def sembra_anno(token):
    token = str(token).strip()
    return bool(re.fullmatch(r"(19|20)\d{2}", token))


def formatta_token_numerico(match):
    token = match.group(0)

    if sembra_anno(token):
        return token

    if token_gia_formattato_it(token):
        return token

    # Non toccare piccoli interi isolati tipo 0, 1, 10, 100
    if re.fullmatch(r"[-+]?\d{1,3}", token):
        return token

    n = normalizza_numero(token)

    if n is None:
        return token

    return format_num_it(n, decimals=2)


def formatta_testo_numeri_it(testo_input):
    """
    Formatta numeri dentro markdown/HTML senza toccare:
    - CSS
    - script
    - tag HTML
    - anni
    - numeri già formattati correttamente
    """
    if not isinstance(testo_input, str):
        return testo_input

    try:
        testo_lavoro = testo_input

        protetti = {}

        def proteggi(m):
            key = f"__BLOCCO_PROTETTO_{len(protetti)}__"
            protetti[key] = m.group(0)
            return key

        testo_lavoro = re.sub(r"<style[\s\S]*?</style>", proteggi, testo_lavoro, flags=re.IGNORECASE)
        testo_lavoro = re.sub(r"<script[\s\S]*?</script>", proteggi, testo_lavoro, flags=re.IGNORECASE)

        parti = re.split(r"(<[^>]+>)", testo_lavoro)

        pattern_num = (
            r"(?<![#\w])[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?"
            r"|(?<![#\w])[-+]?\d{1,3}(?:\.\d{3})+(?:,\d+)?"
            r"|(?<![#\w])[-+]?\d{4,}(?:\.\d+)?"
            r"|(?<![#\w])[-+]?\d+\.\d+(?![\w])"
            r"|(?<![#\w])[-+]?\d+,\d{3,}(?![\w])"
        )

        parti_out = []

        for parte in parti:
            if parte.startswith("<") and parte.endswith(">"):
                parti_out.append(parte)
            else:
                parti_out.append(re.sub(pattern_num, formatta_token_numerico, parte))

        testo_lavoro = "".join(parti_out)

        for key, value in protetti.items():
            testo_lavoro = testo_lavoro.replace(key, value)

        return testo_lavoro

    except Exception:
        return testo_input


def format_df_it(df):
    """
    Formatta le tabelle Streamlit:
    - anni invariati
    - testo invariato
    - numeri con punto migliaia e virgola decimali
    - massimo 2 decimali
    """
    try:
        if not isinstance(df, pd.DataFrame):
            return df

        df2 = df.copy()

        for col in df2.columns:
            col_lower = str(col).lower()

            if col_lower in ["anno", "year"] or "anno" in col_lower or "year" in col_lower:
                continue

            def formatta_cella(x):
                if x is None:
                    return "-"

                try:
                    if pd.isna(x):
                        return "-"
                except Exception:
                    pass

                if isinstance(x, str):
                    sx = x.strip()

                    if sx == "" or sx.lower() in ["nan", "none"]:
                        return "-"

                    if token_gia_formattato_it(sx):
                        return sx

                    n = normalizza_numero(sx)

                    if n is None:
                        return x

                    return format_num_it(n, decimals=2)

                if isinstance(x, (int, float)):
                    return format_num_it(x, decimals=2)

                return x

            df2[col] = df2[col].apply(formatta_cella)

        return df2

    except Exception:
        return df


def formatta_plotly_numeri_it(fig):
    try:
        fig.update_layout(separators=",.")

        fig.update_yaxes(
            tickformat=",.2~f",
            separatethousands=True
        )

        fig.update_xaxes(
            separatethousands=False
        )

        return fig

    except Exception:
        return fig


# Patch markdown / HTML cards
_ST_MARKDOWN_ORIG = st.markdown

def markdown_it(body, *args, **kwargs):
    return _ST_MARKDOWN_ORIG(formatta_testo_numeri_it(body), *args, **kwargs)

st.markdown = markdown_it


# Patch metric
_ST_METRIC_ORIG = st.metric

def metric_it(label, value, delta=None, *args, **kwargs):
    label_lower = str(label).lower()

    euro = any(x in label_lower for x in ["botteghino", "incasso", "ricavi", "euro", "€"])
    percent = any(x in label_lower for x in ["quota", "percentuale", "%", "yoy", "resilienza"])

    value_fmt = format_num_it(value, decimals=2, euro=euro, percent=percent)

    if delta is not None:
        delta_fmt = format_num_it(delta, decimals=2, percent=percent)
    else:
        delta_fmt = None

    return _ST_METRIC_ORIG(label, value_fmt, delta_fmt, *args, **kwargs)

st.metric = metric_it


# Patch tabelle
_ST_DATAFRAME_ORIG = st.dataframe
_ST_TABLE_ORIG = st.table

def dataframe_it(data=None, *args, **kwargs):
    return _ST_DATAFRAME_ORIG(format_df_it(data), *args, **kwargs)

def table_it(data=None, *args, **kwargs):
    return _ST_TABLE_ORIG(format_df_it(data), *args, **kwargs)

st.dataframe = dataframe_it
st.table = table_it

try:
    _ST_DATA_EDITOR_ORIG = st.data_editor

    def data_editor_it(data=None, *args, **kwargs):
        return _ST_DATA_EDITOR_ORIG(format_df_it(data), *args, **kwargs)

    st.data_editor = data_editor_it
except Exception:
    pass


# Patch Plotly
_ST_PLOTLY_CHART_ORIG = st.plotly_chart

def plotly_chart_it(fig, *args, **kwargs):
    fig = formatta_plotly_numeri_it(fig)
    return _ST_PLOTLY_CHART_ORIG(fig, *args, **kwargs)

st.plotly_chart = plotly_chart_it

# =========================
# FINE FORMATTAZIONE NUMERI ITALIANA


# =========================
# FIX ANNI FORMATTAZIONE NUMERI
# =========================

def normalizza_anno_token(token):
    """
    Riconosce e corregge anni scritti come:
    - 2021
    - 2021.0
    - 2,021
    - 2.021
    e li riporta sempre a 2021.
    """
    try:
        s = str(token).strip()

        if s == "":
            return None

        # Caso normale: 2021
        if re.fullmatch(r"(19|20)\d{2}", s):
            return s

        # Caso 2021.0 oppure 2021,0
        if re.fullmatch(r"(19|20)\d{2}[.,]0+", s):
            return s.split(".")[0].split(",")[0]

        # Caso 2,021 oppure 2.021
        if re.fullmatch(r"\d{1,2}[.,]\d{3}", s):
            candidato = s.replace(".", "").replace(",", "")
            if re.fullmatch(r"(19|20)\d{2}", candidato):
                return candidato

        return None

    except Exception:
        return None


def sembra_anno(token):
    """
    Protegge gli anni, evitando che 2021 diventi 2,021 o 2.021.
    """
    return normalizza_anno_token(token) is not None


def formatta_token_numerico(match):
    token = match.group(0)

    anno = normalizza_anno_token(token)
    if anno is not None:
        return anno

    if token_gia_formattato_it(token):
        return token

    # Non toccare piccoli interi isolati tipo 0, 1, 10, 100
    if re.fullmatch(r"[-+]?\d{1,3}", token):
        return token

    n = normalizza_numero(token)

    if n is None:
        return token

    return format_num_it(n, decimals=2)


def format_df_it(df):
    """
    Formatta le tabelle Streamlit:
    - colonne anno/year/periodo/data sempre lasciate come anni leggibili
    - numeri con punto migliaia e virgola decimali
    - massimo 2 decimali
    """
    try:
        if not isinstance(df, pd.DataFrame):
            return df

        df2 = df.copy()

        for col in df2.columns:
            col_lower = str(col).lower()

            is_colonna_anno = (
                col_lower in ["anno", "year", "anni", "periodo", "data"]
                or "anno" in col_lower
                or "year" in col_lower
                or "periodo" in col_lower
                or "data" in col_lower
            )

            def formatta_cella(x):
                if x is None:
                    return "-"

                try:
                    if pd.isna(x):
                        return "-"
                except Exception:
                    pass

                if is_colonna_anno:
                    anno = normalizza_anno_token(x)
                    if anno is not None:
                        return anno

                    sx = str(x).strip()
                    if sx.endswith(".0"):
                        sx = sx[:-2]
                    return sx

                if isinstance(x, str):
                    sx = x.strip()

                    if sx == "" or sx.lower() in ["nan", "none"]:
                        return "-"

                    anno = normalizza_anno_token(sx)
                    if anno is not None:
                        return anno

                    if token_gia_formattato_it(sx):
                        return sx

                    n = normalizza_numero(sx)

                    if n is None:
                        return x

                    return format_num_it(n, decimals=2)

                if isinstance(x, (int, float)):
                    return format_num_it(x, decimals=2)

                return x

            df2[col] = df2[col].apply(formatta_cella)

        return df2

    except Exception:
        return df


def formatta_plotly_numeri_it(fig):
    """
    Formatta i grafici:
    - asse Y numerico in formato italiano
    - asse X con anni sempre senza separatore migliaia
    """
    try:
        fig.update_layout(separators=",.")

        fig.update_yaxes(
            tickformat=",.2~f",
            separatethousands=True
        )

        anni_tickvals = []
        anni_ticktext = []

        try:
            for trace in fig.data:
                if hasattr(trace, "x") and trace.x is not None:
                    for v in list(trace.x):
                        anno = normalizza_anno_token(v)
                        if anno is not None:
                            anni_tickvals.append(v)
                            anni_ticktext.append(anno)
        except Exception:
            pass

        if len(anni_tickvals) > 0:
            # rimuove duplicati mantenendo l'ordine
            coppie = []
            viste = set()

            for val, txt in zip(anni_tickvals, anni_ticktext):
                key = str(txt)
                if key not in viste:
                    viste.add(key)
                    coppie.append((val, txt))

            fig.update_xaxes(
                tickmode="array",
                tickvals=[c[0] for c in coppie],
                ticktext=[c[1] for c in coppie],
                separatethousands=False
            )
        else:
            fig.update_xaxes(
                separatethousands=False
            )

        return fig

    except Exception:
        return fig

# =========================
# FINE FIX ANNI FORMATTAZIONE NUMERI
# =========================

# =========================




















# =====================================================
# SBL LOGO - SOLO VISUALE
# =====================================================
def _sbl_logo_src():
    candidates = [
        "/content/logo_sbl.png",
        "logo_sbl.png",
        "/content/logo_sbl.webp",
        "logo_sbl.webp",
    ]

    for name in candidates:
        p = Path(name)
        if p.exists():
            suffix = p.suffix.lower()
            if suffix == ".png":
                mime = "image/png"
            elif suffix == ".webp":
                mime = "image/webp"
            else:
                mime = "image/jpeg"

            with open(p, "rb") as f:
                return f"data:{mime};base64," + base64.b64encode(f.read()).decode()

    return ""

SBL_LOGO_SRC = _sbl_logo_src()
SBL_HEADER_LOGO = (
    f"<img class='sbl-header-logo' src='{SBL_LOGO_SRC}' />"
    if SBL_LOGO_SRC
    else "🏟️"
)
# =====================================================




# =====================================================
# CONFIGURAZIONE PAGINA
# =====================================================

st.set_page_config(
    page_title="SIAE Sport Dashboard",
    page_icon="🏟️",
    layout="wide"
)



















# =========================
# FIX SIDEBAR MENU
# =========================

st.markdown("""
<style>

/* Larghezza stabile della sidebar */
section[data-testid="stSidebar"] {
    min-width: 310px !important;
    max-width: 360px !important;
}

/* Contenitore radio/menu */
section[data-testid="stSidebar"] div[role="radiogroup"] {
    width: 100% !important;
}

/* Ogni voce del menu */
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 10px !important;
    width: 100% !important;
    min-height: 54px !important;
    padding: 12px 14px !important;
    margin-bottom: 10px !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
    background: rgba(255,255,255,0.08) !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
}

/* Pallino radio: impedisce che diventi una barra enorme */
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
    flex: 0 0 16px !important;
    width: 16px !important;
    min-width: 16px !important;
    max-width: 16px !important;
    height: 16px !important;
    min-height: 16px !important;
    max-height: 16px !important;
    margin: 0 !important;
    padding: 0 !important;
    transform: none !important;
}

/* Eventuali elementi interni del pallino */
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child * {
    width: 16px !important;
    min-width: 16px !important;
    max-width: 16px !important;
    height: 16px !important;
    min-height: 16px !important;
    max-height: 16px !important;
    border-radius: 50% !important;
    transform: none !important;
}

/* Testo della voce menu */
section[data-testid="stSidebar"] div[role="radiogroup"] label p {
    white-space: nowrap !important;
    word-break: normal !important;
    overflow-wrap: normal !important;
    writing-mode: horizontal-tb !important;
    text-orientation: mixed !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    margin: 0 !important;
    line-height: 1.2 !important;
}

/* Contenitore del testo */
section[data-testid="stSidebar"] div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] {
    flex: 1 1 auto !important;
    min-width: 0 !important;
    max-width: 100% !important;
}

/* Evita che Streamlit stringa il testo */
section[data-testid="stSidebar"] div[role="radiogroup"] label span,
section[data-testid="stSidebar"] div[role="radiogroup"] label div {
    writing-mode: horizontal-tb !important;
}

/* Stato hover */
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.16) !important;
}

/* Nasconde eventuali pseudo-elementi enormi creati da vecchi CSS */
section[data-testid="stSidebar"] div[role="radiogroup"] label::before,
section[data-testid="stSidebar"] div[role="radiogroup"] label::after {
    max-width: 18px !important;
    max-height: 18px !important;
}

</style>
""", unsafe_allow_html=True)

# =========================
# FINE FIX SIDEBAR MENU
# =========================






# =====================================================
# SBL UI PATCH - SOLO VISUALE
# =====================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif !important;
    background: linear-gradient(135deg, #EAF9FD 0%, #B7F1FA 45%, #39BDE8 100%) !important;
    color: #0D2D44 !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

.block-container {
    padding-top: 1.6rem !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    max-width: none !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #0D2D44 0%, #174C67 45%, #03789C 75%, #27BBE8 100%) !important;
    color: #ffffff !important;
    box-shadow: 4px 0 22px rgba(13, 45, 68, 0.25);
}

section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

section[data-testid="stSidebar"] label {
    color: #D9F8FF !important;
    font-weight: 600 !important;
}

/* BRAND SIDEBAR */
.sbl-sidebar-brand {
    margin-bottom: 1.1rem;
}

.sbl-sidebar-logo {
    width: 100px;
    height: 100px;
    border-radius: 18px;
    background: rgba(255,255,255,0.12);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1rem;
    overflow: hidden;
}

.sbl-sidebar-logo img {
    width: 90px;
    height: 90px;
    object-fit: contain;
    border-radius: 50%;
    background: #ffffff;
}

.sbl-sidebar-title {
    font-size: 1.35rem;
    font-weight: 800;
    line-height: 1.05;
    color: #ffffff !important;
    margin-bottom: 0.35rem;
}

.sbl-sidebar-sub {
    font-size: 0.82rem;
    color: #D9F8FF !important;
    line-height: 1.35;
}

.sbl-sidebar-sep {
    height: 1px;
    background: rgba(255,255,255,0.22);
    margin: 1.2rem 0;
}

/* RADIO SEZIONI */
section[data-testid="stSidebar"] div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 0.5rem !important;
    width: 100% !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label {
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    width: 100% !important;
    min-height: 54px !important;
    box-sizing: border-box !important;
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.20) !important;
    border-radius: 10px !important;
    padding: 0.65rem 0.8rem !important;
    margin: 0 !important;
    transition: all 0.15s ease !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.16) !important;
    transform: translateX(2px);
}

section[data-testid="stSidebar"] div[role="radiogroup"] label p {
    margin: 0 !important;
    font-size: 0.98rem !important;
    line-height: 1.2 !important;
    white-space: normal !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label > div {
    width: 100% !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label input {
    margin-right: 0.65rem !important;
    flex-shrink: 0 !important;
}

/* SELECTBOX */
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stMultiSelect"] > div > div {
    border-radius: 10px !important;
    border: 1px solid #A5E9F7 !important;
}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.10) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
}

/* TITOLI */
h1, h2, h3 {
    color: #0D2D44 !important;
    font-weight: 800 !important;
}

p, span, label, div {
    font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif !important;
}

/* LOGO NEL TITOLO */
.sbl-header-logo {
    width: 66px;
    height: 66px;
    object-fit: contain;
    vertical-align: middle;
    margin-right: 16px;
    border-radius: 50%;
    background: #ffffff;
    border: 2px solid #F0951D;
    padding: 3px;
    box-shadow: 0 4px 14px rgba(13,45,68,0.18);
}

/* CARD / TABELLE */
div[data-testid="stMetric"],
.kpi-card {
    background: #ffffff !important;
    border-radius: 18px !important;
    box-shadow: 0 8px 24px rgba(13,45,68,0.10) !important;
    border: 1px solid #CDEFF7 !important;
}

[data-testid="stDataFrame"] {
    border-radius: 16px !important;
    overflow: hidden !important;
    box-shadow: 0 8px 24px rgba(13,45,68,0.10) !important;
}

.js-plotly-plot {
    border-radius: 16px !important;
}

/* BOTTONI */
.stButton > button {
    background: #00649C !important;
    color: white !important;
    border-radius: 10px !important;
    border: 1px solid #1C9FE8 !important;
    font-weight: 700 !important;
}

.stButton > button:hover {
    background: #03789C !important;
    border-color: #27BBE8 !important;
}
</style>
""", unsafe_allow_html=True)

px.defaults.color_discrete_sequence = [
    "#00649C",
    "#00A2D2",
    "#27BBE8",
    "#10B6E8",
    "#03789C",
    "#E85933",
    "#E8AA05",
]
px.defaults.template = "plotly_white"
# =====================================================


# =====================================================
# COLORI E LAYOUT GRAFICI
# =====================================================

COLORI_AZIENDALI = [
    "#00649C",
    "#00A2D2",
    "#27BBE8",
    "#10B6E8",
    "#03789C",
    "#E85933",
    "#E8AA05",
]


def applica_layout_plotly(fig):
    """Applica uno stile uniforme ai grafici Plotly."""

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.92)",
        font=dict(
            family="Plus Jakarta Sans, Segoe UI, sans-serif",
            color="#0D2D44"
        ),
        title=dict(
            font=dict(
                size=20,
                color="#0D2D44"
            ),
            x=0.02,
            xanchor="left"
        ),
        margin=dict(
            l=30,
            r=30,
            t=70,
            b=40
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Plus Jakarta Sans, Segoe UI, sans-serif"
        ),
        legend=dict(
            title_font=dict(color="#0D2D44"),
            font=dict(color="#0D2D44")
        ),
        separators=",."
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor="#CDEFF7",
        tickfont=dict(color="#0D2D44"),
        title_font=dict(color="#0D2D44"),
        separatethousands=False
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(13,45,68,0.10)",
        linecolor="#CDEFF7",
        tickfont=dict(color="#0D2D44"),
        title_font=dict(color="#0D2D44"),
        tickformat=",.2~f",
        separatethousands=True
    )

    return fig


@st.cache_data
def load_geojson_regioni():
    """Carica il GeoJSON delle regioni dal repository."""

    import json

    percorso = Path("limits_IT_regions.geojson")

    if not percorso.exists():
        raise FileNotFoundError(
            "Manca limits_IT_regions.geojson nel repository."
        )

    with open(percorso, "r", encoding="utf-8") as file:
        return json.load(file)

# =====================================================


# =====================================================
# FUNZIONI
# =====================================================

@st.cache_data
def load_data():
    df_finale = pd.read_csv("df_finale_siae_sport.csv")
    kpi_regioni = pd.read_csv("kpi_regioni.csv")
    kpi_cards = pd.read_csv("kpi_cards_2021_completa.csv")
    tabella_macroaree = pd.read_csv("tabella_macroaree.csv")
    tabella_categorie_2021 = pd.read_csv("tabella_categorie_2021.csv")

    kpi_cards.columns = [c.lower().strip() for c in kpi_cards.columns]

    if "unita" not in kpi_cards.columns:
        kpi_cards["unita"] = ""

    return df_finale, kpi_regioni, kpi_cards, tabella_macroaree, tabella_categorie_2021


def format_value(value, unit=""):
    """
    Formatta i valori delle KPI card in stile italiano:
    - punto per le migliaia;
    - virgola per i decimali;
    - massimo due decimali;
    - simbolo euro e percentuale;
    - nessun decimale inutile per i valori interi.
    """

    if value is None:
        return "n.d."

    try:
        if pd.isna(value):
            return "n.d."
    except Exception:
        pass

    # Converte anche eventuali numeri salvati come testo
    try:
        if isinstance(value, str):
            valore_testo = value.strip()

            if valore_testo == "":
                return "n.d."

            valore_testo = (
                valore_testo
                .replace("€", "")
                .replace("%", "")
                .strip()
            )

            # Formato italiano: 175.574.380,99
            if "," in valore_testo:
                valore_testo = (
                    valore_testo
                    .replace(".", "")
                    .replace(",", ".")
                )

            value = float(valore_testo)

        else:
            value = float(value)

    except Exception:
        return str(value)

    unit_normalizzata = str(unit).strip().lower()

    # Numero intero oppure massimo due decimali
    if abs(value - round(value)) < 1e-9:
        valore_formattato = f"{int(round(value)):,}"
    else:
        valore_formattato = f"{value:,.2f}"

    # Trasformazione in formato italiano
    valore_formattato = (
        valore_formattato
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    # Indicatori economici
    if unit_normalizzata in [
        "euro",
        "€",
        "euro/evento",
        "euro per evento"
    ]:
        return f"{valore_formattato} €"

    # Indicatori percentuali
    if unit_normalizzata in [
        "%",
        "percentuale",
        "percent"
    ]:
        return f"{valore_formattato}%"

    return valore_formattato


def get_kpi_value(kpi_cards, kpi_name):
    row = kpi_cards[kpi_cards["kpi"] == kpi_name]
    if row.empty:
        return "n.d.", ""
    valore = row.iloc[0]["valore"]
    unita = row.iloc[0]["unita"]
    return valore, unita


def kpi_card(title, value, unit=""):
    """
    Mostra una KPI card uniforme senza far interpretare
    l'HTML come blocco di codice Markdown.
    """

    value_fmt = format_value(value, unit)
    lunghezza = len(str(value_fmt))

    if lunghezza >= 18:
        dimensione_valore = "23px"
    elif lunghezza >= 15:
        dimensione_valore = "26px"
    elif lunghezza >= 11:
        dimensione_valore = "29px"
    else:
        dimensione_valore = "34px"

    html_card = (
        f'<div class="sbl-kpi-card">'
        f'<div class="sbl-kpi-title">{title}</div>'
        f'<div class="sbl-kpi-value" '
        f'style="font-size:{dimensione_valore};">'
        f'{value_fmt}'
        f'</div>'
        f'</div>'
    )

    st.markdown(
        html_card,
        unsafe_allow_html=True
    )


def plot_horizontal_bar(df, x_col, y_col, title, x_label):
    df_plot = df[[x_col, y_col]].dropna().copy()
    df_plot = df_plot.sort_values(x_col, ascending=True)

    fig = px.bar(
        df_plot,
        x=x_col,
        y=y_col,
        orientation="h",
        title=title,
        labels={x_col: x_label, y_col: ""}
    , color_discrete_sequence=COLORI_AZIENDALI)

    fig.update_layout(
        height=650,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    fig = applica_layout_plotly(fig)
    st.plotly_chart(fig, use_container_width=True)


st.markdown(r"""

<style>

/* KPI CARD UNIFORMI */
.sbl-kpi-card {
    background: #ffffff;
    border: 1px solid #D7EDF3;
    border-radius: 17px;
    box-shadow: 0 7px 20px rgba(13, 45, 68, 0.10);

    height: 150px;
    min-height: 150px;
    max-height: 150px;

    padding: 24px 25px;
    margin-bottom: 12px;

    display: flex;
    flex-direction: column;
    justify-content: space-between;

    box-sizing: border-box;
    overflow: hidden;
}

.sbl-kpi-title {
    color: #495463;
    font-size: 16px;
    font-weight: 500;
    line-height: 1.35;

    min-height: 43px;
    max-height: 43px;

    display: flex;
    align-items: flex-start;

    overflow: hidden;
}

.sbl-kpi-value {
    color: #061A38;
    font-weight: 800;
    line-height: 1.05;

    white-space: nowrap;
    overflow: hidden;
    text-overflow: clip;

    letter-spacing: -0.5px;
}

/* Adattamento su schermi più stretti */
@media screen and (max-width: 1100px) {
    .sbl-kpi-card {
        padding: 20px;
    }

    .sbl-kpi-title {
        font-size: 15px;
    }
}

</style>

""", unsafe_allow_html=True)


# =====================================================
# CARICAMENTO DATI
# =====================================================

df_finale, kpi_regioni, kpi_cards, tabella_macroaree, tabella_categorie_2021 = load_data()


# =====================================================
# TITOLO
# =====================================================

st.markdown(f"<h1>{SBL_HEADER_LOGO} SIAE Sport Events Italy Dashboard</h1>", unsafe_allow_html=True)
st.markdown(
    """
    Dashboard interattiva per l'analisi degli eventi sportivi SIAE in Italia,
    con focus su distribuzione territoriale, trend temporali, KPI regionali,
    pandemia e dettaglio categorie sportive 2021.
    """
)


# =====================================================
# SIDEBAR
# =====================================================


# =====================================================
# SBL SIDEBAR BRAND - SOLO VISUALE
# =====================================================
if SBL_LOGO_SRC:
    st.sidebar.markdown(f"""
    <div class="sbl-sidebar-brand">
        <div class="sbl-sidebar-logo">
            <img src="{SBL_LOGO_SRC}" alt="SBL Consultancy logo">
        </div>
        <div class="sbl-sidebar-title">SIAE Sport</div>
        <div class="sbl-sidebar-sub">Eventi sportivi in Italia · 2004–2021</div>
    </div>
    <div class="sbl-sidebar-sep"></div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
    <div class="sbl-sidebar-brand">
        <div class="sbl-sidebar-title">SIAE Sport</div>
        <div class="sbl-sidebar-sub">Eventi sportivi in Italia · 2004–2021</div>
    </div>
    <div class="sbl-sidebar-sep"></div>
    """, unsafe_allow_html=True)
# =====================================================


pagina = st.sidebar.radio(
    "Seleziona sezione",
    [
        "Panoramica nazionale",
        "Trend temporali",
        "Ranking regioni",
        "Mappa Italia",
        "Focus categorie 2021",
        "Scheda singola regione",
        "Tabelle dati"
    ]
)


# =====================================================
# PAGINA 1 - PANORAMICA NAZIONALE
# =====================================================

if pagina == "Panoramica nazionale":

    st.header("Panoramica nazionale 2021")
    # =========================
    # NOTA METODOLOGICA
    # =========================

    with st.expander("📋 Nota metodologica", expanded=False):
        st.markdown("""
    La dashboard analizza l’evoluzione degli eventi sportivi in Italia nel periodo **2004-2021**, 
    con l’obiettivo di fornire una lettura sintetica e comparabile della distribuzione territoriale, 
    della partecipazione del pubblico e della dimensione economica del settore.

    Il dataset di riferimento raccoglie informazioni annuali sugli spettacoli sportivi, organizzate 
    per territorio e, dove disponibile, per categoria sportiva. L’analisi consente di osservare sia 
    l’andamento nazionale nel lungo periodo sia le differenze tra regioni e macroaree territoriali.

    ---

    ### Perimetro dell’analisi

    L’analisi prende in considerazione gli eventi sportivi registrati in Italia tra il **2004 e il 2021**.

    I dati sono letti su tre livelli territoriali:

    - **nazionale**, per osservare l’andamento complessivo del settore;
    - **macroterritoriale**, attraverso il confronto tra Nord-Ovest, Nord-Est, Centro, Sud e Isole;
    - **regionale**, per evidenziare differenze e specificità dei singoli territori.

    Il periodo analizzato include anche la forte discontinuità legata alla pandemia, particolarmente evidente tra il **2020 e il 2021**.

    ---

    ### Indicatori considerati

    La dashboard utilizza indicatori pensati per descrivere le principali dimensioni del fenomeno:

    - numero di spettacoli sportivi;
    - persone partecipanti;
    - persone medie per spettacolo;
    - quota regionale sul totale nazionale;
    - botteghino;
    - botteghino medio per spettacolo;
    - indicatori di resilienza.

    Per il **2021** è disponibile un livello di dettaglio maggiore sulle categorie sportive.

    ---

    ### Logica di lettura della dashboard

    La dashboard accompagna l’utente da una visione generale a una lettura più dettagliata: panoramica nazionale, trend temporali, ranking regionali, mappa Italia, focus categorie, scheda regionale e tabelle dati.

    ---

    ### Criteri di interpretazione

    L’analisi ha finalità **descrittiva e comparativa**. I risultati consentono di individuare tendenze, differenze territoriali e dinamiche di partecipazione, ma non devono essere interpretati come evidenza di relazioni causali dirette.

    Alcuni indicatori non sono disponibili con la stessa granularità per tutti gli anni. Per questo motivo, alcune visualizzazioni mostrano esclusivamente le informazioni effettivamente presenti nel dataset.

    La discontinuità del periodo pandemico rappresenta un elemento centrale dell’analisi.
    """)

    # =========================
    # FINE NOTA METODOLOGICA
    # =========================
    # =========================
    # NOTA METODOLOGICA
    # =========================



    # =========================
    # FINE NOTA METODOLOGICA
    # =========================
    # =========================
    # NOTA METODOLOGICA
    # =========================



    # =========================
    # FINE NOTA METODOLOGICA
    # =========================

    st.subheader("KPI principali")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        valore, unita = get_kpi_value(kpi_cards, "Totale spettacoli")
        kpi_card("Totale spettacoli", valore, unita)

    with col2:
        valore, unita = get_kpi_value(kpi_cards, "Totale persone")
        kpi_card("Totale persone", valore, unita)

    with col3:
        valore, unita = get_kpi_value(kpi_cards, "Totale botteghino")
        kpi_card("Totale botteghino", valore, unita)

    with col4:
        valore, unita = get_kpi_value(kpi_cards, "Totale pubblico")
        kpi_card("Totale pubblico", valore, unita)


    st.markdown("<br>", unsafe_allow_html=True)

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        valore, unita = get_kpi_value(kpi_cards, "Persone medie per spettacolo")
        kpi_card("Persone medie per spettacolo", valore, unita)

    with col6:
        valore, unita = get_kpi_value(kpi_cards, "Botteghino medio per spettacolo")
        kpi_card("Botteghino medio per spettacolo", valore, unita)

    with col7:
        valore, unita = get_kpi_value(kpi_cards, "Variazione YoY spettacoli 2021")
        kpi_card("YoY spettacoli 2021", valore, unita)

    with col8:
        valore, unita = get_kpi_value(kpi_cards, "Indice resilienza medio 2021")
        kpi_card("Indice resilienza medio 2021", valore, unita)


    st.markdown("---")
    st.subheader("KPI cards complete")
    st.dataframe(kpi_cards, use_container_width=True)


# =====================================================
# PAGINA 2 - TREND TEMPORALI
# =====================================================

elif pagina == "Trend temporali":

    st.header("Trend temporali")

    trend_nazionale = df_finale[
        (df_finale["livello_territoriale"] == "totale_nazionale") &
        (df_finale["categoria_sport"] == "Attività sportiva")
    ].copy()

    trend_nazionale = trend_nazionale.sort_values("anno")

    indicatore_trend = st.selectbox(
        "Seleziona indicatore nazionale",
        ["n_spettacoli", "persone"]
    )

    titolo = {
        "n_spettacoli": "Trend nazionale degli spettacoli sportivi",
        "persone": "Trend nazionale delle persone"
    }

    fig = px.line(
        trend_nazionale,
        x="anno",
        y=indicatore_trend,
        markers=True,
        title=titolo[indicatore_trend],
        labels={"anno": "Anno", indicatore_trend: indicatore_trend}
    , color_discrete_sequence=COLORI_AZIENDALI)

    fig.add_vline(x=2020, line_dash="dash")
    fig.add_vline(x=2021, line_dash="dash")

    fig = applica_layout_plotly(fig)
    st.plotly_chart(fig, use_container_width=True)


    st.subheader("Trend per macroarea")

    indicatore_macroarea = st.selectbox(
        "Seleziona indicatore macroarea",
        ["n_spettacoli", "persone"],
        key="indicatore_macroarea"
    )

    macro = tabella_macroaree.copy()
    macro = macro.sort_values(["territorio", "anno"])

    fig = px.line(
        macro,
        x="anno",
        y=indicatore_macroarea,
        color="territorio",
        markers=True,
        title=f"Trend {indicatore_macroarea} per macroarea",
        labels={"anno": "Anno", indicatore_macroarea: indicatore_macroarea, "territorio": "Macroarea"},
        color_discrete_map={
            "Nord-Ovest": "#00649C",
            "Nord-Est": "#27BBE8",
            "Centro": "#E85933",
            "Sud": "#E8AA05",
            "Isole": "#03789C"
        }
    )

    fig.add_vline(x=2020, line_dash="dash")
    fig.add_vline(x=2021, line_dash="dash")

    fig = applica_layout_plotly(fig)
    st.plotly_chart(fig, use_container_width=True)


# =====================================================
# PAGINA 3 - RANKING REGIONI
# =====================================================

elif pagina == "Ranking regioni":

    st.header("Ranking regioni")

    anni = sorted(kpi_regioni["anno"].unique())

    anno_scelto = st.selectbox(
        "Seleziona anno",
        anni,
        index=len(anni) - 1
    )

    kpi_anno = kpi_regioni[kpi_regioni["anno"] == anno_scelto].copy()

    indicatori_base = {
        "Numero spettacoli": "n_spettacoli",
        "Persone": "persone",
        "Persone medie per spettacolo": "persone_medie_per_spettacolo",
        "Quota spettacoli nazionale": "quota_spettacoli_nazionale",
        "Quota persone nazionale": "quota_persone_nazionale",
        "Variazione YoY spettacoli": "variazione_yoy_spettacoli",
        "Variazione YoY persone": "variazione_yoy_persone"
    }

    if anno_scelto == 2021:
        indicatori_base.update({
            "Botteghino": "botteghino",
            "Pubblico": "pubblico",
            "Botteghino medio per spettacolo": "botteghino_medio_per_spettacolo",
            "Pubblico medio per spettacolo": "pubblico_medio_per_spettacolo",
            "Quota botteghino nazionale": "quota_botteghino_nazionale",
            "Quota pubblico nazionale": "quota_pubblico_nazionale"
        })

    indicatore_nome = st.selectbox(
        "Seleziona indicatore",
        list(indicatori_base.keys())
    )

    indicatore_col = indicatori_base[indicatore_nome]

    plot_horizontal_bar(
        kpi_anno,
        indicatore_col,
        "territorio",
        f"{indicatore_nome} per regione - {anno_scelto}",
        indicatore_nome
    )

    st.subheader("Tabella ranking")

    tabella_ranking = kpi_anno[
        ["territorio", indicatore_col]
    ].sort_values(indicatore_col, ascending=False)

    st.dataframe(tabella_ranking.reset_index(drop=True), use_container_width=True)


# =====================================================
# PAGINA 4 - MAPPA ITALIA
# =====================================================

elif pagina == "Mappa Italia":

    st.header("Mappa Italia")

    anni = sorted(kpi_regioni["anno"].dropna().unique())

    anno_mappa = st.selectbox(
        "Seleziona anno",
        anni,
        index=len(anni) - 1,
        key="anno_mappa"
    )

    dati_mappa = kpi_regioni[kpi_regioni["anno"] == anno_mappa].copy()

    indicatori_mappa = {
        "Numero spettacoli": "n_spettacoli",
        "Persone": "persone",
        "Persone medie per spettacolo": "persone_medie_per_spettacolo",
        "Quota spettacoli nazionale": "quota_spettacoli_nazionale",
        "Quota persone nazionale": "quota_persone_nazionale"
    }

    if anno_mappa == 2021:
        indicatori_mappa.update({
            "Botteghino": "botteghino",
            "Pubblico": "pubblico",
            "Botteghino medio per spettacolo": "botteghino_medio_per_spettacolo"
        })

    indicatore_mappa_nome = st.selectbox(
        "Seleziona indicatore mappa",
        list(indicatori_mappa.keys()),
        key="indicatore_mappa"
    )

    indicatore_mappa = indicatori_mappa[indicatore_mappa_nome]

    if indicatore_mappa not in dati_mappa.columns:
        st.warning(f"L'indicatore '{indicatore_mappa_nome}' non è disponibile per l'anno selezionato.")
        st.stop()

    mappa_nomi_regioni = {
        "Piemonte": "Piemonte",
        "Valle d'Aosta": "Valle d'Aosta/Vallée d'Aoste",
        "Valle d’Aosta": "Valle d'Aosta/Vallée d'Aoste",
        "Lombardia": "Lombardia",
        "Liguria": "Liguria",
        "Trentino-Alto Adige": "Trentino-Alto Adige/Südtirol",
        "Trentino Alto Adige": "Trentino-Alto Adige/Südtirol",
        "Veneto": "Veneto",
        "Friuli- Venezia Giulia": "Friuli-Venezia Giulia",
        "Friuli Venezia Giulia": "Friuli-Venezia Giulia",
        "Friuli-Venezia Giulia": "Friuli-Venezia Giulia",
        "Emilia-Romagna": "Emilia-Romagna",
        "Toscana": "Toscana",
        "Umbria": "Umbria",
        "Marche": "Marche",
        "Lazio": "Lazio",
        "Abruzzo": "Abruzzo",
        "Molise": "Molise",
        "Campania": "Campania",
        "Puglia": "Puglia",
        "Basilicata": "Basilicata",
        "Calabria": "Calabria",
        "Sicilia": "Sicilia",
        "Sardegna": "Sardegna"
    }

    # Mantiene il nome originale se non serve conversione
    dati_mappa["regione_geojson"] = dati_mappa["territorio"].replace(mappa_nomi_regioni)

    try:
        geojson_regioni = load_geojson_regioni()

        dati_mappa_plot = dati_mappa.dropna(
            subset=["regione_geojson", indicatore_mappa]
        ).copy()

        if dati_mappa_plot.empty:
            st.warning("Non ci sono dati disponibili per costruire la mappa.")
            st.stop()

        # Scala più equilibrata: evita che una regione estrema renda tutte le altre quasi bianche.
        valore_min = dati_mappa_plot[indicatore_mappa].min()
        valore_max = dati_mappa_plot[indicatore_mappa].quantile(0.95)

        if pd.isna(valore_min) or pd.isna(valore_max):
            st.warning("Valori non disponibili per l'indicatore selezionato.")
            st.stop()

        if valore_min == valore_max:
            valore_max = dati_mappa_plot[indicatore_mappa].max()
            if valore_min == valore_max:
                valore_max = valore_min + 1

        formato_hover = "%{z:,.2f}"
        formato_hover_data = ":,.2f"

        if indicatore_mappa in ["n_spettacoli", "persone", "botteghino", "pubblico"]:
            formato_hover = "%{z:,.0f}"
            formato_hover_data = ":,.0f"

        hover_data_map = {
            indicatore_mappa: formato_hover_data,
            "regione_geojson": False
        }

        if "n_spettacoli" in dati_mappa_plot.columns:
            hover_data_map["n_spettacoli"] = ":,.0f"

        if "persone" in dati_mappa_plot.columns:
            hover_data_map["persone"] = ":,.0f"

        fig = px.choropleth(
            dati_mappa_plot,
            geojson=geojson_regioni,
            locations="regione_geojson",
            featureidkey="properties.reg_name",
            color=indicatore_mappa,
            hover_name="territorio",
            hover_data=hover_data_map,
            color_continuous_scale=[
                "#EAF9FD",
                "#B7F1FA",
                "#39BDE8",
                "#00649C",
                "#0D2D44"
            ],
            range_color=(valore_min, valore_max)
        )

        fig.update_geos(
            fitbounds="locations",
            visible=False,
            projection_type="mercator",
            showcountries=False,
            showcoastlines=False,
            showland=False,
            showframe=False
        )

        fig.update_traces(
            marker_line_color="#5F6B73",
            marker_line_width=0.8,
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                + indicatore_mappa_nome
                + ": "
                + formato_hover
                + "<extra></extra>"
            )
        )

        fig.update_layout(
            title=None,
            height=650,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="Plus Jakarta Sans, Segoe UI, sans-serif",
                color="#0D2D44"
            ),
            coloraxis_colorbar=dict(
                title=dict(text=indicatore_mappa_nome, font=dict(size=12, color="#0D2D44")),
                thickness=14,
                len=0.75,
                x=1.02,
                tickfont=dict(size=11, color="#0D2D44")
            )
        )

        st.markdown("<div class='sbl-map-spacer'></div>", unsafe_allow_html=True)
        fig = applica_layout_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)

    except FileNotFoundError as e:
        st.error("Il file geografico della mappa non è presente.")
        st.code(str(e))

    except Exception as e:
        st.error("Errore durante la costruzione della mappa.")
        st.exception(e)
elif pagina == "Focus categorie 2021":

    st.header("Focus categorie sportive 2021")

    livello_focus = st.selectbox(
        "Seleziona livello territoriale",
        ["totale_nazionale", "regione"]
    )

    if livello_focus == "totale_nazionale":
        territorio_focus = "Totale complessivo"
    else:
        regioni = sorted(
            tabella_categorie_2021[
                tabella_categorie_2021["livello_territoriale"] == "regione"
            ]["territorio"].unique()
        )

        territorio_focus = st.selectbox(
            "Seleziona regione",
            regioni
        )

    categorie_focus = tabella_categorie_2021[
        (tabella_categorie_2021["territorio"] == territorio_focus) &
        (tabella_categorie_2021["categoria_sport"] != "Attività sportiva")
    ].copy()

    col1, col2 = st.columns(2)

    with col1:
        plot_horizontal_bar(
            categorie_focus,
            "n_spettacoli",
            "categoria_sport",
            f"Spettacoli per categoria - {territorio_focus} 2021",
            "Numero spettacoli"
        )

    with col2:
        plot_horizontal_bar(
            categorie_focus,
            "persone",
            "categoria_sport",
            f"Persone per categoria - {territorio_focus} 2021",
            "Persone"
        )

    st.subheader("Tabella categorie sportive 2021")
    st.dataframe(categorie_focus.reset_index(drop=True), use_container_width=True)


# =====================================================
# PAGINA 6 - SCHEDA SINGOLA REGIONE
# =====================================================

elif pagina == "Scheda singola regione":

    st.header("Scheda singola regione")

    regioni = sorted(kpi_regioni["territorio"].unique())

    regione_scelta = st.selectbox(
        "Seleziona regione",
        regioni
    )

    dati_regione = kpi_regioni[
        kpi_regioni["territorio"] == regione_scelta
    ].copy()

    dati_regione = dati_regione.sort_values("anno")

    anni = sorted(dati_regione["anno"].unique())

    anno_regione = st.selectbox(
        "Seleziona anno",
        anni,
        index=len(anni) - 1
    )

    riga = dati_regione[dati_regione["anno"] == anno_regione].iloc[0]

    st.subheader(f"KPI principali - {regione_scelta} ({anno_regione})")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        kpi_card("Spettacoli", riga["n_spettacoli"], "eventi")

    with col2:
        kpi_card("Persone", riga["persone"], "persone")

    with col3:
        kpi_card("Persone medie/spettacolo", riga["persone_medie_per_spettacolo"], "persone/evento")

    with col4:
        kpi_card("Quota spettacoli nazionale", riga["quota_spettacoli_nazionale"], "%")


    st.markdown("<br>", unsafe_allow_html=True)

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        kpi_card("YoY spettacoli", riga["variazione_yoy_spettacoli"], "%")

    with col6:
        kpi_card("YoY persone", riga["variazione_yoy_persone"], "%")

    with col7:
        kpi_card("Quota persone nazionale", riga["quota_persone_nazionale"], "%")

    with col8:
        kpi_card("Resilienza 2021", riga["indice_resilienza_spettacoli_2021"], "%")


    st.subheader("Serie storiche regione")

    indicatore_regione = st.selectbox(
        "Seleziona indicatore serie storica",
        [
            "n_spettacoli",
            "persone",
            "persone_medie_per_spettacolo",
            "quota_spettacoli_nazionale",
            "quota_persone_nazionale"
        ]
    )

    fig = px.line(
        dati_regione,
        x="anno",
        y=indicatore_regione,
        markers=True,
        title=f"{indicatore_regione} - {regione_scelta}",
        labels={"anno": "Anno", indicatore_regione: indicatore_regione}
    , color_discrete_sequence=COLORI_AZIENDALI)

    fig.add_vline(x=2020, line_dash="dash")
    fig.add_vline(x=2021, line_dash="dash")

    fig = applica_layout_plotly(fig)
    st.plotly_chart(fig, use_container_width=True)


    st.subheader(f"Focus categorie sportive 2021 - {regione_scelta}")

    categorie_regione = tabella_categorie_2021[
        (tabella_categorie_2021["territorio"] == regione_scelta) &
        (tabella_categorie_2021["categoria_sport"] != "Attività sportiva")
    ].copy()

    if len(categorie_regione) > 0:
        plot_horizontal_bar(
            categorie_regione,
            "n_spettacoli",
            "categoria_sport",
            f"Spettacoli per categoria - {regione_scelta} 2021",
            "Numero spettacoli"
        )

        st.dataframe(categorie_regione.reset_index(drop=True), use_container_width=True)
    else:
        st.info("Categorie sportive non disponibili per questa regione.")


    st.subheader("Tabella storica completa regione")
    st.dataframe(dati_regione.reset_index(drop=True), use_container_width=True)


# =====================================================
# PAGINA 7 - TABELLE DATI
# =====================================================

elif pagina == "Tabelle dati":

    st.header("Tabelle dati")

    tabella_scelta = st.selectbox(
        "Seleziona tabella",
        [
            "Dataset finale",
            "KPI regioni",
            "KPI cards 2021",
            "Macroaree",
            "Categorie 2021"
        ]
    )

    if tabella_scelta == "Dataset finale":
        st.dataframe(df_finale, use_container_width=True)

    elif tabella_scelta == "KPI regioni":
        st.dataframe(kpi_regioni, use_container_width=True)

    elif tabella_scelta == "KPI cards 2021":
        st.dataframe(kpi_cards, use_container_width=True)

    elif tabella_scelta == "Macroaree":
        st.dataframe(tabella_macroaree, use_container_width=True)

    elif tabella_scelta == "Categorie 2021":
        st.dataframe(tabella_categorie_2021, use_container_width=True)