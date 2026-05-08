import base64
import html
import mimetypes
import re
from urllib.parse import unquote

import pandas as pd
import streamlit as st

from datetime import datetime
from pathlib import Path
from supabase import create_client


st.set_page_config(
    page_title="Minha coleção de minis",
    page_icon="🚗",
    layout="wide"
)

if "mini_detalhe_id" not in st.session_state:
    st.session_state.mini_detalhe_id = None

if "ml_feedback" not in st.session_state:
    st.session_state.ml_feedback = None


def abrir_detalhe(id_mini):
    """Abre a tela de detalhe de forma mais estável no Streamlit."""
    try:
        st.session_state["mini_detalhe_id"] = int(id_mini)
    except Exception:
        st.session_state["mini_detalhe_id"] = id_mini


def voltar_colecao():
    st.session_state["mini_detalhe_id"] = None


BASE_DIR = Path(__file__).parent
FOTOS_DIR = BASE_DIR / "fotos"
FOTOS_DIR.mkdir(exist_ok=True)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
SUPABASE_BUCKET = st.secrets["SUPABASE_BUCKET"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(56,189,248,0.15), transparent 35%),
            radial-gradient(circle at top right, rgba(168,85,247,0.12), transparent 35%),
            linear-gradient(180deg, #020617 0%, #0E1117 55%, #020617 100%);
        color: #FFFFFF;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617, #111827);
        border-right: 1px solid #1E293B;
    }

    h1 { font-size: 42px !important; font-weight: 900 !important; letter-spacing: -1px; }
    h2, h3 { color: #FFFFFF; font-weight: 800 !important; }

    .hero-box {
        background:
            linear-gradient(135deg, rgba(15,23,42,0.95), rgba(30,41,59,0.90)),
            radial-gradient(circle at top right, rgba(56,189,248,0.20), transparent 35%);
        border: 1px solid #334155;
        border-radius: 28px;
        padding: 28px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.45);
        margin-bottom: 22px;
    }

    .hero-title {
        font-size: 38px;
        font-weight: 900;
        color: #FFFFFF;
        margin-bottom: 6px;
    }

    .hero-subtitle { color: #CBD5E1; font-size: 17px; }

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(30,41,59,0.98), rgba(2,6,23,0.98));
        border: 1px solid #334155;
        border-radius: 22px;
        padding: 18px;
        box-shadow: 0 12px 35px rgba(0,0,0,0.35);
    }

    div[data-testid="stMetric"] label {
        color: #94A3B8 !important;
        font-weight: 700;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-weight: 900;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(145deg, rgba(30,41,59,0.96), rgba(2,6,23,0.98));
        border-radius: 24px;
        border: 1px solid #334155;
        padding: 16px;
        box-shadow: 0 16px 45px rgba(0,0,0,0.42);
        transition: all 0.25s ease;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-4px);
        border-color: #38BDF8;
        box-shadow: 0 22px 55px rgba(56,189,248,0.12);
    }

    .mini-title {
        font-size: 19px;
        font-weight: 900;
        color: #FFFFFF;
        min-height: 54px;
        margin-top: 10px;
        margin-bottom: 8px;
        line-height: 1.25;
    }

    .mini-info {
        font-size: 14px;
        color: #CBD5E1;
        margin-bottom: 6px;
    }

    .mini-value {
        font-size: 17px;
        font-weight: 900;
        color: #38BDF8;
        margin-top: 10px;
    }

    .badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 900;
        margin-top: 10px;
        margin-bottom: 6px;
        letter-spacing: .3px;
    }

    .badge-comum { background: rgba(148,163,184,0.15); color: #CBD5E1; border: 1px solid #64748B; }
    .badge-th { background: rgba(34,197,94,0.15); color: #86EFAC; border: 1px solid #22C55E; }
    .badge-sth { background: rgba(250,204,21,0.18); color: #FACC15; border: 1px solid #FACC15; }
    .badge-rlc { background: rgba(239,68,68,0.16); color: #FCA5A5; border: 1px solid #EF4444; }
    .badge-chase { background: rgba(168,85,247,0.18); color: #D8B4FE; border: 1px solid #A855F7; }
    .badge-premium { background: rgba(56,189,248,0.16); color: #7DD3FC; border: 1px solid #38BDF8; }
    .badge-especial { background: rgba(244,114,182,0.17); color: #F9A8D4; border: 1px solid #F472B6; }

    .empty-photo {
        height: 300px;
        border-radius: 18px;
        border: 1px dashed #475569;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #94A3B8;
        background: #020617;
        font-weight: 800;
    }

    .detail-box {
        background: linear-gradient(145deg, rgba(15,23,42,0.98), rgba(2,6,23,0.98));
        border: 1px solid #334155;
        border-radius: 28px;
        padding: 24px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.48);
        margin-top: 20px;
        margin-bottom: 20px;
    }

    .detail-title {
        font-size: 32px;
        font-weight: 900;
        color: #FFFFFF;
        margin-bottom: 6px;
    }

    .detail-subtitle {
        color: #CBD5E1;
        font-size: 16px;
        margin-bottom: 16px;
    }

    .gain-positive { color: #86EFAC; font-weight: 900; }
    .gain-negative { color: #FCA5A5; font-weight: 900; }
    .gain-neutral { color: #CBD5E1; font-weight: 900; }

    .footer-card {
        margin-top: 8px;
        padding-top: 10px;
        border-top: 1px solid #334155;
    }

    .ml-status-ok {
        background: rgba(34,197,94,0.12);
        color: #86EFAC;
        border: 1px solid rgba(34,197,94,0.45);
        border-radius: 14px;
        padding: 10px 12px;
        font-weight: 800;
        margin-top: 10px;
    }

    .ml-status-erro {
        background: rgba(250,204,21,0.12);
        color: #FDE68A;
        border: 1px solid rgba(250,204,21,0.45);
        border-radius: 14px;
        padding: 10px 12px;
        font-weight: 800;
        margin-top: 10px;
    }

    .stButton button {
        border-radius: 14px;
        font-weight: 800;
        border: 1px solid #38BDF8;
        background: linear-gradient(135deg, #0284C7, #2563EB);
        color: white;
    }

    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] {
        border-radius: 14px;
    }


    .dash-card {
        background: linear-gradient(145deg, rgba(15,23,42,0.98), rgba(2,6,23,0.98));
        border: 1px solid #334155;
        border-radius: 24px;
        padding: 18px;
        box-shadow: 0 16px 45px rgba(0,0,0,0.35);
        margin-bottom: 18px;
    }

    .dash-title {
        font-size: 22px;
        font-weight: 900;
        color: #FFFFFF;
        margin-bottom: 14px;
    }

    .dash-row { margin: 12px 0 16px 0; }

    .dash-row-top {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: center;
        margin-bottom: 6px;
        color: #E2E8F0;
        font-size: 14px;
        font-weight: 800;
    }

    .dash-label {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .dash-value {
        color: #38BDF8;
        white-space: nowrap;
        font-weight: 900;
    }

    .dash-bar-bg {
        height: 14px;
        background: rgba(15,23,42,0.95);
        border: 1px solid rgba(51,65,85,0.95);
        border-radius: 999px;
        overflow: hidden;
    }

    .dash-bar-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #0284C7, #38BDF8);
        box-shadow: 0 0 14px rgba(56,189,248,0.45);
    }

    .dash-table-wrap { overflow-x: auto; }

    .dash-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0 8px;
        min-width: 720px;
    }

    .dash-table th {
        color: #94A3B8;
        font-size: 12px;
        text-align: left;
        padding: 6px 8px;
    }

    .dash-table td {
        background: rgba(15,23,42,0.72);
        border-top: 1px solid #334155;
        border-bottom: 1px solid #334155;
        color: #E2E8F0;
        padding: 10px 8px;
        font-size: 13px;
        font-weight: 700;
    }

    .dash-table td:first-child {
        border-left: 1px solid #334155;
        border-radius: 14px 0 0 14px;
    }

    .dash-table td:last-child {
        border-right: 1px solid #334155;
        border-radius: 0 14px 14px 0;
    }


    /* ================= CARDS / FOTOS PADRONIZADAS ================= */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.mini-card-anchor) {
        min-height: 705px;
    }

    .carousel-frame {
        width: 100%;
        height: var(--carousel-height);
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid #334155;
        background:
            radial-gradient(circle at top, rgba(56,189,248,0.10), transparent 42%),
            #020617;
        display: flex;
        align-items: center;
        justify-content: center;
        box-sizing: border-box;
    }

    .carousel-frame img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
        background: #FFFFFF;
        border-radius: 14px;
    }

    .carousel-dots {
        text-align: center;
        color: #38BDF8;
        font-size: 18px;
        font-weight: 900;
        line-height: 1.2;
        min-height: 34px;
    }

    .carousel-count {
        font-size: 12px;
        color: #CBD5E1;
        font-weight: 800;
    }




    .elite-chip {
        display: inline-block;
        margin-top: 4px;
        margin-bottom: 10px;
        padding: 5px 11px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 900;
        color: #E0F2FE;
        background: linear-gradient(135deg, rgba(14,165,233,0.22), rgba(168,85,247,0.18));
        border: 1px solid rgba(56,189,248,0.45);
        letter-spacing: .35px;
        box-shadow: 0 0 18px rgba(56,189,248,0.10);
    }

    .elite-chip-elite { color: #FDE68A; border-color: rgba(250,204,21,0.70); background: rgba(250,204,21,0.12); }
    .elite-chip-hype { color: #F9A8D4; border-color: rgba(244,114,182,0.70); background: rgba(244,114,182,0.12); }
    .elite-chip-jdm { color: #93C5FD; border-color: rgba(59,130,246,0.70); background: rgba(59,130,246,0.12); }
    .elite-chip-street { color: #CBD5E1; border-color: rgba(148,163,184,0.45); background: rgba(148,163,184,0.10); }

    /* ================= EDITOR NO CARD ================= */
    div[data-testid="stExpander"] {
        border: 1px solid rgba(56,189,248,0.28) !important;
        border-radius: 16px !important;
        background: rgba(15,23,42,0.58) !important;
    }

    div[data-testid="stExpander"] summary {
        font-weight: 900 !important;
        color: #E2E8F0 !important;
    }

    /* ================= MOBILE PREMIUM ================= */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 1.2rem !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            max-width: 100% !important;
        }

        .hero-box {
            padding: 18px !important;
            border-radius: 22px !important;
            margin-bottom: 14px !important;
        }

        .hero-title {
            font-size: 27px !important;
            line-height: 1.12 !important;
        }

        .hero-subtitle {
            font-size: 14px !important;
            line-height: 1.35 !important;
        }

        h1 { font-size: 28px !important; }
        h2 { font-size: 23px !important; }
        h3 { font-size: 20px !important; }

        div[data-testid="stMetric"] {
            padding: 14px !important;
            border-radius: 18px !important;
            margin-bottom: 8px !important;
        }

        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 12px !important;
            border-radius: 20px !important;
            margin-bottom: 16px !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.mini-card-anchor) {
            min-height: auto !important;
        }

        .carousel-frame {
            height: 280px !important;
        }

        .mini-title {
            font-size: 18px !important;
            min-height: auto !important;
        }

        .detail-box {
            padding: 14px !important;
            border-radius: 22px !important;
        }

        .detail-title {
            font-size: 25px !important;
            line-height: 1.15 !important;
        }

        .detail-subtitle {
            font-size: 14px !important;
        }

        .empty-photo {
            height: 280px !important;
        }

        .stButton button,
        div[data-testid="stLinkButton"] a {
            min-height: 44px !important;
            font-size: 15px !important;
        }
    }

</style>
""", unsafe_allow_html=True)


# =========================================================
# FUNÇÕES BÁSICAS
# =========================================================

def criar_banco():
    # Banco agora é Supabase. Mantido para não quebrar o fluxo antigo.
    pass


def normalizar_texto(valor):
    return str(valor or "").strip()


def dinheiro(valor):
    try:
        return f"R$ {float(valor or 0):.2f}"
    except Exception:
        return "R$ 0.00"


# =========================================================
# LINK / PREÇO MANUAL
# =========================================================

def extrair_mlb_do_link(link):
    """Extrai o ID MLB do link apenas para limpar/salvar o link quando possível."""
    if not link:
        return None

    texto = unquote(str(link)).upper()

    item_param = re.findall(r"ITEM_ID[:=](MLB-?\d{6,})", texto)
    if item_param:
        return item_param[-1].replace("-", "")

    encontrados = re.findall(r"(?<!U)(MLB-?\d{6,})", texto)
    if encontrados:
        return encontrados[-1].replace("-", "")

    return None


def normalizar_link_ml(link):
    """Mantém um link limpo do Mercado Livre quando houver MLB; caso contrário salva o link informado."""
    item_id = extrair_mlb_do_link(link)
    if item_id:
        return f"https://produto.mercadolivre.com.br/{item_id}"
    return normalizar_texto(link)


# =========================================================
# SUPABASE / CRUD
# =========================================================

def salvar(nome, marca, serie, raridade, status, valor_pago, foto, link_compra="", preco_atual=0, observacoes=""):
    try:
        link_compra = normalizar_texto(link_compra)
        link_salvar = normalizar_link_ml(link_compra) if link_compra else ""

        resposta = supabase.table("minis").insert({
            "nome": normalizar_texto(nome),
            "marca": normalizar_texto(marca),
            "serie": normalizar_texto(serie),
            "raridade": normalizar_texto(raridade),
            "status": normalizar_texto(status),
            "valor_pago": float(valor_pago or 0),
            "foto": foto or "",
            "favorito": False,
            "link_compra": link_salvar,
            "preco_atual": float(preco_atual or 0),
            "observacoes": normalizar_texto(observacoes),
            "atualizado_em": datetime.now().isoformat()
        }).execute()

        if resposta.data and resposta.data[0].get("id"):
            registrar_historico_valor(resposta.data[0]["id"], valor_pago, preco_atual)
    except Exception as e:
        st.error(f"Erro ao salvar mini no Supabase: {e}")


def atualizar_foto(id_mini, novas_fotos):
    try:
        resposta = supabase.table("minis").select("foto").eq("id", id_mini).execute()

        fotos_atuais = ""
        if resposta.data and resposta.data[0].get("foto"):
            fotos_atuais = resposta.data[0]["foto"]

        fotos_final = fotos_atuais + ";" + novas_fotos if fotos_atuais else novas_fotos

        supabase.table("minis").update({
            "foto": fotos_final,
            "atualizado_em": datetime.now().isoformat()
        }).eq("id", id_mini).execute()

    except Exception as e:
        st.error(f"Erro ao atualizar fotos no Supabase: {e}")


def alternar_favorito(id_mini, favorito_atual):
    try:
        supabase.table("minis").update({
            "favorito": not bool(favorito_atual),
            "atualizado_em": datetime.now().isoformat()
        }).eq("id", id_mini).execute()
    except Exception as e:
        st.error(f"Erro ao atualizar favorito: {e}")


def atualizar_dados_extra(id_mini, valor_pago, link_compra, preco_atual, observacoes):
    try:
        link_compra = normalizar_texto(link_compra)
        link_salvar = normalizar_link_ml(link_compra) if link_compra else ""

        supabase.table("minis").update({
            "valor_pago": float(valor_pago or 0),
            "link_compra": link_salvar,
            "preco_atual": float(preco_atual or 0),
            "observacoes": normalizar_texto(observacoes),
            "atualizado_em": datetime.now().isoformat()
        }).eq("id", id_mini).execute()

        registrar_historico_valor(id_mini, valor_pago, preco_atual)
    except Exception as e:
        st.error(f"Erro ao atualizar dados extras: {e}")





def atualizar_mini_completo(
    id_mini,
    nome,
    marca,
    serie,
    raridade,
    status,
    valor_pago,
    link_compra,
    preco_atual,
    observacoes
):
    try:
        link_compra = normalizar_texto(link_compra)
        link_salvar = normalizar_link_ml(link_compra) if link_compra else ""

        supabase.table("minis").update({
            "nome": normalizar_texto(nome),
            "marca": normalizar_texto(marca),
            "serie": normalizar_texto(serie),
            "raridade": normalizar_texto(raridade),
            "status": normalizar_texto(status),
            "valor_pago": float(valor_pago or 0),
            "link_compra": link_salvar,
            "preco_atual": float(preco_atual or 0),
            "observacoes": normalizar_texto(observacoes),
            "atualizado_em": datetime.now().isoformat()
        }).eq("id", id_mini).execute()

        registrar_historico_valor(id_mini, valor_pago, preco_atual)

    except Exception as e:
        st.error(f"Erro ao atualizar mini: {e}")

def registrar_historico_valor(id_mini, valor_pago, preco_atual):
    """
    Registra automaticamente um ponto de histórico.
    Se a tabela historico_valores ainda não existir, o app não quebra.
    """
    try:
        valor_pago_float = float(valor_pago or 0)
        preco_atual_float = float(preco_atual or 0)

        supabase.table("historico_valores").insert({
            "mini_id": id_mini,
            "valor_pago": valor_pago_float,
            "preco_atual": preco_atual_float,
            "valorizacao": preco_atual_float - valor_pago_float
        }).execute()
    except Exception:
        # Mantém o app funcionando mesmo se a tabela ainda não tiver sido criada.
        pass


def obter_historico_valores(id_mini):
    try:
        resposta = (
            supabase.table("historico_valores")
            .select("*")
            .eq("mini_id", id_mini)
            .order("criado_em", desc=False)
            .execute()
        )
        return resposta.data or []
    except Exception:
        return []


def exibir_grafico_historico(id_mini):
    historico = obter_historico_valores(id_mini)

    if not historico:
        st.info("Ainda não há histórico de valores para essa mini. Ao salvar alterações de preço, o histórico começa a ser criado automaticamente.")
        return

    df_hist = pd.DataFrame(historico)

    if df_hist.empty or "criado_em" not in df_hist.columns:
        st.info("Histórico ainda sem dados suficientes para gráfico.")
        return

    df_hist["criado_em"] = pd.to_datetime(df_hist["criado_em"], errors="coerce")
    df_hist = df_hist.dropna(subset=["criado_em"]).sort_values("criado_em")

    for col in ["valor_pago", "preco_atual", "valorizacao"]:
        if col in df_hist.columns:
            df_hist[col] = pd.to_numeric(df_hist[col], errors="coerce").fillna(0)

    if df_hist.empty:
        st.info("Histórico ainda sem dados suficientes para gráfico.")
        return

    grafico = df_hist.set_index("criado_em")[["preco_atual", "valorizacao"]]
    st.line_chart(grafico, use_container_width=True)

    ultimo = df_hist.iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("Último valor pago", dinheiro(ultimo.get("valor_pago", 0)))
    c2.metric("Último preço atual", dinheiro(ultimo.get("preco_atual", 0)))
    c3.metric("Última valorização", dinheiro(ultimo.get("valorizacao", 0)))


def listar():
    try:
        resposta = supabase.table("minis").select("*").order("id", desc=True).execute()

        dados = []
        for m in resposta.data or []:
            dados.append((
                m.get("id"),
                m.get("nome", ""),
                m.get("marca", ""),
                m.get("serie", ""),
                m.get("raridade", ""),
                m.get("status", ""),
                float(m.get("valor_pago") or 0),
                m.get("foto", ""),
                bool(m.get("favorito") or False),
                m.get("link_compra", ""),
                float(m.get("preco_atual") or 0),
                m.get("observacoes", ""),
                m.get("atualizado_em", "")
            ))

        return dados

    except Exception as e:
        st.error(f"Erro ao listar minis do Supabase: {e}")
        return []


def buscar_mini_por_id(id_mini):
    minis = listar()
    for mini in minis:
        if mini[0] == id_mini:
            return mini
    return None


# =========================================================
# FOTOS / CARROSSEL
# =========================================================

def limpar_nome_arquivo(nome):
    proibidos = ['"', "'", "’", "´", "`", "(", ")", "[", "]", "{", "}", "#", "%", "&", "?", "!", ":", ";", ","]

    nome = normalizar_texto(nome)

    for c in proibidos:
        nome = nome.replace(c, "")

    trocas = {
        " ": "_", "ç": "c", "Ç": "C", "ã": "a", "Ã": "A",
        "á": "a", "Á": "A", "é": "e", "É": "E",
        "í": "i", "Í": "I", "ó": "o", "Ó": "O",
        "ú": "u", "Ú": "U", "â": "a", "ê": "e",
        "ô": "o"
    }

    for antigo, novo in trocas.items():
        nome = nome.replace(antigo, novo)

    return nome


def upload_foto_supabase(foto, prefixo="mini"):
    nome_limpo = limpar_nome_arquivo(foto.name)
    nome_arquivo = f"{prefixo}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{nome_limpo}"

    try:
        supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=nome_arquivo,
            file=foto.getvalue(),
            file_options={
                "content-type": foto.type,
                "upsert": "true"
            }
        )

        return supabase.storage.from_(SUPABASE_BUCKET).get_public_url(nome_arquivo)

    except Exception as e:
        st.error(f"Erro ao enviar foto para o Supabase: {e}")
        return None


def resolver_caminho_foto(caminho_salvo):
    if not caminho_salvo:
        return None

    caminho_salvo = caminho_salvo.strip()

    if caminho_salvo.startswith("http://") or caminho_salvo.startswith("https://"):
        return caminho_salvo

    caminho = Path(caminho_salvo)
    if caminho.exists():
        return str(caminho)

    caminho_relativo = BASE_DIR / caminho_salvo
    if caminho_relativo.exists():
        return str(caminho_relativo)

    caminho_fotos = FOTOS_DIR / Path(caminho_salvo).name
    if caminho_fotos.exists():
        return str(caminho_fotos)

    return None


def lista_fotos_validas(fotos):
    if not fotos:
        return []

    fotos_validas = []

    for item in fotos.split(";"):
        caminho_resolvido = resolver_caminho_foto(item)
        if caminho_resolvido:
            fotos_validas.append(caminho_resolvido)

    return fotos_validas


def imagem_para_src(caminho):
    if caminho.startswith("http://") or caminho.startswith("https://"):
        return caminho

    try:
        mime = mimetypes.guess_type(caminho)[0] or "image/png"
        with open(caminho, "rb") as f:
            dados = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{dados}"
    except Exception:
        return ""


def classe_badge(raridade):
    r = normalizar_texto(raridade).lower()

    if r == "th":
        return "badge-th"
    if r == "sth":
        return "badge-sth"
    if r == "rlc":
        return "badge-rlc"
    if r == "chase":
        return "badge-chase"
    if r == "premium":
        return "badge-premium"
    if r == "especial":
        return "badge-especial"

    return "badge-comum"


# =========================================================
# SCORE / ELITE SYSTEM
# =========================================================

def calcular_score_mini(nome, marca, serie, raridade):
    score = 0
    texto = f"{nome} {marca} {serie} {raridade}".lower()

    # Raridades reais / fortes
    if "sth" in texto or "super treasure" in texto:
        score += 70
    if "chase" in texto:
        score += 60
    if "rlc" in texto or "red line club" in texto:
        score += 50
    if "premium" in texto:
        score += 15
    if "especial" in texto:
        score += 10
    if texto.strip().endswith("th") or " treasure hunt" in texto:
        score += 25

    # Modelos e temas fortes de coleção
    if "ferrari" in texto:
        score += 30
    if "f40" in texto:
        score += 22
    if "skyline" in texto or "gt-r" in texto or "gtr" in texto:
        score += 25
    if "lbwk" in texto or "liberty walk" in texto:
        score += 20
    if "pagani" in texto:
        score += 18
    if "lancer" in texto or "evolution" in texto or "evo" in texto:
        score += 16
    if "fairlady" in texto or "nissan" in texto:
        score += 14
    if "porsche" in texto:
        score += 12
    if "batmobile" in texto:
        score += 14
    if "vw" in texto or "volkswagen" in texto or "id. buzz" in texto:
        score += 10
    if "mustang" in texto or "camaro" in texto or "chevy" in texto or "challenger" in texto:
        score += 8

    return int(score)


def categoria_elite(score):
    if score >= 70:
        return "💎 ELITE"
    if score >= 45:
        return "🔥 HYPE"
    if score >= 25:
        return "🏁 JDM"
    return "🚗 STREET"


def classe_elite_chip(score):
    if score >= 70:
        return "elite-chip-elite"
    if score >= 45:
        return "elite-chip-hype"
    if score >= 25:
        return "elite-chip-jdm"
    return "elite-chip-street"


def render_elite_chip(nome, marca, serie, raridade):
    score = calcular_score_mini(nome, marca, serie, raridade)
    categoria = categoria_elite(score)
    css = classe_elite_chip(score)

    # =========================
    # RARIDADE AUTOMÁTICA VISUAL
    # =========================
    # Importante: isso NÃO altera a raridade oficial gravada no Supabase.
    # TH / STH / RLC / Chase continuam sendo raridades reais e manuais.
    raridade_auto = "🚗 Comum"

    if score >= 70:
        raridade_auto = "🏆 Lendária"
    elif score >= 51:
        raridade_auto = "💎 Elite"
    elif score >= 31:
        raridade_auto = "🔥 Premium"
    elif score >= 16:
        raridade_auto = "⭐ Especial"

    st.markdown(
        f'''        <div class="elite-chip {css}">
            {categoria} • SCORE {score}
        </div>

        <div style="
            margin-top:-2px;
            margin-bottom:12px;
            font-size:13px;
            font-weight:800;
            color:#CBD5E1;
        ">
            🎖️ Auto Rank: {raridade_auto}
        </div>
        ''',
        unsafe_allow_html=True
    )
    return score, categoria


def render_bar_list(titulo, serie, formato="dinheiro"):
    """Renderiza ranking com barras em HTML, mais limpo que st.bar_chart para poucos dados."""
    if serie is None or len(serie) == 0:
        st.info("Sem dados suficientes para exibir este bloco.")
        return

    try:
        serie = serie.fillna(0)
    except Exception:
        pass

    valores = [float(v or 0) for v in serie.values]
    max_valor = max(valores) if valores else 0
    itens = []

    for label, valor in serie.items():
        valor_float = float(valor or 0)
        largura = 0 if max_valor <= 0 else max(6, int((valor_float / max_valor) * 100))

        if formato == "dinheiro":
            valor_txt = dinheiro(valor_float)
        elif formato == "inteiro":
            valor_txt = str(int(valor_float))
        else:
            valor_txt = str(valor_float)

        itens.append(f"""
        <div class="dash-row">
            <div class="dash-row-top">
                <div class="dash-label">{html.escape(str(label or 'Sem informação'))}</div>
                <div class="dash-value">{html.escape(valor_txt)}</div>
            </div>
            <div class="dash-bar-bg">
                <div class="dash-bar-fill" style="width:{largura}%;"></div>
            </div>
        </div>
        """)

    st.markdown(
        f"""
        <div class="dash-card">
            <div class="dash-title">{html.escape(titulo)}</div>
            {''.join(itens)}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_top_valorizacao(df_dash):
    if df_dash.empty:
        st.info("Sem dados para ranking.")
        return

    top = df_dash.sort_values("valorizacao", ascending=False).head(10)
    linhas = ""

    for _, row in top.iterrows():
        nome = html.escape(str(row.get("nome", "-")))
        marca = html.escape(str(row.get("marca", "-")))
        raridade = html.escape(str(row.get("raridade", "-")))
        pago = dinheiro(row.get("valor_pago", 0))
        atual = dinheiro(row.get("preco_atual", 0))
        val = dinheiro(row.get("valorizacao", 0))

        linhas += f"""
        <tr>
            <td>{nome}</td>
            <td>{marca}</td>
            <td>{raridade}</td>
            <td>{pago}</td>
            <td>{atual}</td>
            <td class="dash-value">{val}</td>
        </tr>
        """

    st.markdown(
        f"""
        <div class="dash-card">
            <div class="dash-title">🏆 Top valorização</div>
            <div class="dash-table-wrap">
                <table class="dash-table">
                    <thead>
                        <tr>
                            <th>Mini</th>
                            <th>Marca</th>
                            <th>Raridade</th>
                            <th>Pago</th>
                            <th>Atual</th>
                            <th>Ganho</th>
                        </tr>
                    </thead>
                    <tbody>{linhas}</tbody>
                </table>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def exibir_carrossel(fotos, id_mini, altura=300):
    """
    Carrossel leve e estável:
    - sem components.html
    - fotos sempre dentro de uma área fixa
    - não deixa o card crescer/encolher conforme a proporção da imagem
    - melhor para celular e Streamlit Cloud
    """
    imagens = []

    for foto in fotos:
        src = imagem_para_src(foto)
        if src:
            imagens.append(src)

    if not imagens:
        st.markdown(
            f'<div class="empty-photo" style="height:{altura}px;">🚗 Sem foto</div>',
            unsafe_allow_html=True
        )
        return

    safe_id = f"carousel_{str(id_mini).replace('-', '_').replace(' ', '_')}"
    chave_idx = f"{safe_id}_idx"

    if chave_idx not in st.session_state:
        st.session_state[chave_idx] = 0

    total = len(imagens)

    if st.session_state[chave_idx] >= total:
        st.session_state[chave_idx] = 0

    indice = st.session_state[chave_idx]
    imagem_atual = html.escape(imagens[indice], quote=True)

    st.markdown(
        f"""
        <div class="carousel-frame" style="--carousel-height:{altura}px;">
            <img src="{imagem_atual}" alt="Foto da mini">
        </div>
        """,
        unsafe_allow_html=True
    )

    if total > 1:
        c1, c2, c3 = st.columns([1, 2.2, 1])

        with c1:
            if st.button("◀", key=f"{safe_id}_prev", use_container_width=True):
                st.session_state[chave_idx] = (st.session_state[chave_idx] - 1) % total
                st.rerun()

        with c2:
            bolinhas = " ".join(["●" if i == indice else "○" for i in range(total)])
            st.markdown(
                f"""
                <div class="carousel-dots">
                    {bolinhas}<br>
                    <span class="carousel-count">{indice + 1}/{total}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c3:
            if st.button("▶", key=f"{safe_id}_next", use_container_width=True):
                st.session_state[chave_idx] = (st.session_state[chave_idx] + 1) % total
                st.rerun()
    else:
        st.markdown(
            """
            <div class="carousel-dots">
                ●<br><span class="carousel-count">1/1</span>
            </div>
            """,
            unsafe_allow_html=True
        )



# =========================================================
# APP
# =========================================================

criar_banco()

st.markdown("""
<div class="hero-box">
    <div class="hero-title">🚗 Minha coleção de minis</div>
    <div class="hero-subtitle">Seu museu digital premium de miniaturas, raridades e sonhos sobre rodas.</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("## 🔐 Acesso")

senha_digitada = st.sidebar.text_input(
    "Senha de administrador",
    type="password"
)

admin_logado = senha_digitada == st.secrets.get("ADMIN_PASSWORD", "")

if admin_logado:
    st.sidebar.success("Modo administrador ativo 🔥")
    opcoes_menu = ["Dashboard", "Cadastrar", "Ver coleção", "Adicionar fotos", "Importar Excel"]
else:
    st.sidebar.info("Modo visitante: somente visualização")
    opcoes_menu = ["Dashboard", "Ver coleção"]

menu = st.sidebar.radio("Menu", opcoes_menu)

if st.session_state.ml_feedback:
    tipo, mensagem = st.session_state.ml_feedback
    if tipo == "ok":
        st.success(mensagem)
    else:
        st.warning(mensagem)
    st.session_state.ml_feedback = None



if menu == "Dashboard":
    st.header("Dashboard da coleção")

    minis = listar()

    if not minis:
        st.info("Ainda não há minis cadastradas.")
    else:
        total_minis = len(minis)
        valor_total = sum([m[6] for m in minis if m[6]])
        preco_total = sum([m[10] for m in minis if m[10]])
        valorizacao_total = preco_total - valor_total

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🚗 Total de minis", total_minis)
        c2.metric("💰 Total pago", dinheiro(valor_total))
        c3.metric("📈 Valor atual", dinheiro(preco_total))
        c4.metric("🔥 Valorização", dinheiro(valorizacao_total))

        ranking_elite = []
        for mini in minis:
            score = calcular_score_mini(mini[1], mini[2], mini[3], mini[4])
            ranking_elite.append({
                "Mini": mini[1],
                "Marca": mini[2],
                "Raridade": mini[4],
                "Categoria": categoria_elite(score),
                "Score": score,
            })

        df_rank_elite = pd.DataFrame(ranking_elite).sort_values("Score", ascending=False)
        score_total = int(df_rank_elite["Score"].sum()) if not df_rank_elite.empty else 0
        elite_total = int((df_rank_elite["Score"] >= 70).sum()) if not df_rank_elite.empty else 0
        hype_total = int(((df_rank_elite["Score"] >= 45) & (df_rank_elite["Score"] < 70)).sum()) if not df_rank_elite.empty else 0
        jdm_total = int(df_rank_elite["Categoria"].astype(str).str.contains("JDM", na=False).sum()) if not df_rank_elite.empty else 0

        e1, e2, e3, e4 = st.columns(4)
        e1.metric("🏆 Elite Score", score_total)
        e2.metric("💎 Minis Elite", elite_total)
        e3.metric("🔥 Hype", hype_total)
        e4.metric("🏁 JDM Score", jdm_total)

        st.markdown("### 🏆 Ranking Elite da Garagem")
        st.dataframe(
            df_rank_elite.head(15),
            use_container_width=True,
            hide_index=True
        )

        df_dash = pd.DataFrame(minis, columns=[
            "id", "nome", "marca", "serie", "raridade", "status", "valor_pago", "foto",
            "favorito", "link_compra", "preco_atual", "observacoes", "atualizado_em"
        ])

        df_dash["marca"] = df_dash["marca"].replace("", "Sem marca").fillna("Sem marca")
        df_dash["raridade"] = df_dash["raridade"].replace("", "Sem raridade").fillna("Sem raridade")
        df_dash["valor_pago"] = pd.to_numeric(df_dash["valor_pago"], errors="coerce").fillna(0)
        df_dash["preco_atual"] = pd.to_numeric(df_dash["preco_atual"], errors="coerce").fillna(0)
        df_dash["valorizacao"] = df_dash["preco_atual"] - df_dash["valor_pago"]

        render_top_valorizacao(df_dash)

        col_dash1, col_dash2 = st.columns(2)

        with col_dash1:
            por_marca = (
                df_dash.groupby("marca", dropna=False)["preco_atual"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
            )
            render_bar_list("📊 Valor atual por marca", por_marca, formato="dinheiro")

        with col_dash2:
            por_raridade = df_dash["raridade"].value_counts().head(10)
            render_bar_list("⭐ Quantidade por raridade", por_raridade, formato="inteiro")



if menu == "Cadastrar" and admin_logado:
    st.header("Cadastrar mini")

    with st.container(border=True):
        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("Nome")
            marca = st.text_input("Marca")
            serie = st.text_input("Série")

        with col2:
            raridade = st.selectbox(
                "Raridade",
                ["Comum", "TH", "STH", "RLC", "Chase", "Premium", "Especial"]
            )
            status = st.selectbox(
                "Status",
                ["Tenho", "Quero", "Repetido", "Vendido"]
            )
            valor = st.number_input("Valor pago", min_value=0.0, step=1.0)

        st.markdown("### 💰 Dados de mercado")
        col_ml1, col_ml2 = st.columns(2)

        with col_ml1:
            link_compra = st.text_input("Link de compra")

        with col_ml2:
            preco_atual = st.number_input("Preço atual estimado", min_value=0.0, step=1.0)

        if link_compra:
            link_preview = normalizar_link_ml(link_compra)
            st.caption(f"Link que será salvo: {link_preview}")

        observacoes = st.text_area("Observações")

        fotos_upload = st.file_uploader(
            "Fotos",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        if st.button("Salvar mini 🔥", use_container_width=True):
            if not nome.strip():
                st.warning("Informe pelo menos o nome da mini.")
            else:
                caminhos = []

                if fotos_upload:
                    with st.spinner("Enviando fotos para a nuvem..."):
                        for foto in fotos_upload:
                            url = upload_foto_supabase(foto, "mini")
                            if url:
                                caminhos.append(url)

                salvar(nome, marca, serie, raridade, status, valor, ";".join(caminhos), link_compra, preco_atual, observacoes)
                st.success("Mini salvo com sucesso no Supabase! 🔥")
                st.rerun()


if menu == "Ver coleção":
    if st.session_state.mini_detalhe_id:
        mini = buscar_mini_por_id(st.session_state.mini_detalhe_id)

        if not mini:
            st.warning("Mini não encontrada.")
            if st.button("⬅ Voltar", on_click=voltar_colecao):
                st.rerun()
        else:
            (
                id_mini, nome, marca, serie, raridade, status, valor, foto,
                favorito, link_compra, preco_atual, observacoes, atualizado_em
            ) = mini

            fotos_validas = lista_fotos_validas(foto)
            valorizacao = float(preco_atual or 0) - float(valor or 0)

            st.markdown('<div class="detail-box">', unsafe_allow_html=True)

            col_top1, col_top2, col_top3 = st.columns([1, 1, 1])

            with col_top1:
                if st.button("⬅ Voltar para coleção", use_container_width=True, on_click=voltar_colecao):
                    st.rerun()

            with col_top2:
                if st.button("💛 Favorita" if favorito else "⭐ Favoritar", use_container_width=True):
                    alternar_favorito(id_mini, favorito)
                    st.rerun()

            with col_top3:
                if link_compra:
                    st.link_button("🛒 Abrir link de compra", link_compra, use_container_width=True)

            st.markdown(
                f"""
                <div class="detail-title">{html.escape(str(nome or ""))}</div>
                <div class="detail-subtitle">
                    {html.escape(str(marca or "-"))} • {html.escape(str(serie or "-"))} • {html.escape(str(raridade or "-"))}
                </div>
                """,
                unsafe_allow_html=True
            )

            col_img, col_info = st.columns([1.35, 1])

            with col_img:
                exibir_carrossel(fotos_validas, f"detalhe_{id_mini}", altura=430)

            with col_info:
                badge_css = classe_badge(raridade)
                st.markdown(
                    f'<div class="badge {badge_css}">{html.escape(str(raridade or "Comum"))}</div>',
                    unsafe_allow_html=True
                )
                render_elite_chip(nome, marca, serie, raridade)

                m1, m2 = st.columns(2)
                m1.metric("💰 Valor pago", dinheiro(valor))
                m2.metric("📈 Preço atual", dinheiro(preco_atual))

                classe_ganho = "gain-neutral"
                sinal = ""
                if valorizacao > 0:
                    classe_ganho = "gain-positive"
                    sinal = "+"
                elif valorizacao < 0:
                    classe_ganho = "gain-negative"

                st.markdown(
                    f"""
                    <div class="mini-info">🚗 <b>Marca:</b> {html.escape(str(marca or "-"))}</div>
                    <div class="mini-info">📦 <b>Série:</b> {html.escape(str(serie or "-"))}</div>
                    <div class="mini-info">⭐ <b>Status:</b> {html.escape(str(status or "-"))}</div>
                    <div class="mini-info">💛 <b>Favorito:</b> {"Sim" if favorito else "Não"}</div>
                    <div class="mini-info">🕒 <b>Atualizado:</b> {html.escape(str(atualizado_em or "-"))}</div>
                    <br>
                    <div class="{classe_ganho}">Valorização: {sinal}{dinheiro(valorizacao)}</div>
                    """,
                    unsafe_allow_html=True
                )

                if observacoes:
                    st.markdown("### 📝 Observações")
                    st.write(observacoes)

            st.markdown("### 📈 Histórico de valorização")
            exibir_grafico_historico(id_mini)

            st.markdown('</div>', unsafe_allow_html=True)

            if admin_logado:
                with st.expander("⚙️ Editar mini completo"):
                    raridades_opcoes = ["Comum", "TH", "STH", "RLC", "Chase", "Premium", "Especial"]
                    status_opcoes = ["Tenho", "Quero", "Repetido", "Vendido"]

                    col_edit1, col_edit2 = st.columns(2)

                    with col_edit1:
                        novo_nome = st.text_input("Nome", value=nome or "")
                        nova_marca = st.text_input("Marca", value=marca or "")
                        nova_serie = st.text_input("Série", value=serie or "")

                        nova_raridade = st.selectbox(
                            "Raridade",
                            raridades_opcoes,
                            index=raridades_opcoes.index(raridade) if raridade in raridades_opcoes else 0
                        )

                    with col_edit2:
                        novo_status = st.selectbox(
                            "Status",
                            status_opcoes,
                            index=status_opcoes.index(status) if status in status_opcoes else 0
                        )

                        novo_valor_pago = st.number_input(
                            "Valor pago",
                            min_value=0.0,
                            step=1.0,
                            value=float(valor or 0)
                        )

                        novo_preco = st.number_input(
                            "Preço atual",
                            min_value=0.0,
                            step=1.0,
                            value=float(preco_atual or 0)
                        )

                    novo_link = st.text_input("Link de compra", value=link_compra or "")
                    nova_obs = st.text_area("Observações", value=observacoes or "")

                    if novo_link:
                        st.caption(f"Link limpo detectado: {normalizar_link_ml(novo_link)}")

                    if st.button("Salvar alterações 🔥", use_container_width=True):
                        if not novo_nome.strip():
                            st.warning("Informe pelo menos o nome da mini.")
                        else:
                            atualizar_mini_completo(
                                id_mini,
                                novo_nome,
                                nova_marca,
                                nova_serie,
                                nova_raridade,
                                novo_status,
                                novo_valor_pago,
                                novo_link,
                                novo_preco,
                                nova_obs
                            )
                            st.success("Mini atualizado com sucesso 🔥")
                            st.rerun()

    else:
        st.header("Minha coleção")

        minis = listar()

        total_minis = len(minis)
        valor_total = sum([m[6] for m in minis if m[6]])
        preco_total = sum([m[10] for m in minis if m[10]])
        marcas_total = len(set([m[2] for m in minis if m[2]]))
        raros_total = len([m for m in minis if str(m[4]).lower() in ["sth", "rlc", "chase", "especial"]])
        favoritos_total = len([m for m in minis if m[8]])

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("🚗 Total", total_minis)
        col2.metric("💰 Pago", dinheiro(valor_total))
        col3.metric("📈 Atual", dinheiro(preco_total))
        col4.metric("🔥 Raros", raros_total)
        col5.metric("💛 Favoritos", favoritos_total)

        st.markdown("---")

        col_busca, col_marca, col_raridade, col_status, col_fav = st.columns(5)

        with col_busca:
            busca = st.text_input("🔍 Buscar")

        marcas = sorted(list(set([m[2] for m in minis if m[2]])))
        raridades = sorted(list(set([m[4] for m in minis if m[4]])))
        status_lista = sorted(list(set([m[5] for m in minis if m[5]])))

        with col_marca:
            filtro_marca = st.selectbox("🎯 Marca", ["Todas"] + marcas)

        with col_raridade:
            filtro_raridade = st.selectbox("🏁 Raridade", ["Todas"] + raridades)

        with col_status:
            filtro_status = st.selectbox("⭐ Status", ["Todos"] + status_lista)

        with col_fav:
            somente_favoritos = st.checkbox("💛 Favoritos")

        if busca:
            busca_lower = busca.lower()
            minis = [
                m for m in minis
                if busca_lower in str(m[1]).lower()
                or busca_lower in str(m[2]).lower()
                or busca_lower in str(m[3]).lower()
                or busca_lower in str(m[4]).lower()
                or busca_lower in str(m[11]).lower()
            ]

        if filtro_marca != "Todas":
            minis = [m for m in minis if m[2] == filtro_marca]

        if filtro_raridade != "Todas":
            minis = [m for m in minis if m[4] == filtro_raridade]

        if filtro_status != "Todos":
            minis = [m for m in minis if m[5] == filtro_status]

        if somente_favoritos:
            minis = [m for m in minis if m[8]]

        st.write(f"Resultado: **{len(minis)}** mini(s)")

        if minis and admin_logado:
            st.markdown("### ✏️ Atalho rápido de edição")
            opcoes_edicao = {
                f"{m[1]} | {m[2]} | ID {m[0]}": m
                for m in minis
            }

            mini_edicao_label = st.selectbox(
                "Escolha uma mini para editar",
                list(opcoes_edicao.keys()),
                key="select_edicao_rapida"
            )

            mini_edicao = opcoes_edicao[mini_edicao_label]
            (
                edit_id, edit_nome, edit_marca, edit_serie, edit_raridade, edit_status,
                edit_valor, edit_foto, edit_favorito, edit_link, edit_preco, edit_obs, edit_atualizado
            ) = mini_edicao

            with st.expander("Abrir editor desta mini", expanded=False):
                raridades_opcoes = ["Comum", "TH", "STH", "RLC", "Chase", "Premium", "Especial"]
                status_opcoes = ["Tenho", "Quero", "Repetido", "Vendido"]

                col_e1, col_e2 = st.columns(2)

                with col_e1:
                    novo_nome_card = st.text_input("Nome", value=edit_nome or "", key=f"edit_nome_top_{edit_id}")
                    nova_marca_card = st.text_input("Marca", value=edit_marca or "", key=f"edit_marca_top_{edit_id}")
                    nova_serie_card = st.text_input("Série", value=edit_serie or "", key=f"edit_serie_top_{edit_id}")
                    nova_raridade_card = st.selectbox(
                        "Raridade",
                        raridades_opcoes,
                        index=raridades_opcoes.index(edit_raridade) if edit_raridade in raridades_opcoes else 0,
                        key=f"edit_raridade_top_{edit_id}"
                    )

                with col_e2:
                    novo_status_card = st.selectbox(
                        "Status",
                        status_opcoes,
                        index=status_opcoes.index(edit_status) if edit_status in status_opcoes else 0,
                        key=f"edit_status_top_{edit_id}"
                    )
                    novo_valor_card = st.number_input(
                        "Valor pago",
                        min_value=0.0,
                        step=1.0,
                        value=float(edit_valor or 0),
                        key=f"edit_valor_top_{edit_id}"
                    )
                    novo_preco_card = st.number_input(
                        "Preço atual",
                        min_value=0.0,
                        step=1.0,
                        value=float(edit_preco or 0),
                        key=f"edit_preco_top_{edit_id}"
                    )

                novo_link_card = st.text_input("Link de compra", value=edit_link or "", key=f"edit_link_top_{edit_id}")
                nova_obs_card = st.text_area("Observações", value=edit_obs or "", key=f"edit_obs_top_{edit_id}")

                if st.button("Salvar edição rápida 🔥", key=f"salvar_edit_top_{edit_id}", use_container_width=True):
                    if not novo_nome_card.strip():
                        st.warning("Informe pelo menos o nome da mini.")
                    else:
                        atualizar_mini_completo(
                            edit_id,
                            novo_nome_card,
                            nova_marca_card,
                            nova_serie_card,
                            nova_raridade_card,
                            novo_status_card,
                            novo_valor_card,
                            novo_link_card,
                            novo_preco_card,
                            nova_obs_card
                        )
                        st.success("Mini atualizada com sucesso 🔥")
                        st.rerun()

        if minis:
            ITENS_POR_PAGINA = 9
            total_paginas = max(1, (len(minis) + ITENS_POR_PAGINA - 1) // ITENS_POR_PAGINA)
            pagina_atual = st.number_input(
                "Página",
                min_value=1,
                max_value=total_paginas,
                value=1,
                step=1,
                key="pagina_colecao"
            )
            inicio_pagina = (int(pagina_atual) - 1) * ITENS_POR_PAGINA
            fim_pagina = inicio_pagina + ITENS_POR_PAGINA
            minis_para_exibir = minis[inicio_pagina:fim_pagina]
            st.caption(f"Exibindo {inicio_pagina + 1} a {min(fim_pagina, len(minis))} de {len(minis)} minis")
        else:
            minis_para_exibir = []

        if not minis:
            st.info("Nenhuma mini encontrada com esses filtros.")
        else:
            COLUNAS_POR_LINHA = 3

            for linha_inicio in range(0, len(minis_para_exibir), COLUNAS_POR_LINHA):
                linha = minis_para_exibir[linha_inicio:linha_inicio + COLUNAS_POR_LINHA]
                colunas = st.columns(COLUNAS_POR_LINHA)

                for coluna, mini in zip(colunas, linha):
                    (
                        id_mini, nome, marca, serie, raridade, status, valor, foto,
                        favorito, link_compra, preco_atual, observacoes, atualizado_em
                    ) = mini

                    fotos_validas = lista_fotos_validas(foto)
                    badge_css = classe_badge(raridade)
                    valorizacao = float(preco_atual or 0) - float(valor or 0)

                    with coluna:
                        with st.container(border=True):
                            st.markdown('<div class="mini-card-anchor"></div>', unsafe_allow_html=True)
                            exibir_carrossel(fotos_validas, id_mini)

                            st.markdown(
                                f'<div class="badge {badge_css}">{html.escape(str(raridade or "Comum"))}</div>',
                                unsafe_allow_html=True
                            )
                            render_elite_chip(nome, marca, serie, raridade)
                            st.markdown(
                                f'<div class="mini-title">{"💛 " if favorito else ""}{html.escape(str(nome or ""))}</div>',
                                unsafe_allow_html=True
                            )

                            classe_ganho = "gain-neutral"
                            sinal = ""
                            if valorizacao > 0:
                                classe_ganho = "gain-positive"
                                sinal = "+"
                            elif valorizacao < 0:
                                classe_ganho = "gain-negative"

                            st.markdown(
                                f"""
                                <div class="mini-info">🚗 <b>Marca:</b> {html.escape(str(marca or "-"))}</div>
                                <div class="mini-info">📦 <b>Série:</b> {html.escape(str(serie or "-"))}</div>
                                <div class="mini-info">⭐ <b>Status:</b> {html.escape(str(status or "-"))}</div>
                                <div class="footer-card">
                                    <div class="mini-value">💰 Pago: {dinheiro(valor)}</div>
                                    <div class="mini-info">📈 Atual: {dinheiro(preco_atual)}</div>
                                    <div class="{classe_ganho}">Valorização: {sinal}{dinheiro(valorizacao)}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            btn1, btn2 = st.columns(2)

                            with btn1:
                                if st.button("💛" if favorito else "⭐", key=f"fav_{id_mini}", use_container_width=True):
                                    alternar_favorito(id_mini, favorito)
                                    st.rerun()

                            with btn2:
                                with st.expander("✏️ Editar mini"):
                                    raridades_opcoes_card = ["Comum", "TH", "STH", "RLC", "Chase", "Premium", "Especial"]
                                    status_opcoes_card = ["Tenho", "Quero", "Repetido", "Vendido"]

                                    with st.form(key=f"form_card_{id_mini}"):
                                        novo_nome_card2 = st.text_input(
                                            "Nome",
                                            value=nome or "",
                                            key=f"card_nome_{id_mini}"
                                        )

                                        nova_raridade_card2 = st.selectbox(
                                            "Raridade",
                                            raridades_opcoes_card,
                                            index=raridades_opcoes_card.index(raridade) if raridade in raridades_opcoes_card else 0,
                                            key=f"card_raridade_{id_mini}"
                                        )

                                        novo_status_card2 = st.selectbox(
                                            "Status",
                                            status_opcoes_card,
                                            index=status_opcoes_card.index(status) if status in status_opcoes_card else 0,
                                            key=f"card_status_{id_mini}"
                                        )

                                        col_card_val1, col_card_val2 = st.columns(2)
                                        with col_card_val1:
                                            novo_valor_card2 = st.number_input(
                                                "Pago",
                                                min_value=0.0,
                                                step=1.0,
                                                value=float(valor or 0),
                                                key=f"card_valor_{id_mini}"
                                            )
                                        with col_card_val2:
                                            novo_preco_card2 = st.number_input(
                                                "Atual",
                                                min_value=0.0,
                                                step=1.0,
                                                value=float(preco_atual or 0),
                                                key=f"card_preco_{id_mini}"
                                            )

                                        salvar_card = st.form_submit_button(
                                            "Salvar 🔥",
                                            use_container_width=True
                                        )

                                        if salvar_card:
                                            if not novo_nome_card2.strip():
                                                st.warning("Informe pelo menos o nome da mini.")
                                            else:
                                                atualizar_mini_completo(
                                                    id_mini,
                                                    novo_nome_card2,
                                                    marca,
                                                    serie,
                                                    nova_raridade_card2,
                                                    novo_status_card2,
                                                    novo_valor_card2,
                                                    link_compra,
                                                    novo_preco_card2,
                                                    observacoes
                                                )
                                                st.success("Mini atualizada 🔥")
                                                st.rerun()


if menu == "Adicionar fotos" and admin_logado:
    st.header("Adicionar fotos ao mini")

    minis = listar()

    if not minis:
        st.info("Nenhum mini cadastrado ainda.")
    else:
        opcoes = {
            f"{m[1]} | {m[2]} | {m[3]}": m[0]
            for m in minis
        }

        escolhido = st.selectbox("Escolha o mini", list(opcoes.keys()))
        id_escolhido = opcoes[escolhido]

        fotos_upload = st.file_uploader(
            "Selecione uma ou mais fotos do mini",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        if fotos_upload and st.button("Salvar fotos 📸", use_container_width=True):
            caminhos = []

            with st.spinner("Enviando fotos para a nuvem..."):
                for foto in fotos_upload:
                    url = upload_foto_supabase(foto, f"mini_{id_escolhido}")
                    if url:
                        caminhos.append(url)

            atualizar_foto(id_escolhido, ";".join(caminhos))
            st.success("Fotos adicionadas no Supabase! 📸🔥")
            st.rerun()


if menu == "Importar Excel" and admin_logado:
    st.header("Importar Excel")

    arquivo = st.file_uploader("Planilha", type=["xlsx"])

    if arquivo:
        df = pd.read_excel(arquivo)
        st.dataframe(df, use_container_width=True)

        if st.button("Importar planilha 🔥", use_container_width=True):
            try:
                registros = []

                for _, row in df.iterrows():
                    registros.append({
                        "nome": row.get("Nome", ""),
                        "marca": row.get("Marca", ""),
                        "serie": row.get("Série", ""),
                        "raridade": row.get("Raridade", ""),
                        "status": row.get("Status", "Tenho"),
                        "valor_pago": float(row.get("Valor pago", 0) or 0),
                        "foto": "",
                        "favorito": False,
                        "link_compra": "",
                        "preco_atual": 0,
                        "observacoes": "",
                        "atualizado_em": datetime.now().isoformat()
                    })

                if registros:
                    supabase.table("minis").insert(registros).execute()

                st.success("Importado com sucesso para o Supabase 🔥")
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao importar planilha para o Supabase: {e}")
# forcar redeploy streamlit
