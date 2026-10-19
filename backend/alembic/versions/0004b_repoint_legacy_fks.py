"""repoint legacy history foreign keys to content_items

Revision ID: 0004b
Revises: 0004
Create Date: 2026-10-19 12:00:00.000000

Las dos tablas de historial viejo siguen escribiéndose hasta las fases 4 y 5, pero
desde 2.4 el banco sirve ids de `content_items`. Sin este cambio, la FK a
`questions` rechaza cualquier ítem importado después del corte del dual-write.
La tabla vieja queda de solo lectura y se puede dropear en la fase 10.

La FK nueva se crea `NOT VALID`: el backfill de contenido es un comando aparte y
puede no haber corrido todavía. Las filas nuevas se validan igual; las viejas que
queden huérfanas no impiden migrar.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004b"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLAS = ("arcade_answers", "match_rounds")


def _constraint(origen: str, destino: str) -> None:
    nombre = op.f(f"fk_{origen}_question_id")
    op.drop_constraint(nombre, origen, type_="foreignkey")
    # `NOT VALID` en vez de `op.create_foreign_key`: el historial viejo puede
    # referenciar preguntas que el backfill todavía no copió.
    op.execute(
        f"ALTER TABLE {origen} ADD CONSTRAINT {nombre} "
        f"FOREIGN KEY (question_id) REFERENCES {destino} (id) "
        "ON DELETE SET NULL NOT VALID"
    )


def upgrade() -> None:
    """Upgrade schema."""
    for tabla in _TABLAS:
        _constraint(tabla, "content_items")


def downgrade() -> None:
    """Downgrade schema."""
    for tabla in _TABLAS:
        _constraint(tabla, "questions")
