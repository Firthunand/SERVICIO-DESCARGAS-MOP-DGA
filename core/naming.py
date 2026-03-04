from datetime import datetime


def parse_period_month(start: str, end: str) -> int:
    """Extrae el mes (1-12) desde start/end. Soporta 'DD-MM-YYYY' y 'YYYY-MM-DD'."""
    fmts = ("%d-%m-%Y", "%Y-%m-%d")
    for value in (start, end):
        for fmt in fmts:
            try:
                return datetime.strptime(value, fmt).month
            except ValueError:
                pass
    raise ValueError(f"No pude parsear el mes desde start='{start}' end='{end}'")


def month_name_es(month: int) -> str:
    months = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    return months[month - 1]


def expected_filename_for(code: str, start: str, end: str, today: str) -> str:
    """
    Formato:
    '02. Reporte Febrero OB-0302-127.xls'
    Nota: 'today' se mantiene en firma para compatibilidad, pero no se usa.
    """
    month = parse_period_month(start, end)
    month_num = f"{month:02d}"
    month_name = month_name_es(month)
    return f"{month_num}. Reporte {month_name} {code}.xls"


def parse_year_from_period(start: str, end: str) -> int:
    fmts = ("%d-%m-%Y", "%Y-%m-%d")
    for value in (end, start):  # prioriza end
        for fmt in fmts:
            try:
                return datetime.strptime(value, fmt).year
            except ValueError:
                pass
    raise ValueError(f"No pude parsear el anio desde start='{start}' end='{end}'")