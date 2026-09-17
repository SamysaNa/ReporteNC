import io
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Reporte de Notas de Crédito", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS (SÚPER COMPACTOS Y MODERNOS) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Nunito', sans-serif !important; }

/* Letras más grandes y llamativas para TODAS las solapas */
button[role="tab"] {
    background-color: transparent !important;
    border: none !important;
    border-bottom: 4px solid transparent !important;
    padding-bottom: 5px !important;
}
button[role="tab"] p {
    font-size: 1.3rem !important; 
    font-weight: 800 !important;
    color: #888 !important;
    transition: all 0.2s ease;
}
button[role="tab"][aria-selected="true"] { border-bottom: 4px solid #ff4b4b !important; }
button[role="tab"][aria-selected="true"] p { color: #ff4b4b !important; font-size: 1.4rem !important; }

/* KPIs (Totales) Más chicos y compactos */
.kpi-card {
    background-color: white; border-radius: 20px; padding: 10px 15px; margin: 5px 0;
    text-align: center; transition: transform 0.2s ease;
}
.kpi-rojo { border: 2px solid #ff4b4b; color: #ff4b4b; background-color: rgba(255, 75, 75, 0.05); }
.kpi-verde { border: 2px solid #28a745; color: #28a745; background-color: rgba(40, 167, 69, 0.05); }
.kpi-titulo { font-size: 12px; font-weight: 800; text-transform: uppercase; }
.kpi-valor { font-size: 20px; font-weight: 900; }

/* Listas flotantes (Filas cancheras) compactas */
.fila-canchera {
    display: flex; justify-content: space-between; align-items: center;
    background: #ffffff; border-radius: 30px; padding: 5px 15px; margin-bottom: 6px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.03); border: 1px solid #f1f3f5; transition: transform 0.1s;
}
.fila-canchera:hover { transform: translateY(-2px); box-shadow: 0 5px 10px rgba(0,0,0,0.06); }
.fila-titulo { font-weight: 800; color: #2d3748; font-size: 0.95rem; }
.fila-datos { display: flex; gap: 8px; align-items: center; }

/* Badges Transparentes (Rojo y Verde) */
.badge {
    padding: 3px 12px; border-radius: 20px; font-weight: 800; font-size: 0.85rem; display: flex; align-items: center; gap: 5px;
}
.badge-neutral { background: #edf2f7; color: #4a5568; }
.badge-alerta { background: rgba(255, 75, 75, 0.15); color: #c53030; } /* Fondo rojo transparente */
.badge-ok { background: rgba(40, 167, 69, 0.15); color: #22543d; }     /* Fondo verde transparente */
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE FORMATO ---
def tarjeta_kpi(titulo, valor, aumento=True):
    clase = "kpi-rojo" if aumento else "kpi-verde"
    icono = "⬆" if aumento else "⬇"
    return f"""<div class="kpi-card {clase}"><div class="kpi-titulo">{titulo}</div><div class="kpi-valor">{icono} {valor}</div></div>"""

def formato_arg(numero):
    if pd.isna(numero) or numero == 0: return "0,00"
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formato_pct(numero):
    if pd.isna(numero) or numero == 0: return "0,00%"
    return f"{abs(numero)*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")

def render_lista(df, col_titulo, cols_datos, tipo='monto'):
    html = ""
    for _, row in df.iterrows():
        datos_html = ""
        for c in cols_datos:
            val = row[c]
            txt_val = ""
            clase_extra = "badge-neutral"
            
            # Formatos según nombre de columna y tipo
            if 'Total' in c or 'Monto' in c:
                txt_val = f"$ {formato_arg(val)}"
            elif '%' in c:
                txt_val = formato_pct(val)
                # Lógica de colores e íconos para porcentajes
                if val > 0.05: # Más de 5% rojo
                    clase_extra = "badge-alerta"
                    txt_val = f"❌ {txt_val}"
                elif val > 0:
                    clase_extra = "badge-alerta"
                elif val <= 0:
                    clase_extra = "badge-ok"
                    txt_val = f"✔️ {txt_val}"
            elif 'Cantidad' in c or 'Cant' in c:
                txt_val = str(int(val))
            elif 'Variación' in c:
                txt_val = formato_pct(val)
                if val > 0: clase_extra, txt_val = "badge-alerta", f"🔴 {txt_val}"
                else: clase_extra, txt_val = "badge-ok", f"🟢 {txt_val}"
            else:
                txt_val = str(val)

            datos_html += f"<div class='badge {clase_extra}'>{txt_val}</div>"
            
        html += f"<div class='fila-canchera'><div class='fila-titulo'>{row[col_titulo]}</div><div class='fila-datos'>{datos_html}</div></div>"
    return html

def grafico_gradiente(df, x_col, y_col):
    return alt.Chart(df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X(x_col, sort='-y', title=''),
        y=alt.Y(y_col, title='Cantidad'),
        color=alt.Color(y_col, scale=alt.Scale(scheme='reds'), legend=None),
        tooltip=[x_col, y_col]
    ).properties(height=300)

# --- 🔒 LOGIN ---
PASS_ADMIN = "admin123"
PASS_VISOR = "visor123"
if "rol" not in st.session_state: st.session_state.rol = None

if not st.session_state.rol:
    st.title("🔒 Acceso al Sistema")
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if pwd == PASS_ADMIN: st.session_state.rol = "admin"; st.rerun()
        elif pwd == PASS_VISOR: st.session_state.rol = "visor"; st.rerun()
        else: st.error("Clave incorrecta.")
    st.stop() 

# --- 📊 APLICACIÓN PRINCIPAL ---
col_head1, col_head2 = st.columns([8, 2])
with col_head1: st.title("📊 Generador de Reportes NC")
with col_head2: 
    if st.button("Cerrar Sesión"): st.session_state.rol = None; st.rerun()

tab_analisis, tab_top10, tab_motivo, tab_error = st.tabs(["Análisis", "Top 10 Clientes", "Motivos", "Error de Carga"])

# --- SOLAPA 1: ANÁLISIS ---
with tab_analisis:
    if st.session_state.rol == "admin":
        with st.expander("📂 Zona de Carga", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1: file_fcp = st.file_uploader("Facturación 2026", type=['xlsx'])
            with col2: file_nc = st.file_uploader("Notas de Crédito 2026", type=['xlsx'])
            with col3: file_historico = st.file_uploader("Histórico 2025", type=['xlsx'])
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
                        if 'tipo' in df_h.columns:
                            df_h_nc = df_h[df_h['tipo'].astype(str).str.contains('NC', case=False, na=False)]
                            df_h_v = df_h[~df_h['tipo'].astype(str).str.contains('NC|ND', case=False, na=False)]
                        else: df_h_nc, df_h_v = df_h, pd.DataFrame(columns=df_h.columns)
                        st.session_state['d_nc26'], st.session_state['d_v26'] = df_n, df_v
                        st.session_state['d_nc25'], st.session_state['d_v25'] = df_h_nc, df_h_v
                    except Exception as e: st.error(f"Error: {e}")

    if 'd_nc26' in st.session_state:
        st.markdown("<br>", unsafe_allow_html=True)
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        def calc_mensual(df_v, df_nc):
            df_v['mes'] = pd.to_datetime(df_v['fecha']).dt.month
            df_nc['mes'] = pd.to_datetime(df_nc['fecha']).dt.month
            v_m = df_v.groupby('mes')['importe total origen'].sum().reset_index()
            nc_m = df_nc.groupby('mes')['importe total origen'].sum().reset_index()
            nc_c = df_nc.groupby('mes')['numero'].count().reset_index()
            calc = pd.DataFrame({'mes': range(1, 13)})
            calc = calc.merge(v_m, on='mes', how='left').rename(columns={'importe total origen': 'ventas'})
            calc = calc.merge(nc_m, on='mes', how='left').rename(columns={'importe total origen': 'nc'})
            calc = calc.merge(nc_c, on='mes', how='left').rename(columns={'numero': 'cantidad'})
            return calc.fillna(0)

        d26, d25 = calc_mensual(st.session_state['d_v26'], st.session_state['d_nc26']), calc_mensual(st.session_state['d_v25'], st.session_state['d_nc25'])

        mini1, mini2, mini3 = st.tabs(["Métricas 2026", "Días Hábiles", "Comparativa % Venta"])

        with mini1:
            t_nc, t_c = d26['nc'].sum(), d26['cantidad'].sum()
            c_k1, c_k2 = st.columns(2)
            with c_k1: st.markdown(tarjeta_kpi("Total NC Emitidas", int(t_c), True), unsafe_allow_html=True)
            with c_k2: st.markdown(tarjeta_kpi("Monto Total NC", f"$ {formato_arg(t_nc)}", True), unsafe_allow_html=True)

            df_m1 = pd.DataFrame({'Mes': meses, 'Cantidad': d26['cantidad'], 'Monto NC': d26['nc'], 'Total Venta': d26['ventas']})
            df_m1['% s/Total NC'] = np.where(t_nc!=0, df_m1['Monto NC'].abs() / abs(t_nc), 0)
            df_m1['% s/Total Venta'] = np.where(df_m1['Total Venta']!=0, df_m1['Monto NC'].abs() / df_m1['Total Venta'].abs(), 0)
            
            c1, c2 = st.columns(2)
            with c1: st.markdown(render_lista(df_m1, 'Mes', ['Cantidad', 'Monto NC', '% s/Total NC']), unsafe_allow_html=True)
            with c2: st.markdown(render_lista(df_m1, 'Mes', ['Total Venta', 'Monto NC', '% s/Total Venta']), unsafe_allow_html=True)

        with mini2:
            if 'df_dias' not in st.session_state: st.session_state['df_dias'] = pd.DataFrame({'Mes': meses, 'Días Hábiles': [20]*12})
            dias = st.data_editor(st.session_state['df_dias'], hide_index=True, use_container_width=True)
            df_m2 = pd.DataFrame({'Mes': meses, 'Cant 2025': d25['cantidad'], 'Cant 2026': d26['cantidad']})
            df_m2['NC por Día'] = np.where(dias['Días Hábiles']>0, df_m2['Cant 2026'] / dias['Días Hábiles'], 0)
            df_m2['NC por Día'] = df_m2['NC por Día'].apply(lambda x: f"{x:.2f}".replace('.',','))
            st.markdown(render_lista(df_m2, 'Mes', ['Cant 2025', 'Cant 2026', 'NC por Día']), unsafe_allow_html=True)

        with mini3:
            df_m3 = pd.DataFrame({'Mes': meses})
            df_m3['2025 (%)'] = np.where(d25['ventas']!=0, d25['nc'].abs()/d25['ventas'].abs(), 0)
            df_m3['2026 (%)'] = np.where(d26['ventas']!=0, d26['nc'].abs()/d26['ventas'].abs(), 0)
            df_m3['Variación'] = df_m3['2026 (%)'] - df_m3['2025 (%)']
            st.markdown(render_lista(df_m3, 'Mes', ['2025 (%)', '2026 (%)', 'Variación']), unsafe_allow_html=True)

        # DESGLOSE INTERACTIVO
        st.markdown("---")
        st.subheader("🔍 Desglose de Comprobantes (NC 2026)")
        mes_sel = st.selectbox("Seleccione el mes para ver el detalle de comprobantes:", meses)
        mes_idx = meses.index(mes_sel) + 1
        df_det = st.session_state['d_nc26'][st.session_state['d_nc26']['mes'] == mes_idx]
        if not df_det.empty:
            df_det_vis = df_det[['fecha', 'nombre cliente', 'importe total origen']].copy()
            df_det_vis['importe total origen'] = df_det_vis['importe total origen'].apply(lambda x: f"$ {formato_arg(x)}")
            df_det_vis['fecha'] = df_det_vis['fecha'].dt.strftime('%d-%m-%Y')
            st.dataframe(df_det_vis, use_container_width=True, hide_index=True)
        else:
            st.info(f"No hay comprobantes cargados en {mes_sel}.")

# --- OTRAS SOLAPAS ---
if 'd_nc26' in st.session_state:
    d_nc = st.session_state['d_nc26']
    meses_d = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    def armar_seccion_analisis(df, col_agrupar, titulo):
        st.markdown(f"### {titulo}")
        if col_agrupar in df.columns:
            agrupado = df.groupby(col_agrupar).agg(Cant=('numero', 'count'), Total_Monto=('importe total origen', 'sum')).reset_index().sort_values('Cant', ascending=False).head(10)
            colA, colB = st.columns([1,1])
            with colA: st.markdown(render_lista(agrupado, col_agrupar, ['Cant', 'Total_Monto']), unsafe_allow_html=True)
            with colB: st.altair_chart(grafico_gradiente(agrupado, col_agrupar, 'Cant'), use_container_width=True)
            
            st.markdown("#### 🔍 Desglose")
            sel_opcion = st.selectbox(f"Seleccione {col_agrupar} para ver detalle:", agrupado[col_agrupar].tolist(), key=col_agrupar)
            df_det = df[df[col_agrupar] == sel_opcion][['fecha', 'nombre cliente', 'importe total origen']].copy()
            df_det['importe total origen'] = df_det['importe total origen'].apply(lambda x: f"$ {formato_arg(x)}")
            df_det['fecha'] = df_det['fecha'].dt.strftime('%d-%m-%Y')
            st.dataframe(df_det, use_container_width=True, hide_index=True)

    with tab_top10: armar_seccion_analisis(d_nc, 'nombre cliente', "Top 10 Clientes")
    with tab_motivo: armar_seccion_analisis(d_nc, 'referencia 1', "Motivos de NC")
    with tab_error: armar_seccion_analisis(d_nc, 'cobrador cliente', "Errores de Carga (Cobrador)")
