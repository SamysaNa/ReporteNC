import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import io
import xlsxwriter
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Reporte NC Mundi SA", layout="wide")

# --- ESTILOS CSS REFORZADOS ---
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
.celda-header-titulo { flex: 0 0 160px; font-size: 0.75rem; font-weight: 900; color: #718096; text-transform: uppercase; text-align: left; }
.celda-header-datos { flex: 1; display: flex; justify-content: flex-end; gap: 8px; }
.celda-header-valor { flex: 1; text-align: right; font-size: 0.75rem; font-weight: 900; color: #718096; text-transform: uppercase; }

.fila-canchera, details.detalle-fila summary { display: flex; width: 100%; align-items: center; background: #ffffff; border-radius: 8px; padding: 4px 10px; margin-bottom: 5px; border: 1px solid #edf2f7; list-style: none; cursor: default;}
details.detalle-fila summary { cursor: pointer; transition: transform 0.1s; }
details.detalle-fila summary::-webkit-details-marker { display: none; }
details.detalle-fila summary:hover { transform: scale(1.01); background: #f8fafc; }
details[open] summary { border-radius: 8px 8px 0 0; border-bottom: 1px dashed #e2e8f0 !important; }

.celda-titulo { flex: 0 0 160px; font-weight: 800; color: #2d3748; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: left; display: flex; align-items: center; gap: 5px;}
.celda-datos-container { flex: 1; display: flex; justify-content: flex-end; gap: 8px; align-items: center;}

.badge { flex: 1; min-width: 80px; padding: 2px 6px; border-radius: 6px; font-weight: 800; font-size: 0.85rem; display: flex; align-items: center; justify-content: flex-end; gap: 4px; text-align: right; white-space: nowrap;}
.badge-neutral { background: transparent; color: #4a5568; }
.badge-alerta { background: rgba(255, 75, 75, 0.12); color: #c53030; }
.badge-warn { background: rgba(255, 193, 7, 0.15); color: #b8860b; }
.badge-ok { background: rgba(40, 167, 69, 0.12); color: #22543d; }

.detalle-contenido { background: #f7fafc; padding: 10px 15px; border-radius: 0 0 8px 8px; border: 1px solid #edf2f7; border-top: none; margin-top: -5px; font-size: 0.8rem; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02); margin-bottom: 5px;}
.tabla-interna { width: 100%; border-collapse: collapse; }
.tabla-interna th { color: #a0aec0; font-weight: 900; text-transform: uppercase; text-align: left; padding: 4px 8px; border-bottom: 2px solid #e2e8f0; font-size: 0.7rem; }
.tabla-interna td { color: #4a5568; font-weight: 700; text-align: left; padding: 4px 8px; border-bottom: 1px solid #edf2f7; }
</style>
""", unsafe_allow_html=True)

PALETA_COLORES = ['#ff1a1a', '#ff5555', '#ff7f50', '#ffa07a', '#ffb347', '#ffd700', '#d4e157', '#9ece6a', '#48c774', '#20b2aa']
ID_DEL_SHEET = "101j4mRqe6KPhM1htOKqHJxYUKcTalDHosEZF-MalrPY"

# --- EXPORTACIÓN EXCEL FULL ---
def generar_excel_avanzado(df_nc, df_v, df_nc25, df_v25, dias_habiles):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    fmt_titulo = workbook.add_format({'bold': True, 'font_size': 16, 'color': '#2d3748'})
    fmt_header = workbook.add_format({'bold': True, 'bg_color': '#2d3748', 'font_color': 'white', 'border': 1, 'align': 'center'})
    fmt_num = workbook.add_format({'border': 1, 'align': 'center'})
    fmt_plata = workbook.add_format({'num_format': '$ #,##0.00', 'border': 1})
    
    ws_res = workbook.add_worksheet("Resumen")
    ws_res.write(0, 0, "Resumen NC 2026", fmt_titulo)
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    if not df_nc.empty and 'fecha' in df_nc.columns:
        df_nc['mes'] = pd.to_datetime(df_nc['fecha']).dt.month
        df_v['mes'] = pd.to_datetime(df_v['fecha']).dt.month
        df_nc_abs = df_nc.copy()
        if 'total bruto origen' in df_nc_abs.columns: df_nc_abs['total bruto origen'] = df_nc_abs['total bruto origen'].abs()
        v_m = df_v.groupby('mes')['total bruto origen'].sum().reset_index().rename(columns={'total bruto origen': 'Ventas'})
        nc_m = df_nc_abs.groupby('mes')['total bruto origen'].sum().reset_index().rename(columns={'total bruto origen': 'Monto NC'})
        nc_c = df_nc.groupby('mes')['numero'].count().reset_index().rename(columns={'numero': 'Cantidad'})
    else:
        v_m, nc_m, nc_c = pd.DataFrame(columns=['mes', 'Ventas']), pd.DataFrame(columns=['mes', 'Monto NC']), pd.DataFrame(columns=['mes', 'Cantidad'])
    
    calc = pd.DataFrame({'Mes_Num': range(1, 13), 'Mes': meses})
    calc = calc.merge(v_m, left_on='Mes_Num', right_on='mes', how='left').merge(nc_m, left_on='Mes_Num', right_on='mes', how='left').merge(nc_c, left_on='Mes_Num', right_on='mes', how='left').fillna(0)
    
    headers_res = ["Mes", "Cantidad", "Monto NC", "Ventas", "Días Hábiles"]
    for col, h in enumerate(headers_res): ws_res.write(2, col, h, fmt_header)
    ws_res.set_column(0, 4, 18)
    
    for i, row in calc.iterrows():
        ws_res.write(i+3, 0, row['Mes'], fmt_num)
        ws_res.write(i+3, 1, row['Cantidad'], fmt_num)
        ws_res.write(i+3, 2, row['Monto NC'], fmt_plata)
        ws_res.write(i+3, 3, row['Ventas'], fmt_plata)
        ws_res.write(i+3, 4, dias_habiles[i] if i < len(dias_habiles) else 20, fmt_num)
        
    chart_res = workbook.add_chart({'type': 'column'})
    chart_res.add_series({'name': 'Ventas', 'categories': ['Resumen', 3, 0, 14, 0], 'values': ['Resumen', 3, 3, 14, 3], 'fill': {'color': '#4bc0c0'}})
    chart_res.add_series({'name': 'Monto NC', 'categories': ['Resumen', 3, 0, 14, 0], 'values': ['Resumen', 3, 2, 14, 2], 'fill': {'color': '#ff4b4b'}})
    chart_res.set_title({'name': 'Comparativa Mensual (Ventas vs NC)'})
    ws_res.insert_chart('G3', chart_res)
        
    def agregar_hoja(nombre, col_agrupar, tipo_grafico, df_base):
        if df_base.empty or col_agrupar not in df_base.columns: return
        ws = workbook.add_worksheet(nombre)
        ws.write(0, 0, f"Análisis: {nombre}", fmt_titulo)
        
        df_abs = df_base.copy()
        if 'total bruto origen' in df_abs.columns: df_abs['total bruto origen'] = df_abs['total bruto origen'].abs()
        ag = df_abs.groupby(col_agrupar).agg(Cantidad=('numero', 'count'), Total=('total bruto origen', 'sum')).reset_index().sort_values('Cantidad', ascending=False).head(10).reset_index(drop=True)
        
        ws.write(2, 0, col_agrupar.upper(), fmt_header)
        ws.write(2, 1, "CANT", fmt_header)
        ws.write(2, 2, "MONTO", fmt_header)
        ws.set_column(0, 0, 30); ws.set_column(1, 2, 15)
        
        for i, row in ag.iterrows():
            ws.write(i+3, 0, row[col_agrupar], fmt_num)
            ws.write(i+3, 1, row['Cantidad'], fmt_num)
            ws.write(i+3, 2, row['Total'], fmt_plata)
            
        chart = workbook.add_chart({'type': tipo_grafico})
        chart.add_series({
            'name': 'Cantidad',
            'categories': [nombre, 3, 0, len(ag)+2, 0],
            'values':     [nombre, 3, 1, len(ag)+2, 1],
            'points':     [{'fill': {'color': c}} for c in PALETA_COLORES[:len(ag)]]
        })
        if tipo_grafico != 'pie': chart.set_legend({'none': True})
        ws.insert_chart('E3', chart)

    agregar_hoja("Top 10 Clientes", "nombre cliente", "bar", df_nc)
    agregar_hoja("Motivos", "referencia 1", "pie", df_nc)
    
    df_err = df_nc[df_nc['referencia 1'].astype(str).str.strip().str.upper() == 'ERROR DE CARGA'] if not df_nc.empty and 'referencia 1' in df_nc.columns else pd.DataFrame()
    if not df_err.empty: agregar_hoja("Error Carga", "cobrador cliente", "column", df_err)

    workbook.close()
    output.seek(0)
    return output

def conectar_google():
    if "gcp_service_account" not in st.secrets: return None, "Falta configurar credenciales."
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds).open_by_key(ID_DEL_SHEET), "Conexión exitosa"

def guardar_base_completa_en_sheets(dict_dfs):
    sheet_doc, msg = conectar_google()
    if not sheet_doc: return False, msg
    try:
        for nombre_hoja, df in dict_dfs.items():
            df_str = df.copy()
            for col in df_str.select_dtypes(include=['datetime', 'datetimetz']).columns: df_str[col] = df_str[col].dt.strftime('%Y-%m-%d')
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
        try: st.session_state['dias_habiles'] = pd.DataFrame(sheet_doc.worksheet("BD_Config").get_all_records())['Dias'].tolist()
        except: pass
        for key in ['d_nc26_raw', 'd_v26_raw', 'd_nc25_raw', 'd_v25_raw']:
            if 'fecha' in st.session_state[key].columns:
                st.session_state[key]['fecha'] = pd.to_datetime(st.session_state[key]['fecha'], errors='coerce')
                st.session_state[key]['mes'] = st.session_state[key]['fecha'].dt.month
                st.session_state[key]['trimestre'] = (st.session_state[key]['mes'] - 1) // 3 + 1
        return True, "Información descargada exitosamente."
    except Exception as e: return False, f"Error descargando: {e}"

# --- RENDERIZADO VISUAL ---
def tarjeta_kpi(titulo, valor): return f"""<div class="kpi-card kpi-rojo"><div class="kpi-titulo">{titulo}</div><div class="kpi-valor">🔴 ⬆ {valor}</div></div>"""
def formato_arg(n): return "0,00" if pd.isna(n) or n==0 else f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def formato_pct(n): return "0,00%" if pd.isna(n) or n==0 else f"{abs(n)*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")
def icono_cantidad(val):
    if val < 20: return "badge-ok", f"✔️ {int(val)}"
    elif val <= 30: return "badge-warn", f"⚠️ {int(val)}"
    else: return "badge-alerta", f"❌ {int(val)}"

def render_lista(df_agrupado, df_crudo, col_titulo, cols_datos, ranking=False, desglosar=False):
    html = "<div class='tabla-canchera'><div class='fila-header'>" + f"<div class='celda-header-titulo'>{col_titulo}</div><div class='celda-header-datos'>"
    for c in cols_datos: html += f"<div class='celda-header-valor'>{c}</div>"
    html += "</div></div>"
    
    for _, row in df_agrupado.iterrows():
        estilo_borde = f"border: 2px solid {row['Color']}; box-shadow: 0 0 10px {row['Color']}60;" if ranking and 'Color' in row else "border: 1px solid #edf2f7;"
        html += f"<details class='detalle-fila'><summary style='{estilo_borde}'>" if desglosar else f"<div class='fila-canchera' style='{estilo_borde}'>"
        flechita = "▶ " if desglosar else ""
        html += f"<div class='celda-titulo' title='{row[col_titulo]}'>{flechita}{row[col_titulo]}</div><div class='celda-datos-container'>"
        
        for c in cols_datos:
            val, clase_extra, txt_val = row[c], "badge-neutral", ""
            if 'Variación' in c: txt_val = formato_pct(val); clase_extra, txt_val = ("badge-alerta", f"❌ {txt_val}") if val > 0 else ("badge-ok", f"✔️ {txt_val}")
            elif '%' in c or 'SOBRE VENTA' in c: txt_val = formato_pct(val); clase_extra, txt_val = ("badge-alerta", f"❌ {txt_val}") if val > 0.05 else ("badge-warn", f"⚠️ {txt_val}") if val > 0.02 else ("badge-ok", f"✔️ {txt_val}")
            elif 'Cant 20' in c or c == 'CANTIDAD': clase_extra, txt_val = icono_cantidad(val)
            elif 'Total' in c or 'Monto' in c: txt_val = f"$&nbsp;{formato_arg(val)}"
            elif 'Cantidad' in c or 'Cant' in c: txt_val = str(int(val))
            else: txt_val = str(val)
            html += f"<div class='badge {clase_extra}'>{txt_val}</div>"
            
        if desglosar:
            html += "</div></summary>"
            df_det = df_crudo[df_crudo[col_titulo] == row[col_titulo]].sort_values('fecha', ascending=False)
            html += "<div class='detalle-contenido'><table class='tabla-interna'><tr><th>Fecha</th><th>Número</th><th>Cliente</th><th>Monto Bruto</th></tr>"
            for _, det_row in df_det.iterrows():
                f_str = det_row['fecha'].strftime('%d/%m/%Y') if pd.notnull(det_row['fecha']) else ''
                html += f"<tr><td>{f_str}</td><td>{det_row.get('numero', '')}</td><td>{det_row.get('nombre cliente', '')}</td><td>$ {formato_arg(abs(det_row.get('total bruto origen', 0)))}</td></tr>"
            html += "</table></div></details>"
        else: html += "</div></div>"
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

if st.session_state.rol == "visor" and 'd_nc26_raw' not in st.session_state:
    with st.spinner("Sincronizando información en vivo desde la nube..."):
        ex, msg = cargar_base_desde_sheets()
        if ex: st.rerun()
        else: st.error(f"Error de conexión: {msg}")

# --- FILTRO GLOBAL Y CONTROLES (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Controles Globales")
    filtro_tiempo = st.selectbox("📅 Seleccione el período", ["Todo el Año", "Q1 (Ene-Mar)", "Q2 (Abr-Jun)", "Q3 (Jul-Sep)", "Q4 (Oct-Dic)", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
    
    if st.session_state.rol == "admin":
        st.markdown("---")
        st.header("🗓️ Días Hábiles (Admin)")
        if 'dias_habiles' not in st.session_state: st.session_state['dias_habiles'] = [20]*12
        with st.expander("Modificar Días", expanded=False):
            meses_n = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            for i, m in enumerate(meses_n): st.session_state['dias_habiles'][i] = st.number_input(m, value=st.session_state['dias_habiles'][i], min_value=0, max_value=31, key=f"dia_{i}")

        st.markdown("---")
        st.header("💾 Exportación y Nube")
        if 'd_nc26_raw' in st.session_state:
            excel_data = generar_excel_avanzado(st.session_state['d_nc26_raw'], st.session_state['d_v26_raw'], st.session_state['d_nc25_raw'], st.session_state['d_v25_raw'], st.session_state['dias_habiles'])
            st.download_button("📥 Descargar Reporte Completo (Excel)", data=excel_data, file_name="Reporte_Format_NC.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            if st.button("☁️ Guardar Datos en la Nube", type="primary"):
                with st.spinner("Sincronizando..."):
                    dict_db = {"BD_NC_26": st.session_state['d_nc26_raw'], "BD_Ventas_26": st.session_state['d_v26_raw'], "BD_NC_25": st.session_state['d_nc25_raw'], "BD_Ventas_25": st.session_state['d_v25_raw'], "BD_Config": pd.DataFrame({'Dias': st.session_state['dias_habiles']})}
                    ex, msg = guardar_base_completa_en_sheets(dict_db)
                    if ex: st.success(msg)
                    else: st.error(msg)
    
    st.markdown("---")
    if st.button("Cerrar Sesión"): st.session_state.rol = None; st.rerun()

# --- APLICAR FILTRO ---
def filtrar_df(df, filtro):
    if filtro == "Todo el Año" or 'mes' not in df.columns: return df
    meses_map = {"Enero":1, "Febrero":2, "Marzo":3, "Abril":4, "Mayo":5, "Junio":6, "Julio":7, "Agosto":8, "Septiembre":9, "Octubre":10, "Noviembre":11, "Diciembre":12}
    if filtro.startswith("Q"): q = int(filtro[1]); return df[df['mes'].isin([q*3-2, q*3-1, q*3])]
    else: return df[df['mes'] == meses_map[filtro]]

if 'd_nc26_raw' in st.session_state:
    for k in ['d_nc26', 'd_v26', 'd_nc25', 'd_v25']: st.session_state[k] = filtrar_df(st.session_state[f'{k}_raw'], filtro_tiempo)

# --- 📊 DASHBOARD PRINCIPAL ---
st.title("📊 Reporte NC Mundi SA")
if filtro_tiempo != "Todo el Año": st.markdown(f"#### Filtrado por: {filtro_tiempo}")

tab_analisis, tab_top10, tab_motivo, tab_error = st.tabs(["Resumen", "Top 10 Clientes", "Motivos", "Error Carga"])

with tab_analisis:
    if st.session_state.rol == "admin":
        with st.expander("📂 Carga de Archivos Manual (Admin)", expanded=False):
            c1, c2, c3 = st.columns(3)
            with c1: f_fcp = st.file_uploader("Facturación 2026", type=['xlsx'])
            with c2: f_nc = st.file_uploader("Notas Crédito 2026", type=['xlsx'])
            with c3: f_h = st.file_uploader("Histórico 2025", type=['xlsx'])
            if st.button("Procesar Archivos"):
                if f_fcp and f_nc and f_h:
                    df_v, df_n, df_h = pd.read_excel(f_fcp, header=2), pd.read_excel(f_nc, header=2), pd.read_excel(f_h, header=2)
                    for d in [df_v, df_n, df_h]: d.columns = (d.columns.str.lower().str.strip().str.replace('ú', 'u').str.replace('í', 'i').str.replace('ó', 'o').str.replace('á', 'a').str.replace('é', 'e'))
                    df_v, df_n, df_h = df_v.drop_duplicates(subset=['numero']), df_n.drop_duplicates(subset=['numero']), df_h.drop_duplicates(subset=['numero'])
                    df_h['fecha'] = pd.to_datetime(df_h['fecha'], errors='coerce')
                    df_h = df_h[df_h['fecha'] >= '2025-01-01']
                    
                    # FILTRO EXACTO PARA 2025 (Lista brindada por el usuario)
                    if 'tipo' in df_h.columns:
                        tipos_nc_nd = ('C10', 'C11', 'C12', 'C14', 'C16', 'CA2', 'CA3', 'CA4', 'CA6', 'CA7', 'CA8', 'CA9', 'CAC', 'CAE', 'CB3', 'DA1', 'DA2', 'DA3', 'NC2', 'NC3', 'NC6', 'NC7', 'NC8', 'NCC')
                        mask_nc = df_h['tipo'].astype(str).str.strip().str.upper().str.startswith(tipos_nc_nd)
                        df_h_nc = df_h[mask_nc]
                        df_h_v = df_h[~mask_nc]
                    else:
                        df_h_nc, df_h_v = df_h, pd.DataFrame(columns=df_h.columns)
                    
                    st.session_state['d_nc26_raw'], st.session_state['d_v26_raw'], st.session_state['d_nc25_raw'], st.session_state['d_v25_raw'] = df_n, df_v, df_h_nc, df_h_v
                    for key in ['d_nc26_raw', 'd_v26_raw', 'd_nc25_raw', 'd_v25_raw']: st.session_state[key]['fecha'] = pd.to_datetime(st.session_state[key]['fecha'], errors='coerce'); st.session_state[key]['mes'] = st.session_state[key]['fecha'].dt.month; st.session_state[key]['trimestre'] = (st.session_state[key]['mes'] - 1) // 3 + 1
                    st.rerun()

    if 'd_nc26' in st.session_state and not st.session_state['d_nc26_raw'].empty:
        d26_raw, d25_raw = st.session_state['d_nc26_raw'], st.session_state['d_nc25_raw']
        v26_raw, v25_raw = st.session_state['d_v26_raw'], st.session_state['d_v25_raw']
        
        max_mes = int(d26_raw['mes'].max()) if not d26_raw.empty else 12
        meses_activos = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][:max_mes]

        def calc_m(df_v, df_nc, max_m):
            c = pd.DataFrame({'mes': range(1, max_m+1)})
            df_nc_abs = df_nc.copy()
            if 'total bruto origen' in df_nc_abs.columns: df_nc_abs['total bruto origen'] = df_nc_abs['total bruto origen'].abs()
            
            c = c.merge(df_v.groupby('mes')['total bruto origen'].sum().reset_index(), on='mes', how='left').rename(columns={'total bruto origen': 'ventas'})
            c = c.merge(df_nc_abs.groupby('mes')['total bruto origen'].sum().reset_index(), on='mes', how='left').rename(columns={'total bruto origen': 'nc'})
            c = c.merge(df_nc.groupby('mes')['numero'].count().reset_index(), on='mes', how='left').rename(columns={'numero': 'cantidad'})
            return c.fillna(0)
            
        d26_calc, d25_calc = calc_m(v26_raw, d26_raw, max_mes), calc_m(v25_raw, d25_raw, max_mes)

        st.markdown("<h1 style='font-size: 3.5rem; font-weight: 900; color: #1a202c; margin-top: 10px; margin-bottom: 10px;'>2026</h1>", unsafe_allow_html=True)
        
        if filtro_tiempo != "Todo el Año":
            t_nc, t_c = abs(st.session_state['d_nc26']['total bruto origen'].sum()), st.session_state['d_nc26']['numero'].count()
            k1, k2, k3 = st.columns([1, 1, 2])
            with k1: st.markdown(tarjeta_kpi(f"NC Emitidas ({filtro_tiempo})", int(t_c)), unsafe_allow_html=True)
            with k2: st.markdown(tarjeta_kpi(f"Monto Total ({filtro_tiempo})", f"$ {formato_arg(t_nc)}"), unsafe_allow_html=True)
            with k3: st.info("💡 Cambia de solapa para ver el análisis detallado aplicando este filtro de tiempo. (El Dashboard principal muestra el panorama Anual general).")
        else:
            t_nc, t_c = d26_calc['nc'].sum(), d26_calc['cantidad'].sum()
            k1, k2, k3 = st.columns([1, 1, 2])
            with k1: st.markdown(tarjeta_kpi("Total NC Emitidas", int(t_c)), unsafe_allow_html=True)
            with k2: st.markdown(tarjeta_kpi("Monto Total NC", f"$ {formato_arg(t_nc)}"), unsafe_allow_html=True)
            with k3:
                nc_millones = t_nc / 1000000 if t_nc != 0 else 0
                pct_26 = (t_nc / d26_calc['ventas'].sum()) if d26_calc['ventas'].sum() != 0 else 0
                df_hist_anual = pd.DataFrame({'COMPARATIVA ANUAL': ['2023', '2024', '2025', '2026 (Parcial)'], 'CANTIDAD': [336, 358, 342, int(t_c)], 'EN MILLONES': ["76.000", "218.000", "338.000", f"{nc_millones:,.3f}".replace(',', '.')], '% SOBRE VENTA': [0.0486, 0.0438, 0.0548, pct_26]})
                st.markdown(render_lista(df_hist_anual, st.session_state['d_nc26_raw'], 'COMPARATIVA ANUAL', ['CANTIDAD', 'EN MILLONES', '% SOBRE VENTA']), unsafe_allow_html=True)

        df_m1 = pd.DataFrame({'Mes': meses_activos, 'Cantidad': d26_calc['cantidad'], 'Monto NC': d26_calc['nc'], 'Total Venta': d26_calc['ventas']})
        df_m1['% s/Total NC'] = np.where(d26_calc['nc'].sum()!=0, df_m1['Monto NC'] / d26_calc['nc'].sum(), 0)
        df_m1['% s/Total Venta'] = np.where(df_m1['Total Venta']!=0, df_m1['Monto NC'] / df_m1['Total Venta'].abs(), 0)
        c1, c2 = st.columns(2)
        with c1: 
            st.markdown("<h2>Resumen de Notas de Crédito</h2>", unsafe_allow_html=True)
            st.markdown(render_lista(df_m1, st.session_state['d_nc26_raw'], 'Mes', ['Cantidad', 'Monto NC', '% s/Total NC']), unsafe_allow_html=True)
        with c2: 
            st.markdown("<h2>Relación Venta vs NC</h2>", unsafe_allow_html=True)
            st.markdown(render_lista(df_m1, st.session_state['d_nc26_raw'], 'Mes', ['Total Venta', 'Monto NC', '% s/Total Venta']), unsafe_allow_html=True)

        c3, c4 = st.columns(2)
        with c3:
            st.markdown("<h2>Días Hábiles & Frecuencia</h2>", unsafe_allow_html=True)
            cant_2024 = [48, 27, 18, 28, 29, 13, 23, 19, 19, 30, 45, 59][:max_mes]
            df_m2 = pd.DataFrame({'Mes': meses_activos, 'Cant 2024': cant_2024, 'Cant 2025': d25_calc['cantidad'], 'Cant 2026': d26_calc['cantidad']})
            st.markdown(render_lista(df_m2, st.session_state['d_nc26_raw'], 'Mes', ['Cant 2024', 'Cant 2025', 'Cant 2026']), unsafe_allow_html=True)
        with c4:
            st.markdown("<h2>Comparativa % Venta Año a Año</h2>", unsafe_allow_html=True)
            df_m3 = pd.DataFrame({'Mes': meses_activos})
            df_m3['2025 (%)'] = np.where(d25_calc['ventas']!=0, d25_calc['nc']/d25_calc['ventas'].abs(), 0)
            df_m3['2026 (%)'] = np.where(d26_calc['ventas']!=0, d26_calc['nc']/d26_calc['ventas'].abs(), 0)
            df_m3['Variación'] = df_m3['2026 (%)'] - df_m3['2025 (%)']
            st.markdown(render_lista(df_m3, st.session_state['d_nc26_raw'], 'Mes', ['2025 (%)', '2026 (%)', 'Variación']), unsafe_allow_html=True)

        st.markdown("<br><h2>Evolución Trimestral (24-25-26)</h2>", unsafe_allow_html=True)
        cant_24_full = [48, 27, 18, 28, 29, 13, 23, 19, 19, 30, 45, 59]
        d25_full = calc_m(v25_raw, d25_raw, 12)
        q24 = [sum(cant_24_full[0:3]), sum(cant_24_full[3:6]), sum(cant_24_full[6:9]), sum(cant_24_full[9:12])]
        q25 = [d25_full['cantidad'][0:3].sum(), d25_full['cantidad'][3:6].sum(), d25_full['cantidad'][6:9].sum(), d25_full['cantidad'][9:12].sum()]
        q26 = [d26_calc['cantidad'][0:3].sum(), d26_calc['cantidad'][3:6].sum() if max_mes>=6 else 0, d26_calc['cantidad'][6:9].sum() if max_mes>=9 else 0, d26_calc['cantidad'][9:12].sum() if max_mes>=12 else 0]
        
        df_trimestral = pd.DataFrame({'Trimestre': ['Q1', 'Q2', 'Q3', 'Q4'] * 3, 'Año': ['2024']*4 + ['2025']*4 + ['2026']*4, 'Cantidad': q24 + q25 + q26})
        chart_trim = alt.Chart(df_trimestral).mark_bar().encode(
            x=alt.X('Año:N', title=None, axis=alt.Axis(labels=False, ticks=False)), y=alt.Y('Cantidad:Q'),
            color=alt.Color('Año:N', scale=alt.Scale(range=['#4bc0c0', '#36a2eb', '#ff4b4b'])),
            column=alt.Column('Trimestre:N', title=None, header=alt.Header(labelOrient='bottom', labelFontSize=14, labelFontWeight='bold'))
        ).properties(width=200, height=250)
        st.altair_chart(chart_trim, use_container_width=False)

# --- SOLAPAS DE ANÁLISIS DETALLADO ---
if 'd_nc26_raw' in st.session_state and not st.session_state['d_nc26_raw'].empty:
    
    def armar_seccion(df_crudo, col_agrupar, titulo, es_error=False, tipo_grafico="barras_h"):
        if es_error: df_crudo = df_crudo[df_crudo['referencia 1'].astype(str).str.strip().str.upper() == 'ERROR DE CARGA'] if 'referencia 1' in df_crudo.columns else df_crudo
        
        if filtro_tiempo == "Todo el Año":
            st.markdown(f"<br><h2 style='font-size: 2.2rem;'>{titulo}</h2>", unsafe_allow_html=True)
            t_actual = (df_crudo['mes'].max() - 1) // 3 + 1
            df_trim = df_crudo[df_crudo['trimestre'] == t_actual]
            
            st.markdown(f"<h2>📅 Trimestre Actual (Q{int(t_actual)})</h2>", unsafe_allow_html=True)
            if col_agrupar in df_trim.columns and not df_trim.empty:
                df_trim_abs = df_trim.copy()
                if 'total bruto origen' in df_trim_abs.columns: df_trim_abs['total bruto origen'] = df_trim_abs['total bruto origen'].abs()
                ag_trim = df_trim_abs.groupby(col_agrupar).agg(Cant=('numero', 'count'), Total=('total bruto origen', 'sum')).reset_index().sort_values('Cant', ascending=False).head(10).reset_index(drop=True)
                ag_trim['Color'] = PALETA_COLORES[:len(ag_trim)]
                cA, cB = st.columns([1.1, 1.3])
                with cA: st.markdown(render_lista(ag_trim, df_trim, col_agrupar, ['Cant', 'Total'], ranking=True, desglosar=True), unsafe_allow_html=True)
                with cB: 
                    if tipo_grafico == "barras_h": st.altair_chart(grafico_barras_h(ag_trim, col_agrupar, 'Cant'), use_container_width=True)
                    elif tipo_grafico == "torta": st.altair_chart(grafico_torta(ag_trim, col_agrupar, 'Cant'), use_container_width=True)
                    else: st.altair_chart(grafico_barras_v(ag_trim, col_agrupar, 'Cant'), use_container_width=True)
            else: st.info("No hay datos para este trimestre.")

            st.markdown("<br><h2>📈 Acumulado Anual 2026</h2>", unsafe_allow_html=True)
            if col_agrupar in df_crudo.columns and not df_crudo.empty:
                df_crudo_abs = df_crudo.copy()
                if 'total bruto origen' in df_crudo_abs.columns: df_crudo_abs['total bruto origen'] = df_crudo_abs['total bruto origen'].abs()
                ag_acum = df_crudo_abs.groupby(col_agrupar).agg(Cant=('numero', 'count'), Total=('total bruto origen', 'sum')).reset_index().sort_values('Cant', ascending=False).head(10).reset_index(drop=True)
                ag_acum['Color'] = PALETA_COLORES[:len(ag_acum)]
                cC, cD = st.columns([1.1, 1.3])
                with cC: st.markdown(render_lista(ag_acum, df_crudo, col_agrupar, ['Cant', 'Total'], ranking=True, desglosar=True), unsafe_allow_html=True)
                with cD: 
                    if tipo_grafico == "barras_h": st.altair_chart(grafico_barras_h(ag_acum, col_agrupar, 'Cant'), use_container_width=True)
                    elif tipo_grafico == "torta": st.altair_chart(grafico_torta(ag_acum, col_agrupar, 'Cant'), use_container_width=True)
                    else: st.altair_chart(grafico_barras_v(ag_acum, col_agrupar, 'Cant'), use_container_width=True)
        else:
            df_filtrado = filtrar_df(df_crudo, filtro_tiempo)
            if col_agrupar in df_filtrado.columns and not df_filtrado.empty:
                df_filtrado_abs = df_filtrado.copy()
                if 'total bruto origen' in df_filtrado_abs.columns: df_filtrado_abs['total bruto origen'] = df_filtrado_abs['total bruto origen'].abs()
                ag_data = df_filtrado_abs.groupby(col_agrupar).agg(Cant=('numero', 'count'), Total=('total bruto origen', 'sum')).reset_index().sort_values('Cant', ascending=False).head(10).reset_index(drop=True)
                ag_data['Color'] = PALETA_COLORES[:len(ag_data)]
                cA, cB = st.columns([1.1, 1.3])
                with cA: st.markdown(render_lista(ag_data, df_filtrado, col_agrupar, ['Cant', 'Total'], ranking=True, desglosar=True), unsafe_allow_html=True)
                with cB: 
                    if tipo_grafico == "barras_h": st.altair_chart(grafico_barras_h(ag_data, col_agrupar, 'Cant'), use_container_width=True)
                    elif tipo_grafico == "torta": st.altair_chart(grafico_torta(ag_data, col_agrupar, 'Cant'), use_container_width=True)
                    else: st.altair_chart(grafico_barras_v(ag_data, col_agrupar, 'Cant'), use_container_width=True)
            else: st.info(f"No hay datos registrados en {filtro_tiempo}.")

    with tab_top10: armar_seccion(st.session_state['d_nc26_raw'], 'nombre cliente', "Análisis Top 10 Clientes", tipo_grafico="barras_h")
    with tab_motivo: armar_seccion(st.session_state['d_nc26_raw'], 'referencia 1', "Análisis de Motivos", tipo_grafico="torta")
    with tab_error: armar_seccion(st.session_state['d_nc26_raw'], 'cobrador cliente', "Análisis de Cobrador", es_error=True, tipo_grafico="barras_v")
