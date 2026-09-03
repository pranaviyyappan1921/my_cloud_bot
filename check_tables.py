from utils.database import get_engine
from sqlalchemy import text

try:
    engine = get_engine()

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT name FROM sys.tables ORDER BY name")
        )

        tables = [row[0] for row in result]

    print("\nTables found in Azure SQL:")
    print("=========================")

    if tables:
        for table in tables:
            print(f"  {table}")
    else:
        print("  NO TABLES FOUND")

    print("=========================")
    print(f"Total tables: {len(tables)}")

except Exception as e:
    print("ERROR:")
    print(e)