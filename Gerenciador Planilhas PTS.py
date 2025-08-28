import streamlit as st
import pandas as pd
import re
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# =========================
# Configuração geral
# =========================
st.set_page_config(page_title="Central de Planilhas", layout="wide")

BASE_DIR = Path(__file__).parent if "__file__" in globals() else Path.cwd()
DB_PATH = BASE_DIR / "links_db.csv"

# Colunas do "banco"
COLS = [
    "ID", "Nome", "URL", "Categoria", "Tags",
    "Ativo", "Criado_em", "Arquivado_em"
]

# =========================
# Estilos (CSS) - Shopee
# =========================
ACCENT = "#EE4D2D"  # Shopee laranja
ACCENT_RGB = "238,77,45"  # para RGBA
st.markdown(
    f"""
    <style>
    :root {{
        --accent: {ACCENT};
    }}
    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }}
    /* Header em gradiente laranja */
    .app-header {{
        background: linear-gradient(135deg, var(--accent) 0%, #FF8A65 100%);
        color: #ffffff;
        padding: 20px 24px;
        border-radius: 18px;
        box-shadow: 0 10px 30px rgba(0,0,0,.08);
        margin-bottom: 12px;
    }}
    .app-header h1 {{
        font-size: 1.6rem;
        margin: 0 0 .25rem 0;
        line-height: 1.2;
    }}
    .app-header p {{
        margin: 0;
        opacity: .95;
    }}
    /* Cards brancos */
    .card {{
        border: 1px solid rgba(0,0,0,.08);
        border-radius: 16px;
        padding: 16px;
        background: #FFFFFF;
        box-shadow: 0 8px 20px rgba(0,0,0,.05);
        margin-bottom: 12px;
    }}
    /* Badge com laranja translúcido */
    .badge {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba({ACCENT_RGB}, .12);
        color: var(--accent);
        font-weight: 700;
        font-size: 12px;
        margin-right: 6px;
        border: 1px solid rgba({ACCENT_RGB}, .20);
    }}
    /* Chips neutras */
    .chip {{
        display:inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        background: #F3F4F6;
        font-size: 12px;
        margin: 2px 6px 0 0;
        border: 1px solid rgba(0,0,0,.06);
    }}
    .meta {{
        font-size: 12px;
        opacity: .75;
    }}
    /* Botões com cantos arredondados */
    .stButton>button {{
        border-radius: 12px !important;
        border: 1px solid rgba(0,0,0,.08);
        padding: 8px 14px;
    }}
    /* LinkButton */
    .stLinkButton>a {{
        border-radius: 12px !important;
        padding: 8px 14px !important;
        border: 1px solid rgba(0,0,0,.08) !important;
        background: #FFFFFF !important;
        color: var(--accent) !important;
    }}
    /* Realçar botões primários com laranja */
    .stButton>button[kind="primary"] {{
        background: var(--accent);
        color: #FFF;
        border: 1px solid rgba({ACCENT_RGB}, .3);
    }}
    /* Tabs com borda leve */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 6px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 12px;
        padding: 8px 14px;
        border: 1px solid rgba(0,0,0,.08);
        background: #FFFFFF;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# Helpers
# =========================
def is_valid_gsheets_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    pattern = r"^https://docs\.google\.com/spreadsheets/d/[^/\s]+"
    return re.match(pattern, url.strip()) is not None

def ensure_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in COLS:
        if c not in df.columns:
            if c in ("Ativo",):
                df[c] = "True"
            else:
                df[c] = ""
    # IDs
    mask_no_id = (df["ID"].isna()) | (df["ID"].astype(str).str.strip() == "")
    if mask_no_id.any():
        df.loc[mask_no_id, "ID"] = [str(uuid4()) for _ in range(mask_no_id.sum())]
    # Normalizações
    df["Ativo"] = df["Ativo"].fillna("True").astype(str)
    df["Arquivado_em"] = df["Arquivado_em"].fillna("").astype(str)
    df["Tags"] = df["Tags"].fillna("").astype(str)
    return df[COLS]

def load_db() -> pd.DataFrame:
    if DB_PATH.exists():
        df = pd.read_csv(DB_PATH, dtype=str)
        df = ensure_cols(df)
        df.to_csv(DB_PATH, index=False)  # grava caso tenha completado colunas
        return df
    else:
        df = pd.DataFrame(columns=COLS)
        df = ensure_cols(df)
        df.to_csv(DB_PATH, index=False)
        return df

def save_db(df: pd.DataFrame):
    df = ensure_cols(df)
    df.to_csv(DB_PATH, index=False)

def parse_tags(tags_str: str) -> list[str]:
    if not isinstance(tags_str, str) or not tags_str.strip():
        return []
    return [t.strip() for t in tags_str.split(",") if t.strip()]

def unique_sorted(values):
    vals = sorted({v for v in values if isinstance(v, str) and v.strip()})
    return vals

# Ações
def archive_ids(ids: list[str]):
    if not ids: return
    df = st.session_state.df_links.copy()
    df.loc[df["ID"].isin(ids), "Ativo"] = "False"
    df.loc[df["ID"].isin(ids), "Arquivado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_db(df)
    st.session_state.df_links = df
    st.toast(f"🗃️ {len(ids)} link(s) enviados para a lixeira.")

def restore_ids(ids: list[str]):
    if not ids: return
    df = st.session_state.df_links.copy()
    df.loc[df["ID"].isin(ids), "Ativo"] = "True"
    df.loc[df["ID"].isin(ids), "Arquivado_em"] = ""
    save_db(df)
    st.session_state.df_links = df
    st.toast(f"♻️ {len(ids)} link(s) restaurado(s).")

def permanent_delete_ids(ids: list[str]):
    if not ids: return
    df = st.session_state.df_links.copy()
    before = len(df)
    df = df[~df["ID"].isin(ids)].reset_index(drop=True)
    save_db(df)
    st.session_state.df_links = df
    st.toast(f"🗑️ Excluídos definitivamente {before - len(df)} link(s).")

# =========================
# Estado (upgrade de esquema garantido)
# =========================
if "df_links" not in st.session_state:
    st.session_state.df_links = load_db()
else:
    st.session_state.df_links = ensure_cols(st.session_state.df_links)
    save_db(st.session_state.df_links)

df = st.session_state.df_links

# =========================
# Header
# =========================
st.markdown(
    """
    <div class="app-header">
      <h1>📊 Central de Planilhas — Google Sheets</h1>
      <p>Cadastre, filtre, arquive/restaure e gerencie todos os seus links em um só lugar.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Métricas
total = len(df)
ativas = int((df["Ativo"] == "True").sum())
arquivadas = total - ativas
m1, m2, m3 = st.columns([1,1,1])
with m1: st.metric("Total", total)
with m2: st.metric("Ativas", ativas)
with m3: st.metric("Arquivadas", arquivadas)

st.write("")

# =========================
# Formulário: Adicionar link
# =========================
with st.container(border=True):
    st.subheader("➕ Adicionar nova planilha")
    c1, c2, c3, c4 = st.columns([3, 5, 3, 3])

    with c1:
        nome = st.text_input("Nome", placeholder="Ex.: Controle de Frota")

    with c2:
        url = st.text_input("URL do Google Sheets", placeholder="https://docs.google.com/spreadsheets/d/…")

    with c3:
        categoria = st.text_input("Categoria", placeholder="Operações, Vendas…")

    with c4:
        tags = st.text_input("Tags (separe por vírgulas)", placeholder="Shopee, LPA-03, Motoristas")

    col_a, col_b = st.columns([1, 5])
    with col_a:
        ativo = st.checkbox("Ativo", value=True)

    if st.button("Salvar link", type="primary"):
        if not nome.strip() or not url.strip():
            st.error("Informe **Nome** e **URL**.")
        elif not is_valid_gsheets_url(url):
            st.error("URL inválida. Use um link de Google Sheets (começando com `https://docs.google.com/spreadsheets/d/`).")
        else:
            new_row = {
                "ID": str(uuid4()),
                "Nome": nome.strip(),
                "URL": url.strip(),
                "Categoria": categoria.strip(),
                "Tags": tags.strip(),
                "Ativo": "True" if ativo else "False",
                "Criado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Arquivado_em": "" if ativo else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_db(df)
            st.session_state.df_links = df
            st.success(f"✅ '{nome}' adicionada.")

# =========================
# Abas
# =========================
tab1, tab2, tab3 = st.tabs(["📁 Ativas", "🗃️ Arquivadas (Lixeira)", "🧾 Tabela & Importar"])

# ============
# Filtros comuns
# ============
def filtros_basicos(df_base: pd.DataFrame, show_archived: bool = False) -> pd.DataFrame:
    with st.container(border=True):
        st.subheader("🔎 Buscar e filtrar")

        # Proteções para esquemas antigos
        df_base = df_base.copy()
        if "Categoria" not in df_base.columns: df_base["Categoria"] = ""
        if "Tags" not in df_base.columns: df_base["Tags"] = ""

        all_cats = unique_sorted(df_base["Categoria"].dropna().astype(str).tolist())
        all_tags = sorted({t for s in df_base["Tags"].fillna("").astype(str) for t in parse_tags(s)})

        fc1, fc2 = st.columns([3, 2])
        with fc1:
            termo = st.text_input(
                "Buscar por nome",
                placeholder="Digite um trecho do nome…",
                key=f"search_{'arch' if show_archived else 'act'}"
            )
        with fc2:
            order = st.selectbox(
                "Ordenar por",
                ["Mais recentes", "Mais antigas", "Nome (A→Z)", "Nome (Z→A)"],
                index=0,
                key=f"order_{'arch' if show_archived else 'act'}"
            )

        fc3, fc4, fc5 = st.columns([2, 3, 2])
        with fc3:
            cat_multi = st.multiselect("Categoria", all_cats, key=f"cat_{'arch' if show_archived else 'act'}")
        with fc4:
            tag_multi = st.multiselect("Tags", all_tags, key=f"tag_{'arch' if show_archived else 'act'}")
        with fc5:
            st.write("")
            if show_archived:
                st.caption("Exibindo apenas **arquivadas**.")
            else:
                only_active = st.checkbox("Somente ativas", value=True, key="only_active_filter")
                df_base = df_base[df_base["Ativo"] == "True"] if only_active else df_base

        df_view = df_base.copy()

        # filtros
        if termo:
            df_view = df_view[df_view["Nome"].str.contains(termo, case=False, na=False)]
        if cat_multi:
            df_view = df_view[df_view["Categoria"].isin(cat_multi)]
        if tag_multi:
            def has_tags(s):
                tset = set(parse_tags(str(s)))
                return set(tag_multi).issubset(tset)
            df_view = df_view[df_view["Tags"].apply(has_tags)]

        # ordenação
        if "Criado_em" not in df_view.columns:
            df_view["Criado_em"] = ""
        if order == "Mais recentes":
            df_view = df_view.sort_values(by="Criado_em", ascending=False, na_position="last")
        elif order == "Mais antigas":
            df_view = df_view.sort_values(by="Criado_em", ascending=True, na_position="last")
        elif order == "Nome (A→Z)":
            df_view = df_view.sort_values(by="Nome", ascending=True, na_position="last")
        else:
            df_view = df_view.sort_values(by="Nome", ascending=False, na_position="last")

        st.write(f"Exibindo **{len(df_view)}** planilha(s).")
        return df_view

# ============
# Render de card
# ============
def render_card(row: pd.Series, archived: bool = False):
    tags = parse_tags(row.get("Tags", ""))
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"**{row['Nome']}**")
    # badges
    badges = ""
    if row.get("Categoria"):
        badges += f'<span class="badge">{row["Categoria"]}</span>'
    if badges:
        st.markdown(badges, unsafe_allow_html=True)

    # chips de tags
    if tags:
        chips = " ".join([f'<span class="chip">{t}</span>' for t in tags])
        st.markdown(chips, unsafe_allow_html=True)

    # meta
    criado = row.get("Criado_em", "")
    arquivado = row.get("Arquivado_em", "")
    meta = f'<div class="meta">Criado em: {criado}'
    if archived and arquivado:
        meta += f' &nbsp;•&nbsp; Arquivado em: {arquivado}'
    meta += "</div>"
    st.markdown(meta, unsafe_allow_html=True)

    # ações
    c1, c2, c3 = st.columns([1.2, 1, 1.2])
    with c1:
        st.link_button("🔗 Abrir planilha", row["URL"])
    with c2:
        if not archived:
            # Arquivar com confirmação
            with st.popover("🗃️ Arquivar", use_container_width=True):
                st.write(f"Arquivar **{row['Nome']}**?")
                confirm = st.checkbox("Confirmo", key=f"arch_{row['ID']}")
                if st.button("Confirmar", key=f"arch_btn_{row['ID']}", use_container_width=True):
                    if confirm:
                        archive_ids([row["ID"]])
                        st.rerun()
                    else:
                        st.warning("Confirme antes de arquivar.")
        else:
            # Restaurar
            if st.button("♻️ Restaurar", key=f"restore_{row['ID']}", use_container_width=True):
                restore_ids([row["ID"]])
                st.rerun()
    with c3:
        if archived:
            # Exclusão permanente
            with st.popover("🗑️ Excluir definitivamente", use_container_width=True):
                st.write("Esta ação não pode ser desfeita.")
                confirm2 = st.checkbox("Entendo os riscos", key=f"del_{row['ID']}")
                if st.button("Excluir", key=f"del_btn_{row['ID']}", use_container_width=True, type="secondary"):
                    if confirm2:
                        permanent_delete_ids([row["ID"]])
                        st.rerun()
                    else:
                        st.warning("Confirme antes de excluir.")
        else:
            st.caption("")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# Tab 1: ATIVAS
# =========================
with tab1:
    df_ativas = df[df["Ativo"] == "True"].copy()
    view1 = filtros_basicos(df_ativas, show_archived=False)

    if len(view1) == 0:
        st.info("Nenhuma planilha encontrada com os filtros aplicados.")
    else:
        cols = st.columns(3)
        for i, (_, row) in enumerate(view1.iterrows()):
            with cols[i % 3]:
                render_card(row, archived=False)

# =========================
# Tab 2: LIXEIRA (Arquivadas)
# =========================
with tab2:
    df_arch = df[df["Ativo"] != "True"].copy()
    view2 = filtros_basicos(df_arch, show_archived=True)

    if len(view2) == 0:
        st.info("Nenhuma planilha arquivada.")
    else:
        cols = st.columns(3)
        for i, (_, row) in enumerate(view2.iterrows()):
            with cols[i % 3]:
                render_card(row, archived=True)

# =========================
# Tab 3: TABELA & IMPORTAR
# =========================
with tab3:
    st.subheader("🧾 Edição em tabela")
    table_df = df.copy()
    if "Tags" not in table_df.columns:  # proteção extra
        table_df["Tags"] = ""
    table_df["Selecionar"] = False  # coluna auxiliar

    edited = st.data_editor(
        table_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "ID": st.column_config.TextColumn(disabled=True, width="small"),
            "Nome": st.column_config.TextColumn(required=True, width="medium"),
            "URL": st.column_config.LinkColumn(required=True, width="large"),
            "Categoria": st.column_config.TextColumn(width="small"),
            "Tags": st.column_config.TextColumn(help="Separe por vírgulas", width="medium"),
            "Ativo": st.column_config.SelectboxColumn(options=["True", "False"], width="small"),
            "Criado_em": st.column_config.TextColumn(width="small", help="Preenchido automaticamente"),
            "Arquivado_em": st.column_config.TextColumn(width="small"),
            "Selecionar": st.column_config.CheckboxColumn(help="Marque para ação em lote", width="small"),
        }
    )

    a1, a2, a3, a4 = st.columns([1.2, 1.2, 1.4, 2.2])
    with a1:
        if st.button("💾 Salvar alterações", type="primary", use_container_width=True):
            # Validação básica
            if edited["Nome"].isna().any() or (edited["Nome"].astype(str).str.strip() == "").any():
                st.error("Há linhas com **Nome** vazio.")
            elif (~edited["URL"].apply(is_valid_gsheets_url)).any():
                st.error("Há URLs inválidas. Corrija antes de salvar.")
            else:
                # garante ID para novas linhas
                mask_no_id = (edited["ID"].isna()) | (edited["ID"].astype(str).str.strip() == "")
                if mask_no_id.any():
                    edited.loc[mask_no_id, "ID"] = [str(uuid4()) for _ in range(mask_no_id.sum())]
                save_db(edited.drop(columns=["Selecionar"], errors="ignore"))
                st.session_state.df_links = load_db()
                st.success("Alterações salvas.")
    with a2:
        if st.button("🗃️ Arquivar selecionados", use_container_width=True):
            ids = edited.loc[edited["Selecionar"] == True, "ID"].dropna().astype(str).tolist()
            if not ids:
                st.warning("Nenhuma linha selecionada.")
            else:
                archive_ids(ids)
                st.rerun()
    with a3:
        if st.button("♻️ Restaurar selecionados", use_container_width=True):
            ids = edited.loc[edited["Selecionar"] == True, "ID"].dropna().astype(str).tolist()
            if not ids:
                st.warning("Nenhuma linha selecionada.")
            else:
                restore_ids(ids)
                st.rerun()
    with a4:
        if st.button("🗑️ Excluir permanentemente selecionados", use_container_width=True):
            ids = edited.loc[edited["Selecionar"] == True, "ID"].dropna().astype(str).tolist()
            if not ids:
                st.warning("Nenhuma linha selecionada.")
            else:
                permanent_delete_ids(ids)
                st.rerun()

    st.divider()
    cexp, cup = st.columns([1, 1])
    with cexp:
        st.download_button(
            "⬇️ Exportar CSV",
            data=edited.drop(columns=["Selecionar"], errors="ignore").to_csv(index=False).encode("utf-8"),
            file_name="links_export.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with cup:
        up = st.file_uploader("📥 Importar/mesclar CSV", type=["csv"])
        if up is not None:
            try:
                new_df = pd.read_csv(up, dtype=str)
                new_df = ensure_cols(new_df)

                # mescla por ID (mantém existentes, adiciona novos)
                base = st.session_state.df_links.copy()
                merged = pd.concat([base, new_df], ignore_index=True)
                merged = merged.drop_duplicates(subset=["ID"], keep="last").reset_index(drop=True)

                save_db(merged)
                st.session_state.df_links = load_db()
                st.success(f"Importação concluída. Total agora: {len(merged)}.")
            except Exception as e:
                st.error(f"Falha ao importar: {e}")

st.caption("💡 Desenvolvido por Kayo Soares - LPA-O3")
