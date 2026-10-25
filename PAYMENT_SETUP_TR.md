# EGONIA VIP ödeme kurulumu

Plan: 9,90 USDT, TRON (TRC20), 30 gün.

Alıcı adresi: `TR6c5N8GwTF1FKtQsGVTSPdQfh9m74NXYB`

## Gizli bilgiler

`CREDENTIALS.md`, `CREDENTIALS.cmd` veya kaynak kod içine token yazmayın ve bu
dosyaları sohbete yüklemeyin. Trust Wallet seed phrase/private key hiçbir zaman
gerekmez. Bulut ortamı ayarlarında şu değerleri tanımlayın:

- `TELEGRAM_BOT_TOKEN`: BotFather bot tokenı (gizli)
- `TELEGRAM_VIP_CHAT_ID`: özel VIP kanalının `-100...` kimliği (gizli anahtar değil)
- `TRONGRID_API_KEY`: TronGrid API anahtarı (gizli)

Botu VIP kanalına yönetici ekleyin. Katılım bağlantısı oluşturma, katılım
isteklerini yönetme ve süresi dolan üyeyi çıkarma yetkileri gereklidir. Aynı bot
tokenıyla başka `getUpdates` süreci veya webhook çalıştırmayın.

## Müşteri akışı

1. Botla özel konuşmada `Unlock VIP` butonuna basılır ve müşterinin Trust Wallet
   TRON adresi doğrudan gönderilir. Bu adres ödeme gönderilecek alıcı adresi
   değil, müşterinin ödeme yapacağı adrestir.
2. Botun verdiği alıcı adrese TRON ağından tam 9,90 resmî USDT gönderilir.
   Ağ ücreti TRX olarak ayrıca ödenir.
3. Müşteri 64 karakterli TXID'yi doğrudan bota yapıştırır.
4. Onaylanmış transfer doğrulanınca 30 gün eklenir ve özel VIP katılım
   bağlantısı otomatik gönderilir. `/invite` bağlantıyı tekrar almak içindir;
   katılım isteği yalnızca aktif üyeye onaylanır.

Borsadan çekimde zincirdeki gönderici adresi müşterinin adresinden farklı
olabilir. İlk sürümde otomatik ödeme için Trust Wallet gibi müşterinin kontrol
ettiği adresten gönderim kullanın; borsa çekimlerini elle inceleyin.

## Çalıştırma

### Windows'taki mevcut kurulum

Bu güncelleme paketini mevcut bot klasörüne çıkarın. Eski `CREDENTIALS.cmd`
dosyanızı koruyun; güncelleme paketinde credential dosyası yoktur. Sinyal botu
ve ödeme botu için ayrı pencerelerde `START.bat` ve `START_PAYMENT_BOT.bat`
çalıştırılabilir. `START_PAYMENT_BOT.bat`, VIP kanal kimliğini hazır kullanır.
TronGrid anahtarı ilk kullanımda zorunlu değildir.

### Bulut ortamı

Bulut ortamı ayarları uygulanıp yayımlandıktan sonra:

```bash
MPLCONFIGDIR=/workspace/egonia-runtime/matplotlib \
  /workspace/egonia-venv/bin/python \
  /workspace/egonia-runtime/start_review.py --membership-bot
```

Önce test botu ve küçük, bilinçli bir uçtan uca deneme kullanın. Gerçek 9,90
USDT transferinin geri alınamayacağını unutmayın.
