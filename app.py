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

/* ══════════════════════════════════════════════
   TABLAS DE PORTAFOLIO (HTML renderizado)
══════════════════════════════════════════════ */
.ptable { width:100%; border-collapse:collapse; font-size:13px; font-family:'Inter',sans-serif; margin-bottom:0.5rem; }
.ptable th { padding:8px 14px; border-bottom:2px solid #e2e8f0; color:#6b7280; font-size:11px; text-transform:uppercase; letter-spacing:0.05em; font-weight:600; background:#f8fafc; white-space:nowrap; }
.ptable td { padding:8px 14px; border-bottom:1px solid #f1f5f9; color:#1B2333; white-space:nowrap; }
.ptable tr:last-child td { border-bottom:none; }
.ptable tr:hover td { background:#f8fafc; }
.ptable .r { text-align:right; }
.ptable .l { text-align:left; }

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
# Carga modo Resumen (port dummy.xlsx)
# ─────────────────────────────────────────────
def load_data_resumen(filename='port dummy.xlsx'):
    """
    Carga datos del formato 'port dummy.xlsx' (modo Resumen).

    Hoja Trades (header en fila 1, fila 0 vacía):
      A=Asset, B=Date, C=Kind, D=Trade, E=Asset Class, F=Currency,
      G=Sector, H=Type, I=Law, J=Settlement, K=AcBivo (Activo),
      L=Nominal, M=Price, N=%Amort, O=Monto Amt/Cpn/Div, P=Value

    Mapeo a operaciones_mapped:
      Fecha      ← B (Date)
      Tipo       ← D (Trade: Compra/Venta/…)
      Activo     ← A (Asset)
      Cantidad   ← L (Nominal)
      Precio ARS ← M (Price)   — precios en ARS
      Monto ARS  ← P (Value)   — montos en ARS
      Precio/Monto USD ← NaN   (no disponible)

    Hoja Precios: mismo formato que operaciones.xlsx (fila 0 = tickers, filas 1+ = fecha+precios).
    Los precios se almacenan como 'Precio' (en ARS). fx_rates se fija a 1.0 para que
    los cálculos en modo ARS devuelvan el precio directamente.
    """
    try:
        # ── Trades ───────────────────────────────────────────────────────────
        trades_raw = pd.read_excel(filename, sheet_name='Trades', header=1)

        operaciones_mapped = pd.DataFrame()
        operaciones_mapped['Fecha']      = pd.to_datetime(trades_raw['Date'], errors='coerce')
        operaciones_mapped['Tipo']       = trades_raw['Trade'].astype(str).str.strip().str.title()
        operaciones_mapped['Activo']     = trades_raw['Asset'].astype(str).str.strip()
        # Nominal puede venir negativo en Ventas/Amortizaciones; normalizamos con abs()
        # porque el signo lo determina el Tipo (Compra/Venta) en las funciones de cálculo.
        operaciones_mapped['Cantidad']   = pd.to_numeric(trades_raw['Nominal'], errors='coerce').abs()
        operaciones_mapped['Precio']     = np.nan
        operaciones_mapped['Monto']      = np.nan
        operaciones_mapped['Precio ARS'] = pd.to_numeric(trades_raw['Price'], errors='coerce')
        operaciones_mapped['Monto ARS']  = pd.to_numeric(trades_raw['Value'], errors='coerce').abs()

        # Filtrar filas sin fecha, activo válido, o cantidad cero
        operaciones_mapped = operaciones_mapped[
            operaciones_mapped['Fecha'].notna() &
            operaciones_mapped['Activo'].notna() &
            (operaciones_mapped['Activo'] != 'nan') &
            (operaciones_mapped['Cantidad'].fillna(0) != 0)
        ].reset_index(drop=True)

        # ── Precios ───────────────────────────────────────────────────────────
        precios_raw = pd.read_excel(filename, sheet_name='Precios', header=None)

        # Fila 0 = tickers; fila 1+ = fecha + valores
        tickers_raw = precios_raw.iloc[0].tolist()

        # Mapear ticker limpio → índice de columna (ignorar NaN y duplicados)
        asset_cols = {}
        for i, t in enumerate(tickers_raw[1:], start=1):
            if pd.isna(t):
                continue
            ticker = str(t).strip()
            if not ticker or ticker == 'nan':
                continue
            if ticker not in asset_cols:
                asset_cols[ticker] = i

        # Construir precios_long fila a fila (evita melt con columnas duplicadas/NaN)
        # Las filas de datos van desde la fila 1 del raw (fila 0 son tickers)
        raw_date_vals = precios_raw.iloc[1:, 0].reset_index(drop=True)  # valores sin parsear
        precios_rows = []
        live_prices  = {}
        fechas_validas = []

        for row_i, raw_val in enumerate(raw_date_vals):
            raw_str = str(raw_val).strip() if pd.notna(raw_val) else ''

            # Detectar fila "Precio Actual" → live prices (no histórico)
            if raw_str.lower() == 'precio actual':
                raw_row = precios_raw.iloc[row_i + 1]  # +1 porque fila 0 son tickers
                for ticker, col_idx in asset_cols.items():
                    try:
                        val = float(raw_row.iloc[col_idx])
                    except (TypeError, ValueError):
                        continue
                    if not np.isnan(val):
                        live_prices[ticker] = val
                continue  # no agregar al histórico

            # Intentar parsear como fecha
            fecha = pd.to_datetime(raw_val, errors='coerce')
            if pd.isna(fecha):
                continue

            fechas_validas.append(fecha)
            raw_row = precios_raw.iloc[row_i + 1]  # +1 porque fila 0 son tickers
            for ticker, col_idx in asset_cols.items():
                try:
                    val = float(raw_row.iloc[col_idx])
                except (TypeError, ValueError):
                    continue
                if np.isnan(val):
                    continue
                precios_rows.append({'Fecha': fecha, 'Activo': ticker, 'Precio': val})

        precios_long = (
            pd.DataFrame(precios_rows)
            if precios_rows
            else pd.DataFrame(columns=['Fecha', 'Activo', 'Precio'])
        )

        # fx_rates = 1.0 en todas las fechas (precios ya en ARS, sin conversión)
        fx_rates = pd.DataFrame({'Fecha': fechas_validas, 'ARS': 1.0})

        live_fx = 1.0

        return operaciones_mapped, precios_long, fx_rates, live_prices, live_fx

    except FileNotFoundError:
        st.error(f"No se encontró '{filename}'. Asegurate de que esté en la carpeta del proyecto.")
        return None, None, None, {}, None
    except Exception as e:
        st.error(f"Error al cargar Resumen: {e}")
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
    Fallback: si Monto ARS es NaN/0, convierte Monto USD × TC de cierre del día.
    Si ambos son NaN/0 (modo Resumen sin Value), retorna 0.0 en lugar de NaN.
    """
    if moneda == 'ARS':
        monto_ars = op.get('Monto ARS', np.nan)
        if pd.notna(monto_ars) and monto_ars != 0:
            return float(monto_ars)
        # Fallback: TC de cierre como aproximación
        monto_usd = op.get('Monto', np.nan)
        if pd.isna(monto_usd):
            return 0.0  # modo Resumen sin Value disponible
        fx = _get_fx(fx_rates, op['Fecha'])
        return float(monto_usd) * fx
    monto_usd = op.get('Monto', np.nan)
    return float(monto_usd) if pd.notna(monto_usd) else 0.0


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
        costo_unit_promedio = 0.0
        total_amort         = 0
        total_cupones       = 0
        total_dividendos    = 0

        for _, op in ops.iterrows():
            tipo = op['Tipo'].strip()
            monto = _get_monto(op, moneda, fx_rates)
            if tipo == 'Compra':
                costo_prev          = current_nominals * costo_unit_promedio
                current_nominals   += op['Cantidad']
                costo_unit_promedio = (costo_prev + monto) / current_nominals if current_nominals else 0.0
            elif tipo == 'Venta':
                current_nominals -= op['Cantidad']
            else:
                categoria = _clasificar_operacion(tipo)
                if categoria == 'amortizacion':
                    total_amort += monto
                    # En formato Resumen la amortización incluye Cantidad explícita
                    # (el nominal restituido). En Excel Propio Cantidad es NaN → no aplica.
                    qty = op.get('Cantidad', np.nan)
                    if pd.notna(qty) and qty > 0:
                        current_nominals = max(current_nominals - qty, 0)
                elif categoria == 'cupon':
                    total_cupones    += monto
                elif categoria == 'dividendo':
                    total_dividendos += monto

        if current_nominals <= 0:
            continue

        costo_posicion = current_nominals * costo_unit_promedio
        current_price  = _get_current_price(asset, asset_prices, moneda, fx_rates,
                                            live_prices, live_fx)
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
                qty = op.get('Cantidad', np.nan)
                if _clasificar_operacion(tipo) == 'amortizacion' and pd.notna(qty) and qty > 0:
                    nom_inicio = max(nom_inicio - qty, 0)

        # Omitir activos sin actividad relevante en el período
        if nom_inicio <= 0 and ops_en_rango.empty:
            continue

        # Excluir activos cuya amortización final cae exactamente en fecha_inicio:
        # su posición efectiva el primer día del período ya es cero.
        # Solo se excluye si tampoco hay operaciones posteriores en el rango.
        ops_on_inicio_day   = ops_en_rango[ops_en_rango['Fecha'] == pd.to_datetime(fecha_inicio)]
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

        for _, op in ops_en_rango.iterrows():
            tipo = op['Tipo'].strip()
            monto = _get_monto(op, moneda, fx_rates)
            if tipo == 'Compra':
                nom_fin            += op['Cantidad']
                compras_en_periodo += monto
            elif tipo == 'Venta':
                nom_fin   -= op['Cantidad']
                sales_fin += monto
            elif _clasificar_operacion(tipo):
                divcup_fin += monto
                qty = op.get('Cantidad', np.nan)
                if _clasificar_operacion(tipo) == 'amortizacion' and pd.notna(qty) and qty > 0:
                    nom_fin = max(nom_fin - qty, 0)

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
        precio_fin    = _get_current_price(asset, asset_prices, moneda, fx_rates,
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

        # Para activos comprados dentro del período (nom_inicio = 0), mostrar el costo
        # de compra como "Valor al Inicio" en lugar de 0. La ganancia se calcula igual
        # porque internamente valor_inicio = 0 para esos activos.
        valor_inicio_display = valor_inicio if nom_inicio > 0 else compras_en_periodo

        # "Compras Adicionales" = compras realizadas sobre una posición pre-existente.
        # Para activos nuevos (nom_inicio = 0) es 0 porque su inversión inicial ya
        # queda capturada en Valor al Inicio (evita doble conteo en la tarjeta Flujos).
        compras_adicionales = compras_en_periodo if nom_inicio > 0 else 0

        evolution_data.append({
            'Activo':               asset,
            'Nominales':            nom_fin,
            'Precio Actual':        precio_fin,
            'Valor Actual':         valor_fin,
            'Valor al Inicio':      valor_inicio_display,
            'Compras':              compras_en_periodo,
            'Compras Adicionales':  compras_adicionales,
            'Ventas':               ventas_en_periodo,
            'Amort / Cup / Div':    div_cup_en_periodo,
            'Ganancia Total':       ganancia_total,
        })

    return pd.DataFrame(evolution_data)


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
        precio_fin = _get_current_price(activo, ap, moneda, fx_rates, live_prices, live_fx)
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
        _render_df(display, left_cols=('Fecha', 'Operación'))

    else:
        st.info(f"No hay operaciones para {activo} en el período seleccionado.")


# ─────────────────────────────────────────────
# Helpers de formato
# ─────────────────────────────────────────────
def _fmt_money(x, moneda='USD'):
    """Formatea un monto monetario según la moneda.

    USD: dos decimales (ej: $1,234.56)
    ARS: en millones con un decimal (ej: $1,234.5M)
    Cero: muestra "-"
    """
    if not pd.notna(x) or x == 0:
        return "-"
    if moneda == 'ARS':
        return f"${x / 1_000_000:,.1f}M"
    return f"${x:,.2f}"


def _fmt_price(x, moneda='USD'):
    """Formatea un precio según la moneda (ambos con 2 decimales)."""
    if not pd.notna(x) or x == 0:
        return "-"
    return f"${x:,.2f}"


def _fmt_number(x):
    if not pd.notna(x) or x == 0:
        return "-"
    return f"{x:,.0f}"


def _render_df(df, left_cols=('Activo',)):
    """Renderiza un DataFrame como tabla HTML con alineación derecha en columnas numéricas.
    Si la última fila tiene 'Activo'=='TOTAL' se renderiza en negrita con fondo gris."""
    html = '<table class="ptable"><thead><tr>'
    for col in df.columns:
        a = 'l' if col in left_cols else 'r'
        html += f'<th class="{a}">{col}</th>'
    html += '</tr></thead><tbody>'
    rows = list(df.iterrows())
    for i, (_, row) in enumerate(rows):
        is_total = (i == len(rows) - 1 and str(row.get('Activo', '')).strip() == 'TOTAL')
        row_style = ' style="background:#F0F2F6;font-weight:700;border-top:2px solid #CBD5E1;"' if is_total else ''
        html += f'<tr{row_style}>'
        for col in df.columns:
            a = 'l' if col in left_cols else 'r'
            html += f'<td class="{a}">{row[col]}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)


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
        f'<div style="background:#FFFFFF;border-radius:10px;padding:1rem 1.1rem 0.9rem;border:1px solid #E5E7EB;box-shadow:0 1px 4px rgba(0,0,0,0.06);height:90px;">'
        f'<div style="font-size:0.68rem;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:0.55px;margin-bottom:6px;">{label}</div>'
        f'<div style="font-size:1.25rem;font-weight:700;color:#1B2333;line-height:1.25;word-break:break-word;">{value_str}</div>'
        f'{delta_html}'
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

    # ── Esta rama usa siempre port dummy.xlsx en ARS ──────────────────────────
    vista  = 'Resumen'
    moneda = 'ARS'

    # ── Fecha actual fija = hoy ────────────────────────────────────────────────
    fecha_actual = datetime.now().date()

    # ── Carga de datos ─────────────────────────────────────────────────────────
    operaciones, precios, fx_rates, live_prices, live_fx = load_data_resumen('port dummy.xlsx')

    if operaciones is None or precios is None:
        st.error("Error al cargar los datos. Verifica que 'port dummy.xlsx' esté en la carpeta.")
        return

    lbl_moneda = 'ARS'

    # ── Hero card ──────────────────────────────────────────────────────────────
    fecha_str = _fecha_es(fecha_actual)
    st.markdown(
        f'<div style="background:#1A4B9B;border-radius:12px;padding:1.2rem 1.8rem;'
        f'margin-bottom:0.5rem;display:flex;align-items:center;justify-content:space-between;">'
        f'<div>'
        f'<div style="font-size:1.4rem;font-weight:700;color:#FFFFFF;">Análisis de Portafolio</div>'
        f'<div style="font-size:0.82rem;color:rgba(255,255,255,0.75);margin-top:2px;">{fecha_str}</div>'
        f'</div>'
        f'<div style="font-size:0.78rem;font-weight:500;color:#FFFFFF;'
        f'background:rgba(255,255,255,0.12);padding:4px 12px;'
        f'border-radius:20px;border:1px solid rgba(255,255,255,0.35);">ARS</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ══════════════════════════════════════════
    # PESTAÑAS
    # ══════════════════════════════════════════
    tab1, tab2, tab3 = st.tabs([
        "Composición Actual",
        "Evolución de la Cartera",
        "Análisis por Activo",
    ])

    with tab1:
        portfolio_df = calculate_current_portfolio(
            operaciones, precios, fecha_actual, moneda=moneda, fx_rates=fx_rates,
            live_prices=live_prices, live_fx=live_fx
        )

        if portfolio_df.empty:
            st.warning("No hay activos con nominales positivos en la fecha seleccionada.")
        else:
            total_valor_mercado = portfolio_df['_Valor Actual'].sum()
            total_costo         = portfolio_df['Costo'].sum()
            total_amort         = portfolio_df['Amortizaciones'].sum()
            total_cup           = portfolio_df['Cupones'].sum()
            total_div           = portfolio_df['Dividendos'].sum()
            total_ganancia_r    = total_amort + total_cup + total_div
            total_ganancia_no_r = portfolio_df['Ganancias no Realizadas'].sum()
            pct_no_r            = (total_ganancia_no_r / total_costo * 100) if total_costo > 0 else 0

            total_ganancia = total_ganancia_r + total_ganancia_no_r
            pct_total      = (total_ganancia / total_costo * 100) if total_costo > 0 else 0
            pct_str        = f"{'▼' if pct_total < 0 else '▲'} {abs(pct_total):.1f}%"
            c1, c2, c3, c4 = st.columns(4)
            with c1: _metric("Valor de Mercado",  _fmt_money(total_valor_mercado, moneda))
            with c2: _metric("Costo Total",        _fmt_money(total_costo, moneda))
            with c3: _metric("Amort / Cup / Div",  _fmt_money(total_amort + total_cup + total_div, moneda))
            with c4: _metric("Ganancia Total",      _fmt_money(total_ganancia, moneda), sub_str=pct_str)
            st.markdown('<div style="margin-bottom:1rem;"></div>', unsafe_allow_html=True)

            # ── Diferencia diaria y mensual por activo (en valor, no %) ──────
            precios_hist = precios.copy()
            precios_hist['Fecha'] = pd.to_datetime(precios_hist['Fecha'])
            hoy = pd.Timestamp(fecha_actual)
            inicio_mes = hoy.replace(day=1)

            def _diff_diaria(asset, nom):
                ap = precios_hist[precios_hist['Activo'] == asset].sort_values('Fecha')
                r_hoy = ap[ap['Fecha'] <= hoy]
                if r_hoy.empty:
                    return np.nan
                p_hoy = float(r_hoy.iloc[-1]['Precio'])
                fecha_hoy_precio = r_hoy.iloc[-1]['Fecha']
                r_prev = ap[ap['Fecha'] < fecha_hoy_precio]
                if r_prev.empty:
                    return np.nan
                p_prev = float(r_prev.iloc[-1]['Precio'])
                return (p_hoy - p_prev) * nom

            def _diff_mensual(asset, nom):
                ap = precios_hist[precios_hist['Activo'] == asset].sort_values('Fecha')
                r_hoy = ap[ap['Fecha'] <= hoy]
                if r_hoy.empty:
                    return np.nan
                p_hoy = float(r_hoy.iloc[-1]['Precio'])
                r_mes = ap[ap['Fecha'] < inicio_mes]
                if r_mes.empty:
                    return np.nan
                p_mes = float(r_mes.iloc[-1]['Precio'])
                return (p_hoy - p_mes) * nom

            def _fmt_diff(x):
                if not pd.notna(x) or x == 0:
                    return '-'
                arrow = '▼' if x < 0 else '▲'
                return f"{arrow} {_fmt_money(abs(x), moneda)}"

            cols_display = [
                'Activo', 'Nominales', 'Precio Actual', 'Valor Actual', 'Costo',
                'Amortizaciones', 'Cupones', 'Dividendos', 'Ganancia Total'
            ]
            display_df = portfolio_df.rename(columns={'_Valor Actual': 'Valor Actual'})[cols_display] \
                             .sort_values('Nominales', ascending=False).reset_index(drop=True).copy()

            display_df['Amort / Cup / Div'] = display_df['Amortizaciones'] + display_df['Cupones'] + display_df['Dividendos']
            nom_raw = portfolio_df.rename(columns={'_Valor Actual': 'Valor Actual'}) \
                          .sort_values('Nominales', ascending=False).reset_index(drop=True)['Nominales']
            display_df['_nom'] = nom_raw.values
            display_df['Dif. Diaria']  = display_df.apply(lambda r: _diff_diaria(r['Activo'], r['_nom']), axis=1)
            display_df['Dif. Mensual'] = display_df.apply(lambda r: _diff_mensual(r['Activo'], r['_nom']), axis=1)

            tot_valor_actual = display_df['Valor Actual'].sum()
            tot_costo        = display_df['Costo'].sum()
            tot_amort        = display_df['Amort / Cup / Div'].sum()
            tot_dif_dia      = display_df['Dif. Diaria'].sum()
            tot_dif_mes      = display_df['Dif. Mensual'].sum()
            tot_ganancia     = display_df['Ganancia Total'].sum()

            display_df['Nominales']         = display_df['Nominales'].apply(_fmt_number)
            display_df['Precio Actual']     = display_df['Precio Actual'].apply(lambda x: _fmt_price(x, moneda))
            display_df['Valor Actual']      = display_df['Valor Actual'].apply(lambda x: _fmt_money(x, moneda))
            display_df['Costo']             = display_df['Costo'].apply(lambda x: _fmt_money(x, moneda))
            display_df['Amort / Cup / Div'] = display_df['Amort / Cup / Div'].apply(lambda x: _fmt_money(x, moneda))
            display_df['Ganancia Total']    = display_df['Ganancia Total'].apply(lambda x: _fmt_money(x, moneda))
            display_df['Dif. Diaria']       = display_df['Dif. Diaria'].apply(_fmt_diff)
            display_df['Dif. Mensual']      = display_df['Dif. Mensual'].apply(_fmt_diff)

            final_cols = ['Activo', 'Nominales', 'Precio Actual', 'Valor Actual',
                          'Costo', 'Amort / Cup / Div', 'Dif. Diaria', 'Dif. Mensual', 'Ganancia Total']
            display_df = display_df[final_cols]

            total_row = pd.DataFrame([{
                'Activo': 'TOTAL', 'Nominales': '-', 'Precio Actual': '-',
                'Valor Actual':      _fmt_money(tot_valor_actual, moneda),
                'Costo':             _fmt_money(tot_costo, moneda),
                'Amort / Cup / Div': _fmt_money(tot_amort, moneda),
                'Dif. Diaria':       _fmt_diff(tot_dif_dia),
                'Dif. Mensual':      _fmt_diff(tot_dif_mes),
                'Ganancia Total':    _fmt_money(tot_ganancia, moneda),
            }])
            display_df = pd.concat([display_df, total_row], ignore_index=True)
            _render_df(display_df)

            if '_nota' in portfolio_df.columns:
                for nota in portfolio_df[portfolio_df['_nota'] != '']['_nota']:
                    st.caption(nota)

    with tab2:
        # ── helpers de precios para dif diaria/mensual ─────────────────────────
        _ph = precios.copy()
        _ph['Fecha'] = pd.to_datetime(_ph['Fecha'])
        _hoy   = pd.Timestamp(datetime.now().date())
        _imes  = _hoy.replace(day=1)

        def _dif_dia_nom(asset, nom):
            ap = _ph[_ph['Activo'] == asset].sort_values('Fecha')
            rh = ap[ap['Fecha'] <= _hoy]
            if rh.empty: return np.nan
            p_hoy = float(rh.iloc[-1]['Precio'])
            rp = ap[ap['Fecha'] < rh.iloc[-1]['Fecha']]
            if rp.empty: return np.nan
            return (p_hoy - float(rp.iloc[-1]['Precio'])) * nom

        def _dif_mes_nom(asset, nom):
            ap = _ph[_ph['Activo'] == asset].sort_values('Fecha')
            rh = ap[ap['Fecha'] <= _hoy]
            if rh.empty: return np.nan
            p_hoy = float(rh.iloc[-1]['Precio'])
            rm = ap[ap['Fecha'] < _imes]
            if rm.empty: return np.nan
            return (p_hoy - float(rm.iloc[-1]['Precio'])) * nom

        def _fmt_diff(x):
            if not pd.notna(x) or x == 0: return '-'
            return f"{'▼' if x < 0 else '▲'} {_fmt_money(abs(x), moneda)}"

        def _render_evo_block(df, with_diffs=False):
            """Renderiza cards + tabla para un DataFrame de evolución."""
            evo_disp = df.sort_values('Nominales', ascending=False).reset_index(drop=True).copy()

            # totales numéricos antes de formatear
            tot_val  = evo_disp['Valor Actual'].sum()
            tot_vi   = evo_disp['Valor al Inicio'].sum()
            tot_comp = evo_disp['Compras'].sum()
            tot_ven  = evo_disp['Ventas'].sum()
            tot_acd  = evo_disp['Amort / Cup / Div'].sum()
            tot_gan  = evo_disp['Ganancia Total'].sum()
            tot_neto = tot_comp - tot_ven

            if with_diffs:
                evo_disp['Dif. Diaria']  = evo_disp.apply(
                    lambda r: _dif_dia_nom(r['Activo'], r['Nominales']), axis=1
                )
                # Dif. Mensual = P&L real del período (precio ponderado por timing de cada lote):
                # Valor Actual − Valor al Inicio − Flujos netos del activo
                # Para activos existentes: gana sobre pos. original + gana sobre compras desde adquisición
                # Para activos nuevos:     gana desde precio de compra (Flujos neto = 0)
                flujos_neto_activo = (
                    evo_disp['Compras Adicionales']
                    - evo_disp['Ventas']
                    - evo_disp['Amort / Cup / Div']
                )
                evo_disp['Dif. Mensual'] = (
                    evo_disp['Valor Actual']
                    - evo_disp['Valor al Inicio']
                    - flujos_neto_activo
                )
                tot_dif_dia = evo_disp['Dif. Diaria'].sum()
                tot_dif_mes = evo_disp['Dif. Mensual'].sum()
                # Cards: Flujos = compras adicionales (sobre posición pre-existente) − ventas − amort
                # Las compras de activos nuevos ya están en Valor al Inicio → no se suman de nuevo.
                tot_flujos = evo_disp['Compras Adicionales'].sum() - tot_ven - tot_acd
                e1, e2, e3, e4, e5 = st.columns(5)
                with e1: _metric("Valor Total",        _fmt_money(tot_val, moneda))
                with e2: _metric("Valor al Inicio",    _fmt_money(tot_vi, moneda))
                with e3: _metric("Flujos",             _fmt_money(tot_flujos, moneda))
                with e4: _metric("Diferencia Diaria",  _fmt_diff(tot_dif_dia))
                with e5: _metric("Diferencia Mensual", _fmt_diff(tot_dif_mes))
            else:
                flujos = tot_ven + tot_acd
                e1, e2, e3, e4, e5 = st.columns(5)
                with e1: _metric("Valor Total",     _fmt_money(tot_val, moneda))
                with e2: _metric("Valor al Inicio", _fmt_money(tot_vi, moneda))
                with e3: _metric("Compras",         _fmt_money(tot_comp, moneda))
                with e4: _metric("Ventas + Flujos", _fmt_money(flujos, moneda))
                with e5: _metric("Ganancia Total",  _fmt_money(tot_gan, moneda))
            st.markdown('<div style="margin-bottom:1rem;"></div>', unsafe_allow_html=True)

            # Fusionar Compras y Ventas en columna "Compras - Ventas" (antes de formatear)
            evo_disp['Compras - Ventas'] = evo_disp['Compras'] - evo_disp['Ventas']

            evo_disp['Nominales'] = evo_disp['Nominales'].apply(_fmt_number)
            for col in ['Precio Actual', 'Valor Actual', 'Valor al Inicio',
                        'Compras - Ventas', 'Amort / Cup / Div', 'Ganancia Total']:
                if col == 'Precio Actual':
                    evo_disp[col] = evo_disp[col].apply(lambda x: _fmt_price(x, moneda))
                else:
                    evo_disp[col] = evo_disp[col].apply(lambda x: _fmt_money(x, moneda))

            if with_diffs:
                evo_disp['Dif. Diaria']  = evo_disp['Dif. Diaria'].apply(_fmt_diff)
                evo_disp['Dif. Mensual'] = evo_disp['Dif. Mensual'].apply(_fmt_diff)
                final_cols = ['Activo', 'Nominales', 'Valor al Inicio', 'Compras - Ventas',
                              'Amort / Cup / Div', 'Precio Actual', 'Valor Actual',
                              'Dif. Diaria', 'Dif. Mensual']
                total_row = pd.DataFrame([{
                    'Activo': 'TOTAL', 'Nominales': '-', 'Valor al Inicio': _fmt_money(tot_vi, moneda),
                    'Compras - Ventas': _fmt_money(tot_neto, moneda),
                    'Amort / Cup / Div': _fmt_money(tot_acd, moneda), 'Precio Actual': '-',
                    'Valor Actual': _fmt_money(tot_val, moneda),
                    'Dif. Diaria': _fmt_diff(tot_dif_dia), 'Dif. Mensual': _fmt_diff(tot_dif_mes),
                }])
            else:
                final_cols = ['Activo', 'Nominales', 'Valor al Inicio', 'Compras - Ventas',
                              'Amort / Cup / Div', 'Precio Actual', 'Valor Actual', 'Ganancia Total']
                total_row = pd.DataFrame([{
                    'Activo': 'TOTAL', 'Nominales': '-', 'Valor al Inicio': _fmt_money(tot_vi, moneda),
                    'Compras - Ventas': _fmt_money(tot_neto, moneda),
                    'Amort / Cup / Div': _fmt_money(tot_acd, moneda), 'Precio Actual': '-',
                    'Valor Actual': _fmt_money(tot_val, moneda),
                    'Ganancia Total': _fmt_money(tot_gan, moneda),
                }])

            evo_disp = pd.concat([evo_disp[final_cols], total_row], ignore_index=True)
            _render_df(evo_disp)

        # ── Análisis Mensual (fechas fijas: último día mes anterior → hoy) ──────
        hoy_t2        = datetime.now().date()
        inicio_mes_t2 = hoy_t2.replace(day=1) - timedelta(days=1)   # último día del mes anterior
        _section_header("Análisis Mensual",
                         f"{inicio_mes_t2.strftime('%d/%m/%Y')} — {hoy_t2.strftime('%d/%m/%Y')}")
        evo_mes = calculate_portfolio_evolution(
            operaciones, precios, inicio_mes_t2, hoy_t2, moneda=moneda, fx_rates=fx_rates,
            live_prices=live_prices, live_fx=live_fx
        )
        if evo_mes.empty:
            st.info("Sin datos para el mes en curso.")
        else:
            _render_evo_block(evo_mes, with_diffs=True)

        st.markdown('<div style="margin-bottom:1.5rem;"></div>', unsafe_allow_html=True)

        # ── Selector de fechas ────────────────────────────────────────────────
        col_s2, col_i, col_f = st.columns([4, 1, 1])
        with col_s2:
            _section_header("Análisis de la Evolución de la Cartera")
        with col_i:
            fecha_inicio = st.date_input(
                "Inicio",
                value=datetime.now().date() - timedelta(days=365),
                help="Fecha de inicio del período"
            )
        with col_f:
            fecha_fin = st.date_input(
                "Fin",
                value=datetime.now().date(),
                help="Fecha de fin del período"
            )

        if fecha_inicio > fecha_fin:
            st.error("⚠️ La fecha de inicio no puede ser posterior a la fecha de fin.")
        else:
            evolution_df = calculate_portfolio_evolution(
                operaciones, precios, fecha_inicio, fecha_fin, moneda=moneda, fx_rates=fx_rates,
                live_prices=live_prices, live_fx=live_fx
            )
            if evolution_df.empty:
                st.warning("No hay datos de evolución para el rango de fechas seleccionado.")
            else:
                _render_evo_block(evolution_df)

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
                flujos_netos = sum(
                    ((row[col_dep] if pd.notna(row.get(col_dep, np.nan)) else 0.0) -
                     (row[col_ret] if pd.notna(row.get(col_ret, np.nan)) else 0.0)) *
                    (_get_fx(fx_rates, row['Fecha']) if moneda == 'ARS' else 1.0)
                    for _, row in ops_flujos.iterrows()
                    if pd.notna(row.get(col_dep, np.nan)) or pd.notna(row.get(col_ret, np.nan))
                )
            else:
                cash_inicio = cash_fin = flujos_netos = 0.0

            titulos_inicio      = evolution_df['Valor al Inicio'].sum()
            titulos_fin         = evolution_df['Valor Actual'].sum()
            valor_inicial_total = titulos_inicio + cash_inicio
            valor_final_total   = titulos_fin    + cash_fin
            ganancia_cash       = valor_final_total - valor_inicial_total - flujos_netos
            base_cash           = valor_inicial_total + max(flujos_netos, 0)
            pct_cash            = (ganancia_cash / base_cash * 100) if base_cash > 0 else 0
            pct_str_cash        = f"({'▼' if pct_cash < 0 else '▲'} {abs(pct_cash):.1f}%)"


            # ── Gráfico: Valor Total vs. Neto Invertido ───────────────────────────
            try:
                # Precios enriquecidos con live prices
                precios_g = precios.copy()
                if live_prices:
                    today_g = pd.Timestamp.today().normalize()
                    rows_live = [{'Activo': a, 'Fecha': today_g, 'Precio': float(p)}
                                 for a, p in live_prices.items() if pd.notna(p)]
                    if rows_live:
                        precios_g = pd.concat([precios_g, pd.DataFrame(rows_live)]) \
                                      .drop_duplicates(subset=['Activo', 'Fecha'], keep='last')

                fi_g = pd.to_datetime(fecha_inicio)
                ff_g = pd.to_datetime(fecha_fin)

                # Fechas del gráfico: fechas con precios en el rango + extremos
                price_dates_g = precios_g[
                    (precios_g['Fecha'] >= fi_g) & (precios_g['Fecha'] <= ff_g)
                ]['Fecha'].unique().tolist()
                chart_dates_g = sorted({pd.Timestamp(d) for d in price_dates_g} | {fi_g, ff_g})

                # ── Construir la serie temporal del gráfico ────────────────────────
                # Lógica:
                # "Valor al Inicio" arranca en fi_g = sum(nom_inicio × precio_inicio)
                #   y es una step function que cambia solo con flujos en el período:
                #   + Compras (nuevo capital invertido)
                #   - Ventas (capital desinvertido)
                #   - Amort / Cupones / Dividendos (capital devuelto)
                # "Valor Total" = sum(nom_actual × precio_actual) en cada fecha.
                # En fi_g ambas líneas coinciden (= Valor al Inicio de la tabla).

                all_ops_g = operaciones.copy()
                all_ops_g['Fecha'] = pd.to_datetime(all_ops_g['Fecha'])
                assets_g = [a for a in all_ops_g['Activo'].dropna().unique() if pd.notna(a)]

                # ── Paso 1: nom_inicio y precio_inicio por activo (igual que tabla) ─
                valor_inicio_total = 0.0
                nom_inicio_g = {}  # asset -> nominales en fi_g (ops < fi_g)
                for asset in assets_g:
                    aops = all_ops_g[all_ops_g['Activo'] == asset].sort_values('Fecha')
                    ops_before = aops[aops['Fecha'] < fi_g]
                    _, last_reset_pos = _find_last_reset(ops_before)
                    if last_reset_pos >= 0:
                        reset_idx = ops_before.index[last_reset_pos]
                        ops_from_reset = aops[aops.index > reset_idx]
                        ops_until_inicio = ops_from_reset[ops_from_reset['Fecha'] < fi_g]
                    else:
                        ops_until_inicio = ops_before

                    nom = 0.0
                    for _, op in ops_until_inicio.iterrows():
                        tipo = str(op['Tipo']).strip()
                        qty  = float(op.get('Cantidad', 0) or 0)
                        if tipo == 'Compra':
                            nom += qty
                        elif tipo == 'Venta':
                            nom = max(nom - qty, 0.0)
                        elif _clasificar_operacion(tipo) == 'amortizacion' and pd.notna(op.get('Cantidad')) and qty > 0:
                            nom = max(nom - qty, 0.0)
                    nom_inicio_g[asset] = nom

                    if nom > 0:
                        ap = precios_g[
                            (precios_g['Activo'] == asset) & (precios_g['Fecha'] <= fi_g)
                        ]
                        if not ap.empty:
                            p = float(ap.iloc[-1]['Precio'])
                            if moneda == 'ARS':
                                p *= _get_fx(fx_rates, fi_g)
                            valor_inicio_total += nom * p

                # ── Paso 2: step function de "Valor al Inicio" post fi_g ─────────
                # Flujos en el período: compras suman, ventas/flujos restan
                ops_en_periodo_g = all_ops_g[
                    (all_ops_g['Fecha'] >= fi_g) & (all_ops_g['Fecha'] <= ff_g)
                ].sort_values('Fecha')

                flujo_steps = []  # (Fecha, delta_capital)
                for _, op in ops_en_periodo_g.iterrows():
                    tipo  = str(op['Tipo']).strip()
                    monto = _get_monto(op, moneda, fx_rates)
                    cat   = _clasificar_operacion(tipo)
                    if tipo == 'Compra':
                        flujo_steps.append((op['Fecha'], +monto))
                    elif tipo == 'Venta':
                        flujo_steps.append((op['Fecha'], -monto))
                    elif cat in ('amortizacion', 'cupon', 'dividendo'):
                        flujo_steps.append((op['Fecha'], -monto))

                # Step function acumulada de flujos
                flujo_cum = {}
                acc = 0.0
                for fecha_f, delta in flujo_steps:
                    acc += delta
                    flujo_cum[fecha_f] = acc

                def _vi_at(d):
                    """Valor al Inicio acumulado hasta fecha d (inclusive)."""
                    acc_vi = 0.0
                    for fd, delta in flujo_steps:
                        if fd <= d:
                            acc_vi += delta
                    return valor_inicio_total + acc_vi

                # ── Paso 3: holdings actuales por activo en cada fecha ───────────
                # Arranca desde nom_inicio_g y acumula ops en el período
                asset_nom_steps = {}  # asset -> list of (Fecha, nom)
                for asset in assets_g:
                    nom = nom_inicio_g.get(asset, 0.0)
                    steps = [(fi_g, nom)]  # estado en fi_g
                    aops_period = ops_en_periodo_g[ops_en_periodo_g['Activo'] == asset]
                    for _, op in aops_period.iterrows():
                        tipo = str(op['Tipo']).strip()
                        qty  = float(op.get('Cantidad', 0) or 0)
                        if tipo == 'Compra':
                            nom += qty
                        elif tipo == 'Venta':
                            nom = max(nom - qty, 0.0)
                        elif _clasificar_operacion(tipo) == 'amortizacion' and pd.notna(op.get('Cantidad')) and qty > 0:
                            nom = max(nom - qty, 0.0)
                        steps.append((op['Fecha'], nom))
                    asset_nom_steps[asset] = pd.DataFrame(steps, columns=['Fecha', 'Nom']) \
                                               .set_index('Fecha').groupby(level=0).last()

                def _nom_at(asset, d):
                    df = asset_nom_steps.get(asset)
                    if df is None or df.empty:
                        return 0.0
                    r = df[df.index <= d]
                    return float(r.iloc[-1]['Nom']) if not r.empty else 0.0

                # ── Paso 4: construir serie temporal ─────────────────────────────
                chart_rows_g = []
                for d in chart_dates_g:
                    d = pd.Timestamp(d)
                    bv = 0.0
                    for asset in assets_g:
                        nom = _nom_at(asset, d)
                        if nom > 0:
                            ap = precios_g[
                                (precios_g['Activo'] == asset) & (precios_g['Fecha'] <= d)
                            ]
                            if not ap.empty:
                                price = float(ap.iloc[-1]['Precio'])
                                if moneda == 'ARS':
                                    price *= _get_fx(fx_rates, d)
                                bv += nom * price
                    chart_rows_g.append({
                        'Fecha':          d,
                        'Valor Total':    bv,
                        'Valor al Inicio': _vi_at(d),
                    })

                ni_steps_g = True  # siempre mostrar ambas líneas

                df_chart = pd.DataFrame(chart_rows_g)
                df_chart['Ganancia'] = df_chart['Valor Total'] - df_chart['Valor al Inicio']
                lbl_y = 'ARS' if moneda == 'ARS' else 'USD'

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_chart['Fecha'], y=df_chart['Valor al Inicio'],
                    fill='tozeroy', name='Valor al Inicio',
                    mode='lines', line=dict(color='#93C5FD', width=1.5),
                    fillcolor='rgba(147, 197, 253, 0.25)',
                    yaxis='y1',
                ))
                fig.add_trace(go.Scatter(
                    x=df_chart['Fecha'], y=df_chart['Valor Total'],
                    name='Valor Total',
                    mode='lines', line=dict(color='#1A4B9B', width=2.5),
                    yaxis='y1',
                ))
                fig.add_trace(go.Scatter(
                    x=df_chart['Fecha'], y=df_chart['Ganancia'],
                    name='Ganancia Acumulada',
                    mode='lines', line=dict(color='#10B981', width=1.5, dash='dot'),
                    yaxis='y2',
                ))
                fig.update_layout(
                    hovermode='x unified',
                    xaxis_title=None,
                    yaxis=dict(title=lbl_y, side='left'),
                    yaxis2=dict(title=f'Ganancia ({lbl_y})', side='right', overlaying='y', showgrid=False),
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
                    height=340,
                    margin=dict(l=0, r=60, t=30, b=0),
                    plot_bgcolor='#F0F2F6',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.caption(f"⚠️ No se pudo generar el gráfico: {e}")


    with tab3:
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
