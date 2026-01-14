from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime
from models.schemas import VentaCreate, VentaResponse, MessageResponse
from config.database import get_db_cursor, execute_query_dict
from utils.helpers import obtener_rango_periodo_actual

router = APIRouter()


@router.post("/", response_model=VentaResponse, status_code=status.HTTP_201_CREATED)
def registrar_venta(venta: VentaCreate):
    """Registrar una venta (reduce stock automáticamente)"""
    try:
        with get_db_cursor(commit=True) as cursor:
            # Llamar a la función de PostgreSQL
            cursor.execute("""
                SELECT registrar_venta(%s, %s, %s)
            """, (venta.id_producto, venta.cantidad, venta.notas))
            
            id_venta = cursor.fetchone()[0]
            
            # Obtener la venta registrada con datos del producto
            cursor.execute("""
                SELECT v.*, p.nombre as producto_nombre, p.codigo_barras as producto_codigo_barras
                FROM ventas v
                JOIN productos p ON v.id_producto = p.id_producto
                WHERE v.id_venta = %s
            """, (id_venta,))
            
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
    
    except Exception as e:
        error_msg = str(e)
        if "Stock insuficiente" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        elif "Producto no encontrado" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al registrar venta: {error_msg}"
            )


@router.get("/", response_model=List[VentaResponse])
def listar_ventas(
    id_producto: Optional[int] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
):
    """Listar ventas con filtros opcionales"""
    try:
        query = """
            SELECT v.*, p.nombre as producto_nombre, p.codigo_barras as producto_codigo_barras
            FROM ventas v
            JOIN productos p ON v.id_producto = p.id_producto
            WHERE 1=1
        """
        params = []
        
        if id_producto is not None:
            query += " AND v.id_producto = %s"
            params.append(id_producto)
        
        if fecha_inicio:
            query += " AND v.fecha_venta >= %s"
            params.append(fecha_inicio)
        
        if fecha_fin:
            query += " AND v.fecha_venta <= %s"
            params.append(fecha_fin)
        
        query += " ORDER BY v.fecha_venta DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        return execute_query_dict(query, tuple(params))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar ventas: {str(e)}"
        )


@router.get("/periodo-actual", response_model=List[VentaResponse])
def listar_ventas_periodo_actual():
    """Listar ventas del período actual (mes actual)"""
    try:
        fecha_inicio, fecha_fin = obtener_rango_periodo_actual()
        
        query = """
            SELECT v.*, p.nombre as producto_nombre, p.codigo_barras as producto_codigo_barras
            FROM ventas v
            JOIN productos p ON v.id_producto = p.id_producto
            WHERE v.fecha_venta BETWEEN %s AND %s
            ORDER BY v.fecha_venta DESC
        """
        
        return execute_query_dict(query, (fecha_inicio, fecha_fin))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar ventas del período: {str(e)}"
        )


@router.get("/{id_venta}", response_model=VentaResponse)
def obtener_venta(id_venta: int):
    """Obtener una venta por ID"""
    try:
        query = """
            SELECT v.*, p.nombre as producto_nombre, p.codigo_barras as producto_codigo_barras
            FROM ventas v
            JOIN productos p ON v.id_producto = p.id_producto
            WHERE v.id_venta = %s
        """
        
        result = execute_query_dict(query, (id_venta,))
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Venta con ID {id_venta} no encontrada"
            )
        
        return result[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener venta: {str(e)}"
        )

