# Telegram Günlük Finans & Haber Botu

Her gün saat 09:00'da (Europe/Istanbul) altın, gümüş, döviz, BIST-100, kripto para fiyatlarını ve güncel haberleri Telegram'a gönderen bot.

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

## Telegram Bot Oluşturma (BotFather)

1. Telegram'da [@BotFather](https://t.me/BotFather) ile sohbet başlat
2. `/newbot` komutunu gönder
3. Bot adını gir (ör. "Günlük Finans Botu")
4. Kullanıcı adını gir (ör. `gunluk_finans_bot`)
5. BotFather sana bir **token** verecek — bunu kopyala

### Chat ID Bulma

1. Oluşturduğun bota Telegram'dan `/start` mesajı gönder
2. Tarayıcıda şu URL'yi aç (TOKEN yerine kendi token'ını yaz):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. JSON çıktısında `"chat":{"id":123456789}` şeklinde **chat_id**'ni bul

## Ortam Değişkenleri (.env)

`.env.example` dosyasını `.env` olarak kopyalayıp değerleri doldur:

```bash
cp .env.example .env
```

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIjKlMnOpQrStUvWxYz
TELEGRAM_CHAT_ID=123456789
```

| Değişken | Açıklama |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather'dan aldığın bot token'ı |
| `TELEGRAM_CHAT_ID` | Mesajların gönderileceği sohbet/kanal ID'si |

## Çalıştırma

### Scheduler modu (varsayılan)

```bash
python main.py
```

Bot başladığında:
1. Telegram'a "Bot başladı ✅" test mesajı gönderir
2. APScheduler ile her gün **09:00 Europe/Istanbul**'da günlük özeti gönderir
3. `Ctrl+C` ile düzgün kapatılır

### Manuel tetikleme

```bash
python main.py --now
```

Günlük özeti **hemen** gönderir ve çıkar. Scheduler başlatmaz.

## Günlük Özet İçeriği

| Bölüm | Kaynak | Veri |
|---|---|---|
| Altın & Gümüş | yfinance | Gram TRY fiyatı + günlük değişim |
| Döviz | yfinance | USD/TRY, EUR/TRY + günlük değişim |
| BIST-100 | yfinance | Endeks fiyatı + günlük değişim |
| Kripto | CoinGecko API | BTC, ETH fiyatları (USD + TRY) + 24s değişim |
| Haberler | RSS (feedparser) | Hürriyet, Bloomberg HT, Google News TR |

## Testler

```bash
# Tüm testleri çalıştır
python -m pytest tests/ -v

# Sadece entegrasyon testleri
python -m pytest tests/test_integration.py -v
```

## Proje Yapısı

```
daily-bot/
├── main.py              # Giriş noktası, APScheduler yapılandırması
├── constants.py         # Sabitler (ticker, RSS URL, zamanlama)
├── .env.example         # Ortam değişkenleri şablonu
├── requirements.txt     # Bağımlılıklar
├── data/
│   ├── finance.py       # yfinance: altın, gümüş, döviz, BIST-100
│   ├── crypto.py        # CoinGecko: BTC, ETH fiyatları
│   └── news.py          # RSS: haber başlıkları
├── bot/
│   ├── formatter.py     # Verileri Telegram mesajına dönüştürür
│   └── telegram_bot.py  # Telegram API ile mesaj gönderme
├── scheduler/
│   └── jobs.py          # run_daily_summary() günlük görev
└── tests/
    ├── test_finance.py
    ├── test_crypto.py
    ├── test_news.py
    ├── test_formatter.py
    ├── test_telegram_bot.py
    └── test_integration.py
```
