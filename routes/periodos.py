from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List
from datetime import datetime
import io
from models.schemas import (
    PeriodoMensualCreate, PeriodoMensualResponse, MessageResponse
)
from config.database import get_db_cursor, execute_query_dict
from utils.excel_generator import ExcelGenerator
from utils.helpers import obtener_primer_dia_mes, obtener_ultimo_dia_mes

router = APIRouter()


@router.post("/cerrar", response_model=PeriodoMensualResponse, status_code=status.HTTP_201_CREATED)
def cerrar_periodo_mensual(periodo: PeriodoMensualCreate):
    """Cerrar período mensual y archivar datos"""
    try:
        # Verificar que no exista ya un período cerrado para ese mes
        existing = execute_query_dict("""
            SELECT id_periodo FROM periodos_mensuales
            WHERE anio = %s AND mes = %s
        """, (periodo.anio, periodo.mes))
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un período cerrado para {periodo.mes}/{periodo.anio}"
            )
        
        with get_db_cursor(commit=True) as cursor:
            # Llamar a la función de PostgreSQL
            cursor.execute("""
                SELECT cerrar_periodo_mensual(%s, %s, %s, %s, %s)
            """, (
                periodo.anio, periodo.mes,
                periodo.fecha_inicio, periodo.fecha_fin,
                periodo.notas
            ))
            
            id_periodo = cursor.fetchone()[0]
            
            # Obtener el período creado
            cursor.execute("""
                SELECT * FROM periodos_mensuales WHERE id_periodo = %s
            """, (id_periodo,))
            
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cerrar período: {str(e)}"
        )


@router.get("/", response_model=List[PeriodoMensualResponse])
def listar_periodos(skip: int = 0, limit: int = 100):
    """Listar todos los períodos cerrados"""
    try:
        query = """
            SELECT * FROM periodos_mensuales
            ORDER BY anio DESC, mes DESC
            LIMIT %s OFFSET %s
        """
        
        return execute_query_dict(query, (limit, skip))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar períodos: {str(e)}"
        )


@router.get("/{id_periodo}", response_model=PeriodoMensualResponse)
def obtener_periodo(id_periodo: int):
    """Obtener un período por ID"""
    try:
        result = execute_query_dict(
            "SELECT * FROM periodos_mensuales WHERE id_periodo = %s",
            (id_periodo,)
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Período con ID {id_periodo} no encontrado"
            )
        
        return result[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener período: {str(e)}"
        )


@router.get("/{id_periodo}/excel")
async def generar_excel_periodo(id_periodo: int):
    """Generar archivo Excel del período cerrado"""
    try:
        # Obtener datos del período
        periodo_data = execute_query_dict(
            "SELECT * FROM periodos_mensuales WHERE id_periodo = %s",
            (id_periodo,)
        )
        
        if not periodo_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Período con ID {id_periodo} no encontrado"
            )
        
        periodo = periodo_data[0]
        
        # Procesar top_productos (JSON)
        top_productos = []
        if periodo.get('top_productos'):
            import json
            if isinstance(periodo['top_productos'], str):
                top_productos = json.loads(periodo['top_productos'])
            else:
                top_productos = periodo['top_productos']
        
        # Generar Excel
        generator = ExcelGenerator()
        excel_bytes = generator.generar_reporte_periodo({
            **periodo,
            'top_productos': top_productos
        })
        
        # Nombre del archivo
        filename = f"reporte_{periodo['anio']}_{periodo['mes']:02d}.xlsx"
        
        # Retornar como descarga
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar Excel: {str(e)}"
        )


@router.get("/periodo-actual/excel")
async def generar_excel_periodo_actual():
    """Generar Excel del período actual (sin cerrar)"""
    try:
        # Obtener fechas del período actual
        fecha_inicio = obtener_primer_dia_mes()
        fecha_fin = obtener_ultimo_dia_mes()
        
        # Obtener datos
        ganancia = execute_query_dict("SELECT * FROM vista_ganancia_periodo_actual")[0]
        top_productos = execute_query_dict("""
            SELECT * FROM vista_top_productos_periodo LIMIT 8
        """)
        
        # Preparar datos
        periodo_data = {
            'anio': fecha_inicio.year,
            'mes': fecha_inicio.month,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'total_ventas': ganancia['ingresos_ventas'],
            'total_compras': ganancia['inversion_compras'],
            'total_inversion_manual': ganancia['inversion_manual'],
            'total_gastos_manual': ganancia['gastos_manuales'],
            'ganancia_manual': ganancia['ganancia_manual'],
            'ganancia_neta': ganancia['ganancia_neta_total'],
            'top_productos': top_productos,
            'cantidad_productos_vendidos': len(top_productos),
            'cantidad_productos_registrados': 0
        }
        
        # Generar Excel
        generator = ExcelGenerator()
        excel_bytes = generator.generar_reporte_periodo(periodo_data)
        
        # Nombre del archivo
        filename = f"reporte_actual_{fecha_inicio.year}_{fecha_inicio.month:02d}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar Excel: {str(e)}"
        )