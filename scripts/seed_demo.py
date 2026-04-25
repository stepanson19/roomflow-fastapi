from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import Base, engine
from app.demo_data import seed_demo_data


def require_env(name: str) -> str:
    import os

    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Set {name}")
    return value


def main() -> None:
    import os

    require_env("ROOMFLOW_ADMIN_EMAIL")
    require_env("ROOMFLOW_ADMIN_PASSWORD")
    os.environ["ROOMFLOW_SEED_DEMO"] = "1"
    Base.metadata.create_all(bind=engine)
    from app.database import session_factory

    db = session_factory()
    try:
        seed_demo_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
