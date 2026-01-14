import psycopg2
from psycopg2 import pool
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from contextlib import contextmanager
import os

# ==========================================
# CONFIGURACIÓN DE BASE DE DATOS
# ==========================================

# Detectar si estamos en modo Supabase o Local
USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

if USE_SUPABASE:
    # CONFIGURACIÓN SUPABASE
    DB_CONFIG = {
        "dbname": "postgres",
        "user": "postgres",
        "password": os.getenv("SUPABASE_DB_PASSWORD", "?8$UX3ATrZp%SmP"),  # ⚠️ CAMBIAR ESTO
        "host": "db.tlywccsyiwfdhpixbkjg.supabase.co",
        "port": "5432"
    }
    print("🌐 Usando SUPABASE como base de datos")
else:
    # CONFIGURACIÓN LOCAL
    DB_CONFIG = {
        "dbname": os.getenv("DB_NAME", "claud_store"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "Acancun71"),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432")
    }
    print("💻 Usando PostgreSQL LOCAL")

# Pool de conexiones para mejor rendimiento
connection_pool = None

def init_connection_pool():
    """Inicializa el pool de conexiones"""
    global connection_pool
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1,  # Mínimo de conexiones
            10,  # Máximo de conexiones
            **DB_CONFIG
        )
        
        # Configurar todas las conexiones del pool con UTF-8
        test_conn = connection_pool.getconn()
        test_conn.set_client_encoding('UTF8')
        cursor = test_conn.cursor()
        cursor.execute("SET CLIENT_ENCODING TO 'UTF8';")
        cursor.close()
        connection_pool.putconn(test_conn)
        
        print("✅ Pool de conexiones creado exitosamente con UTF-8")
    except Exception as e:
        print(f"❌ Error al crear pool de conexiones: {e}")
        raise

def get_db_connection():
    """Obtiene una conexión del pool"""
    global connection_pool
    if connection_pool is None:
        init_connection_pool()
    try:
        conn = connection_pool.getconn()
        if conn is None:
            raise Exception("No hay conexiones disponibles en el pool")
        # Forzar UTF-8 en cada conexión
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        cursor.execute("SET CLIENT_ENCODING TO 'UTF8';")
        cursor.close()
        conn.commit()
        return conn
    except Exception as e:
        print(f"❌ Error al obtener conexión: {e}")
        raise

def release_db_connection(conn):
    """Devuelve la conexión al pool"""
    global connection_pool
    if connection_pool and conn:
        connection_pool.putconn(conn)

@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager para manejar cursor de base de datos
    
    Args:
        commit (bool): Si es True, hace commit automático. False para solo lectura.
    
    Uso:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("INSERT INTO ...")
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        release_db_connection(conn)

def execute_query(query, params=None, fetch=True):
    """
    Ejecuta una consulta SQL y devuelve los resultados
    
    Args:
        query (str): Query SQL a ejecutar
        params (tuple): Parámetros para la query
        fetch (bool): Si es True, devuelve los resultados. False para INSERT/UPDATE/DELETE
    
    Returns:
        list: Lista de tuplas con los resultados (si fetch=True)
        int: Número de filas afectadas (si fetch=False)
    """
    with get_db_cursor(commit=not fetch) as cursor:
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        else:
            return cursor.rowcount

def execute_query_dict(query, params=None):
    """
    Ejecuta una consulta y devuelve los resultados como lista de diccionarios
    
    Args:
        query (str): Query SQL a ejecutar
        params (tuple): Parámetros para la query
    
    Returns:
        list: Lista de diccionarios con los resultados
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        cursor.close()
        return [dict(zip(columns, row)) for row in results]
    finally:
        release_db_connection(conn)

def close_all_connections():
    """Cierra todas las conexiones del pool"""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        print("✅ Todas las conexiones cerradas")