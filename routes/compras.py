from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime
from models.schemas import CompraCreate, CompraResponse, MessageResponse
from config.database import get_db_cursor, execute_query_dict
from utils.helpers import obtener_rango_periodo_actual

router = APIRouter()


@router.post("/", response_model=CompraResponse, status_code=status.HTTP_201_CREATED)
def registrar_compra(compra: CompraCreate):
    """Registrar una compra (aumenta stock automáticamente)"""
    try:
        with get_db_cursor(commit=True) as cursor:
            # Llamar a la función de PostgreSQL
            cursor.execute("""
                SELECT registrar_compra(%s, %s, %s, %s)
            """, (compra.id_producto, compra.cantidad, compra.costo_unitario, compra.notas))
            
            id_compra = cursor.fetchone()[0]
            
            # Obtener la compra registrada con datos del producto
            cursor.execute("""
                SELECT c.*, p.nombre as producto_nombre, p.codigo_barras as producto_codigo_barras
                FROM compras c
                JOIN productos p ON c.id_producto = p.id_producto
                WHERE c.id_compra = %s
            """, (id_compra,))
            
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
    
    except Exception as e:
        error_msg = str(e)
        if "Producto no encontrado" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al registrar compra: {error_msg}"
            )


@router.get("/", response_model=List[CompraResponse])
def listar_compras(
    id_producto: Optional[int] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
):
    """Listar compras con filtros opcionales"""
    try:
        query = """
            SELECT c.*, p.nombre as producto_nombre, p.codigo_barras as producto_codigo_barras
            FROM compras c
            JOIN productos p ON c.id_producto = p.id_producto
            WHERE 1=1
        """
        params = []
        
        if id_producto is not None:
            query += " AND c.id_producto = %s"
            params.append(id_producto)
        
        if fecha_inicio:
            query += " AND c.fecha_compra >= %s"
            params.append(fecha_inicio)
        
        if fecha_fin:
            query += " AND c.fecha_compra <= %s"
            params.append(fecha_fin)
        
        query += " ORDER BY c.fecha_compra DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        return execute_query_dict(query, tuple(params))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar compras: {str(e)}"
        )


@router.get("/periodo-actual", response_model=List[CompraResponse])
def listar_compras_periodo_actual():
    """Listar compras del período actual (mes actual)"""
    try:
        fecha_inicio, fecha_fin = obtener_rango_periodo_actual()
        
        query = """
            SELECT c.*, p.nombre as producto_nombre, p.codigo_barras as producto_codigo_barras
            FROM compras c
            JOIN productos p ON c.id_producto = p.id_producto
            WHERE c.fecha_compra BETWEEN %s AND %s
            ORDER BY c.fecha_compra DESC
        """
        
        return execute_query_dict(query, (fecha_inicio, fecha_fin))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar compras del período: {str(e)}"
        )


@router.get("/{id_compra}", response_model=CompraResponse)
def obtener_compra(id_compra: int):
    """Obtener una compra por ID"""
    try:
        query = """
            SELECT c.*, p.nombre as producto_nombre, p.codigo_barras as producto_codigo_barras
            FROM compras c
            JOIN productos p ON c.id_producto = p.id_producto
            WHERE c.id_compra = %s
        """
        
        result = execute_query_dict(query, (id_compra,))
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Compra con ID {id_compra} no encontrada"
            )
        
        return result[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener compra: {str(e)}"
        )