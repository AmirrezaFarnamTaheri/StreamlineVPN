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
                enabled BOOLEAN DEFAULT TRUE,
                fail_streak INTEGER DEFAULT 0,
                quarantined BOOLEAN DEFAULT 0
            )
        ''')
        # Helpful indexes for common queries
        try:
            conn.execute('CREATE INDEX IF NOT EXISTS idx_configs_protocol ON configs(protocol);')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_configs_quality ON configs(quality_score DESC);')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_configs_host ON configs(host);')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_configs_source ON configs(source_url);')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_sources_quarantined ON sources(quarantined);')
        except Exception:
            pass
        # Migrate missing columns if table pre-existed
        try:
            cursor = conn.execute('PRAGMA table_info(sources);')
            cols = {row[1] for row in cursor.fetchall()}
            if 'fail_streak' not in cols:
                try:
                    conn.execute('ALTER TABLE sources ADD COLUMN fail_streak INTEGER DEFAULT 0;')
                except Exception:
                    pass
            if 'quarantined' not in cols:
                try:
                    conn.execute('ALTER TABLE sources ADD COLUMN quarantined BOOLEAN DEFAULT 0;')
                except Exception:
                    pass
        except Exception:
            pass
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

    def has_config(self, config_url: str) -> bool:
        conn = self._connect()
        try:
            cur = conn.execute('SELECT 1 FROM configs WHERE config_url = ? LIMIT 1;', (config_url,))
            return cur.fetchone() is not None
        finally:
            conn.close()

    # --- Quarantine helpers ---
    def _ensure_source(self, conn: sqlite3.Connection, url: str) -> None:
        conn.execute('INSERT OR IGNORE INTO sources (url, enabled, fail_streak, quarantined) VALUES (?, 1, 0, 0);', (url,))

    def get_quarantined_sources(self) -> List[str]:
        conn = self._connect()
        try:
            cur = conn.execute('SELECT url FROM sources WHERE quarantined = 1;')
            return [r[0] for r in cur.fetchall()]
        finally:
            conn.close()

    def increment_fail_streak(self, url: str) -> int:
        conn = self._connect()
        try:
            self._ensure_source(conn, url)
            conn.execute('UPDATE sources SET fail_streak = fail_streak + 1 WHERE url = ?;', (url,))
            cur = conn.execute('SELECT fail_streak FROM sources WHERE url = ?;', (url,))
            val = cur.fetchone()
            conn.commit()
            return int(val[0]) if val else 1
        finally:
            conn.close()

    def reset_fail_streak(self, url: str) -> None:
        conn = self._connect()
        try:
            self._ensure_source(conn, url)
            conn.execute('UPDATE sources SET fail_streak = 0 WHERE url = ?;', (url,))
            conn.commit()
        finally:
            conn.close()

    def set_quarantined(self, url: str, value: bool) -> None:
        conn = self._connect()
        try:
            self._ensure_source(conn, url)
            conn.execute('UPDATE sources SET quarantined = ? WHERE url = ?;', (1 if value else 0, url))
            conn.commit()
        finally:
            conn.close()


