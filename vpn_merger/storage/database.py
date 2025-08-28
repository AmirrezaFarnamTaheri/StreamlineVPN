import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class ConfigEntry:
    id: int
    config_url: str
    protocol: str
    host: str
    port: int
    ping_ms: float
    success_rate: float
    last_tested: datetime
    quality_score: float
    geographic_region: str
    source_url: str


class VPNDatabase:
    def __init__(self, db_path: str = "vpn_configs.db"):
        self.db_path = db_path
        self.init_database()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def init_database(self):
        conn = self._connect()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_url TEXT UNIQUE,
                protocol TEXT,
                host TEXT,
                port INTEGER,
                ping_ms REAL,
                success_rate REAL,
                last_tested TIMESTAMP,
                quality_score REAL,
                geographic_region TEXT,
                source_url TEXT,
                raw_config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS testing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id INTEGER,
                test_timestamp TIMESTAMP,
                ping_ms REAL,
                success BOOLEAN,
                error_message TEXT,
                FOREIGN KEY (config_id) REFERENCES configs (id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                last_fetched TIMESTAMP,
                configs_found INTEGER,
                success_rate REAL,
                enabled BOOLEAN DEFAULT TRUE
            )
        ''')
        conn.commit()
        conn.close()

    def store_config(self, config_result: Any) -> None:
        conn = self._connect()
        try:
            conn.execute(
                '''INSERT OR IGNORE INTO configs (config_url, protocol, host, port, ping_ms, success_rate, last_tested, quality_score, geographic_region, source_url, raw_config)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    getattr(config_result, 'config', None),
                    getattr(config_result, 'protocol', None),
                    getattr(config_result, 'host', None),
                    getattr(config_result, 'port', None),
                    (getattr(config_result, 'ping_time', None) or 0.0) * 1000.0,
                    getattr(config_result, 'success_rate', None) or 0.0,
                    datetime.utcnow().isoformat(),
                    getattr(config_result, 'quality_score', None) or 0.0,
                    getattr(config_result, 'geographic_region', None) or '',
                    getattr(config_result, 'source_url', None) or '',
                    getattr(config_result, 'config', None) or '',
                )
            )
            conn.commit()
        finally:
            conn.close()

    def get_best_configs(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = self._connect()
        try:
            cursor = conn.execute(
                'SELECT config_url, protocol, host, port, ping_ms, quality_score FROM configs ORDER BY quality_score DESC, ping_ms ASC LIMIT ?;',
                (limit,)
            )
            rows = cursor.fetchall()
            return [
                {
                    'config_url': r[0],
                    'protocol': r[1],
                    'host': r[2],
                    'port': r[3],
                    'ping_ms': r[4],
                    'quality_score': r[5],
                }
                for r in rows
            ]
        finally:
            conn.close()


