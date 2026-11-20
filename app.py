import streamlit as st
import pandas as pd
import datetime
import os
from supabase import create_client

# =========================================================================
# 🔒 CONFIGURACIÓN DE SEGURIDAD Y CONEXIÓN A SUPABASE
# =========================================================================
# IMPORTANTE: Para que tus datos persistan al día siguiente, debes ir a la
# configuración de tu app en Streamlit Community Cloud (pestaña 'Secrets')
# y añadir tus credenciales reales en este formato:
#
# SUPABASE_URL = "https://tu-proyecto.supabase.co"
# SUPABASE_KEY = "tu-clave-anon-key-de-supabase"
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

# Rutas de base de datos locales (Únicamente como respaldo temporal en caché del contenedor)
DB_PATH = "movimientos_financieros.csv"
PRESTAMOS_PATH = "prestamos.csv"

# Cargar datos de transacciones de Supabase con respaldo local efímero
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

# Cargar datos de préstamos de Supabase con respaldo local efímero
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
                nueva_fila = {
                    "fecha": nueva_fecha,
                    "detalle": nuevo_detalle,
                    "cuenta": nueva_cuenta,
                    "debe": debe_val,
                    "haber": haber_val
                }
                df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
                df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
                df = df.dropna(subset=["fecha"])
                df.to_csv(DB_PATH, index=False)
                st.session_state.transactions = df

                if supabase:
                    data = {
                        "fecha": str(nueva_fecha),
                        "cuenta": nueva_cuenta,
                        "debe": debe_val,
                        "haber": haber_val,
                        "detalle": nuevo_detalle,
                    }
                    try:
                        supabase.table("transacciones").insert(data).execute()
                        st.sidebar.success("¡Registrado con éxito en la nube y localmente!")
                    except Exception as e:
                        st.sidebar.error(f"❌ Error al sincronizar con Supabase: {e}")
                else:
                    st.sidebar.warning("⚠️ Solo guardado local (Los cambios se perderán al reiniciar la app)")
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
                fila_salida = {
                    "fecha": trans_fecha,
                    "detalle": f"Transferencia enviada a {cuenta_destino}",
                    "cuenta": cuenta_origen,
                    "debe": 0.0,
                    "haber": monto_val
                }
                fila_entrada = {
                    "fecha": trans_fecha,
                    "detalle": f"Transferencia recibida desde {cuenta_origen}",
                    "cuenta": cuenta_destino,
                    "debe": monto_val,
                    "haber": 0.0
                }
                df = pd.concat([df, pd.DataFrame([fila_salida, fila_entrada])], ignore_index=True)
                df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
                df = df.dropna(subset=["fecha"])
                df.to_csv(DB_PATH, index=False)
                st.session_state.transactions = df

                if supabase:
                    datos_supabase = [
                        {
                            "fecha": str(trans_fecha),
                            "detalle": f"Transferencia enviada a {cuenta_destino}",
                            "cuenta": cuenta_origen,
                            "debe": 0.0,
                            "haber": monto_val
                        },
                        {
                            "fecha": str(trans_fecha),
                            "detalle": f"Transferencia recibida desde {cuenta_origen}",
                            "cuenta": cuenta_destino,
                            "debe": monto_val,
                            "haber": 0.0
                        }
                    ]
                    try:
                        supabase.table("transacciones").insert(datos_supabase).execute()
                        st.sidebar.success("¡Transferencia registrada en la nube y localmente!")
                    except Exception as e:
                        st.sidebar.error(f"❌ Error al guardar transferencia en Supabase: {e}")
                else:
                    st.sidebar.warning("⚠️ Guardado localmente (Sin conexión de respaldo)")
                st.rerun()

elif tipo_registro == "Préstamo Nuevo":
    with st.sidebar.form("nuevo_prestamo", clear_on_submit=True):
        p_fecha = st.date_input("Fecha Préstamo:", datetime.date.today())
        p_deudor = st.text_input("¿A quién le prestas? (Nombre):", "")
        p_cuenta_origen = st.selectbox("¿De qué cuenta sale el dinero?:", st.session_state.accounts_list)
        p_monto = st.number_input("Monto Prestado (COP):", min_value=0.0, step=1000.0, format="%.0f")

        p_tipo_int = st.sidebar.radio("¿Tiene Interés?:", ["Sin Interés", "Con Interés"])
        p_tasa = st.number_input("Porcentaje de Interés (%):", min_value=0.0, max_value=100.0, value=0.0, step=0.5)

        boton_prestar = st.form_submit_button("Registrar Préstamo")

        if boton_prestar:
            if not p_deudor:
                st.sidebar.error("Escribe el nombre del deudor.")
            elif p_monto <= 0:
                st.sidebar.error("El monto prestado debe ser mayor a 0.")
            else:
                monto_estimado = p_monto + (p_monto * (p_tasa / 100.0)) if p_tipo_int == "Con Interés" else p_monto

                nuevo_p = {
                    "fecha": p_fecha,
                    "deudor": p_deudor,
                    "monto_inicial": float(p_monto),
                    "tasa_interes": float(p_tasa) if p_tipo_int == "Con Interés" else 0.0,
                    "monto_total_estimado": float(monto_estimado),
                    "monto_pagado": 0.0,
                    "intereses_pagados_reales": 0.0,
                    "cuenta_origen": p_cuenta_origen,
                    "estado": "Pendiente"
                }
                df_prestamos = pd.concat([df_prestamos, pd.DataFrame([nuevo_p])], ignore_index=True)
                df_prestamos.to_csv(PRESTAMOS_PATH, index=False)
                st.session_state.prestamos = df_prestamos

                if supabase:
                    try:
                        supabase.table("prestamos").insert({
                            "fecha": str(p_fecha),
                            "deudor": p_deudor,
                            "monto_inicial": float(p_monto),
                            "tasa_interes": float(p_tasa) if p_tipo_int == "Con Interés" else 0.0,
                            "monto_total_estimado": float(monto_estimado),
                            "monto_pagado": 0.0,
                            "intereses_pagados_reales": 0.0,
                            "cuenta_origen": p_cuenta_origen,
                            "estado": "Pendiente"
                        }).execute()
                        st.sidebar.success(f"¡Préstamo de {p_monto:,.0f} COP registrado en la nube!")
                    except Exception as e:
                        st.sidebar.error(f"❌ Error al registrar préstamo en Supabase: {e}")

                # Registrar egreso automático de transacciones
                fila_salida = {
                    "fecha": p_fecha,
                    "detalle": f"Préstamo otorgado a {p_deudor}",
                    "cuenta": p_cuenta_origen,
                    "debe": 0.0,
                    "haber": float(p_monto)
                }
                df = pd.concat([df, pd.DataFrame([fila_salida])], ignore_index=True)
                df.to_csv(DB_PATH, index=False)
                st.session_state.transactions = df

                if supabase:
                    try:
                        supabase.table("transacciones").insert({
                            "fecha": str(p_fecha),
                            "detalle": f"Préstamo otorgado a {p_deudor}",
                            "cuenta": p_cuenta_origen,
                            "debe": 0.0,
                            "haber": float(p_monto)
                        }).execute()
                    except Exception:
                        pass
                st.rerun()

elif tipo_registro == "Cobrar Préstamo":
    prestamos_pendientes = df_prestamos[df_prestamos["estado"] == "Pendiente"]
    if prestamos_pendientes.empty:
        st.sidebar.warning("No hay préstamos pendientes por cobrar.")
    else:
        with st.sidebar.form("cobrar_prestamo", clear_on_submit=True):
            opciones_p = prestamos_pendientes.apply(lambda r: f"{r['deudor']} (Inicial: {r['monto_inicial']:,.0f} | Pendiente: {r['monto_total_estimado'] - r['monto_pagado']:,.0f})", axis=1).tolist()
            seleccion_idx = st.selectbox("Selecciona el préstamo:", range(len(prestamos_pendientes)), format_func=lambda x: opciones_p[x])
            prestamo_seleccionado = prestamos_pendientes.iloc[seleccion_idx]

            c_fecha = st.date_input("Fecha del cobro:", datetime.date.today())
            c_cuenta_destino = st.selectbox("¿A qué cuenta ingresa el pago?:", st.session_state.accounts_list)

            saldo_capital_pelt = prestamo_seleccionado["monto_inicial"] - prestamo_seleccionado["monto_pagado"]
            c_capital = st.number_input("Monto abonado al Capital (COP):", min_value=0.0, max_value=float(saldo_capital_pelt), value=float(saldo_capital_pelt), step=1000.0, format="%.0f")
            c_intereses = st.number_input("Intereses Recibidos Reales:", min_value=0.0, value=0.0, step=1000.0, format="%.0f")

            boton_cobrar = st.form_submit_button("Registrar Cobro")

            if boton_cobrar:
                if c_capital <= 0 and c_intereses <= 0:
                    st.sidebar.error("El abono de capital o los intereses deben ser mayores a 0.")
                else:
                    nuevo_pago = float(prestamo_seleccionado["monto_pagado"] + c_capital)
                    nuevos_intereses = float(prestamo_seleccionado["intereses_pagados_reales"] + c_intereses)
                    nuevo_estado = "Pagado" if nuevo_pago >= prestamo_seleccionado["monto_inicial"] else "Pendiente"

                    idx_original = prestamo_seleccionado.name
                    df_prestamos.at[idx_original, "monto_pagado"] = nuevo_pago
                    df_prestamos.at[idx_original, "intereses_pagados_reales"] = nuevos_intereses
                    df_prestamos.at[idx_original, "estado"] = nuevo_estado
                    df_prestamos.to_csv(PRESTAMOS_PATH, index=False)
                    st.session_state.prestamos = df_prestamos

                    if supabase:
                        try:
                            p_id = prestamo_seleccionado["id"]
                            supabase.table("prestamos").update({
                                "monto_pagado": nuevo_pago,
                                "intereses_pagados_reales": nuevos_intereses,
                                "estado": nuevo_estado
                            }).eq("id", p_id).execute()
                        except Exception as e:
                            st.sidebar.error(f"❌ No se pudo actualizar préstamo en Supabase: {e}")

                    total_recibido = c_capital + c_intereses
                    if total_recibido > 0:
                        fila_entrada = {
                            "fecha": c_fecha,
                            "detalle": f"Abono préstamo de {prestamo_seleccionado['deudor']} (Cap: {c_capital:,.0f} | Int: {c_intereses:,.0f})",
                            "cuenta": c_cuenta_destino,
                            "debe": float(total_recibido),
                            "haber": 0.0
                        }
                        df = pd.concat([df, pd.DataFrame([fila_entrada])], ignore_index=True)
                        df.to_csv(DB_PATH, index=False)
                        st.session_state.transactions = df

                        if supabase:
                            try:
                                supabase.table("transacciones").insert({
                                    "fecha": str(c_fecha),
                                    "detalle": f"Abono préstamo de {prestamo_seleccionado['deudor']} (Cap: {c_capital:,.0f} | Int: {c_intereses:,.0f})",
                                    "cuenta": c_cuenta_destino,
                                    "debe": float(total_recibido),
                                    "haber": 0.0
                                }).execute()
                            except Exception:
                                pass
                    st.sidebar.success("¡Cobro registrado con éxito!")
                    st.rerun()

# =========================================================================
# VISUALIZACIÓN DE TABLEROS Y MÉTRICAS
# =========================================================================
# Filtro de Mes
if not df.empty and df["mes_auto"].notna().any():
    valid_months = df["mes_auto"].dropna().unique()
    months = sorted(list(valid_months))
else:
    months = [datetime.date(datetime.date.today().year, datetime.date.today().month, 1)]

selected_month = st.sidebar.selectbox(
    "📅 Filtrar por Mes:",
    options=months,
    format_func=lambda x: x.strftime("%B %Y").capitalize() if hasattr(x, 'strftime') else str(x)
)

# Segmentación de datos (histórico vs mes seleccionado)
if not df.empty:
    df_before = df[df["mes_auto"] < selected_month]
    df_month = df[df["mes_auto"] == selected_month]
else:
    df_before = pd.DataFrame(columns=["cuenta", "debe", "haber"])
    df_month = pd.DataFrame(columns=["cuenta", "debe", "haber"])

# Panel de Cuentas T
cuentas = st.session_state.accounts_list
st.markdown(f"### 📊 Estado de tus Cuentas (COP) - {selected_month.strftime('%B %Y').capitalize() if hasattr(selected_month, 'strftime') else str(selected_month)}")

cols = st.columns(len(cuentas)) if len(cuentas) > 0 else []
total_capital = 0.0

for idx, cta in enumerate(cuentas):
    debe_ant = df_before[df_before["cuenta"] == cta]["debe"].sum() if not df_before.empty else 0.0
    haber_ant = df_before[df_before["cuenta"] == cta]["haber"].sum() if not df_before.empty else 0.0
    saldo_ini = debe_ant - haber_ant

    debe_mes = df_month[df_month["cuenta"] == cta]["debe"].sum() if not df_month.empty else 0.0
    haber_mes = df_month[df_month["cuenta"] == cta]["haber"].sum() if not df_month.empty else 0.0

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

# =========================================================================
# EDICIÓN DIRECTA DE TABLAS (ADMINISTRACIÓN Y CORRECCIONES)
# =========================================================================
st.divider()
st.markdown("### 👥 Control y Seguimiento de Préstamos")
if df_prestamos.empty:
    st.info("No tienes registros de préstamos todavía.")
else:
    df_prestamos_ver = df_prestamos.copy()
    df_prestamos_ver["Pendiente de Cobro"] = df_prestamos_ver["monto_inicial"] - df_prestamos_ver["monto_pagado"]

    edited_prestamos_df = st.data_editor(
        df_prestamos_ver,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "fecha": st.column_config.DateColumn("Fecha Préstamo"),
            "deudor": st.column_config.TextColumn("Deudor"),
            "monto_inicial": st.column_config.NumberColumn("Monto Inicial", format="$ %d"),
            "tasa_interes": st.column_config.NumberColumn("Interés (%)"),
            "monto_pagado": st.column_config.NumberColumn("Capital Abonado", format="$ %d"),
            "Pendiente de Cobro": st.column_config.NumberColumn("Capital Pendiente (Calculado)", format="$ %d", disabled=True),
            "intereses_pagados_reales": st.column_config.NumberColumn("Intereses Recaudados", format="$ %d"),
            "cuenta_origen": st.column_config.TextColumn("Cuenta Origen"),
            "estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente", "Pagado"])
        },
        key="prestamos_editor"
    )

    if st.button("💾 Guardar Cambios en Préstamos"):
        edited_prestamos_df["fecha"] = pd.to_datetime(edited_prestamos_df["fecha"], errors='coerce').dt.date
        edited_prestamos_df = edited_prestamos_df.dropna(subset=["fecha"])
        edited_prestamos_df["monto_total_estimado"] = edited_prestamos_df["monto_inicial"] + (edited_prestamos_df["monto_inicial"] * (edited_prestamos_df["tasa_interes"] / 100.0))

        columnas_guardar = ["id", "fecha", "deudor", "monto_inicial", "tasa_interes", "monto_total_estimado", "monto_pagado", "intereses_pagados_reales", "cuenta_origen", "estado"]
        for col in columnas_guardar:
            if col not in edited_prestamos_df.columns:
                edited_prestamos_df[col] = None

        df_p_guardar = edited_prestamos_df[columnas_guardar]
        df_p_guardar.to_csv(PRESTAMOS_PATH, index=False)
        st.session_state.prestamos = df_p_guardar

        if supabase:
            try:
                # Sincronización masiva rápida
                for _, row in df_p_guardar.iterrows():
                    row_data = row.to_dict()
                    row_data["fecha"] = str(row_data["fecha"])
                    if pd.notna(row_data.get("id")):
                        supabase.table("prestamos").upsert(row_data).execute()
                    else:
                        # Si es nuevo fila sin ID aún
                        row_data.pop("id", None)
                        supabase.table("prestamos").insert(row_data).execute()
                st.success("¡La base de datos de préstamos se sincronizó correctamente con la nube!")
            except Exception as e:
                st.error(f"❌ Error al actualizar préstamos en Supabase: {e}")
        else:
            st.success("¡La base de datos de préstamos ha sido actualizada temporalmente en el caché local!")
        st.rerun()

st.divider()
st.markdown("### 📝 Editor y Visor de Base de Datos (COP)")
df_ordenado = df[["id", "fecha", "detalle", "cuenta", "debe", "haber"]].sort_values(by="fecha", ascending=True) if "id" in df.columns else df[["fecha", "detalle", "cuenta", "debe", "haber"]].sort_values(by="fecha", ascending=True)

edited_df = st.data_editor(
    df_ordenado,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "fecha": st.column_config.DateColumn("Fecha"),
        "detalle": st.column_config.TextColumn("Detalle"),
        "cuenta": st.column_config.TextColumn("Cuenta"),
        "debe": st.column_config.NumberColumn("Debe / Entra (COP)", format="%d"),
        "haber": st.column_config.NumberColumn("Haber / Sale (COP)", format="%d"),
    },
    key="db_editor"
)

if st.button("💾 Aplicar y Guardar Cambios en Base de Datos"):
    edited_df["fecha"] = pd.to_datetime(edited_df["fecha"], errors='coerce').dt.date
    edited_df = edited_df.dropna(subset=["fecha"])
    edited_df["debe"] = pd.to_numeric(edited_df["debe"], errors='coerce').fillna(0.0)
    edited_df["haber"] = pd.to_numeric(edited_df["haber"], errors='coerce').fillna(0.0)

    edited_df.to_csv(DB_PATH, index=False)
    st.session_state.transactions = edited_df

    if supabase:
        try:
            for _, row in edited_df.iterrows():
                row_data = row.to_dict()
                row_data["fecha"] = str(row_data["fecha"])
                if "id" in row_data and pd.notna(row_data["id"]):
                    supabase.table("transacciones").upsert(row_data).execute()
                else:
                    row_data.pop("id", None)
                    supabase.table("transacciones").insert(row_data).execute()
            st.success("¡La base de datos se ha guardado en la nube de Supabase correctamente!")
        except Exception as e:
            st.error(f"❌ Error al escribir cambios en Supabase: {e}")
    else:
        st.success("¡Cambios aplicados localmente de forma temporal!")
    st.rerun()
