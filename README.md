# 🖥️ Telegram Laptop Monitor Bot

Bot Telegram untuk monitoring laptop Ubuntu — suhu, RAM, CPU, GPU, baterai, IP, serta **shutdown & restart remote via SSH**.

---

## ✨ Fitur Lengkap

| Fitur | Keterangan |
|---|---|
| 🟢 Notifikasi hidup | Kirim pesan otomatis beserta IP saat bot/laptop start |
| 🖥️ PC Info | OS, RAM, CPU & GPU usage, suhu, baterai, IP lokal & publik |
| 🌡️ Set batas suhu | Set suhu maksimum CPU/GPU dengan konfirmasi |
| 🌡️ Cek batas suhu | Lihat batas suhu yang sedang aktif |
| 🔄 Restart | Restart laptop remote via SSH dengan konfirmasi |
| 🔴 Shutdown | Matikan laptop remote via SSH dengan konfirmasi |
| 📋 Menu tombol | Keyboard permanen di bawah chat |
| 🔔 Warning suhu | Notifikasi otomatis jika suhu >90% dari batas |
| 👥 Multi user | CHAT_ID bisa lebih dari satu |
| 🔒 Akses terbatas | Hanya CHAT_ID terdaftar yang bisa pakai bot |

---

## 📋 Daftar Perintah

| Perintah | Fungsi |
|---|---|
| `/start` | Salam pembuka + tampilkan menu |
| `/menu` | Tampilkan ulang tombol menu jika hilang |
| `/pc_info` | Info sistem lengkap |
| `/get_max_temperature` | Lihat batas suhu CPU/GPU saat ini |
| `/set_max_temperature` | Set batas suhu CPU/GPU |
| `/pc_restart` | Restart laptop (perlu SSH dikonfigurasi) |
| `/pc_shutdown` | Matikan laptop (perlu SSH dikonfigurasi) |

---

## 🔑 Cara Mendapatkan CHAT_ID

### Cara 1 — @userinfobot (termudah)

1. Buka Telegram → cari **@userinfobot**
2. Klik **Start**
3. Bot langsung reply, catat angka di bagian **Id**:

```
Your user information:
Id: 987654321       ← ini CHAT_ID Anda
First name: Eric
```

### Cara 2 — @RawDataBot

1. Cari **@RawDataBot** → klik **Start**
2. Lihat bagian JSON:

```json
"chat": {
    "id": 987654321,
    "type": "private"
}
```

### Cara 3 — CHAT_ID Group

1. Tambahkan bot ke grup
2. Kirim pesan di grup
3. Buka browser akses:
   ```
   https://api.telegram.org/botTOKEN_ANDA/getUpdates
   ```
4. Cari `"chat"` → `"id"` — angkanya **negatif** untuk grup:
   ```json
   "chat": { "id": -1001234567890 }
   ```

---

## 👥 Konfigurasi CHAT_ID Single & Multiple

```bash
# 1 user
CHAT_ID=987654321

# 2+ user — pisahkan dengan koma
CHAT_ID=987654321,111222333,444555666

# 2+ user — alternatif pakai garis lurus
CHAT_ID=987654321|111222333
```

> ⚠️ **Jangan ada spasi** di sekitar pemisah.
> ✅ Benar : `CHAT_ID=101,102`
> ❌ Salah : `CHAT_ID=101, 102`

Bot akan balas `⛔ Anda tidak memiliki akses ke bot ini.` jika ID tidak terdaftar.

---

## 🔐 Setup SSH (Wajib untuk Shutdown & Restart)

Fitur shutdown dan restart bekerja dengan cara bot **SSH ke localhost** dari dalam container ke host laptop. Berikut langkah lengkapnya:

### Langkah 1 — Install & aktifkan SSH Server di laptop

```bash
sudo apt install openssh-server -y
sudo systemctl enable ssh
sudo systemctl start ssh

# Verifikasi SSH berjalan
sudo systemctl status ssh
```

### Langkah 2 — Buat SSH key khusus untuk bot

Jalankan perintah ini **di laptop host** (bukan di container):

```bash
# Buat folder untuk menyimpan key
mkdir -p /home/eric-tandra/PortainerApp/telegram-monitor-bot/ssh

# Generate SSH key tanpa passphrase
ssh-keygen -t ed25519 \
  -f /home/eric-tandra/PortainerApp/telegram-monitor-bot/ssh/bot_key \
  -N "" \
  -C "telegram-bot-key"
```

Akan terbuat 2 file:
- `ssh/bot_key` — private key (untuk container)
- `ssh/bot_key.pub` — public key (didaftarkan ke host)

### Langkah 3 — Daftarkan public key ke host

```bash
# Tambahkan public key ke authorized_keys
cat /home/eric-tandra/PortainerApp/telegram-monitor-bot/ssh/bot_key.pub \
  >> /home/eric-tandra/.ssh/authorized_keys

# Pastikan permission benar
chmod 700 /home/eric-tandra/.ssh
chmod 600 /home/eric-tandra/.ssh/authorized_keys
```

### Langkah 4 — Izinkan user jalankan shutdown/reboot tanpa password

```bash
sudo visudo
```

Tambahkan baris ini di **paling bawah** (ganti `eric-tandra` dengan username Anda):

```
eric-tandra ALL=(ALL) NOPASSWD: /sbin/shutdown, /sbin/reboot
```

Simpan: `Ctrl+O` → `Enter` → `Ctrl+X`

### Langkah 5 — Test koneksi SSH manual

```bash
ssh -i /home/eric-tandra/PortainerApp/telegram-monitor-bot/ssh/bot_key \
    -o StrictHostKeyChecking=no \
    eric-tandra@127.0.0.1 \
    "echo 'SSH OK'"
```

Output harus: `SSH OK`

---

## 🐳 Deploy via Portainer

### Langkah 1 — Build image

```bash
cd /home/eric-tandra/PortainerApp/telegram-monitor-bot
docker build -t tg-monitor-bot:latest .
```

### Langkah 2 — Buat Stack di Portainer

Portainer → **Stacks** → **+ Add stack** → tab **Web editor**, paste:

```yaml
version: "3.9"

services:
  telegram-monitor-bot:
    image: tg-monitor-bot:latest
    container_name: tg-laptop-monitor
    restart: unless-stopped
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - CHAT_ID=${CHAT_ID}
      - SSH_KEY_LOCATION=${SSH_KEY_LOCATION}
      - SSH_USER_NAME=${SSH_USER_NAME}
    privileged: true
    network_mode: host
    volumes:
      - /sys:/sys:ro
      - /proc:/proc:ro
      - /home/eric-tandra/PortainerApp/telegram-monitor-bot/ssh:/app/ssh:ro
      - bot-data:/app/data

volumes:
  bot-data:
    driver: local
```

### Langkah 3 — Isi Environment Variables di Portainer

| Name | Contoh | Keterangan |
|---|---|---|
| `BOT_TOKEN` | `1234567890:AAxxxx` | Token dari @BotFather |
| `CHAT_ID` | `987654321` atau `987654321,111222` | ID dari @userinfobot |
| `SSH_KEY_LOCATION` | `/app/ssh/bot_key` | Path key di dalam container |
| `SSH_USER_NAME` | `eric-tandra` | Username laptop host |

Klik **Deploy the stack**.

---

## 🐳 Deploy via GitHub + Portainer

### Push ke GitHub

```bash
cd /home/eric-tandra/PortainerApp/telegram-monitor-bot
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/USERNAME/telegram-monitor-bot.git
git push -u origin main
```

> ⚠️ Pastikan folder `ssh/` ada di `.gitignore` agar private key tidak terupload!

```bash
echo "ssh/" >> .gitignore
git add .gitignore
git commit -m "chore: ignore ssh keys"
git push
```

### Buat Stack di Portainer (tab Repository)

| Field | Value |
|---|---|
| Repository URL | `https://github.com/USERNAME/telegram-monitor-bot` |
| Repository reference | `refs/heads/main` |
| Compose path | `docker-compose.yml` |

Isi environment variables seperti tabel di atas, klik **Deploy**.

### Update script ke depan

```bash
nano bot.py   # atau edit lainnya
git add .
git commit -m "deskripsi perubahan"
git push
```

Portainer → **Stacks** → **pc-bot-telegram** → **Pull and redeploy**.

---

## 🌡️ Cara Kerja Monitoring Suhu

Bot cek suhu setiap **60 detik**. Jika suhu melebihi **90% dari batas** yang diset, semua CHAT_ID terdaftar mendapat peringatan:

```
🔥 PERINGATAN SUHU CPU!
Suhu saat ini : 74°
Batas maksimum: 80°
Persentase    : 92.50%
```

Rumus: `(suhu / batas_max) × 100`

---

## 🔬 Dukungan Sensor Hardware

| Komponen | Metode |
|---|---|
| Suhu CPU Intel | `psutil` → `coretemp` |
| Suhu CPU AMD | `psutil` → `k10temp` |
| Suhu CPU ARM | `/sys/class/thermal/thermal_zone0/temp` |
| Suhu GPU NVIDIA | `nvidia-smi` |
| Suhu GPU AMD | `psutil` → `amdgpu` / `radeon` |
| Baterai | `psutil.sensors_battery()` |
| RAM & CPU | `psutil` |

---

## 📁 Struktur File

```
telegram-monitor-bot/
├── bot.py              ← kode utama bot
├── requirements.txt    ← dependency Python
├── Dockerfile          ← image Docker
├── docker-compose.yml  ← stack untuk Portainer
├── .env.example        ← contoh konfigurasi
├── .gitignore          ← pastikan ssh/ ada di sini
├── ssh/                ← folder SSH key (JANGAN dicommit)
│   ├── bot_key         ← private key
│   └── bot_key.pub     ← public key
└── README.md           ← dokumentasi ini
```

---

## 🐛 Troubleshooting

| Error / Gejala | Solusi |
|---|---|
| `Harap setting dahulu SSH` | Isi `SSH_KEY_LOCATION` dan `SSH_USER_NAME` di env |
| `Shutdown/Restart Gagal Jalankan` | Cek SSH key path, permission, dan sudoers |
| Bot tidak reply | Cek `CHAT_ID` benar, tanpa spasi/kutip |
| Notifikasi startup tidak muncul | Pastikan `post_init` lewat `.post_init()` di builder |
| Suhu N/A | `privileged: true` belum diset atau driver sensor belum ada |
| `unexpected keyword argument 'persistent'` | Hapus `persistent=True` dari `ReplyKeyboardMarkup` |
| `Command pc-info is not valid` | Nama command tidak boleh pakai `-`, gunakan `_` |
| SSH: `Permission denied` | Cek `authorized_keys` dan permission folder `.ssh` |
| SSH: `sudo: no tty` | Pastikan sudoers sudah diset `NOPASSWD` untuk shutdown/reboot |
