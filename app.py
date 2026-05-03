import pandas as pd
import sqlite3
from datetime import datetime
from pathlib import Path
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Minha coleção de minis",
    page_icon="🚗",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    section[data-testid="stSidebar"] { background-color: #111827; }
    h1, h2, h3 { color: #FFFFFF; }

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1E293B, #111827);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.30);
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(145deg, #1E293B, #111827);
        border-radius: 18px;
        border-color: #334155;
        padding: 14px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.35);
    }

    .mini-title {
        font-size: 20px;
        font-weight: 800;
        color: #FFFFFF;
        min-height: 52px;
        margin-top: 8px;
        margin-bottom: 8px;
    }

    .mini-info {
        font-size: 14px;
        color: #CBD5E1;
        margin-bottom: 5px;
    }

    .mini-value {
        font-size: 15px;
        font-weight: 800;
        color: #38BDF8;
        margin-top: 8px;
    }

    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        background-color: #0F172A;
        border: 1px solid #334155;
        color: #FACC15;
        font-size: 12px;
        font-weight: 700;
        margin-top: 8px;
        margin-bottom: 6px;
    }

    .stButton > button {
        border-radius: 12px;
        border: 1px solid #334155;
        background-color: #1E293B;
        color: white;
        font-weight: 700;
        height: 40px;
    }

    .stButton > button:hover {
        background-color: #2563EB;
        color: white;
        border-color: #38BDF8;
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "colecao.db"
FOTOS_DIR = BASE_DIR / "fotos"
FOTOS_DIR.mkdir(exist_ok=True)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
SUPABASE_BUCKET = st.secrets["SUPABASE_BUCKET"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def conectar():
    return sqlite3.connect(DB_PATH)

def criar_banco():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS minis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        marca TEXT,
        serie TEXT,
        raridade TEXT,
        status TEXT,
        valor_pago REAL,
        foto TEXT
    )
    """)
    conn.commit()
    conn.close()

def salvar(nome, marca, serie, raridade, status, valor_pago, foto):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO minis (nome, marca, serie, raridade, status, valor_pago, foto)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (nome, marca, serie, raridade, status, valor_pago, foto))
    conn.commit()
    conn.close()

def atualizar_foto(id_mini, novas_fotos):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT foto FROM minis WHERE id = ?", (id_mini,))
    atual = cursor.fetchone()

    fotos_atuais = atual[0] if atual and atual[0] else ""
    fotos_final = fotos_atuais + ";" + novas_fotos if fotos_atuais else novas_fotos

    cursor.execute("UPDATE minis SET foto = ? WHERE id = ?", (fotos_final, id_mini))
    conn.commit()
    conn.close()

def listar():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM minis ORDER BY id DESC")
    dados = cursor.fetchall()
    conn.close()
    return dados

def limpar_nome_arquivo(nome):
    return (
        nome.replace(" ", "_")
            .replace("'", "")
            .replace('"', "")
            .replace("ç", "c")
            .replace("Ç", "C")
            .replace("ã", "a")
            .replace("Ã", "A")
            .replace("á", "a")
            .replace("Á", "A")
            .replace("é", "e")
            .replace("É", "E")
            .replace("í", "i")
            .replace("Í", "I")
            .replace("ó", "o")
            .replace("Ó", "O")
            .replace("ú", "u")
            .replace("Ú", "U")
            .replace("’", "")
    )

def upload_foto_supabase(foto, prefixo="mini"):
    nome_limpo = limpar_nome_arquivo(foto.name)
    nome_arquivo = f"{prefixo}_{datetime.now().timestamp()}_{nome_limpo}"

    try:
        supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=nome_arquivo,
            file=foto.getvalue(),
            file_options={
                "content-type": foto.type,
                "upsert": "true"
            }
        )

        url_publica = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(nome_arquivo)
        return url_publica

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

    nome_arquivo = Path(caminho_salvo).name
    caminho_fotos = FOTOS_DIR / nome_arquivo

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

criar_banco()

st.markdown("# 🚗 Minha coleção de minis")
st.markdown("### Seu museu digital de miniaturas 🔥")

# =========================
# SEGURANÇA / MODO ADMIN
# =========================
st.sidebar.markdown("## 🔐 Acesso")

senha_digitada = st.sidebar.text_input(
    "Senha de administrador",
    type="password"
)

admin_logado = senha_digitada == st.secrets.get("ADMIN_PASSWORD", "")

if admin_logado:
    st.sidebar.success("Modo administrador ativo 🔥")
    opcoes_menu = ["Cadastrar", "Ver coleção", "Adicionar fotos", "Importar Excel"]
else:
    st.sidebar.info("Modo visitante: somente visualização")
    opcoes_menu = ["Ver coleção"]

menu = st.sidebar.radio("Menu", opcoes_menu)

# =========================
# CADASTRAR — SOMENTE ADMIN
# =========================
if menu == "Cadastrar" and admin_logado:
    st.header("Cadastrar mini")

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

    fotos_upload = st.file_uploader(
        "Fotos",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    if st.button("Salvar mini 🔥"):
        caminhos = []

        if fotos_upload:
            with st.spinner("Enviando fotos para a nuvem..."):
                for foto in fotos_upload:
                    url = upload_foto_supabase(foto, "mini")
                    if url:
                        caminhos.append(url)

        salvar(nome, marca, serie, raridade, status, valor, ";".join(caminhos))
        st.success("Mini salvo com sucesso na nuvem! 🔥")

# =========================
# VER COLEÇÃO — VISITANTE E ADMIN
# =========================
if menu == "Ver coleção":
    st.header("Minha coleção")

    minis = listar()

    total_minis = len(minis)
    valor_total = sum([m[6] for m in minis if m[6]])

    col1, col2, col3 = st.columns(3)
    col1.metric("🚗 Total de minis", total_minis)
    col2.metric("💰 Valor total", f"R$ {valor_total:.2f}")
    col3.metric("🏁 Categorias", len(set([m[4] for m in minis if m[4]])))

    st.markdown("---")

    col_busca, col_marca, col_raridade = st.columns(3)

    with col_busca:
        busca = st.text_input("🔍 Buscar por nome")

    marcas = sorted(list(set([m[2] for m in minis if m[2]])))
    raridades = sorted(list(set([m[4] for m in minis if m[4]])))

    with col_marca:
        filtro_marca = st.selectbox("🎯 Filtrar por marca", ["Todas"] + marcas)

    with col_raridade:
        filtro_raridade = st.selectbox("🏁 Filtrar por raridade", ["Todas"] + raridades)

    if busca:
        minis = [m for m in minis if busca.lower() in m[1].lower()]

    if filtro_marca != "Todas":
        minis = [m for m in minis if m[2] == filtro_marca]

    if filtro_raridade != "Todas":
        minis = [m for m in minis if m[4] == filtro_raridade]

    st.write(f"Resultado: **{len(minis)}** mini(s)")

    COLUNAS_POR_LINHA = 3

    for linha_inicio in range(0, len(minis), COLUNAS_POR_LINHA):
        linha = minis[linha_inicio:linha_inicio + COLUNAS_POR_LINHA]
        colunas = st.columns(COLUNAS_POR_LINHA)

        for coluna, mini in zip(colunas, linha):
            id_mini, nome, marca, serie, raridade, status, valor, foto = mini
            fotos_validas = lista_fotos_validas(foto)

            with coluna:
                with st.container(border=True):
                    chave = f"foto_index_{id_mini}"

                    if chave not in st.session_state:
                        st.session_state[chave] = 0

                    if fotos_validas:
                        if st.session_state[chave] >= len(fotos_validas):
                            st.session_state[chave] = 0

                        idx = st.session_state[chave]
                        st.image(fotos_validas[idx], use_container_width=True)

                        if len(fotos_validas) > 1:
                            col_btn1, col_btn2 = st.columns(2)

                            with col_btn1:
                                if st.button("⬅️", key=f"prev_{id_mini}"):
                                    st.session_state[chave] = (st.session_state[chave] - 1) % len(fotos_validas)
                                    st.rerun()

                            with col_btn2:
                                if st.button("➡️", key=f"next_{id_mini}"):
                                    st.session_state[chave] = (st.session_state[chave] + 1) % len(fotos_validas)
                                    st.rerun()
                    else:
                        st.info("Sem foto")

                    st.markdown(f'<div class="badge">{raridade}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="mini-title">{nome}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="mini-info">🚗 <b>Marca:</b> {marca}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="mini-info">📦 <b>Série:</b> {serie}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="mini-info">⭐ <b>Status:</b> {status}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="mini-value">💰 Valor: R$ {valor:.2f}</div>', unsafe_allow_html=True)

# =========================
# ADICIONAR FOTOS — SOMENTE ADMIN
# =========================
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

        if fotos_upload and st.button("Salvar fotos 📸"):
            caminhos = []

            with st.spinner("Enviando fotos para a nuvem..."):
                for foto in fotos_upload:
                    url = upload_foto_supabase(foto, f"mini_{id_escolhido}")
                    if url:
                        caminhos.append(url)

            atualizar_foto(id_escolhido, ";".join(caminhos))
            st.success("Fotos adicionadas na nuvem! 📸🔥")

# =========================
# IMPORTAR EXCEL — SOMENTE ADMIN
# =========================
if menu == "Importar Excel" and admin_logado:
    st.header("Importar Excel")

    arquivo = st.file_uploader("Planilha", type=["xlsx"])

    if arquivo:
        df = pd.read_excel(arquivo)
        st.dataframe(df, use_container_width=True)

        if st.button("Importar planilha 🔥"):
            conn = conectar()
            cursor = conn.cursor()

            for _, row in df.iterrows():
                cursor.execute("""
                INSERT INTO minis (nome, marca, serie, raridade, status, valor_pago, foto)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("Nome", ""),
                    row.get("Marca", ""),
                    row.get("Série", ""),
                    row.get("Raridade", ""),
                    row.get("Status", "Tenho"),
                    row.get("Valor pago", 0),
                    ""
                ))

            conn.commit()
            conn.close()
            st.success("Importado com sucesso 🔥")