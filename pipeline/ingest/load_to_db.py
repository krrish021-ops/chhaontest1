"""
Load the analysis grid into PostGIS database.
==============================================
This lets us do fast spatial queries later, like:
  "Which grid cells are within 2km of Futala Lake?"
"""

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine
from config.loader import get_db_url


def main():
    print("🗄️  Loading grid into PostGIS...")

    # 1. Read the grid GeoJSON
    grid = gpd.read_file("data/boundaries/nagpur_grid.geojson")
    print(f"   Read {len(grid)} grid cells from GeoJSON")

    # 2. Connect to database
    db_url = get_db_url()
    engine = create_engine(db_url)
    print(f"   Connected to database")

    # 3. Write to PostGIS
    grid.to_postgis(
        name="nagpur_grid",
        con=engine,
        if_exists="replace",
        index=False
    )
    print(f"   ✅ Table 'nagpur_grid' created in PostGIS")

    # 4. Verify by reading back using pandas
    result = pd.read_sql(
        "SELECT cell_id, lon_center, lat_center FROM nagpur_grid LIMIT 5",
        con=engine
    )
    print(f"\n   First 5 cells in database:")
    print(result.to_string(index=False))
    print(f"\n   Total cells in DB: {len(grid)}")


if __name__ == "__main__":
    main()
