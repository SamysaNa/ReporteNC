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
    file_fcp = st.file_uploader("Subir archivo de Facturación", type=['xlsx'])
    file_nc = st.file_uploader("Subir archivo de Notas de Crédito", type=['xlsx'])
    file_historico = st.file_uploader("Subir archivo Histórico Base", type=['xlsx'])
    
    if st.button("Procesar y Generar Reporte"):
        if file_fcp and file_nc and file_historico:
            try:
                df_ventas = pd.read_excel(file_fcp)
                df_nc = pd.read_excel(file_nc)
                
                # Estandarizar columnas a minúsculas
                df_ventas.columns = df_ventas.columns.str.lower().str.strip()
                df_nc.columns = df_nc.columns.str.lower().str.strip()

                # Filtro Antiduplicados
                if 'numero de comprobante' in df_ventas.columns:
                    df_ventas = df_ventas.drop_duplicates(subset=['numero de comprobante'], keep='first')
                if 'numero de comprobante' in df_nc.columns:
                    df_nc = df_nc.drop_duplicates(subset=['numero de comprobante'], keep='first')

                # Verificar que exista la columna de fechas para extraer el mes
                if 'fecha' in df_ventas.columns and 'fecha' in df_nc.columns:
                    df_ventas['mes'] = pd.to_datetime(df_ventas['fecha']).dt.month
                    df_nc['mes'] = pd.to_datetime(df_nc['fecha']).dt.month

                    # Agrupar sumando el total bruto por mes
                    v_mes = df_ventas.groupby('mes')['total bruto'].sum().reset_index()
                    nc_mes = df_nc.groupby('mes')['total bruto'].sum().reset_index()

                    # Cruzar datos y calcular porcentaje
                    calculo = pd.merge(v_mes, nc_mes, on='mes', how='left', suffixes=('_venta', '_nc'))
                    calculo['total bruto_nc'] = calculo['total bruto_nc'].fillna(0)
                    calculo['2026'] = (calculo['total bruto_nc'] / calculo['total bruto_venta'])

                    # Armar estructura visual (Enero-Diciembre)
                    meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
                    df_final = pd.DataFrame({"% NC SOBRE EL TOTAL DE LA VENTA": meses, "mes": range(1, 13)})
                    df_final = pd.merge(df_final, calculo[['mes', '2026']], on='mes', how='left')

                    # Formato visual de porcentaje
                    df_final['2026'] = df_final['2026'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "")

                    st.success("Cálculos procesados correctamente.")
                    st.dataframe(df_final[['% NC SOBRE EL TOTAL DE LA VENTA', '2026']])

                else:
                    st.error("No se encontró la columna 'fecha' en los Excel. El cálculo no puede realizarse.")

            except Exception as e:
                st.error(f"Ocurrió un error al procesar la información: {e}")
        else:
            st.warning("Por favor sube los 3 archivos.")
with tab_comparativa:
    st.header("Comparativa Trimestre a Trimestre")
    st.info("Aquí aparecerá el gráfico comparativo.")

with tab_acumulado:
    st.header("Acumulado Anual")
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()
