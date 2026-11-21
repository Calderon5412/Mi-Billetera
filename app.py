import streamlit as st
import pandas as pd
import datetime
import os
from supabase import create_client

# =========================================================================
# 🔒 CONFIGURACIÓN DE SEGURIDAD Y CONEXIÓN A SUPABASE
# =========================================================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.sidebar.error("⚠️ No se pudo inicializar la conexión con Supabase. Verifica tus Secrets en Streamlit Cloud.")
    st.sidebar.caption(f"Detalle del error: {e}")
    supabase = None

# Código de acceso simple a la UI de la aplicación
CODIGO_ACCESO = "124"  # Cambia esto por tu PIN o contraseña favorita

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

# Inicializar estado de sesión para el login
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# Pantalla de Login Simple
if not st.session_state.autenticado:
    st.title("🔑 Acceso Protegido")
    st.markdown("Por favor ingresa el código de acceso para ver la información financiera.")

    codigo_ingresado = st.text_input("Código de Seguridad:", type="password")
    if st.button("Ingresar"):
        if codigo_ingresado == CODIGO_ACCESO:
            st.session_state.autenticado = True
            st.success("¡Acceso concedido!")
            st.rerun()
        else:
            st.error("Código de seguridad incorrecto. Inténtalo de nuevo.")
    st.stop()

# Rutas de base de datos locales
DB_PATH = "movimientos_financieros.csv"
PRESTAMOS_PATH = "prestamos.csv"

# Cargar datos de transacciones de Supabase
def cargar_datos():
    if supabase:
        try:
            response = (
                supabase.table("transacciones")
                .select("*")
                .order("id", desc=True)
                .execute()
            )
            if response.data:
                df = pd.DataFrame(response.data)
                df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
                return df
        except Exception as e:
            st.warning(f"⚠️ Error al recuperar transacciones de Supabase (usando respaldo temporal): {e}")

    if os.path.exists(DB_PATH):
        try:
            df_local = pd.read_csv(DB_PATH)
            df_local["fecha"] = pd.to_datetime(df_local["fecha"], errors="coerce").dt.date
            return df_local
        except Exception:
            pass
    return pd.DataFrame(columns=["id", "fecha", "detalle", "cuenta", "debe", "haber"])

# Cargar datos de préstamos de Supabase
def cargar_prestamos():
    if supabase:
        try:
            response = (
                supabase.table("prestamos")
                .select("*")
                .order("id", desc=True)
                .execute()
            )
            if response.data:
                df_p = pd.DataFrame(response.data)
                df_p["fecha"] = pd.to_datetime(df_p["fecha"], errors="coerce").dt.date
                return df_p
        except Exception as e:
            st.warning(f"⚠️ Error al recuperar préstamos de Supabase (usando respaldo temporal): {e}")

    if os.path.exists(PRESTAMOS_PATH):
        try:
            df_p = pd.read_csv(PRESTAMOS_PATH)
            df_p["fecha"] = pd.to_datetime(df_p["fecha"], errors="coerce").dt.date
            return df_p
        except Exception:
            pass
    return pd.DataFrame(columns=["id", "fecha", "deudor", "monto_inicial", "tasa_interes", "monto_total_estimado", "monto_pagado", "intereses_pagados_reales", "cuenta_origen", "estado"])

# Inicializar estados de sesión
if 'transactions' not in st.session_state:
    st.session_state.transactions = cargar_datos()

if 'prestamos' not in st.session_state:
    st.session_state.prestamos = cargar_prestamos()

df = st.session_state.transactions.copy()
df_prestamos = st.session_state.prestamos.copy()

# Lista de cuentas dinámicas por defecto
cuentas_defecto = ["Efectivo", "Nequi", "Nu", "BBVA", "Pibank"]
if 'accounts_list' not in st.session_state:
    if not df.empty:
        cuentas_existentes = list(df["cuenta"].dropna().unique())
        for c in cuentas_existentes:
            if c not in cuentas_defecto:
                cuentas_defecto.append(c)
    st.session_state.accounts_list = cuentas_defecto

# Formatear fechas de transacciones de forma segura
if not df.empty:
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
    df = df.dropna(subset=["fecha"])
    df["mes_auto"] = df["fecha"].apply(lambda x: datetime.date(x.year, x.month, 1) if isinstance(x, (datetime.date, datetime.datetime)) else None)
    df = df.dropna(subset=["mes_auto"])
else:
    df["mes_auto"] = None

# Botón de Cerrar Sesión en Sidebar
if st.sidebar.button("🔒 Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()

# Título de la app
st.title("💰 Mi Billetera Calde' - Pesos Colombianos (COP)")
st.markdown("Esta aplicación trabaja de forma sincronizada y almacena la información de forma persistente en **Supabase**.")

# Sidebar - Gestión de Cuentas
st.sidebar.header("⚙️ Gestionar Cuentas")
with st.sidebar.expander("🛠️ Añadir Nueva Cuenta"):
    nueva_cta_nombre = st.text_input("Nombre de la cuenta:", "")
    if st.button("Crear Cuenta"):
        if nueva_cta_nombre and nueva_cta_nombre not in st.session_state.accounts_list:
            st.session_state.accounts_list.append(nueva_cta_nombre)
            st.success(f"¡Cuenta '{nueva_cta_nombre}' añadida!")
            st.rerun()

# Sidebar - Registrar Operación
st.sidebar.header("➕ Registrar Operación")
tipo_registro = st.sidebar.radio("Selecciona tipo de registro:", ["Movimiento Simple", "Transferencia entre Cuentas", "Préstamo Nuevo", "Cobrar Préstamo"])

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
                debe_val = float(monto) if "Ingreso" in tipo_mov else 0.0
                haber_val = float(monto) if "Egreso" in tipo_mov else 0.0

                if supabase:
                    data = {
                        "fecha": str(nueva_fecha),
                        "cuenta": nueva_cuenta,
                        "debe": debe_val,
                        "haber": haber_val,
                        "detalle": nuevo_detalle,
                    }
                    try:
                        res = supabase.table("transacciones").insert(data).execute()
                        if res.data:
                            nueva_fila = res.data[0]
                        else:
                            nueva_fila = {"fecha": nueva_fecha, "detalle": nuevo_detalle, "cuenta": nueva_cuenta, "debe": debe_val, "haber": haber_val}
                        st.sidebar.success("¡Registrado con éxito en la nube y localmente!")
                    except Exception as e:
                        st.sidebar.error(f"❌ Error al sincronizar con Supabase: {e}")
                        nueva_fila = {"fecha": nueva_fecha, "detalle": nuevo_detalle, "cuenta": nueva_cuenta, "debe": debe_val, "haber": haber_val}
                else:
                    nueva_fila = {"fecha": nueva_fecha, "detalle": nuevo_detalle, "cuenta": nueva_cuenta, "debe": debe_val, "haber": haber_val}
                    st.sidebar.warning("⚠️ Solo guardado local (Los cambios se perderán al reiniciar la app)")

                df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
                df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
                df = df.dropna(subset=["fecha"])
                df.to_csv(DB_PATH, index=False)
                st.session_state.transactions = df
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
                monto_val = float(trans_monto)
                datos_supabase = [
                    {
                        "fecha": str(trans_fecha),
                        "detalle": f
