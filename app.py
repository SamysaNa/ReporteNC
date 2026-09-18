import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import io
import xlsxwriter
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Reporte de Notas de Crédito", layout="wide")

# --- ESTILOS CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Nunito', sans-serif !important; }
button[role="tab"] { background-color: transparent !important; border: none !important; border-bottom: 5px solid transparent !important; padding-bottom: 10px !important; margin-right: 20px !important; }
button[role="tab"] p { font-size: 2rem !important; font-weight: 900 !important; color: #a0aec0 !important; transition: all 0.2s ease; }
button[role="tab"][aria-selected="true"] { border-bottom: 5px solid #ff4b4b !important; }
button[role="tab"][aria-selected="true"] p { color: #ff4b4b !important; font-size: 2.1rem !important; }
h2 { font-size: 1.8rem !important; font-weight: 900 !important; color: #2d3748 !important; margin-top: 1rem !important; margin-bottom: 0.5rem !important; }
.kpi-card { background-color: white; border-radius: 12px; padding: 15px; text-align: center; border: 2px solid #e2e8f0; height: 100%; display: flex; flex-direction: column; justify-content: center;}
.kpi-rojo { border-color: #ff4b4b; color: #ff4b4b; background-color: rgba(255, 75, 75, 0.05); }
.kpi-titulo { font-size: 13px; font-weight: 900; text-transform: uppercase; }
.kpi-valor { font-size: 26px; font-weight: 900; }
.tabla-canchera { width: 100%; display: flex; flex-direction: column; margin-bottom: 20px; }
.fila-header { display: flex; width: 100%; border-bottom: 2px solid #edf2f7; padding: 2px 10px; margin-bottom: 4px; }
.celda-header-titulo { flex: 0 0 110px; font-size: 0.75rem; font-weight: 900; color: #718096; text-transform: uppercase; text-align: left; }
.celda-header-valor { flex: 1; text-align: right; font-size: 0.75rem; font-weight: 900; color: #718096; text-transform: uppercase; padding-right: 15px;}
.fila-canchera { display: flex; width: 100%; align-items: center; background: #ffffff; border-radius: 8px; padding: 2px 10px; margin-bottom: 5px; transition: transform 0.1s; border: 1px solid #edf2f7;}
.fila-canchera:hover { transform: scale(1.01); }
.celda-titulo { flex: 0 0 110px; font-weight: 800; color: #2d3748; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: left; }
.celda-valor { flex: 1; display: flex; justify-content: flex-end; }
.badge { width: 100%; max-width: 95px; padding: 2px 6px; border-radius: 6px; font-weight: 800; font-size: 0.85rem; display: flex; align-items: center; justify-content: flex-end; gap: 4px; text-align: right; white-space: nowrap;}
.badge-neutral { background: transparent; color: #4a5568; }
.badge-alerta { background: rgba(255, 75, 75, 0.12); color: #c53030; }
.badge-warn { background: rgba(255, 193, 7, 0.15); color: #b8860b; }
.badge-ok { background: rgba(40, 167, 69, 0.12); color: #22543d; }
</style>
""", unsafe_allow_html=True)

PALETA_COLORES = ['#ff1a1a', '#ff5555', '#ff7f50', '#ffa07a', '#ffb347', '#ffd700', '#d4e157', '#9ece6a', '#48c774', '#20b2aa']
ID_DEL_SHEET = "101j4mRqe6KPhM1htOKqHJxYUKcTalDHosEZF-MalrPY"

# --- FUNCIONES DE BASE DE DATOS (GOOGLE SHEETS) ---
def conectar_google():
    if "gcp_service_account" not in st.secrets: return None, "Falta configurar credenciales (Secrets)."
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client.open_by_key(ID_DEL_SHEET), "Conexión exitosa"

def guardar_base_completa_en_sheets(dict_dfs):
    sheet_doc, msg = conectar_google()
    if not sheet_doc: return False, msg
    try:
        for nombre_hoja, df in dict_dfs.items():
            df_str = df.copy()
            for col in df_str.select_dtypes(include=['datetime', 'datetimetz']).columns:
                df_str[col] = df_str[col].dt.strftime('%Y-%m-%d')
            df_str = df_str.fillna("")
            try: worksheet = sheet_doc.worksheet(nombre_hoja)
            except gspread.exceptions.WorksheetNotFound: worksheet = sheet_doc.add_worksheet(title=nombre_hoja, rows="100", cols="20")
            worksheet.clear()
            worksheet.update([df_str.columns.values.tolist()] + df_str.astype(str).values.tolist())
        return True, "Base de datos sincronizada en la nube."
    except Exception as e: return False, str(e)

def cargar_base_desde_sheets():
    sheet_doc, msg = conectar_google()
    if not sheet_doc: return False, msg
    try:
        st.session_state['d_nc26_raw'] = pd.DataFrame(sheet_doc.worksheet("BD_NC_26").get_all_records())
        st.session_state['d_v26_raw'] = pd.DataFrame(sheet_doc.worksheet("BD_Ventas_26").get_all_records())
        st.session_state['d_nc25_raw'] = pd.DataFrame(sheet_doc.worksheet("BD_NC_25").get_all_records())
        st.session_state['d_v25_raw'] = pd.DataFrame(sheet_doc.worksheet("BD_Ventas_25").get_all_records())
        
        for key in ['d_nc26_raw', 'd_v26_raw', 'd_nc25_raw', 'd_v25_raw']:
            if 'fecha' in st.session_state[key].columns:
                st.session_state[key]['fecha'] = pd.to_datetime(st.session_state[key]['fecha'], errors='coerce')
                st.session_state[key]['mes'] = st.session_state[key]['fecha'].dt.month
        return True, "Información descargada exitosamente."
    except Exception as e: return False, f"Error descargando: {e}"

# --- FUNCIONES DE EXCEL AVANZADO ---
def generar_excel_avanzado(df_nc, df_v):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    fmt_header = workbook.add_format({'bold': True, 'bg_color': '#2d3748', 'font_color': 'white', 'border': 1, 'align': 'center'})
    fmt_plata = workbook.add_format({'num_format': '$ #,##0.00', 'border': 1})
    fmt_num = workbook.add_format({'border': 1, 'align': 'center'})
    fmt_titulo = workbook.add_format({'bold': True, 'font_size': 14})

    def agregar_hoja_analisis(nombre_hoja, col_agrupar, tipo_grafico="column"):
        ws = workbook.add_worksheet(nombre_hoja)
        ws.write(0, 0, f"Análisis: {nombre_hoja}", fmt_titulo)
        
        # Procesar datos
        if col_agrupar in df_nc.columns:
            agrupado = df_nc.groupby(col_agrupar).agg(Cantidad=('numero', 'count'), Total_Monto=('importe total origen', 'sum')).reset_index().sort_values('Cantidad', ascending=False).head(10)
        else: return
        
        # Escribir Headers
        ws.write(2, 0, col_agrupar.upper(), fmt_header)
        ws.write(2, 1, "CANTIDAD", fmt_header)
        ws.write(2, 2, "MONTO TOTAL", fmt_header)
        ws.set_column(0, 0, 25)
        ws.set_column(1, 2, 15)

        # Escribir Datos
        for i, row in agrupado.iterrows():
            row_idx = i + 3
            ws.write(row_idx, 0, row[col_agrupar], fmt_num)
            ws.write(row_idx, 1, row['Cantidad'], fmt_num)
            ws.write(row_idx, 2, row['Total_Monto'], fmt_plata)
            
        # Crear Gráfico Nativo Excel
        chart = workbook.add_chart({'type': tipo_grafico})
        max_row = len(agrupado) + 2
        chart.add_series({
            'name': 'Cantidad',
            'categories': [nombre_hoja, 3, 0, max_row, 0],
            'values':     [nombre_hoja, 3, 1, max_row, 1],
            'fill':       {'color': '#ff4b4b'}
        })
        chart.set_title({'name': f'Top 10 - {nombre_hoja}'})
        chart.set_legend({'none': True})
        ws.insert_chart('E3', chart)

    # Crear Solapas
    agregar_hoja_analisis("Top 10 Clientes", "nombre cliente", "bar")
    agregar_hoja_analisis("Motivos", "referencia 1", "pie")
    
    # Filtrar Error Carga
    df_err = df_nc[df_nc['referencia 1'].astype(str).str.contains('ERROR', case=False, na=False)] if 'referencia 1' in df_nc.columns else df_nc
    ws_err = workbook.add_worksheet("Error Carga")
    ws_err.write(0, 0, "Análisis: Error de Carga", fmt_titulo)
    if 'cobrador cliente' in df_err.columns:
        agrupado_err = df_err.groupby('cobrador cliente').agg(Cantidad=('numero', 'count'), Total_Monto=('importe total origen', 'sum')).reset_index().sort_values('Cantidad', ascending=False).head(10)
        ws_err.write(2, 0, "COBRADOR", fmt_header); ws_err.write(2, 1, "CANT", fmt_header); ws_err.write(2, 2, "MONTO", fmt_header)
        ws_err.set_column(0, 0, 25)
        for i, row in agrupado_err.iterrows():
            ws_err.write(i+3, 0, row['cobrador cliente'], fmt_num); ws_err.write(i+3, 1, row['Cantidad'], fmt_num); ws_err.write(i+3, 2, row['Total_Monto'], fmt_plata)
        chart_e = workbook.add_chart({'type': 'column'})
        chart_e.add_series({'categories': ["Error Carga", 3, 0, len(agrupado_err)+2, 0], 'values': ["Error Carga", 3, 1, len(agrupado_err)+2, 1], 'fill': {'color': '#ff4b4b'}})
        ws_err.insert_chart('E3', chart_e)

    workbook.close()
    output.seek(0)
    return output

# --- RENDERIZADO VISUAL ---
def tarjeta_kpi(titulo, valor): return f"""<div class="kpi-card kpi-rojo"><div class="kpi-titulo">{titulo}</div><div class="kpi-valor">🔴 ⬆ {valor}</div></div>"""
def formato_arg(n): return "0,00" if pd.isna(n) or n==0 else f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def formato_pct(n): return "0,00%" if pd.isna(n) or n==0 else f"{abs(n)*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")
def icono_cantidad(val):
    if val < 20: return "badge-ok", f"✔️ {int(val)}"
    elif val <= 30: return "badge-warn", f"⚠️ {int(val)}"
    else: return "badge-alerta", f"❌ {int(val)}"

def render_lista(df, col_titulo, cols_datos, ranking=False):
    html = "<div class='tabla-canchera'><div class='fila-header'>" + f"<div class='celda-header-titulo'>{col_titulo}</div>"
    for c in cols_datos: html += f"<div class='celda-header-valor'>{c}</div>"
    html += "</div>"
    for _, row in df.iterrows():
        estilo_borde = f"border: 2px solid {row['Color']}; box-shadow: 0 0 10px {row['Color']}60;" if ranking and 'Color' in row else "border: 1px solid #edf2f7;"
        html += f"<div class='fila-canchera' style='{estilo_borde}'><div class='celda-titulo' title='{row[col_titulo]}'>{row[col_titulo]}</div>"
        for c in cols_datos:
            val, clase_extra, txt_val = row[c], "badge-neutral", ""
            if 'Variación' in c:
                txt_val = formato_pct(val)
                clase_extra, txt_val = ("badge-alerta", f"❌ {txt_val}") if val > 0 else ("badge-ok", f"✔️ {txt_val}")
            elif '%' in c or 'SOBRE VENTA' in c:
                txt_val = formato_pct(val)
                if val > 0.05: clase_extra, txt_val = "badge-alerta", f"❌ {txt_val}"
                elif val > 0.02: clase_extra, txt_val = "badge-warn", f"⚠️ {txt_val}"
                else: clase_extra, txt_val = "badge-ok", f"✔️ {txt_val}"
            elif 'Cant 20' in c or c == 'CANTIDAD': clase_extra, txt_val = icono_cantidad(val)
            elif 'Total' in c or 'Monto' in c: txt_val = f"$&nbsp;{formato_arg(val)}"
            elif 'Cantidad' in c or 'Cant' in c: txt_val = str(int(val))
            else: txt_val = str(val)
            html += f"<div class='celda-valor'><div class='badge {clase_extra}'>{txt_val}</div></div>"
        html += "</div>"
    html += "</div>"
    return html

def grafico_barras_v(df, x_col, y_col): return alt.Chart(df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(x=alt.X(x_col, sort=alt.EncodingSortField(field='Cant', order='descending'), title='', axis=alt.Axis(labelAngle=-45)), y=alt.Y(y_col, title=''), color=alt.Color('Color:N', scale=None, legend=None)).properties(height=320)
def grafico_barras_h(df, x_col, y_col): return alt.Chart(df).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(y=alt.Y(x_col, sort=alt.EncodingSortField(field='Cant', order='descending'), title=''), x=alt.X(y_col, title=''), color=alt.Color('Color:N', scale=None, legend=None)).properties(height=320)
def grafico_torta(df, x_col, y_col): return alt.Chart(df).mark_arc(innerRadius=60).encode(theta=alt.Theta(field=y_col, type="quantitative"), color=alt.Color(field=x_col, type="nominal", scale=alt.Scale(range=PALETA_COLORES), sort=alt.EncodingSortField(field='Cant', order='descending'), legend=alt.Legend(title="", orient="bottom"))).properties(height=320)

# --- 🔒 LOGIN ---
if "rol" not in st.session_state: st.session_state.rol = None
if not st.session_state.rol:
    st.title("🔒 Acceso al Sistema")
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if pwd == "admin123": st.session_state.rol = "admin"; st.rerun()
        elif pwd == "visor123": st.session_state.rol = "visor"; st.rerun()
        else: st.error("Clave incorrecta.")
    st.stop() 

# --- CARGA AUTOMÁTICA PARA VISOR ---
if st.session_state.rol == "visor" and 'd_nc26_raw' not in st.session_state:
    with st.spinner("Sincronizando información en vivo desde la nube..."):
        exito, msg = cargar_base_desde_sheets()
        if exito: st.rerun()
        else: st.error(f"Error de conexión: {msg}")

# --- FILTRO GLOBAL (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Controles")
    filtro_tiempo = st.selectbox("📅 Período de Análisis", ["Todo el Año", "Q1 (Ene-Mar)", "Q2 (Abr-Jun)", "Q3 (Jul-Sep)", "Q4 (Oct-Dic)", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
    st.markdown("---")
    
    # Opciones Admin
    if st.session_state.rol == "admin":
        st.header("💾 Nube & Exportación")
        if 'd_nc26_raw' in st.session_state:
            excel_data = generar_excel_avanzado(st.session_state['d_nc26_raw'], st.session_state['d_v26_raw'])
            st.download_button("📥 Exportar Reporte a Excel", data=excel_data, file_name="Reporte_Format_NC.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            if st.button("☁️ Guardar Datos en la Nube", type="primary"):
                with st.spinner("Sincronizando..."):
                    dict_db = {"BD_NC_26": st.session_state['d_nc26_raw'], "BD_Ventas_26": st.session_state['d_v26_raw'], "BD_NC_25": st.session_state['d_nc25_raw'], "BD_Ventas_25": st.session_state['d_v25_raw']}
                    ex, msg = guardar_base_completa_en_sheets(dict_db)
                    if ex: st.success(msg)
                    else: st.error(msg)
    
    st.markdown("---")
    if st.button("Cerrar Sesión"): st.session_state.rol = None; st.rerun()

# --- APLICAR FILTRO GLOBAL A LOS DATOS ---
def filtrar_df(df, filtro):
    if filtro == "Todo el Año" or 'mes' not in df.columns: return df
    meses_map = {"Enero":1, "Febrero":2, "Marzo":3, "Abril":4, "Mayo":5, "Junio":6, "Julio":7, "Agosto":8, "Septiembre":9, "Octubre":10, "Noviembre":11, "Diciembre":12}
    if filtro.startswith("Q"):
        q = int(filtro[1])
        return df[df['mes'].isin([q*3-2, q*3-1, q*3])]
    else: return df[df['mes'] == meses_map[filtro]]

if 'd_nc26_raw' in st.session_state:
    st.session_state['d_nc26'] = filtrar_df(st.session_state['d_nc26_raw'], filtro_tiempo)
    st.session_state['d_v26'] = filtrar_df(st.session_state['d_v26_raw'], filtro_tiempo)
    st.session_state['d_nc25'] = filtrar_df(st.session_state['d_nc25_raw'], filtro_tiempo)
    st.session_state['d_v25'] = filtrar_df(st.session_state['d_v25_raw'], filtro_tiempo)

# --- 📊 APLICACIÓN PRINCIPAL ---
st.title(f"📊 Análisis de Reportes NC - {filtro_tiempo}")
tab_analisis, tab_top10, tab_motivo, tab_error = st.tabs(["Dashboard", "Top 10 Clientes", "Motivos", "Error Carga"])

with tab_analisis:
    if st.session_state.rol == "admin":
        with st.expander("📂 Carga de Archivos Manual (Admin)", expanded=False):
            c1, c2, c3 = st.columns(3)
            with c1: file_fcp = st.file_uploader("Facturación 2026", type=['xlsx'])
            with c2: file_nc = st.file_uploader("Notas Crédito 2026", type=['xlsx'])
            with c3: file_historico = st.file_uploader("Histórico 2025", type=['xlsx'])
            if st.button("Procesar Archivos"):
                if file_fcp and file_nc and file_historico:
                    df_v, df_n, df_h = pd.read_excel(file_fcp, header=2), pd.read_excel(file_nc, header=2), pd.read_excel(file_historico, header=2)
                    for d in [df_v, df_n, df_h]: d.columns = (d.columns.str.lower().str.strip().str.replace('ú', 'u').str.replace('í', 'i').str.replace('ó', 'o').str.replace('á', 'a').str.replace('é', 'e'))
                    df_v, df_n, df_h = df_v.drop_duplicates(subset=['numero']), df_n.drop_duplicates(subset=['numero']), df_h.drop_duplicates(subset=['numero'])
                    df_h['fecha'] = pd.to_datetime(df_h['fecha'], errors='coerce')
                    df_h = df_h[df_h['fecha'] >= '2025-01-01']
                    df_h_nc = df_h[df_h['tipo'].astype(str).str.contains('NC', case=False, na=False)] if 'tipo' in df_h.columns else df_h
                    df_h_v = df_h[~df_h['tipo'].astype(str).str.contains('NC|ND', case=False, na=False)] if 'tipo' in df_h.columns else pd.DataFrame(columns=df_h.columns)
                    st.session_state['d_nc26_raw'], st.session_state['d_v26_raw'], st.session_state['d_nc25_raw'], st.session_state['d_v25_raw'] = df_n, df_v, df_h_nc, df_h_v
                    for key in ['d_nc26_raw', 'd_v26_raw', 'd_nc25_raw', 'd_v25_raw']: st.session_state[key]['fecha'] = pd.to_datetime(st.session_state[key]['fecha'], errors='coerce'); st.session_state[key]['mes'] = st.session_state[key]['fecha'].dt.month
                    st.rerun()

    if 'd_nc26' in st.session_state and not st.session_state['d_nc26'].empty:
        d26, d25 = st.session_state['d_nc26'], st.session_state['d_nc25']
        v26, v25 = st.session_state['d_v26'], st.session_state['d_v25']
        
        t_nc, t_c = d26['importe total origen'].sum(), d26['numero'].count()
        k1, k2, k3 = st.columns([1, 1, 2])
        with k1: st.markdown(tarjeta_kpi(f"NC Emitidas ({filtro_tiempo})", int(t_c)), unsafe_allow_html=True)
        with k2: st.markdown(tarjeta_kpi(f"Monto Total ({filtro_tiempo})", f"$ {formato_arg(t_nc)}"), unsafe_allow_html=True)
        with k3:
            v_26_mill = (v26['importe total origen'].sum() / 1000000) if v26['importe total origen'].sum() != 0 else 0
            pct_26 = (t_nc / v26['importe total origen'].sum()) if v26['importe total origen'].sum() != 0 else 0
            df_hist_anual = pd.DataFrame({'AÑO': ['2023', '2024', '2025', '2026 (Selección)'], 'CANTIDAD': [336, 358, 342, int(t_c)], 'EN MILLONES': ["76.000", "218.000", "338.000", f"{v_26_mill:,.3f}".replace(',', '.')], '% SOBRE VENTA': [0.0486, 0.0438, 0.0548, pct_26]})
            st.markdown(render_lista(df_hist_anual, 'AÑO', ['CANTIDAD', 'EN MILLONES', '% SOBRE VENTA']), unsafe_allow_html=True)
            
        st.info("💡 Cambia de solapa para ver el análisis detallado del Top 10 Clientes, Motivos y Errores aplicando este filtro de tiempo.")

# --- SOLAPAS DE ANÁLISIS ---
if 'd_nc26' in st.session_state and not st.session_state['d_nc26'].empty:
    d_nc = st.session_state['d_nc26']

    def armar_seccion(df_analisis, col_agrupar, titulo, es_error=False, tipo_grafico="barras_h"):
        if es_error: df_analisis = df_analisis[df_analisis['referencia 1'].astype(str).str.contains('ERROR', case=False, na=False)] if 'referencia 1' in df_analisis.columns else df_analisis
        
        st.markdown(f"<br><h2 style='font-size: 2.2rem;'>{titulo} - {filtro_tiempo}</h2>", unsafe_allow_html=True)
        if col_agrupar in df_analisis.columns and not df_analisis.empty:
            ag_data = df_analisis.groupby(col_agrupar).agg(Cant=('numero', 'count'), Total=('importe total origen', 'sum')).reset_index().sort_values('Cant', ascending=False).head(10).reset_index(drop=True)
            ag_data['Color'] = PALETA_COLORES[:len(ag_data)]
            cA, cB = st.columns([1.1, 1.3])
            with cA: st.markdown(render_lista(ag_data, col_agrupar, ['Cant', 'Total'], ranking=True), unsafe_allow_html=True)
            with cB: 
                if tipo_grafico == "barras_h": st.altair_chart(grafico_barras_h(ag_data, col_agrupar, 'Cant'), use_container_width=True)
                elif tipo_grafico == "torta": st.altair_chart(grafico_torta(ag_data, col_agrupar, 'Cant'), use_container_width=True)
                else: st.altair_chart(grafico_barras_v(ag_data, col_agrupar, 'Cant'), use_container_width=True)
        else: st.info(f"No hay datos registrados en {filtro_tiempo}.")

    with tab_top10: armar_seccion(d_nc, 'nombre cliente', "Análisis Top 10 Clientes", tipo_grafico="barras_h")
    with tab_motivo: armar_seccion(d_nc, 'referencia 1', "Análisis de Motivos", tipo_grafico="torta")
    with tab_error: armar_seccion(d_nc, 'cobrador cliente', "Análisis de Error de Carga", es_error=True, tipo_grafico="barras_v")
