import streamlit as st
from pathlib import Path

fase0 = next(Path("pages").glob("02_*_Fase_0_Portafolio.py"), None)
if fase0:
    st.switch_page(str(fase0))
else:
    st.title("Inicio")
    st.error("No se encontró la página de Fase 0. Verifica la estructura en la carpeta `pages`.")
