import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Reporte de Notas de Crédito", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS (ALINEACIÓN PERFECTA Y SOMBRAS NEÓN) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Nunito', sans-serif !important; }

/* Títulos de Solapas Gigantes */
button[role="tab"] { background-color: transparent !important; border: none !important; border-bottom: 5px solid transparent !important; padding-bottom: 10px !important; margin-right: 20px !important; }
button[role="tab"] p { font-size: 2rem !important; font-weight: 900 !important; color: #a0aec0 !important; transition: all 0.2s ease; }
button[role="tab"][aria-selected="true"] { border-bottom: 5px solid #ff4b4b !important; }
button[role="tab"][aria-selected="true"] p { color: #ff4b4b !important; font-size: 2.1rem !important; }

/* Tarjetas KPI compactas */
.kpi-card { background-color: white; border-radius: 12px; padding: 10px; margin: 5px 0; text-align: center; border: 2px solid #e2e8f0; }
.kpi-rojo { border-color: #ff4b4b; color: #ff4b4b; background-color: rgba(255, 75, 75, 0.05); }
.kpi-titulo { font-size: 13px; font-weight: 900; text-transform: uppercase; }
.kpi-valor { font-size: 24px; font-weight: 900; }

/* Títulos de Secciones */
h2 { font-size: 1.8rem !important; font-weight: 900 !important; color: #2d3748 !important; margin-top: 1rem !important; margin-bottom: 0.5rem !important; }

/* Sistema de Cuadros 100% Alineados */
.tabla-canchera { width: 100%; display: flex; flex-direction: column; margin-bottom: 20px; }
.fila-header { display: flex; width: 100%; border-bottom: 2px solid #edf2f7; padding: 2px 10px; margin-bottom: 4px; }
.celda-header-titulo { flex: 0 0 120px; font-size: 0.75rem; font-weight: 900; color: #718096; text-transform: uppercase; text-align: left; }
.celda-header-valor { flex: 1; text-align: center; font-size: 0.75rem; font-weight: 900; color: #718096; text-transform: uppercase; }

.fila-canchera { display: flex; width: 100%; align-items: center; background: #ffffff; border-radius: 8px; padding: 2px 10px; margin-bottom: 5px; transition: transform 0.1s; }
.fila-canchera:hover { transform: scale(1.01); }
.celda-titulo { flex: 0 0 120px; font-weight: 800; color: #2d3748; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: left; }
.celda-valor { flex: 1; display: flex; justify-content: center; }

/* Badges con Ancho Fijo Estricto y Sin Salto de Línea (No-wrap) */
.badge { 
    width: 100%; max-width: 105px; padding: 2px 6px; border-radius: 6px; font-weight: 800; font-size: 0.85rem; 
    display: flex; align-items: center; justify-content: center; gap: 4px; text-align: center;
    white-space: nowrap; /* Evita que el $ salte de línea */
}
.badge-neutral { background: transparent; color: #4a5568; }
.badge-alerta { background: rgba(255, 75, 75, 0.12); color: #c53030; }
.badge-ok { background: rgba(40, 167, 69, 0.12); color: #22543d; }
</style>
""", unsafe_allow_html=True)

# --- PALETA DE COLORES PERSONALIZADA (Verde Agua -> Rojo Sangre) ---
# Se aplica a los gráficos y a los bordes de las tablas de ranking.
PALETA_COLORES = ['#20b2aa', '#48c774', '#9ece6a', '#d4e157', '#ffd700', '#ffb347', '#ffa07a', '#ff7f50', '#ff5555', '#ff1a1a']
PALETA_INVERTIDA = PALETA_COLORES[::-1] # Rojo primero (para iterar en la tabla de Mayor a Menor)

# --- FUNCIONES DE FORMATO Y RENDERIZADO ---
def tarjeta_kpi(titulo, valor):
    return f"""<div class="kpi-card kpi-rojo"><div class="kpi-titulo">{titulo}</div><div class="kpi-valor">🔴 ⬆ {valor}</div></div>"""

def formato_arg(numero):
    if pd.isna(numero) or numero == 0: return "0,00"
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formato_pct(numero):
    if pd.isna(numero) or numero == 0: return "0,00%"
    return f"{abs(numero)*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")

def render_lista(df, col_titulo, cols_datos, ranking=False):
    html = "<div class='tabla-canchera'><div class='fila-header'>"
    html += f"<div class='celda-header-titulo'>{col_titulo}</div>"
    for c in cols_datos: html += f"<div class='celda-header-valor'>{c}</div>"
    html += "</div>"

    for i, (_, row) in enumerate(df.iterrows()):
        # Lógica de reborde brillante según ranking
        estilo_borde = ""
        if ranking:
            color = PALETA_INVERTIDA[i % len(PALETA_INVERTIDA)]
            estilo_borde = f"border: 2px solid {color}; box-shadow: 0 0 10px {color}60;"
        else:
            estilo_borde = "border: 1px solid #edf2f7;"

        html += f"<div class='fila-canchera' style='{estilo_borde}'>"
        html += f"<div class='celda-titulo' title='{row[col_titulo]}'>{row[col_titulo]}</div>"
        for c in cols_datos:
            val = row[c]
            clase_extra = "badge-neutral"
            txt_val = ""
            
            if 'Variación' in c:
                txt_val = formato_pct(val)
                if val > 0: clase_extra, txt_val = "badge-alerta", f"🔴 {txt_val}"
                elif val < 0: clase_extra, txt_val = "badge-ok", f"✔️ {txt_val}"
            elif '%' in c:
                txt_val = formato_pct(val)
                if val > 0.05: clase_extra, txt_val = "badge-alerta", f"❌ {txt_val}"
                elif val > 0.02: clase_extra, txt_val = "badge-alerta", f"🔴 {txt_val}"
                else: clase_extra, txt_val = "badge-ok", f"✔️ {txt_val}"
            elif 'Total' in c or 'Monto' in c: 
                txt_val = f"$&nbsp;{formato_arg(val)}" # &nbsp; asegura que el $ no se separe del número
            elif 'Cantidad' in c or 'Cant' in c: 
                txt_val = str(int(val))
            else: 
                txt_val = str(val)

            html += f"<div class='celda-valor'><div class='badge {clase_extra}'>{txt_val}</div></div>"
        html += "</div>"
    html += "</div>"
    return html

# Funciones de Gráficos (Altair con paleta personalizada)
escala_colores = alt.Scale(range=PALETA_COLORES)

def grafico_barras_v(df, x_col, y_col):
    return alt.Chart(df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X(x_col, sort='-y', title='', axis=alt.Axis(labelAngle=-45)), 
        y=alt.Y(y_col, title=''),
        color=alt.Color(y_col, scale=escala_colores, legend=None), tooltip=[x_col, y_col]
    ).properties(height=320)

def grafico_barras_h(df, x_col, y_col):
    return alt.Chart(df).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
        y=alt.Y(x_col, sort='-x', title=''), x=alt.X(y_col, title=''),
        color=alt.Color(y_col, scale=escala_colores, legend=None), tooltip=[x_col, y_col]
    ).properties(height=320)

def grafico_torta(df, x_col, y_col):
    return alt.Chart(df).mark_arc(innerRadius=50).encode(
        theta=alt.Theta(field=y_col, type="quantitative"),
        color=alt.Color(field=x_col, type="nominal", scale=alt.Scale(scheme='turbo'), legend=alt.Legend(title="", orient="bottom")),
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
        
        st.markdown("**Configurar Días Hábiles**")
        cols_dias = st.columns(12)
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        if 'dias_habiles' not in st.session_state: st.session_state['dias_habiles'] = [20]*12
        for i, col in enumerate(cols_dias):
            st.session_state['dias_habiles'][i] = col.number_input(meses[i], value=st.session_state['dias_habiles'][i], min_value=0, max_value=31, key=f"dia_{i}")

        if st.button("Procesar Datos", type="primary"):
            if file_fcp and file_nc and file_historico:
                try:
                    df_v, df_n, df_h = pd.read_excel(file_fcp, header=2), pd.read_excel(file_nc, header=2), pd.read_excel(file_historico, header=2)
                    for d in [df_v, df_n, df_h]: d.columns = (d.columns.str.lower().str.strip().str.replace('ú', 'u').str.replace('í', 'i').str.replace('ó', 'o').str.replace('á', 'a').str.replace('é', 'e'))
                    df_v = df_v.drop_duplicates(subset=['numero'], keep='first')
                    df_n = df_n.drop_duplicates(subset=['numero'], keep='first')
                    df_h = df_h.drop_duplicates(subset=['numero'], keep='first')
                    df_h['fecha'] = pd.to_datetime(df_h['fecha'], errors='coerce')
                    df_h = df_h[df_h['fecha'] >= '2025-01-01']
                    df_h_nc = df_h[df_h['tipo'].astype(str).str.contains('NC', case=False, na=False)] if 'tipo' in df_h.columns else df_h
                    df_h_v = df_h[~df_h['tipo'].astype(str).str.contains('NC|ND', case=False, na=False)] if 'tipo' in df_h.columns else pd.DataFrame(columns=df_h.columns)
                    st.session_state['d_nc26'], st.session_state['d_v26'] = df_n, df_v
                    st.session_state['d_nc25'], st.session_state['d_v25'] = df_h_nc, df_h_v
                except Exception as e: st.error(f"Error: {e}")

    if 'd_nc26' in st.session_state:
        st.session_state['d_nc26']['mes'] = pd.to_datetime(st.session_state['d_nc26']['fecha']).dt.month
        max_mes = int(st.session_state['d_nc26']['mes'].max()) if not st.session_state['d_nc26'].empty else 12
        meses_completos = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        meses_activos = meses_completos[:max_mes]

        def calc_mensual(df_v, df_nc, max_m):
            df_v['mes'] = pd.to_datetime(df_v['fecha']).dt.month
            df_nc['mes'] = pd.to_datetime(df_nc['fecha']).dt.month
            v_m = df_v.groupby('mes')['importe total origen'].sum().reset_index()
            nc_m = df_nc.groupby('mes')['importe total origen'].sum().reset_index()
            nc_c = df_nc.groupby('mes')['numero'].count().reset_index()
            calc = pd.DataFrame({'mes': range(1, max_m+1)})
            calc = calc.merge(v_m, on='mes', how='left').rename(columns={'importe total origen': 'ventas'})
            calc = calc.merge(nc_m, on='mes', how='left').rename(columns={'importe total origen': 'nc'})
            calc = calc.merge(nc_c, on='mes', how='left').rename(columns={'numero': 'cantidad'})
            return calc.fillna(0)

        d26 = calc_mensual(st.session_state['d_v26'], st.session_state['d_nc26'], max_mes)
        d25 = calc_mensual(st.session_state['d_v25'], st.session_state['d_nc25'], max_mes)

        st.markdown("<h1 style='font-size: 3.5rem; font-weight: 900; color: #1a202c; margin-top: 20px; margin-bottom: 0px;'>2026</h1>", unsafe_allow_html=True)
        
        t_nc, t_c = d26['nc'].sum(), d26['cantidad'].sum()
        c_k1, c_k2, _, _ = st.columns(4)
        with c_k1: st.markdown(tarjeta_kpi("Total NC Emitidas", int(t_c)), unsafe_allow_html=True)
        with c_k2: st.markdown(tarjeta_kpi("Monto Total NC", f"$ {formato_arg(t_nc)}"), unsafe_allow_html=True)

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

        # Tablas Inferiores alineadas en columnas para mejor uso del espacio
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("<h2>Días Hábiles & Frecuencia</h2>", unsafe_allow_html=True)
            df_m2 = pd.DataFrame({'Mes': meses_activos, 'Cant 2025': d25['cantidad'], 'Cant 2026': d26['cantidad']})
            dias_activos = st.session_state['dias_habiles'][:max_mes]
            df_m2['NC por Día'] = np.where(np.array(dias_activos)>0, df_m2['Cant 2026'] / np.array(dias_activos), 0)
            df_m2['NC por Día'] = df_m2['NC por Día'].apply(lambda x: f"{x:.2f}".replace('.',','))
            st.markdown(render_lista(df_m2, 'Mes', ['Cant 2025', 'Cant 2026', 'NC por Día']), unsafe_allow_html=True)

        with c4:
            st.markdown("<h2>Comparativa % Venta Año a Año</h2>", unsafe_allow_html=True)
            df_m3 = pd.DataFrame({'Mes': meses_activos})
            df_m3['2025 (%)'] = np.where(d25['ventas']!=0, d25['nc'].abs()/d25['ventas'].abs(), 0)
            df_m3['2026 (%)'] = np.where(d26['ventas']!=0, d26['nc'].abs()/d26['ventas'].abs(), 0)
            df_m3['Variación Año/Año'] = df_m3['2026 (%)'] - df_m3['2025 (%)']
            st.markdown(render_lista(df_m3, 'Mes', ['2025 (%)', '2026 (%)', 'Variación Año/Año']), unsafe_allow_html=True)

# --- SOLAPAS DE ANÁLISIS (TRIMESTRE VS ACUMULADO) ---
if 'd_nc26' in st.session_state:
    d_nc = st.session_state['d_nc26']
    trimestre_actual = (int(d_nc['mes'].max()) - 1) // 3 + 1 if not d_nc.empty else 1
    d_nc['trimestre'] = (d_nc['mes'] - 1) // 3 + 1
    d_nc_trim = d_nc[d_nc['trimestre'] == trimestre_actual]

    def armar_seccion_doble(df_trim, df_acum, col_agrupar, titulo, es_error_carga=False, tipo_grafico="barras_h"):
        if es_error_carga:
            if 'referencia 1' in df_trim.columns: df_trim = df_trim[df_trim['referencia 1'].astype(str).str.contains('ERROR', case=False, na=False)]
            if 'referencia 1' in df_acum.columns: df_acum = df_acum[df_acum['referencia 1'].astype(str).str.contains('ERROR', case=False, na=False)]

        st.markdown(f"<br><h2 style='font-size: 2.2rem; color: #1a202c;'>{titulo}</h2>", unsafe_allow_html=True)
        
        st.markdown(f"<h2>📅 Trimestre Actual (Q{trimestre_actual})</h2>", unsafe_allow_html=True)
        if col_agrupar in df_trim.columns and not df_trim.empty:
            ag_trim = df_trim.groupby(col_agrupar).agg(Cant=('numero', 'count'), Total=('importe total origen', 'sum')).reset_index().sort_values('Cant', ascending=False).head(10)
            cA, cB = st.columns([1, 1.4]) # Más espacio para el gráfico para que quede cerca
            with cA: st.markdown(render_lista(ag_trim, col_agrupar, ['Cant', 'Total'], ranking=True), unsafe_allow_html=True)
            with cB: 
                if tipo_grafico == "barras_h": st.altair_chart(grafico_barras_h(ag_trim, col_agrupar, 'Cant'), use_container_width=True)
                elif tipo_grafico == "torta": st.altair_chart(grafico_torta(ag_trim, col_agrupar, 'Cant'), use_container_width=True)
                else: st.altair_chart(grafico_barras_v(ag_trim, col_agrupar, 'Cant'), use_container_width=True)
        else:
            st.info("No hay datos para este trimestre.")

        st.markdown("<br><h2>📈 Acumulado Anual 2026</h2>", unsafe_allow_html=True)
        if col_agrupar in df_acum.columns and not df_acum.empty:
            ag_acum = df_acum.groupby(col_agrupar).agg(Cant=('numero', 'count'), Total=('importe total origen', 'sum')).reset_index().sort_values('Cant', ascending=False).head(10)
            cC, cD = st.columns([1, 1.4])
            with cC: st.markdown(render_lista(ag_acum, col_agrupar, ['Cant', 'Total'], ranking=True), unsafe_allow_html=True)
            with cD: 
                if tipo_grafico == "barras_h": st.altair_chart(grafico_barras_h(ag_acum, col_agrupar, 'Cant'), use_container_width=True)
                elif tipo_grafico == "torta": st.altair_chart(grafico_torta(ag_acum, col_agrupar, 'Cant'), use_container_width=True)
                else: st.altair_chart(grafico_barras_v(ag_acum, col_agrupar, 'Cant'), use_container_width=True)

    with tab_top10: armar_seccion_doble(d_nc_trim, d_nc, 'nombre cliente', "Análisis Top 10 Clientes", tipo_grafico="barras_h")
    with tab_motivo: armar_seccion_doble(d_nc_trim, d_nc, 'referencia 1', "Análisis de Motivos", tipo_grafico="torta")
    with tab_error: armar_seccion_doble(d_nc_trim, d_nc, 'cobrador cliente', "Análisis de Error de Carga", es_error_carga=True, tipo_grafico="barras_v")
