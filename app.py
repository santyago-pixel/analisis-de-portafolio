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
import plotly.graph_objects as go
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
    initial_sidebar_state="collapsed"
)

# ── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>

/* ══════════════════════════════════════════════
   TIPOGRAFÍA  —  Inter (Google Fonts)
══════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], .stApp, button, input, select, textarea {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ══════════════════════════════════════════════
   FONDO Y CONTENEDOR PRINCIPAL
══════════════════════════════════════════════ */
/* Fondo: blanco en los márgenes laterales, gris en la franja central de 1200px */
.stApp {
    background: linear-gradient(
        to right,
        #FFFFFF 0%,
        #FFFFFF calc(50% - 600px),
        #F0F2F6 calc(50% - 600px),
        #F0F2F6 calc(50% + 600px),
        #FFFFFF calc(50% + 600px),
        #FFFFFF 100%
    ) !important;
    min-height: 100vh !important;
}
/* Ocultar sidebar completamente */
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
/* Centrar contenido principal */
.main .block-container,
[data-testid="block-container"],
div.block-container {
    max-width: 1200px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding-top: 1.5rem !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    background-color: transparent !important;
}
section[data-testid="stMain"],
.main {
    background-color: transparent !important;
}

/* ══════════════════════════════════════════════
   CHROME DE STREAMLIT  —  ocultar / reestilizar
══════════════════════════════════════════════ */
#MainMenu          { visibility: hidden; }
footer             { visibility: hidden; }
[data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stHeader"] {
    background-color: #1B2333 !important;
    border-bottom: 3px solid #1A4B9B !important;
}

/* ══════════════════════════════════════════════
   SIDEBAR
══════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E5E7EB !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #1B2333 !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] label {
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    color: #374151 !important;
}
[data-testid="stSidebar"] hr {
    border-color: #E5E7EB !important;
    margin: 0.8rem 0 !important;
}

/* Date inputs */
.stDateInput input,
[data-testid="stDateInputField"] input {
    font-size: 0.95rem !important;
}

/* ══════════════════════════════════════════════
   TÍTULOS NATIVOS DE STREAMLIT
   (usados solo como fallback; normalmente
    reemplazados por _section_header)
══════════════════════════════════════════════ */
h1 { font-size: 1.5rem !important; font-weight: 700 !important; color: #1B2333 !important; }
h2 { font-size: 1.2rem !important; font-weight: 600 !important; color: #1B2333 !important; }
h3 { font-size: 1.0rem !important; font-weight: 600 !important; color: #1B2333 !important; }

/* ══════════════════════════════════════════════
   DATAFRAMES / TABLAS
══════════════════════════════════════════════ */
[data-testid="stDataFrame"] > div {
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 1px solid #E5E7EB !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
    background: #FFFFFF !important;
}

/* ══════════════════════════════════════════════
   BOTONES DE DESCARGA
══════════════════════════════════════════════ */
[data-testid="stDownloadButton"] button {
    background-color: transparent !important;
    color: #1A4B9B !important;
    border: 1.5px solid #1A4B9B !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    padding: 0.3rem 0.9rem !important;
    transition: background 0.15s ease, color 0.15s ease !important;
}
[data-testid="stDownloadButton"] button:hover {
    background-color: #1A4B9B !important;
    color: #FFFFFF !important;
}

/* ══════════════════════════════════════════════
   FILE UPLOADER
══════════════════════════════════════════════ */
[data-testid="stFileUploader"] {
    border-radius: 8px !important;
}

/* ══════════════════════════════════════════════
   SELECTBOX  /  DATE INPUT
══════════════════════════════════════════════ */
[data-testid="stSelectbox"] > div > div,
[data-testid="stDateInput"]  > div > div {
    border-radius: 6px !important;
    border-color: #D1D5DB !important;
    font-size: 0.88rem !important;
}

/* ══════════════════════════════════════════════
   RADIO (toggle de moneda)
══════════════════════════════════════════════ */
[data-testid="stRadio"] label span {
    font-size: 0.88rem !important;
    font-weight: 500 !important;
}

/* ══════════════════════════════════════════════
   ALERTAS  (warning / error / info / success)
══════════════════════════════════════════════ */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    border-left-width: 4px !important;
    font-size: 0.85rem !important;
}

/* ══════════════════════════════════════════════
   CAPTION / NOTAS AL PIE
══════════════════════════════════════════════ */
[data-testid="stCaptionContainer"] p {
    color: #9CA3AF !important;
    font-size: 0.78rem !important;
}

/* ══════════════════════════════════════════════
   DIVIDER NATIVO
══════════════════════════════════════════════ */
hr {
    border-color: #E5E7EB !important;
    margin: 1.2rem 0 !important;
}

</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Carga de datos
# ─────────────────────────────────────────────
def load_data(filename='operaciones.xlsx'):
    """Cargar datos desde operaciones.xlsx o archivo especificado.

    Retorna (operaciones_mapped, precios_long, fx_rates, live_prices, live_fx) donde:
      - operaciones_mapped: DataFrame con columnas Fecha, Tipo, Activo,
        Cantidad, Precio, Monto (USD), Precio ARS, Monto ARS.
      - precios_long: precios históricos de bonos en USD en formato largo (sin fila
        "Precio Actual" y sin columna ARS).
      - fx_rates: DataFrame con columnas Fecha y ARS (tipo de cambio histórico USD/ARS).
      - live_prices: dict {activo: precio_usd} con precios en vivo de la primera fila.
      - live_fx: float con el tipo de cambio en vivo (ARS/USD) de la primera fila,
        o None si no está disponible.
    """
    try:
        # ── Hoja Operaciones ─────────────────────────────────────────────
        operaciones = pd.read_excel(filename, sheet_name='Operaciones')

        operaciones_mapped = pd.DataFrame()
        operaciones_mapped['Fecha']    = operaciones['Fecha']
        operaciones_mapped['Tipo']     = operaciones['Operacion']
        operaciones_mapped['Activo']   = operaciones['Activo']
        operaciones_mapped['Cantidad'] = operaciones['Nominales']
        operaciones_mapped['Precio']   = operaciones['Precio']

        # Columna de monto en USD: puede llamarse 'Valor USD' o 'Valor'
        if 'Valor USD' in operaciones.columns:
            operaciones_mapped['Monto'] = operaciones['Valor USD']
        elif 'Valor' in operaciones.columns:
            operaciones_mapped['Monto'] = operaciones['Valor']
        else:
            st.error("No se encontró columna de Valor/Valor USD en la hoja Operaciones.")
            return None, None, None

        # Columnas ARS (pueden no existir en archivos más antiguos)
        operaciones_mapped['Precio ARS'] = (
            operaciones['Precio ARS'] if 'Precio ARS' in operaciones.columns else np.nan
        )
        operaciones_mapped['Monto ARS'] = (
            operaciones['Valor ARS'] if 'Valor ARS' in operaciones.columns else np.nan
        )

        # Columnas de cash (pasan tal cual si existen)
        for src, dst in [('Deposito cash', 'Deposito cash'),
                         ('Retiro Cash',   'Retiro Cash'),
                         ('Invertido',     'Invertido')]:
            operaciones_mapped[dst] = operaciones[src] if src in operaciones.columns else np.nan

        # Me2: normalizar capitalización para que 'compra', 'VENTA', etc. funcionen
        operaciones_mapped['Tipo']   = operaciones_mapped['Tipo'].str.strip().str.title()
        operaciones_mapped['Activo'] = operaciones_mapped['Activo'].str.strip()
        # Mantener filas de trading (Tipo+Activo+Monto completos) Y filas de cash puro
        # (depósitos/retiros sin Activo, que tienen Invertido). Las filas de cash son
        # ignoradas por el código de portfolio (filtra por Activo específico).
        es_trading  = operaciones_mapped[['Fecha', 'Tipo', 'Activo', 'Monto']].notna().all(axis=1)
        es_cash     = operaciones_mapped['Fecha'].notna() & operaciones_mapped['Invertido'].notna()
        operaciones_mapped = operaciones_mapped[es_trading | es_cash].reset_index(drop=True)

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

        # ── Hoja Precios ─────────────────────────────────────────────────
        precios = pd.read_excel(filename, sheet_name='Precios')
        fecha_col = precios.columns[0]
        precios = precios.rename(columns={fecha_col: 'Fecha'})

        # ── Extraer fila "Precio Actual" (primera fila = precios en vivo) ──
        # La primera fila tiene Fecha="Precio Actual" en lugar de una fecha real.
        # Se separa antes de convertir Fecha a datetime para evitar errores de parseo.
        live_prices = {}
        live_fx     = None
        mask_live   = precios['Fecha'].astype(str).str.strip().str.lower() == 'precio actual'
        if mask_live.any():
            live_row = precios[mask_live].iloc[0]
            for col in precios.columns:
                if col == 'Fecha':
                    continue
                val = live_row[col]
                if col == 'ARS':
                    if pd.notna(val):
                        live_fx = float(val)
                elif pd.notna(val):
                    live_prices[str(col).strip()] = float(val)
            # Remover fila de precios en vivo del DataFrame histórico
            precios = precios[~mask_live].copy()

        precios['Fecha'] = pd.to_datetime(precios['Fecha'])

        # Extraer tipo de cambio ARS ANTES del melt para que no aparezca como bono
        if 'ARS' in precios.columns:
            fx_rates = (
                precios[['Fecha', 'ARS']]
                .dropna(subset=['ARS'])
                .sort_values('Fecha')
                .reset_index(drop=True)
            )
            precios_para_melt = precios.drop(columns=['ARS'])
        else:
            fx_rates = pd.DataFrame(columns=['Fecha', 'ARS'])
            precios_para_melt = precios

        precios_long = precios_para_melt.melt(
            id_vars=['Fecha'],
            var_name='Activo',
            value_name='Precio'
        ).dropna()

        return operaciones_mapped, precios_long, fx_rates, live_prices, live_fx

    except FileNotFoundError:
        st.error(f"No se encontró el archivo '{filename}' en la carpeta del proyecto.")
        return None, None, None, {}, None
    except Exception as e:
        st.error(f"Error al cargar el archivo: {str(e)}")
        return None, None, None, {}, None


# ─────────────────────────────────────────────
# Helpers de moneda
# ─────────────────────────────────────────────
def _get_fx(fx_rates, fecha):
    """Devuelve el último tipo de cambio ARS/USD disponible hasta `fecha`.

    Usa la cotización de cierre del día (end-of-day), que es el estándar
    para valuar posiciones en pesos. Para operaciones se usa el TC efectivo
    que ya está capturado en las columnas Precio ARS / Monto ARS del Excel.
    """
    if fx_rates is None or fx_rates.empty:
        return 1.0
    avail = fx_rates[fx_rates['Fecha'] <= pd.to_datetime(fecha)]
    return float(avail.iloc[-1]['ARS']) if not avail.empty else 1.0


def _get_monto(op, moneda, fx_rates):
    """Devuelve el monto de una operación en la moneda seleccionada.

    En ARS: usa Monto ARS (TC efectivo al momento de la operación).
    Fallback: si Monto ARS es NaN, convierte Monto USD × TC de cierre del día.
    """
    if moneda == 'ARS':
        monto_ars = op.get('Monto ARS', np.nan)
        if pd.notna(monto_ars) and monto_ars != 0:
            return float(monto_ars)
        # Fallback: TC de cierre como aproximación
        fx = _get_fx(fx_rates, op['Fecha'])
        return float(op['Monto']) * fx
    return float(op['Monto'])


def _get_precio_op(op, moneda, fx_rates):
    """Devuelve el precio de una operación en la moneda seleccionada."""
    if moneda == 'ARS':
        precio_ars = op.get('Precio ARS', np.nan)
        if pd.notna(precio_ars) and precio_ars != 0:
            return float(precio_ars)
        fx = _get_fx(fx_rates, op['Fecha'])
        return float(op['Precio']) * fx
    return float(op['Precio'])


def _get_price_at_date(asset_prices, fecha, moneda, fx_rates):
    """Precio histórico de mercado de un activo a una fecha dada.

    Busca el último precio disponible ≤ fecha en el histórico.
    En ARS: precio_USD × TC de cierre del día.
    """
    avail = asset_prices[asset_prices['Fecha'] <= pd.to_datetime(fecha)]
    if avail.empty:
        return 0.0
    price_usd = float(avail.iloc[-1]['Precio'])
    if moneda == 'ARS' and fx_rates is not None:
        fx = _get_fx(fx_rates, fecha)
        return price_usd * fx
    return price_usd


def _get_current_price(asset, asset_prices, moneda, fx_rates,
                       live_prices=None, live_fx=None):
    """Precio actual de un activo: usa el precio en vivo si está disponible.

    Para la valuación de posiciones corrientes (Sección 1 y Valor Actual de
    Sección 2) se usa la primera fila del Excel ('Precio Actual'), que refleja
    la cotización en tiempo real. Si el activo no está en live_prices, cae back
    al último precio histórico disponible.

    En ARS: precio_USD × TC en vivo (live_fx) si está disponible,
            o TC histórico más reciente como alternativa.
    """
    if live_prices and asset in live_prices:
        price_usd = live_prices[asset]
        if moneda == 'ARS':
            fx = live_fx if live_fx is not None else _get_fx(fx_rates, pd.Timestamp.now())
            return price_usd * fx
        return price_usd
    # Fallback: último precio histórico disponible
    if asset_prices.empty:
        return 0.0
    price_usd = float(asset_prices.iloc[-1]['Precio'])
    if moneda == 'ARS':
        fx = live_fx if live_fx is not None else _get_fx(fx_rates, asset_prices.iloc[-1]['Fecha'])
        return price_usd * fx
    return price_usd


def _get_end_price(asset, asset_prices, fecha_fin, moneda, fx_rates,
                   live_prices=None, live_fx=None):
    """Precio al cierre del período.

    Para rangos históricos usa el último precio disponible <= fecha_fin.
    Si fecha_fin es hoy y existe precio en vivo, usa ese mark actual.
    """
    fecha_fin_ts = pd.to_datetime(fecha_fin).normalize()
    today_ts = pd.Timestamp.today().normalize()
    if fecha_fin_ts == today_ts:
        return _get_current_price(asset, asset_prices, moneda, fx_rates,
                                  live_prices, live_fx)
    return _get_price_at_date(asset_prices, fecha_fin, moneda, fx_rates)


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
def calculate_current_portfolio(operaciones, precios, fecha_actual,
                                moneda='USD', fx_rates=None,
                                live_prices=None, live_fx=None):
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

        # ── Precio más reciente ──────────────────────────────────────────
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
        nota = ''
        buys_q  = ops[ops['Tipo'].str.strip() == 'Compra']['Cantidad'].sum()
        sells_q = ops[ops['Tipo'].str.strip() == 'Venta']['Cantidad'].sum()
        buys_q  = buys_q  if not pd.isna(buys_q)  else 0
        sells_q = sells_q if not pd.isna(sells_q) else 0
        deficit = sells_q - buys_q
        if deficit > 0:
            oldest_row   = asset_prices.iloc[0]
            oldest_price = float(oldest_row['Precio'])
            oldest_date  = oldest_row['Fecha']
            oldest_monto = deficit * oldest_price
            # En ARS: el monto sintético usa el TC más antiguo disponible
            oldest_precio_ars = oldest_price * _get_fx(fx_rates, oldest_date) if moneda == 'ARS' else np.nan
            oldest_monto_ars  = oldest_monto  * _get_fx(fx_rates, oldest_date) if moneda == 'ARS' else np.nan
            synthetic    = pd.DataFrame([{
                'Fecha':      oldest_date,
                'Tipo':       'Compra',
                'Activo':     asset,
                'Cantidad':   deficit,
                'Precio':     oldest_price,
                'Monto':      oldest_monto,
                'Precio ARS': oldest_precio_ars,
                'Monto ARS':  oldest_monto_ars,
            }])
            ops  = pd.concat([synthetic, ops]).sort_values('Fecha').reset_index(drop=True)
            nota = (
                f'⚠️ {asset}: compra de origen no registrada — se estimaron '
                f'{deficit:.0f} nominales al precio más antiguo disponible '
                f'(${oldest_price:.2f} al {oldest_date.strftime("%d/%m/%Y")}). '
                f'Probable operación anterior al inicio de la base de datos.'
            )

        # ── Costo Promedio Ponderado ──────────────────────────────────────
        # Todos los montos se calculan en la moneda seleccionada (USD o ARS).
        # En ARS se usa el TC efectivo de cada operación (columna Monto ARS),
        # con fallback a Monto_USD × TC_cierre si Monto ARS no está disponible.
        current_nominals    = 0
        costo_unit_usd      = 0.0
        costo_unit_ars      = 0.0
        gan_realizada_usd   = 0.0
        gan_realizada_ars   = 0.0
        compras_usd         = 0.0
        compras_ars         = 0.0
        ventas_usd          = 0.0
        ventas_ars          = 0.0
        total_amort_usd     = 0.0
        total_amort_ars     = 0.0
        total_cupones_usd   = 0.0
        total_cupones_ars   = 0.0
        total_dividendos_usd = 0.0
        total_dividendos_ars = 0.0

        for _, op in ops.iterrows():
            tipo = op['Tipo'].strip()
            qty = float(op['Cantidad']) if pd.notna(op.get('Cantidad')) else 0.0
            monto_usd = float(op.get('Monto')) if pd.notna(op.get('Monto')) else 0.0
            monto_ars = _get_monto(op, 'ARS', fx_rates)
            if tipo == 'Compra':
                costo_prev_usd = current_nominals * costo_unit_usd
                costo_prev_ars = current_nominals * costo_unit_ars
                current_nominals += qty
                costo_unit_usd = (costo_prev_usd + monto_usd) / current_nominals
                costo_unit_ars = (costo_prev_ars + monto_ars) / current_nominals
                compras_usd += monto_usd
                compras_ars += monto_ars
            elif tipo == 'Venta':
                gan_realizada_usd += monto_usd - (qty * costo_unit_usd)
                gan_realizada_ars += monto_ars - (qty * costo_unit_ars)
                current_nominals -= qty
                ventas_usd += monto_usd
                ventas_ars += monto_ars
            else:
                categoria = _clasificar_operacion(tipo)
                if categoria == 'amortizacion':
                    total_amort_usd += monto_usd
                    total_amort_ars += monto_ars
                elif categoria == 'cupon':
                    total_cupones_usd += monto_usd
                    total_cupones_ars += monto_ars
                elif categoria == 'dividendo':
                    total_dividendos_usd += monto_usd
                    total_dividendos_ars += monto_ars

        if current_nominals <= 0:
            continue

        costo_posicion_usd = current_nominals * costo_unit_usd
        costo_posicion_ars = current_nominals * costo_unit_ars
        current_price_usd  = _get_current_price(asset, asset_prices, 'USD', fx_rates,
                                                live_prices, live_fx)
        current_price_ars  = _get_current_price(asset, asset_prices, 'ARS', fx_rates,
                                                live_prices, live_fx)
        valor_actual_usd   = current_nominals * current_price_usd
        valor_actual_ars   = current_nominals * current_price_ars
        gan_no_r_usd       = valor_actual_usd - costo_posicion_usd
        gan_no_r_ars       = valor_actual_ars - costo_posicion_ars
        ganancia_total_usd = (
            gan_realizada_usd + gan_no_r_usd
            + total_amort_usd + total_cupones_usd + total_dividendos_usd
        )
        ganancia_total_ars = (
            gan_realizada_ars + gan_no_r_ars
            + total_amort_ars + total_cupones_ars + total_dividendos_ars
        )

        fx_actual = (
            (current_price_ars / current_price_usd)
            if current_price_usd
            else (live_fx if live_fx is not None else _get_fx(fx_rates, pd.Timestamp.now()))
        )
        resultado_econ_usd_tc = ganancia_total_usd * fx_actual
        efecto_fx = ganancia_total_ars - resultado_econ_usd_tc

        current_price = current_price_ars if moneda == 'ARS' else current_price_usd
        valor_actual = valor_actual_ars if moneda == 'ARS' else valor_actual_usd
        costo_posicion = costo_posicion_ars if moneda == 'ARS' else costo_posicion_usd
        ganancia_realizada = gan_realizada_ars if moneda == 'ARS' else gan_realizada_usd
        total_amort = total_amort_ars if moneda == 'ARS' else total_amort_usd
        total_cupones = total_cupones_ars if moneda == 'ARS' else total_cupones_usd
        total_dividendos = total_dividendos_ars if moneda == 'ARS' else total_dividendos_usd
        ganancia_no_r = gan_no_r_ars if moneda == 'ARS' else gan_no_r_usd
        ganancia_total = ganancia_total_ars if moneda == 'ARS' else ganancia_total_usd
        retorno_pct = (ganancia_total / costo_posicion * 100) if costo_posicion > 0 else np.nan

        portfolio_data.append({
            'Activo':                  asset,
            'Nominales':               current_nominals,
            'Precio Actual':           current_price,
            '_Valor Actual':           valor_actual,
            'Costo':                   costo_posicion,
            'Ganancias Realizadas':    ganancia_realizada,
            'Resultado Econ. USD @ TC': resultado_econ_usd_tc if moneda == 'ARS' else np.nan,
            'Efecto FX':               efecto_fx if moneda == 'ARS' else np.nan,
            'Amortizaciones':          total_amort,
            'Cupones':                 total_cupones,
            'Dividendos':              total_dividendos,
            'Ganancias no Realizadas': ganancia_no_r,
            'Ganancia Total':          ganancia_total,
            'Retorno':                 retorno_pct,
            '_nota':                   nota,
        })

    return pd.DataFrame(portfolio_data)


# ─────────────────────────────────────────────
# Evolución histórica
# ─────────────────────────────────────────────
def calculate_portfolio_evolution(operaciones, precios, fecha_inicio, fecha_fin,
                                  moneda='USD', fx_rates=None,
                                  live_prices=None, live_fx=None):
    """Calcular evolución de la cartera en un rango de fechas."""
    operaciones = operaciones.copy()
    precios = precios.copy()
    operaciones['Fecha'] = pd.to_datetime(operaciones['Fecha'])
    precios['Fecha']     = pd.to_datetime(precios['Fecha'])

    assets = [a for a in operaciones['Activo'].unique() if pd.notna(a)]
    evolution_data = []
    all_flows_md = []  # flujos datados para Modified Dietz a nivel portafolio

    for asset in assets:
        asset_ops = operaciones[operaciones['Activo'] == asset].sort_values('Fecha')

        # C1/C2/C6: Detectar último reset usando solo ops ANTES de fecha_inicio.
        # Si se usara ops hasta fecha_fin, activos que cierran posición dentro del
        # rango (ej. compra+venta mismo día, o posición que llega a 0 en el período)
        # quedarían marcados como reset y su actividad sería excluida incorrectamente.
        ops_until_fin = asset_ops[asset_ops['Fecha'] <= pd.to_datetime(fecha_fin)]
        ops_for_reset = asset_ops[asset_ops['Fecha'] <  pd.to_datetime(fecha_inicio)]
        last_reset_date, last_reset_pos_pre = _find_last_reset(ops_for_reset)

        if last_reset_date is None:
            ops_since_reset = ops_until_fin
        else:
            # Mapear posición del reset (en ops_for_reset) a ops_until_fin vía index label
            reset_label = ops_for_reset.index[last_reset_pos_pre]
            pos_in_fin  = ops_until_fin.index.get_loc(reset_label)
            ops_since_reset = ops_until_fin.iloc[pos_in_fin + 1:]

        # C4: Detectar ventas sin compra previa — igual que Sección 1.
        # Si el total de ventas supera el total de compras registradas,
        # la compra original es anterior a la base de datos.
        # Se inyecta una compra sintética al precio más antiguo disponible.
        asset_prices = precios[precios['Activo'] == asset].sort_values('Fecha')
        buys_q  = ops_since_reset[ops_since_reset['Tipo'].str.strip() == 'Compra']['Cantidad'].sum()
        sells_q = ops_since_reset[ops_since_reset['Tipo'].str.strip() == 'Venta']['Cantidad'].sum()
        buys_q  = buys_q  if not pd.isna(buys_q)  else 0
        sells_q = sells_q if not pd.isna(sells_q) else 0
        deficit = sells_q - buys_q
        if deficit > 0 and not asset_prices.empty:
            oldest_row        = asset_prices.iloc[0]
            oldest_price      = float(oldest_row['Precio'])
            oldest_date       = oldest_row['Fecha']
            oldest_monto      = deficit * oldest_price
            oldest_precio_ars = oldest_price * _get_fx(fx_rates, oldest_date) if moneda == 'ARS' else np.nan
            oldest_monto_ars  = oldest_monto  * _get_fx(fx_rates, oldest_date) if moneda == 'ARS' else np.nan
            synthetic = pd.DataFrame([{
                'Fecha':      oldest_date,
                'Tipo':       'Compra',
                'Activo':     asset,
                'Cantidad':   deficit,
                'Precio':     oldest_price,
                'Monto':      oldest_monto,
                'Precio ARS': oldest_precio_ars,
                'Monto ARS':  oldest_monto_ars,
            }])
            ops_since_reset = pd.concat([synthetic, ops_since_reset]).sort_values('Fecha').reset_index(drop=True)
            st.caption(
                f'⚠️ {asset}: compra de origen no registrada — se estimaron '
                f'{deficit:.0f} nominales al precio más antiguo disponible '
                f'(${oldest_price:.2f} al {oldest_date.strftime("%d/%m/%Y")}). '
                f'Probable operación anterior al inicio de la base de datos.'
            )

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
            monto = _get_monto(op, moneda, fx_rates)
            if tipo == 'Compra':
                nom_inicio   += op['Cantidad']
            elif tipo == 'Venta':
                nom_inicio   -= op['Cantidad']
                sales_inicio += monto
            elif _clasificar_operacion(tipo):
                divcup_inicio += monto

        # Omitir activos sin actividad relevante en el período
        if nom_inicio <= 0 and ops_en_rango.empty:
            continue

        # Excluir activos cuya amortización final cae exactamente en fecha_inicio:
        # su posición efectiva el primer día del período ya es cero.
        ops_on_inicio_day    = ops_en_rango[ops_en_rango['Fecha'] == pd.to_datetime(fecha_inicio)]
        ops_after_inicio_day = ops_en_rango[ops_en_rango['Fecha'] >  pd.to_datetime(fecha_inicio)]
        nom_after_inicio_day = nom_inicio
        for _, op in ops_on_inicio_day.iterrows():
            tipo = op['Tipo'].strip()
            if tipo == 'Compra':
                nom_after_inicio_day += op['Cantidad']
            elif tipo == 'Venta':
                nom_after_inicio_day -= op['Cantidad']
            elif _clasificar_operacion(tipo) == 'amortizacion':
                qty = op.get('Cantidad', np.nan)
                if pd.notna(qty) and qty > 0:
                    nom_after_inicio_day = max(nom_after_inicio_day - qty, 0)
        if nom_after_inicio_day <= 0 and ops_after_inicio_day.empty:
            continue

        # Acumulados en el período
        nom_fin    = nom_inicio
        sales_fin  = sales_inicio
        divcup_fin = divcup_inicio
        compras_en_periodo = 0
        ops_nom_periodo = 0.0
        flujos_md = []  # flujos datados para Modified Dietz por activo

        for _, op in ops_en_rango.iterrows():
            tipo = op['Tipo'].strip()
            monto = _get_monto(op, moneda, fx_rates)
            if tipo == 'Compra':
                nom_fin            += op['Cantidad']
                ops_nom_periodo    += op['Cantidad']
                compras_en_periodo += monto
                flujos_md.append((op['Fecha'], +monto))
            elif tipo == 'Venta':
                nom_fin   -= op['Cantidad']
                ops_nom_periodo -= op['Cantidad']
                sales_fin += monto
                flujos_md.append((op['Fecha'], -monto))
            elif _clasificar_operacion(tipo):
                divcup_fin += monto
                flujos_md.append((op['Fecha'], -monto))

        # M3: advertir si faltan precios
        avail_inicio = asset_prices[asset_prices['Fecha'] <= pd.to_datetime(fecha_inicio)]
        avail_fin    = asset_prices[asset_prices['Fecha'] <= pd.to_datetime(fecha_fin)]
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

        precio_inicio = _get_price_at_date(asset_prices, fecha_inicio, moneda, fx_rates)
        precio_fin    = _get_end_price(asset, asset_prices, fecha_fin, moneda, fx_rates,
                                       live_prices, live_fx)

        # Red de seguridad: si después de la compra sintética los nominales
        # siguen siendo negativos hay un error de datos en el Excel.
        if nom_fin < 0:
            st.warning(
                f"⚠️ {asset}: nominales negativos ({nom_fin:.0f}) incluso tras ajuste — "
                f"verificar operaciones en el Excel. Se excluye."
            )
            continue

        valor_inicio       = nom_inicio * precio_inicio if nom_inicio > 0 else 0
        valor_fin          = nom_fin * precio_fin
        div_cup_en_periodo = divcup_fin - divcup_inicio
        ventas_en_periodo  = sales_fin  - sales_inicio
        ganancia_total     = (valor_fin - valor_inicio - compras_en_periodo) + div_cup_en_periodo + ventas_en_periodo

        # "Valor al Inicio" debe reflejar estrictamente la foto al comienzo del período.
        # Las compras posteriores se muestran siempre en la columna "Compras".
        valor_inicio_display = valor_inicio
        compras_adicionales = compras_en_periodo

        # Modified Dietz: retorno por activo ponderado por tiempo de flujos
        retorno_md = _modified_dietz_pct(valor_inicio, valor_fin, flujos_md,
                                         fecha_inicio, fecha_fin)
        all_flows_md.extend(flujos_md)

        # PPP: costo promedio ponderado de la posición remanente al cierre.
        # Para posiciones abiertas al inicio, se toma el mark de fecha_inicio
        # como costo base del tramo preexistente dentro del período.
        costo_ppp = valor_inicio
        nom_ppp = nom_inicio
        for _, op in ops_en_rango.iterrows():
            tipo = op['Tipo'].strip()
            monto = _get_monto(op, moneda, fx_rates)
            qty = op.get('Cantidad', np.nan)
            qty = float(qty) if pd.notna(qty) else 0.0

            if tipo == 'Compra' and qty > 0:
                costo_ppp += monto
                nom_ppp += qty
            elif tipo == 'Venta' and qty > 0 and nom_ppp > 0:
                sold_qty = min(qty, nom_ppp)
                avg_cost = (costo_ppp / nom_ppp) if nom_ppp > 0 else 0
                costo_ppp = max(costo_ppp - (avg_cost * sold_qty), 0)
                nom_ppp = max(nom_ppp - sold_qty, 0)
                if nom_ppp == 0:
                    costo_ppp = 0

        ppp = (costo_ppp / nom_ppp) if nom_ppp > 0 else np.nan

        evolution_data.append({
            'Activo':               asset,
            'Nominales':            nom_fin,
            'Nominales al Inicio':  nom_inicio,
            'Operaciones del Período': ops_nom_periodo,
            'Nominales Fin Período': nom_fin,
            'Costo':                costo_ppp,
            'PPP':                  ppp,
            'Precio al Fin':        precio_fin,
            'Valor Actual':         valor_fin,
            'Valor al Inicio':      valor_inicio_display,
            '_Valor Inicio Real':   valor_inicio,
            'Compras':              compras_en_periodo,
            'Compras Adicionales':  compras_adicionales,
            'Ventas':               ventas_en_periodo,
            'Amort / Cup / Div':    div_cup_en_periodo,
            'Ganancia Total':       ganancia_total,
            'Retorno':              retorno_md,
        })

    return pd.DataFrame(evolution_data), all_flows_md


# ─────────────────────────────────────────────
# Detalle por activo
# ─────────────────────────────────────────────
def mostrar_analisis_detallado_activo(operaciones, precios, activo,
                                      fecha_inicio, fecha_fin,
                                      moneda='USD', fx_rates=None,
                                      live_prices=None, live_fx=None):
    """Mostrar análisis detallado de un activo específico."""
    operaciones = operaciones.copy()
    precios = precios.copy()
    operaciones['Fecha'] = pd.to_datetime(operaciones['Fecha'])
    precios['Fecha']     = pd.to_datetime(precios['Fecha'])

    asset_ops = operaciones[operaciones['Activo'] == activo].sort_values('Fecha')

    # C1/C2: Reset detectado solo con ops ANTES de fecha_inicio (igual que Sección 2).
    # Así, activos que cierran posición dentro del período (AL29, AL30) no quedan excluidos.
    ops_until_fin_d = asset_ops[asset_ops['Fecha'] <= pd.to_datetime(fecha_fin)]
    ops_for_reset_d = asset_ops[asset_ops['Fecha'] <  pd.to_datetime(fecha_inicio)]
    last_reset_date, last_reset_pos_pre = _find_last_reset(ops_for_reset_d)

    if last_reset_date is None:
        ops_since_reset = ops_until_fin_d
    else:
        reset_label = ops_for_reset_d.index[last_reset_pos_pre]
        pos_in_fin  = ops_until_fin_d.index.get_loc(reset_label)
        ops_since_reset = ops_until_fin_d.iloc[pos_in_fin + 1:]

    # Nominales al inicio (ops ESTRICTAMENTE antes de fecha_inicio → sin doble conteo)
    nom_inicio = 0
    for _, op in ops_since_reset.iterrows():
        if op['Fecha'] >= pd.to_datetime(fecha_inicio):
            break
        if op['Tipo'].strip() == 'Compra':
            nom_inicio += op['Cantidad']
        elif op['Tipo'].strip() == 'Venta':
            nom_inicio -= op['Cantidad']

    detalle_data = []

    ap = precios[precios['Activo'] == activo].sort_values('Fecha')

    # M7: solo agregar fila "Valor Inicial" si había posición al inicio del período
    if nom_inicio > 0:
        precio_inicio = _get_price_at_date(ap, fecha_inicio, moneda, fx_rates)
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
            'Precio':    _get_precio_op(op, moneda, fx_rates),
            'Valor':     _get_monto(op, moneda, fx_rates),
        })

    # Me7: fila de cierre siempre presente (muestra $0 si la posición fue cerrada)
    if nom_fin > 0:
        precio_fin = _get_end_price(activo, ap, fecha_fin, moneda, fx_rates,
                                    live_prices, live_fx)
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
            lambda x: _fmt_price(x, moneda) if pd.notna(x) and x != 0 else ""
        )
        display['Valor'] = display['Valor'].apply(
            lambda x: _fmt_money(x, moneda) if pd.notna(x) and x != 0 else ""
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

    else:
        st.info(f"No hay operaciones para {activo} en el período seleccionado.")


# ─────────────────────────────────────────────
# Helpers de formato
# ─────────────────────────────────────────────
def _fmt_money(x, moneda='USD'):
    """Formatea un monto monetario según la moneda.

    USD: dos decimales (ej: $1,234.56)
    ARS: sin decimales porque los valores en pesos son grandes (ej: $1,234,567)
    """
    if not pd.notna(x):
        return ""
    if moneda == 'ARS':
        return f"${x:,.0f}"
    return f"${x:,.2f}"


def _fmt_price(x, moneda='USD'):
    """Formatea un precio según la moneda (ambos con 2 decimales)."""
    if not pd.notna(x):
        return ""
    return f"${x:,.2f}"


def _fmt_number(x):
    return f"{x:,.0f}" if pd.notna(x) else ""


def _style_variation_cell(val):
    """Colorea variaciones: verde si positiva, rojo si negativa."""
    if not isinstance(val, str):
        return ""
    text = val.strip()
    if '▼' in text or '(▼' in text or text.startswith('-'):
        return "color:#DC2626;font-weight:600;"
    if '▲' in text or '(▲' in text:
        return "color:#16A34A;font-weight:600;"
    return ""


def _metric(label, value_str, sub_str=None):
    """Card de métrica estilo dashboard financiero.

    Fondo blanco, label en gris uppercase, valor grande en negrita,
    delta opcional con flecha y color verde/rojo (M2).
    """
    delta_html = ''
    if sub_str:
        # M2: rojo si negativo, verde si positivo
        is_neg = str(sub_str).strip().startswith('-')
        color  = '#DC2626' if is_neg else '#16A34A'
        arrow  = '▼' if is_neg else '▲'
        delta_html = (
            f'<div style="display:flex;align-items:center;gap:3px;margin-top:5px;">'
            f'<span style="font-size:0.78rem;font-weight:600;color:{color};">'
            f'{arrow} {sub_str}</span></div>'
        )

    st.markdown(
        f'''<div style="
                background:#FFFFFF;
                border-radius:10px;
                padding:1rem 1.1rem 0.9rem;
                border:1px solid #E5E7EB;
                box-shadow:0 1px 4px rgba(0,0,0,0.06);
                min-height:90px;">
            <div style="font-size:0.68rem;font-weight:600;color:#6B7280;
                        text-transform:uppercase;letter-spacing:0.55px;
                        margin-bottom:6px;">{label}</div>
            <div style="font-size:1.25rem;font-weight:700;color:#1B2333;
                        line-height:1.25;word-break:break-word;">{value_str}</div>
            {delta_html}
        </div>''',
        unsafe_allow_html=True
    )


def _render_summary_panel(base_items, total_label, total_value, total_sub=None, side_items=None, inline_total=False):
    """Renderiza un resumen superior estilo tablero compacto."""
    side_items = side_items or []
    has_side = bool(side_items)
    if inline_total:
        cols = st.columns([6.4, 2.6] if has_side else [1])
    else:
        cols = st.columns([4.85, 1.95, 2.2] if has_side else [5.7, 2.3])
    if has_side and side_items and isinstance(side_items[0], tuple):
        side_groups = [side_items]
    else:
        side_groups = side_items

    left_col = cols[0]
    total_col = None if inline_total else cols[1]
    side_col = cols[1] if inline_total and has_side else (cols[2] if has_side else None)

    with left_col:
        left_items = list(base_items)
        if inline_total:
            total_delta_html = ''
            if total_sub:
                is_neg = '▼' in str(total_sub)
                color = '#DC2626' if is_neg else '#16A34A'
                total_delta_html = (
                    f'<span style="font-size:0.74rem;font-weight:700;color:{color};'
                    f'margin-left:0.45rem;white-space:nowrap;">{total_sub}</span>'
                )
            left_items.append((total_label, total_value, total_delta_html))
        cells = []
        for i, item in enumerate(left_items):
            if len(item) == 3:
                label, value, extra_html = item
            else:
                label, value = item
                extra_html = ''
            border = 'border-right:1px solid #E5E7EB;' if i < len(left_items) - 1 else ''
            cell_bg = 'background:linear-gradient(180deg,#FFFFFF 0%,#F7FAFF 100%);' if inline_total and i == len(left_items) - 1 else ''
            cell_border = 'border-left:1px solid #D9E3F0;' if inline_total and i == len(left_items) - 1 else ''
            cells.append(
                f'<div style="padding:0.86rem 0.95rem 0.82rem;{border}{cell_bg}{cell_border}">'
                f'<div style="font-size:0.8rem;font-weight:600;color:#667085;'
                f'margin-bottom:0.42rem;white-space:nowrap;">{label}</div>'
                f'<div style="display:flex;align-items:baseline;gap:0.15rem;flex-wrap:wrap;'
                f'font-size:1.04rem;font-weight:700;color:#1B2333;line-height:1.2;">'
                f'<span>{value}</span>{extra_html}'
                f'</div>'
                f'</div>'
            )
        st.markdown(
            f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:16px;'
            f'box-shadow:0 10px 26px rgba(15,23,42,0.05);overflow:hidden;">'
            f'<div style="display:grid;grid-template-columns:repeat({len(left_items)}, minmax(0, 1fr));">'
            f'{"".join(cells)}'
            f'</div></div>',
            unsafe_allow_html=True
        )

    if total_col is not None:
        with total_col:
            compact_total = not has_side
            delta_html = ''
            if total_sub:
                is_neg = str(total_sub).strip().startswith('(') and '▼' in str(total_sub)
                color = '#DC2626' if is_neg else '#16A34A'
                delta_html = (
                    f'<span style="font-size:0.9rem;font-weight:700;color:{color};'
                    f'margin-left:0.45rem;white-space:nowrap;">{total_sub}</span>'
                )
            st.markdown(
                f'<div style="background:{"#FFFFFF" if compact_total else "linear-gradient(180deg,#FFFFFF 0%,#F7FAFF 100%)"};'
                f'border:1px solid {"#E5E7EB" if compact_total else "#D9E3F0"};border-radius:{16 if compact_total else 18}px;'
                f'box-shadow:{"0 10px 26px rgba(15,23,42,0.05)" if compact_total else "0 12px 28px rgba(15,23,42,0.08)"};'
                f'padding:{"0.86rem 0.95rem 0.82rem" if compact_total else "0.95rem 1rem"};'
                f'min-height:{"auto" if compact_total else "118px"};'
                f'display:flex;flex-direction:column;justify-content:center;align-items:{"flex-start" if compact_total else "center"};text-align:{"left" if compact_total else "center"};">'
                f'<div style="font-size:{"0.8rem" if compact_total else "0.82rem"};font-weight:{600 if compact_total else 700};color:#667085;'
                f'margin-bottom:0.42rem;">{total_label}</div>'
                f'<div style="display:flex;align-items:baseline;justify-content:{"flex-start" if compact_total else "center"};'
                f'gap:0.15rem;flex-wrap:wrap;font-size:{"1.04rem" if compact_total else "1.35rem"};'
                f'font-weight:{700 if compact_total else 800};color:#122033;line-height:1.12;">'
                f'<span>{total_value}</span>{delta_html}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    if has_side and side_col is not None:
        with side_col:
            cards = []
            for group in side_groups:
                rows = []
                for i, (label, value) in enumerate(group):
                    border = 'border-bottom:1px solid #E5E7EB;' if i < len(group) - 1 else ''
                    rows.append(
                        f'<div style="display:flex;justify-content:space-between;gap:0.8rem;'
                        f'align-items:center;min-height:40px;padding:0 0.85rem;box-sizing:border-box;{border}">'
                        f'<div style="font-size:0.76rem;font-weight:600;color:#667085;'
                        f'white-space:nowrap;">{label}</div>'
                        f'<div style="font-size:0.98rem;font-weight:700;color:#122033;text-align:right;line-height:1.12;">{value}</div>'
                        f'</div>'
                    )
                cards.append(
                    f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:16px;'
                    f'box-shadow:0 10px 26px rgba(15,23,42,0.05);overflow:hidden;min-height:82px;">'
                    f'{"".join(rows)}'
                    f'</div>'
                )
            st.markdown(
                f'<div style="display:flex;flex-direction:column;gap:0.7rem;">'
                f'{"".join(cards)}'
                f'</div>',
                unsafe_allow_html=True
            )


def _section_header(title, subtitle=None):
    """Encabezado de sección con barra azul lateral, título y subtítulo opcional.

    Usa HTML en una sola línea para evitar que el parser de Streamlit
    interprete los saltos de línea como markdown.
    """
    sub_html = f'<div style="font-size:0.83rem;color:#6B7280;margin-top:3px;">{subtitle}</div>' if subtitle else ''
    st.markdown(
        f'<div style="display:flex;align-items:flex-start;gap:11px;margin:2rem 0 0.75rem;">'
        f'<div style="width:4px;min-height:28px;background:#1A4B9B;border-radius:2px;flex-shrink:0;margin-top:3px;"></div>'
        f'<div><div style="font-size:1.2rem;font-weight:700;color:#1B2333;line-height:1.25;">{title}</div>{sub_html}</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def _modified_dietz_pct(v_inicio, v_fin, flows, fecha_inicio, fecha_fin):
    """Retorno Modified Dietz (%).

    Fórmula estándar de medición de rendimiento ponderado por tiempo simplificado:
      R = (V_fin − V_inicio − ΣCF_i) / (V_inicio + Σ(CF_i × W_i))
    donde W_i = (T − t_i) / T  y  t_i = días desde inicio hasta el flujo i.

    Parámetros:
      v_inicio: valor de mercado al inicio del período.
      v_fin:    valor de mercado al final del período.
      flows:    lista de (fecha, monto) — monto > 0 = inflow (compra/depósito),
                monto < 0 = outflow (venta/amort/cupón/dividendo/retiro).
      fecha_inicio, fecha_fin: límites del período.

    Retorna porcentaje (ej. 5.2 para 5.2%).
    """
    T = (pd.to_datetime(fecha_fin) - pd.to_datetime(fecha_inicio)).days
    if T <= 0:
        return 0.0

    sum_flows = sum(f for _, f in flows)
    gain = v_fin - v_inicio - sum_flows

    weighted_flows = sum(
        f * (T - (pd.to_datetime(d) - pd.to_datetime(fecha_inicio)).days) / T
        for d, f in flows
    )

    base = v_inicio + weighted_flows
    if abs(base) < 1e-9:
        return 0.0

    return (gain / base) * 100


# ─────────────────────────────────────────────
# Helpers de presentación
# ─────────────────────────────────────────────
_MESES_ES = {
    'January': 'enero', 'February': 'febrero', 'March': 'marzo',
    'April': 'abril', 'May': 'mayo', 'June': 'junio',
    'July': 'julio', 'August': 'agosto', 'September': 'septiembre',
    'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre',
}

def _fecha_es(fecha):
    """Devuelve la fecha formateada con el mes en español."""
    return f"{fecha.day} de {_MESES_ES[fecha.strftime('%B')]} de {fecha.year}"


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    import uuid

    # ── Archivo a usar ─────────────────────────────────────────────────────────
    # El uploader está al pie de la página. Su contenido se guarda en session_state
    # para que esté disponible desde el inicio del script en reruns posteriores.
    filename = 'operaciones.xlsx'
    if st.session_state.get('upload_bytes'):
        if 'upload_id' not in st.session_state:
            st.session_state.upload_id = uuid.uuid4().hex[:12]
        filename = f"temp_{st.session_state.upload_id}.xlsx"
        with open(filename, 'wb') as f:
            f.write(st.session_state.upload_bytes)

    # ── Moneda desde sesión (disponible antes del widget, que se renderiza luego) ─
    moneda = st.session_state.get('moneda_sel', 'USD')

    # ── Fecha actual fija = hoy (se muestra en hero card, sin input) ───────────
    fecha_actual = datetime.now().date()

    # ── Carga de datos ─────────────────────────────────────────────────────────
    operaciones, precios, fx_rates, live_prices, live_fx = load_data(filename)

    if operaciones is None or precios is None:
        st.error(
            "Error al cargar los datos. "
            "Verifica que el archivo 'operaciones.xlsx' esté en la carpeta del proyecto."
        )
        return

    # Validar ARS
    if moneda == 'ARS' and (fx_rates is None or fx_rates.empty):
        st.warning(
            "⚠️ Modo ARS: no se encontró columna 'ARS' en Precios. "
            "Se muestran valores en USD."
        )
        moneda = 'USD'

    lbl_moneda = 'ARS' if moneda == 'ARS' else 'USD'

    # ── Hero card ──────────────────────────────────────────────────────────────
    fecha_str = _fecha_es(fecha_actual)
    st.markdown(
        f'<div style="background:#1A4B9B;border-radius:12px;padding:1.2rem 1.8rem;'
        f'margin-bottom:0.5rem;display:flex;align-items:center;justify-content:space-between;">'
        f'<div>'
        f'<div style="font-size:1.4rem;font-weight:700;color:#FFFFFF;">Tus Inversiones</div>'
        f'<div style="font-size:0.82rem;color:rgba(255,255,255,0.75);margin-top:2px;">{fecha_str}</div>'
        f'</div>'
        f'<div style="font-size:0.78rem;font-weight:500;color:#FFFFFF;'
        f'background:rgba(255,255,255,0.12);padding:4px 12px;'
        f'border-radius:20px;border:1px solid rgba(255,255,255,0.35);">{lbl_moneda}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ══════════════════════════════════════════
    # SECCIÓN 1 – COMPOSICIÓN ACTUAL
    # Título y toggle de moneda en la misma fila
    # ══════════════════════════════════════════
    col_s1, _, col_mon = st.columns([5, 1, 1])
    with col_s1:
        _section_header(
            "Composición Actual de la Cartera",
            f"Calculado al {fecha_actual.strftime('%d/%m/%Y')} — valores en {lbl_moneda}"
        )
    with col_mon:
        # Espaciador para alinear verticalmente el radio con el título
        st.markdown('<div style="height:2.1rem;"></div>', unsafe_allow_html=True)
        moneda = st.radio(
            'Moneda', ['USD', 'ARS'],
            horizontal=True,
            key='moneda_sel',
            label_visibility='collapsed'
        )
    lbl_moneda = 'ARS' if moneda == 'ARS' else 'USD'

    portfolio_df = calculate_current_portfolio(
        operaciones, precios, fecha_actual, moneda=moneda, fx_rates=fx_rates,
        live_prices=live_prices, live_fx=live_fx
    )

    if portfolio_df.empty:
        st.warning("No hay activos con nominales positivos en la fecha seleccionada.")
    else:
        total_valor_mercado = portfolio_df['_Valor Actual'].sum()
        total_costo         = portfolio_df['Costo'].sum()
        total_ganancia_rlz  = portfolio_df['Ganancias Realizadas'].sum()
        total_res_usd_tc    = portfolio_df['Resultado Econ. USD @ TC'].sum() if 'Resultado Econ. USD @ TC' in portfolio_df.columns else np.nan
        total_efecto_fx     = portfolio_df['Efecto FX'].sum() if 'Efecto FX' in portfolio_df.columns else np.nan
        total_amort         = portfolio_df['Amortizaciones'].sum()
        total_cup           = portfolio_df['Cupones'].sum()
        total_div           = portfolio_df['Dividendos'].sum()
        total_ganancia_r    = total_amort + total_cup + total_div
        total_ganancia_no_r = portfolio_df['Ganancias no Realizadas'].sum()
        pct_no_r            = (total_ganancia_no_r / total_costo * 100) if total_costo > 0 else 0

        total_ganancia = total_ganancia_rlz + total_ganancia_r + total_ganancia_no_r
        pct_total      = (total_ganancia / total_costo * 100) if total_costo > 0 else 0
        pct_str        = f"({'▼' if pct_total < 0 else '▲'} {abs(pct_total):.1f}%)"
        if moneda == 'ARS':
            _render_summary_panel(
                base_items=[
                    ('Valor de Mercado <span style="font-size:0.68rem;font-weight:500;">(1)</span>', _fmt_money(total_valor_mercado, moneda)),
                    ('Costo Total <span style="font-size:0.68rem;font-weight:500;">(2)</span>', _fmt_money(total_costo, moneda)),
                    ('Amort Cupones Div <span style="font-size:0.68rem;font-weight:500;">(3)</span>', _fmt_money(total_ganancia_r, moneda)),
                    ('Resultado por Ventas <span style="font-size:0.68rem;font-weight:500;">(4)</span>', _fmt_money(total_ganancia_rlz, moneda)),
                ],
                total_label='Resultado <span style="font-size:0.68rem;font-weight:500;">(1) + (3) + (4) - (2)</span>',
                total_value=_fmt_money(total_ganancia, moneda),
                total_sub=pct_str,
                side_items=[
                    [
                        ('Gan. Realizadas <span style="font-size:0.66rem;font-weight:500;">(3) + (4)</span>', _fmt_money(total_ganancia_rlz + total_ganancia_r, moneda)),
                        ('Gan. no Real. <span style="font-size:0.66rem;font-weight:500;">(1) - (2)</span>', _fmt_money(total_ganancia_no_r, moneda)),
                    ],
                    [
                        ("Efecto Precio/Cobros", _fmt_money(total_res_usd_tc, moneda)),
                        ("Efecto FX", _fmt_money(total_efecto_fx, moneda)),
                    ],
                ],
                inline_total=True,
            )
        else:
            _render_summary_panel(
                base_items=[
                    ("Valor de Mercado", _fmt_money(total_valor_mercado, moneda)),
                    ("Costo Total", _fmt_money(total_costo, moneda)),
                    ("Amort Cupones Div", _fmt_money(total_ganancia_r, moneda)),
                    ("Resultado por Ventas", _fmt_money(total_ganancia_rlz, moneda)),
                ],
                total_label="Resultado",
                total_value=_fmt_money(total_ganancia, moneda),
                total_sub=pct_str,
            )

        st.markdown("<div style='height:1.25rem;'></div>", unsafe_allow_html=True)

        if moneda == 'ARS':
            cols_display = [
                'Activo', 'Nominales', 'Precio Actual', 'Valor Actual', 'Costo',
                'Ganancias Realizadas', 'Amort / Cup / Div',
                'Retorno', 'Resultado Econ. USD @ TC', 'Efecto FX'
            ]
        else:
            cols_display = [
                'Activo', 'Nominales', 'Precio Actual', 'Valor Actual', 'Costo',
                'Ganancias Realizadas', 'Amort / Cup / Div', 'Retorno'
            ]
        display_df = portfolio_df.rename(columns={'_Valor Actual': 'Valor Actual'}).copy()
        display_df['Amort / Cup / Div'] = (
            display_df['Amortizaciones'] + display_df['Cupones'] + display_df['Dividendos']
        )
        display_df = display_df[cols_display].copy()
        display_df['Nominales']      = display_df['Nominales'].apply(_fmt_number)
        display_df['Precio Actual']  = display_df['Precio Actual'].apply(lambda x: _fmt_price(x, moneda))
        display_df['Valor Actual']   = display_df['Valor Actual'].apply(lambda x: _fmt_money(x, moneda))
        display_df['Costo']          = display_df['Costo'].apply(lambda x: _fmt_money(x, moneda))
        display_df['Ganancias Realizadas'] = display_df['Ganancias Realizadas'].apply(lambda x: _fmt_money(x, moneda))
        if moneda == 'ARS':
            display_df['Resultado Econ. USD @ TC'] = display_df['Resultado Econ. USD @ TC'].apply(lambda x: _fmt_money(x, moneda))
            display_df['Efecto FX'] = display_df['Efecto FX'].apply(lambda x: _fmt_money(x, moneda))
            display_df['Amort / Cup / Div'] = display_df['Amort / Cup / Div'].apply(lambda x: _fmt_money(x, moneda))
        else:
            display_df['Amort / Cup / Div'] = display_df['Amort / Cup / Div'].apply(lambda x: _fmt_money(x, moneda))
        display_df['Retorno'] = display_df['Retorno'].apply(
            lambda x: f"{'▼' if x < 0 else '▲'} {abs(x):.1f}%" if pd.notna(x) else "-"
        )
        st.dataframe(display_df.style.map(_style_variation_cell, subset=['Retorno']), use_container_width=True, hide_index=True,
                     column_config={
                         "Activo": st.column_config.TextColumn("Activo", width="small"),
                         "Nominales": st.column_config.TextColumn("Nom.", width="small"),
                         "Precio Actual": st.column_config.TextColumn("Precio", width="small"),
                         "Valor Actual": st.column_config.TextColumn("Valor de Mercado", width="small"),
                         "Costo": st.column_config.TextColumn("Costo", width="small"),
                         "Ganancias Realizadas": st.column_config.TextColumn("Resultado por Ventas", width="small"),
                         "Ganancias no Realizadas": st.column_config.TextColumn("No real.", width="small"),
                         "Resultado Econ. USD @ TC": st.column_config.TextColumn("Efecto Precio/Cobros", width="small"),
                         "Efecto FX": st.column_config.TextColumn("FX", width="small"),
                         "Amort / Cup / Div": st.column_config.TextColumn("Amort Cupones Div", width="small"),
                         "Amortizaciones": st.column_config.TextColumn("Pagos", width="small"),
                         "Cupones": st.column_config.TextColumn("Pagos", width="small"),
                         "Dividendos": st.column_config.TextColumn("Pagos", width="small"),
                         "Retorno": st.column_config.TextColumn("Retorno", width="small"),
                     })

        if '_nota' in portfolio_df.columns:
            for nota in portfolio_df[portfolio_df['_nota'] != '']['_nota']:
                st.caption(nota)
        if moneda == 'ARS':
            st.caption(
                "ℹ️ Gan. Realizadas = (3) + (4). "
                "Gan. no Real. = (1) - (2). "
                "Ganancia Total = (1) + (3) + (4) - (2). "
                "También se abre como: Ganancia Total = Efecto Precio/Cobros + Efecto FX."
            )

    # ══════════════════════════════════════════
    # SECCIÓN 2 – EVOLUCIÓN HISTÓRICA
    # Título y selector de fechas en la misma fila
    # ══════════════════════════════════════════
    col_s2, col_i, col_f = st.columns([4.6, 1.5, 1.5])
    with col_s2:
        _section_header("Análisis de la Evolución de la Cartera")
    with col_i:
        st.markdown('<div style="height:2.15rem;"></div>', unsafe_allow_html=True)
        lbl_i, inp_i = st.columns([0.7, 2.3])
        with lbl_i:
            st.markdown('<div style="padding-top:0.42rem;font-size:0.95rem;color:#1B2333;">Inicio</div>', unsafe_allow_html=True)
        with inp_i:
            fecha_inicio = st.date_input(
                "Inicio",
                value=datetime.now().date() - timedelta(days=365),
                help="Fecha de inicio del período",
                label_visibility='collapsed'
            )
    with col_f:
        st.markdown('<div style="height:2.15rem;"></div>', unsafe_allow_html=True)
        lbl_f, inp_f = st.columns([0.45, 2.55])
        with lbl_f:
            st.markdown('<div style="padding-top:0.42rem;font-size:0.95rem;color:#1B2333;">Fin</div>', unsafe_allow_html=True)
        with inp_f:
            fecha_fin = st.date_input(
                "Fin",
                value=datetime.now().date(),
                help="Fecha de fin del período",
                label_visibility='collapsed'
            )

    # Me1: validar rango
    if fecha_inicio > fecha_fin:
        st.error("⚠️ La fecha de inicio no puede ser posterior a la fecha de fin.")
        return

    evolution_df, all_flows_md = calculate_portfolio_evolution(
        operaciones, precios, fecha_inicio, fecha_fin, moneda=moneda, fx_rates=fx_rates,
        live_prices=live_prices, live_fx=live_fx
    )

    if evolution_df.empty:
        st.warning("No hay datos de evolución para el rango de fechas seleccionado.")
    else:
        flujos     = evolution_df['Ventas'].sum() + evolution_df['Amort / Cup / Div'].sum()
        total_gain = evolution_df['Ganancia Total'].sum()
        # Modified Dietz a nivel portafolio: pondera flujos por tiempo
        v_inicio_real_total = evolution_df['_Valor Inicio Real'].sum()
        v_fin_total         = evolution_df['Valor Actual'].sum()
        pct_evo = _modified_dietz_pct(v_inicio_real_total, v_fin_total,
                                       all_flows_md, fecha_inicio, fecha_fin)
        pct_str2   = f"({'▼' if pct_evo < 0 else '▲'} {abs(pct_evo):.1f}%)"
        _render_summary_panel(
            base_items=[
                ("Valor al Inicio", _fmt_money(evolution_df['Valor al Inicio'].sum(), moneda)),
                ("Compras - Ventas", _fmt_money(evolution_df['Compras'].sum() - evolution_df['Ventas'].sum(), moneda)),
                ("Amort / Cupones / Div", _fmt_money(evolution_df['Amort / Cup / Div'].sum(), moneda)),
                ("Valor Final", _fmt_money(evolution_df['Valor Actual'].sum(), moneda)),
            ],
            total_label="Resultado",
            total_value=_fmt_money(total_gain, moneda),
            total_sub=pct_str2,
        )
        st.markdown("<div style='height:1.25rem;'></div>", unsafe_allow_html=True)

        evo_display = evolution_df.sort_values('Nominales Fin Período', ascending=False).reset_index(drop=True).copy()
        evo_display = evo_display[
            ['Activo', 'Nominales al Inicio', 'Valor al Inicio',
             'Nominales Fin Período', 'Precio al Fin', 'Valor Actual',
             'Amort / Cup / Div', 'Costo', 'Ganancia Total', 'Retorno']
        ]
        for col in ['Nominales al Inicio', 'Nominales Fin Período']:
            evo_display[col] = evo_display[col].apply(_fmt_number)
        evo_display['Retorno'] = evo_display['Retorno'].apply(
            lambda x: f"{'▼' if x < 0 else '▲'} {abs(x):.1f}%" if pd.notna(x) else "-"
        )
        for col in ['Precio al Fin', 'Valor Actual', 'Valor al Inicio',
                    'Costo', 'Amort / Cup / Div', 'Ganancia Total']:
            if col == 'Precio al Fin':
                evo_display[col] = evo_display[col].apply(lambda x: _fmt_price(x, moneda))
            else:
                evo_display[col] = evo_display[col].apply(lambda x: _fmt_money(x, moneda))
        st.dataframe(evo_display.style.map(_style_variation_cell, subset=['Retorno']), use_container_width=True, hide_index=True,
                     column_config={
                         "Activo": st.column_config.TextColumn("Activo", width="medium"),
                         "Nominales al Inicio": st.column_config.TextColumn("Nom. Inicio", width="small"),
                         "Nominales Fin Período": st.column_config.TextColumn("Nom. Fin", width="small"),
                         "Valor al Inicio": st.column_config.TextColumn("Valor al Inicio", width="small"),
                         "Precio al Fin": st.column_config.TextColumn("Precio Fin", width="small"),
                         "Valor Actual": st.column_config.TextColumn("Valor Fin", width="small"),
                         "Amort / Cup / Div": st.column_config.TextColumn("Amort/Cup/Div", width="small"),
                         "Costo": st.column_config.TextColumn("Costo", width="small"),
                         "Ganancia Total": st.column_config.TextColumn("Resultado", width="small"),
                     })

        # ── Tabla cash: cross-check por efectivo real ────────────────────────────
        # El "efectivo real" en una fecha = depósitos − retiros − compras + (ventas+amort+cup+div)
        # acumulados hasta esa fecha. Esto garantiza que ganancia_cash == ganancia_bonds.
        ops_cash = operaciones.copy()
        ops_cash['Fecha'] = pd.to_datetime(ops_cash['Fecha'], errors='coerce')

        cols_ops = ops_cash.columns.tolist()
        col_dep  = next((c for c in cols_ops if 'deposit' in c.strip().lower()), None)
        col_ret  = next((c for c in cols_ops if 'retiro'  in c.strip().lower()), None)
        has_cash = bool(col_dep and col_ret)

        def _actual_cash(df, fecha, strict_bond=False, strict_ext=False):
            """Efectivo real acumulado.
            strict_bond: usa < fecha para flujos de bonos (compras/ventas/amort/cup).
            strict_ext:  usa < fecha para flujos externos (depósitos/retiros).
            Para cash_inicio: strict_bond=True, strict_ext=False
              → depósitos/retiros del día de inicio cuentan como capital inicial,
                pero los bonos comprados ese día no (consistente con bond table).
            """
            total = 0.0
            for _, row in df.iterrows():
                fecha_row = row['Fecha']
                if pd.isna(fecha_row):
                    continue
                fx  = _get_fx(fx_rates, fecha_row) if moneda == 'ARS' else 1.0
                dep = row[col_dep] if col_dep and pd.notna(row.get(col_dep, np.nan)) else 0.0
                ret = row[col_ret] if col_ret and pd.notna(row.get(col_ret, np.nan)) else 0.0
                cut_ext  = fecha_row <  pd.to_datetime(fecha) if strict_ext  else fecha_row <= pd.to_datetime(fecha)
                if cut_ext:
                    total += (dep - ret) * fx
                tipo = row.get('Tipo', np.nan)
                if pd.notna(tipo):
                    cut_bond = fecha_row < pd.to_datetime(fecha) if strict_bond else fecha_row <= pd.to_datetime(fecha)
                    if cut_bond:
                        monto = _get_monto(row, moneda, fx_rates)
                        total += -monto if str(tipo).strip() == 'Compra' else monto
            return total

        if has_cash:
            # cash_inicio: depósitos/retiros ≤ fecha_inicio (mismo día = capital inicial),
            #              bonos < fecha_inicio (consistente con bond table).
            cash_inicio = _actual_cash(ops_cash, fecha_inicio, strict_bond=True,  strict_ext=False)
            cash_fin    = _actual_cash(ops_cash, fecha_fin,    strict_bond=False, strict_ext=False)
            # Flujos externos ESTRICTAMENTE después de fecha_inicio (evita doble-contar
            # depósitos del día de inicio que ya están en cash_inicio).
            ops_flujos = ops_cash[
                (ops_cash['Fecha'] >  pd.to_datetime(fecha_inicio)) &
                (ops_cash['Fecha'] <= pd.to_datetime(fecha_fin))
            ]
            flujos_netos = 0.0
            cash_flows_md = []  # flujos datados para Modified Dietz cash
            for _, row in ops_flujos.iterrows():
                if pd.notna(row.get(col_dep, np.nan)) or pd.notna(row.get(col_ret, np.nan)):
                    dep = row[col_dep] if pd.notna(row.get(col_dep, np.nan)) else 0.0
                    ret = row[col_ret] if pd.notna(row.get(col_ret, np.nan)) else 0.0
                    fx  = _get_fx(fx_rates, row['Fecha']) if moneda == 'ARS' else 1.0
                    net = (dep - ret) * fx
                    flujos_netos += net
                    if abs(net) > 1e-9:
                        cash_flows_md.append((row['Fecha'], net))
        else:
            cash_inicio = cash_fin = flujos_netos = 0.0
            cash_flows_md = []
            st.caption("ℹ️ Sin columnas de cash (Deposito / Retiro) en el Excel — valores de cash en $0.")

        titulos_inicio      = evolution_df['_Valor Inicio Real'].sum()
        titulos_fin         = evolution_df['Valor Actual'].sum()
        valor_inicial_total = titulos_inicio + cash_inicio
        valor_final_total   = titulos_fin    + cash_fin
        ganancia_cash       = valor_final_total - valor_inicial_total - flujos_netos
        # Modified Dietz para retorno incluyendo cash (pondera flujos externos por tiempo)
        pct_cash = _modified_dietz_pct(valor_inicial_total, valor_final_total,
                                        cash_flows_md, fecha_inicio, fecha_fin)
        pct_str_cash        = f"({'▼' if pct_cash < 0 else '▲'} {abs(pct_cash):.1f}%)"

        _render_summary_panel(
            base_items=[
                ("Valor Inicial (Tít. + Cash)", _fmt_money(valor_inicial_total, moneda)),
                ("Flujos Netos", _fmt_money(flujos_netos, moneda)),
                ("Valor Final Títulos", _fmt_money(titulos_fin, moneda)),
                ("Valor Final Cash", _fmt_money(cash_fin, moneda)),
            ],
            total_label="Resultado",
            total_value=_fmt_money(ganancia_cash, moneda),
            total_sub=pct_str_cash,
        )
        st.markdown("<div style='height:1.25rem;'></div>", unsafe_allow_html=True)

        st.caption(
            "ℹ️ Los retornos (%) se calculan con Modified Dietz: pondera cada flujo "
            "por el tiempo que estuvo invertido en el período, evitando distorsiones "
            "por compras/ventas cercanas al inicio o fin del rango."
        )

        # ── Gráfico: Valor Total vs. Neto Invertido ───────────────────────────
        try:
            from collections import defaultdict

            ops_sorted_g = ops_cash.dropna(subset=['Fecha']).sort_values('Fecha')

            # Precios enriquecidos con live prices
            precios_g = precios.copy()
            if live_prices:
                today_g = pd.Timestamp.today().normalize()
                rows_live = [{'Activo': a, 'Fecha': today_g, 'Precio': float(p)}
                             for a, p in live_prices.items() if pd.notna(p)]
                if rows_live:
                    precios_g = pd.concat([precios_g, pd.DataFrame(rows_live)]) \
                                  .drop_duplicates(subset=['Activo', 'Fecha'], keep='last')

            # Fechas del gráfico: union precios + transacciones en el rango
            fi_g = pd.to_datetime(fecha_inicio)
            ff_g = pd.to_datetime(fecha_fin)
            price_dates_g = precios_g[(precios_g['Fecha'] >= fi_g) & (precios_g['Fecha'] <= ff_g)]['Fecha'].tolist()
            tx_dates_g    = ops_sorted_g[(ops_sorted_g['Fecha'] >= fi_g) & (ops_sorted_g['Fecha'] <= ff_g)]['Fecha'].tolist()
            chart_dates_g = sorted(set(price_dates_g) | set(tx_dates_g))
            if not chart_dates_g:
                chart_dates_g = [fi_g, ff_g]

            # Step function: holdings acumulados por activo
            cum_h_g = defaultdict(float)
            h_steps_g = defaultdict(list)
            for _, row in ops_sorted_g.iterrows():
                tipo = row.get('Tipo', np.nan)
                asset = row.get('Activo', np.nan)
                if pd.isna(tipo) or pd.isna(asset):
                    continue
                t = str(tipo).strip()
                qty = float(row.get('Cantidad', 0) or 0)
                if t == 'Compra':
                    cum_h_g[asset] += qty
                elif t == 'Venta':
                    cum_h_g[asset] -= qty
                h_steps_g[asset].append((row['Fecha'], cum_h_g[asset]))

            h_dfs_g = {
                a: pd.DataFrame(steps, columns=['Fecha', 'H'])
                         .set_index('Fecha').groupby(level=0).last()
                for a, steps in h_steps_g.items()
            }

            def _h_at(asset, d):
                df = h_dfs_g.get(asset)
                if df is None or df.empty:
                    return 0.0
                r = df[df.index <= d]
                return float(r.iloc[-1]['H']) if not r.empty else 0.0

            # Step function: cash acumulado
            cash_cum_g = 0.0
            cash_steps_g = []
            for _, row in ops_sorted_g.iterrows():
                d = row['Fecha']
                if pd.isna(d):
                    continue
                fx = _get_fx(fx_rates, d) if moneda == 'ARS' else 1.0
                dep = float(row[col_dep]) if has_cash and col_dep and pd.notna(row.get(col_dep, np.nan)) else 0.0
                ret = float(row[col_ret]) if has_cash and col_ret and pd.notna(row.get(col_ret, np.nan)) else 0.0
                cash_cum_g += (dep - ret) * fx
                tipo = row.get('Tipo', np.nan)
                if pd.notna(tipo):
                    monto = _get_monto(row, moneda, fx_rates)
                    cash_cum_g += -monto if str(tipo).strip() == 'Compra' else monto
                cash_steps_g.append((d, cash_cum_g))

            cash_sdf_g = (pd.DataFrame(cash_steps_g, columns=['Fecha', 'Cash'])
                            .set_index('Fecha').groupby(level=0).last()
                          if cash_steps_g else pd.DataFrame(columns=['Cash']))

            def _cash_at_g(d):
                r = cash_sdf_g[cash_sdf_g.index <= d]
                return float(r.iloc[-1]['Cash']) if not r.empty else 0.0

            # "Invertido" del gráfico: parte del valor inicial del período y
            # luego solo ajusta por flujos externos posteriores al inicio.
            ni_cum_g = float(valor_inicial_total)
            ni_steps_g = [(fi_g, ni_cum_g)]
            for _, row in ops_sorted_g.iterrows():
                d = row['Fecha']
                if not has_cash or pd.isna(d) or d <= fi_g:
                    continue
                dep = float(row[col_dep]) if pd.notna(row.get(col_dep, np.nan)) else 0.0
                ret = float(row[col_ret]) if pd.notna(row.get(col_ret, np.nan)) else 0.0
                if dep != 0 or ret != 0:
                    fx = _get_fx(fx_rates, d) if moneda == 'ARS' else 1.0
                    ni_cum_g += (dep - ret) * fx
                    ni_steps_g.append((d, ni_cum_g))

            ni_sdf_g = (pd.DataFrame(ni_steps_g, columns=['Fecha', 'NI'])
                          .set_index('Fecha').groupby(level=0).last()
                        if ni_steps_g else pd.DataFrame(columns=['NI']))

            def _ni_at_g(d):
                r = ni_sdf_g[ni_sdf_g.index <= d]
                return float(r.iloc[-1]['NI']) if not r.empty else 0.0

            # Construir serie temporal
            assets_g = [a for a in ops_cash['Activo'].dropna().unique() if pd.notna(a)]
            chart_rows_g = []
            for d in chart_dates_g:
                bv = 0.0
                for asset in assets_g:
                    h = _h_at(asset, d)
                    if h > 0:
                        ap = precios_g[(precios_g['Activo'] == asset) & (precios_g['Fecha'] <= d)]
                        if not ap.empty:
                            price = float(ap.iloc[-1]['Precio'])
                            if moneda == 'ARS':
                                price *= _get_fx(fx_rates, d)
                            bv += h * price
                chart_rows_g.append({
                    'Fecha':          d,
                    'Valor Total':    bv + _cash_at_g(d),
                    'Invertido':      _ni_at_g(d),
                })

            df_chart = pd.DataFrame(chart_rows_g)
            lbl_y = 'ARS' if moneda == 'ARS' else 'USD'

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_chart['Fecha'], y=df_chart['Invertido'],
                fill='tozeroy', name='Invertido',
                mode='lines', line=dict(color='#93C5FD', width=1.5),
                fillcolor='rgba(147, 197, 253, 0.25)',
            ))
            fig.add_trace(go.Scatter(
                x=df_chart['Fecha'], y=df_chart['Valor Total'],
                name='Valor Total (tít+cash)',
                mode='lines', line=dict(color='#1A4B9B', width=2.5),
            ))
            fig.update_layout(
                hovermode='x unified',
                xaxis_title=None,
                yaxis_title=lbl_y,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
                height=320,
                margin=dict(l=0, r=10, t=30, b=0),
                plot_bgcolor='#F0F2F6',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.caption(f"⚠️ No se pudo generar el gráfico: {e}")


    # ── Detalle por activo ─────────────────────────────────────────────────────
    if not evolution_df.empty:
        st.markdown("---")
        _section_header("Análisis Detallado de Evolución por Activo")
        activos_disponibles = ["Seleccionar"] + evolution_df['Activo'].tolist()
        activo_sel = st.selectbox(
            "Seleccionar activo para análisis detallado:",
            activos_disponibles,
            index=0,
        )
        if activo_sel and activo_sel != "Seleccionar":
            mostrar_analisis_detallado_activo(
                operaciones, precios, activo_sel, fecha_inicio, fecha_fin,
                moneda=moneda, fx_rates=fx_rates,
                live_prices=live_prices, live_fx=live_fx
            )

    # ══════════════════════════════════════════
    # UPLOADER — al pie de la página
    # ══════════════════════════════════════════
    st.markdown("---")
    with st.expander("📁 Cargar archivo Excel diferente"):
        uploaded_file = st.file_uploader(
            "Arrastrá un .xlsx o hacé click para seleccionar",
            type=['xlsx', 'xls'],
            label_visibility='collapsed'
        )
        if uploaded_file is not None:
            new_bytes = uploaded_file.getbuffer().tobytes()
            if new_bytes != st.session_state.get('upload_bytes', b''):
                st.session_state.upload_bytes = new_bytes
                if 'upload_id' not in st.session_state:
                    st.session_state.upload_id = uuid.uuid4().hex[:12]
                st.rerun()
        if st.session_state.get('upload_bytes'):
            st.success(f"✅ Usando archivo cargado.")
            if st.button("↩ Volver al archivo original"):
                st.session_state.upload_bytes = None
                st.rerun()


if __name__ == "__main__":
    main()
