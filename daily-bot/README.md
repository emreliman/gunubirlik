# Telegram Günlük Finans & Haber Botu

Telegram **kanalına** altın, gümüş, döviz, BIST-100, kripto para fiyatlarını ve güncel haberleri gönderen bot. Yetkili kullanıcılar özel mesajla komut göndererek verileri kanala iletebilir. Her gün saat 09:00'da (Europe/Istanbul) otomatik günlük özet gönderir.

## Kurulum

```bash
# 1. Repoyu klonla
git clone <repo-url>
cd daily-bot

# 2. Sanal ortam oluştur (önerilir)
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Bağımlılıkları kur
pip install -r requirements.txt
```

## Telegram Hazırlığı

### 1. Bot Oluşturma (BotFather)

1. Telegram'da [@BotFather](https://t.me/BotFather) ile sohbet başlat
2. `/newbot` komutunu gönder
3. Bot adını gir (ör. "Günlük Finans Botu")
4. Kullanıcı adını gir (ör. `gunluk_finans_bot`)
5. BotFather sana bir **token** verecek — bunu kopyala

### 2. Kanal Oluşturma

1. Telegram'da **New Channel** ile kanal oluştur
2. Kanal ayarları → **Administrators** → botu admin olarak ekle → **Post Messages** yetkisi ver
3. Kanal ID'sini al:
   - **Public kanal:** `@kanal_adi` formatında
   - **Private kanal:** Kanala bir mesaj at, `https://api.telegram.org/bot<TOKEN>/getUpdates` ile `-100` ile başlayan ID'yi bul

### 3. Kullanıcı ID Bulma

Telegram'da [@userinfobot](https://t.me/userinfobot)'a mesaj at — sana user ID'ni söyler. Bu ID'yi `ADMIN_USER_IDS` olarak kullan.

## Ortam Değişkenleri (.env)

`.env.example` dosyasını `.env` olarak kopyalayıp değerleri doldur:

```bash
cp .env.example .env
```

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIjKlMnOpQrStUvWxYz
TELEGRAM_CHAT_ID=123456789
TELEGRAM_CHANNEL_ID=@kanal_adi
ADMIN_USER_IDS=123456789,987654321
```

| Değişken | Açıklama |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather'dan aldığın bot token'ı |
| `TELEGRAM_CHAT_ID` | Eski uyumluluk için chat ID (opsiyonel) |
| `TELEGRAM_CHANNEL_ID` | Mesajların gönderileceği kanal ID'si |
| `ADMIN_USER_IDS` | Komut kullanabilecek kullanıcı ID'leri (virgülle ayrılmış) |

## Çalıştırma

### Komut + Scheduler modu (varsayılan)

```bash
python main.py
```

Bot başladığında:
1. Telegram komutlarını dinlemeye başlar (polling)
2. Her gün **09:00 Europe/Istanbul**'da günlük özeti kanala gönderir
3. `Ctrl+C` ile düzgün kapatılır

### Manuel tetikleme

```bash
python main.py --now
```

Günlük özeti **hemen** kanala gönderir ve çıkar.

## Komutlar

Sadece `ADMIN_USER_IDS`'deki kullanıcılar bota **özel mesaj** (DM) göndererek bu komutları kullanabilir:

| Komut | Açıklama | Nereye Gönderir |
|---|---|---|
| `/ozet` | Tam günlük özet | Kanala |
| `/doviz` | USD/TRY, EUR/TRY kurları | Kanala |
| `/altin` | Altın & Gümüş fiyatları | Kanala |
| `/kripto` | BTC, ETH fiyatları | Kanala |
| `/haber` | Son haberler | Kanala |
| `/bist` | BIST-100 + ABD borsaları | Kanala |
| `/grafik <btc\|altin> <1h\|1a>` | 1 hafta/1 ay grafik görseli | Kanala |
| `/dm grafik <btc\|altin> <1h\|1a>` | 1 hafta/1 ay grafik görseli | Admin'e (DM) |
| `/yardim` | Komut listesi | Admin'e (DM) |
| `/start` | Komut listesi | Admin'e (DM) |

Yetkisiz kullanıcılar komut gönderirse "⛔ Bu komutu kullanma yetkiniz yok." yanıtı alır.

## Günlük Özet İçeriği

| Bölüm | Kaynak | Veri |
|---|---|---|
| Altın & Gümüş | yfinance | Gram TRY fiyatı + günlük değişim |
| Döviz | yfinance | USD/TRY, EUR/TRY + günlük değişim |
| BIST-100 | yfinance | Endeks fiyatı + günlük değişim |
| ABD Borsası | yfinance | S&P 500, Dow Jones, Nasdaq |
| Kripto | CoinGecko API | BTC, ETH fiyatları (USD + TRY) + 24s değişim |
| Haberler | RSS (feedparser) | Hürriyet, Bloomberg HT, Google News TR |

## Testler

```bash
# Tüm testleri çalıştır
python -m pytest tests/ -v

# Sadece entegrasyon testleri
python -m pytest tests/test_integration.py -v

# Sadece komut testleri
python -m pytest tests/test_commands.py -v
```

## Deploy (DigitalOcean)

Botu 7/24 çalıştırmak için DigitalOcean Droplet kullanılır. GitHub Student Developer Pack ile **$200 ücretsiz kredi** alınabilir.

### 1. Droplet Oluşturma

1. [DigitalOcean](https://www.digitalocean.com) panelinde **Create** > **Droplets**
2. **Region:** Amsterdam veya Frankfurt
3. **Image:** Ubuntu 24.04 LTS
4. **Size:** Basic > Regular > **$4/ay** (512 MB RAM, 1 vCPU)
5. **Authentication:** SSH Key
6. **Create Droplet** → IP adresini not al

### 2. Sunucu Kurulumu

```bash
ssh root@DROPLET_IP

# Sistem güncelle
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git

# Bot kullanıcısı oluştur
adduser --disabled-password --gecos "" botuser
su - botuser

# Projeyi kur
mkdir ~/app && cd ~/app
git clone <repo-url> .
cd daily-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Ortam Değişkenleri

```bash
nano ~/app/daily-bot/.env
```

`.env.example` dosyasındaki değişkenleri kendi değerlerinizle doldurun.

### 4. Test

```bash
cd ~/app/daily-bot
source venv/bin/activate
python -m pytest tests/ -v
python main.py --now
```

### 5. systemd Servisi (7/24 Çalışma)

`root` kullanıcı ile:

```bash
nano /etc/systemd/system/telegram-bot.service
```

İçerik:

```ini
[Unit]
Description=Telegram Daily Finance Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/app/daily-bot
ExecStart=/home/botuser/app/daily-bot/venv/bin/python main.py
Restart=always
RestartSec=10
EnvironmentFile=/home/botuser/app/daily-bot/.env

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable telegram-bot
systemctl start telegram-bot
```

### 6. Yönetim Komutları

| İşlem | Komut |
|---|---|
| Sunucuya bağlan | `ssh root@DROPLET_IP` |
| Bot durumu | `systemctl status telegram-bot` |
| Botu yeniden başlat | `systemctl restart telegram-bot` |
| Botu durdur | `systemctl stop telegram-bot` |
| Canlı log izle | `journalctl -u telegram-bot -f` |
| Son 50 log satırı | `journalctl -u telegram-bot -n 50` |

### 7. Kod Güncelleme

```bash
ssh root@DROPLET_IP
cd /home/botuser/app
su - botuser
cd ~/app
git pull
cd daily-bot
source venv/bin/activate
pip install -r requirements.txt
exit
systemctl restart telegram-bot
```

Alternatif olarak dosyaları `scp` ile kopyalayabilirsiniz:

```powershell
scp -r .\daily-bot\* root@DROPLET_IP:/home/botuser/app/daily-bot/
ssh root@DROPLET_IP "systemctl restart telegram-bot"
```

## Proje Yapısı

```
daily-bot/
├── main.py              # Giriş noktası, Application + JobQueue
├── constants.py         # Sabitler (ticker, RSS URL, zamanlama)
├── .env.example         # Ortam değişkenleri şablonu
├── requirements.txt     # Bağımlılıklar
├── data/
│   ├── finance.py       # yfinance: altın, gümüş, döviz, BIST-100, ABD borsaları
│   ├── crypto.py        # CoinGecko: BTC, ETH fiyatları
│   └── news.py          # RSS: haber başlıkları
├── bot/
│   ├── auth.py          # Yetkilendirme (admin_only decorator)
│   ├── commands.py      # Komut handler'ları (/ozet, /doviz, vb.)
│   ├── formatter.py     # Verileri Telegram mesajına dönüştürür
│   └── telegram_bot.py  # Telegram API ile mesaj gönderme
├── scheduler/
│   └── jobs.py          # run_daily_summary() günlük görev
└── tests/
    ├── test_auth.py
    ├── test_commands.py
    ├── test_finance.py
    ├── test_crypto.py
    ├── test_news.py
    ├── test_formatter.py
    ├── test_telegram_bot.py
    └── test_integration.py
```
