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
.stApp {
    background-color: #FFFFFF !important;
}
/* Ocultar sidebar completamente */
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
/* Centrar contenido principal con márgenes blancos a los costados */
.main .block-container,
[data-testid="block-container"],
div.block-container {
    background-color: #F0F2F6 !important;
    padding-top: 1.5rem !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    max-width: 1050px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    min-height: 100vh !important;
    box-shadow: 4px 0 16px rgba(0,0,0,0.04), -4px 0 16px rgba(0,0,0,0.04) !important;
}
/* La sección main debe ser transparente para que el blanco del stApp se vea a los costados */
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
                costo_unit_promedio = (costo_prev + monto) / current_nominals
            elif tipo == 'Venta':
                current_nominals -= op['Cantidad']
            else:
                categoria = _clasificar_operacion(tipo)
                if categoria == 'amortizacion':
                    total_amort      += monto
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

        # Precios inicio / fin (M4: sort garantiza iloc[-1] correcto)
        asset_prices = precios[precios['Activo'] == asset].sort_values('Fecha')

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
            'Precio Actual':     precio_fin,
            'Valor Actual':      valor_fin,
            'Valor al Inicio':   valor_inicio,
            'Compras':           compras_en_periodo,
            'Ventas':            ventas_en_periodo,
            'Amort / Cup / Div': div_cup_en_periodo,
            'Ganancia Total':    ganancia_total,
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

    # C1/C2: Último reset hasta fecha_fin — mismo criterio que Sección 1 y Sección 2.
    ops_until_fin_d = asset_ops[asset_ops['Fecha'] <= pd.to_datetime(fecha_fin)]
    last_reset_date, last_reset_pos = _find_last_reset(ops_until_fin_d)

    if last_reset_date is None:
        ops_since_reset = ops_until_fin_d
    else:
        ops_since_reset = ops_until_fin_d.iloc[last_reset_pos + 1:]

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
        f'<div style="font-size:1.4rem;font-weight:700;color:#FFFFFF;">Tu Cartera</div>'
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
        total_amort         = portfolio_df['Amortizaciones'].sum()
        total_cup           = portfolio_df['Cupones'].sum()
        total_div           = portfolio_df['Dividendos'].sum()
        total_ganancia_r    = total_amort + total_cup + total_div
        total_ganancia_no_r = portfolio_df['Ganancias no Realizadas'].sum()
        pct_no_r            = (total_ganancia_no_r / total_costo * 100) if total_costo > 0 else 0

        pct_str = f"({'▼' if pct_no_r < 0 else '▲'} {abs(pct_no_r):.1f}%)"
        summary_row = pd.DataFrame([{
            'Activos':          len(portfolio_df),
            'Valor de Mercado': _fmt_money(total_valor_mercado, moneda),
            'Costo Total':      _fmt_money(total_costo, moneda),
            'G. Realizadas':    _fmt_money(total_ganancia_r, moneda),
            'G. no Realizadas': f"{_fmt_money(total_ganancia_no_r, moneda)} {pct_str}",
            'Amortizaciones':   _fmt_money(total_amort, moneda),
            'Cupones':          _fmt_money(total_cup, moneda),
            'Dividendos':       _fmt_money(total_div, moneda),
        }])
        st.dataframe(summary_row, use_container_width=True, hide_index=True)

        cols_display = [
            'Activo', 'Nominales', 'Precio Actual', 'Valor Actual', 'Costo',
            'Amortizaciones', 'Cupones', 'Dividendos', 'Ganancia Total'
        ]
        display_df = portfolio_df.rename(columns={'_Valor Actual': 'Valor Actual'})[cols_display].copy()
        display_df['Nominales']      = display_df['Nominales'].apply(_fmt_number)
        display_df['Precio Actual']  = display_df['Precio Actual'].apply(lambda x: _fmt_price(x, moneda))
        display_df['Valor Actual']   = display_df['Valor Actual'].apply(lambda x: _fmt_money(x, moneda))
        display_df['Costo']          = display_df['Costo'].apply(lambda x: _fmt_money(x, moneda))
        display_df['Amortizaciones'] = display_df['Amortizaciones'].apply(lambda x: _fmt_money(x, moneda))
        display_df['Cupones']        = display_df['Cupones'].apply(lambda x: _fmt_money(x, moneda))
        display_df['Dividendos']     = display_df['Dividendos'].apply(lambda x: _fmt_money(x, moneda))
        display_df['Ganancia Total'] = display_df['Ganancia Total'].apply(lambda x: _fmt_money(x, moneda))
        st.dataframe(display_df, use_container_width=True, hide_index=True,
                     column_config={"Activo": st.column_config.TextColumn("Activo", width="medium")})

        if '_nota' in portfolio_df.columns:
            for nota in portfolio_df[portfolio_df['_nota'] != '']['_nota']:
                st.caption(nota)
        st.caption(
            "ℹ️ Amortizaciones, Cupones y Dividendos corresponden únicamente a los flujos "
            "cobrados desde la apertura de la posición actual. Los flujos de posiciones "
            "anteriores del mismo activo (antes del último reset) se reflejan en la Sección 2."
        )
        csv = portfolio_df.rename(columns={'_Valor Actual': 'Valor Actual'})[cols_display].to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"composicion_cartera_{fecha_actual.strftime('%Y%m%d')}_{lbl_moneda}.csv",
            mime="text/csv",
        )

    # ══════════════════════════════════════════
    # SECCIÓN 2 – EVOLUCIÓN HISTÓRICA
    # Título y selector de fechas en la misma fila
    # ══════════════════════════════════════════
    col_s2, col_i, col_f = st.columns([4, 1, 1])
    with col_s2:
        st.markdown('<div style="border-left:4px solid #1A4B9B;padding-left:10px;margin:0.3rem 0 0.5rem;"><div style="font-size:1.2rem;font-weight:700;color:#1B2333;">Análisis de la Evolución de la Cartera</div></div>', unsafe_allow_html=True)
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

    # Me1: validar rango
    if fecha_inicio > fecha_fin:
        st.error("⚠️ La fecha de inicio no puede ser posterior a la fecha de fin.")
        return

    evolution_df = calculate_portfolio_evolution(
        operaciones, precios, fecha_inicio, fecha_fin, moneda=moneda, fx_rates=fx_rates,
        live_prices=live_prices, live_fx=live_fx
    )

    if evolution_df.empty:
        st.warning("No hay datos de evolución para el rango de fechas seleccionado.")
    else:
        n_abiertos = int((evolution_df['Nominales'] > 0).sum())
        n_cerrados = int((evolution_df['Nominales'] <= 0).sum())
        label_act  = str(n_abiertos) if n_cerrados == 0 else (
            f"{n_abiertos} ({n_cerrados} cerrado{'s' if n_cerrados > 1 else ''})"
        )
        flujos     = evolution_df['Ventas'].sum() + evolution_df['Amort / Cup / Div'].sum()
        total_gain = evolution_df['Ganancia Total'].sum()
        base       = evolution_df['Valor al Inicio'].sum() + evolution_df['Compras'].sum()
        pct_evo    = (total_gain / base * 100) if base > 0 else 0
        pct_str2   = f"({'▼' if pct_evo < 0 else '▲'} {abs(pct_evo):.1f}%)"
        summary_evo = pd.DataFrame([{
            'Activos':         label_act,
            'Valor Total':     _fmt_money(evolution_df['Valor Actual'].sum(), moneda),
            'Valor al Inicio': _fmt_money(evolution_df['Valor al Inicio'].sum(), moneda),
            'Compras':         _fmt_money(evolution_df['Compras'].sum(), moneda),
            'Ventas + Flujos': _fmt_money(flujos, moneda),
            'Ganancia Total':  f"{_fmt_money(total_gain, moneda)} {pct_str2}",
        }])
        st.dataframe(summary_evo, use_container_width=True, hide_index=True)

        evo_display = evolution_df.copy()
        evo_display['Nominales'] = evo_display['Nominales'].apply(_fmt_number)
        for col in ['Precio Actual', 'Valor Actual', 'Valor al Inicio',
                    'Compras', 'Ventas', 'Amort / Cup / Div', 'Ganancia Total']:
            if col == 'Precio Actual':
                evo_display[col] = evo_display[col].apply(lambda x: _fmt_price(x, moneda))
            else:
                evo_display[col] = evo_display[col].apply(lambda x: _fmt_money(x, moneda))
        st.dataframe(evo_display, use_container_width=True, hide_index=True,
                     column_config={"Activo": st.column_config.TextColumn("Activo", width="medium")})

        csv_evo = evolution_df.to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV Evolución",
            data=csv_evo,
            file_name=f"evolucion_cartera_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}_{lbl_moneda}.csv",
            mime="text/csv",
        )

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
