#!/usr/bin/env python3
"""
Database migration runner for Open-AutoGLM
"""

import os
import logging
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class MigrationRunner:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SECRET_KEY', os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase configuration. Please check SUPABASE_URL and SUPABASE_SECRET_KEY")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.migrations_dir = Path(__file__).parent

    def execute_sql(self, sql: str, migration_name: str):
        """Execute SQL migration"""
        try:
            # Split SQL by semicolons and execute each statement
            statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]

            for statement in statements:
                if statement:
                    # Use Supabase RPC to execute SQL
                    result = self.supabase.rpc('execute_sql', {'sql_query': statement}).execute()
                    logger.info(f"Executed statement in {migration_name}")

            logger.info(f"Successfully executed migration: {migration_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute migration {migration_name}: {e}")
            return False

    def run_migrations(self):
        """Run all pending migrations"""
        logger.info("Starting database migrations...")

        # Get all migration files
        migration_files = sorted([
            f for f in os.listdir(self.migrations_dir)
            if f.endswith('.sql') and f != 'migration_runner.py'
        ])

        logger.info(f"Found {len(migration_files)} migration files")

        success_count = 0
        total_count = len(migration_files)

        for migration_file in migration_files:
            migration_path = self.migrations_dir / migration_file
            migration_name = migration_path.stem

            logger.info(f"Running migration: {migration_name}")

            try:
                with open(migration_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()

                if self.execute_sql(sql_content, migration_name):
                    success_count += 1
                else:
                    logger.error(f"Migration failed: {migration_name}")
                    break

            except Exception as e:
                logger.error(f"Error reading migration file {migration_file}: {e}")
                break

        logger.info(f"Migration complete: {success_count}/{total_count} successful")
        return success_count == total_count

def main():
    """Main migration runner"""
    try:
        runner = MigrationRunner()
        success = runner.run_migrations()

        if success:
            logger.info("All migrations completed successfully!")
            exit(0)
        else:
            logger.error("Some migrations failed!")
            exit(1)

    except Exception as e:
        logger.error(f"Migration runner failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()