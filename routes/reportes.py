# ==========================================
# routes/reportes.py
# ==========================================
from fastapi import APIRouter, HTTPException, status
from typing import List
from models.schemas import (
    InversionInventarioResponse, VentasPeriodoResponse, ComprasPeriodoResponse,
    GananciaPeriodoResponse, TopProductoResponse, StockBajoResponse
)
from config.database import execute_query_dict

router = APIRouter()


@router.get("/inversion-inventario", response_model=InversionInventarioResponse)
def obtener_inversion_inventario():
    """Obtener inversión total en inventario actual"""
    try:
        result = execute_query_dict("SELECT * FROM vista_inversion_inventario")
        
        if not result:
            return {
                "inversion_total": 0,
                "total_productos": 0,
                "total_unidades": 0
            }
        
        return result[0]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener inversión: {str(e)}"
        )


@router.get("/ventas-periodo", response_model=List[VentasPeriodoResponse])
def obtener_ventas_periodo():
    """Obtener ventas del período actual"""
    try:
        result = execute_query_dict("SELECT * FROM vista_ventas_periodo_actual")
        return result if result else []
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener ventas del período: {str(e)}"
        )


@router.get("/compras-periodo", response_model=List[ComprasPeriodoResponse])
def obtener_compras_periodo():
    """Obtener compras del período actual"""
    try:
        result = execute_query_dict("SELECT * FROM vista_compras_periodo_actual")
        return result if result else []
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener compras del período: {str(e)}"
        )


@router.get("/ganancia-periodo", response_model=GananciaPeriodoResponse)
def obtener_ganancia_periodo():
    """Obtener ganancia neta del período actual"""
    try:
        result = execute_query_dict("SELECT * FROM vista_ganancia_periodo_actual")
        
        if not result:
            return {
                "ingresos_ventas": 0,
                "inversion_compras": 0,
                "inversion_manual": 0,
                "gastos_manuales": 0,
                "ganancia_manual": 0,
                "ganancia_neta_total": 0
            }
        
        return result[0]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener ganancia del período: {str(e)}"
        )


@router.get("/top-productos", response_model=List[TopProductoResponse])
def obtener_top_productos(limite: int = 8):
    """Obtener top productos más vendidos del período actual"""
    try:
        query = """
            SELECT 
                p.id_producto,
                p.nombre,
                p.codigo_barras,
                c.nombre AS categoria,
                SUM(v.cantidad) AS total_vendido,
                SUM(v.total) AS ingresos_generados
            FROM ventas v
            JOIN productos p ON v.id_producto = p.id_producto
            LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
            WHERE v.fecha_venta >= DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY p.id_producto, p.nombre, p.codigo_barras, c.nombre
            ORDER BY total_vendido DESC
            LIMIT %s
        """
        
        result = execute_query_dict(query, (limite,))
        return result if result else []
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener top productos: {str(e)}"
        )


@router.get("/stock-bajo", response_model=List[StockBajoResponse])
def obtener_productos_stock_bajo(minimo: int = 3):
    """Obtener productos con stock bajo"""
    try:
        query = """
            SELECT 
                p.id_producto,
                p.codigo_barras,
                p.nombre,
                c.nombre AS categoria,
                p.stock,
                p.costo,
                p.precio_venta
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
            WHERE p.stock <= %s AND p.activo = TRUE
            ORDER BY p.stock ASC
        """
        
        result = execute_query_dict(query, (minimo,))
        return result if result else []
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener productos con stock bajo: {str(e)}"
        )
