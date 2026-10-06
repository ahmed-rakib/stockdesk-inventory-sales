import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
(ROOT / 'data').mkdir(exist_ok=True)
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{(ROOT / "data" / "stockdesk.db").as_posix()}')
engine = create_engine(DATABASE_URL, pool_pre_ping=True,
    connect_args={'check_same_thread': False, 'timeout': 20} if DATABASE_URL.startswith('sqlite') else {})

if DATABASE_URL.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def sqlite_connect(connection, _):
        connection.isolation_level = None
        connection.execute('PRAGMA foreign_keys=ON')

    @event.listens_for(engine, 'begin')
    def sqlite_begin(connection):
        # SQLite has no SELECT FOR UPDATE. Serialize transactions for this local demo.
        connection.exec_driver_sql('BEGIN IMMEDIATE')

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(engine, expire_on_commit=False)

def get_db():
    with SessionLocal() as session:
        with session.begin():
            yield session
