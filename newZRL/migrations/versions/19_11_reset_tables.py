"""reset tables teams, wtrl_riders, rider_teams"""

from alembic import op
import sqlalchemy as sa

# Revisione Alembic
revision = "xxxx_reset_tables"
down_revision = None  # oppure metti l'ID della migrazione precedente
branch_labels = None
depends_on = None


def upgrade():
    # Droppa prima le tabelle figlie per evitare errori di vincolo
    op.drop_table("rider_teams")
    op.drop_table("teams")
    op.drop_table("wtrl_riders")

    # Ricrea la tabella teams
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("trc", sa.Integer, unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(10)),
        sa.Column("division", sa.String(50)),
        sa.Column("wtrl_team_id", sa.Integer),
        sa.Column("jersey_name", sa.String(255)),
        sa.Column("jersey_image", sa.String(255)),
        sa.Column("recruiting", sa.Boolean, default=False),
        sa.Column("is_dev", sa.Boolean, default=False),
        sa.Column("competition_class", sa.String(50)),
        sa.Column("competition_season", sa.Integer),
        sa.Column("competition_year", sa.Integer),
        sa.Column("competition_round", sa.Integer),
        sa.Column("competition_status", sa.String(50)),
        sa.Column("member_count", sa.Integer, default=0),
        sa.Column("members_remaining", sa.Integer, default=0),
        sa.Column("captain_profile_id", sa.BigInteger),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Ricrea la tabella wtrl_riders
    op.create_table(
        "wtrl_riders",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("team_id", sa.Integer, sa.ForeignKey("teams.id")),
        sa.Column("name", sa.String(255)),
        sa.Column("tmuid", sa.Integer),
        sa.Column("avatar", sa.String(255)),
        sa.Column("member_status", sa.String(50)),
        sa.Column("signedup", sa.Boolean, default=False),
        sa.Column("category", sa.String(5)),
        sa.Column("zftp", sa.Float),
        sa.Column("zftpw", sa.Integer),
        sa.Column("zmapw", sa.Integer),
        sa.Column("zmap", sa.Float),
        sa.Column("riderpoints", sa.Integer, default=0),
        sa.Column("teams", sa.Integer, default=0),
        sa.Column("appearances_round", sa.Integer, default=0),
        sa.Column("appearances_season", sa.Integer, default=0),
        sa.Column("profile_id", sa.BigInteger, unique=True),
        sa.Column("user_id", sa.String(255), unique=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Ricrea la tabella rider_teams
    op.create_table(
        "rider_teams",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("rider_id", sa.Integer, sa.ForeignKey("wtrl_riders.id")),
        sa.Column("team_id", sa.Integer, sa.ForeignKey("teams.id")),
    )


def downgrade():
    op.drop_table("rider_teams")
    op.drop_table("wtrl_riders")
    op.drop_table("teams")
