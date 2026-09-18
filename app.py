import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Reporte de Notas de Crédito", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS (MÁXIMA COMPACTACIÓN Y ALINEACIÓN) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Nunito', sans-serif !important; }

/* Títulos de Solapas (Pestañas) - Gigantes y Negrita */
button[role="tab"] {
    background-color: transparent !important;
    border: none !important;
    border-bottom: 5px solid transparent !important;
    padding-bottom: 10px !important;
    margin-right: 20px !important;
}
button[role="tab"] p {
    font-size: 2rem !important; 
    font-weight: 900 !important;
    color: #a0aec0 !important;
    transition: all 0.2s ease;
}
button[role="tab"][aria-selected="true"] { border-bottom: 5px solid #ff4b4b !important; }
button[role="tab"][aria-selected="true"] p { color: #ff4b4b !important; font-size: 2.1rem !important; }

/* Títulos de Secciones Internas */
h2 { font-size: 2.5rem !important; font-weight: 900 !important; color: #1a202c !important; margin-top: 1rem !important; margin-bottom: 0.5rem !important; }

/* KPIs (Tarjetas de Totales) - Más compactas */
.kpi-card {
    background-color: white; border-radius: 15px; padding: 10px; margin: 5px 0;
    text-align: center; border: 2px solid #e2e8f0;
}
.kpi-rojo { border-color: #ff4b4b; color: #ff4b4b; background-color: rgba(255, 75, 75, 0.05); }
.kpi-titulo { font-size: 13px; font-weight: 900; text-transform: uppercase; }
.kpi-valor { font-size: 24px; font-weight: 900; }

/* Filas Súper Compactas y Alineadas */
.fila-canchera {
    display: flex; justify-content: space-between; align-items: center;
    background: #ffffff; border-radius: 8px; padding: 2px 10px; margin-bottom: 3px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02); border: 1px solid #edf2f7;
}
.fila-canchera:hover { background: #f7fafc; border-color: #e2e8f0; }
.fila-titulo { font-weight: 800; color: #2d3748; font-size: 0.85rem; flex-grow: 1; }
.fila-datos { display: flex; gap: 4px; align-items: center; justify-content: flex-end; }

/* Badges con Ancho Fijo Estricto para Alineación Tabulada */
.badge {
    padding: 1px 8px; border-radius: 6px; font-weight: 800; font-size: 0.85rem; 
    display: flex; align-items: center; justify-content: flex-end; gap: 4px;
    min-width: 95px; text-align: right;
}
.badge-neutral { background: transparent; color: #4a5568; }
.badge-alerta { background: rgba(255, 75, 75, 0.12); color: #c53030; }
.badge-ok { background: rgba(40, 167, 69, 0.12); color: #22543d; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE FORMATO ---
def tarjeta_kpi(titulo, valor):
    return f"""<div class="kpi-card kpi-rojo"><div class="kpi-titulo">{titulo}</div><div class="kpi-valor">🔴 ⬆ {valor}</div></div>"""

def formato_arg(numero):
    if pd.isna(numero) or numero == 0: return "0,00"
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formato_pct(numero):
    if pd.isna(numero) or numero == 0: return "0,00%"
    return f"{abs(numero)*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")

def render_lista(df, col_titulo, cols_datos):
    html = ""
    for _, row in df.iterrows():
        datos_html = ""
        for c in cols_datos:
            val = row[c]
            txt_val = ""
            clase_extra = "badge-neutral"
            
            # El orden importa: Primero buscamos % para evitar que se pise con "Total"
            if '%' in c or 'Variación' in c:
                txt_val = formato_pct(val)
                if val > 0.05: clase_extra, txt_val = "badge-alerta", f"❌ {txt_val}"
                elif val > 0: clase_extra, txt_val = "badge-alerta", f"🔴 {txt_val}"
                elif val <= 0: clase_extra, txt_val = "badge-ok", f"✔️ {txt_val}"
            elif 'Total' in c or 'Monto' in c: 
                txt_val = f"$ {formato_arg(val)}"
            elif 'Cantidad' in c or 'Cant' in c: 
                txt_val = str(int(val))
            else: 
                txt_val = str(val)

            datos_html += f"<div class='badge {clase_extra}'>{txt_val}</div>"
        html += f"<div class='fila-canchera'><div class='fila-titulo'>{row[col_titulo]}</div><div class='fila-datos'>{datos_html}</div></div>"
    return html

def grafico_gradiente(df, x_col, y_col):
    return alt.Chart(df).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X(x_col, sort='-y', title=''), y=alt.Y(y_col, title='Cantidad'),
        color=alt.Color(y_col, scale=alt.Scale(scheme='reds'), legend=None), tooltip=[x_col, y_col]
    ).properties(height=200)

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

        st.markdown("## 2026", unsafe_allow_html=True)
        t_nc, t_c = d26['nc'].sum(), d26['cantidad'].sum()
        c_k1, c_k2 = st.columns(2)
        with c_k1: st.markdown(tarjeta_kpi("Total NC Emitidas", int(t_c)), unsafe_allow_html=True)
        with c_k2: st.markdown(tarjeta_kpi("Monto Total NC", f"$ {formato_arg(t_nc)}"), unsafe_allow_html=True)

        df_m1 = pd.DataFrame({'Mes': meses_activos, 'Cantidad': d26['cantidad'], 'Monto NC': d26['nc'], 'Total Venta': d26['ventas']})
        df_m1['% s/Total NC'] = np.where(t_nc!=0, df_m1['Monto NC'].abs() / abs(t_nc), 0)
        df_m1['% s/Total Venta'] = np.where(df_m1['Total Venta']!=0, df_m1['Monto NC'].abs() / df_m1['Total Venta'].abs(), 0)
        
        c1, c2 = st.columns(2)
        with c1: st.markdown(render_lista(df_m1, 'Mes', ['Cantidad', 'Monto NC', '% s/Total NC']), unsafe_allow_html=True)
        with c2: st.markdown(render_lista(df_m1, 'Mes', ['Total Venta', 'Monto NC', '% s/Total Venta']), unsafe_allow_html=True)

        st.markdown("## Días Hábiles & Frecuencia", unsafe_allow_html=True)
        df_m2 = pd.DataFrame({'Mes': meses_activos, 'Cant 2025': d25['cantidad'], 'Cant 2026': d26['cantidad']})
        dias_activos = st.session_state['dias_habiles'][:max_mes]
        df_m2['NC por Día'] = np.where(np.array(dias_activos)>0, df_m2['Cant 2026'] / np.array(dias_activos), 0)
        df_m2['NC por Día'] = df_m2['NC por Día'].apply(lambda x: f"{x:.2f}".replace('.',','))
        st.markdown(render_lista(df_m2, 'Mes', ['Cant 2025', 'Cant 2026', 'NC por Día']), unsafe_allow_html=True)

        st.markdown("## Comparativa % Venta Año a Año", unsafe_allow_html=True)
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

    def armar_seccion_doble(df_trim, df_acum, col_agrupar, titulo):
        st.markdown(f"## {titulo}", unsafe_allow_html=True)
        
        st.markdown(f"#### Trimestre Actual (Q{trimestre_actual})")
        if col_agrupar in df_trim.columns and not df_trim.empty:
            ag_trim = df_trim.groupby(col_agrupar).agg(Cant=('numero', 'count'), Total=('importe total origen', 'sum')).reset_index().sort_values('Cant', ascending=False).head(10)
            cA, cB = st.columns([1,1])
            with cA: st.markdown(render_lista(ag_trim, col_agrupar, ['Cant', 'Total']), unsafe_allow_html=True)
            with cB: st.altair_chart(grafico_gradiente(ag_trim, col_agrupar, 'Cant'), use_container_width=True)
        else:
            st.info("No hay datos para este trimestre.")

        st.markdown("<br>#### Acumulado Anual 2026", unsafe_allow_html=True)
        if col_agrupar in df_acum.columns and not df_acum.empty:
            ag_acum = df_acum.groupby(col_agrupar).agg(Cant=('numero', 'count'), Total=('importe total origen', 'sum')).reset_index().sort_values('Cant', ascending=False).head(10)
            cC, cD = st.columns([1,1])
            with cC: st.markdown(render_lista(ag_acum, col_agrupar, ['Cant', 'Total']), unsafe_allow_html=True)
            with cD: st.altair_chart(grafico_gradiente(ag_acum, col_agrupar, 'Cant'), use_container_width=True)

    with tab_top10: armar_seccion_doble(d_nc_trim, d_nc, 'nombre cliente', "Análisis de Clientes")
    with tab_motivo: armar_seccion_doble(d_nc_trim, d_nc, 'referencia 1', "Análisis de Motivos")
    with tab_error: armar_seccion_doble(d_nc_trim, d_nc, 'cobrador cliente', "Análisis de Error de Carga")
