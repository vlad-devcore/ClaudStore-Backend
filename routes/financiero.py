from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime
from models.schemas import (
    RegistroFinancieroCreate, RegistroFinancieroResponse, MessageResponse
)
from config.database import get_db_cursor, execute_query_dict
from utils.helpers import obtener_rango_periodo_actual

router = APIRouter()


@router.post("/", response_model=RegistroFinancieroResponse, status_code=status.HTTP_201_CREATED)
def crear_registro_financiero(registro: RegistroFinancieroCreate):
    """Crear un registro financiero manual (inversión, gasto, ganancia, ajuste)"""
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO registro_financiero (tipo, concepto, monto, descripcion)
                VALUES (%s, %s, %s, %s)
                RETURNING *
            """, (registro.tipo, registro.concepto, registro.monto, registro.descripcion))
            
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear registro financiero: {str(e)}"
        )


@router.get("/", response_model=List[RegistroFinancieroResponse])
def listar_registros_financieros(
    tipo: Optional[str] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
):
    """Listar registros financieros con filtros opcionales"""
    try:
        query = "SELECT * FROM registro_financiero WHERE 1=1"
        params = []
        
        if tipo:
            query += " AND tipo = %s"
            params.append(tipo.lower())
        
        if fecha_inicio:
            query += " AND fecha_registro >= %s"
            params.append(fecha_inicio)
        
        if fecha_fin:
            query += " AND fecha_registro <= %s"
            params.append(fecha_fin)
        
        query += " ORDER BY fecha_registro DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        return execute_query_dict(query, tuple(params))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar registros financieros: {str(e)}"
        )


@router.get("/periodo-actual", response_model=List[RegistroFinancieroResponse])
def listar_registros_periodo_actual():
    """Listar registros financieros del período actual (mes actual)"""
    try:
        fecha_inicio, fecha_fin = obtener_rango_periodo_actual()
        
        query = """
            SELECT * FROM registro_financiero
            WHERE fecha_registro BETWEEN %s AND %s
            ORDER BY fecha_registro DESC
        """
        
        return execute_query_dict(query, (fecha_inicio, fecha_fin))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar registros del período: {str(e)}"
        )


@router.get("/{id_registro}", response_model=RegistroFinancieroResponse)
def obtener_registro_financiero(id_registro: int):
    """Obtener un registro financiero por ID"""
    try:
        result = execute_query_dict(
            "SELECT * FROM registro_financiero WHERE id_registro = %s",
            (id_registro,)
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Registro con ID {id_registro} no encontrado"
            )
        
        return result[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener registro financiero: {str(e)}"
        )


@router.delete("/{id_registro}", response_model=MessageResponse)
def eliminar_registro_financiero(id_registro: int):
    """Eliminar un registro financiero"""
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                DELETE FROM registro_financiero
                WHERE id_registro = %s
                RETURNING id_registro
            """, (id_registro,))
            
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Registro con ID {id_registro} no encontrado"
                )
            
            return {
                "message": "Registro financiero eliminado exitosamente",
                "detail": f"ID: {id_registro}"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar registro: {str(e)}"
        )