# 🖥️ Telegram Laptop Monitor Bot

Bot Telegram untuk monitoring laptop Ubuntu — suhu, RAM, CPU, GPU, baterai, IP, dan shutdown remote.

---

## 🚀 Fitur

| Perintah | Fungsi |
|---|---|
| (Otomatis saat hidup) | Kirim notifikasi IP lokal & online |
| `/pc-info` | Tampilkan info sistem lengkap |
| `/set-max-temperature` | Set batas suhu CPU/GPU |
| `/get-max-temperature` | Lihat batas suhu saat ini |
| `/pc-shutdown` | Matikan laptop (dengan konfirmasi) |

---

## 📋 Persiapan

### 1. Buat Bot Telegram

1. Chat ke **@BotFather** di Telegram
2. Ketik `/newbot` → ikuti instruksi
3. Salin **Token** yang diberikan

### 2. Dapatkan Chat ID Anda

1. Chat ke **@userinfobot** di Telegram
2. Salin angka **Id** yang tampil (contoh: `987654321`)

---

## 🐳 Deploy via Portainer (Cara Mudah)

### Langkah 1 — Upload / clone project

```bash
# Di server Ubuntu
git clone <repo-url> /opt/tg-monitor
# atau upload manual via SFTP ke /opt/tg-monitor
```

### Langkah 2 — Buat file .env

```bash
cd /opt/tg-monitor
cp .env.example .env
nano .env
```

Isi:
```
BOT_TOKEN=1234567890:AAxxxx...
CHAT_ID=987654321
```

### Langkah 3 — Deploy via Portainer UI

1. Buka Portainer → **Stacks** → **+ Add stack**
2. Pilih **Upload** → upload file `docker-compose.yml`
3. Scroll ke bawah → **Environment variables**:
   - `BOT_TOKEN` = token bot Anda
   - `CHAT_ID`   = chat ID Anda
4. Klik **Deploy the stack**

---

## 🖥️ Deploy Manual (tanpa Portainer)

```bash
cd /opt/tg-monitor

# Build image
docker compose build

# Jalankan
docker compose up -d

# Lihat log
docker compose logs -f
```

---

## 🔧 Deploy Tanpa Docker (langsung di host)

> Cocok jika tidak memakai container

```bash
# Install dependency
pip3 install -r requirements.txt

# Set environment variable
export BOT_TOKEN="token_anda"
export CHAT_ID="chat_id_anda"

# Jalankan
python3 bot.py
```

Untuk jalan terus sebagai service systemd:

```bash
sudo nano /etc/systemd/system/tg-monitor.service
```

```ini
[Unit]
Description=Telegram Laptop Monitor Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tg-monitor
ExecStart=/usr/bin/python3 /opt/tg-monitor/bot.py
Restart=always
Environment=BOT_TOKEN=TOKEN_ANDA
Environment=CHAT_ID=CHATID_ANDA

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable tg-monitor
sudo systemctl start tg-monitor
```

---

## ⚙️ Konfigurasi Suhu

Setelah bot berjalan, gunakan:
- `/set-max-temperature` → pilih CPU atau GPU → ketik angka (misal `75`)
- `/get-max-temperature` → lihat batas yang aktif

Config disimpan di `/app/data/config.json` (Docker) atau `./data/config.json` (manual).

Bot akan **otomatis mengirim peringatan** jika suhu melebihi **90% dari batas** yang diset.

---

## 🔬 Dukungan Sensor

| Komponen | Metode |
|---|---|
| Suhu CPU | `psutil.sensors_temperatures()` (coretemp, k10temp, dll) |
| Suhu GPU NVIDIA | `nvidia-smi` |
| Suhu GPU AMD/Intel | `psutil` sensors (amdgpu, radeon) |
| Baterai | `psutil.sensors_battery()` |
| RAM & CPU Usage | `psutil` |

> **Catatan**: Jika GPU tidak terdeteksi, kolom GPU akan tampil `N/A`.  
> Untuk NVIDIA, pastikan driver terinstal di host.

---

## 🛡️ Keamanan

- Bot hanya merespons chat dari `CHAT_ID` yang diset
- Perintah shutdown memerlukan konfirmasi via tombol inline
- Container berjalan dengan `privileged: true` untuk akses sensor & shutdown host

---

## 📁 Struktur File

```
tg-monitor/
├── bot.py              ← kode utama bot
├── requirements.txt    ← dependency Python
├── Dockerfile          ← image Docker
├── docker-compose.yml  ← stack untuk Portainer
├── .env.example        ← contoh konfigurasi
└── README.md           ← dokumentasi ini
```
