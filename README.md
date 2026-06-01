# 🖥️ Telegram Laptop Monitor Bot

Bot Telegram untuk monitoring laptop Ubuntu dari jarak jauh — cek suhu, RAM, CPU, GPU, baterai, IP, serta **shutdown & restart remote**.

---

## ✨ Fitur

| Fitur | Keterangan |
|---|---|
| 🟢 Notifikasi hidup | Kirim pesan otomatis beserta IP saat laptop nyala |
| 🖥️ PC Info | OS, RAM, CPU & GPU usage, suhu, baterai, IP lokal & publik |
| 🌡️ Monitor suhu | Warning otomatis jika suhu melebihi batas yang diset |
| 🔄 Restart | Restart laptop remote dengan konfirmasi |
| 🔴 Shutdown | Matikan laptop remote dengan konfirmasi |
| 📋 Menu tombol | Keyboard permanen di bawah chat, tidak perlu ketik |
| 👥 Multi user | Bisa diakses lebih dari 1 orang |
| 🔒 Akses terbatas | Hanya user terdaftar yang bisa pakai bot |

---

## 📋 Perintah Bot

| Perintah / Tombol | Fungsi |
|---|---|
| `/start` | Salam pembuka + tampilkan menu |
| `/menu` | Tampilkan ulang tombol jika hilang |
| `/pc_info` atau 🖥️ PC Info | Info sistem lengkap |
| `/get_max_temperature` atau 🌡️ Cek Suhu Max | Lihat batas suhu aktif |
| `/set_max_temperature` atau ⚙️ Set Suhu Max | Set batas suhu CPU/GPU |
| `/pc_restart` atau 🔄 Restart | Restart laptop |
| `/pc_shutdown` atau 🔴 Shutdown | Matikan laptop |

---

## 🗂️ Struktur File Project

```
telegram-monitor-bot/
├── bot.py                ← kode utama bot
├── Dockerfile            ← image Docker
├── docker-compose.yml    ← stack untuk Portainer
├── requirements.txt      ← dependency Python
├── .env.example          ← contoh konfigurasi env
├── .gitignore            ← pastikan ssh/ ada di sini
├── ssh/                  ← folder SSH key (JANGAN dicommit ke GitHub)
│   ├── bot_key           ← private key
│   └── bot_key.pub       ← public key
└── README.md             ← dokumentasi ini
```

---

## 🚀 Panduan Setup Lengkap (Untuk Pemula)

### BAGIAN 1 — Persiapan Telegram

#### 1.1 Buat Bot Telegram

1. Buka Telegram → cari **@BotFather**
2. Klik **Start**
3. Ketik `/newbot`
4. Ikuti instruksi — masukkan nama bot dan username bot
5. BotFather akan memberikan **Token**, contoh:
   ```
   1234567890:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
6. Simpan token ini, akan dipakai nanti

#### 1.2 Dapatkan CHAT_ID Anda

CHAT_ID adalah ID unik akun Telegram Anda. Bot hanya merespons ID yang terdaftar.

**Cara paling mudah — @userinfobot:**

1. Cari **@userinfobot** di Telegram
2. Klik **Start**
3. Bot langsung reply, catat angka di bagian **Id**:
   ```
   Your user information:
   Id: 987654321       ← ini CHAT_ID Anda
   First name: Eric
   ```

**Cara alternatif — @RawDataBot:**

1. Cari **@RawDataBot** → klik **Start**
2. Lihat bagian JSON yang muncul:
   ```json
   "chat": {
       "id": 987654321   ← ini CHAT_ID
   }
   ```

**Untuk Group Chat:**

1. Tambahkan bot ke grup
2. Kirim pesan di grup
3. Buka browser, akses URL (ganti TOKEN dengan token bot Anda):
   ```
   https://api.telegram.org/botTOKEN/getUpdates
   ```
4. Cari `"chat"` → `"id"` — angkanya **negatif** untuk grup:
   ```json
   "chat": { "id": -1001234567890 }
   ```

#### 1.3 CHAT_ID untuk Lebih dari 1 Orang

Bot bisa diakses oleh beberapa orang sekaligus. Pisahkan dengan koma:

```bash
# 1 orang
CHAT_ID=987654321

# 2 orang atau lebih — pisah koma
CHAT_ID=987654321,111222333,444555666

# Alternatif — pisah garis lurus
CHAT_ID=987654321|111222333
```

> ⚠️ Jangan ada spasi di sekitar pemisah
> ✅ Benar : `CHAT_ID=101,102`
> ❌ Salah : `CHAT_ID=101, 102`

---

### BAGIAN 2 — Persiapan SSH di Laptop

Fitur **Shutdown** dan **Restart** bekerja dengan cara bot SSH ke laptop dari dalam container. Bagian ini wajib disetup agar kedua fitur tersebut bisa berjalan.

#### 2.1 Install SSH Server

```bash
sudo apt install openssh-server -y
sudo systemctl enable ssh
sudo systemctl start ssh

# Verifikasi SSH berjalan
sudo systemctl status ssh
# Harus tampil: Active: active (running)
```

#### 2.2 Buat SSH Key Khusus untuk Bot

```bash
# Buat folder ssh di dalam folder project
mkdir -p /home/eric-tandra/PortainerApp/telegram-monitor-bot/ssh

# Generate SSH key baru (tanpa passphrase)
ssh-keygen -t ed25519 \
  -f /home/eric-tandra/PortainerApp/telegram-monitor-bot/ssh/bot_key \
  -N "" \
  -C "telegram-bot-key"
```

Perintah di atas membuat 2 file:
- `ssh/bot_key` → **private key** (dipakai oleh container)
- `ssh/bot_key.pub` → **public key** (didaftarkan ke laptop)

#### 2.3 Daftarkan Public Key ke Laptop

```bash
# Buat folder .ssh jika belum ada
mkdir -p ~/.ssh

# Daftarkan public key
cat /home/eric-tandra/PortainerApp/telegram-monitor-bot/ssh/bot_key.pub \
  >> ~/.ssh/authorized_keys

# Set permission yang benar
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 600 /home/eric-tandra/PortainerApp/telegram-monitor-bot/ssh/bot_key
```

#### 2.4 Izinkan Shutdown & Reboot Tanpa Password

```bash
sudo visudo
```

Tambahkan baris ini di **paling bawah** (ganti `eric-tandra` dengan username Anda):

```
eric-tandra ALL=(ALL) NOPASSWD: /sbin/shutdown, /sbin/reboot
```

Simpan: `Ctrl+O` → `Enter` → `Ctrl+X`

#### 2.5 Test Koneksi SSH

```bash
ssh -i /home/eric-tandra/PortainerApp/telegram-monitor-bot/ssh/bot_key \
    -o StrictHostKeyChecking=no \
    eric-tandra@127.0.0.1 \
    "echo SSH OK"
```

Output harus: `SSH OK`

Test sudo tanpa password:

```bash
ssh -i /home/eric-tandra/PortainerApp/telegram-monitor-bot/ssh/bot_key \
    -o StrictHostKeyChecking=no \
    eric-tandra@127.0.0.1 \
    "sudo shutdown -h +1 && sudo shutdown -c"
```

Tidak boleh muncul pertanyaan password. Kalau OK berarti semua sudah siap.

---

### BAGIAN 3 — Setup GitHub (Opsional tapi Direkomendasikan)

Menyimpan script di GitHub memudahkan update ke depannya — tinggal push ke GitHub lalu redeploy di Portainer.

#### 3.1 Buat .gitignore dulu (PENTING)

```bash
cd /home/eric-tandra/PortainerApp/telegram-monitor-bot

cat > .gitignore << 'EOF'
ssh/
.env
__pycache__/
*.pyc
EOF
```

> ⚠️ Folder `ssh/` wajib ada di `.gitignore` agar private key tidak terupload ke GitHub!

#### 3.2 Push ke GitHub

```bash
cd /home/eric-tandra/PortainerApp/telegram-monitor-bot

git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/USERNAME/telegram-monitor-bot.git
git push -u origin main
```

---

### BAGIAN 4 — Deploy di Portainer

#### 4.1 Buat Stack Baru

1. Buka Portainer → klik **Stacks** di sidebar
2. Klik **+ Add stack**
3. Beri nama: `pc-bot-telegram`

#### 4.2 Pilih Sumber (salah satu)

**Dari GitHub (direkomendasikan):**

Pilih tab **Repository**, isi:

| Field | Value |
|---|---|
| Repository URL | `https://github.com/USERNAME/telegram-monitor-bot` |
| Repository reference | `refs/heads/main` |
| Compose path | `docker-compose.yml` |

**Dari Web Editor (tanpa GitHub):**

Pilih tab **Web editor**, paste isi `docker-compose.yml`:

```yaml
version: "3.9"

services:
  telegram-monitor-bot:
    build:
      context: .
      dockerfile: Dockerfile
    pull_policy: build
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
      - ${SSH_KEY_HOST_PATH}:/app/ssh:ro
      - /sys:/sys:ro
      - /proc:/proc:ro
      - bot-data:/app/data

volumes:
  bot-data:
    driver: local
```

#### 4.3 Isi Environment Variables

Scroll ke bawah, isi semua variable berikut:

| Name | Contoh | Keterangan |
|---|---|---|
| `BOT_TOKEN` | `1234567890:AAxxxx` | Token dari @BotFather |
| `CHAT_ID` | `987654321` | ID dari @userinfobot, bisa multiple |
| `SSH_KEY_HOST_PATH` | `/home/eric-tandra/PortainerApp/telegram-monitor-bot/ssh` | Path folder ssh di laptop host |
| `SSH_KEY_LOCATION` | `/app/ssh/bot_key` | Path key di dalam container (selalu ini) |
| `SSH_USER_NAME` | `eric-tandra` | Username laptop |

#### 4.4 Deploy

Klik **Deploy the stack** dan tunggu hingga selesai.

Cek log untuk memastikan bot berjalan:

```bash
docker logs tg-laptop-monitor --tail 30
```

Harus muncul:
```
INFO - Allowed CHAT_IDs: ['987654321']
INFO - SSH_USER: 'eric-tandra' | SSH_KEY: '/app/ssh/bot_key'
INFO - Bot berjalan dengan mode polling...
INFO - Startup notification sent to 987654321.
```

Dan di Telegram Anda akan menerima pesan:
```
✅ Laptop sudah hidup!
🏠 Local : 192.168.x.x
🌐 Online: xxx.xxx.xxx.xxx
```

---

### BAGIAN 5 — Update Script ke Depannya

#### Jika pakai GitHub

```bash
# Edit file yang ingin diubah
nano /home/eric-tandra/PortainerApp/telegram-monitor-bot/bot.py

# Push ke GitHub
cd /home/eric-tandra/PortainerApp/telegram-monitor-bot
git add .
git commit -m "deskripsi perubahan"
git push
```

Lalu di Portainer → **Stacks** → `pc-bot-telegram` → **Pull and redeploy**.

#### Jika tanpa GitHub

```bash
# Edit langsung di server
nano /home/eric-tandra/PortainerApp/telegram-monitor-bot/bot.py
```

Lalu di Portainer → **Containers** → `tg-laptop-monitor` → **Restart**.

> Catatan: Jika ada perubahan di `Dockerfile`, wajib rebuild image dulu:
> ```bash
> cd /home/eric-tandra/PortainerApp/telegram-monitor-bot
> docker build -t tg-monitor-bot:latest .
> ```
> Baru kemudian Pull and redeploy di Portainer.

---

## 🌡️ Cara Kerja Monitor Suhu

Bot mengecek suhu setiap **60 detik**. Jika suhu melebihi **90% dari batas** yang diset, semua CHAT_ID terdaftar mendapat peringatan otomatis:

```
🔥 PERINGATAN SUHU CPU!
Suhu saat ini : 74°
Batas maksimum: 80°
Persentase    : 92.50%
```

Rumus perhitungan: `(suhu_sekarang ÷ batas_max) × 100`

Peringatan tidak berulang sampai suhu turun di bawah 90% lagi.

---

## 🔬 Dukungan Sensor Hardware

| Komponen | Metode Deteksi |
|---|---|
| Suhu CPU Intel | `psutil` → sensor `coretemp` |
| Suhu CPU AMD | `psutil` → sensor `k10temp` |
| Suhu CPU ARM | `/sys/class/thermal/thermal_zone0/temp` |
| Suhu GPU NVIDIA | `nvidia-smi` (driver harus terinstall di host) |
| Suhu GPU AMD | `psutil` → sensor `amdgpu` / `radeon` |
| Baterai | `psutil.sensors_battery()` |
| RAM & CPU Usage | `psutil` |

> Jika sensor tidak terdeteksi, kolom terkait tampil `N/A` — bot tetap berjalan normal.

---

## 🐛 Troubleshooting

| Error / Gejala | Penyebab | Solusi |
|---|---|---|
| `Harap setting dahulu SSH` | Env SSH belum diisi | Isi `SSH_KEY_LOCATION` dan `SSH_USER_NAME` di Portainer |
| `Shutdown/Restart Gagal Jalankan` | SSH gagal konek atau sudoers belum diset | Jalankan test SSH manual, cek sudoers |
| `No such file or directory: 'ssh'` | `openssh-client` belum ada di container | Rebuild image dari Dockerfile terbaru |
| `sudo: a password is required` | Sudoers belum dikonfigurasi | Tambahkan `NOPASSWD` di `sudo visudo` |
| `Permission denied (publickey)` | Public key belum terdaftar | Jalankan perintah di langkah 2.3 |
| Bot tidak reply sama sekali | CHAT_ID salah atau ada spasi/kutip | Cek env `CHAT_ID` di Portainer |
| Notifikasi startup tidak muncul | `post_init` salah cara assign | Pastikan pakai `.post_init()` di builder |
| Suhu tampil N/A | `privileged: true` belum diset | Pastikan ada di docker-compose.yml |
| Tombol menu hilang | Keyboard reset | Ketik `/menu` untuk tampilkan ulang |
| `unexpected keyword argument 'persistent'` | Versi library lama | Hapus `persistent=True` dari ReplyKeyboardMarkup |
