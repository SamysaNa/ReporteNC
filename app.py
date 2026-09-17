import io
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Reporte de Notas de Crédito", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS (MODERNIZADOS) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif !important;
}

/* Solapas principales más grandes y con forma de píldora */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
}
.stTabs [data-baseweb="tab"] {
    background-color: #f8f9fa;
    border-radius: 30px !important;
    padding: 10px 20px;
    border: 1px solid #e9ecef;
    transition: all 0.3s ease;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #1e88e5;
    border-color: #1e88e5;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] p {
    color: white !important;
    font-weight: 900 !important;
}
.stTabs [data-baseweb="tab-list"] button p {
    font-size: 1.1rem;
    font-weight: 700;
    color: #555;
    margin: 0;
}

/* Animaciones y tarjetas flotantes de KPI */
@keyframes latido-rojo {
    0% { box-shadow: 0 0 10px rgba(255, 75, 75, 0.3); transform: scale(1); }
    50% { box-shadow: 0 0 25px rgba(255, 75, 75, 0.7); transform: scale(1.02); }
    100% { box-shadow: 0 0 10px rgba(255, 75, 75, 0.3); transform: scale(1); }
}
@keyframes latido-verde {
    0% { box-shadow: 0 0 10px rgba(40, 167, 69, 0.3); transform: scale(1); }
    50% { box-shadow: 0 0 25px rgba(40, 167, 69, 0.7); transform: scale(1.02); }
    100% { box-shadow: 0 0 10px rgba(40, 167, 69, 0.3); transform: scale(1); }
}

.kpi-card {
    background-color: white;
    border-radius: 40px;
    padding: 20px 30px;
    margin: 15px 0;
    text-align: center;
    transition: transform 0.2s ease;
}
.kpi-rojo { border: 3px solid #ff4b4b; color: #ff4b4b; }
.kpi-rojo:hover { animation: latido-rojo 1.5s infinite; }
.kpi-verde { border: 3px solid #28a745; color: #28a745; }
.kpi-verde:hover { animation: latido-verde 1.5s infinite; }
.kpi-titulo { font-size: 16px; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: 1px; }
.kpi-valor { font-size: 32px; font-weight: 900; margin-top: 5px; }

/* Listas flotantes (Filas cancheras) */
.fila-canchera {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #ffffff;
    border-radius: 50px;
    padding: 12px 25px;
    margin-bottom: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.04);
    border: 1px solid #f1f3f5;
    transition: transform 0.2s, box-shadow 0.2s;
}
.fila-canchera:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.08);
    border-color: #e2e8f0;
}
.fila-titulo { font-weight: 800; color: #2d3748; font-size: 1.1rem; }
.fila-datos { display: flex; gap: 10px; align-items: center; }
.badge {
    background: #edf2f7;
    color: #4a5568;
    padding: 6px 15px;
    border-radius: 30px;
    font-weight: 700;
    font-size: 0.95rem;
}
.badge-alerta { background: #fed7d7; color: #c53030; }
.badge-ok { background: #c6f6d5; color: #22543d; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE FORMATO Y HTML ---
def tarjeta_kpi(titulo, valor, aumento=True):
    clase = "kpi-rojo" if aumento else "kpi-verde"
    icono = "🔴 ⬆" if aumento else "🟢 ⬇"
    return f"""<div class="kpi-card {clase}"><div class="kpi-titulo">{titulo}</div><div class="kpi-valor">{icono} {valor}</div></div>"""

def formato_arg(numero):
    if pd.isna(numero) or numero == 0: return "0,00"
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formato_pct(numero):
    if pd.isna(numero) or numero == 0: return "0,00%"
    return f"{abs(numero)*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".") # El abs() soluciona el % negativo

def render_lista(df, col_titulo, cols_datos, es_porcentaje=False):
    html = ""
    for _, row in df.iterrows():
        datos_html = ""
        for idx, c in enumerate(cols_datos):
            val = row[c]
            # Determinar formato según el tipo de columna
            if es_porcentaje and ('%' in c or idx == len(cols_datos)-1):
                txt_val = formato_pct(val)
                # Darle color si es porcentaje mayor a 0
                clase_extra = "badge-alerta" if (val > 0.05 and '%' in c) else "" 
            elif isinstance(val, (int, float)) and val > 1000:
                txt_val = f"$ {formato_arg(val)}"
                clase_extra = ""
            else:
                txt_val = str(val) if not pd.isna(val) else "-"
                clase_extra = ""
                
            datos_html += f"<div class='badge {clase_extra}'>{txt_val}</div>"
            
        html += f"""
        <div class='fila-canchera'>
            <div class='fila-titulo'>{row[col_titulo]}</div>
            <div class='fila-datos'>{datos_html}</div>
        </div>
        """
    return html

# --- 🔒 LOGIN ---
PASS_ADMIN = "admin123"
PASS_VISOR = "visor123"

if "rol" not in st.session_state:
    st.session_state.rol = None

if not st.session_state.rol:
    st.title("🔒 Acceso al Sistema de Reportes")
    password_ingresada = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if password_ingresada == PASS_ADMIN: st.session_state.rol = "admin"; st.rerun()
        elif password_ingresada == PASS_VISOR: st.session_state.rol = "visor"; st.rerun()
        else: st.error("Contraseña incorrecta.")
    st.stop() 

# --- 📊 APLICACIÓN ---
col_head1, col_head2 = st.columns([8, 2])
with col_head1: st.title("📊 Generador de Reportes NC")
with col_head2: 
    if st.button("Cerrar Sesión"): st.session_state.rol = None; st.rerun()

tab_analisis, tab_top10, tab_motivo, tab_error = st.tabs([
    "Análisis General", "Top 10 Clientes", "Motivos", "Error de Carga"
])

# --- SOLAPA 1: ANÁLISIS ---
with tab_analisis:
    if st.session_state.rol == "admin":
        with st.expander("📂 Zona de Carga de Archivos", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1: file_fcp = st.file_uploader("Facturación 2026", type=['xlsx'])
            with col2: file_nc = st.file_uploader("Notas de Crédito 2026", type=['xlsx'])
            with col3: file_historico = st.file_uploader("Histórico 2025", type=['xlsx'])
            
            if st.button("Procesar y Generar Reporte", type="primary"):
                if file_fcp and file_nc and file_historico:
                    try:
                        df_ventas = pd.read_excel(file_fcp, header=2)
                        df_nc = pd.read_excel(file_nc, header=2)
                        df_hist = pd.read_excel(file_historico, header=2)
                        
                        for df in [df_ventas, df_nc, df_hist]:
                            df.columns = (df.columns.str.lower().str.strip().str.replace('ú', 'u').str.replace('í', 'i').str.replace('ó', 'o').str.replace('á', 'a').str.replace('é', 'e'))
                        
                        df_ventas = df_ventas.drop_duplicates(subset=['numero'], keep='first')
                        df_nc = df_nc.drop_duplicates(subset=['numero'], keep='first')
                        df_hist = df_hist.drop_duplicates(subset=['numero'], keep='first')

                        df_hist['fecha'] = pd.to_datetime(df_hist['fecha'], errors='coerce')
                        df_hist = df_hist[df_hist['fecha'] >= '2025-01-01']
                        
                        if 'tipo' in df_hist.columns:
                            df_hist_nc = df_hist[df_hist['tipo'].astype(str).str.contains('NC', case=False, na=False)]
                            df_hist_v = df_hist[~df_hist['tipo'].astype(str).str.contains('NC|ND', case=False, na=False)]
                        else:
                            df_hist_nc, df_hist_v = df_hist, pd.DataFrame(columns=df_hist.columns)

                        st.session_state['d_nc26'], st.session_state['d_v26'] = df_nc, df_ventas
                        st.session_state['d_nc25'], st.session_state['d_v25'] = df_hist_nc, df_hist_v
                        
                    except Exception as e:
                        st.error(f"Error procesando: {e}")
                else:
                    st.warning("Faltan archivos por subir.")
    else:
        st.info("Modo Visor.")

    # --- MINI SOLAPAS CON NUEVO DISEÑO ---
    if 'd_nc26' in st.session_state:
        st.markdown("<br>", unsafe_allow_html=True)
        
        def calc_mensual(df_v, df_nc):
            df_v['mes'] = pd.to_datetime(df_v['fecha']).dt.month
            df_nc['mes'] = pd.to_datetime(df_nc['fecha']).dt.month
            v_mes = df_v.groupby('mes')['importe total origen'].sum().reset_index()
            nc_mes = df_nc.groupby('mes')['importe total origen'].sum().reset_index()
            nc_cant = df_nc.groupby('mes')['numero'].count().reset_index()
            
            calc = pd.DataFrame({'mes': range(1, 13)})
            calc = pd.merge(calc, v_mes, on='mes', how='left').rename(columns={'importe total origen': 'ventas'})
            calc = pd.merge(calc, nc_mes, on='mes', how='left').rename(columns={'importe total origen': 'nc'})
            calc = pd.merge(calc, nc_cant, on='mes', how='left').rename(columns={'numero': 'cantidad'})
            calc.fillna(0, inplace=True)
            return calc

        d26 = calc_mensual(st.session_state['d_v26'], st.session_state['d_nc26'])
        d25 = calc_mensual(st.session_state['d_v25'], st.session_state['d_nc25'])
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

        mini1, mini2, mini3 = st.tabs(["Métricas 2026", "Cantidades & Días", "Comparativa Histórica"])

        with mini1:
            tot_nc_2026 = d26['nc'].sum()
            tot_cant_2026 = d26['cantidad'].sum()
            
            col_k1, col_k2 = st.columns(2)
            with col_k1: st.markdown(tarjeta_kpi("Total NC Emitidas (2026)", int(tot_cant_2026), aumento=True), unsafe_allow_html=True)
            with col_k2: st.markdown(tarjeta_kpi("Monto Total NC (2026)", f"$ {formato_arg(tot_nc_2026)}", aumento=True), unsafe_allow_html=True)

            df_m1 = pd.DataFrame({'Mes': meses, 'Cantidad': d26['cantidad'].astype(int), 'Monto NC/ND': d26['nc'], 'Total Venta': d26['ventas']})
            # Usamos abs() para garantizar porcentajes positivos
            df_m1['% s/Total NC'] = np.where(tot_nc_2026!=0, df_m1['Monto NC/ND'].abs() / abs(tot_nc_2026), 0)
            df_m1['% s/Total Venta'] = np.where(df_m1['Total Venta']!=0, df_m1['Monto NC/ND'].abs() / df_m1['Total Venta'].abs(), 0)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Resumen de Notas de Crédito")
                st.markdown(render_lista(df_m1, 'Mes', ['Cantidad', 'Monto NC/ND', '% s/Total NC'], es_porcentaje=True), unsafe_allow_html=True)
            with c2:
                st.markdown("#### Relación Venta vs NC")
                st.markdown(render_lista(df_m1, 'Mes', ['Total Venta', 'Monto NC/ND', '% s/Total Venta'], es_porcentaje=True), unsafe_allow_html=True)

        with mini2:
            st.markdown("#### Ajuste de Días Hábiles (Click para editar)")
            if 'df_dias' not in st.session_state:
                st.session_state['df_dias'] = pd.DataFrame({'Mes': meses, 'Días Hábiles': [20]*12})
            
            dias_editados = st.data_editor(st.session_state['df_dias'], hide_index=True, use_container_width=True)
            
            df_m2 = pd.DataFrame({'Mes': meses, '2025': d25['cantidad'].astype(int), '2026': d26['cantidad'].astype(int)})
            df_m2['Días Hábiles'] = dias_editados['Días Hábiles']
            df_m2['NC por Día'] = np.where(df_m2['Días Hábiles']>0, df_m2['2026'] / df_m2['Días Hábiles'], 0)
            df_m2['NC por Día'] = df_m2['NC por Día'].apply(lambda x: f"{x:.2f}".replace('.',','))
            
            variacion_cant = d26['cantidad'].sum() - d25['cantidad'].sum()
            st.markdown(tarjeta_kpi("Variación de Cantidad (26 vs 25)", f"{variacion_cant:+.0f} NC", aumento=(variacion_cant>0)), unsafe_allow_html=True)
            
            st.markdown(render_lista(df_m2, 'Mes', ['2025', '2026', 'Días Hábiles', 'NC por Día']), unsafe_allow_html=True)

        with mini3:
            st.markdown("#### Variación Porcentual sobre Venta")
            df_m3 = pd.DataFrame({'Mes': meses})
            df_m3['2025 (%)'] = np.where(d25['ventas']!=0, d25['nc'].abs()/d25['ventas'].abs(), 0)
            df_m3['2026 (%)'] = np.where(d26['ventas']!=0, d26['nc'].abs()/d26['ventas'].abs(), 0)
            df_m3['Variación'] = df_m3['2026 (%)'] - df_m3['2025 (%)']
            
            st.markdown(render_lista(df_m3, 'Mes', ['2025 (%)', '2026 (%)', 'Variación'], es_porcentaje=True), unsafe_allow_html=True)

# --- LAS OTRAS SOLAPAS VUELVEN A LA VIDA ---
if 'd_nc26' in st.session_state:
    d_nc = st.session_state['d_nc26']
    
    with tab_top10:
        st.markdown("### Top 10 Clientes con más Notas de Crédito")
        if 'nombre cliente' in d_nc.columns:
            top10 = d_nc.groupby('nombre cliente').agg(Cant=('numero', 'count'), Total=('importe total origen', 'sum')).reset_index().sort_values('Cant', ascending=False).head(10)
            colA, colB = st.columns([1,1])
            with colA: st.markdown(render_lista(top10, 'nombre cliente', ['Cant', 'Total']), unsafe_allow_html=True)
            with colB: st.bar_chart(top10, x='nombre cliente', y='Cant', color="#ff4b4b")

    with tab_motivo:
        st.markdown("### Análisis por Motivo")
        if 'referencia 1' in d_nc.columns:
            motivos = d_nc.groupby('referencia 1').agg(Cant=('numero', 'count'), Total=('importe total origen', 'sum')).reset_index().sort_values('Cant', ascending=False)
            colA, colB = st.columns([1,1])
            with colA: st.markdown(render_lista(motivos, 'referencia 1', ['Cant', 'Total']), unsafe_allow_html=True)
            with colB: st.bar_chart(motivos, x='referencia 1', y='Cant', color="#ff4b4b")

    with tab_error:
        st.markdown("### Análisis por Error de Carga (Cobrador)")
        if 'cobrador cliente' in d_nc.columns:
            errores = d_nc.groupby('cobrador cliente').agg(Cant=('numero', 'count'), Total=('importe total origen', 'sum')).reset_index().sort_values('Cant', ascending=False)
            colA, colB = st.columns([1,1])
            with colA: st.markdown(render_lista(errores, 'cobrador cliente', ['Cant', 'Total']), unsafe_allow_html=True)
            with colB: st.bar_chart(errores, x='cobrador cliente', y='Cant', color="#ff4b4b")
