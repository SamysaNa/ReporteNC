import io
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Reporte de Notas de Crédito", layout="wide")

def formato_arg(numero):
    if pd.isna(numero) or numero == 0:
        return "0,00"
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def color_variacion(val):
    if pd.isna(val) or val == "":
        return ""
    try:
        num = float(str(val).replace('%', '').replace(',', '.'))
        if num > 0:
            return 'color: red'
        elif num < 0:
            return 'color: green'
    except:
        pass
    return ""

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
    "Carga de Archivos", "Comparativa Histórica", "Acumulado Anual", "Top 10 Clientes", "Motivos", "Error de Carga"
])

# --- SOLAPA 1: CARGA DE ARCHIVOS ---
with tab_carga:
    st.header("1. Carga de Archivos (Mismo Formato)")
    col1, col2, col3 = st.columns(3)
    with col1: file_fcp = st.file_uploader("Facturación 2026", type=['xlsx'])
    with col2: file_nc = st.file_uploader("Notas de Crédito 2026", type=['xlsx'])
    with col3: file_historico = st.file_uploader("Histórico 2025", type=['xlsx'])
    
    if st.button("Procesar y Generar Reporte"):
        if file_fcp and file_nc and file_historico:
            try:
                # Lectura 
                df_ventas = pd.read_excel(file_fcp, header=2)
                df_nc = pd.read_excel(file_nc, header=2)
                df_hist = pd.read_excel(file_historico, header=2)
                
                # Estandarizar columnas
                for df in [df_ventas, df_nc, df_hist]:
                    df.columns = (df.columns.str.lower()
                                  .str.strip()
                                  .str.replace('ú', 'u')
                                  .str.replace('í', 'i')
                                  .str.replace('ó', 'o')
                                  .str.replace('á', 'a')
                                  .str.replace('é', 'e'))

                col_comprobante = 'numero' 
                col_monto = 'importe total origen'
                col_fecha = 'fecha'
                col_tipo = 'tipo'
                
                # Seguridad de columnas
                if col_comprobante not in df_ventas.columns or col_fecha not in df_ventas.columns:
                    st.error("No se encontraron las columnas 'fecha' o 'numero'. Revisa el header=2.")
                    st.stop()

                # Antiduplicados
                df_ventas = df_ventas.drop_duplicates(subset=[col_comprobante], keep='first')
                df_nc = df_nc.drop_duplicates(subset=[col_comprobante], keep='first')
                df_hist = df_hist.drop_duplicates(subset=[col_comprobante], keep='first')

                # Filtrar Histórico >= 01/01/2025
                df_hist[col_fecha] = pd.to_datetime(df_hist[col_fecha], errors='coerce')
                df_hist = df_hist[df_hist[col_fecha] >= '2025-01-01']
                
                if col_tipo in df_hist.columns:
                    df_hist_nc = df_hist[df_hist[col_tipo].astype(str).str.contains('NC', case=False, na=False)]
                    df_hist_v = df_hist[~df_hist[col_tipo].astype(str).str.contains('NC|ND', case=False, na=False)]
                else:
                    df_hist_nc = df_hist 
                    df_hist_v = pd.DataFrame(columns=df_hist.columns)

                # Guardar en sesión
                st.session_state['d_nc26'] = df_nc
                st.session_state['d_v26'] = df_ventas
                st.session_state['d_nc25'] = df_hist_nc
                st.session_state['d_v25'] = df_hist_v
                
                st.success("¡Datos procesados! Revisa las solapas.")

            except Exception as e:
                st.error(f"Error procesando: {e}")
        else:
            st.warning("Faltan archivos por subir.")

# --- LÓGICA DE SOLAPAS ---
if 'd_nc26' in st.session_state:
    d_nc26 = st.session_state['d_nc26']
    d_v26 = st.session_state['d_v26']
    d_nc25 = st.session_state['d_nc25']
    d_v25 = st.session_state['d_v25']
    
    col_comprobante = 'numero'
    col_monto = 'importe total origen'
    col_fecha = 'fecha'
    
    meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    # --- FUNCIONES MATEMÁTICAS ---
    def calcular_mensual(df_v, df_nc):
        df_v['mes'] = pd.to_datetime(df_v[col_fecha]).dt.month
        df_nc['mes'] = pd.to_datetime(df_nc[col_fecha]).dt.month
        
        v_mes = df_v.groupby('mes')[col_monto].sum().reset_index()
        nc_mes = df_nc.groupby('mes')[col_monto].sum().reset_index()
        
        calc = pd.merge(pd.DataFrame({'mes': range(1, 13)}), v_mes, on='mes', how='left').rename(columns={col_monto: 'ventas'})
        calc = pd.merge(calc, nc_mes, on='mes', how='left').rename(columns={col_monto: 'nc'})
        calc.fillna(0, inplace=True)
        calc['pct'] = np.where(calc['ventas'] > 0, calc['nc'] / calc['ventas'], 0)
        return calc

    # --- SOLAPA: COMPARATIVA HISTÓRICA ---
    with tab_comparativa:
        st.header("Comparativa Trimestre a Trimestre / Año a Año")
        
        calc_25 = calcular_mensual(d_v25, d_nc25)
        calc_26 = calcular_mensual(d_v26, d_nc26)
        
        # Armar tabla comparativa
        df_comp = pd.DataFrame({'Mes': meses_nombres})
        df_comp['% NC 2025'] = calc_25['pct']
        df_comp['% NC 2026'] = calc_26['pct']
        
        # Calcular variación (2026 - 2025)
        df_comp['Variación Año/Año'] = df_comp['% NC 2026'] - df_comp['% NC 2025']
        
        # Formatear a texto para visualización
        df_comp_vis = df_comp.copy()
        df_comp_vis['% NC 2025'] = df_comp_vis['% NC 2025'].apply(lambda x: f"{x*100:.2f}%" if x != 0 else "-")
        df_comp_vis['% NC 2026'] = df_comp_vis['% NC 2026'].apply(lambda x: f"{x*100:.2f}%" if x != 0 else "-")
        df_comp_vis['Variación Año/Año'] = df_comp_vis['Variación Año/Año'].apply(
            lambda x: f"🔴 +{x*100:.2f}%" if x > 0 else (f"🟢 {x*100:.2f}%" if x < 0 else "-")
        )
        
        # Limpiar filas vacías (donde ni 2025 ni 2026 tienen datos)
        df_comp_vis = df_comp_vis[(df_comp_vis['% NC 2025'] != "-") | (df_comp_vis['% NC 2026'] != "-")]
        
        # SOLUCIÓN APLICADA AQUÍ: Cambio applymap por map
        st.dataframe(df_comp_vis.style.map(color_variacion, subset=['Variación Año/Año']), use_container_width=True)
        
        if st.button("💾 Guardar Información en Google Sheets"):
            st.success("API de Google pendiente de configuración.")

    # --- SOLAPA: ACUMULADO ANUAL ---
    with tab_acumulado:
        st.header("Acumulado Anual 2026")
        
        calc_26 = calcular_mensual(d_v26, d_nc26)
        
        tot_v = calc_26['ventas'].sum()
        tot_nc = calc_26['nc'].sum()
        pct_tot = (tot_nc / tot_v) if tot_v > 0 else 0
        
        # Métricas principales
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Facturado (2026)", f"$ {formato_arg(tot_v)}")
        col2.metric("Total NC (2026)", f"$ {formato_arg(tot_nc)}")
        col3.metric("% NC Acumulado", f"{pct_tot*100:.2f}%")
        
        # Detalle mensual 2026
        st.subheader("Detalle Mensual")
        df_acu = pd.DataFrame({'Mes': meses_nombres})
        df_acu['Ventas'] = calc_26['ventas'].apply(lambda x: f"$ {formato_arg(x)}")
        df_acu['NC'] = calc_26['nc'].apply(lambda x: f"$ {formato_arg(x)}")
        df_acu['% NC'] = calc_26['pct'].apply(lambda x: f"{x*100:.2f}%" if x != 0 else "-")
        
        df_acu = df_acu[df_acu['Ventas'] != "$ 0,00"] # Ocultar meses futuros
        st.table(df_acu)

    # --- SOLAPAS DE GRÁFICOS (Ya validadas) ---
    with tab_top10:
        st.header("Top 10 Clientes con más Notas de Crédito")
        col_cliente = 'nombre cliente'
        if col_cliente in d_nc26.columns:
            top10 = d_nc26.groupby(col_cliente).agg(Cantidad=(col_comprobante, 'count'), Total_Bruto=(col_monto, 'sum')).reset_index().sort_values('Cantidad', ascending=False).head(10)
            top10_v = top10.copy()
            top10_v['Total_Bruto'] = top10_v['Total_Bruto'].apply(lambda x: f"$ {formato_arg(x)}")
            st.table(top10_v)
            st.bar_chart(data=top10, x=col_cliente, y='Cantidad')

    with tab_motivo:
        st.header("Análisis por Motivo")
        col_motivo = 'referencia 1'
        if col_motivo in d_nc26.columns:
            motivos = d_nc26.groupby(col_motivo).agg(Cantidad=(col_comprobante, 'count'), Total_Bruto=(col_monto, 'sum')).reset_index().sort_values('Cantidad', ascending=False)
            motivos_v = motivos.copy()
            motivos_v['Total_Bruto'] = motivos_v['Total_Bruto'].apply(lambda x: f"$ {formato_arg(x)}")
            st.table(motivos_v)
            st.bar_chart(data=motivos, x=col_motivo, y='Cantidad')

    with tab_error:
        st.header("Análisis por Error de Carga (Cobrador)")
        col_cobrador = 'cobrador cliente'
        if col_cobrador in d_nc26.columns:
            errores = d_nc26.groupby(col_cobrador).agg(Cantidad=(col_comprobante, 'count'), Total_Bruto=(col_monto, 'sum')).reset_index().sort_values('Cantidad', ascending=False)
            errores_v = errores.copy()
            errores_v['Total_Bruto'] = errores_v['Total_Bruto'].apply(lambda x: f"$ {formato_arg(x)}")
            st.table(errores_v)
            st.bar_chart(data=errores, x=col_cobrador, y='Cantidad')
