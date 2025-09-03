#!/usr/bin/env python3
"""
VPN Management Telegram Bot
Comprehensive multi-panel VPN management with advanced features
"""

import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Any

import aiohttp
import psutil
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("vpn_bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class VPNManagementBot:
    def __init__(self, bot_token: str, panels_config: dict[str, Any], db_path: str = "vpn_bot.db"):
        self.bot_token = bot_token
        self.panels = panels_config
        self.db_path = db_path
        self.authorized_users = set()
        self.admin_users = set()
        self.session = None
        self.db = None

        # Security settings
        self.rate_limit = {}  # IP-based rate limiting
        self.max_requests_per_minute = 30
        self.session_timeout = 3600  # 1 hour

        # Initialize database
        self.init_database()

        # Load authorized users
        self.load_authorized_users()

    def init_database(self):
        """Initialize SQLite database"""
        self.db = sqlite3.connect(self.db_path)
        cursor = self.db.cursor()

        # Create tables
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                user_id INTEGER,
                session_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vpn_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER,
                panel_name TEXT,
                panel_user_id TEXT,
                username TEXT,
                email TEXT,
                data_limit_gb INTEGER,
                data_used_gb REAL DEFAULT 0,
                days_remaining INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (telegram_user_id) REFERENCES users (user_id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                panel_name TEXT,
                total_users INTEGER,
                active_users INTEGER,
                total_traffic_gb REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        self.db.commit()

    def load_authorized_users(self):
        """Load authorized users from database"""
        cursor = self.db.cursor()
        cursor.execute("SELECT user_id, role FROM users WHERE is_active = 1")
        for user_id, role in cursor.fetchall():
            self.authorized_users.add(user_id)
            if role == "admin":
                self.admin_users.add(user_id)

    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized"""
        return user_id in self.authorized_users

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admin_users

    def rate_limit_check(self, user_id: int) -> bool:
        """Check rate limiting for user"""
        now = datetime.now()
        if user_id not in self.rate_limit:
            self.rate_limit[user_id] = []

        # Remove old requests
        self.rate_limit[user_id] = [
            req_time for req_time in self.rate_limit[user_id] if (now - req_time).seconds < 60
        ]

        if len(self.rate_limit[user_id]) >= self.max_requests_per_minute:
            return False

        self.rate_limit[user_id].append(now)
        return True

    def log_action(self, user_id: int, action: str, details: str = ""):
        """Log user actions"""
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO bot_actions (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, action, details),
        )
        self.db.commit()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bot startup command"""
        user_id = update.effective_user.id

        if not self.is_authorized(user_id):
            await update.message.reply_text(
                "⚠️ **Unauthorized Access!**\n\n"
                "You are not authorized to use this bot. "
                "Please contact an administrator.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Check rate limiting
        if not self.rate_limit_check(user_id):
            await update.message.reply_text(
                "⚠️ **Rate Limit Exceeded!**\n\n"
                "Please wait a moment before making another request.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Log action
        self.log_action(user_id, "start", "Bot started")

        # Create main menu
        keyboard = [
            [KeyboardButton("📊 Dashboard"), KeyboardButton("👥 Users")],
            [KeyboardButton("📡 Servers"), KeyboardButton("📈 Analytics")],
            [KeyboardButton("⚙️ Settings"), KeyboardButton("🔄 Actions")],
        ]

        if self.is_admin(user_id):
            keyboard.append([KeyboardButton("🔧 Admin Panel")])

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        # Build welcome message
        welcome_text = f"""
🚀 **VPN Management Bot v2.0**

Welcome back, {update.effective_user.first_name}!

**Connected Panels:**
"""

        for panel_name, config in self.panels.items():
            status = "🟢" if await self.check_panel_health(panel_name) else "🔴"
            welcome_text += f"{status} **{panel_name.upper()}** ({config['type']})\n"

        welcome_text += f"\n**Your Role:** {'👑 Admin' if self.is_admin(user_id) else '👤 User'}"

        await update.message.reply_text(
            welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def check_panel_health(self, panel_name: str) -> bool:
        """Check if panel is responsive"""
        try:
            config = self.panels[panel_name]
            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.get(f"{config['url']}/health", timeout=5) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Health check failed for {panel_name}: {e}")
            return False

    async def dashboard_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show comprehensive dashboard"""
        user_id = update.effective_user.id

        if not self.rate_limit_check(user_id):
            await update.message.reply_text("⚠️ Rate limit exceeded!")
            return

        self.log_action(user_id, "dashboard", "Dashboard accessed")

        dashboard_text = "📊 **System Dashboard**\n\n"

        # System overview
        total_users = 0
        active_users = 0
        total_traffic = 0.0

        for panel_name, config in self.panels.items():
            try:
                stats = await self.get_panel_stats(panel_name)
                dashboard_text += f"**{panel_name.upper()}:**\n"
                dashboard_text += f"👥 Users: {stats.get('users', 'N/A')}\n"
                dashboard_text += f"📊 Active: {stats.get('active_users', 'N/A')}\n"
                dashboard_text += f"📈 Traffic: {stats.get('traffic', 'N/A')}\n"
                dashboard_text += f"💾 Storage: {stats.get('storage', 'N/A')}\n\n"

                total_users += stats.get("users", 0)
                active_users += stats.get("active_users", 0)
                if isinstance(stats.get("traffic", 0), (int, float)):
                    total_traffic += stats.get("traffic", 0)

            except Exception as e:
                dashboard_text += f"❌ **{panel_name.upper()}:** Error - {e!s}\n\n"

        # System summary
        dashboard_text += "**📋 System Summary:**\n"
        dashboard_text += f"🌐 Total Users: {total_users}\n"
        dashboard_text += f"🟢 Active Users: {active_users}\n"
        dashboard_text += f"📊 Total Traffic: {total_traffic:.2f} GB\n"

        # System resources
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        dashboard_text += "\n**💻 System Resources:**\n"
        dashboard_text += f"🖥️ CPU: {cpu_percent}%\n"
        dashboard_text += f"🧠 Memory: {memory.percent}%\n"
        dashboard_text += f"💾 Disk: {disk.percent}%\n"

        await update.message.reply_text(dashboard_text, parse_mode=ParseMode.MARKDOWN)

    async def get_panel_stats(self, panel_name: str) -> dict[str, Any]:
        """Get statistics from specific panel"""
        config = self.panels[panel_name]

        if config["type"] == "hiddify":
            return await self.get_hiddify_stats(config)
        elif config["type"] == "xui":
            return await self.get_xui_stats(config)
        elif config["type"] == "v2board":
            return await self.get_v2board_stats(config)
        else:
            return {}

    async def get_hiddify_stats(self, config: dict[str, Any]) -> dict[str, Any]:
        """Get Hiddify panel statistics"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            params = {"admin_secret": config["secret"]}
            async with self.session.get(
                f"{config['url']}/api/v1/admin/system/", params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "users": data.get("total_users", 0),
                        "active_users": data.get("active_users", 0),
                        "traffic": data.get("total_usage", 0) / (1024**3),  # Convert to GB
                        "storage": data.get("disk_usage", 0),
                    }
        except Exception as e:
            logger.error(f"Failed to get Hiddify stats: {e}")
            return {}

    async def get_xui_stats(self, config: dict[str, Any]) -> dict[str, Any]:
        """Get 3X-UI panel statistics"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            # Login to get session
            login_data = {"username": config["username"], "password": config["password"]}

            async with self.session.post(f"{config['url']}/login", json=login_data) as response:
                if response.status == 200:
                    # Get statistics
                    async with self.session.get(
                        f"{config['url']}/panel/api/inbounds/list"
                    ) as stats_response:
                        if stats_response.status == 200:
                            data = await stats_response.json()
                            total_users = sum(
                                len(inbound.get("settings", {}).get("clients", []))
                                for inbound in data.get("obj", [])
                            )
                            return {
                                "users": total_users,
                                "active_users": total_users,  # XUI doesn't provide active user count
                                "traffic": 0,  # Would need to calculate from logs
                                "storage": 0,
                            }
        except Exception as e:
            logger.error(f"Failed to get XUI stats: {e}")
            return {}

    async def get_v2board_stats(self, config: dict[str, Any]) -> dict[str, Any]:
        """Get V2Board panel statistics"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            headers = {"Authorization": f'Bearer {config["api_key"]}'}
            async with self.session.get(
                f"{config['url']}/api/v1/admin/user", headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "users": len(data.get("data", [])),
                        "active_users": len(
                            [u for u in data.get("data", []) if u.get("status") == 1]
                        ),
                        "traffic": 0,  # Would need to calculate from usage data
                        "storage": 0,
                    }
        except Exception as e:
            logger.error(f"Failed to get V2Board stats: {e}")
            return {}

    async def create_user_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user creation across all panels"""
        user_id = update.effective_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text(
                "❌ **Access Denied!**\n\nOnly administrators can create users.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        if not self.rate_limit_check(user_id):
            await update.message.reply_text("⚠️ Rate limit exceeded!")
            return

        if len(context.args) < 1:
            await update.message.reply_text(
                "📝 **Usage:** `/create_user username [data_limit_gb] [days]`\n\n"
                "**Examples:**\n"
                "• `/create_user john_doe` (default: 10GB, 30 days)\n"
                "• `/create_user jane_smith 50 90` (50GB, 90 days)",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        username = context.args[0]
        data_limit = int(context.args[1]) if len(context.args) > 1 else 10
        days = int(context.args[2]) if len(context.args) > 2 else 30

        self.log_action(
            user_id, "create_user", f"Creating user: {username}, {data_limit}GB, {days} days"
        )

        results = {}
        for panel_name in self.panels.keys():
            try:
                result = await self.create_user_in_panel(panel_name, username, data_limit, days)
                results[panel_name] = "✅ Success" if result else "❌ Failed"
            except Exception as e:
                results[panel_name] = f"❌ Error: {e!s}"

        response_text = f"👤 **User Creation Results**\n\n**User:** `{username}`\n**Data Limit:** {data_limit}GB\n**Duration:** {days} days\n\n"
        for panel, status in results.items():
            response_text += f"**{panel.upper()}:** {status}\n"

        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)

    async def create_user_in_panel(
        self, panel_name: str, username: str, data_limit: int, days: int
    ) -> bool:
        """Create user in specific panel"""
        config = self.panels[panel_name]

        if config["type"] == "hiddify":
            return await self.create_hiddify_user(config, username, data_limit, days)
        elif config["type"] == "xui":
            return await self.create_xui_user(config, username, data_limit, days)
        else:
            return False

    async def create_hiddify_user(
        self, config: dict[str, Any], username: str, data_limit: int, days: int
    ) -> bool:
        """Create user in Hiddify"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            data = {
                "name": username,
                "usage_limit_GB": data_limit,
                "package_days": days,
                "mode": "no_reset",
                "admin_secret": config["secret"],
            }

            async with self.session.post(f"{config['url']}/api/v1/user/", json=data) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Failed to create Hiddify user: {e}")
            return False

    async def create_xui_user(
        self, config: dict[str, Any], username: str, data_limit: int, days: int
    ) -> bool:
        """Create user in 3X-UI"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            # Login first
            login_data = {"username": config["username"], "password": config["password"]}

            async with self.session.post(f"{config['url']}/login", json=login_data) as response:
                if response.status == 200:
                    # Create user
                    user_data = {
                        "up": 0,
                        "down": 0,
                        "total": data_limit * 1024 * 1024 * 1024,  # Convert to bytes
                        "remark": username,
                        "enable": True,
                        "expiryTime": int(
                            (datetime.now() + timedelta(days=days)).timestamp() * 1000
                        ),
                        "listen": "",
                        "port": 0,
                        "protocol": "vmess",
                        "settings": {"clients": [{"id": self.generate_uuid(), "alterId": 0}]},
                        "streamSettings": {
                            "network": "tcp",
                            "security": "none",
                            "tcpSettings": {"header": {"type": "none"}},
                        },
                        "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
                    }

                    async with self.session.post(
                        f"{config['url']}/panel/api/inbounds/add", json=user_data
                    ) as create_response:
                        return create_response.status == 200
        except Exception as e:
            logger.error(f"Failed to create XUI user: {e}")
            return False

    def generate_uuid(self) -> str:
        """Generate UUID for XUI users"""
        import uuid

        return str(uuid.uuid4())

    async def users_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle users management"""
        user_id = update.effective_user.id

        if not self.rate_limit_check(user_id):
            await update.message.reply_text("⚠️ Rate limit exceeded!")
            return

        self.log_action(user_id, "users", "Users panel accessed")

        # Create inline keyboard for user management
        keyboard = [
            [
                InlineKeyboardButton("👥 List Users", callback_data="list_users"),
                InlineKeyboardButton("➕ Create User", callback_data="create_user"),
            ],
            [
                InlineKeyboardButton("📊 User Stats", callback_data="user_stats"),
                InlineKeyboardButton("🔍 Search User", callback_data="search_user"),
            ],
        ]

        if self.is_admin(user_id):
            keyboard.append(
                [
                    InlineKeyboardButton("🗑️ Delete User", callback_data="delete_user"),
                    InlineKeyboardButton("✏️ Edit User", callback_data="edit_user"),
                ]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "👥 **User Management**\n\n" "Select an option to manage VPN users:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )

    async def servers_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle server management"""
        user_id = update.effective_user.id

        if not self.rate_limit_check(user_id):
            await update.message.reply_text("⚠️ Rate limit exceeded!")
            return

        self.log_action(user_id, "servers", "Servers panel accessed")

        servers_text = "📡 **Server Status**\n\n"

        for panel_name, config in self.panels.items():
            status = "🟢 Online" if await self.check_panel_health(panel_name) else "🔴 Offline"
            servers_text += f"**{panel_name.upper()}:** {status}\n"
            servers_text += f"📍 URL: `{config['url']}`\n"
            servers_text += f"🔧 Type: {config['type']}\n\n"

        await update.message.reply_text(servers_text, parse_mode=ParseMode.MARKDOWN)

    async def analytics_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle analytics and reporting"""
        user_id = update.effective_user.id

        if not self.rate_limit_check(user_id):
            await update.message.reply_text("⚠️ Rate limit exceeded!")
            return

        self.log_action(user_id, "analytics", "Analytics panel accessed")

        # Get analytics data
        analytics_text = "📈 **Analytics Dashboard**\n\n"

        # System performance
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        analytics_text += "**💻 System Performance:**\n"
        analytics_text += f"🖥️ CPU Usage: {cpu_percent}%\n"
        analytics_text += f"🧠 Memory Usage: {memory.percent}%\n"
        analytics_text += f"💾 Disk Usage: {disk.percent}%\n\n"

        # Network statistics
        net_io = psutil.net_io_counters()
        analytics_text += "**🌐 Network Statistics:**\n"
        analytics_text += f"📤 Bytes Sent: {net_io.bytes_sent / (1024**3):.2f} GB\n"
        analytics_text += f"📥 Bytes Received: {net_io.bytes_recv / (1024**3):.2f} GB\n\n"

        # Panel statistics
        analytics_text += "**📊 Panel Statistics:**\n"
        for panel_name in self.panels.keys():
            try:
                stats = await self.get_panel_stats(panel_name)
                analytics_text += f"**{panel_name.upper()}:**\n"
                analytics_text += f"  👥 Users: {stats.get('users', 0)}\n"
                analytics_text += f"  🟢 Active: {stats.get('active_users', 0)}\n"
                analytics_text += f"  📊 Traffic: {stats.get('traffic', 0):.2f} GB\n"
            except Exception as e:
                analytics_text += f"  ❌ Error: {e!s}\n"

        await update.message.reply_text(analytics_text, parse_mode=ParseMode.MARKDOWN)

    async def settings_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle settings management"""
        user_id = update.effective_user.id

        if not self.rate_limit_check(user_id):
            await update.message.reply_text("⚠️ Rate limit exceeded!")
            return

        self.log_action(user_id, "settings", "Settings panel accessed")

        settings_text = "⚙️ **Bot Settings**\n\n"
        settings_text += "**👤 User Settings:**\n"
        settings_text += f"🆔 User ID: `{user_id}`\n"
        settings_text += f"👑 Role: {'Admin' if self.is_admin(user_id) else 'User'}\n"
        settings_text += f"📊 Rate Limit: {self.max_requests_per_minute} requests/minute\n"
        settings_text += f"⏰ Session Timeout: {self.session_timeout // 3600} hours\n\n"

        settings_text += "**🤖 Bot Settings:**\n"
        settings_text += f"📡 Connected Panels: {len(self.panels)}\n"
        settings_text += f"👥 Authorized Users: {len(self.authorized_users)}\n"
        settings_text += f"👑 Admin Users: {len(self.admin_users)}\n"

        await update.message.reply_text(settings_text, parse_mode=ParseMode.MARKDOWN)

    async def actions_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle quick actions"""
        user_id = update.effective_user.id

        if not self.rate_limit_check(user_id):
            await update.message.reply_text("⚠️ Rate limit exceeded!")
            return

        self.log_action(user_id, "actions", "Actions panel accessed")

        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh All", callback_data="refresh_all"),
                InlineKeyboardButton("📊 System Status", callback_data="system_status"),
            ],
            [
                InlineKeyboardButton("🧹 Clean Logs", callback_data="clean_logs"),
                InlineKeyboardButton("💾 Backup Data", callback_data="backup_data"),
            ],
        ]

        if self.is_admin(user_id):
            keyboard.append(
                [
                    InlineKeyboardButton("🔧 Maintenance Mode", callback_data="maintenance_mode"),
                    InlineKeyboardButton("🚨 Emergency Stop", callback_data="emergency_stop"),
                ]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🔄 **Quick Actions**\n\n" "Select an action to perform:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )

    async def admin_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin panel"""
        user_id = update.effective_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text(
                "❌ **Access Denied!**\n\nOnly administrators can access this panel.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        if not self.rate_limit_check(user_id):
            await update.message.reply_text("⚠️ Rate limit exceeded!")
            return

        self.log_action(user_id, "admin", "Admin panel accessed")

        keyboard = [
            [
                InlineKeyboardButton("👥 Manage Users", callback_data="admin_users"),
                InlineKeyboardButton("🔧 System Config", callback_data="admin_config"),
            ],
            [
                InlineKeyboardButton("📊 Advanced Stats", callback_data="admin_stats"),
                InlineKeyboardButton("🔐 Security", callback_data="admin_security"),
            ],
            [
                InlineKeyboardButton("💾 Database", callback_data="admin_database"),
                InlineKeyboardButton("📝 Logs", callback_data="admin_logs"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🔧 **Admin Panel**\n\n" "Administrative functions and system management:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )

    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        user_id = query.from_user.id

        if not self.rate_limit_check(user_id):
            await query.answer("⚠️ Rate limit exceeded!")
            return

        await query.answer()

        if query.data == "list_users":
            await self.list_users_callback(query)
        elif query.data == "create_user":
            await self.create_user_callback(query)
        elif query.data == "user_stats":
            await self.user_stats_callback(query)
        elif query.data == "search_user":
            await self.search_user_callback(query)
        elif query.data == "refresh_all":
            await self.refresh_all_callback(query)
        elif query.data == "system_status":
            await self.system_status_callback(query)
        # Add more callback handlers as needed

    async def list_users_callback(self, query):
        """Handle list users callback"""
        user_id = query.from_user.id
        self.log_action(user_id, "list_users", "List users requested")

        users_text = "👥 **User List**\n\n"

        # Get users from database
        cursor = self.db.cursor()
        cursor.execute("SELECT username, role, created_at FROM users WHERE is_active = 1 LIMIT 10")
        users = cursor.fetchall()

        if users:
            for username, role, created_at in users:
                users_text += f"👤 **{username}** ({role})\n"
                users_text += f"📅 Created: {created_at}\n\n"
        else:
            users_text += "No users found.\n"

        await query.edit_message_text(users_text, parse_mode=ParseMode.MARKDOWN)

    async def create_user_callback(self, query):
        """Handle create user callback"""
        user_id = query.from_user.id

        if not self.is_admin(user_id):
            await query.edit_message_text(
                "❌ **Access Denied!**\n\nOnly administrators can create users.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        await query.edit_message_text(
            "📝 **Create User**\n\n"
            "Use the command:\n"
            "`/create_user username [data_limit_gb] [days]`\n\n"
            "**Examples:**\n"
            "• `/create_user john_doe`\n"
            "• `/create_user jane_smith 50 90`",
            parse_mode=ParseMode.MARKDOWN,
        )

    async def user_stats_callback(self, query):
        """Handle user stats callback"""
        user_id = query.from_user.id
        self.log_action(user_id, "user_stats", "User stats requested")

        stats_text = "📊 **User Statistics**\n\n"

        # Get user statistics from database
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT COUNT(*) as total, COUNT(CASE WHEN role = 'admin' THEN 1 END) as admins FROM users WHERE is_active = 1"
        )
        result = cursor.fetchone()

        if result:
            total_users, admin_users = result
            regular_users = total_users - admin_users

            stats_text += f"👥 **Total Users:** {total_users}\n"
            stats_text += f"👑 **Admins:** {admin_users}\n"
            stats_text += f"👤 **Regular Users:** {regular_users}\n\n"

        # Get recent activity
        cursor.execute(
            "SELECT action, COUNT(*) as count FROM bot_actions WHERE timestamp > datetime('now', '-24 hours') GROUP BY action ORDER BY count DESC LIMIT 5"
        )
        recent_actions = cursor.fetchall()

        if recent_actions:
            stats_text += "📈 **Recent Activity (24h):**\n"
            for action, count in recent_actions:
                stats_text += f"• {action}: {count} times\n"

        await query.edit_message_text(stats_text, parse_mode=ParseMode.MARKDOWN)

    async def search_user_callback(self, query):
        """Handle search user callback"""
        await query.edit_message_text(
            "🔍 **Search User**\n\n"
            "Use the command:\n"
            "`/search_user username`\n\n"
            "This will search for users across all panels.",
            parse_mode=ParseMode.MARKDOWN,
        )

    async def refresh_all_callback(self, query):
        """Handle refresh all callback"""
        user_id = query.from_user.id
        self.log_action(user_id, "refresh_all", "Refresh all requested")

        await query.edit_message_text(
            "🔄 **Refreshing...**\n\nPlease wait while I refresh all panels and data."
        )

        # Simulate refresh process
        await asyncio.sleep(2)

        refresh_text = "✅ **Refresh Complete**\n\n"

        for panel_name in self.panels.keys():
            status = "🟢 Online" if await self.check_panel_health(panel_name) else "🔴 Offline"
            refresh_text += f"**{panel_name.upper()}:** {status}\n"

        await query.edit_message_text(refresh_text, parse_mode=ParseMode.MARKDOWN)

    async def system_status_callback(self, query):
        """Handle system status callback"""
        user_id = query.from_user.id
        self.log_action(user_id, "system_status", "System status requested")

        status_text = "💻 **System Status**\n\n"

        # System resources
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        status_text += f"🖥️ **CPU:** {cpu_percent}%\n"
        status_text += f"🧠 **Memory:** {memory.percent}%\n"
        status_text += f"💾 **Disk:** {disk.percent}%\n\n"

        # Network status
        net_io = psutil.net_io_counters()
        status_text += "🌐 **Network:**\n"
        status_text += f"📤 Sent: {net_io.bytes_sent / (1024**3):.2f} GB\n"
        status_text += f"📥 Received: {net_io.bytes_recv / (1024**3):.2f} GB\n\n"

        # Panel status
        status_text += "📡 **Panel Status:**\n"
        for panel_name in self.panels.keys():
            status = "🟢 Online" if await self.check_panel_health(panel_name) else "🔴 Offline"
            status_text += f"• {panel_name.upper()}: {status}\n"

        await query.edit_message_text(status_text, parse_mode=ParseMode.MARKDOWN)

    def run(self):
        """Start the bot"""
        application = Application.builder().token(self.bot_token).build()

        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("create_user", self.create_user_handler))
        application.add_handler(
            MessageHandler(filters.Regex("^📊 Dashboard$"), self.dashboard_handler)
        )
        application.add_handler(MessageHandler(filters.Regex("^👥 Users$"), self.users_handler))
        application.add_handler(MessageHandler(filters.Regex("^📡 Servers$"), self.servers_handler))
        application.add_handler(
            MessageHandler(filters.Regex("^📈 Analytics$"), self.analytics_handler)
        )
        application.add_handler(
            MessageHandler(filters.Regex("^⚙️ Settings$"), self.settings_handler)
        )
        application.add_handler(MessageHandler(filters.Regex("^🔄 Actions$"), self.actions_handler))
        application.add_handler(
            MessageHandler(filters.Regex("^🔧 Admin Panel$"), self.admin_handler)
        )

        # Add callback query handler
        application.add_handler(CallbackQueryHandler(self.callback_handler))

        # Start bot
        logger.info("Starting VPN Management Bot...")
        application.run_polling()


# Configuration
panels_config = {
    "hiddify": {
        "type": "hiddify",
        "url": "https://hiddify.example.com",
        "secret": "your-secret-key",
    },
    "xui": {
        "type": "xui",
        "url": "https://xui.example.com:2053",
        "username": "admin",
        "password": "password123",
    },
    "v2board": {"type": "v2board", "url": "https://panel.example.com", "api_key": "your-api-key"},
}

# Start bot
if __name__ == "__main__":
    bot = VPNManagementBot("YOUR_BOT_TOKEN", panels_config)
    bot.run()
