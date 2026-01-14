
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
from models.schemas import (
    ProductoCreate, ProductoUpdate, ProductoResponse, MessageResponse
)
from config.database import get_db_cursor, execute_query_dict
from utils.helpers import (
    generar_nombre_archivo, guardar_archivo_local, 
    eliminar_archivo_local, validar_imagen
)
from decimal import Decimal
import psycopg2

router = APIRouter()


@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_producto(producto: ProductoCreate):
    """Crear un nuevo producto"""
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO productos 
                (codigo_barras, nombre, descripcion, id_categoria, costo, 
                 precio_venta, stock, imagen_url, activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                producto.codigo_barras, producto.nombre, producto.descripcion,
                producto.id_categoria, producto.costo, producto.precio_venta,
                producto.stock, producto.imagen_url, producto.activo
            ))
            
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
    
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un producto con el código de barras '{producto.codigo_barras}'"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear producto: {str(e)}"
        )
    

@router.post("/con-imagen/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
async def crear_producto_con_imagen(
    codigo_barras: Optional[str] = Form(None),
    nombre: str = Form(...),
    descripcion: Optional[str] = Form(None),
    id_categoria: Optional[int] = Form(None),
    costo: float = Form(...),
    precio_venta: float = Form(...),
    stock: int = Form(0),
    activo: bool = Form(True),
    imagen: Optional[UploadFile] = File(None)
):
    """Crear producto con imagen"""
    try:
        imagen_url = None
        
        # Guardar imagen si se proporcionó
        if imagen:
            if not validar_imagen(imagen.filename):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de imagen no válido. Use: jpg, jpeg, png, gif, webp"
                )
            
            # Generar nombre único
            extension = imagen.filename.split('.')[-1]
            nombre_archivo = generar_nombre_archivo(extension)
            
            # Leer y guardar archivo
            contenido = await imagen.read()
            imagen_url = guardar_archivo_local(contenido, nombre_archivo)
        
        # Crear producto
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO productos 
                (codigo_barras, nombre, descripcion, id_categoria, costo, 
                 precio_venta, stock, imagen_url, activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                codigo_barras, nombre, descripcion, id_categoria,
                Decimal(str(costo)), Decimal(str(precio_venta)),
                stock, imagen_url, activo
            ))
            
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear producto: {str(e)}"
        )    


@router.put("/con-imagen/{id_producto}", response_model=ProductoResponse)
async def actualizar_producto_con_imagen(
    id_producto: int,
    codigo_barras: Optional[str] = Form(None),
    nombre: Optional[str] = Form(None),
    descripcion: Optional[str] = Form(None),
    id_categoria: Optional[int] = Form(None),
    costo: Optional[float] = Form(None),
    precio_venta: Optional[float] = Form(None),
    stock: Optional[int] = Form(None),
    activo: Optional[bool] = Form(None),
    imagen: Optional[UploadFile] = File(None)
):
    """Actualizar producto con imagen opcional"""
    try:
        # Verificar que el producto existe
        existing = execute_query_dict(
            "SELECT * FROM productos WHERE id_producto = %s",
            (id_producto,)
        )
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {id_producto} no encontrado"
            )
        
        producto_actual = existing[0]
        imagen_url = producto_actual.get('imagen_url')
        
        # Si se proporciona nueva imagen
        if imagen:
            if not validar_imagen(imagen.filename):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de imagen no válido. Use: jpg, jpeg, png, gif, webp"
                )
            
            # Eliminar imagen anterior si existe
            if imagen_url:
                eliminar_archivo_local(imagen_url)
            
            # Guardar nueva imagen
            extension = imagen.filename.split('.')[-1]
            nombre_archivo = generar_nombre_archivo(extension)
            contenido = await imagen.read()
            imagen_url = guardar_archivo_local(contenido, nombre_archivo)
        
        # Construir actualización dinámica
        updates = []
        params = []
        
        if codigo_barras is not None:
            updates.append("codigo_barras = %s")
            params.append(codigo_barras)
        
        if nombre is not None:
            updates.append("nombre = %s")
            params.append(nombre)
        
        if descripcion is not None:
            updates.append("descripcion = %s")
            params.append(descripcion)
        
        if id_categoria is not None:
            updates.append("id_categoria = %s")
            params.append(id_categoria)
        
        if costo is not None:
            updates.append("costo = %s")
            params.append(Decimal(str(costo)))
        
        if precio_venta is not None:
            updates.append("precio_venta = %s")
            params.append(Decimal(str(precio_venta)))
        
        if stock is not None:
            updates.append("stock = %s")
            params.append(stock)
        
        if activo is not None:
            updates.append("activo = %s")
            params.append(activo)
        
        # Actualizar imagen_url si cambió
        if imagen:
            updates.append("imagen_url = %s")
            params.append(imagen_url)
        
        if not updates:
            return producto_actual
        
        params.append(id_producto)
        
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(f"""
                UPDATE productos
                SET {', '.join(updates)}
                WHERE id_producto = %s
                RETURNING *
            """, tuple(params))
            
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar producto: {str(e)}"
        )


@router.get("/", response_model=List[ProductoResponse])
def listar_productos(
    activo: Optional[bool] = None,
    id_categoria: Optional[int] = None,
    nombre: Optional[str] = None,
    stock_minimo: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """Listar productos con filtros opcionales"""
    try:
        query = """
            SELECT p.*, c.nombre as categoria_nombre,
                   (p.precio_venta - p.costo) as margen_ganancia,
                   CASE WHEN p.costo > 0 
                        THEN ((p.precio_venta - p.costo) / p.costo * 100)
                        ELSE 0 
                   END as porcentaje_ganancia
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
            WHERE 1=1
        """
        params = []
        
        if activo is not None:
            query += " AND p.activo = %s"
            params.append(activo)
        
        if id_categoria is not None:
            query += " AND p.id_categoria = %s"
            params.append(id_categoria)
        
        if nombre:
            query += " AND p.nombre ILIKE %s"
            params.append(f"%{nombre}%")
        
        if stock_minimo is not None:
            query += " AND p.stock <= %s"
            params.append(stock_minimo)
        
        query += " ORDER BY p.nombre LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        return execute_query_dict(query, tuple(params))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar productos: {str(e)}"
        )


@router.get("/barcode/{codigo_barras}", response_model=ProductoResponse)
def buscar_por_codigo_barras(codigo_barras: str):
    """Buscar producto por código de barras"""
    try:
        query = """
            SELECT p.*, c.nombre as categoria_nombre,
                   (p.precio_venta - p.costo) as margen_ganancia,
                   CASE WHEN p.costo > 0 
                        THEN ((p.precio_venta - p.costo) / p.costo * 100)
                        ELSE 0 
                   END as porcentaje_ganancia
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
            WHERE p.codigo_barras = %s
        """
        
        result = execute_query_dict(query, (codigo_barras,))
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con código de barras '{codigo_barras}' no encontrado"
            )
        
        return result[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al buscar producto: {str(e)}"
        )


@router.get("/{id_producto}", response_model=ProductoResponse)
def obtener_producto(id_producto: int):
    """Obtener un producto por ID"""
    try:
        query = """
            SELECT p.*, c.nombre as categoria_nombre,
                   (p.precio_venta - p.costo) as margen_ganancia,
                   CASE WHEN p.costo > 0 
                        THEN ((p.precio_venta - p.costo) / p.costo * 100)
                        ELSE 0 
                   END as porcentaje_ganancia
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
            WHERE p.id_producto = %s
        """
        
        result = execute_query_dict(query, (id_producto,))
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {id_producto} no encontrado"
            )
        
        return result[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener producto: {str(e)}"
        )


@router.put("/{id_producto}", response_model=ProductoResponse)
def actualizar_producto(id_producto: int, producto: ProductoUpdate):
    """Actualizar un producto"""
    try:
        # Verificar que existe
        existing = execute_query_dict(
            "SELECT * FROM productos WHERE id_producto = %s",
            (id_producto,)
        )
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {id_producto} no encontrado"
            )
        
        # Construir query dinámicamente
        updates = []
        params = []
        
        if producto.codigo_barras is not None:
            updates.append("codigo_barras = %s")
            params.append(producto.codigo_barras)
        
        if producto.nombre is not None:
            updates.append("nombre = %s")
            params.append(producto.nombre)
        
        if producto.descripcion is not None:
            updates.append("descripcion = %s")
            params.append(producto.descripcion)
        
        if producto.id_categoria is not None:
            updates.append("id_categoria = %s")
            params.append(producto.id_categoria)
        
        if producto.costo is not None:
            updates.append("costo = %s")
            params.append(producto.costo)
        
        if producto.precio_venta is not None:
            updates.append("precio_venta = %s")
            params.append(producto.precio_venta)
        
        if producto.stock is not None:
            updates.append("stock = %s")
            params.append(producto.stock)
        
        if producto.imagen_url is not None:
            updates.append("imagen_url = %s")
            params.append(producto.imagen_url)
        
        if producto.activo is not None:
            updates.append("activo = %s")
            params.append(producto.activo)
        
        if not updates:
            return existing[0]
        
        params.append(id_producto)
        
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(f"""
                UPDATE productos
                SET {', '.join(updates)}
                WHERE id_producto = %s
                RETURNING *
            """, tuple(params))
            
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar producto: {str(e)}"
        )


@router.delete("/{id_producto}", response_model=MessageResponse)
def eliminar_producto(id_producto: int, eliminar_fisicamente: bool = False):
    """
    Eliminar un producto
    - Por defecto: borrado lógico (activo = false)
    - eliminar_fisicamente=true: borrado físico (si no tiene ventas/compras)
    """
    try:
        if eliminar_fisicamente:
            # Verificar que no tenga ventas o compras
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM ventas WHERE id_producto = %s) as ventas,
                        (SELECT COUNT(*) FROM compras WHERE id_producto = %s) as compras
                """, (id_producto, id_producto))
                
                result = cursor.fetchone()
                ventas, compras = result
                
                if ventas > 0 or compras > 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"No se puede eliminar: el producto tiene {ventas} ventas y {compras} compras registradas"
                    )
            
            # Obtener imagen para eliminar
            producto = execute_query_dict(
                "SELECT imagen_url FROM productos WHERE id_producto = %s",
                (id_producto,)
            )
            
            if producto and producto[0].get('imagen_url'):
                eliminar_archivo_local(producto[0]['imagen_url'])
            
            # Eliminar producto
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("""
                    DELETE FROM productos
                    WHERE id_producto = %s
                    RETURNING id_producto
                """, (id_producto,))
                
                result = cursor.fetchone()
                
                if not result:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Producto con ID {id_producto} no encontrado"
                    )
            
            return {
                "message": "Producto eliminado físicamente",
                "detail": f"ID: {id_producto}"
            }
        
        else:
            # Borrado lógico
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("""
                    UPDATE productos
                    SET activo = FALSE
                    WHERE id_producto = %s
                    RETURNING id_producto
                """, (id_producto,))
                
                result = cursor.fetchone()
                
                if not result:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Producto con ID {id_producto} no encontrado"
                    )
            
            return {
                "message": "Producto desactivado exitosamente",
                "detail": f"ID: {id_producto}"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar producto: {str(e)}"
        )
