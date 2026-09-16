import streamlit as st
import pandas as pd

# Configuración de la página web
st.set_page_config(page_title="Reporte de Notas de Crédito", layout="wide")

# --- 🔒 SISTEMA DE LOGIN ---
PASSWORD_CORRECTA = "admin123" 

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acceso al Sistema de Reportes")
    st.write("Por favor, ingresa la contraseña para continuar.")
    
    password_ingresada = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        if password_ingresada == PASSWORD_CORRECTA:
            st.session_state.autenticado = True
            st.rerun() 
        else:
            st.error("Contraseña incorrecta. Intenta nuevamente.")
    
    st.stop() 

# --- 📊 APLICACIÓN PRINCIPAL ---
st.title("📊 Generador de Reportes Trimestrales (NC)")

tab_carga, tab_comparativa, tab_acumulado = st.tabs([
    "Carga de Archivos", "Comparativa Histórica", "Acumulado Anual"
])

with tab_carga:
    st.header("1. Carga de Archivos del Trimestre")
    file_fcp = st.file_uploader("Subir archivo de Facturación (ej. FCP2026T1.xlsx)", type=['xlsx'])
    file_nc = st.file_uploader("Subir archivo de Notas de Crédito (ej. NC2026T1.xlsx)", type=['xlsx'])
    file_historico = st.file_uploader("Subir archivo Histórico Base (ej. NC2026 T1 v2.xlsx)", type=['xlsx'])
    
    if st.button("Procesar y Generar Reporte"):
        if file_fcp and file_nc and file_historico:
            st.success("¡Archivos cargados! (Listo para procesar la información).")
        else:
            st.warning("Por favor, sube los 3 archivos Excel para continuar.")

with tab_comparativa:
    st.header("Comparativa Trimestre a Trimestre")

with tab_acumulado:
    st.header("Acumulado Anual")
    
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()
