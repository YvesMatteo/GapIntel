
import os
import sys
import argparse
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import urllib.parse

def get_db_connection():
    """Establish a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ Error: DATABASE_URL environment variable is not set.")
        print("   Please set it in the format: postgres://user:password@host:port/dbname")
        sys.exit(1)
    
    try:
        # Verify it's a valid URL format
        result = urllib.parse.urlparse(db_url)
        if not result.scheme or not result.netloc:
             print("❌ Error: DATABASE_URL appears invalid.")
             sys.exit(1)
             
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

def execute_query(query, description="Executing query"):
    """Execute a single SQL query."""
    print(f"🔄 {description}...")
    conn = get_db_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            
            # Try to fetch results if it's a SELECT
            if cur.description:
                rows = cur.fetchall()
                print(f"✅ Query executed successfully. Rows returned: {len(rows)}")
                for row in rows:
                    print(f"   {row}")
            else:
                print("✅ Query executed successfully (No rows returned).")
                
    except Exception as e:
        print(f"❌ Query execution failed: {e}")
        sys.exit(1)
    finally:
        conn.close()

def execute_file(file_path):
    """Execute SQL commands from a file."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
        
    print(f"🔄 Executing SQL file: {file_path}...")
    
    with open(file_path, 'r') as f:
        sql_content = f.read()
        
    conn = get_db_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    try:
        with conn.cursor() as cur:
            cur.execute(sql_content)
        print(f"✅ Successfully executed {file_path}")
    except Exception as e:
        print(f"❌ Execution failed for {file_path}: {e}")
        sys.exit(1)
    finally:
        conn.close()

def test_connection():
    """Test the database connection."""
    execute_query("SELECT version();", "Testing database connection")

def main():
    parser = argparse.ArgumentParser(description="Manage Supabase Database via Direct SQL")
    parser.add_argument("--test", action="store_true", help="Test database connection")
    parser.add_argument("--query", type=str, help="Execute a raw SQL query")
    parser.add_argument("--file", type=str, help="Execute an SQL file")
    
    args = parser.parse_args()
    
    if args.test:
        test_connection()
    elif args.query:
        execute_query(args.query)
    elif args.file:
        execute_file(args.file)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
