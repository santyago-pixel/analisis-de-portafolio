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

warnings.filterwarnings('ignore')

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

        operaciones_mapped['Tipo']   = operaciones_mapped['Tipo'].str.strip()
        operaciones_mapped['Activo'] = operaciones_mapped['Activo'].str.strip()
        operaciones_mapped = operaciones_mapped.dropna(
            subset=['Fecha', 'Tipo', 'Activo', 'Monto']
        )

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


def _find_last_reset(asset_ops_until_date):
    """
    Recorre las operaciones y devuelve la fecha del último reset a cero
    (cuando los nominales pasan de positivo a ≤ 0).
    Retorna None si nunca ocurrió un reset.
    """
    running = 0
    last_reset_date = None
    for _, op in asset_ops_until_date.iterrows():
        prev = running
        if op['Tipo'].strip() == 'Compra':
            running += op['Cantidad']
        elif op['Tipo'].strip() == 'Venta':
            running -= op['Cantidad']
        if prev > 0 and running <= 0:
            last_reset_date = op['Fecha']
            running = 0
    return last_reset_date


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

        # Último reset a cero
        last_reset_date = _find_last_reset(asset_ops_until)

        # Operaciones desde el reset
        if last_reset_date is None:
            ops = asset_ops_until
        else:
            ops = asset_ops_until[asset_ops_until['Fecha'] > last_reset_date]

        # ── Costo Promedio Ponderado ──────────────────────────────────────
        # costo_unit_promedio = costo total acumulado / nominales acumulados
        # En Compra: se recalcula ponderando el lote nuevo con la posición previa
        # En Venta:  los nominales bajan pero el costo unitario no cambia
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
                # costo_unit_promedio permanece igual en ventas parciales
            else:
                categoria = _clasificar_operacion(tipo)
                if categoria == 'amortizacion':
                    total_amort      += op['Monto']
                elif categoria == 'cupon':
                    total_cupones    += op['Monto']
                elif categoria == 'dividendo':
                    total_dividendos += op['Monto']

        # Solo activos con nominales positivos
        if current_nominals <= 0:
            continue

        # Costo de la posición actual = nominales × costo unitario promedio
        costo_posicion = current_nominals * costo_unit_promedio

        # Precio más reciente disponible hasta fecha_actual
        asset_prices = precios[precios['Activo'] == asset]
        available    = asset_prices[asset_prices['Fecha'] <= pd.to_datetime(fecha_actual)]
        if available.empty:
            continue

        current_price = available.iloc[-1]['Precio']
        valor_actual  = current_nominals * current_price
        ganancia_no_r = valor_actual - costo_posicion

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

        # PASO 1: ¿Tuvo nominales positivos en el período?
        had_positive = False
        temp = 0
        for _, op in asset_ops.iterrows():
            if op['Fecha'] > pd.to_datetime(fecha_fin):
                break
            if op['Tipo'].strip() == 'Compra':
                temp += op['Cantidad']
            elif op['Tipo'].strip() == 'Venta':
                temp -= op['Cantidad']
            if (op['Fecha'] >= pd.to_datetime(fecha_inicio) and
                    op['Fecha'] <= pd.to_datetime(fecha_fin) and
                    temp > 0):
                had_positive = True
                break

        if not had_positive:
            temp_inicio = 0
            for _, op in asset_ops.iterrows():
                if op['Fecha'] >= pd.to_datetime(fecha_inicio):
                    break
                if op['Tipo'].strip() == 'Compra':
                    temp_inicio += op['Cantidad']
                elif op['Tipo'].strip() == 'Venta':
                    temp_inicio -= op['Cantidad']
            if temp_inicio > 0:
                had_positive = True

        if not had_positive:
            continue

        # PASO 2: Último reset ANTES o EN el inicio del período
        running = 0
        last_reset_date = None
        for _, op in asset_ops.iterrows():
            if op['Fecha'] > pd.to_datetime(fecha_inicio):
                break
            prev = running
            if op['Tipo'].strip() == 'Compra':
                running += op['Cantidad']
            elif op['Tipo'].strip() == 'Venta':
                running -= op['Cantidad']
            if prev > 0 and running <= 0:
                last_reset_date = op['Fecha']
                running = 0

        # PASO 3: Operaciones desde reset hasta fecha_fin
        if last_reset_date is None:
            ops_since_reset = asset_ops[asset_ops['Fecha'] <= pd.to_datetime(fecha_fin)]
        else:
            ops_since_reset = asset_ops[
                (asset_ops['Fecha'] > last_reset_date) &
                (asset_ops['Fecha'] <= pd.to_datetime(fecha_fin))
            ]

        # Acumulados hasta inicio  (en base a precios de mercado, no costo)
        nom_inicio = sales_inicio = divcup_inicio = 0
        ops_until_inicio = ops_since_reset[ops_since_reset['Fecha'] <= pd.to_datetime(fecha_inicio)]

        for _, op in ops_until_inicio.iterrows():
            tipo = op['Tipo'].strip()
            if tipo == 'Compra':
                nom_inicio   += op['Cantidad']
            elif tipo == 'Venta':
                nom_inicio   -= op['Cantidad']
                sales_inicio += op['Monto']
            elif _clasificar_operacion(tipo):
                divcup_inicio += op['Monto']

        # Acumulados hasta fin
        nom_fin    = nom_inicio
        sales_fin  = sales_inicio
        divcup_fin = divcup_inicio

        ops_en_rango = ops_since_reset[
            (ops_since_reset['Fecha'] >= pd.to_datetime(fecha_inicio)) &
            (ops_since_reset['Fecha'] <= pd.to_datetime(fecha_fin))
        ]

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

        # Precios inicio / fin
        asset_prices = precios[precios['Activo'] == asset]
        avail_inicio  = asset_prices[asset_prices['Fecha'] <= pd.to_datetime(fecha_inicio)]
        avail_fin     = asset_prices[asset_prices['Fecha'] <= pd.to_datetime(fecha_fin)]
        precio_inicio = avail_inicio.iloc[-1]['Precio'] if not avail_inicio.empty else 0
        precio_fin    = avail_fin.iloc[-1]['Precio']    if not avail_fin.empty    else 0

        # Valor al inicio del período
        valor_inicio = 0
        if nom_inicio > 0:
            valor_inicio += nom_inicio * precio_inicio
        valor_inicio += compras_en_periodo

        valor_fin          = nom_fin * precio_fin
        div_cup_en_periodo = divcup_fin - divcup_inicio
        ventas_en_periodo  = sales_fin  - sales_inicio
        ganancia_total     = (valor_fin - valor_inicio) + div_cup_en_periodo + ventas_en_periodo

        evolution_data.append({
            'Activo':         asset,
            'Nominales':      nom_fin,
            'Precio Actual':  precio_fin,
            'Valor Actual':   valor_fin,
            'Valor al Inicio': valor_inicio,
            'Ventas':         ventas_en_periodo,
            'Div - Cupones':  div_cup_en_periodo,
            'Ganancia Total': ganancia_total,
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

    # Último reset antes o en el inicio
    running = 0
    last_reset_date = None
    for _, op in asset_ops.iterrows():
        if op['Fecha'] > pd.to_datetime(fecha_inicio):
            break
        prev = running
        if op['Tipo'].strip() == 'Compra':
            running += op['Cantidad']
        elif op['Tipo'].strip() == 'Venta':
            running -= op['Cantidad']
        if prev > 0 and running <= 0:
            last_reset_date = op['Fecha']
            running = 0

    if last_reset_date is None:
        ops_since_reset = asset_ops[asset_ops['Fecha'] <= pd.to_datetime(fecha_fin)]
    else:
        ops_since_reset = asset_ops[
            (asset_ops['Fecha'] > last_reset_date) &
            (asset_ops['Fecha'] <= pd.to_datetime(fecha_fin))
        ]

    # Nominales al inicio
    nom_inicio = 0
    for _, op in ops_since_reset.iterrows():
        if op['Fecha'] > pd.to_datetime(fecha_inicio):
            break
        if op['Tipo'].strip() == 'Compra':
            nom_inicio += op['Cantidad']
        elif op['Tipo'].strip() == 'Venta':
            nom_inicio -= op['Cantidad']

    detalle_data = []

    if nom_inicio > 0:
        ap = precios[precios['Activo'] == activo]
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
    for _, op in ops_en_periodo.iterrows():
        detalle_data.append({
            'Fecha':     op['Fecha'],
            'Operación': op['Tipo'],
            'Nominales': op['Cantidad'],
            'Precio':    op['Precio'],
            'Valor':     op['Monto'],
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
        st.markdown(
            f'<div style="text-align:center;font-size:1.1em;color:#00C851;">{sub_str}</div>',
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
        with open("temp_file.xlsx", "wb") as f:
            f.write(uploaded_file.getbuffer())
        filename = "temp_file.xlsx"
        st.success(f"📁 Archivo cargado: {uploaded_file.name}")
    else:
        filename = 'operaciones.xlsx'

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
            'Activo', 'Nominales', 'Precio Actual', 'Costo',
            'Amortizaciones', 'Cupones', 'Dividendos', 'Ganancias no Realizadas'
        ]

        display_df = portfolio_df[cols_display].copy()
        display_df['Nominales']              = display_df['Nominales'].apply(_fmt_number)
        display_df['Precio Actual']          = display_df['Precio Actual'].apply(_fmt_money)
        display_df['Costo']                  = display_df['Costo'].apply(_fmt_money)
        display_df['Amortizaciones']         = display_df['Amortizaciones'].apply(_fmt_money)
        display_df['Cupones']                = display_df['Cupones'].apply(_fmt_money)
        display_df['Dividendos']             = display_df['Dividendos'].apply(_fmt_money)
        display_df['Ganancias no Realizadas'] = display_df['Ganancias no Realizadas'].apply(_fmt_money)

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Activo": st.column_config.TextColumn("Activo", width="medium"),
            }
        )

        # ── Descarga ─────────────────────────
        csv = portfolio_df[cols_display].to_csv(index=False)
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
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            _metric("Total Activos",   str(len(evolution_df)))
        with col2:
            _metric("Valor Total",     f"${evolution_df['Valor Actual'].sum():,.0f}")
        with col3:
            _metric("Valor al Inicio", f"${evolution_df['Valor al Inicio'].sum():,.0f}")
        with col4:
            flujos = evolution_df['Ventas'].sum() + evolution_df['Div - Cupones'].sum()
            _metric("Flujos Netos",    f"${flujos:,.0f}")
        with col5:
            total_gain  = evolution_df['Ganancia Total'].sum()
            val_inicio  = evolution_df['Valor al Inicio'].sum()
            pct_evo     = (total_gain / val_inicio * 100) if val_inicio > 0 else 0
            _metric("Ganancia Total",  f"${total_gain:,.0f}", f"{pct_evo:.1f}%")

        # Tabla
        evo_display = evolution_df.copy()
        for col in ['Nominales']:
            evo_display[col] = evo_display[col].apply(_fmt_number)
        for col in ['Precio Actual', 'Valor Actual', 'Valor al Inicio',
                    'Ventas', 'Div - Cupones', 'Ganancia Total']:
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
