import streamlit as st
import pandas as pd
import datetime
import os
from supabase import create_client
#Conexion con supabase usando los secretos de Streamlit Cloud
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuración inicial de la página
st.set_page_config(page_title="Control Financiero", page_icon="💰", layout="wide")

# Estilo CSS personalizado para un acabado profesional
st.markdown("""
    <style>
    .main { background-color: #f4f6f8; }
    .card { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .metric-title { font-size: 0.9em; color: #6c757d; font-weight: bold; }
    .metric-value { font-size: 1.8em; font-weight: bold; color: #1e3d59; }
    </style>
""", unsafe_allow_html=True)

# Ruta de la base de datos limpia de movimientos financieros
DB_PATH = "movimientos_financieros.csv"

# Inicialización de la base de datos vacía
def cargar_datos():
    if os.path.exists(DB_PATH):
        try:
            df = pd.read_csv(DB_PATH)
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce').dt.date
            df = df.dropna(subset=['Fecha'])
            return df
        except Exception:
            pass
    # Crear base de datos vacía
    df_vacio = pd.DataFrame(columns=["Fecha", "Detalle", "Cuenta", "Debe", "Haber"])
    df_vacio.to_csv(DB_PATH, index=False)
    return df_vacio

# Inicializar estado de sesión
if 'transactions' not in st.session_state:
    st.session_state.transactions = cargar_datos()

df = st.session_state.transactions.copy()

# Lista de cuentas dinámicas por defecto
cuentas_defecto = ["Efectivo", "Nequi", "Nu", "BBVA", "Pibank"]
if 'accounts_list' not in st.session_state:
    if not df.empty:
        cuentas_existentes = list(df["Cuenta"].dropna().unique())
        for c in cuentas_existentes:
            if c not in cuentas_defecto:
                cuentas_defecto.append(c)
    st.session_state.accounts_list = cuentas_defecto

# Formatear fechas de forma segura
if not df.empty:
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce').dt.date
    df = df.dropna(subset=["Fecha"])
    df["Mes_Auto"] = df["Fecha"].apply(lambda x: datetime.date(x.year, x.month, 1) if isinstance(x, (datetime.date, datetime.datetime)) else None)
    df = df.dropna(subset=["Mes_Auto"])
else:
    df["Mes_Auto"] = None

# Título de la app
st.title("💰 Mi Billetera Financiera Real - Pesos Colombianos (COP)")
st.markdown("Esta aplicación trabaja de forma local y almacena la información exclusivamente en Pesos Colombianos (**COP**).")

# Sidebar - Gestión de Cuentas
st.sidebar.header("⚙️ Gestionar Cuentas")
with st.sidebar.expander("🛠️ Añadir Nueva Cuenta"):
    nueva_cta_nombre = st.text_input("Nombre de la cuenta:", "")
    if st.button("Crear Cuenta"):
        if nueva_cta_nombre and nueva_cta_nombre not in st.session_state.accounts_list:
            st.session_state.accounts_list.append(nueva_cta_nombre)
            st.success(f"¡Cuenta '{nueva_cta_nombre}' añadida!")
            st.rerun()

# Sidebar - Registrar Movimiento o Transferencia
st.sidebar.header("➕ Registrar Movimiento / Transferencia")
tipo_registro = st.sidebar.radio("Selecciona tipo de registro:", ["Movimiento Simple", "Transferencia entre Cuentas"])

if tipo_registro == "Movimiento Simple":
    with st.sidebar.form("nuevo_registro", clear_on_submit=True):
        nueva_fecha = st.date_input("Fecha:", datetime.date.today())
        nuevo_detalle = st.text_input("Detalle/Concepto:", "")
        nueva_cuenta = st.selectbox("Cuenta:", st.session_state.accounts_list)
        tipo_mov = st.radio("Tipo de Movimiento:", ["Ingreso / Entrada (+)", "Egreso / Salida (-)"])
        monto = st.number_input("Monto en COP:", min_value=0.0, step=1000.0, format="%.0f")
        boton_guardar = st.form_submit_button("Registrar en el Sistema")

        if boton_guardar:
            if nuevo_detalle == "":
                st.sidebar.error("Por favor ingresa un detalle.")
            else:
                debe = monto if "Ingreso" in tipo_mov else 0.0
                haber = monto if "Egreso" in tipo_mov else 0.0
                nueva_fila = {
                    "Fecha": nueva_fecha,
                    "Detalle": nuevo_detalle,
                    "Cuenta": nueva_cuenta,
                    "Debe": debe,
                    "Haber": haber
                }
                df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
                df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce').dt.date
                df = df.dropna(subset=["Fecha"])
                df.to_csv(DB_PATH, index=False)
                st.session_state.transactions = df
                st.sidebar.success("¡Registrado con éxito!")
                st.rerun()

elif tipo_registro == "Transferencia entre Cuentas":
    with st.sidebar.form("nueva_transferencia", clear_on_submit=True):
        trans_fecha = st.date_input("Fecha:", datetime.date.today())
        cuenta_origen = st.selectbox("Desde cuenta (Sale):", st.session_state.accounts_list, key="origen")
        cuenta_destino = st.selectbox("Hacia cuenta (Entra):", st.session_state.accounts_list, key="destino")
        trans_monto = st.number_input("Monto a transferir en COP:", min_value=0.0, step=1000.0, format="%.0f")
        boton_transferir = st.form_submit_button("Efectuar Transferencia")

        if boton_transferir:
            if cuenta_origen == cuenta_destino:
                st.sidebar.error("La cuenta de origen y destino no pueden ser iguales.")
            elif trans_monto <= 0:
                st.sidebar.error("El monto debe ser mayor a 0.")
            else:
                fila_salida = {
                    "Fecha": trans_fecha,
                    "Detalle": f"Transferencia enviada a {cuenta_destino}",
                    "Cuenta": cuenta_origen,
                    "Debe": 0.0,
                    "Haber": trans_monto
                }
                fila_entrada = {
                    "Fecha": trans_fecha,
                    "Detalle": f"Transferencia recibida desde {cuenta_origen}",
                    "Cuenta": cuenta_destino,
                    "Debe": trans_monto,
                    "Haber": 0.0
                }
                df = pd.concat([df, pd.DataFrame([fila_salida, fila_entrada])], ignore_index=True)
                df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce').dt.date
                df = df.dropna(subset=["Fecha"])
                df.to_csv(DB_PATH, index=False)
                st.session_state.transactions = df
                st.sidebar.success("¡Transferencia registrada exitosamente!")
                st.rerun()

# Filtro de Mes
if not df.empty and df["Mes_Auto"].notna().any():
    months = sorted(df["Mes_Auto"].unique())
else:
    months = [datetime.date(datetime.date.today().year, datetime.date.today().month, 1)]

selected_month = st.sidebar.selectbox(
    "📅 Filtrar por Mes:",
    options=months,
    format_func=lambda x: x.strftime("%B %Y").capitalize() if hasattr(x, 'strftime') else str(x)
)

# Segmentación de datos (histórico vs mes seleccionado)
if not df.empty:
    df_before = df[df["Mes_Auto"] < selected_month]
    df_month = df[df["Mes_Auto"] == selected_month]
else:
    df_before = pd.DataFrame(columns=["Cuenta", "Debe", "Haber"])
    df_month = pd.DataFrame(columns=["Cuenta", "Debe", "Haber"])

# Panel de Cuentas T
cuentas = st.session_state.accounts_list
st.markdown(f"### 📊 Estado de tus Cuentas (COP) - {selected_month.strftime('%B %Y').capitalize() if hasattr(selected_month, 'strftime') else str(selected_month)}")

cols = st.columns(len(cuentas)) if len(cuentas) > 0 else []
total_capital = 0.0

for idx, cta in enumerate(cuentas):
    debe_ant = df_before[df_before["Cuenta"] == cta]["Debe"].sum() if not df_before.empty else 0.0
    haber_ant = df_before[df_before["Cuenta"] == cta]["Haber"].sum() if not df_before.empty else 0.0
    saldo_ini = debe_ant - haber_ant

    debe_mes = df_month[df_month["Cuenta"] == cta]["Debe"].sum() if not df_month.empty else 0.0
    haber_mes = df_month[df_month["Cuenta"] == cta]["Haber"].sum() if not df_month.empty else 0.0

    saldo_final = saldo_ini + debe_mes - haber_mes
    total_capital += saldo_final

    if len(cols) > idx:
        with cols[idx]:
            st.markdown(f"""
            <div class="card">
                <div class="metric-title">💳 {cta}</div>
                <div style="font-size: 0.8em; color: gray;">Inicial: {saldo_ini:,.0f} COP</div>
                <div style="color: green; font-size: 0.85em;">Entra (+): {debe_mes:,.0f} COP</div>
                <div style="color: red; font-size: 0.85em;">Sale (-): {haber_mes:,.0f} COP</div>
                <div class="metric-value">{saldo_final:,.0f} COP</div>
            </div>
            """, unsafe_allow_html=True)

# Tarjeta del Balance Global / Disponible
st.markdown(f"""
<div class="card" style="background-color: #e3f2fd;">
    <div class="metric-title" style="color: #0d47a1;">💎 PATRIMONIO TOTAL DISPONIBLE (GLOBAL)</div>
    <div style="font-size: 2.2em; font-weight: bold; color: #0d47a1;">{total_capital:,.0f} COP</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# Vista de editor de base de datos directa ordenada por Fecha
st.markdown("### 📝 Editor y Visor de Base de Datos (COP)")
st.markdown("Aquí puedes editar transacciones directamente. Las transacciones se muestran ordenadas por Fecha de forma predeterminada.")

# Ordenar el dataframe por Fecha antes de enviarlo al editor de Streamlit
df_ordenado = df[["Fecha", "Detalle", "Cuenta", "Debe", "Haber"]].sort_values(by="Fecha", ascending=True)

edited_df = st.data_editor(
    df_ordenado,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Debe": st.column_config.NumberColumn("Debe / Entra (COP)", format="%d"),
        "Haber": st.column_config.NumberColumn("Haber / Sale (COP)", format="%d"),
    },
    key="db_editor"
)

if st.button("💾 Aplicar y Guardar Cambios en Base de Datos"):
    edited_df["Fecha"] = pd.to_datetime(edited_df["Fecha"], errors='coerce').dt.date
    edited_df = edited_df.dropna(subset=["Fecha"])

    edited_df["Debe"] = pd.to_numeric(edited_df["Debe"], errors='coerce').fillna(0.0)
    edited_df["Haber"] = pd.to_numeric(edited_df["Haber"], errors='coerce').fillna(0.0)

    # Guardar en archivo manteniendo el formato
    edited_df.to_csv(DB_PATH, index=False)
    st.session_state.transactions = edited_df
    st.success("¡La base de datos local ha sido actualizada y recalculada exitosamente en COP!")
    st.rerun()
