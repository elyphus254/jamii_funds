import os
import django
import subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.db import connections

def reset_migration_state():
    print("=== RESETTING MIGRATION STATE ===")
    
    for db_name in connections:
        print(f"\nProcessing database: {db_name}")
        
        try:
            with connections[db_name].cursor() as cursor:
                # Check if django_migrations table exists
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = 'django_migrations'
                """)
                
                if cursor.fetchone():
                    # Table exists - truncate it
                    cursor.execute("TRUNCATE TABLE django_migrations")
                    print("✓ Cleared django_migrations table")
                else:
                    # Table doesn't exist - create it
                    cursor.execute("""
                        CREATE TABLE django_migrations (
                            id SERIAL PRIMARY KEY,
                            app VARCHAR(255) NOT NULL,
                            name VARCHAR(255) NOT NULL,
                            applied TIMESTAMP WITH TIME ZONE NOT NULL
                        )
                    """)
                    print("✓ Created django_migrations table")
                    
        except Exception as e:
            print(f"✗ Error with {db_name}: {e}")
    
    print("\n=== NOW RUNNING MIGRATIONS ===")
    
    # Run migrations for real
    result = subprocess.run(
        ['python', 'manage.py', 'migrate', '--settings=config.settings.base'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ Migrations applied successfully!")
        print(result.stdout)
    else:
        print("✗ Migration failed:")
        print(result.stderr)
        
    # Verify tables were created
    print("\n=== VERIFYING TABLES ===")
    for db_name in connections:
        print(f"\nChecking {db_name}:")
        try:
            with connections[db_name].cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = [t[0] for t in cursor.fetchall()]
                print(f"Tables found: {len(tables)}")
                for table in tables:
                    print(f"  - {table}")
        except Exception as e:
            print(f"Error checking {db_name}: {e}")

if __name__ == "__main__":
    reset_migration_state()
    