import streamlit as st
import pandas as pd
import datetime

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
            try:
                # 1. Leer los archivos Excel
                df_ventas = pd.read_excel(file_fcp)
                df_nc = pd.read_excel(file_nc)
                
                # 2. Convertir los nombres de las columnas a minúsculas para evitar errores
                df_ventas.columns = df_ventas.columns.str.lower().str.strip()
                df_nc.columns = df_nc.columns.str.lower().str.strip()

                # 3. FILTRO ANTI-DUPLICADOS (Por número de comprobante)
                if 'numero de comprobante' in df_ventas.columns:
                    df_ventas = df_ventas.drop_duplicates(subset=['numero de comprobante'], keep='first')
                if 'numero de comprobante' in df_nc.columns:
                    df_nc = df_nc.drop_duplicates(subset=['numero de comprobante'], keep='first')

                # 4. Mostrar Resultados en Pantalla
                st.success("¡Archivos procesados! El filtro anti-duplicados funcionó correctamente.")
                
                st.write("### Resumen de Facturación (Sin Duplicados)")
                # Mostramos cuánto suma el total bruto de ventas
                if 'total bruto' in df_ventas.columns:
                    total_ventas = df_ventas['total bruto'].sum()
                    st.metric(label="Suma Total Bruto (Ventas)", value=f"$ {total_ventas:,.2f}")
                st.dataframe(df_ventas.head()) # Muestra las primeras 5 filas para comprobar

                st.write("### Resumen de Notas de Crédito (Sin Duplicados)")
                # Mostramos cuánto suma el total bruto de NC
                if 'total bruto' in df_nc.columns:
                    total_nc = df_nc['total bruto'].sum()
                    st.metric(label="Suma Total Bruto (Notas de Crédito)", value=f"$ {total_nc:,.2f}")
                st.dataframe(df_nc.head())

            except Exception as e:
                st.error(f"Hubo un error al procesar las columnas: {e}")
                st.info("Asegúrate de que los Excel tengan una columna llamada 'numero de comprobante' y 'total bruto'.")
        else:
            st.warning("Por favor, sube los 3 archivos Excel para continuar.")

with tab_comparativa:
    st.header("Comparativa Trimestre a Trimestre")
    st.info("Aquí aparecerá el gráfico comparativo.")

with tab_acumulado:
    st.header("Acumulado Anual")
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()
