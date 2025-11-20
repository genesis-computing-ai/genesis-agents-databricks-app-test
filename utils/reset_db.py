
from sqlalchemy import create_engine, text
import os
import yaml
from pathlib import Path

# Read config - look for app.yaml in parent directory
app_yaml_path = Path(__file__).parent.parent / "app.yaml"
with open(app_yaml_path, "r") as f:
    config = yaml.safe_load(f)

local_conf = config["database_local"]
url = f"postgresql://{local_conf['user']}@{local_conf['host']}:{local_conf['port']}/{local_conf['database']}"

print(f"Connecting to {url}")
engine = create_engine(url)

with engine.connect() as conn:
    print("Connected.")
    # Drop tables
    print("Dropping tables...")
    conn.execute(text("DROP TABLE IF EXISTS todos CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    conn.commit()
    print("Tables dropped.")

