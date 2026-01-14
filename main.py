from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Importar rutas
from routes import categorias, productos, ventas, compras, financiero, reportes, periodos

app = FastAPI(
    title="Sistema de Inventario API",
    description="API para gestión de inventario con PostgreSQL",
    version="1.0.0"
)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción cambiar a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear carpeta para imágenes locales si no existe
os.makedirs("static/images", exist_ok=True)

# Servir archivos estáticos (imágenes)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ruta de prueba
@app.get("/")
def read_root():
    return {
        "message": "API de Sistema de Inventario",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "activo"
    }

# Ruta de health check
@app.get("/health")
def health_check():
    from config.database import get_db_connection
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

# Incluir routers
app.include_router(categorias.router, prefix="/categorias", tags=["Categorías"])
app.include_router(productos.router, prefix="/productos", tags=["Productos"])
app.include_router(ventas.router, prefix="/ventas", tags=["Ventas"])
app.include_router(compras.router, prefix="/compras", tags=["Compras"])
app.include_router(financiero.router, prefix="/financiero", tags=["Financiero"])
app.include_router(reportes.router, prefix="/reportes", tags=["Reportes"])
app.include_router(periodos.router, prefix="/periodos", tags=["Períodos"])

if __name__ == "__main__":
    import uvicorn
    # Usar variable PORT de Render, o 8000 por defecto para desarrollo local
    port = int(os.getenv("PORT", 8000))
    # reload=False en producción para mejor rendimiento
    is_dev = os.getenv("ENVIRONMENT", "development") == "development"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=is_dev)