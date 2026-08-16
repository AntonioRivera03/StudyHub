from pathlib import Path

from alembic.config import Config

from alembic import command
from app.core.settings import Settings


def upgrade_database(settings: Settings) -> None:
    server_root = Path(__file__).resolve().parents[2]
    config = Config(server_root / "alembic.ini")
    config.set_main_option("script_location", str(server_root / "alembic"))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
