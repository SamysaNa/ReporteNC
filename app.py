import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import io
import xlsxwriter
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Reporte de Notas de Crédito", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS ---
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

.badge { 
    width: 100%; max-width: 95px; padding: 2px 6px; border-radius: 6px; font-weight: 800; font-size: 0.85rem; 
    display: flex; align-items: center; justify-content: flex-end; gap: 4px; text-align: right; white-space: nowrap;
}
.badge-neutral { background: transparent; color: #4a5568; }
.badge-alerta { background: rgba(255, 75, 75, 0.12); color: #c53030; }
.badge-warn { background: rgba(255, 193, 7, 0.15); color: #b8860b; }
.badge-ok { background: rgba(40, 167, 69, 0.12); color: #22543d; }
</style>
""", unsafe_allow_html=True)

PALETA_COLORES = ['#ff1a1a', '#ff5555', '#ff7f50', '#ffa07a', '#ffb347', '#ffd700', '#d4e157', '#9ece6a', '#48c774', '#20b2aa']

# --- FUNCIONES DE EXPORTACIÓN Y GOOGLE SHEETS ---
def generar_excel_formateado(diccionario_dfs):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # Definición de formatos visuales para Excel
    formato_header = workbook.add_format({'bold': True, 'bg_color': '#2d3748', 'font_color': 'white', 'border': 1})
    formato_plata = workbook.add_format({'num_format': '$ #,##0.00', 'border': 1})
    formato_pct = workbook.add_format({'num_format': '0.00%', 'border': 1})
    formato_alerta = workbook.add_format({'bg_color': '#fed7d7', 'font_color': '#c53030', 'num_format': '0.00%', 'border': 1})
    formato_ok = workbook.add_format({'bg_color': '#c6f6d5', 'font_color': '#22543d', 'num_format': '0.00%', 'border': 1})
    formato_normal = workbook.add_format({'border': 1})

    for nombre_hoja, df in diccionario_dfs.items():
        worksheet = workbook.add_worksheet(nombre_hoja)
        # Escribir encabezados
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, formato_header)
            worksheet.set_column(col_num, col_num, 18) # Ajustar ancho de columnas

        # Escribir datos con lógica de color
        for row_num, row_data in enumerate(df.values):
            for col_num, value in enumerate(row_data):
                col_name = df.columns[col_num]
                
                if pd.isna(value):
                    worksheet.write(row_num + 1, col_num, "", formato_normal)
                    continue
                    
                if 'Total' in col_name or 'Monto' in col_name:
                    worksheet.write_number(row_num + 1, col_num, float(value), formato_plata)
                elif '%' in col_name or 'Variación' in col_name or 'SOBRE VENTA' in col_name:
                    val_pct = float(value)
                    # Aplicar formato de color si supera los umbrales de alerta
                    if val_pct > 0.05:
                        worksheet.write_number(row_num + 1, col_num, val_pct, formato_alerta)
                    elif val_pct <= 0:
                        worksheet.write_number(row_num + 1, col_num, val_pct, formato_ok)
                    else:
                        worksheet.write_number(row_num + 1, col_num, val_pct, formato_pct)
                else:
                    worksheet.write(row_num + 1, col_num, value, formato_normal)

    workbook.close()
    output.seek(0)
    return output

def guardar_en_sheets(df, nombre_hoja):
    # Esta función requiere configurar st.secrets["gcp_service_account"]
    try:
        if "gcp_service_account" not in st.secrets:
            return False, "Falta configurar las credenciales de Google (secrets) en Streamlit Cloud."
            
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        
        # Necesitas poner el ID de tu Google Sheet aquí (la parte larga de la URL de tu sheet)
        ID_DEL_SHEET = "REEMPLAZAR_CON_TU_ID_DE_SHEET" 
        if ID_DEL_SHEET == "REEMPLAZAR_CON_TU_ID_DE_SHEET":
            return False, "Falta configurar el ID_DEL_SHEET en el código."

        sheet = client.open_by_key(ID_DEL_SHEET)
        
        try:
            worksheet = sheet.worksheet(nombre_hoja)
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=nombre_hoja, rows="100", cols="20")
            
        worksheet.update([df.columns.values.tolist()] + df.fillna("").values.tolist())
        return True, f"Datos guardados exitosamente en la pestaña '{nombre_hoja}'."
    except Exception as e:
        return False, str(e)

# --- FUNCIONES DE FORMATO Y RENDERIZADO VISUAL ---
def tarjeta_kpi(titulo, valor):
    return f"""<div class="kpi-card kpi-rojo"><div class="kpi-titulo">{titulo}</div><div class="kpi-valor">🔴 ⬆ {valor}</div></div>"""

def formato_arg(n):
    if pd.isna(n) or n == 0: return "0,00"
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formato_pct(n):
    if pd.isna(n) or n == 0: return "0,00%"
    return f"{abs(n)*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")

def icono_cantidad(val):
    if val < 20: return "badge-ok", f"✔️ {int(val)}"
    elif val <= 30: return "badge-warn", f"⚠️ {int(val)}"
    else: return "badge-alerta", f"❌ {int(val)}"

def render_lista(df, col_titulo, cols_datos, ranking=False):
    html = "<div class='tabla-canchera'><div class='fila-header'>"
    html += f"<div class='celda-header-titulo'>{col_titulo}</div>"
    for c in cols_datos: html += f"<div class='celda-header-valor'>{c}</div>"
    html += "</div>"

    for _, row in df.iterrows():
        estilo_borde = f"border: 2px solid {row['Color']}; box-shadow: 0 0 10px {row['Color']}60;" if ranking and 'Color' in row else "border: 1px solid #edf2f7;"
        html += f"<div class='fila-canchera' style='{estilo_borde}'><div class='celda-titulo' title='{row[col_titulo]}'>{row[col_titulo]}</div>"
        
        for c in cols_datos:
            val = row[c]
            clase_extra, txt_val = "badge-neutral", ""
            
            if 'Variación' in c:
                txt_val = formato_pct(val)
                if val > 0: clase_extra, txt_val = "badge-alerta", f"❌ {txt_val}"
                elif val < 0: clase_extra, txt_val = "badge-ok", f"✔️ {txt_val}"
            elif '%' in c or 'SOBRE VENTA' in c:
                txt_val = formato_pct(val)
                if val > 0.05: clase_extra, txt_val = "badge-alerta", f"❌ {txt_val}"
                elif val > 0.02: clase_extra, txt_val = "badge-warn", f"⚠️ {txt_val}"
                else: clase_extra, txt_val = "badge-ok", f"✔️ {txt_val}"
            elif 'Cant 20' in c or c == 'CANTIDAD':
                clase_extra, txt_val = icono_cantidad(val)
            elif 'Total' in c or 'Monto' in c: 
                txt_val = f"$&nbsp;{formato_arg(val)}"
            elif 'Cantidad' in c or 'Cant' in c: txt_val = str(int(val))
            else: txt_val = str(val)

            html += f"<div class='celda-valor'><div class='badge {clase_extra}'>{txt_val}</div></div>"
        html += "</div>"
    html += "</div>"
    return html

def grafico_barras_v(df, x_col, y_col):
    return alt.Chart(df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X(x_col, sort=alt.EncodingSortField(field='Cant', order='descending'), title='', axis=alt.Axis(labelAngle=-45)), 
        y=alt.Y(y_col, title=''), color=alt.Color('Color:N', scale=None, legend=None), tooltip=[x_col, y_col]
    ).properties(height=320)

def grafico_barras_h(df, x_col, y_col):
    return alt.Chart(df).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
        y=alt.Y(x_col, sort=alt.EncodingSortField(field='Cant', order='descending'), title=''), x=alt.X(y_col, title=''),
        color=alt.Color('Color:N', scale=None, legend=None), tooltip=[x_col, y_col]
    ).properties(height=320)

def grafico_torta(df, x_col, y_col):
    return alt.Chart(df).mark_arc(innerRadius=60).encode(
        theta=alt.Theta(field=y_col, type="quantitative"),
        color=alt.Color(field=x_col, type="nominal", scale=alt.Scale(range=PALETA_COLORES), sort=alt.EncodingSortField(field='Cant', order='descending'), legend=alt.Legend(title="", orient="bottom")),
        tooltip=[x_col, y_col]
    ).properties(height=320)

# --- 🔒 LOGIN ---
PASS_ADMIN = "admin123"
if "rol" not in st.session_state: st.session_state.rol = None
if not st.session_state.rol:
    st.title("🔒 Acceso al Sistema")
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if pwd == PASS_ADMIN: st.session_state.rol = "admin"; st.rerun()
        else: st.error("Clave incorrecta.")
    st.stop() 

# --- PANEL LATERAL: EXPORTACIÓN (Solo Admin) ---
if st.session_state.rol == "admin":
    with st.sidebar:
        st.header("💾 Exportar y Guardar")
        if 'd_nc26' in st.session_state:
            st.success("Datos listos para exportar")
            
            # Preparar los DataFrames que queremos exportar
            df_nc = st.session_state['d_nc26']
            top_clientes = df_nc.groupby('nombre cliente').agg(Cant=('numero', 'count'), Total=('importe total origen', 'sum')).reset_index().sort_values('Cant', ascending=False)
            top_motivos = df_nc.groupby('referencia 1').agg(Cant=('numero', 'count'), Total=('importe total origen', 'sum')).reset_index().sort_values('Cant', ascending=False)
            
            diccionario_exportar = {
                "Data Cruda 2026": df_nc,
                "Top Clientes": top_clientes,
                "Motivos NC": top_motivos
            }
            
            # Botón Descargar Excel
            excel_data = generar_excel_formateado(diccionario_exportar)
            st.download_button(
                label="📥 Descargar Reporte en Excel",
                data=excel_data,
                file_name="Reporte_NC_Format.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Botón Guardar Sheets
            st.markdown("---")
            if st.button("☁️ Sincronizar con Google Sheets"):
                with st.spinner("Conectando con Google..."):
                    exito, mensaje = guardar_en_sheets(top_clientes, "Top Clientes")
                    if exito:
                        st.success(mensaje)
                    else:
                        st.error(mensaje)
        else:
            st.warning("Procesa los archivos primero para habilitar la exportación.")
        
        st.markdown("---")
        if st.button("Cerrar Sesión"): st.session_state.rol = None; st.rerun()

# --- 📊 APLICACIÓN PRINCIPAL ---
st.title("📊 Análisis de Reportes NC")
tab_analisis, tab_top10, tab_motivo, tab_error = st.tabs(["Dashboard", "Top 10 Clientes", "Motivos", "Error Carga"])

# --- SOLAPA 1: DASHBOARD ---
with tab_analisis:
    with st.expander("📂 Archivos y Configuración", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1: file_fcp = st.file_uploader("Facturación 2026", type=['xlsx'])
        with col2: file_nc = st.file_uploader("Notas Crédito 2026", type=['xlsx'])
        with col3: file_historico = st.file_uploader("Histórico 2025", type=['xlsx'])
        
        if st.button("Procesar Datos", type="primary"):
            if file_fcp and file_nc and file_historico:
                try:
                    df_v, df_n, df_h = pd.read_excel(file_fcp, header=2), pd.read_excel(file_nc, header=2), pd.read_excel(file_historico, header=2)
                    for d in [df_v, df_n, df_h]: d.columns = (d.columns.str.lower().str.strip().str.replace('ú', 'u').str.replace('í', 'i').str.replace('ó', 'o').str.replace('á', 'a').str.replace('é', 'e'))
                    df_v, df_n, df_h = df_v.drop_duplicates(subset=['numero']), df_n.drop_duplicates(subset=['numero']), df_h.drop_duplicates(subset=['numero'])
                    df_h['fecha'] = pd.to_datetime(df_h['fecha'], errors='coerce')
                    df_h = df_h[df_h['fecha'] >= '2025-01-01']
                    df_h_nc = df_h[df_h['tipo'].astype(str).str.contains('NC', case=False, na=False)] if 'tipo' in df_h.columns else df_h
                    df_h_v = df_h[~df_h['tipo'].astype(str).str.contains('NC|ND', case=False, na=False)] if 'tipo' in df_h.columns else pd.DataFrame(columns=df_h.columns)
                    st.session_state['d_nc26'], st.session_state['d_v26'], st.session_state['d_nc25'], st.session_state['d_v25'] = df_n, df_v, df_h_nc, df_h_v
                except Exception as e: st.error(f"Error: {e}")

    if 'd_nc26' in st.session_state:
        st.session_state['d_nc26']['mes'] = pd.to_datetime(st.session_state['d_nc26']['fecha']).dt.month
        max_mes = int(st.session_state['d_nc26']['mes'].max()) if not st.session_state['d_nc26'].empty else 12
        meses_completos = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        meses_activos = meses_completos[:max_mes]

        def calc_m(df_v, df_nc, max_m):
            df_v['mes'], df_nc['mes'] = pd.to_datetime(df_v['fecha']).dt.month, pd.to_datetime(df_nc['fecha']).dt.month
            c = pd.DataFrame({'mes': range(1, max_m+1)})
            c = c.merge(df_v.groupby('mes')['importe total origen'].sum().reset_index(), on='mes', how='left').rename(columns={'importe total origen': 'ventas'})
            c = c.merge(df_nc.groupby('mes')['importe total origen'].sum().reset_index(), on='mes', how='left').rename(columns={'importe total origen': 'nc'})
            c = c.merge(df_nc.groupby('mes')['numero'].count().reset_index(), on='mes', how='left').rename(columns={'numero': 'cantidad'})
            return c.fillna(0)

        d26, d25 = calc_m(st.session_state['d_v26'], st.session_state['d_nc26'], max_mes), calc_m(st.session_state['d_v25'], st.session_state['d_nc25'], max_mes)

        st.markdown("<h1 style='font-size: 3.5rem; font-weight: 900; color: #1a202c; margin-top: 10px; margin-bottom: 10px;'>2026</h1>", unsafe_allow_html=True)
        
        t_nc, t_c = d26['nc'].sum(), d26['cantidad'].sum()
        k1, k2, k3 = st.columns([1, 1, 2])
        with k1: st.markdown(tarjeta_kpi("Total NC Emitidas", int(t_c)), unsafe_allow_html=True)
        with k2: st.markdown(tarjeta_kpi("Monto Total NC", f"$ {formato_arg(t_nc)}"), unsafe_allow_html=True)
        with k3:
            v_26_mill = (d26['ventas'].sum() / 1000000) if d26['ventas'].sum() != 0 else 0
            pct_26 = (t_nc / d26['ventas'].sum()) if d26['ventas'].sum() != 0 else 0
            df_hist_anual = pd.DataFrame({
                'AÑO': ['2023', '2024', '2025', '2026 (Parcial)'],
                'CANTIDAD': [336, 358, 342, int(t_c)],
                'EN MILLONES': ["76.000", "218.000", "338.000", f"{v_26_mill:,.3f}".replace(',', '.')],
                '% SOBRE VENTA': [0.0486, 0.0438, 0.0548, pct_26]
            })
            st.markdown(render_lista(df_hist_anual, 'AÑO', ['CANTIDAD', 'EN MILLONES', '% SOBRE VENTA']), unsafe_allow_html=True)

        df_m1 = pd.DataFrame({'Mes': meses_activos, 'Cantidad': d26['cantidad'], 'Monto NC': d26['nc'], 'Total Venta': d26['ventas']})
        df_m1['% s/Total NC'] = np.where(t_nc!=0, df_m1['Monto NC'].abs() / abs(t_nc), 0)
        df_m1['% s/Total Venta'] = np.where(df_m1['Total Venta']!=0, df_m1['Monto NC'].abs() / df_m1['Total Venta'].abs(), 0)
        c1, c2 = st.columns(2)
        with c1: 
            st.markdown("<h2>Resumen de Notas de Crédito</h2>", unsafe_allow_html=True)
            st.markdown(render_lista(df_m1, 'Mes', ['Cantidad', 'Monto NC', '% s/Total NC']), unsafe_allow_html=True)
        with c2: 
            st.markdown("<h2>Relación Venta vs NC</h2>", unsafe_allow_html=True)
            st.markdown(render_lista(df_m1, 'Mes', ['Total Venta', 'Monto NC', '% s/Total Venta']), unsafe_allow_html=True)

        c3, c4 = st.columns(2)
        with c3:
            st.markdown("<h2>Días Hábiles & Frecuencia</h2>", unsafe_allow_html=True)
            cant_2024 = [48, 27, 18, 28, 29, 13, 23, 19, 19, 30, 45, 59][:max_mes]
            df_m2 = pd.DataFrame({'Mes': meses_activos, 'Cant 2024': cant_2024, 'Cant 2025': d25['cantidad'], 'Cant 2026': d26['cantidad']})
            st.markdown(render_lista(df_m2, 'Mes', ['Cant 2024', 'Cant 2025', 'Cant 2026']), unsafe_allow_html=True)
        with c4:
            st.markdown("<h2>Comparativa % Venta Año a Año</h2>", unsafe_allow_html=True)
            df_m3 = pd.DataFrame({'Mes': meses_activos})
            df_m3['2025 (%)'] = np.where(d25['ventas']!=0, d25['nc'].abs()/d25['ventas'].abs(), 0)
            df_m3['2026 (%)'] = np.where(d26['ventas']!=0, d26['nc'].abs()/d26['ventas'].abs(), 0)
            df_m3['Variación'] = df_m3['2026 (%)'] - df_m3['2025 (%)']
            st.markdown(render_lista(df_m3, 'Mes', ['2025 (%)', '2026 (%)', 'Variación']), unsafe_allow_html=True)

        st.markdown("<br><h2>Evolución Trimestral (24-25-26)</h2>", unsafe_allow_html=True)
        cant_24_full = [48, 27, 18, 28, 29, 13, 23, 19, 19, 30, 45, 59]
        d25_full = calc_m(st.session_state['d_v25'], st.session_state['d_nc25'], 12)
        q24 = [sum(cant_24_full[0:3]), sum(cant_24_full[3:6]), sum(cant_24_full[6:9]), sum(cant_24_full[9:12])]
        q25 = [d25_full['cantidad'][0:3].sum(), d25_full['cantidad'][3:6].sum(), d25_full['cantidad'][6:9].sum(), d25_full['cantidad'][9:12].sum()]
        q26 = [d26['cantidad'][0:3].sum(), d26['cantidad'][3:6].sum(), d26['cantidad'][6:9].sum(), d26['cantidad'][9:12].sum()] if max_mes >= 12 else [d26['cantidad'][0:3].sum(), d26['cantidad'][3:6].sum() if max_mes>=6 else 0, d26['cantidad'][6:9].sum() if max_mes>=9 else 0, d26['cantidad'][9:12].sum() if max_mes>=12 else 0]
        
        df_trimestral = pd.DataFrame({
            'Trimestre': ['Q1', 'Q2', 'Q3', 'Q4'] * 3, 'Año': ['2024']*4 + ['2025']*4 + ['2026']*4, 'Cantidad': q24 + q25 + q26
        })
        chart_trim = alt.Chart(df_trimestral).mark_bar().encode(
            x=alt.X('Año:N', title=None, axis=alt.Axis(labels=False, ticks=False)),
            y=alt.Y('Cantidad:Q'),
            color=alt.Color('Año:N', scale=alt.Scale(range=['#4bc0c0', '#36a2eb', '#ff4b4b'])),
            column=alt.Column('Trimestre:N', title=None, header=alt.Header(labelOrient='bottom', labelFontSize=14, labelFontWeight='bold'))
        ).properties(width=200, height=250)
        st.altair_chart(chart_trim, use_container_width=False)

# --- SOLAPAS DE ANÁLISIS ---
if 'd_nc26' in st.session_state:
    d_nc = st.session_state['d_nc26']
    trimestre_actual = (int(d_nc['mes'].max()) - 1) // 3 + 1 if not d_nc.empty else 1
    d_nc['trimestre'] = (d_nc['mes'] - 1) // 3 + 1
    d_nc_trim = d_nc[d_nc['trimestre'] == trimestre_actual]

    def armar_seccion_doble(df_trim, df_acum, col_agrupar, titulo, es_error_carga=False, tipo_grafico="barras_h"):
        if es_error_carga:
            df_trim = df_trim[df_trim['referencia 1'].astype(str).str.contains('ERROR', case=False, na=False)] if 'referencia 1' in df_trim.columns else df_trim
            df_acum = df_acum[df_acum['referencia 1'].astype(str).str.contains('ERROR', case=False, na=False)] if 'referencia 1' in df_acum.columns else df_acum

        st.markdown(f"<br><h2 style='font-size: 2.2rem;'>{titulo}</h2>", unsafe_allow_html=True)
        
        st.markdown(f"<h2>📅 Trimestre Actual (Q{trimestre_actual})</h2>", unsafe_allow_html=True)
        if col_agrupar in df_trim.columns and not df_trim.empty:
            ag_trim = df_trim.groupby(col_agrupar).agg(Cant=('numero', 'count'), Total=('importe total origen', 'sum')).reset_index().sort_values('Cant', ascending=False).head(10).reset_index(drop=True)
            ag_trim['Color'] = PALETA_COLORES[:len(ag_trim)]
            cA, cB = st.columns([1.1, 1.3])
            with cA: st.markdown(render_lista(ag_trim, col_agrupar, ['Cant', 'Total'], ranking=True), unsafe_allow_html=True)
            with cB: 
                if tipo_grafico == "barras_h": st.altair_chart(grafico_barras_h(ag_trim, col_agrupar, 'Cant'), use_container_width=True)
                elif tipo_grafico == "torta": st.altair_chart(grafico_torta(ag_trim, col_agrupar, 'Cant'), use_container_width=True)
                else: st.altair_chart(grafico_barras_v(ag_trim, col_agrupar, 'Cant'), use_container_width=True)
        else: st.info("No hay datos para este trimestre.")

        st.markdown("<br><h2>📈 Acumulado Anual 2026</h2>", unsafe_allow_html=True)
        if col_agrupar in df_acum.columns and not df_acum.empty:
            ag_acum = df_acum.groupby(col_agrupar).agg(Cant=('numero', 'count'), Total=('importe total origen', 'sum')).reset_index().sort_values('Cant', ascending=False).head(10).reset_index(drop=True)
            ag_acum['Color'] = PALETA_COLORES[:len(ag_acum)]
            cC, cD = st.columns([1.1, 1.3])
            with cC: st.markdown(render_lista(ag_acum, col_agrupar, ['Cant', 'Total'], ranking=True), unsafe_allow_html=True)
            with cD: 
                if tipo_grafico == "barras_h": st.altair_chart(grafico_barras_h(ag_acum, col_agrupar, 'Cant'), use_container_width=True)
                elif tipo_grafico == "torta": st.altair_chart(grafico_torta(ag_acum, col_agrupar, 'Cant'), use_container_width=True)
                else: st.altair_chart(grafico_barras_v(ag_acum, col_agrupar, 'Cant'), use_container_width=True)

    with tab_top10: armar_seccion_doble(d_nc_trim, d_nc, 'nombre cliente', "Análisis Top 10 Clientes", tipo_grafico="barras_h")
    with tab_motivo: armar_seccion_doble(d_nc_trim, d_nc, 'referencia 1', "Análisis de Motivos", tipo_grafico="torta")
    with tab_error: armar_seccion_doble(d_nc_trim, d_nc, 'cobrador cliente', "Análisis de Error de Carga", es_error_carga=True, tipo_grafico="barras_v")
