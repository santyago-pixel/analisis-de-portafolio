from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from io import BytesIO
import re

from pypdf import PdfReader


SECTION_INSTRUMENTS = "SALDOS EN CUENTA COMITENTE - INSTRUMENTOS"
SECTION_GUARANTEES = "GARANTIAS EN CUENTA COMITENTE"
HEADER_LINES = {"CODIGO", "DESCRIPCION", "CANTIDAD", "ESTADO", "(**)"}
USD_CODES = {"DOLAR", "DOLARES", "USD", "U$S"}


@dataclass
class InitialBalanceParseResult:
    positions: list[dict]
    cash_usd: float
    cash_ars: float
    period_start: date | None
    period_end: date | None


def _clean_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in (text or "").splitlines():
        line = re.sub(r"\s+", " ", str(raw)).strip()
        if line:
            lines.append(line)
    return lines


def _parse_amount(text: str) -> float | None:
    cleaned = str(text).strip().replace(",", "")
    cleaned = cleaned.replace("$", "").replace("(", "-").replace(")", "")
    if not cleaned:
        return None
    if re.fullmatch(r"-?\d+(?:\.\d+)?", cleaned):
        return float(cleaned)
    return None


def _extract_period(text: str) -> tuple[date | None, date | None]:
    match = re.search(r"(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})", text or "")
    if not match:
        return (None, None)
    start = datetime.strptime(match.group(1), "%d/%m/%Y").date()
    end = datetime.strptime(match.group(2), "%d/%m/%Y").date()
    return (start, end)


def _find_section_end(lines: list[str], start_idx: int) -> int:
    for idx in range(start_idx, len(lines)):
        if SECTION_GUARANTEES in lines[idx].upper() or lines[idx].startswith("FECHA CONC."):
            return idx
    return len(lines)


def _parse_instrument_rows(lines: list[str]) -> tuple[list[dict], float, float]:
    positions_by_code: dict[str, dict] = {}
    cash_usd = 0.0
    cash_ars = 0.0

    upper_lines = [line.upper() for line in lines]
    code_idx = next((i for i, line in enumerate(upper_lines) if line == "CODIGO"), None)
    if code_idx is None:
        return ([], 0.0, 0.0)

    end_idx = _find_section_end(lines, code_idx + 1)
    i = code_idx + 1
    while i < end_idx:
        line = lines[i]
        upper = line.upper()
        if upper in HEADER_LINES:
            i += 1
            continue
        if SECTION_GUARANTEES in upper or upper.startswith("FECHA CONC."):
            break

        code = upper.replace("$ ", "").replace("$", "").strip()
        if not code:
            i += 1
            continue

        j = i + 1
        desc_parts: list[str] = []
        qty = None
        while j < end_idx:
            candidate = lines[j]
            if candidate.upper() in HEADER_LINES:
                j += 1
                continue
            parsed_amount = _parse_amount(candidate)
            if parsed_amount is not None:
                qty = parsed_amount
                break
            desc_parts.append(candidate)
            j += 1

        if qty is None:
            i += 1
            continue

        state = lines[j + 1].strip().upper() if j + 1 < end_idx else ""
        description = " ".join(desc_parts).strip()

        if code in USD_CODES:
            cash_usd += qty
        elif "PESO" in code:
            cash_ars += qty
        else:
            entry = positions_by_code.setdefault(
                code,
                {
                    "Activo": code,
                    "Descripción": description,
                    "Nominales": 0.0,
                    "_Estados": set(),
                },
            )
            if description and not entry["Descripción"]:
                entry["Descripción"] = description
            entry["Nominales"] += qty
            if state:
                entry["_Estados"].add(state)

        i = j + 2

    positions = [
        {
            "Activo": item["Activo"],
            "Descripción": item["Descripción"],
            "Nominales": float(item["Nominales"]),
        }
        for item in positions_by_code.values()
        if item["Nominales"] > 0
    ]
    positions.sort(key=lambda row: row["Activo"])
    return (positions, cash_usd, cash_ars)


def extract_initial_balances_from_pdf_bytes(pdf_bytes: bytes) -> InitialBalanceParseResult:
    reader = PdfReader(BytesIO(pdf_bytes))
    if not reader.pages:
        return InitialBalanceParseResult([], 0.0, 0.0, None, None)

    first_page_text = reader.pages[0].extract_text() or ""
    lines = _clean_lines(first_page_text)
    positions, cash_usd, cash_ars = _parse_instrument_rows(lines)
    period_start, period_end = _extract_period(first_page_text)

    return InitialBalanceParseResult(
        positions=positions,
        cash_usd=float(cash_usd),
        cash_ars=float(cash_ars),
        period_start=period_start,
        period_end=period_end,
    )
