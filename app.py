"""
Análisis de Portafolio
======================

Aplicación web para analizar y medir el rendimiento de una cartera de inversión.
Muestra activos con nominales positivos después del último reset a cero.

Autor: Santiago Aronson
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

# Me8: suprimir solo warnings específicos, no todos globalmente
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning, module='streamlit')

# ─────────────────────────────────────────────
# Configuración de la página
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Análisis de Portafolio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .positive {
        color: #00C851;
    }
    .negative {
        color: #ff4444;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Carga de datos
# ─────────────────────────────────────────────
def load_data(filename='operaciones.xlsx'):
    """Cargar datos desde operaciones.xlsx o archivo especificado."""
    try:
        # Cargar hoja Operaciones
        operaciones = pd.read_excel(filename, sheet_name='Operaciones')

        operaciones_mapped = pd.DataFrame()
        operaciones_mapped['Fecha']    = operaciones['Fecha']
        operaciones_mapped['Tipo']     = operaciones['Operacion']
        operaciones_mapped['Activo']   = operaciones['Activo']
        operaciones_mapped['Cantidad'] = operaciones['Nominales']
        operaciones_mapped['Precio']   = operaciones['Precio']
        operaciones_mapped['Monto']    = operaciones['Valor']

        # Me2: normalizar capitalización para que 'compra', 'VENTA', etc. funcionen
        operaciones_mapped['Tipo']   = operaciones_mapped['Tipo'].str.strip().str.title()
        operaciones_mapped['Activo'] = operaciones_mapped['Activo'].str.strip()
        operaciones_mapped = operaciones_mapped.dropna(
            subset=['Fecha', 'Tipo', 'Activo', 'Monto']
        )

        # C5: descartar Compra/Venta sin Nominales y avisar al usuario
        mask_bs  = operaciones_mapped['Tipo'].isin(['Compra', 'Venta'])
        invalid  = operaciones_mapped[mask_bs & operaciones_mapped['Cantidad'].isna()]
        if not invalid.empty:
            activos_inv = ', '.join(invalid['Activo'].dropna().unique())
            st.warning(
                f"⚠️ Se ignoraron {len(invalid)} fila(s) de Compra/Venta sin Nominales "
                f"({activos_inv}). Verificar el Excel."
            )
        operaciones_mapped = operaciones_mapped[
            ~(mask_bs & operaciones_mapped['Cantidad'].isna())
        ]

        # Cargar hoja Precios
        precios = pd.read_excel(filename, sheet_name='Precios')
        fecha_col = precios.columns[0]
        precios = precios.rename(columns={fecha_col: 'Fecha'})
        precios_long = precios.melt(
            id_vars=['Fecha'],
            var_name='Activo',
            value_name='Precio'
        ).dropna()

        return operaciones_mapped, precios_long

    except FileNotFoundError:
        st.error(f"No se encontró el archivo '{filename}' en la carpeta del proyecto.")
        return None, None
    except Exception as e:
        st.error(f"Error al cargar el archivo: {str(e)}")
        return None, None


# ─────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────
def _clasificar_operacion(tipo: str):
    """Devuelve la categoría de una operación de flujo."""
    t = tipo.strip().lower()
    if 'amortizacion' in t or 'amortización' in t:
        return 'amortizacion'
    if 'cupon' in t or 'coupon' in t:
        return 'cupon'
    if 'dividendo' in t or 'dividend' in t:
        return 'dividendo'
    return None


def _find_last_reset(asset_ops_sorted):
    """
    Recorre las operaciones y devuelve (fecha_reset, pos_reset) del último
    momento en que los nominales pasan de positivo a ≤ 0.

    Retorna (None, -1) si nunca ocurrió un reset.

    pos_reset es el índice iloc de la operación que causó el reset.
    Usarlo como ops.iloc[pos_reset + 1:] garantiza que operaciones del
    mismo día posteriores al reset (C2) sí queden incluidas en ops_since_reset.
    """
    running = 0
    last_reset_date = None
    last_reset_pos  = -1
    for i, (_, op) in enumerate(asset_ops_sorted.iterrows()):
        prev = running
        if op['Tipo'].strip() == 'Compra':
            running += op['Cantidad']
        elif op['Tipo'].strip() == 'Venta':
            running -= op['Cantidad']
        if prev > 0 and running <= 0:
            last_reset_date = op['Fecha']
            last_reset_pos  = i
            running = 0
    return last_reset_date, last_reset_pos


# ─────────────────────────────────────────────
# Composición actual
# ─────────────────────────────────────────────
def calculate_current_portfolio(operaciones, precios, fecha_actual):
    """
    Calcula la composición actual de la cartera con lógica de reseteo.

    El Costo usa Costo Promedio Ponderado (CPP):
      - En cada Compra se recalcula el costo unitario promedio.
      - En cada Venta los nominales bajan pero el costo unitario NO cambia,
        por lo que el Costo de la posición restante se reduce proporcionalmente.
      - Este es el método estándar de bancos y brokers (CNV / IFRS).

    Tratamiento de Amortizaciones (precio dirty argentino):
      - Los nominales NO se modifican: el precio dirty ya cotiza contra el
        VNO (Valor Nominal Original), por lo que Valor Actual = nom × precio_dirty
        es correcto sin tocar los nominales.
      - El Costo NO se ajusta por amortizaciones (estándar de bancos y brokers):
        Costo = suma de compras (CPP). La caída del precio dirty al momento
        de la amortización ya refleja la devolución de capital en Ganancias
        no Realizadas. La columna Amortizaciones muestra el cash cobrado.
      - Fórmula verificable por el usuario:
        Ganancia Total = Ganancias no Realizadas + Amortizaciones + Cupones + Dividendos

    Columnas de salida:
        Activo | Nominales | Precio Actual | _Valor Actual (interno) |
        Costo | Amortizaciones | Cupones | Dividendos | Ganancias no Realizadas
    """
    operaciones = operaciones.copy()
    precios = precios.copy()
    operaciones['Fecha'] = pd.to_datetime(operaciones['Fecha'])
    precios['Fecha']     = pd.to_datetime(precios['Fecha'])

    assets = [a for a in operaciones['Activo'].unique() if pd.notna(a)]
    portfolio_data = []

    for asset in assets:
        asset_ops = operaciones[operaciones['Activo'] == asset].sort_values('Fecha')
        asset_ops_until = asset_ops[asset_ops['Fecha'] <= pd.to_datetime(fecha_actual)]

        if asset_ops_until.empty:
            continue

        # Último reset a cero (C2: filtrar por posición iloc, no por fecha)
        last_reset_date, last_reset_pos = _find_last_reset(asset_ops_until)

        if last_reset_date is None:
            ops = asset_ops_until
        else:
            ops = asset_ops_until.iloc[last_reset_pos + 1:]

        # ── Precio más reciente (necesario también para C4) ──────────────
        asset_prices = precios[precios['Activo'] == asset].sort_values('Fecha')
        available    = asset_prices[asset_prices['Fecha'] <= pd.to_datetime(fecha_actual)]
        if available.empty:
            # M3: avisar en lugar de descartar silenciosamente
            st.warning(
                f"⚠️ {asset}: sin precio disponible hasta el "
                f"{fecha_actual.strftime('%d/%m/%Y')}. Se excluye de la cartera."
            )
            continue

        # ── C4: Detectar ventas sin compra previa ────────────────────────
        # Si el total de ventas supera el total de compras post-reset,
        # se infiere una compra anterior al inicio de la base de datos.
        nota = ''
        buys_q  = ops[ops['Tipo'].str.strip() == 'Compra']['Cantidad'].sum()
        sells_q = ops[ops['Tipo'].str.strip() == 'Venta']['Cantidad'].sum()
        buys_q  = buys_q  if not pd.isna(buys_q)  else 0
        sells_q = sells_q if not pd.isna(sells_q) else 0
        deficit = sells_q - buys_q
        if deficit > 0:
            oldest_row   = asset_prices.iloc[0]
            oldest_price = oldest_row['Precio']
            oldest_date  = oldest_row['Fecha']
            synthetic    = pd.DataFrame([{
                'Fecha':    oldest_date,
                'Tipo':     'Compra',
                'Activo':   asset,
                'Cantidad': deficit,
                'Precio':   oldest_price,
                'Monto':    deficit * oldest_price,
            }])
            ops  = pd.concat([synthetic, ops]).sort_values('Fecha').reset_index(drop=True)
            nota = (
                f'⚠️ {asset}: compra de origen no registrada — se estimaron '
                f'{deficit:.0f} nominales al precio más antiguo disponible '
                f'(${oldest_price:.2f} al {oldest_date.strftime("%d/%m/%Y")}). '
                f'Probable operación anterior al inicio de la base de datos.'
            )

        # ── Costo Promedio Ponderado ──────────────────────────────────────
        # En Compra: se recalcula ponderando el lote nuevo con la posición previa.
        # En Venta:  los nominales bajan pero el costo unitario no cambia.
        # Amortizaciones: NO ajustan el costo (estándar broker argentino).
        current_nominals    = 0
        costo_unit_promedio = 0.0
        total_amort         = 0
        total_cupones       = 0
        total_dividendos    = 0

        for _, op in ops.iterrows():
            tipo = op['Tipo'].strip()
            if tipo == 'Compra':
                costo_prev          = current_nominals * costo_unit_promedio
                current_nominals   += op['Cantidad']
                costo_unit_promedio = (costo_prev + op['Monto']) / current_nominals
            elif tipo == 'Venta':
                current_nominals -= op['Cantidad']
            else:
                categoria = _clasificar_operacion(tipo)
                if categoria == 'amortizacion':
                    total_amort      += op['Monto']
                elif categoria == 'cupon':
                    total_cupones    += op['Monto']
                elif categoria == 'dividendo':
                    total_dividendos += op['Monto']

        if current_nominals <= 0:
            continue

        costo_posicion = current_nominals * costo_unit_promedio
        current_price  = available.iloc[-1]['Precio']
        valor_actual   = current_nominals * current_price
        ganancia_no_r  = valor_actual - costo_posicion
        ganancia_total = ganancia_no_r + total_amort + total_cupones + total_dividendos

        portfolio_data.append({
            'Activo':                  asset,
            'Nominales':               current_nominals,
            'Precio Actual':           current_price,
            '_Valor Actual':           valor_actual,
            'Costo':                   costo_posicion,
            'Amortizaciones':          total_amort,
            'Cupones':                 total_cupones,
            'Dividendos':              total_dividendos,
            'Ganancias no Realizadas': ganancia_no_r,
            'Ganancia Total':          ganancia_total,
            '_nota':                   nota,
        })

    return pd.DataFrame(portfolio_data)


# ─────────────────────────────────────────────
# Evolución histórica  (sin cambios respecto al original)
# ─────────────────────────────────────────────
def calculate_portfolio_evolution(operaciones, precios, fecha_inicio, fecha_fin):
    """Calcular evolución de la cartera en un rango de fechas."""
    operaciones = operaciones.copy()
    precios = precios.copy()
    operaciones['Fecha'] = pd.to_datetime(operaciones['Fecha'])
    precios['Fecha']     = pd.to_datetime(precios['Fecha'])

    assets = [a for a in operaciones['Activo'].unique() if pd.notna(a)]
    evolution_data = []

    for asset in assets:
        asset_ops = operaciones[operaciones['Activo'] == asset].sort_values('Fecha')

        # C1/C2/C6: Último reset hasta fecha_fin — mismo criterio que Sección 1.
        # Filtra por posición iloc para incluir ops del mismo día post-reset (C2).
        ops_until_fin   = asset_ops[asset_ops['Fecha'] <= pd.to_datetime(fecha_fin)]
        last_reset_date, last_reset_pos = _find_last_reset(ops_until_fin)

        if last_reset_date is None:
            ops_since_reset = ops_until_fin
        else:
            ops_since_reset = ops_until_fin.iloc[last_reset_pos + 1:]

        # Acumulados hasta inicio (ops ESTRICTAMENTE antes de fecha_inicio)
        ops_until_inicio = ops_since_reset[
            ops_since_reset['Fecha'] < pd.to_datetime(fecha_inicio)
        ]
        ops_en_rango = ops_since_reset[
            (ops_since_reset['Fecha'] >= pd.to_datetime(fecha_inicio)) &
            (ops_since_reset['Fecha'] <= pd.to_datetime(fecha_fin))
        ]

        nom_inicio = sales_inicio = divcup_inicio = 0
        for _, op in ops_until_inicio.iterrows():
            tipo = op['Tipo'].strip()
            if tipo == 'Compra':
                nom_inicio   += op['Cantidad']
            elif tipo == 'Venta':
                nom_inicio   -= op['Cantidad']
                sales_inicio += op['Monto']
            elif _clasificar_operacion(tipo):
                divcup_inicio += op['Monto']

        # Omitir activos sin actividad relevante en el período
        if nom_inicio <= 0 and ops_en_rango.empty:
            continue

        # Acumulados en el período
        nom_fin    = nom_inicio
        sales_fin  = sales_inicio
        divcup_fin = divcup_inicio
        compras_en_periodo = 0

        for _, op in ops_en_rango.iterrows():
            tipo = op['Tipo'].strip()
            if tipo == 'Compra':
                nom_fin            += op['Cantidad']
                compras_en_periodo += op['Monto']
            elif tipo == 'Venta':
                nom_fin   -= op['Cantidad']
                sales_fin += op['Monto']
            elif _clasificar_operacion(tipo):
                divcup_fin += op['Monto']

        # Precios inicio / fin (sort garantiza iloc[-1] correcto — M4)
        asset_prices  = precios[precios['Activo'] == asset].sort_values('Fecha')
        avail_inicio  = asset_prices[asset_prices['Fecha'] <= pd.to_datetime(fecha_inicio)]
        avail_fin     = asset_prices[asset_prices['Fecha'] <= pd.to_datetime(fecha_fin)]
        # M3: advertir si faltan precios
        if avail_inicio.empty and nom_inicio > 0:
            st.warning(
                f"⚠️ {asset}: sin precio al {fecha_inicio.strftime('%d/%m/%Y')}. "
                f"Valor al Inicio = $0."
            )
        if avail_fin.empty and nom_fin > 0:
            st.warning(
                f"⚠️ {asset}: sin precio al {fecha_fin.strftime('%d/%m/%Y')}. "
                f"Valor Final = $0."
            )
        precio_inicio = avail_inicio.iloc[-1]['Precio'] if not avail_inicio.empty else 0
        precio_fin    = avail_fin.iloc[-1]['Precio']    if not avail_fin.empty    else 0

        # Filtrar activos con nominales finales negativos (error de datos, igual que Sección 1)
        if nom_fin < 0:
            continue

        valor_inicio       = nom_inicio * precio_inicio if nom_inicio > 0 else 0
        valor_fin          = nom_fin * precio_fin
        div_cup_en_periodo = divcup_fin - divcup_inicio
        ventas_en_periodo  = sales_fin  - sales_inicio
        ganancia_total     = (valor_fin - valor_inicio - compras_en_periodo) + div_cup_en_periodo + ventas_en_periodo

        evolution_data.append({
            'Activo':            asset,
            'Nominales':         nom_fin,
            'Precio Cierre':     precio_fin,   # Me5: es precio al fecha_fin, no "actual"
            'Valor Actual':      valor_fin,
            'Valor al Inicio':   valor_inicio,
            'Compras':           compras_en_periodo,
            'Ventas':            ventas_en_periodo,
            'Amort / Cup / Div': div_cup_en_periodo,
            'Ganancia Total':    ganancia_total,
        })

    return pd.DataFrame(evolution_data)


# ─────────────────────────────────────────────
# Detalle por activo  (sin cambios respecto al original)
# ─────────────────────────────────────────────
def mostrar_analisis_detallado_activo(operaciones, precios, activo, fecha_inicio, fecha_fin):
    """Mostrar análisis detallado de un activo específico."""
    operaciones = operaciones.copy()
    precios = precios.copy()
    operaciones['Fecha'] = pd.to_datetime(operaciones['Fecha'])
    precios['Fecha']     = pd.to_datetime(precios['Fecha'])

    asset_ops = operaciones[operaciones['Activo'] == activo].sort_values('Fecha')

    # C1/C2: Último reset hasta fecha_fin — mismo criterio que Sección 1 y Sección 2.
    # Filtra por posición iloc para incluir ops del mismo día post-reset (C2).
    ops_until_fin_d = asset_ops[asset_ops['Fecha'] <= pd.to_datetime(fecha_fin)]
    last_reset_date, last_reset_pos = _find_last_reset(ops_until_fin_d)

    if last_reset_date is None:
        ops_since_reset = ops_until_fin_d
    else:
        ops_since_reset = ops_until_fin_d.iloc[last_reset_pos + 1:]

    # Nominales al inicio (ops ESTRICTAMENTE antes de fecha_inicio → sin doble conteo)
    nom_inicio = 0
    for _, op in ops_since_reset.iterrows():
        if op['Fecha'] >= pd.to_datetime(fecha_inicio):   # FIXED: >= evita doble conteo
            break
        if op['Tipo'].strip() == 'Compra':
            nom_inicio += op['Cantidad']
        elif op['Tipo'].strip() == 'Venta':
            nom_inicio -= op['Cantidad']

    detalle_data = []

    ap = precios[precios['Activo'] == activo].sort_values('Fecha')

    # M7: solo agregar fila "Valor Inicial" si había posición al inicio del período
    if nom_inicio > 0:
        avail = ap[ap['Fecha'] <= pd.to_datetime(fecha_inicio)]
        precio_inicio = avail.iloc[-1]['Precio'] if not avail.empty else 0
        detalle_data.append({
            'Fecha':     fecha_inicio,
            'Operación': 'Valor Inicial',
            'Nominales': nom_inicio,
            'Precio':    precio_inicio,
            'Valor':     nom_inicio * precio_inicio,
        })

    ops_en_periodo = ops_since_reset[
        (ops_since_reset['Fecha'] >= pd.to_datetime(fecha_inicio)) &
        (ops_since_reset['Fecha'] <= pd.to_datetime(fecha_fin))
    ]

    nom_fin = nom_inicio
    for _, op in ops_en_periodo.iterrows():
        tipo = op['Tipo'].strip()
        if tipo == 'Compra':
            nom_fin += op['Cantidad']
        elif tipo == 'Venta':
            nom_fin -= op['Cantidad']
        detalle_data.append({
            'Fecha':     op['Fecha'],
            'Operación': op['Tipo'],
            'Nominales': op['Cantidad'],
            'Precio':    op['Precio'],
            'Valor':     op['Monto'],
        })

    # Me7: fila de cierre siempre presente (muestra $0 si la posición fue cerrada)
    if nom_fin > 0:
        avail_fin  = ap[ap['Fecha'] <= pd.to_datetime(fecha_fin)]
        precio_fin = avail_fin.iloc[-1]['Precio'] if not avail_fin.empty else 0
        detalle_data.append({
            'Fecha':     fecha_fin,
            'Operación': 'Valor Final',
            'Nominales': nom_fin,
            'Precio':    precio_fin,
            'Valor':     nom_fin * precio_fin,
        })
    elif detalle_data:   # hubo operaciones pero la posición quedó en 0
        detalle_data.append({
            'Fecha':     fecha_fin,
            'Operación': 'Posición cerrada',
            'Nominales': 0,
            'Precio':    None,
            'Valor':     0,
        })

    detalle_df = pd.DataFrame(detalle_data)

    if not detalle_df.empty:
        detalle_df['Fecha'] = pd.to_datetime(detalle_df['Fecha']).dt.strftime('%d/%m/%Y')
        display = detalle_df.copy()
        display['Nominales'] = display['Nominales'].apply(
            lambda x: f"{x:,.0f}" if pd.notna(x) and x != 0 else ""
        )
        display['Precio'] = display['Precio'].apply(
            lambda x: f"${x:,.2f}" if pd.notna(x) and x != 0 else ""
        )
        display['Valor'] = display['Valor'].apply(
            lambda x: f"${x:,.2f}" if pd.notna(x) and x != 0 else ""
        )

        st.markdown(f"**Operaciones detalladas para {activo}:**")
        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Fecha":     st.column_config.TextColumn("Fecha",     width="small"),
                "Operación": st.column_config.TextColumn("Operación", width="medium"),
                "Nominales": st.column_config.TextColumn("Nominales", width="small"),
                "Precio":    st.column_config.TextColumn("Precio",    width="small"),
                "Valor":     st.column_config.TextColumn("Valor",     width="small"),
            }
        )

        csv_detalle = detalle_df.to_csv(index=False)
        st.download_button(
            label=f"📥 Descargar CSV - {activo}",
            data=csv_detalle,
            file_name=f"detalle_{activo}_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info(f"No hay operaciones para {activo} en el período seleccionado.")


# ─────────────────────────────────────────────
# Helpers de formato
# ─────────────────────────────────────────────
def _fmt_money(x):
    return f"${x:,.2f}" if pd.notna(x) else ""


def _fmt_number(x):
    return f"{x:,.0f}" if pd.notna(x) else ""


def _metric(label, value_str, sub_str=None):
    st.markdown(
        f'<div style="text-align:center;font-size:0.8em;">{label}</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div style="text-align:center;font-size:1.6em;font-weight:bold;">{value_str}</div>',
        unsafe_allow_html=True
    )
    if sub_str:
        # M2: rojo si el subtítulo es negativo, verde si es positivo
        color = '#ff4444' if str(sub_str).strip().startswith('-') else '#00C851'
        st.markdown(
            f'<div style="text-align:center;font-size:1.1em;color:{color};">{sub_str}</div>',
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():

    # ── Sidebar ──────────────────────────────
    with st.sidebar:
        st.header("Configuración")

        uploaded_file = st.file_uploader(
            "Cargar archivo Excel diferente",
            type=['xlsx', 'xls'],
            help="Opcional: cargar un Excel diferente a operaciones.xlsx"
        )

        fecha_actual = st.date_input(
            "Fecha actual",
            value=datetime.now().date(),
            help="Fecha para calcular la composición actual"
        )

        st.markdown("---")
        st.subheader("Análisis de Evolución")

        fecha_inicio = st.date_input(
            "Fecha de Inicio",
            value=datetime.now().date() - timedelta(days=365),
            help="Fecha de inicio para el análisis de evolución"
        )

        fecha_fin = st.date_input(
            "Fecha de Fin",
            value=datetime.now().date(),
            help="Fecha de fin para el análisis de evolución"
        )

    # ── Archivo a usar ────────────────────────
    if uploaded_file is not None:
        # M5: nombre único por sesión para evitar colisiones entre usuarios
        import uuid
        if 'upload_id' not in st.session_state:
            st.session_state.upload_id = uuid.uuid4().hex[:12]
        filename = f"temp_{st.session_state.upload_id}.xlsx"
        with open(filename, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"📁 Archivo cargado: {uploaded_file.name}")
    else:
        filename = 'operaciones.xlsx'

    # Me1: validar rango de fechas de evolución
    if fecha_inicio > fecha_fin:
        st.error("⚠️ La fecha de inicio no puede ser posterior a la fecha de fin.")
        return

    # ── Carga de datos ────────────────────────
    operaciones, precios = load_data(filename)

    if operaciones is None or precios is None:
        st.error(
            "Error al cargar los datos. "
            "Verifica que el archivo 'operaciones.xlsx' esté en la carpeta del proyecto."
        )
        return

    # ══════════════════════════════════════════
    # SECCIÓN 1 – COMPOSICIÓN ACTUAL
    # ══════════════════════════════════════════
    portfolio_df = calculate_current_portfolio(operaciones, precios, fecha_actual)

    st.header("Composición Actual de la Cartera")
    st.markdown(f"*Calculado al {fecha_actual.strftime('%d/%m/%Y')}*")

    if portfolio_df.empty:
        st.warning("No hay activos con nominales positivos en la fecha seleccionada.")
    else:
        # ── Métricas resumen ──────────────────
        total_valor_mercado  = portfolio_df['_Valor Actual'].sum()
        total_costo          = portfolio_df['Costo'].sum()
        total_amort          = portfolio_df['Amortizaciones'].sum()
        total_cup            = portfolio_df['Cupones'].sum()
        total_div            = portfolio_df['Dividendos'].sum()
        total_ganancia_r     = total_amort + total_cup + total_div
        total_ganancia_no_r  = portfolio_df['Ganancias no Realizadas'].sum()
        pct_no_r             = (total_ganancia_no_r / total_costo * 100) if total_costo > 0 else 0

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            _metric("Total Activos",       str(len(portfolio_df)))
        with col2:
            _metric("Valor de Mercado",    f"${total_valor_mercado:,.0f}")
        with col3:
            _metric("Costo Total",         f"${total_costo:,.0f}")
        with col4:
            _metric("Ganancias Realizadas",f"${total_ganancia_r:,.0f}")
        with col5:
            _metric(
                "Ganancias no Realizadas",
                f"${total_ganancia_no_r:,.0f}",
                f"{pct_no_r:.1f}%"
            )
        with col6:
            _metric("Amort / Cup / Div",
                    f"${total_amort:,.0f} / ${total_cup:,.0f} / ${total_div:,.0f}")

        # ── Tabla ────────────────────────────
        # Columnas visibles (excluimos la interna _Valor Actual)
        cols_display = [
            'Activo', 'Nominales', 'Precio Actual', 'Valor Actual', 'Costo',
            'Amortizaciones', 'Cupones', 'Dividendos', 'Ganancia Total'
        ]

        display_df = portfolio_df.rename(columns={'_Valor Actual': 'Valor Actual'})[cols_display].copy()
        display_df['Nominales']      = display_df['Nominales'].apply(_fmt_number)
        display_df['Precio Actual']  = display_df['Precio Actual'].apply(_fmt_money)
        display_df['Valor Actual']   = display_df['Valor Actual'].apply(_fmt_money)
        display_df['Costo']          = display_df['Costo'].apply(_fmt_money)
        display_df['Amortizaciones'] = display_df['Amortizaciones'].apply(_fmt_money)
        display_df['Cupones']        = display_df['Cupones'].apply(_fmt_money)
        display_df['Dividendos']     = display_df['Dividendos'].apply(_fmt_money)
        display_df['Ganancia Total'] = display_df['Ganancia Total'].apply(_fmt_money)

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Activo": st.column_config.TextColumn("Activo", width="medium"),
            }
        )

        # ── Notas sobre compras estimadas (C4) ───────────────────────────
        if '_nota' in portfolio_df.columns:
            for nota in portfolio_df[portfolio_df['_nota'] != '']['_nota']:
                st.caption(nota)

        # ── C3: aclaración sobre flujos pre-reset ────────────────────────
        st.caption(
            "ℹ️ Amortizaciones, Cupones y Dividendos corresponden únicamente a los flujos "
            "cobrados desde la apertura de la posición actual. Los flujos de posiciones "
            "anteriores del mismo activo (antes del último reset) se reflejan en la Sección 2."
        )

        # ── Descarga ─────────────────────────
        csv = portfolio_df.rename(columns={'_Valor Actual': 'Valor Actual'})[cols_display].to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"composicion_cartera_{fecha_actual.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

    # ══════════════════════════════════════════
    # SECCIÓN 2 – EVOLUCIÓN HISTÓRICA  (sin cambios)
    # ══════════════════════════════════════════
    st.header("Análisis de la Evolución de la Cartera")
    st.markdown(f"*Análisis del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}*")

    evolution_df = calculate_portfolio_evolution(operaciones, precios, fecha_inicio, fecha_fin)

    if evolution_df.empty:
        st.warning("No hay datos de evolución para el rango de fechas seleccionado.")
    else:
        # Métricas
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            # Me4: distinguir activos abiertos de posiciones cerradas en el período
            n_abiertos = int((evolution_df['Nominales'] > 0).sum())
            n_cerrados = int((evolution_df['Nominales'] <= 0).sum())
            label_act  = str(n_abiertos) if n_cerrados == 0 else (
                f"{n_abiertos} ({n_cerrados} cerrado{'s' if n_cerrados > 1 else ''})"
            )
            _metric("Total Activos", label_act)
        with col2:
            _metric("Valor Total",     f"${evolution_df['Valor Actual'].sum():,.0f}")
        with col3:
            _metric("Valor al Inicio", f"${evolution_df['Valor al Inicio'].sum():,.0f}")
        with col4:
            _metric("Compras en Período", f"${evolution_df['Compras'].sum():,.0f}")
        with col5:
            flujos = evolution_df['Ventas'].sum() + evolution_df['Amort / Cup / Div'].sum()
            _metric("Ventas + Flujos", f"${flujos:,.0f}")
        with col6:
            total_gain  = evolution_df['Ganancia Total'].sum()
            base        = evolution_df['Valor al Inicio'].sum() + evolution_df['Compras'].sum()
            pct_evo     = (total_gain / base * 100) if base > 0 else 0
            _metric("Ganancia Total",  f"${total_gain:,.0f}", f"{pct_evo:.1f}%")

        # Tabla
        evo_display = evolution_df.copy()
        for col in ['Nominales']:
            evo_display[col] = evo_display[col].apply(_fmt_number)
        for col in ['Precio Cierre', 'Valor Actual', 'Valor al Inicio',
                    'Compras', 'Ventas', 'Amort / Cup / Div', 'Ganancia Total']:
            evo_display[col] = evo_display[col].apply(_fmt_money)

        st.dataframe(
            evo_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Activo": st.column_config.TextColumn("Activo", width="medium"),
            }
        )

        csv_evo = evolution_df.to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV Evolución",
            data=csv_evo,
            file_name=f"evolucion_cartera_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

    # ── Detalle por activo ───────────────────
    if not evolution_df.empty:
        st.markdown("---")
        st.subheader("📋 Análisis Detallado de Evolución por Activo")

        activos_disponibles = ["Seleccionar"] + evolution_df['Activo'].tolist()
        activo_sel = st.selectbox(
            "Seleccionar activo para análisis detallado:",
            activos_disponibles,
            index=0,
            help="Selecciona un activo para ver todas las operaciones consideradas en el período"
        )

        if activo_sel and activo_sel != "Seleccionar":
            mostrar_analisis_detallado_activo(
                operaciones, precios, activo_sel, fecha_inicio, fecha_fin
            )


if __name__ == "__main__":
    main()
