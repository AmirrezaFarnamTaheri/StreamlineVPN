#!/usr/bin/env python3
"""
VPN Management Telegram Bot
Version: 1.0.0

A comprehensive Telegram bot for managing VPN infrastructure, users, and monitoring.
"""

import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime

import aiohttp
import psutil
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_USER_IDS = [int(id) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id]
VPN_SERVER_IP = os.getenv("VPN_SERVER_IP", "")
VPN_API_URL = os.getenv("VPN_API_URL", "http://localhost:8080/api")
DATABASE_PATH = os.getenv("DATABASE_PATH", "vpn_bot.db")

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class VPNBot:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()

    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Users table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # VPN configurations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vpn_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                protocol TEXT,
                config_data TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """
        )

        # Statistics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                bytes_sent BIGINT DEFAULT 0,
                bytes_received BIGINT DEFAULT 0,
                connection_time INTEGER DEFAULT 0,
                last_connected TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """
        )

        # System logs table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id

        # Register user if not exists
        await self.register_user(user)

        welcome_message = f"""
🤖 Welcome to VPN Management Bot!

👤 User: {user.first_name}
🆔 ID: {user_id}

Available commands:
/status - Check VPN server status
/users - List all users (Admin only)
/adduser - Add new user (Admin only)
/removeuser - Remove user (Admin only)
/config - Get your VPN configuration
/stats - View your usage statistics
/help - Show this help message

For admin commands, use /adminhelp
        """

        await update.message.reply_text(welcome_message)

    async def register_user(self, user):
        """Register or update user in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, last_activity)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (user.id, user.username, user.first_name, user.last_name),
        )

        conn.commit()
        conn.close()

    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in ADMIN_USER_IDS

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            # Get system status
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Get VPN service status
            vpn_status = await self.get_vpn_service_status()

            status_message = f"""
🖥️ System Status:

CPU Usage: {cpu_percent}%
Memory: {memory.percent}% ({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)
Disk: {disk.percent}% ({disk.used // 1024 // 1024 // 1024}GB / {disk.total // 1024 // 1024 // 1024}GB)

🔒 VPN Service: {vpn_status['status']}
👥 Active Users: {vpn_status['active_users']}
📊 Total Traffic: {vpn_status['total_traffic']}
            """

            await update.message.reply_text(status_message)

        except Exception as e:
            logger.error(f"Error getting status: {e}")
            await update.message.reply_text("❌ Error getting system status")

    async def get_vpn_service_status(self) -> dict:
        """Get VPN service status from API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{VPN_API_URL}/status") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"status": "Unknown", "active_users": 0, "total_traffic": "0 MB"}
        except Exception as e:
            logger.error(f"Error getting VPN status: {e}")
            return {"status": "Error", "active_users": 0, "total_traffic": "0 MB"}

    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /users command (Admin only)"""
        user_id = update.effective_user.id

        if not await self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only.")
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT user_id, username, first_name, is_active, last_activity
                FROM users ORDER BY created_at DESC
            """
            )

            users = cursor.fetchall()
            conn.close()

            if not users:
                await update.message.reply_text("📝 No users found")
                return

            users_message = "👥 Registered Users:\n\n"
            for user in users:
                user_id, username, first_name, is_active, last_activity = user
                status = "✅ Active" if is_active else "❌ Inactive"
                users_message += f"🆔 {user_id}\n👤 {first_name or username or 'Unknown'}\n{status}\n📅 {last_activity}\n\n"

            await update.message.reply_text(users_message)

        except Exception as e:
            logger.error(f"Error getting users: {e}")
            await update.message.reply_text("❌ Error getting users list")

    async def adduser_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /adduser command (Admin only)"""
        user_id = update.effective_user.id

        if not await self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only.")
            return

        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Usage: /adduser <user_id> <protocol>")
            return

        try:
            new_user_id = int(context.args[0])
            protocol = context.args[1].lower()

            # Validate protocol
            valid_protocols = ["vless", "vmess", "trojan", "shadowsocks"]
            if protocol not in valid_protocols:
                await update.message.reply_text(
                    f"❌ Invalid protocol. Use: {', '.join(valid_protocols)}"
                )
                return

            # Add user to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO users (user_id, is_active)
                VALUES (?, TRUE)
            """,
                (new_user_id,),
            )

            # Generate VPN configuration
            config_data = await self.generate_vpn_config(new_user_id, protocol)

            cursor.execute(
                """
                INSERT INTO vpn_configs (user_id, protocol, config_data)
                VALUES (?, ?, ?)
            """,
                (new_user_id, protocol, json.dumps(config_data)),
            )

            conn.commit()
            conn.close()

            await update.message.reply_text(f"✅ User {new_user_id} added with {protocol} protocol")

        except ValueError:
            await update.message.reply_text("❌ Invalid user ID")
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            await update.message.reply_text("❌ Error adding user")

    async def generate_vpn_config(self, user_id: int, protocol: str) -> dict:
        """Generate VPN configuration for user"""
        import uuid

        config = {
            "user_id": user_id,
            "protocol": protocol,
            "server": VPN_SERVER_IP,
            "port": 443,
            "uuid": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
        }

        if protocol == "vless":
            config.update(
                {
                    "flow": "xtls-rprx-vision",
                    "security": "reality",
                    "server_name": "www.microsoft.com",
                }
            )
        elif protocol == "vmess":
            config.update({"alter_id": 0, "security": "tls", "network": "ws"})
        elif protocol == "trojan":
            config.update({"password": str(uuid.uuid4()), "security": "tls"})
        elif protocol == "shadowsocks":
            config.update({"method": "2022-blake3-aes-256-gcm", "password": str(uuid.uuid4())})

        return config

    async def config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /config command"""
        user_id = update.effective_user.id

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT protocol, config_data FROM vpn_configs 
                WHERE user_id = ? AND is_active = TRUE
                ORDER BY created_at DESC LIMIT 1
            """,
                (user_id,),
            )

            result = cursor.fetchone()
            conn.close()

            if not result:
                await update.message.reply_text("❌ No active VPN configuration found")
                return

            protocol, config_data = result
            config = json.loads(config_data)

            config_message = f"""
🔧 Your VPN Configuration:

Protocol: {protocol.upper()}
Server: {config['server']}
Port: {config['port']}
UUID/Password: {config.get('uuid', config.get('password', 'N/A'))}

📋 Full config:
```json
{json.dumps(config, indent=2)}
```
            """

            await update.message.reply_text(config_message)

        except Exception as e:
            logger.error(f"Error getting config: {e}")
            await update.message.reply_text("❌ Error getting configuration")

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user_id = update.effective_user.id

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT bytes_sent, bytes_received, connection_time, last_connected
                FROM statistics WHERE user_id = ?
            """,
                (user_id,),
            )

            result = cursor.fetchone()
            conn.close()

            if not result:
                await update.message.reply_text("📊 No statistics available")
                return

            bytes_sent, bytes_received, connection_time, last_connected = result

            # Convert bytes to human readable format
            def format_bytes(bytes_value):
                for unit in ["B", "KB", "MB", "GB"]:
                    if bytes_value < 1024:
                        return f"{bytes_value:.2f} {unit}"
                    bytes_value /= 1024
                return f"{bytes_value:.2f} TB"

            stats_message = f"""
📊 Your Usage Statistics:

📤 Data Sent: {format_bytes(bytes_sent)}
📥 Data Received: {format_bytes(bytes_received)}
⏱️ Total Connection Time: {connection_time // 3600}h {(connection_time % 3600) // 60}m
🕒 Last Connected: {last_connected or 'Never'}
            """

            await update.message.reply_text(stats_message)

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            await update.message.reply_text("❌ Error getting statistics")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
🤖 VPN Management Bot - Help

Basic Commands:
/start - Start the bot
/status - Check VPN server status
/config - Get your VPN configuration
/stats - View your usage statistics
/help - Show this help message

Admin Commands (if you're an admin):
/users - List all users
/adduser - Add new user
/removeuser - Remove user
/adminhelp - Show admin help

For support, contact your administrator.
        """

        await update.message.reply_text(help_message)

    async def adminhelp_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /adminhelp command"""
        user_id = update.effective_user.id

        if not await self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only.")
            return

        admin_help_message = """
🔧 Admin Commands:

User Management:
/users - List all registered users
/adduser <user_id> <protocol> - Add new user with VPN config
/removeuser <user_id> - Remove user and deactivate configs

System Management:
/status - Check system and VPN service status
/restart - Restart VPN service
/backup - Create system backup
/update - Update VPN software

Monitoring:
/logs - View recent system logs
/alerts - Configure monitoring alerts
/notifications - Manage notification settings

Usage: /adduser 123456 vless
        """

        await update.message.reply_text(admin_help_message)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")

        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )


async def main():
    """Main function"""
    if not BOT_TOKEN:
        logger.error("No bot token provided!")
        return

    # Create bot instance
    bot = VPNBot()

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("status", bot.status_command))
    application.add_handler(CommandHandler("users", bot.users_command))
    application.add_handler(CommandHandler("adduser", bot.adduser_command))
    application.add_handler(CommandHandler("config", bot.config_command))
    application.add_handler(CommandHandler("stats", bot.stats_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("adminhelp", bot.adminhelp_command))

    # Add error handler
    application.add_error_handler(bot.error_handler)

    # Start the bot
    logger.info("Starting VPN Management Bot...")
    await application.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
