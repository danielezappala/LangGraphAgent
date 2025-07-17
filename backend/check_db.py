import sqlite3
import os

def check_database():
    db_path = 'backend/langgraph_agent.db'
    print(f"Checking database at: {os.path.abspath(db_path)}")
    
    if not os.path.exists(db_path):
        print("Database file does not exist.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\nTables in database:")
        for table in tables:
            print(f"- {table[0]}")
            
            # For each table, show its structure
            cursor.execute(f"PRAGMA table_info({table[0]});")
            columns = cursor.fetchall()
            print(f"  Columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        
        # Check if the table has any data
        if 'llm_providers' in [t[0] for t in tables]:
            cursor.execute("SELECT COUNT(*) FROM llm_providers;")
            count = cursor.fetchone()[0]
            print(f"\nNumber of providers in llm_providers: {count}")
            
            if count > 0:
                print("\nSample data:")
                cursor.execute("SELECT * FROM llm_providers LIMIT 5;")
                for row in cursor.fetchall():
                    print(row)
        
        conn.close()
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database()
