# Crypto Signal Commercial v1.7 — Dynamic USDT Discovery

## Neler yeni
- Binance, MEXC, Gate Spot USDT pariteleri otomatik keşfedilir.
- Yalnızca aktif spot pariteler; sabit paralar ve kaldıraç token etiketleri elenir.
- 24 saatlik quote volume ile filtrelenir ve sıralanır.
- Her borsadan en fazla 60 piyasa, her döngüde toplam 12 piyasa taranır.
- Keşif her 3600 saniyede bir yenilenir; ağ hatasında bot çalışmayı sürdürür.
- Önceki grafik/X/Telegram Free/VIP altyapısı korunur.

## Yapılandırma (`config.json`)
- `auto_discovery`: true (false ile eski `symbols` sabit listesi)
- `min_daily_quote_volume_usdt`: 1000000
- `max_pairs_per_exchange`: 60
- `markets_per_cycle`: 12
- `discovery_refresh_seconds`: 3600
- `exchanges`: Binance / MEXC / Gate

## Önemli
- Piyasa taraması 2026 API uç noktalarını esas alır fakat canlı dış API erişimi bu test ortamında doğrulanmadı. Borsalar API formatlarını değiştirebilir.
- Çok sayıda piyasa ve zaman dilimi: `markets_per_cycle * len(strategy_timeframes)` adet mum API isteği/döngü. Varsayılan 36 istek/döngü + keşif isteği/saat.
- `dry_run: true`, X/Telegram yayınları kapalıdır. Gerçek hesap kimlik bilgileri ve doğrulama gerekir.
- USDT ödeme sistemi bu sürüme dahil değildir; sonraki aşamaya bırakıldı.
- Bu paket trading emri vermez, sinyallerin kârlılığı kanıtlanmış değildir.

## Başlat
`START.bat` ile yerel panel: http://127.0.0.1:8787
Test: `python -m unittest discover -s . -p "test_*.py"`
