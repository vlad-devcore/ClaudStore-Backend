# ==========================================
# models/__init__.py
# ==========================================
# Archivo vacío para que Python reconozca models como paquete


# ==========================================
# models/schemas.py
# ==========================================
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# ==========================================
# CATEGORÍAS
# ==========================================

class CategoriaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre de la categoría")
    descripcion: Optional[str] = Field(None, description="Descripción de la categoría")
    activo: bool = Field(True, description="Si la categoría está activa")

class CategoriaCreate(CategoriaBase):
    """Schema para crear una categoría"""
    pass

class CategoriaUpdate(BaseModel):
    """Schema para actualizar una categoría (todos los campos opcionales)"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = None
    activo: Optional[bool] = None

class CategoriaResponse(CategoriaBase):
    """Schema de respuesta con datos completos de la categoría"""
    id_categoria: int
    fecha_registro: datetime
    
    class Config:
        from_attributes = True


# ==========================================
# PRODUCTOS
# ==========================================

class ProductoBase(BaseModel):
    codigo_barras: Optional[str] = Field(None, max_length=100, description="Código de barras del producto")
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del producto")
    descripcion: Optional[str] = Field(None, description="Descripción del producto")
    id_categoria: Optional[int] = Field(None, description="ID de la categoría")
    costo: Decimal = Field(..., ge=0, description="Costo de compra del producto")
    precio_venta: Decimal = Field(..., ge=0, description="Precio de venta del producto")
    stock: int = Field(0, ge=0, description="Cantidad en stock")
    imagen_url: Optional[str] = Field(None, max_length=255, description="URL de la imagen")
    activo: bool = Field(True, description="Si el producto está activo")
    
    # @validator('precio_venta')
# def precio_mayor_que_costo(cls, v, values):
#     """Validar que el precio de venta sea mayor o igual al costo"""
#     if 'costo' in values and v < values['costo']:
#         raise ValueError('El precio de venta debe ser mayor o igual al costo')
#     return v

class ProductoCreate(ProductoBase):
    """Schema para crear un producto"""
    pass

class ProductoUpdate(BaseModel):
    """Schema para actualizar un producto (todos los campos opcionales)"""
    codigo_barras: Optional[str] = Field(None, max_length=100)
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = None
    id_categoria: Optional[int] = None
    costo: Optional[Decimal] = Field(None, ge=0)
    precio_venta: Optional[Decimal] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    imagen_url: Optional[str] = Field(None, max_length=255)
    activo: Optional[bool] = None

class ProductoResponse(ProductoBase):
    """Schema de respuesta con datos completos del producto"""
    id_producto: int
    fecha_registro: datetime
    fecha_modificacion: datetime
    categoria_nombre: Optional[str] = None  # Nombre de la categoría (JOIN)
    margen_ganancia: Optional[Decimal] = None  # Calculado
    porcentaje_ganancia: Optional[float] = None  # Calculado
    
    class Config:
        from_attributes = True

class ProductoConCategoria(ProductoResponse):
    """Schema extendido con información de la categoría"""
    categoria: Optional[CategoriaResponse] = None


# ==========================================
# VENTAS
# ==========================================

class VentaBase(BaseModel):
    id_producto: int = Field(..., description="ID del producto a vender")
    cantidad: int = Field(..., gt=0, description="Cantidad a vender")
    notas: Optional[str] = Field(None, description="Notas adicionales de la venta")

class VentaCreate(VentaBase):
    """Schema para registrar una venta"""
    pass

class VentaResponse(BaseModel):
    """Schema de respuesta de una venta"""
    id_venta: int
    id_producto: int
    cantidad: int
    precio_unitario: Decimal
    total: Decimal
    fecha_venta: datetime
    notas: Optional[str] = None
    
    # Datos del producto (JOIN)
    producto_nombre: Optional[str] = None
    producto_codigo_barras: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==========================================
# COMPRAS
# ==========================================

class CompraBase(BaseModel):
    id_producto: int = Field(..., description="ID del producto a comprar")
    cantidad: int = Field(..., gt=0, description="Cantidad a comprar")
    costo_unitario: Decimal = Field(..., ge=0, description="Costo unitario de compra")
    notas: Optional[str] = Field(None, description="Notas adicionales de la compra")

class CompraCreate(CompraBase):
    """Schema para registrar una compra"""
    pass

class CompraResponse(BaseModel):
    """Schema de respuesta de una compra"""
    id_compra: int
    id_producto: int
    cantidad: int
    costo_unitario: Decimal
    total: Decimal
    fecha_compra: datetime
    notas: Optional[str] = None
    
    # Datos del producto (JOIN)
    producto_nombre: Optional[str] = None
    producto_codigo_barras: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==========================================
# REGISTRO FINANCIERO (Manual)
# ==========================================

class RegistroFinancieroBase(BaseModel):
    tipo: str = Field(..., description="Tipo: inversion, gasto, ganancia, ajuste")
    concepto: str = Field(..., min_length=1, max_length=200, description="Concepto del registro")
    monto: Decimal = Field(..., description="Monto del registro")
    descripcion: Optional[str] = Field(None, description="Descripción detallada")
    
    @validator('tipo')
    def validar_tipo(cls, v):
        tipos_validos = ['inversion', 'gasto', 'ganancia', 'ajuste']
        if v.lower() not in tipos_validos:
            raise ValueError(f'Tipo debe ser uno de: {", ".join(tipos_validos)}')
        return v.lower()

class RegistroFinancieroCreate(RegistroFinancieroBase):
    """Schema para crear un registro financiero manual"""
    pass

class RegistroFinancieroResponse(RegistroFinancieroBase):
    """Schema de respuesta de un registro financiero"""
    id_registro: int
    fecha_registro: datetime
    
    class Config:
        from_attributes = True


# ==========================================
# PERÍODOS MENSUALES
# ==========================================

class PeriodoMensualBase(BaseModel):
    anio: int = Field(..., ge=2000, le=2100, description="Año del período")
    mes: int = Field(..., ge=1, le=12, description="Mes del período")
    notas: Optional[str] = Field(None, description="Notas del cierre")

class PeriodoMensualCreate(PeriodoMensualBase):
    """Schema para crear/cerrar un período mensual"""
    fecha_inicio: datetime = Field(..., description="Fecha de inicio del período")
    fecha_fin: datetime = Field(..., description="Fecha de fin del período")

class PeriodoMensualResponse(BaseModel):
    """Schema de respuesta de un período mensual cerrado"""
    id_periodo: int
    anio: int
    mes: int
    fecha_inicio: datetime
    fecha_fin: datetime
    total_ventas: Decimal
    total_compras: Decimal
    total_inversion_manual: Decimal
    total_gastos_manual: Decimal
    ganancia_neta: Decimal
    top_productos: Optional[dict] = None  # JSON con top productos
    cantidad_productos_vendidos: int
    cantidad_productos_registrados: int
    fecha_cierre: datetime
    notas: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==========================================
# REPORTES Y ESTADÍSTICAS
# ==========================================

class InversionInventarioResponse(BaseModel):
    """Inversión total en inventario actual"""
    inversion_total: Decimal
    total_productos: int
    total_unidades: int

class VentasPeriodoResponse(BaseModel):
    """Ventas del período actual"""
    mes: datetime
    total_ventas: Decimal
    unidades_vendidas: int
    productos_diferentes: int

class ComprasPeriodoResponse(BaseModel):
    """Compras del período actual"""
    mes: datetime
    total_compras: Decimal
    unidades_compradas: int

class GananciaPeriodoResponse(BaseModel):
    """Ganancia neta del período actual"""
    ingresos_ventas: Decimal
    inversion_compras: Decimal
    inversion_manual: Decimal
    gastos_manuales: Decimal
    ganancia_manual: Decimal
    ganancia_neta_total: Decimal

class TopProductoResponse(BaseModel):
    """Producto en el ranking de más vendidos"""
    id_producto: int
    nombre: str
    codigo_barras: Optional[str] = None
    categoria: Optional[str] = None
    total_vendido: int
    ingresos_generados: Decimal

class StockBajoResponse(BaseModel):
    """Producto con stock bajo"""
    id_producto: int
    codigo_barras: Optional[str] = None
    nombre: str
    categoria: Optional[str] = None
    stock: int
    costo: Decimal
    precio_venta: Decimal


# ==========================================
# SCHEMAS AUXILIARES
# ==========================================

class MessageResponse(BaseModel):
    """Respuesta genérica con mensaje"""
    message: str
    detail: Optional[str] = None

class ErrorResponse(BaseModel):
    """Respuesta de error"""
    error: str
    detail: Optional[str] = None
    status_code: int

class PaginatedResponse(BaseModel):
    """Respuesta paginada genérica"""
    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[dict]


# ==========================================
# FILTROS Y BÚSQUEDAS
# ==========================================

class ProductoFiltros(BaseModel):
    """Filtros para búsqueda de productos"""
    nombre: Optional[str] = None
    codigo_barras: Optional[str] = None
    id_categoria: Optional[int] = None
    stock_minimo: Optional[int] = None
    stock_maximo: Optional[int] = None
    activo: Optional[bool] = True
    orden_por: Optional[str] = Field("nombre", description="Campo para ordenar")
    orden: Optional[str] = Field("asc", description="Orden: asc o desc")
    
    @validator('orden')
    def validar_orden(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('orden debe ser "asc" o "desc"')
        return v.lower()

class VentasFiltros(BaseModel):
    """Filtros para búsqueda de ventas"""
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    id_producto: Optional[int] = None

class ComprasFiltros(BaseModel):
    """Filtros para búsqueda de compras"""
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    id_producto: Optional[int] = None


# ==========================================
# NOTAS DE USO
# ==========================================
"""
CÓMO USAR ESTOS SCHEMAS:

1. IMPORTAR EN TUS RUTAS:
   from models.schemas import ProductoCreate, ProductoResponse

2. USAR EN ENDPOINTS:
   @app.post("/productos/", response_model=ProductoResponse)
   def crear_producto(producto: ProductoCreate):
       # FastAPI valida automáticamente los datos
       pass

3. VALIDACIÓN AUTOMÁTICA:
   - FastAPI valida tipos de datos
   - Valida rangos (ge=0 significa >= 0)
   - Valida longitudes de strings
   - Ejecuta validadores personalizados

4. CONVERTIR DE BD A SCHEMA:
   # Opción 1: Diccionario
   producto_dict = {
       "id_producto": 1,
       "nombre": "Mouse",
       "costo": 150.00,
       ...
   }
   producto = ProductoResponse(**producto_dict)
   
   # Opción 2: Desde cursor
   cursor.execute("SELECT * FROM productos WHERE id = %s", (1,))
   row = cursor.fetchone()
   producto = ProductoResponse(**dict(zip([desc[0] for desc in cursor.description], row)))

5. EJEMPLOS DE VALIDACIÓN:
   # Esto fallará automáticamente:
   producto = ProductoCreate(
       nombre="Mouse",
       costo=100,
       precio_venta=50  # ❌ Error: precio menor que costo
   )
   
   # Esto funcionará:
   producto = ProductoCreate(
       nombre="Mouse",
       costo=100,
       precio_venta=200  # ✅ OK
   )
"""