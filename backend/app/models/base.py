from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Sin nombres propios, Postgres bautiza los constraints ("questions_check1") y
# cada migración que los toque tiene que adivinarlos. Los patrones usan
# `column_0_N_name`: todas las columnas del constraint, no solo la primera.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    # Un CHECK cruza varias columnas y no hay patrón legible que lo derive, así
    # que toma el nombre que le da el modelo. Consecuencia: todo CheckConstraint
    # está obligado a declarar `name=`, y SQLAlchemy avisa si falta.
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
