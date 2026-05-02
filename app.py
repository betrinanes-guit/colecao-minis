import pandas as pd
import sqlite3
from datetime import datetime
from pathlib import Path
import streamlit as st

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

def corrigir_caminhos_antigos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, foto FROM minis")
    registros = cursor.fetchall()

    for id_mini, fotos in registros:
        if not fotos:
            continue

        novas_fotos = []

        for caminho in fotos.split(";"):
            caminho = caminho.strip()

            if not caminho:
                continue

            nome_arquivo = Path(caminho).name
            novo_caminho = str(Path("fotos") / nome_arquivo)
            novas_fotos.append(novo_caminho)

        if novas_fotos:
            cursor.execute(
                "UPDATE minis SET foto = ? WHERE id = ?",
                (";".join(novas_fotos), id_mini)
            )

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

def caminho_para_salvar(nome_arquivo):
    return str(Path("fotos") / nome_arquivo)

def resolver_caminho_foto(caminho_salvo):
    if not caminho_salvo:
        return None

    caminho_salvo = caminho_salvo.strip()

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
corrigir_caminhos_antigos()

st.markdown("# 🚗 Minha coleção de minis")
st.markdown("### Seu museu digital de miniaturas 🔥")

menu = st.sidebar.radio(
    "Menu",
    ["Cadastrar", "Ver coleção", "Adicionar fotos", "Importar Excel"]
)

if menu == "Cadastrar":
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
            for foto in fotos_upload:
                nome_arquivo = f"mini_{datetime.now().timestamp()}_{foto.name}"
                caminho_fisico = FOTOS_DIR / nome_arquivo

                with open(caminho_fisico, "wb") as f:
                    f.write(foto.getbuffer())

                caminhos.append(caminho_para_salvar(nome_arquivo))

        salvar(nome, marca, serie, raridade, status, valor, ";".join(caminhos))
        st.success("Mini salvo com sucesso! 🔥")

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

if menu == "Adicionar fotos":
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

            for foto in fotos_upload:
                nome_arquivo = f"mini_{id_escolhido}_{datetime.now().timestamp()}_{foto.name}"
                caminho_fisico = FOTOS_DIR / nome_arquivo

                with open(caminho_fisico, "wb") as f:
                    f.write(foto.getbuffer())

                caminhos.append(caminho_para_salvar(nome_arquivo))

            atualizar_foto(id_escolhido, ";".join(caminhos))
            st.success("Fotos adicionadas! 📸🔥")

if menu == "Importar Excel":
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