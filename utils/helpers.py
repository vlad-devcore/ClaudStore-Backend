# ==========================================
# utils/helpers.py
# ==========================================
"""
Funciones auxiliares para el sistema de inventario
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
import os
import uuid


def generar_nombre_archivo(extension: str = "jpg") -> str:
    """
    Genera un nombre único para archivos (imágenes)
    
    Args:
        extension (str): Extensión del archivo (sin punto)
    
    Returns:
        str: Nombre único del archivo
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"{timestamp}_{unique_id}.{extension}"


def formatear_precio(precio: Decimal) -> str:
    """
    Formatea un precio a formato de moneda
    
    Args:
        precio (Decimal): Precio a formatear
    
    Returns:
        str: Precio formateado (ej: "$1,234.56")
    """
    return f"${precio:,.2f}"


def formatear_fecha(fecha: datetime, formato: str = "%d/%m/%Y %H:%M") -> str:
    """
    Formatea una fecha a string
    
    Args:
        fecha (datetime): Fecha a formatear
        formato (str): Formato de salida
    
    Returns:
        str: Fecha formateada
    """
    return fecha.strftime(formato)


def calcular_porcentaje_ganancia(costo: Decimal, precio_venta: Decimal) -> float:
    """
    Calcula el porcentaje de ganancia
    
    Args:
        costo (Decimal): Costo del producto
        precio_venta (Decimal): Precio de venta
    
    Returns:
        float: Porcentaje de ganancia
    """
    if costo == 0:
        return 0.0
    ganancia = precio_venta - costo
    return float((ganancia / costo) * 100)


def calcular_margen_ganancia(costo: Decimal, precio_venta: Decimal) -> Decimal:
    """
    Calcula el margen de ganancia (diferencia)
    
    Args:
        costo (Decimal): Costo del producto
        precio_venta (Decimal): Precio de venta
    
    Returns:
        Decimal: Margen de ganancia
    """
    return precio_venta - costo


def obtener_primer_dia_mes(fecha: Optional[datetime] = None) -> datetime:
    """
    Obtiene el primer día del mes
    
    Args:
        fecha (datetime): Fecha de referencia (si es None, usa hoy)
    
    Returns:
        datetime: Primer día del mes a las 00:00:00
    """
    if fecha is None:
        fecha = datetime.now()
    return fecha.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def obtener_ultimo_dia_mes(fecha: Optional[datetime] = None) -> datetime:
    """
    Obtiene el último día del mes
    
    Args:
        fecha (datetime): Fecha de referencia (si es None, usa hoy)
    
    Returns:
        datetime: Último día del mes a las 23:59:59
    """
    if fecha is None:
        fecha = datetime.now()
    
    # Obtener el primer día del mes siguiente
    if fecha.month == 12:
        primer_dia_siguiente = fecha.replace(year=fecha.year + 1, month=1, day=1)
    else:
        primer_dia_siguiente = fecha.replace(month=fecha.month + 1, day=1)
    
    # Restar un día para obtener el último día del mes actual
    ultimo_dia = primer_dia_siguiente - timedelta(days=1)
    return ultimo_dia.replace(hour=23, minute=59, second=59, microsecond=999999)


def obtener_rango_periodo_actual() -> Tuple[datetime, datetime]:
    """
    Obtiene el rango de fechas del período actual (mes actual)
    
    Returns:
        Tuple[datetime, datetime]: (fecha_inicio, fecha_fin)
    """
    return obtener_primer_dia_mes(), obtener_ultimo_dia_mes()


def paginar_resultados(resultados: List[Any], page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """
    Pagina una lista de resultados
    
    Args:
        resultados (List): Lista de resultados
        page (int): Número de página (empieza en 1)
        page_size (int): Tamaño de página
    
    Returns:
        Dict: Diccionario con datos paginados
    """
    total = len(resultados)
    total_pages = (total + page_size - 1) // page_size  # Ceil division
    
    # Validar página
    if page < 1:
        page = 1
    if page > total_pages and total_pages > 0:
        page = total_pages
    
    # Calcular índices
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "data": resultados[start_idx:end_idx]
    }


def validar_imagen(filename: str, extensiones_permitidas: set = {"jpg", "jpeg", "png", "gif", "webp"}) -> bool:
    """
    Valida si un archivo es una imagen válida
    
    Args:
        filename (str): Nombre del archivo
        extensiones_permitidas (set): Set de extensiones permitidas
    
    Returns:
        bool: True si es válida
    """
    if not filename:
        return False
    extension = filename.lower().split('.')[-1]
    return extension in extensiones_permitidas


def guardar_archivo_local(archivo_bytes: bytes, nombre_archivo: str, carpeta: str = "static/images") -> str:
    """
    Guarda un archivo localmente
    
    Args:
        archivo_bytes (bytes): Contenido del archivo
        nombre_archivo (str): Nombre del archivo
        carpeta (str): Carpeta donde guardar
    
    Returns:
        str: Ruta relativa del archivo guardado
    """
    # Crear carpeta si no existe
    os.makedirs(carpeta, exist_ok=True)
    
    # Ruta completa
    ruta_completa = os.path.join(carpeta, nombre_archivo)
    
    # Guardar archivo
    with open(ruta_completa, 'wb') as f:
        f.write(archivo_bytes)
    
    # Retornar ruta relativa para la BD
    return f"/{carpeta}/{nombre_archivo}"


def eliminar_archivo_local(ruta_archivo: str) -> bool:
    """
    Elimina un archivo local
    
    Args:
        ruta_archivo (str): Ruta del archivo
    
    Returns:
        bool: True si se eliminó correctamente
    """
    try:
        # Limpiar la ruta (remover / inicial si existe)
        if ruta_archivo.startswith('/'):
            ruta_archivo = ruta_archivo[1:]
        
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)
            return True
        return False
    except Exception as e:
        print(f"Error al eliminar archivo: {e}")
        return False


def convertir_decimal_a_float(obj: Any) -> Any:
    """
    Convierte objetos Decimal a float recursivamente (para JSON)
    
    Args:
        obj: Objeto a convertir
    
    Returns:
        Objeto con Decimals convertidos a float
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convertir_decimal_a_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convertir_decimal_a_float(item) for item in obj]
    return obj


def cursor_to_dict(cursor) -> List[Dict[str, Any]]:
    """
    Convierte resultados de un cursor a lista de diccionarios
    
    Args:
        cursor: Cursor de psycopg2
    
    Returns:
        List[Dict]: Lista de diccionarios
    """
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def validar_periodo_mes(anio: int, mes: int) -> bool:
    """
    Valida que el año y mes sean válidos
    
    Args:
        anio (int): Año
        mes (int): Mes (1-12)
    
    Returns:
        bool: True si es válido
    """
    if not (2000 <= anio <= 2100):
        return False
    if not (1 <= mes <= 12):
        return False
    return True


def calcular_totales_periodo(ventas: List[Dict], compras: List[Dict], 
                             registros_financieros: List[Dict]) -> Dict[str, Decimal]:
    """
    Calcula totales de un período
    
    Args:
        ventas (List[Dict]): Lista de ventas
        compras (List[Dict]): Lista de compras
        registros_financieros (List[Dict]): Lista de registros financieros
    
    Returns:
        Dict: Diccionario con totales calculados
    """
    total_ventas = sum(Decimal(str(v.get('total', 0))) for v in ventas)
    total_compras = sum(Decimal(str(c.get('total', 0))) for c in compras)
    
    inversion_manual = sum(
        Decimal(str(r.get('monto', 0))) 
        for r in registros_financieros 
        if r.get('tipo') == 'inversion'
    )
    
    gastos_manual = sum(
        Decimal(str(r.get('monto', 0))) 
        for r in registros_financieros 
        if r.get('tipo') == 'gasto'
    )
    
    ganancia_manual = sum(
        Decimal(str(r.get('monto', 0))) 
        for r in registros_financieros 
        if r.get('tipo') == 'ganancia'
    )
    
    ganancia_neta = (total_ventas - total_compras + 
                     ganancia_manual - inversion_manual - gastos_manual)
    
    return {
        'total_ventas': total_ventas,
        'total_compras': total_compras,
        'inversion_manual': inversion_manual,
        'gastos_manual': gastos_manual,
        'ganancia_manual': ganancia_manual,
        'ganancia_neta': ganancia_neta
    }
