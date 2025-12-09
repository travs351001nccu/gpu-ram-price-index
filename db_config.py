"""
Database Configuration
"""

import os
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """PostgreSQL connection configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "price_index"
    user: str = os.getenv("PGUSER", "traviscua")
    password: str = os.getenv("PGPASSWORD", "")
    
    def get_connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def get_psycopg2_params(self) -> dict:
        """Get connection parameters for psycopg2"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password
        }

config = DatabaseConfig()
