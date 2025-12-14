"""
Database Configuration
"""

import os
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """PostgreSQL connection configuration"""
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", 5432))
    database: str = os.getenv("DB_NAME", "price_index")
    user: str = os.getenv("PGUSER", "traviscua")
    password: str = os.getenv("PGPASSWORD", "")
    
    # Support for DATABASE_URL (common in cloud providers like Render/Heroku/Neon)
    database_url: str = os.getenv("DATABASE_URL", "")

    def get_connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def get_psycopg2_params(self) -> dict:
        """Get connection parameters for psycopg2"""
        if self.database_url:
            return {"dsn": self.database_url}
            
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password
        }

config = DatabaseConfig()

def get_db_connection():
    """Get a psycopg2 database connection"""
    import psycopg2
    params = config.get_psycopg2_params()
    # Handle DSN connection vs individual params
    if "dsn" in params:
        return psycopg2.connect(params["dsn"])
    return psycopg2.connect(**params)
