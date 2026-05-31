#!/usr/bin/env python3
"""
Telegram Bot - Linux System Monitor
Monitoring: suhu, RAM, CPU, GPU, baterai, IP
Fitur: notifikasi hidup, pc-info, set/get max temperature, shutdown
"""

import os
import time
import json
import logging
import asyncio
import subprocess
import threading
import requests
import psutil

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ─── KONFIGURASI ────────────────────────────────────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN", "ISI_TOKEN_DISINI")
CHAT_ID     = os.getenv("CHAT_ID",   "ISI_CHAT_ID_DISINI")   # ID chat/user yang boleh pakai bot
CONFIG_FILE = "/app/data/config.json"
CHECK_INTERVAL = 60   # detik antar pengecekan suhu otomatis

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# ─── HELPER: AKSES DIBATASI ──────────────────────────────────────────────────────
def allowed(update: Update) -> bool:
    """Hanya chat_id yang diizinkan bisa pakai bot."""
    return str(update.effective_chat.id) == str(CHAT_ID)


# ─── HELPER: KONFIGURASI (max suhu) ─────────────────────────────────────────────
def load_config() -> dict:
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"max_cpu": 80, "max_gpu": 80}


def save_config(cfg: dict):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)


# ─── HELPER: SISTEM ─────────────────────────────────────────────────────────────
def get_local_ip() -> str:
    try:
        result = subprocess.run(
            ["hostname", "-I"], capture_output=True, text=True, timeout=5
        )
        ips = result.stdout.strip().split()
        return ips[0] if ips else "N/A"
    except Exception:
        return "N/A"


def get_public_ip() -> str:
    try:
        r = requests.get("https://api.ipify.org", timeout=5)
        return r.text.strip()
    except Exception:
        try:
            r = requests.get("https://ifconfig.me/ip", timeout=5)
            return r.text.strip()
        except Exception:
            return "N/A"


def get_os_info() -> str:
    try:
        with open("/etc/os-release") as f:
            lines = dict(l.strip().split("=", 1) for l in f if "=" in l)
        name = lines.get("PRETTY_NAME", "Linux").strip('"')
        return name
    except Exception:
        return "Linux"


def get_ram_info() -> tuple[float, float]:
    """Return (used_gb, total_gb)."""
    mem = psutil.virtual_memory()
    return round(mem.used / 1e9, 1), round(mem.total / 1e9, 1)


def get_cpu_usage() -> float:
    return psutil.cpu_percent(interval=1)


def get_cpu_temp() -> float | None:
    """Baca suhu CPU dari berbagai sumber."""
    try:
        temps = psutil.sensors_temperatures()
        # cari sensor yang umum
        for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz", "cpu-thermal"):
            if key in temps and temps[key]:
                vals = [t.current for t in temps[key]]
                return round(max(vals), 1)
        # fallback: ambil sensor pertama yang ada
        for key, entries in temps.items():
            if entries:
                return round(entries[0].current, 1)
    except Exception:
        pass

    # Coba via file langsung (Raspberry Pi / ARM)
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read().strip()) / 1000, 1)
    except Exception:
        pass

    return None


def get_gpu_info() -> dict:
    """Return {'usage': float|None, 'temp': float|None, 'name': str}."""
    info = {"usage": None, "temp": None, "name": "N/A"}

    # nvidia-smi
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(",")
            if len(parts) >= 3:
                info["name"]  = parts[0].strip()
                info["usage"] = float(parts[1].strip())
                info["temp"]  = float(parts[2].strip())
                return info
    except FileNotFoundError:
        pass
    except Exception:
        pass

    # AMD / Intel via psutil sensors
    try:
        temps = psutil.sensors_temperatures()
        for key in ("amdgpu", "radeon", "nouveau", "intel-gpu"):
            if key in temps and temps[key]:
                info["temp"] = round(temps[key][0].current, 1)
                info["name"] = key
                break
    except Exception:
        pass

    return info


def get_battery() -> dict:
    """Return {'percent': float|None, 'plugged': bool|None, 'has_battery': bool}."""
    try:
        batt = psutil.sensors_battery()
        if batt is None:
            return {"has_battery": False}
        return {
            "has_battery": True,
            "percent": round(batt.percent, 1),
            "plugged": batt.power_plugged,
        }
    except Exception:
        return {"has_battery": False}


def build_pc_info_message() -> str:
    os_name    = get_os_info()
    ram_used, ram_total = get_ram_info()
    cpu_pct    = get_cpu_usage()
    cpu_temp   = get_cpu_temp()
    gpu        = get_gpu_info()
    battery    = get_battery()
    local_ip   = get_local_ip()
    public_ip  = get_public_ip()

    cpu_temp_str = f"{cpu_temp}°" if cpu_temp is not None else "N/A"
    gpu_temp_str = f"{gpu['temp']}°" if gpu["temp"] is not None else "N/A"
    gpu_use_str  = f"{gpu['usage']}%" if gpu["usage"] is not None else "N/A"

    if battery["has_battery"]:
        plug_icon = "🔌" if battery.get("plugged") else "🔋"
        batt_str  = f"{plug_icon} {battery['percent']}%"
    else:
        batt_str  = "Tidak ada baterai (Desktop/Server)"

    lines = [
        "🖥️ *PC Info*",
        f"OS       : {os_name}",
        f"RAM      : {ram_used}/{ram_total} GB",
        f"CPU Usage: {cpu_pct}%",
        f"GPU Usage: {gpu_use_str}",
        f"Suhu CPU : {cpu_temp_str}",
        f"Suhu GPU : {gpu_temp_str}",
        f"Baterai  : {batt_str}",
        f"IP Lokal : `{local_ip}`",
        f"IP Online: `{public_ip}`",
    ]
    return "\n".join(lines)


# ─── COMMAND HANDLERS ────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return
    await update.message.reply_text(
        "👋 *Selamat datang di Laptop Monitor Bot!*\n\n"
        "Perintah tersedia:\n"
        "/pc\\-info – Info sistem lengkap\n"
        "/set\\-max\\-temperature – Set batas suhu\n"
        "/get\\-max\\-temperature – Lihat batas suhu\n"
        "/pc\\-shutdown – Matikan laptop",
        parse_mode="MarkdownV2",
    )


async def cmd_pc_info(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return
    msg = await update.message.reply_text("⏳ Mengambil info sistem...")
    try:
        text = build_pc_info_message()
        await msg.edit_text(text, parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"❌ Gagal ambil info: {e}")


async def cmd_set_max_temperature(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return

    keyboard = [
        [
            InlineKeyboardButton("🌡️ Set CPU Max Temp", callback_data="set_cpu"),
            InlineKeyboardButton("🌡️ Set GPU Max Temp", callback_data="set_gpu"),
        ]
    ]
    cfg = load_config()
    await update.message.reply_text(
        f"Pilih komponen yang ingin diatur batas suhunya:\n"
        f"Saat ini → CPU: *{cfg['max_cpu']}°* | GPU: *{cfg['max_gpu']}°*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def cmd_get_max_temperature(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return
    cfg = load_config()
    await update.message.reply_text(
        f"🌡️ *Batas Suhu Maksimum*\n"
        f"CPU: {cfg['max_cpu']}°\n"
        f"GPU: {cfg['max_gpu']}°",
        parse_mode="Markdown",
    )


async def cmd_shutdown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return

    keyboard = [[
        InlineKeyboardButton("✅ Ya, matikan!", callback_data="confirm_shutdown"),
        InlineKeyboardButton("❌ Batal",        callback_data="cancel_shutdown"),
    ]]
    await update.message.reply_text(
        "⚠️ *Yakin ingin mematikan laptop?*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# ─── CALLBACK QUERY (inline buttons) ────────────────────────────────────────────

# Simpan state sementara: user sedang set cpu/gpu?
_pending_set: dict[int, str] = {}


async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not allowed(update):
        return

    data = query.data
    user_id = update.effective_user.id

    # ── Shutdown ──
    if data == "confirm_shutdown":
        await query.edit_message_text("🛑 *Laptop akan dimatikan. Bye! 👋*", parse_mode="Markdown")
        log.info("Shutdown command received. Executing...")
        subprocess.Popen(["shutdown", "-h", "now"])
        return

    if data == "cancel_shutdown":
        await query.edit_message_text("✅ Shutdown dibatalkan.")
        return

    # ── Set temperature: pilih komponen ──
    if data in ("set_cpu", "set_gpu"):
        komponen = "CPU" if data == "set_cpu" else "GPU"
        _pending_set[user_id] = data.replace("set_", "")
        await query.edit_message_text(
            f"Ketik angka suhu maksimum untuk *{komponen}* (contoh: `75`):",
            parse_mode="Markdown",
        )
        return


# ─── MESSAGE HANDLER untuk input angka suhu ─────────────────────────────────────
from telegram.ext import MessageHandler, filters

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return

    user_id = update.effective_user.id
    if user_id not in _pending_set:
        return  # bukan input yang ditunggu

    text = update.message.text.strip()
    try:
        val = int(float(text))
        if val < 30 or val > 120:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Angka tidak valid. Masukkan antara 30–120.")
        return

    komponen = _pending_set.pop(user_id)
    cfg = load_config()
    cfg[f"max_{komponen}"] = val
    save_config(cfg)

    await update.message.reply_text(
        f"✅ Batas suhu *{komponen.upper()}* diset ke *{val}°*",
        parse_mode="Markdown",
    )


# ─── NOTIFIKASI STARTUP ──────────────────────────────────────────────────────────
async def send_startup_notification(app: Application):
    local_ip  = get_local_ip()
    public_ip = get_public_ip()
    text = (
        "✅ *Laptop sudah hidup!*\n"
        f"🏠 Local : `{local_ip}`\n"
        f"🌐 Online: `{public_ip}`"
    )
    try:
        await app.bot.send_message(
            chat_id=CHAT_ID, text=text, parse_mode="Markdown"
        )
        log.info("Startup notification sent.")
    except Exception as e:
        log.error(f"Gagal kirim notif startup: {e}")


# ─── TEMPERATURE WATCHER (background task) ───────────────────────────────────────
_warned: dict[str, bool] = {"cpu": False, "gpu": False}


async def temperature_watcher(app: Application):
    """Cek suhu setiap CHECK_INTERVAL detik dan kirim peringatan jika perlu."""
    global _warned
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        cfg = load_config()

        cpu_temp = get_cpu_temp()
        gpu_info = get_gpu_info()
        gpu_temp = gpu_info["temp"]

        for komponen, temp, max_temp in [
            ("CPU", cpu_temp, cfg["max_cpu"]),
            ("GPU", gpu_temp, cfg["max_gpu"]),
        ]:
            if temp is None:
                continue
            pct = (temp / max_temp) * 100

            if pct > 90 and not _warned[komponen.lower()]:
                _warned[komponen.lower()] = True
                msg = (
                    f"🔥 *PERINGATAN SUHU {komponen}!*\n"
                    f"Suhu saat ini : *{temp}°*\n"
                    f"Batas maksimum: *{max_temp}°*\n"
                    f"Persentase    : *{pct:.2f}%*"
                )
                try:
                    await app.bot.send_message(
                        chat_id=CHAT_ID, text=msg, parse_mode="Markdown"
                    )
                    log.warning(f"Suhu {komponen} warning sent: {temp}° / {max_temp}°")
                except Exception as e:
                    log.error(f"Gagal kirim warning suhu: {e}")

            elif pct <= 90:
                _warned[komponen.lower()] = False   # reset warning


# ─── MAIN ────────────────────────────────────────────────────────────────────────
def main():
    if BOT_TOKEN == "ISI_TOKEN_DISINI":
        log.error("BOT_TOKEN belum diisi! Set via environment variable BOT_TOKEN.")
        return
    if CHAT_ID == "ISI_CHAT_ID_DISINI":
        log.error("CHAT_ID belum diisi! Set via environment variable CHAT_ID.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Daftarkan handler
    app.add_handler(CommandHandler("start",                cmd_start))
    app.add_handler(CommandHandler("pc_info",              cmd_pc_info))
    app.add_handler(CommandHandler("pc-info",              cmd_pc_info))
    app.add_handler(CommandHandler("set_max_temperature",  cmd_set_max_temperature))
    app.add_handler(CommandHandler("set-max-temperature",  cmd_set_max_temperature))
    app.add_handler(CommandHandler("get_max_temperature",  cmd_get_max_temperature))
    app.add_handler(CommandHandler("get-max-temperature",  cmd_get_max_temperature))
    app.add_handler(CommandHandler("pc_shutdown",          cmd_shutdown))
    app.add_handler(CommandHandler("pc-shutdown",          cmd_shutdown))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    async def post_init(app: Application):
        await send_startup_notification(app)
        asyncio.create_task(temperature_watcher(app))

    app.post_init = post_init

    log.info("Bot berjalan dengan mode polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
