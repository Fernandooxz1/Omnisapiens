from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings

# pool_pre_ping: valida la conexión antes de prestarla, si no Postgres cerró
# una del pool mientras estaba inactiva y el pedido explota.
engine = create_async_engine(settings.database_url, pool_pre_ping=True)

# expire_on_commit=False: sin esto, leer un atributo después del commit dispara
# un SELECT extra que en async falla (MissingGreenlet).
session_factory = async_sessionmaker(engine, expire_on_commit=False)
