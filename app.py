import os
from datetime import datetime
import pandas as pd
import streamlit as st


# ----------------- Config -----------------
st.set_page_config(page_title="Gestión de Ventas", page_icon="📊", layout="centered")

PERSONAS_DEFAULT = ["Pepe", "Frank", "Porfi", "Alva", "Freddy", "Vitol", "Douglas", "Villa"]

ARCHIVO_RESUMEN = "resumen_compras_ventas.csv"
ARCHIVO_HISTORIAL = "historial_transacciones.csv"
ARCHIVO_TXT = "resumen_final.txt"


# ----------------- Persistencia -----------------
def cargar_estado(personas):
    # Resumen
    if os.path.exists(ARCHIVO_RESUMEN):
        df = pd.read_csv(ARCHIVO_RESUMEN, index_col=0)
        resumen = df[["Compras", "Ventas"]].to_dict("index")
    else:
        resumen = {n: {"Compras": 300.0, "Ventas": 0.0} for n in personas}

    # Historial
    if os.path.exists(ARCHIVO_HISTORIAL) and os.path.getsize(ARCHIVO_HISTORIAL) > 0:
        try:
            transacciones = pd.read_csv(ARCHIVO_HISTORIAL).to_dict("records")
        except pd.errors.EmptyDataError:
            transacciones = []
    else:
        transacciones = []

    # Asegurar que todas las personas existan en resumen
    for n in personas:
        if n not in resumen:
            resumen[n] = {"Compras": 300.0, "Ventas": 0.0}

    # Limpiar personas que ya no están (opcional)
    resumen = {k: v for k, v in resumen.items() if k in personas}

    return resumen, transacciones


def guardar_estado(resumen, transacciones):
    df = pd.DataFrame(resumen).T
    df["Diferencia"] = df["Ventas"] - df["Compras"]
    df.to_csv(ARCHIVO_RESUMEN)

    pd.DataFrame(transacciones).to_csv(ARCHIVO_HISTORIAL, index=False)


def df_resumen(resumen):
    df = pd.DataFrame(resumen).T
    df["Diferencia"] = df["Ventas"] - df["Compras"]
    df = df.sort_values("Diferencia", ascending=False)
    return df


def generar_txt(resumen):
    df = df_resumen(resumen)
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_compras = float(df["Compras"].sum())
    total_ventas = float(df["Ventas"].sum())

    with open(ARCHIVO_TXT, "w", encoding="utf-8") as f:
        f.write("📊 RESUMEN FINAL DE COMPRAS Y VENTAS\n")
        f.write(f"📅 Generado el {fecha} por Publio\n\n")
        f.write("{:<10} {:>10} {:>10} {:>12}\n".format("Nombre", "Compras", "Ventas", "Diferencia"))
        f.write("-" * 46 + "\n")
        for nombre, fila in df.iterrows():
            f.write("{:<10} {:>10.1f} {:>10.1f} {:>12.1f}\n".format(
                nombre, float(fila["Compras"]), float(fila["Ventas"]), float(fila["Diferencia"])
            ))
        f.write("\n📦 Totales Globales:\n")
        f.write(f"Total Compras: {total_compras}\n")
        f.write(f"Total Ventas:  {total_ventas}\n")
        f.write(f"Diferencia Total: {total_ventas - total_compras}\n")

    return ARCHIVO_TXT


def resetear(personas):
    resumen = {n: {"Compras": 300.0, "Ventas": 0.0} for n in personas}
    transacciones = []
    for f in [ARCHIVO_RESUMEN, ARCHIVO_HISTORIAL, ARCHIVO_TXT]:
        if os.path.exists(f):
            os.remove(f)
    guardar_estado(resumen, transacciones)
    return resumen, transacciones


# ----------------- UI -----------------
st.title("📊 Gestión de Compras y Ventas")
st.caption("Versión web del script de Pythonista. Aquí no hay `console.alert`, pero hay botones (más civilizados).")

with st.sidebar:
    st.subheader("⚙️ Configuración")
    personas_text = st.text_area(
        "Personas (una por línea)",
        value="\n".join(PERSONAS_DEFAULT),
        height=200
    )
    personas = [p.strip().capitalize() for p in personas_text.splitlines() if p.strip()]
    if not personas:
        st.warning("Agrega al menos 1 persona.")
        st.stop()

    if st.button("🔄 Cargar/Refrescar datos", use_container_width=True):
        st.session_state.resumen, st.session_state.transacciones = cargar_estado(personas)
        st.success("Datos cargados.")

    if st.button("🧨 Nueva corrida (reiniciar)", use_container_width=True):
        st.session_state.resumen, st.session_state.transacciones = resetear(personas)
        st.success("Datos reiniciados.")


# Inicialización de session_state
if "resumen" not in st.session_state or "transacciones" not in st.session_state:
    st.session_state.resumen, st.session_state.transacciones = cargar_estado(personas)

# Asegurar que coincida con lista actual de personas
st.session_state.resumen, st.session_state.transacciones = cargar_estado(personas)


tab1, tab2, tab3 = st.tabs(["➕ Agregar", "📈 Resumen", "📜 Historial"])


with tab1:
    st.subheader("➕ Agregar transacción")

    col1, col2 = st.columns(2)
    with col1:
        vendedor = st.selectbox("Vendedor", personas, index=0)
    with col2:
        comprador_opciones = ["(sin comprador)"] + personas
        comprador_sel = st.selectbox("Comprador", comprador_opciones, index=0)

    comprador = "" if comprador_sel == "(sin comprador)" else comprador_sel
    monto = st.number_input("Monto", min_value=0.0, value=0.0, step=1.0, format="%.2f")

    if st.button("✅ Guardar transacción", use_container_width=True):
        if vendedor not in st.session_state.resumen:
            st.error("Vendedor inválido.")
        elif comprador and comprador not in st.session_state.resumen:
            st.error("Comprador inválido.")
        elif monto <= 0:
            st.error("El monto debe ser mayor que 0.")
        else:
            st.session_state.resumen[vendedor]["Ventas"] += float(monto)
            if comprador:
                st.session_state.resumen[comprador]["Compras"] += float(monto)

            st.session_state.transacciones.append({
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Vendedor": vendedor,
                "Comprador": comprador,
                "Monto": float(monto),
            })

            guardar_estado(st.session_state.resumen, st.session_state.transacciones)

            extra = f"a {comprador}" if comprador else "(sin comprador)"
            st.success(f"Registrado: {vendedor} vendió {monto:.2f} {extra}.")


with tab2:
    st.subheader("📈 Resumen")
    df = df_resumen(st.session_state.resumen)
    st.dataframe(df, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Compras", f"{df['Compras'].sum():.1f}")
    c2.metric("Total Ventas", f"{df['Ventas'].sum():.1f}")
    c3.metric("Diferencia Total", f"{(df['Ventas'].sum() - df['Compras'].sum()):.1f}")

    st.divider()

    colA, colB = st.columns(2)

    with colA:
        if st.button("❌ Eliminar última transacción", use_container_width=True):
            if not st.session_state.transacciones:
                st.warning("No hay transacciones para eliminar.")
            else:
                ultima = st.session_state.transacciones.pop()
                v = ultima.get("Vendedor", "")
                c = ultima.get("Comprador", "")
                m = float(ultima.get("Monto", 0.0))

                if v in st.session_state.resumen:
                    st.session_state.resumen[v]["Ventas"] -= m
                if c and c in st.session_state.resumen:
                    st.session_state.resumen[c]["Compras"] -= m

                guardar_estado(st.session_state.resumen, st.session_state.transacciones)
                st.success(f"Eliminada: {v} → {c if c else '(sin comprador)'} por {m:.2f}")

    with colB:
        if st.button("📝 Generar TXT", use_container_width=True):
            ruta = generar_txt(st.session_state.resumen)
            st.success(f"Archivo generado: {ruta}")

            # Descargar desde la web
            with open(ruta, "rb") as f:
                st.download_button(
                    "⬇️ Descargar resumen_final.txt",
                    data=f,
                    file_name=ruta,
                    mime="text/plain",
                    use_container_width=True
                )


with tab3:
    st.subheader("📜 Historial")
    if not st.session_state.transacciones:
        st.info("Aún no hay transacciones.")
    else:
        dfh = pd.DataFrame(st.session_state.transacciones)
        st.dataframe(dfh.tail(200), use_container_width=True)

        st.divider()
        st.subheader("🔎 Historial por persona")
        persona_sel = st.selectbox("Elegir persona", personas)

        compras = dfh[dfh["Comprador"] == persona_sel]
        ventas = dfh[dfh["Vendedor"] == persona_sel]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**🛒 Compras de {persona_sel}**")
            st.dataframe(compras if not compras.empty else pd.DataFrame(), use_container_width=True)
        with col2:
            st.markdown(f"**💰 Ventas de {persona_sel}**")
            st.dataframe(ventas if not ventas.empty else pd.DataFrame(), use_container_width=True)
