"""
Clean database script - drops all Phase 1 tables and indexes
"""
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:anirudh_84@localhost:5432/datacue'

engine = create_engine(DATABASE_URL)
conn = engine.connect()

print("Dropping all Phase 1 database objects...")

# First, drop all indexes explicitly
try:
    conn.execute(text("DROP INDEX IF EXISTS idx_datasets_session_id CASCADE"))
    conn.execute(text("DROP INDEX IF EXISTS idx_datasets_created_at CASCADE"))
    conn.execute(text("DROP INDEX IF EXISTS idx_datasetrows_dataset_id CASCADE"))
    conn.execute(text("DROP INDEX IF EXISTS idx_datasetrows_session_id CASCADE"))
    conn.execute(text("DROP INDEX IF EXISTS idx_datasetrows_row_number CASCADE"))
    print("✓ Indexes dropped")
except Exception as e:
    print(f"Warning: {e}")

# Drop tables with CASCADE
conn.execute(text('DROP TABLE IF EXISTS dataset_rows CASCADE'))
conn.execute(text('DROP TABLE IF EXISTS datasets CASCADE'))
print("✓ Tables dropped")

conn.commit()
conn.close()

print("✓ Database cleaned successfully")
print("✓ Ready to restart server")
