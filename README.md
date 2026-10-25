# EGONIA Crypto Signal Bot

Windows tabanlı Telegram kripto sinyal, VIP üyelik ve USDT-TRC20 ödeme botu.

`config.json` gerçek Telegram yayını için açıktır. Model ürünü 5 dakikalık
mumlardan 2 saatlik LONG/SHORT scalp tahmini üretir; hedef %1,2, stop %0,7,
FREE kota 2/gün ve VIP kota 6/gündür. İlk başlangıçta eski 12 saatlik modeller
otomatik geçersiz sayılır ve yeni scalp modelleri eğitilir.

## Windows kurulumu

1. Depoyu ZIP olarak indirin ve klasöre çıkarın.
2. `SETUP_TELEGRAM.bat` çalıştırın. BotFather tokenı gizli girişle yalnızca
   yerel ve Git tarafından yok sayılan `CREDENTIALS.cmd` dosyasına yazılır.
3. Sinyal tarayıcı için `START.bat`, VIP ödeme/üyelik için
   `START_PAYMENT_BOT.bat` çalıştırın.
4. Bir kez `INSTALL_AUTOSTART.bat` çalıştırın. Ödeme botu ve gerçek sinyal
   tarayıcısı Windows oturumu açıldığında otomatik başlar; beklenmedik şekilde
   kapanırlarsa yeniden açılırlar.

Çıktılar `payment_bot.log` ve `scanner.log` dosyalarına yazılır. Aynı anda ikinci
ödeme botu çalıştırılamaz. Otomatik başlatmayı kaldırmak için
`REMOVE_AUTOSTART.bat` kullanılır. Bilgisayar kapalı veya internetsizken ödeme
işlenemez; gerçek 7/24 kullanım için bot bir sunucuda çalıştırılmalıdır.

Tokenı GitHub dosyalarına, issue'lara veya sohbetlere yazmayın.

## VIP ödeme

- Fiyat: 9,90 USDT / 30 gün
- Ağ: TRON (TRC20)
- Alıcı: `TR6c5N8GwTF1FKtQsGVTSPdQfh9m74NXYB`
- VIP kanal kimliği: `-1004409446943`

Müşteri free kanal mesajındaki bağlantıdan bota ulaşır, özel konuşmada
`/subscribe T_SENDER_ADDRESS` yazar, tam 9,90 USDT gönderir ve `/payment TXID`
ile onaylatır. Başarılı doğrulamada 30 günlük üyelik ve kişisel VIP katılım
bağlantısı otomatik gönderilir. `/invite` bağlantıyı tekrar almak içindir.
Eski Türkçe komutlar da desteklenir. Ayrıntılar için
`PAYMENT_SETUP_TR.md` dosyasına bakın.

Ödeme doğrulaması cüzdan private key veya seed phrase kullanmaz. Onaylanmış
zincir verisini, resmî USDT kontratını, tutarı, gönderici/alıcı adreslerini ve
TXID'nin daha önce kullanılmadığını kontrol eder.

## Test

```bat
py -3 -m pip install -r requirements.txt
py -3 -m unittest discover -v
```

Sinyal modelleri ve performans ölçümleri için `README_V3_7_1.md` ile
`README_TWO_MODELS_V3_6.md` belgelerini okuyun. Geçmiş test sonucu gelecekteki
performansı garanti etmez.
