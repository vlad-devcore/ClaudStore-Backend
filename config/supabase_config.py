# ==========================================
# config/supabase_config.py
# ==========================================
"""
Configuración de Supabase para almacenamiento de imágenes
Por ahora está preparado pero no se usa (modo local)
"""

import os
from supabase import create_client, Client
from typing import Optional

# Configuración de Supabase (descomentar cuando estés listo para deploy)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "productos-imagenes")

# Cliente de Supabase (se inicializa cuando se necesite)
supabase_client: Optional[Client] = None

def init_supabase():
    """Inicializa el cliente de Supabase"""
    global supabase_client
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️  Supabase no configurado (usando almacenamiento local)")
        return None
    
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Cliente Supabase inicializado")
        return supabase_client
    except Exception as e:
        print(f"❌ Error al inicializar Supabase: {e}")
        return None

def upload_image(file_path: str, file_name: str) -> Optional[str]:
    """
    Sube una imagen a Supabase Storage
    
    Args:
        file_path (str): Ruta local del archivo
        file_name (str): Nombre con el que se guardará en Supabase
    
    Returns:
        str: URL pública de la imagen o None si falla
    """
    global supabase_client
    
    if supabase_client is None:
        supabase_client = init_supabase()
    
    if supabase_client is None:
        # Modo local: devolver ruta local
        return f"/static/images/{file_name}"
    
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Subir archivo a Supabase
        response = supabase_client.storage.from_(SUPABASE_BUCKET).upload(
            file_name, 
            file_data,
            {"content-type": "image/jpeg"}  # Ajustar según tipo de imagen
        )
        
        # Obtener URL pública
        public_url = supabase_client.storage.from_(SUPABASE_BUCKET).get_public_url(file_name)
        return public_url
    
    except Exception as e:
        print(f"❌ Error al subir imagen a Supabase: {e}")
        return None

def delete_image(file_name: str) -> bool:
    """
    Elimina una imagen de Supabase Storage
    
    Args:
        file_name (str): Nombre del archivo en Supabase
    
    Returns:
        bool: True si se eliminó correctamente
    """
    global supabase_client
    
    if supabase_client is None:
        supabase_client = init_supabase()
    
    if supabase_client is None:
        # Modo local: intentar eliminar archivo local
        try:
            local_path = f"static/images/{file_name}"
            if os.path.exists(local_path):
                os.remove(local_path)
            return True
        except Exception as e:
            print(f"❌ Error al eliminar imagen local: {e}")
            return False
    
    try:
        supabase_client.storage.from_(SUPABASE_BUCKET).remove([file_name])
        return True
    except Exception as e:
        print(f"❌ Error al eliminar imagen de Supabase: {e}")
        return False

def get_image_url(file_name: str) -> str:
    """
    Obtiene la URL de una imagen (local o Supabase)
    
    Args:
        file_name (str): Nombre del archivo
    
    Returns:
        str: URL de la imagen
    """
    global supabase_client
    
    if supabase_client is None:
        # Modo local
        return f"/static/images/{file_name}"
    
    try:
        return supabase_client.storage.from_(SUPABASE_BUCKET).get_public_url(file_name)
    except Exception as e:
        print(f"❌ Error al obtener URL de Supabase: {e}")
        return f"/static/images/{file_name}"