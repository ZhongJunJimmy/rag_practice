# libs/db.py
from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector
from libs.config import CONFIG

PG_DSN = CONFIG["PG_DSN"]

pool = ConnectionPool(
    conninfo=PG_DSN,
    min_size=1,
    max_size=5,
    kwargs={"autocommit": True}
)

def init_db():
    with pool.connection() as conn:
        register_vector(conn)

def get_conn():
    conn = pool.getconn()
    register_vector(conn)
    return conn

def put_conn(conn):
    pool.putconn(conn)