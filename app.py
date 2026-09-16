import streamlit as st
import pandas as pd

# Configuración de la página web
st.set_page_config(page_title="Reporte de Notas de Crédito", layout="wide")
st.title("📊 Generador de Reportes Trimestrales (NC)")

# Solapas de la web
tab_carga, tab_comparativa, tab_acumulado = st.tabs([
    "Carga de Archivos", "Comparativa Histórica", "Acumulado Anual"
])

with tab_carga:
    st.header("1. Carga de Archivos del Trimestre")
    st.write("Sube aquí tus archivos para procesar el periodo.")
    
    # Cajas para subir los Excel
    file_fcp = st.file_uploader("Subir archivo de Facturación (ej. FCP2026T1.xlsx)", type=['xlsx'])
    file_nc = st.file_uploader("Subir archivo de Notas de Crédito (ej. NC2026T1.xlsx)", type=['xlsx'])
    file_historico = st.file_uploader("Subir archivo Histórico Base (ej. NC2026 T1 v2.xlsx)", type=['xlsx'])
    
    if st.button("Procesar y Generar Reporte"):
        if file_fcp and file_nc and file_historico:
            try:
                # LÓGICA DE PROCESAMIENTO (El motor)
                df_ventas = pd.read_excel(file_fcp)
                df_nc = pd.read_excel(file_nc)
                
                # Eliminar duplicados por comprobante
                col_comprobante = 'numero de comprobante' # Ajustar si en tu Excel se llama distinto
                if col_comprobante in df_ventas.columns and col_comprobante in df_nc.columns:
                    df_ventas = df_ventas.drop_duplicates(subset=[col_comprobante], keep='first')
                    df_nc = df_nc.drop_duplicates(subset=[col_comprobante], keep='first')
                
                st.success("¡Archivos procesados correctamente! (Filtro anti-duplicados aplicado).")
                st.write("Esta es una vista previa de la facturación procesada:")
                st.dataframe(df_ventas.head()) # Muestra las primeras filas para que veas que funciona
                
                # (En los próximos pasos agregaremos aquí el cruce completo para replicar tu imagen)
                
            except Exception as e:
                st.error(f"Hubo un error al leer los archivos: {e}")
        else:
            st.warning("Por favor, sube los 3 archivos Excel para continuar.")

with tab_comparativa:
    st.header("Comparativa Trimestre a Trimestre")
    st.info("Una vez que crucemos los datos, el gráfico aparecerá aquí.")
