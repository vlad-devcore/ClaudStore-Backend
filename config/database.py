import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import os
from urllib.parse import quote_plus

# Detectar si estamos en modo Supabase o Local
USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

if USE_SUPABASE:
    # Usar DATABASE_URL completa
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise Exception("DATABASE_URL no está configurada")
    
    print("🌐 Usando SUPABASE POOLER como base de datos")
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

connection_pool = None

def init_connection_pool():
    """Inicializa el pool de conexiones"""
    global connection_pool
    try:
        if USE_SUPABASE:
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10,
                DATABASE_URL
            )
        else:
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10,
                **DB_CONFIG
            )
        
        # Configurar UTF-8
        test_conn = connection_pool.getconn()
        test_conn.set_client_encoding('UTF8')
        cursor = test_conn.cursor()
        cursor.execute("SET CLIENT_ENCODING TO 'UTF8';")
        cursor.close()
        connection_pool.putconn(test_conn)
        
        print("✅ Pool de conexiones creado exitosamente")
    except Exception as e:
        print(f"❌ Error al crear pool: {e}")
        raise

def get_db_connection():
    """Obtiene una conexión del pool"""
    global connection_pool
    if connection_pool is None:
        init_connection_pool()
    try:
        conn = connection_pool.getconn()
        if conn is None:
            raise Exception("No hay conexiones disponibles")
        conn.set_client_encoding('UTF8')
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
    """Context manager para cursor"""
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
    """Ejecuta una consulta SQL"""
    with get_db_cursor(commit=not fetch) as cursor:
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        else:
            return cursor.rowcount

def execute_query_dict(query, params=None):
    """Ejecuta consulta y devuelve diccionarios"""
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
    """Cierra todas las conexiones"""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        print("✅ Todas las conexiones cerradas")