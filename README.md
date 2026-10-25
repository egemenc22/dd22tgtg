# EGONIA Crypto Signal Bot

Windows tabanlı Telegram kripto sinyal, VIP üyelik ve USDT-TRC20 ödeme botu.

## Windows kurulumu

1. Depoyu ZIP olarak indirin ve klasöre çıkarın.
2. `SETUP_TELEGRAM.bat` çalıştırın. BotFather tokenı gizli girişle yalnızca
   yerel ve Git tarafından yok sayılan `CREDENTIALS.cmd` dosyasına yazılır.
3. Sinyal tarayıcı için `START.bat`, VIP ödeme/üyelik için
   `START_PAYMENT_BOT.bat` çalıştırın.

Tokenı GitHub dosyalarına, issue'lara veya sohbetlere yazmayın.

## VIP ödeme

- Fiyat: 9,90 USDT / 30 gün
- Ağ: TRON (TRC20)
- Alıcı: `TR6c5N8GwTF1FKtQsGVTSPdQfh9m74NXYB`
- VIP kanal kimliği: `-1004409446943`

Müşteri botla özel konuşmada `/abonelik T_GONDEREN_ADRESI` yazar, tam 9,90
USDT gönderir ve `/odeme TXID` ile onaylatır. `/davet` kişisel VIP katılım
bağlantısını verir. Ayrıntılar için `PAYMENT_SETUP_TR.md` dosyasına bakın.

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
