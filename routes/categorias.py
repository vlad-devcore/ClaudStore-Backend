from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from models.schemas import (
    CategoriaCreate, CategoriaUpdate, CategoriaResponse, MessageResponse
)
from config.database import get_db_cursor, execute_query_dict
import psycopg2

router = APIRouter()


@router.post("/", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def crear_categoria(categoria: CategoriaCreate):
    """Crear una nueva categoría"""
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO categorias (nombre, descripcion, activo)
                VALUES (%s, %s, %s)
                RETURNING id_categoria, nombre, descripcion, activo, fecha_registro
            """, (categoria.nombre, categoria.descripcion, categoria.activo))
            
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
    
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una categoría con el nombre '{categoria.nombre}'"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear categoría: {str(e)}"
        )


@router.get("/", response_model=List[CategoriaResponse])
def listar_categorias(activo: Optional[bool] = None, skip: int = 0, limit: int = 100):
    """Listar todas las categorías"""
    try:
        query = "SELECT * FROM categorias"
        params = []
        
        if activo is not None:
            query += " WHERE activo = %s"
            params.append(activo)
        
        query += " ORDER BY nombre LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        return execute_query_dict(query, tuple(params))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar categorías: {str(e)}"
        )


@router.get("/{id_categoria}", response_model=CategoriaResponse)
def obtener_categoria(id_categoria: int):
    """Obtener una categoría por ID"""
    try:
        result = execute_query_dict(
            "SELECT * FROM categorias WHERE id_categoria = %s",
            (id_categoria,)
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoría con ID {id_categoria} no encontrada"
            )
        
        return result[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener categoría: {str(e)}"
        )


@router.put("/{id_categoria}", response_model=CategoriaResponse)
def actualizar_categoria(id_categoria: int, categoria: CategoriaUpdate):
    """Actualizar una categoría"""
    try:
        # Verificar que existe
        existing = execute_query_dict(
            "SELECT * FROM categorias WHERE id_categoria = %s",
            (id_categoria,)
        )
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoría con ID {id_categoria} no encontrada"
            )
        
        # Construir query dinámicamente solo con campos proporcionados
        updates = []
        params = []
        
        if categoria.nombre is not None:
            updates.append("nombre = %s")
            params.append(categoria.nombre)
        
        if categoria.descripcion is not None:
            updates.append("descripcion = %s")
            params.append(categoria.descripcion)
        
        if categoria.activo is not None:
            updates.append("activo = %s")
            params.append(categoria.activo)
        
        if not updates:
            return existing[0]  # No hay cambios
        
        params.append(id_categoria)
        
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(f"""
                UPDATE categorias
                SET {', '.join(updates)}
                WHERE id_categoria = %s
                RETURNING id_categoria, nombre, descripcion, activo, fecha_registro
            """, tuple(params))
            
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
    
    except HTTPException:
        raise
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una categoría con el nombre '{categoria.nombre}'"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar categoría: {str(e)}"
        )


@router.delete("/{id_categoria}", response_model=MessageResponse)
def eliminar_categoria(id_categoria: int):
    """Eliminar una categoría (borrado lógico)"""
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                UPDATE categorias
                SET activo = FALSE
                WHERE id_categoria = %s
                RETURNING id_categoria
            """, (id_categoria,))
            
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Categoría con ID {id_categoria} no encontrada"
                )
            
            return {
                "message": "Categoría desactivada exitosamente",
                "detail": f"ID: {id_categoria}"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar categoría: {str(e)}"
        )
