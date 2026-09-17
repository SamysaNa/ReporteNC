import io
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Reporte de Notas de Crédito", layout="wide")

def formato_arg(numero):
    if pd.isna(numero) or numero == 0:
        return "0,00"
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- 🔒 SISTEMA DE LOGIN ---
PASSWORD_CORRECTA = "admin123" 
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acceso al Sistema de Reportes")
    password_ingresada = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if password_ingresada == PASSWORD_CORRECTA:
            st.session_state.autenticado = True
            st.rerun() 
        else:
            st.error("Contraseña incorrecta.")
    st.stop() 

# --- 📊 APLICACIÓN PRINCIPAL ---
st.title("📊 Generador de Reportes Trimestrales (NC)")

tab_carga, tab_comparativa, tab_acumulado, tab_top10, tab_motivo, tab_error = st.tabs([
    "Carga de Archivos", "Comparativa Histórica", "Acumulado", "Top 10 Clientes", "Motivos", "Error de Carga"
])

with tab_carga:
    st.header("1. Carga de Archivos (Mismo Formato)")
    col1, col2, col3 = st.columns(3)
    with col1: file_fcp = st.file_uploader("Facturación 2026", type=['xlsx'])
    with col2: file_nc = st.file_uploader("Notas de Crédito 2026", type=['xlsx'])
    with col3: file_historico = st.file_uploader("Histórico 2025 (Todos los doc.)", type=['xlsx'])
    
    if st.button("Procesar y Generar Reporte"):
        if file_fcp and file_nc and file_historico:
           try:
                # 1. Lectura de archivos 
                # (NOTA: Si tus títulos ahora están en la FILA 1 del Excel, cambia los tres "header=2" por "header=0")
                df_ventas = pd.read_excel(file_fcp, header=2)
                df_nc = pd.read_excel(file_nc, header=2)
                df_hist = pd.read_excel(file_historico, header=2)
                
                # 2. Estandarizar columnas: minúsculas, sin espacios extra y quitamos las tildes
                for df in [df_ventas, df_nc, df_hist]:
                    df.columns = (df.columns.str.lower()
                                  .str.strip()
                                  .str.replace('ú', 'u')
                                  .str.replace('í', 'i')
                                  .str.replace('ó', 'o')
                                  .str.replace('á', 'a')
                                  .str.replace('é', 'e'))

                # Nombres "seguros" (sin tildes)
                col_comprobante = 'numero' 
                col_monto = 'importe total origen'
                col_fecha = 'fecha'
                col_tipo = 'tipo'
                
                # VERIFICACIÓN DE SEGURIDAD ANTES DE AVANZAR
                columnas_faltantes = []
                if col_comprobante not in df_ventas.columns: columnas_faltantes.append(col_comprobante)
                if col_fecha not in df_ventas.columns: columnas_faltantes.append(col_fecha)

                if columnas_faltantes:
                    st.error(f"Faltan estas columnas en el Excel: {columnas_faltantes}")
                    st.warning(f"Las columnas que el sistema SÍ está leyendo son: {list(df_ventas.columns)}")
                    st.info("💡 Si la lista de arriba muestra números o datos en lugar de tus títulos, cambia 'header=2' por 'header=0' en el código.")
                    st.stop() # Detenemos el proceso acá para no tirar errores rojos raros

                # 3. Antiduplicados
                df_ventas = df_ventas.drop_duplicates(subset=[col_comprobante], keep='first')
                df_nc = df_nc.drop_duplicates(subset=[col_comprobante], keep='first')
                df_hist = df_hist.drop_duplicates(subset=[col_comprobante], keep='first')

                # 4. Procesar Histórico 2025 (Filtro fecha >= 01/01/2025)
                df_hist[col_fecha] = pd.to_datetime(df_hist[col_fecha], errors='coerce')
                df_hist = df_hist[df_hist[col_fecha] >= '2025-01-01']
                
                # Separar NC de Facturas en el histórico
                if col_tipo in df_hist.columns:
                    df_hist_nc = df_hist[df_hist[col_tipo].astype(str).str.contains('NC', case=False, na=False)]
                    df_hist_ventas = df_hist[~df_hist[col_tipo].astype(str).str.contains('NC|ND', case=False, na=False)]
                else:
                    df_hist_nc = df_hist 
                    df_hist_ventas = pd.DataFrame(columns=df_hist.columns)

                # 5. Guardar datos puros en sesión para las demás solapas
                st.session_state['datos_nc_2026'] = df_nc
                st.session_state['datos_v_2026'] = df_ventas
                st.session_state['datos_hist_nc'] = df_hist_nc
                st.session_state['datos_hist_ventas'] = df_hist_ventas
                
                st.success("¡Cálculos procesados correctamente! Navega por las solapas para ver los resultados.")

            except Exception as e:
                st.error(f"Error técnico procesando: {e}")

# --- LÓGICA DE SOLAPAS ---

if 'datos_nc_2026' in st.session_state:
    df_nc = st.session_state['datos_nc_2026']
    col_comprobante = 'número'
    col_monto = 'importe total origen'
    
    with tab_comparativa:
        st.header("Comparativa Histórica")
        st.info("Aquí cruzaremos los porcentajes mensuales de 2025 (desde el archivo crudo) vs 2026.")
        
        # Botón para guardar en Sheets (Simulado por ahora)
        if st.button("💾 Guardar Información en Google Sheets"):
            st.success("Los datos están listos para enviarse. Próximamente conectaremos la API de Google.")

    with tab_acumulado:
        st.header("Acumulado Anual")
        st.write("Datos en construcción...")

    with tab_top10:
        st.header("Top 10 Clientes con más Notas de Crédito")
        col_cliente = 'nombre cliente'
        if col_cliente in df_nc.columns:
            top10 = df_nc.groupby(col_cliente).agg(
                Cantidad=(col_comprobante, 'count'),
                Total_Bruto=(col_monto, 'sum')
            ).reset_index().sort_values('Cantidad', ascending=False).head(10)
            
            top10_visual = top10.copy()
            top10_visual['Total_Bruto'] = top10_visual['Total_Bruto'].apply(lambda x: f"$ {formato_arg(x)}")
            st.table(top10_visual)
            st.bar_chart(data=top10, x=col_cliente, y='Cantidad')
        else:
            st.error(f"No se encontró la columna '{col_cliente}' en el archivo de NC.")

    with tab_motivo:
        st.header("Análisis por Motivo")
        col_motivo = 'referencia 1'
        if col_motivo in df_nc.columns:
            motivos = df_nc.groupby(col_motivo).agg(
                Cantidad=(col_comprobante, 'count'),
                Total_Bruto=(col_monto, 'sum')
            ).reset_index().sort_values('Cantidad', ascending=False)
            
            motivos_visual = motivos.copy()
            motivos_visual['Total_Bruto'] = motivos_visual['Total_Bruto'].apply(lambda x: f"$ {formato_arg(x)}")
            st.table(motivos_visual)
            st.bar_chart(data=motivos, x=col_motivo, y='Cantidad')
        else:
            st.error(f"No se encontró la columna '{col_motivo}'.")

    with tab_error:
        st.header("Análisis por Error de Carga (Cobrador)")
        col_cobrador = 'cobrador cliente'
        if col_cobrador in df_nc.columns:
            errores = df_nc.groupby(col_cobrador).agg(
                Cantidad=(col_comprobante, 'count'),
                Total_Bruto=(col_monto, 'sum')
            ).reset_index().sort_values('Cantidad', ascending=False)
            
            errores_visual = errores.copy()
            errores_visual['Total_Bruto'] = errores_visual['Total_Bruto'].apply(lambda x: f"$ {formato_arg(x)}")
            st.table(errores_visual)
            st.bar_chart(data=errores, x=col_cobrador, y='Cantidad')
        else:
            st.error(f"No se encontró la columna '{col_cobrador}'.")
            
else:
    for tab in [tab_comparativa, tab_acumulado, tab_top10, tab_motivo, tab_error]:
        with tab:
            st.info("Por favor, sube y procesa los archivos en la primera solapa.")
