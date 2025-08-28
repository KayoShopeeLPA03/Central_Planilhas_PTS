# app.py
import streamlit as st
import pandas as pd
import re
from pathlib import Path
from datetime import datetime
from uuid import uuid4

st.set_page_config(page_title="Central de Planilhas", layout="wide")

BASE_DIR = Path(__file__).parent if "__file__" in globals() else Path.cwd()
DB_PATH = BASE_DIR / "links_db.csv"

COLS = ["ID","Nome","URL","Categoria","Tags","Ativo","Criado_em","Arquivado_em"]

ACCENT = "#EE4D2D"
ACCENT_RGB = "238,77,45"
st.markdown(f"""
<style>
:root {{ --accent: {ACCENT}; }}
.block-container {{ padding-top:1.5rem; padding-bottom:2rem; }}
.app-header {{
  background: linear-gradient(135deg, var(--accent) 0%, #FF8A65 100%);
  color:#fff; padding:20px 24px; border-radius:18px;
  box-shadow:0 10px 30px rgba(0,0,0,.08); margin-bottom:12px;
}}
.app-header h1 {{ font-size:1.6rem; margin:0 0 .25rem 0; line-height:1.2; }}
.app-header p {{ margin:0; opacity:.95; }}
.card {{ border:1px solid rgba(0,0,0,.08); border-radius:16px; padding:16px;
         background:#fff; box-shadow:0 8px 20px rgba(0,0,0,.05); margin-bottom:12px; }}
.badge {{ display:inline-block; padding:4px 10px; border-radius:999px;
          background: rgba({ACCENT_RGB}, .12); color:var(--accent); font-weight:700;
          font-size:12px; margin-right:6px; border:1px solid rgba({ACCENT_RGB}, .20); }}
.chip {{ display:inline-block; padding:3px 10px; border-radius:999px; background:#F3F4F6;
        font-size:12px; margin:2px 6px 0 0; border:1px solid rgba(0,0,0,.06); }}
.meta {{ font-size:12px; opacity:.75; }}
.stButton>button {{ border-radius:12px!important; border:1px solid rgba(0,0,0,.08); padding:8px 14px; }}
.stLinkButton>a {{ border-radius:12px!important; padding:8px 14px!important; border:1px solid rgba(0,0,0,.08)!important;
                   background:#fff!important; color:var(--accent)!important; }}
.stButton>button[kind="primary"] {{ background:var(--accent); color:#fff; border:1px solid rgba({ACCENT_RGB}, .3); }}
.stTabs [data-baseweb="tab-list"] {{ gap:6px; }}
.stTabs [data-baseweb="tab"] {{ border-radius:12px; padding:8px 14px; border:1px solid rgba(0,0,0,.08); background:#fff; }}
</style>
""", unsafe_allow_html=True)

def is_valid_gsheets_url(url:str)->bool:
    if not isinstance(url,str): return False
    return re.match(r"^https://docs\.google\.com/spreadsheets/d/[^/\s]+", url.strip()) is not None

def ensure_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in COLS:
        if c not in df.columns:
            df[c] = "True" if c=="Ativo" else ""
    mask_no_id = (df["ID"].isna()) | (df["ID"].astype(str).str.strip()=="")
    if mask_no_id.any():
        df.loc[mask_no_id,"ID"] = [str(uuid4()) for _ in range(mask_no_id.sum())]
    df["Ativo"] = df["Ativo"].fillna("True").astype(str)
    df["Arquivado_em"] = df["Arquivado_em"].fillna("").astype(str)
    df["Tags"] = df["Tags"].fillna("").astype(str)
    return df[COLS]

def load_db()->pd.DataFrame:
    if DB_PATH.exists():
        df = pd.read_csv(DB_PATH, dtype=str)
        df = ensure_cols(df)
        df.to_csv(DB_PATH, index=False)
        return df
    else:
        df = ensure_cols(pd.DataFrame(columns=COLS))
        df.to_csv(DB_PATH, index=False)
        return df

def save_db(df: pd.DataFrame):
    ensure_cols(df).to_csv(DB_PATH, index=False)

def parse_tags(s:str):
    if not isinstance(s,str) or not s.strip(): return []
    return [t.strip() for t in s.split(",") if t.strip()]

def uniq_sorted(values):
    return sorted({v for v in values if isinstance(v,str) and v.strip()})

def archive_ids(ids):
    if not ids: return
    df = st.session_state.df_links.copy()
    df.loc[df["ID"].isin(ids),"Ativo"]="False"
    df.loc[df["ID"].isin(ids),"Arquivado_em"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_db(df); st.session_state.df_links=df; st.toast(f"🗃️ {len(ids)} link(s) arquivado(s).")

def restore_ids(ids):
    if not ids: return
    df = st.session_state.df_links.copy()
    df.loc[df["ID"].isin(ids),"Ativo"]="True"
    df.loc[df["ID"].isin(ids),"Arquivado_em"]=""
    save_db(df); st.session_state.df_links=df; st.toast(f"♻️ {len(ids)} link(s) restaurado(s).")

def permanent_delete_ids(ids):
    if not ids: return
    df = st.session_state.df_links.copy()
    before=len(df); df=df[~df["ID"].isin(ids)].reset_index(drop=True)
    save_db(df); st.session_state.df_links=df; st.toast(f"🗑️ {before-len(df)} link(s) excluído(s).")

# Estado
if "df_links" not in st.session_state:
    st.session_state.df_links = load_db()
else:
    st.session_state.df_links = ensure_cols(st.session_state.df_links)
    save_db(st.session_state.df_links)
df = st.session_state.df_links

# Header
st.markdown("""
<div class="app-header">
  <h1>📊 Central de Planilhas — Google Sheets</h1>
  <p>Cadastre, filtre, arquive/restaure e gerencie todos os seus links em um só lugar.</p>
</div>
""", unsafe_allow_html=True)

m1,m2,m3 = st.columns(3)
with m1: st.metric("Total", len(df))
with m2: st.metric("Ativas", int((df["Ativo"]=="True").sum()))
with m3: st.metric("Arquivadas", int((df["Ativo"]!="True").sum()))

with st.container(border=True):
    st.subheader("➕ Adicionar nova planilha")
    c1,c2,c3,c4 = st.columns([3,5,3,3])
    nome = c1.text_input("Nome", placeholder="Ex.: Controle de Frota")
    url = c2.text_input("URL do Google Sheets", placeholder="https://docs.google.com/spreadsheets/d/...")
    categoria = c3.text_input("Categoria", placeholder="Operações, Vendas…")
    tags = c4.text_input("Tags (separe por vírgulas)", placeholder="Shopee, LPA-03, Motoristas")
    ativo = st.checkbox("Ativo", value=True)
    if st.button("Salvar link", type="primary"):
        if not nome.strip() or not url.strip():
            st.error("Informe **Nome** e **URL**.")
        elif not is_valid_gsheets_url(url):
            st.error("URL inválida. Use um link de Google Sheets.")
        else:
            row = {
                "ID": str(uuid4()), "Nome": nome.strip(), "URL": url.strip(),
                "Categoria": categoria.strip(), "Tags": tags.strip(),
                "Ativo": "True" if ativo else "False",
                "Criado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Arquivado_em": "" if ativo else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            save_db(df); st.session_state.df_links=df
            st.success(f"✅ '{nome}' adicionada.")

tab1,tab2,tab3 = st.tabs(["📁 Ativas","🗃️ Arquivadas (Lixeira)","🧾 Tabela & Importar"])

def filtros(df_base: pd.DataFrame, show_arch=False)->pd.DataFrame:
    with st.container(border=True):
        st.subheader("🔎 Buscar e filtrar")
        df_base=df_base.copy()
        for col in ["Categoria","Tags"]: 
            if col not in df_base.columns: df_base[col]=""
        all_cats = uniq_sorted(df_base["Categoria"].astype(str).tolist())
        all_tags = sorted({t for s in df_base["Tags"].fillna("").astype(str) for t in parse_tags(s)})
        c1,c2 = st.columns([3,2])
        termo = c1.text_input("Buscar por nome", placeholder="Digite um trecho…", key=f"s_{'arch' if show_arch else 'act'}")
        order = c2.selectbox("Ordenar por", ["Mais recentes","Mais antigas","Nome (A→Z)","Nome (Z→A)"], key=f"o_{'arch' if show_arch else 'act'}")
        c3,c4,c5 = st.columns([2,3,2])
        cat_sel = c3.multiselect("Categoria", all_cats, key=f"c_{'arch' if show_arch else 'act'}")
        tag_sel = c4.multiselect("Tags", all_tags, key=f"t_{'arch' if show_arch else 'act'}")
        if not show_arch:
            only_active = c5.checkbox("Somente ativas", value=True, key="only_active_filter")
            df_base = df_base[df_base["Ativo"]=="True"] if only_active else df_base
        else:
            c5.caption("Exibindo apenas **arquivadas**.")
        view=df_base.copy()
        if termo: view=view[view["Nome"].str.contains(termo, case=False, na=False)]
        if cat_sel: view=view[view["Categoria"].isin(cat_sel)]
        if tag_sel:
            view = view[view["Tags"].apply(lambda s: set(tag_sel).issubset(set(parse_tags(str(s)))) )]
        if "Criado_em" not in view.columns: view["Criado_em"]=""
        if order=="Mais recentes": view=view.sort_values("Criado_em", ascending=False, na_position="last")
        elif order=="Mais antigas": view=view.sort_values("Criado_em", ascending=True, na_position="last")
        elif order=="Nome (A→Z)": view=view.sort_values("Nome", ascending=True, na_position="last")
        else: view=view.sort_values("Nome", ascending=False, na_position="last")
        st.write(f"Exibindo **{len(view)}** planilha(s).")
        return view

def card(row: pd.Series, archived=False):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"**{row['Nome']}**")
    if row.get("Categoria"):
        st.markdown(f'<span class="badge">{row["Categoria"]}</span>', unsafe_allow_html=True)
    t = parse_tags(row.get("Tags",""))
    if t:
        st.markdown(" ".join([f'<span class="chip">{x}</span>' for x in t]), unsafe_allow_html=True)
    meta = f'<div class="meta">Criado em: {row.get("Criado_em","")}'
    if archived and row.get("Arquivado_em"):
        meta += f' &nbsp;•&nbsp; Arquivado em: {row.get("Arquivado_em","")}'
    meta += "</div>"
    st.markdown(meta, unsafe_allow_html=True)
    c1,c2,c3 = st.columns([1.2,1,1.2])
    with c1: st.link_button("🔗 Abrir planilha", row["URL"])
    with c2:
        if not archived:
            with st.popover("🗃️ Arquivar", use_container_width=True):
                st.write(f"Arquivar **{row['Nome']}**?")
                ok = st.checkbox("Confirmo", key=f"a_{row['ID']}")
                if st.button("Confirmar", key=f"ab_{row['ID']}", use_container_width=True):
                    if ok: archive_ids([row["ID"]]); st.rerun()
                    else: st.warning("Confirme antes de arquivar.")
        else:
            if st.button("♻️ Restaurar", key=f"r_{row['ID']}", use_container_width=True):
                restore_ids([row["ID"]]); st.rerun()
    with c3:
        if archived:
            with st.popover("🗑️ Excluir definitivamente", use_container_width=True):
                st.write("Esta ação não pode ser desfeita.")
                ok2 = st.checkbox("Entendo os riscos", key=f"d_{row['ID']}")
                if st.button("Excluir", key=f"db_{row['ID']}", type="secondary", use_container_width=True):
                    if ok2: permanent_delete_ids([row["ID"]]); st.rerun()
                    else: st.warning("Confirme antes de excluir.")
        else:
            st.caption("")
    st.markdown("</div>", unsafe_allow_html=True)

with tab1:
    v = filtros(df[df["Ativo"]=="True"].copy(), show_arch=False)
    if len(v)==0: st.info("Nenhuma planilha encontrada com os filtros aplicados.")
    else:
        cols = st.columns(3)
        for i,(_,row) in enumerate(v.iterrows()):
            with cols[i%3]: card(row, archived=False)

with tab2:
    v = filtros(df[df["Ativo"]!="True"].copy(), show_arch=True)
    if len(v)==0: st.info("Nenhuma planilha arquivada.")
    else:
        cols = st.columns(3)
        for i,(_,row) in enumerate(v.iterrows()):
            with cols[i%3]: card(row, archived=True)

with tab3:
    st.subheader("🧾 Edição em tabela")
    table_df = df.copy()
    if "Tags" not in table_df.columns: table_df["Tags"]=""
    table_df["Selecionar"]=False
    edited = st.data_editor(
        table_df, use_container_width=True, num_rows="dynamic",
        column_config={
            "ID": st.column_config.TextColumn(disabled=True, width="small"),
            "Nome": st.column_config.TextColumn(required=True, width="medium"),
            "URL": st.column_config.LinkColumn(required=True, width="large"),
            "Categoria": st.column_config.TextColumn(width="small"),
            "Tags": st.column_config.TextColumn(help="Separe por vírgulas", width="medium"),
            "Ativo": st.column_config.SelectboxColumn(options=["True","False"], width="small"),
            "Criado_em": st.column_config.TextColumn(width="small", help="Preenchido automaticamente"),
            "Arquivado_em": st.column_config.TextColumn(width="small"),
            "Selecionar": st.column_config.CheckboxColumn(help="Marque para ação em lote", width="small"),
        }
    )
    a1,a2,a3,a4 = st.columns([1.2,1.2,1.4,2.2])
    with a1:
        if st.button("💾 Salvar alterações", type="primary", use_container_width=True):
            if edited["Nome"].isna().any() or (edited["Nome"].astype(str).str.strip()=="").any():
                st.error("Há linhas com **Nome** vazio.")
            elif (~edited["URL"].apply(is_valid_gsheets_url)).any():
                st.error("Há URLs inválidas. Corrija antes de salvar.")
            else:
                mask_no_id = (edited["ID"].isna()) | (edited["ID"].astype(str).str.strip()=="")
                if mask_no_id.any():
                    edited.loc[mask_no_id,"ID"] = [str(uuid4()) for _ in range(mask_no_id.sum())]
                save_db(edited.drop(columns=["Selecionar"], errors="ignore"))
                st.session_state.df_links = load_db()
                st.success("Alterações salvas.")
    with a2:
        if st.button("🗃️ Arquivar selecionados", use_container_width=True):
            ids = edited.loc[edited["Selecionar"]==True,"ID"].dropna().astype(str).tolist()
            if not ids: st.warning("Nenhuma linha selecionada.")
            else: archive_ids(ids); st.rerun()
    with a3:
        if st.button("♻️ Restaurar selecionados", use_container_width=True):
            ids = edited.loc[edited["Selecionar"]==True,"ID"].dropna().astype(str).tolist()
            if not ids: st.warning("Nenhuma linha selecionada.")
            else: restore_ids(ids); st.rerun()
    with a4:
        if st.button("🗑️ Excluir permanentemente selecionados", use_container_width=True):
            ids = edited.loc[edited["Selecionar"]==True,"ID"].dropna().astype(str).tolist()
            if not ids: st.warning("Nenhuma linha selecionada.")
            else: permanent_delete_ids(ids); st.rerun()

    st.divider()
    cexp, cup = st.columns([1,1])
    with cexp:
        st.download_button(
            "⬇️ Exportar CSV",
            data=edited.drop(columns=["Selecionar"], errors="ignore").to_csv(index=False).encode("utf-8"),
            file_name="links_export.csv", mime="text/csv", use_container_width=True
        )
    with cup:
        up = st.file_uploader("📥 Importar/mesclar CSV", type=["csv"])
        if up is not None:
            try:
                new_df = pd.read_csv(up, dtype=str)
                new_df = ensure_cols(new_df)
                base = st.session_state.df_links.copy()
                merged = pd.concat([base, new_df], ignore_index=True)
                merged = merged.drop_duplicates(subset=["ID"], keep="last").reset_index(drop=True)
                save_db(merged); st.session_state.df_links = load_db()
                st.success(f"Importação concluída. Total agora: {len(merged)}.")
            except Exception as e:
                st.error(f"Falha ao importar: {e}")

st.caption("💡 Dica: versionar o arquivo `links_db.csv` no Git ajuda a manter histórico de alterações.")
