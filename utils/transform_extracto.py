from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook


CASH_MOVEMENTS = {
    "Recibo en pesos",
    "Comp pago en pesos",
    "Recibo en dolares",
    "Comp pago en dolares",
}

FLOW_MOVEMENTS = {
    "Renta": "Cupon",
    "Acreencias u$s +": "Cupon",
}

FEE_MOVEMENTS = {
    "Comision caja de valores",
}

IGNORE_CASH_DESCRIPTIONS = {
    "Operacion de cierre de caucion tomadora",
    "Operacion de cierre de caucion colocadora",
    "Debito por suscripcion de fondos usd",
}

IGNORE_TITLE_DESCRIPTIONS = {
    "Garantia caucion",
    "Devolucion garantia caucion",
    "Canjedevalores",
}

BUY_PREFIXES = (
    "Compra",
    "Suscripcion",
    "Suscripción",
    "Paridadcompra",
)

SELL_PREFIXES = (
    "Venta",
    "Rescate",
    "Paridad venta",
)

# TODO: reemplazar este fallback temporal por el precio correcto de cada activo.
USD_PRICE_FALLBACK_RICS = {
    "BPOB7",
    "BPOC7",
    "BPOD7",
    "BPY26",
    "PNXCO",
    "SFEH",
    "TB261225",
    "TTC9O",
}

PESO_PRICE_FALLBACK_RICS = {
    "S18J5",
    "S30J5",
    "SA$F",
    "T13F6",
    "T15E7",
    "TZVD5",
    "TZXD7",
    "TZXM7",
}

OUTPUT_OPERATION_COLUMNS = [
    "Fecha",
    "Operacion",
    "Tipo de activo",
    "Activo",
    "Nominales",
    "Precio",
    "Valor USD",
    "Precio ARS",
    "Valor ARS",
    "Deposito cash",
    "Retiro Cash",
    "Invertido",
]


def _read_extract_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=sheet_name, header=3)
    raw.columns = raw.iloc[0]
    df = raw.iloc[1:].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    if "Fecha de Liquidación" in df.columns:
        df["Fecha de Liquidación"] = pd.to_datetime(
            df["Fecha de Liquidación"], dayfirst=True, errors="coerce"
        )
    if "Fecha de Concertación" in df.columns:
        df["Fecha de Concertación"] = pd.to_datetime(
            df["Fecha de Concertación"], dayfirst=True, errors="coerce"
        )
    for col in ["Cantidad", "Precio Promedio Ponderado", "Importe"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "Descripción" in df.columns:
        df["Descripción"] = df["Descripción"].astype(str).str.strip()
    if "RIC" in df.columns:
        df["RIC"] = df["RIC"].astype(str).str.strip()
    if "Moneda" in df.columns:
        df["Moneda"] = df["Moneda"].astype(str).str.strip()
    return df


def _load_reference_prices(reference_workbook: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    prices = pd.read_excel(reference_workbook, sheet_name="Precios")
    fx_rates = prices.copy()
    fx_rates["Fecha"] = fx_rates["Fecha"].astype(str)
    fx_rates = fx_rates[fx_rates["Fecha"].str.strip().str.lower() != "precio actual"].copy()
    fx_rates["Fecha"] = pd.to_datetime(fx_rates["Fecha"], errors="coerce")
    fx_rates = fx_rates[["Fecha", "ARS"]].dropna(subset=["Fecha"]).sort_values("Fecha")
    return prices, fx_rates


def _fx_from_prices(fx_rates: pd.DataFrame, fecha: pd.Timestamp) -> float:
    rows = fx_rates[fx_rates["Fecha"] <= pd.to_datetime(fecha)]
    if rows.empty:
        rows = fx_rates.dropna(subset=["Fecha"])
    if rows.empty:
        raise ValueError("No hay tipo de cambio disponible en la hoja Precios.")
    return float(rows.iloc[-1]["ARS"])


def _currency_bucket(moneda: str) -> str:
    moneda = str(moneda).strip()
    if moneda == "Pesos":
        return "ARS"
    if "Dólares" in moneda:
        return "USD"
    return "OTHER"


def _weighted_price(sub: pd.DataFrame) -> float | None:
    qty = sub["Cantidad"].abs().sum()
    if qty <= 0:
        return None
    return float(sub["Importe"].abs().sum() / qty)


def _same_day_fx_map(titulos: pd.DataFrame) -> dict[tuple[pd.Timestamp, str], float]:
    fx_map: dict[tuple[pd.Timestamp, str], float] = {}
    valid = titulos[~titulos["Descripción"].isin(IGNORE_TITLE_DESCRIPTIONS)].copy()
    valid["Bucket"] = valid["Moneda"].apply(_currency_bucket)
    valid = valid[valid["Bucket"].isin(["ARS", "USD"])]

    for (fecha, ric), sub in valid.groupby(["Fecha de Liquidación", "RIC"]):
        ars = sub[sub["Bucket"] == "ARS"]
        usd = sub[sub["Bucket"] == "USD"]
        if ars.empty or usd.empty:
            continue

        qty_ars = float(ars["Cantidad"].abs().sum())
        qty_usd = float(usd["Cantidad"].abs().sum())
        if qty_ars <= 0 or qty_usd <= 0:
            continue

        if not np.isclose(qty_ars, qty_usd, rtol=1e-4, atol=1e-8):
            continue

        price_ars = _weighted_price(ars)
        price_usd = _weighted_price(usd)
        if price_ars and price_usd and price_usd > 0:
            fx_map[(pd.Timestamp(fecha).normalize(), ric)] = float(price_ars / price_usd)

    return fx_map


def _observed_native_price_map(titulos: pd.DataFrame) -> dict[str, tuple[str, float, pd.Timestamp]]:
    observed: dict[str, tuple[str, float, pd.Timestamp]] = {}
    valid = titulos[~titulos["Descripción"].isin(IGNORE_TITLE_DESCRIPTIONS)].copy()
    valid["Bucket"] = valid["Moneda"].apply(_currency_bucket)
    valid = valid[valid["Bucket"].isin(["ARS", "USD"])]
    valid["Fecha de Liquidación"] = pd.to_datetime(valid["Fecha de Liquidación"], errors="coerce")
    valid = valid.dropna(subset=["Fecha de Liquidación", "RIC", "Precio Promedio Ponderado"])

    for asset, sub in valid.sort_values("Fecha de Liquidación").groupby("RIC"):
        last = sub.iloc[-1]
        observed[str(asset).strip()] = (
            str(last["Bucket"]).strip(),
            float(last["Precio Promedio Ponderado"]),
            pd.Timestamp(last["Fecha de Liquidación"]),
        )
    return observed


def _classify_asset_type(species_description: str) -> str:
    text = str(species_description).lower()
    if "cuota" in text or "fci" in text or "fondo" in text:
        return "Fondo"
    if "on " in text or text.startswith("on "):
        return "ON"
    if "bopreal" in text or "bono" in text or "bo rep" in text or "us treasury" in text:
        return "Bono"
    if "lt rep" in text or "tesoro" in text or "lecap" in text:
        return "Lecap/CER"
    return "Instrumento"


def _normalize_title_operation(description: str) -> str | None:
    desc = str(description).strip()
    if any(desc.startswith(prefix) for prefix in BUY_PREFIXES):
        return "Compra"
    if any(desc.startswith(prefix) for prefix in SELL_PREFIXES):
        return "Venta"
    return None


def _resolve_usd_ars_values(
    row: pd.Series,
    fx_map: dict[tuple[pd.Timestamp, str], float],
    fx_rates: pd.DataFrame,
) -> tuple[float | None, float | None, float | None, float | None]:
    fecha = pd.Timestamp(row["Fecha de Liquidación"]).normalize()
    ric = str(row["RIC"]).strip()
    bucket = _currency_bucket(row.get("Moneda", ""))
    precio = float(row["Precio Promedio Ponderado"]) if pd.notna(row["Precio Promedio Ponderado"]) else np.nan
    importe = float(abs(row["Importe"])) if pd.notna(row["Importe"]) else np.nan

    fx = fx_map.get((fecha, ric))
    if fx is None:
        fx = _fx_from_prices(fx_rates, fecha)

    if bucket == "ARS":
        precio_ars = precio
        valor_ars = importe
        precio_usd = precio / fx if pd.notna(precio) else np.nan
        valor_usd = importe / fx if pd.notna(importe) else np.nan
    elif bucket == "USD":
        precio_usd = precio
        valor_usd = importe
        precio_ars = precio * fx if pd.notna(precio) else np.nan
        valor_ars = importe * fx if pd.notna(importe) else np.nan
    else:
        raise ValueError(f"Moneda no soportada para {ric}: {row.get('Moneda')}")

    return precio_usd, valor_usd, precio_ars, valor_ars


def _build_market_rows(
    titulos: pd.DataFrame,
    fx_map: dict[tuple[pd.Timestamp, str], float],
    fx_rates: pd.DataFrame,
) -> list[dict]:
    rows: list[dict] = []
    valid = titulos[~titulos["Descripción"].isin(IGNORE_TITLE_DESCRIPTIONS)].copy()

    for _, row in valid.iterrows():
        op = _normalize_title_operation(row["Descripción"])
        if op is None:
            continue

        precio_usd, valor_usd, precio_ars, valor_ars = _resolve_usd_ars_values(row, fx_map, fx_rates)
        rows.append(
            {
                "Fecha": row["Fecha de Liquidación"],
                "Operacion": op,
                "Tipo de activo": _classify_asset_type(row.get("Descripción de Especie", "")),
                "Activo": row["RIC"],
                "Nominales": abs(row["Cantidad"]) if pd.notna(row["Cantidad"]) else np.nan,
                "Precio": precio_usd,
                "Valor USD": valor_usd,
                "Precio ARS": precio_ars,
                "Valor ARS": valor_ars,
                "Deposito cash": np.nan,
                "Retiro Cash": np.nan,
            }
        )
    return rows


def _cash_usd_amount(row: pd.Series, fx_rates: pd.DataFrame) -> float:
    importe = float(abs(row["Importe"]))
    desc = str(row["Descripción"]).strip()
    if "pesos" in desc.lower():
        fx = _fx_from_prices(fx_rates, pd.Timestamp(row["Fecha de Liquidación"]))
        return importe / fx
    return importe


def _build_cash_and_flow_rows(
    pesos: pd.DataFrame,
    dolares: pd.DataFrame,
    fx_rates: pd.DataFrame,
) -> list[dict]:
    rows: list[dict] = []
    for sheet_name, df in [("Pesos", pesos), ("Dólares", dolares)]:
        for _, row in df.iterrows():
            desc = str(row["Descripción"]).strip()
            if desc in IGNORE_CASH_DESCRIPTIONS:
                continue

            if desc in CASH_MOVEMENTS:
                amount_usd = _cash_usd_amount(row, fx_rates)
                rows.append(
                    {
                        "Fecha": row["Fecha de Liquidación"],
                        "Operacion": "Retiro/Ingreso",
                        "Tipo de activo": np.nan,
                        "Activo": np.nan,
                        "Nominales": np.nan,
                        "Precio": np.nan,
                        "Valor USD": np.nan,
                        "Precio ARS": np.nan,
                        "Valor ARS": np.nan,
                        "Deposito cash": amount_usd if "Recibo" in desc else np.nan,
                        "Retiro Cash": amount_usd if "Comp pago" in desc else np.nan,
                    }
                )
            elif desc in FLOW_MOVEMENTS:
                fx = _fx_from_prices(fx_rates, pd.Timestamp(row["Fecha de Liquidación"]))
                amount_usd = float(abs(row["Importe"])) if sheet_name == "Dólares" else float(abs(row["Importe"])) / fx
                amount_ars = float(abs(row["Importe"])) if sheet_name == "Pesos" else float(abs(row["Importe"])) * fx
                rows.append(
                    {
                        "Fecha": row["Fecha de Liquidación"],
                        "Operacion": FLOW_MOVEMENTS[desc],
                        "Tipo de activo": _classify_asset_type(row.get("Descripción de Especie", "")),
                        "Activo": row["RIC"],
                        "Nominales": np.nan,
                        "Precio": np.nan,
                        "Valor USD": amount_usd,
                        "Precio ARS": 0.0,
                        "Valor ARS": amount_ars,
                        "Deposito cash": np.nan,
                        "Retiro Cash": np.nan,
                    }
                )
            elif desc in FEE_MOVEMENTS:
                amount_usd = _cash_usd_amount(row, fx_rates)
                rows.append(
                    {
                        "Fecha": row["Fecha de Liquidación"],
                        "Operacion": "Retiro/Ingreso",
                        "Tipo de activo": np.nan,
                        "Activo": np.nan,
                        "Nominales": np.nan,
                        "Precio": np.nan,
                        "Valor USD": np.nan,
                        "Precio ARS": np.nan,
                        "Valor ARS": np.nan,
                        "Deposito cash": np.nan,
                        "Retiro Cash": amount_usd,
                    }
                )
    return rows


def _compute_invertido(ops: pd.DataFrame) -> pd.DataFrame:
    ops = ops.sort_values(["Fecha", "Operacion", "Activo"], na_position="last").reset_index(drop=True)
    delta = ops["Deposito cash"].fillna(0.0) - ops["Retiro Cash"].fillna(0.0)
    ops["Invertido"] = delta.cumsum()
    return ops


def _copy_and_extend_prices(
    base_prices: pd.DataFrame,
    assets: set[str],
    observed_native_prices: dict[str, tuple[str, float, pd.Timestamp]] | None = None,
    fx_rates: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict[str, dict[str, object]]]:
    prices = base_prices.copy()
    existing = {str(c).strip() for c in prices.columns}
    price_meta: dict[str, dict[str, object]] = {}
    if "BPD7" not in prices.columns:
        raise ValueError("La hoja Precios base no contiene la columna BPD7.")

    for asset in sorted(assets):
        if asset == "DOLAR":
            continue
        if observed_native_prices and asset in observed_native_prices:
            bucket, observed_price, observed_date = observed_native_prices[asset]
            observed_usd = (
                observed_price / _fx_from_prices(fx_rates, observed_date)
                if bucket == "ARS"
                else observed_price
            )
            if asset in existing:
                source = "precios_fallback"
                scale_factor = 1.0
                mask_live = prices["Fecha"].astype(str).str.strip().str.lower() == "precio actual"
                hist = pd.to_numeric(prices.loc[~mask_live, asset], errors="coerce").dropna()
                base_last = float(hist.iloc[-1]) if not hist.empty else np.nan
                if pd.notna(base_last) and base_last > 0 and observed_usd > 0:
                    ratio = base_last / observed_usd
                    if ratio > 20 or ratio < 0.05:
                        scale_factor = observed_usd / base_last
                        prices[asset] = pd.to_numeric(prices[asset], errors="coerce") * scale_factor
                        source = "rescaled_legacy"
                price_meta[asset] = {
                    "Moneda Cotizacion": bucket,
                    "Fuente Precio": source,
                    "Scale Factor": scale_factor,
                }
                continue
            prices[asset] = observed_usd
            price_meta[asset] = {
                "Moneda Cotizacion": bucket,
                "Fuente Precio": "extract_native",
                "Scale Factor": 1.0,
            }
            continue
        if asset in existing:
            price_meta[asset] = {
                "Moneda Cotizacion": "USD",
                "Fuente Precio": "precios_fallback",
                "Scale Factor": 1.0,
            }
            continue
        if asset in USD_PRICE_FALLBACK_RICS:
            prices[asset] = prices["BPD7"]
            price_meta[asset] = {
                "Moneda Cotizacion": "USD",
                "Fuente Precio": "fallback_bpd7",
                "Scale Factor": 1.0,
            }
        elif asset in PESO_PRICE_FALLBACK_RICS:
            prices[asset] = pd.to_numeric(prices["BPD7"], errors="coerce")
            price_meta[asset] = {
                "Moneda Cotizacion": "ARS",
                "Fuente Precio": "fallback_bpd7",
                "Scale Factor": 1.0,
            }
        else:
            # Fallback conservador: usar BPD7 en USD.
            prices[asset] = prices["BPD7"]
            price_meta[asset] = {
                "Moneda Cotizacion": "USD",
                "Fuente Precio": "fallback_bpd7",
                "Scale Factor": 1.0,
            }
    return prices, price_meta


def _build_prices_long(
    prices_wide: pd.DataFrame,
    fx_rates: pd.DataFrame,
    price_meta: dict[str, dict[str, object]],
) -> pd.DataFrame:
    prices = prices_wide.copy()
    mask_live = prices["Fecha"].astype(str).str.strip().str.lower() == "precio actual"
    hist = prices.loc[~mask_live].copy()
    hist["Fecha"] = pd.to_datetime(hist["Fecha"], errors="coerce")
    hist = hist.dropna(subset=["Fecha"]).sort_values("Fecha")

    tracked_assets = set(price_meta)
    asset_cols = [col for col in hist.columns if col not in {"Fecha", "ARS"} and col in tracked_assets]
    prices_long = (
        hist.melt(id_vars=["Fecha"], value_vars=asset_cols, var_name="Activo", value_name="Precio USD")
        .dropna(subset=["Precio USD"])
        .reset_index(drop=True)
    )
    if prices_long.empty:
        return pd.DataFrame(
            columns=[
                "Fecha",
                "Activo",
                "Moneda Cotizacion",
                "Precio Original",
                "FX Usado",
                "Precio USD",
                "Fuente Precio",
            ]
        )

    fx_only = fx_rates.rename(columns={"ARS": "FX Usado"}).copy()
    fx_only["Fecha"] = pd.to_datetime(fx_only["Fecha"], errors="coerce")
    prices_long = prices_long.merge(fx_only, on="Fecha", how="left")

    meta_df = pd.DataFrame(
        [
            {
                "Activo": asset,
                "Moneda Cotizacion": meta.get("Moneda Cotizacion", "USD"),
                "Fuente Precio": meta.get("Fuente Precio", "precios_fallback"),
            }
            for asset, meta in price_meta.items()
        ]
    )
    if not meta_df.empty:
        prices_long = prices_long.merge(meta_df, on="Activo", how="left")
    else:
        prices_long["Moneda Cotizacion"] = "USD"
        prices_long["Fuente Precio"] = "precios_fallback"

    prices_long["Moneda Cotizacion"] = prices_long["Moneda Cotizacion"].fillna("USD")
    prices_long["Fuente Precio"] = prices_long["Fuente Precio"].fillna("precios_fallback")
    prices_long["Precio Original"] = np.where(
        prices_long["Moneda Cotizacion"].eq("ARS"),
        prices_long["Precio USD"] * prices_long["FX Usado"],
        prices_long["Precio USD"],
    )
    return prices_long[
        [
            "Fecha",
            "Activo",
            "Moneda Cotizacion",
            "Precio Original",
            "FX Usado",
            "Precio USD",
            "Fuente Precio",
        ]
    ].sort_values(["Fecha", "Activo"]).reset_index(drop=True)


def _build_compat_prices_sheet(
    prices_long: pd.DataFrame,
    fx_rates: pd.DataFrame,
    base_prices: pd.DataFrame,
    price_meta: dict[str, dict[str, object]],
) -> pd.DataFrame:
    wide_hist = (
        prices_long.pivot(index="Fecha", columns="Activo", values="Precio USD")
        .reset_index()
        .sort_values("Fecha")
    )
    fx_hist = fx_rates[["Fecha", "ARS"]].copy()
    fx_hist["Fecha"] = pd.to_datetime(fx_hist["Fecha"], errors="coerce")
    wide_hist = wide_hist.merge(fx_hist, on="Fecha", how="left")

    base_live = pd.DataFrame()
    if "Fecha" in base_prices.columns:
        mask_live = base_prices["Fecha"].astype(str).str.strip().str.lower() == "precio actual"
        if mask_live.any():
            base_live = base_prices.loc[mask_live].copy()

    live_row: dict[str, object] = {"Fecha": "Precio Actual"}
    live_row["ARS"] = (
        float(base_live.iloc[0]["ARS"])
        if not base_live.empty and "ARS" in base_live.columns and pd.notna(base_live.iloc[0]["ARS"])
        else float(fx_hist.iloc[-1]["ARS"])
    )

    if not wide_hist.empty:
        last_hist = wide_hist.sort_values("Fecha").iloc[-1]
        asset_cols = [col for col in wide_hist.columns if col not in {"Fecha", "ARS"}]
        for asset in asset_cols:
            scale_factor = float(price_meta.get(asset, {}).get("Scale Factor", 1.0))
            if not base_live.empty and asset in base_live.columns and pd.notna(base_live.iloc[0][asset]):
                live_row[asset] = float(base_live.iloc[0][asset]) * scale_factor
            else:
                live_row[asset] = float(last_hist[asset]) if pd.notna(last_hist[asset]) else np.nan

    prices_compat = pd.concat([pd.DataFrame([live_row]), wide_hist], ignore_index=True, sort=False)
    return prices_compat


def _price_for_asset(prices: pd.DataFrame, asset: str, fecha: pd.Timestamp) -> float:
    if asset not in prices.columns:
        raise ValueError(f"No hay precio disponible para el activo {asset}.")
    mask_live = prices["Fecha"].astype(str).str.strip().str.lower() == "precio actual"
    hist = prices.loc[~mask_live].copy()
    hist["Fecha"] = pd.to_datetime(hist["Fecha"], errors="coerce")
    hist = hist.dropna(subset=["Fecha"]).sort_values("Fecha")
    rows = hist[hist["Fecha"] <= pd.to_datetime(fecha)]
    if rows.empty:
        rows = hist
    if rows.empty:
        raise ValueError(f"No hay histórico de precios para {asset}.")
    return float(rows.iloc[-1][asset])


def _build_initial_balance_rows(
    prices: pd.DataFrame,
    fx_rates: pd.DataFrame,
    first_operation_date: pd.Timestamp,
    initial_asset_balances: list[dict] | None = None,
    initial_cash_usd: float = 0.0,
    initial_cash_ars: float = 0.0,
    opening_reference_date: date | datetime | pd.Timestamp | None = None,
) -> list[dict]:
    reference_date = (
        pd.Timestamp(opening_reference_date).normalize()
        if opening_reference_date is not None
        else pd.Timestamp(first_operation_date).normalize()
    )
    funding_date = reference_date - pd.Timedelta(days=2)
    opening_date = reference_date - pd.Timedelta(days=1)
    opening_rows: list[dict] = []
    total_opening_value_usd = 0.0
    balances = initial_asset_balances or []
    opening_fx = _fx_from_prices(fx_rates, opening_date)

    if not balances and float(initial_cash_usd) == 0.0 and float(initial_cash_ars) == 0.0:
        return []

    for item in balances:
        asset = item["Activo"]
        qty = float(item["Nominales"])
        price = _price_for_asset(prices, asset, opening_date)
        precio_usd = price
        valor_usd = qty * price
        precio_ars = price * opening_fx
        valor_ars = valor_usd * opening_fx

        total_opening_value_usd += valor_usd
        opening_rows.append(
            {
                "Fecha": opening_date,
                "Operacion": "Compra",
                "Tipo de activo": _classify_asset_type(item["Descripción"]),
                "Activo": asset,
                "Nominales": qty,
                "Precio": precio_usd,
                "Valor USD": valor_usd,
                "Precio ARS": precio_ars,
                "Valor ARS": valor_ars,
                "Deposito cash": np.nan,
                "Retiro Cash": np.nan,
            }
        )

    opening_rows.insert(
        0,
        {
            "Fecha": funding_date,
            "Operacion": "Retiro/Ingreso",
            "Tipo de activo": np.nan,
            "Activo": np.nan,
            "Nominales": np.nan,
            "Precio": np.nan,
            "Valor USD": np.nan,
            "Precio ARS": np.nan,
            "Valor ARS": np.nan,
            "Deposito cash": total_opening_value_usd + float(initial_cash_usd) + (float(initial_cash_ars) / opening_fx if opening_fx > 0 else 0.0),
            "Retiro Cash": np.nan,
        },
    )
    return opening_rows


def transform_extract_to_legacy(
    extract_path: Path,
    base_workbook: Path,
    output_path: Path,
    initial_asset_balances: list[dict] | None = None,
    initial_cash_usd: float | None = None,
    initial_cash_ars: float | None = None,
    opening_reference_date: date | datetime | pd.Timestamp | None = None,
) -> None:
    pesos = _read_extract_sheet(extract_path, "Pesos")
    dolares = _read_extract_sheet(extract_path, "Dólares")
    titulos = _read_extract_sheet(extract_path, "Títulos")
    base_prices, fx_rates = _load_reference_prices(base_workbook)

    fx_map = _same_day_fx_map(titulos)
    observed_native_prices = _observed_native_price_map(titulos)
    market_rows = _build_market_rows(titulos, fx_map, fx_rates)
    cash_rows = _build_cash_and_flow_rows(pesos, dolares, fx_rates)
    all_assets = {
        *[str(row["Activo"]).strip() for row in market_rows if pd.notna(row.get("Activo"))],
        *[item["Activo"] for item in (initial_asset_balances or [])],
    }
    prices_wide, price_meta = _copy_and_extend_prices(base_prices, all_assets, observed_native_prices, fx_rates)
    prices_long = _build_prices_long(prices_wide, fx_rates, price_meta)
    prices = _build_compat_prices_sheet(prices_long, fx_rates, base_prices, price_meta)
    first_operation_date = min(
        pd.Timestamp(df["Fecha de Liquidación"].dropna().min())
        for df in [pesos, dolares, titulos]
        if not df["Fecha de Liquidación"].dropna().empty
    )
    opening_rows = _build_initial_balance_rows(
        prices,
        fx_rates,
        first_operation_date,
        initial_asset_balances=initial_asset_balances or [],
        initial_cash_usd=0.0 if initial_cash_usd is None else initial_cash_usd,
        initial_cash_ars=0.0 if initial_cash_ars is None else initial_cash_ars,
        opening_reference_date=opening_reference_date,
    )

    ops = pd.DataFrame(opening_rows + market_rows + cash_rows)
    ops = _compute_invertido(ops)
    ops["Fecha"] = pd.to_datetime(ops["Fecha"], errors="coerce").dt.date
    for col in OUTPUT_OPERATION_COLUMNS:
        if col not in ops.columns:
            ops[col] = np.nan
    ops = ops[OUTPUT_OPERATION_COLUMNS]

    mask_live = prices["Fecha"].astype(str).str.strip().str.lower() == "precio actual"
    prices.loc[~mask_live, "Fecha"] = pd.to_datetime(
        prices.loc[~mask_live, "Fecha"], errors="coerce"
    ).dt.date

    with pd.ExcelWriter(
        output_path,
        engine="openpyxl",
        date_format="DD/MM/YYYY",
        datetime_format="DD/MM/YYYY",
    ) as writer:
        ops.to_excel(writer, sheet_name="Operaciones", index=False)
        prices_long.to_excel(writer, sheet_name="PreciosLong", index=False)
        fx_rates.to_excel(writer, sheet_name="FX", index=False)
        prices.to_excel(writer, sheet_name="Precios", index=False)

    workbook = load_workbook(output_path)
    for sheet_name in ["Operaciones", "Precios", "PreciosLong", "FX"]:
        sheet = workbook[sheet_name]
        for cell in sheet["A"][1:]:
            if isinstance(cell.value, (datetime, date)):
                cell.number_format = "DD/MM/YYYY"
    workbook.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Transforma extractos de cuenta al formato legado de la app.")
    parser.add_argument("--input", default="2025_3618.xlsx", help="Excel extracto fuente.")
    parser.add_argument("--base", default="operaciones extracto.xlsx", help="Excel de referencia usado como base de precios.")
    parser.add_argument("--output", default="extracto_transformado.xlsx", help="Ruta del Excel de salida.")
    args = parser.parse_args()

    transform_extract_to_legacy(
        extract_path=Path(args.input),
        base_workbook=Path(args.base),
        output_path=Path(args.output),
    )
    print(f"OK: generado {args.output}")


if __name__ == "__main__":
    main()
