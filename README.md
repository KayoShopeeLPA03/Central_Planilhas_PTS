# Central de Planilhas (Streamlit) 

App Streamlit para centralizar links de Google Sheets com:
- cadastro/edição, tags, categorias
- arquivar/restaurar (lixeira) e exclusão definitiva
- import/export CSV
- persistência local em `links_db.csv` (ignorado no git por padrão)

## Rodar localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estrutura
```
.
├─ app.py
├─ requirements.txt
├─ .gitignore
└─ .streamlit/
   └─ config.toml
```


