# Crypto Signal Commercial v1.3 — Windows

Bu paket v1.2'nin tamamını içerir. Yeni özellik: **Telegram VIP kanalı için kimlik kontrollü katılım isteği**.

## Kurulum
1. `config.json` içinde `enable_vip_member_enforcement`: true ve `vip_join_request_mode`: true yapın.
2. Botu VIP kanalına **yönetici** olarak ekleyin. Davet bağlantısı üretme, katılım isteklerini yönetme ve üyeleri çıkarma yetkileri gerekli.
3. Windows ortam değişkenleri: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_VIP_CHAT_ID`. Bot için tek bir `getUpdates` tüketicisi çalıştırın; başka bir bot süreci/webhook aynı token ile güncellemeleri almamalı.
4. Kullanıcının sayısal Telegram user ID bilgisini alın. **Ödemeyi manuel doğruladıktan sonra** `VIP_GRANT_30_DAYS.cmd` ile üyeliği açın. Kullanıcı ID'si bilinmeden davet gönderilmez.
5. `VIP_SYNC.cmd` ile katılım isteği bağlantısı oluşturun. Link veritabanında `members.invite_link` sütununa yazılır; üyeye doğrudan, özel yoldan iletin. Bot çalışırken katılım isteğini yalnızca kayıtlı ve süresi geçmemiş Telegram kullanıcısından gelmişse onaylar.
6. Süresi dolan kullanıcılar için senkronizasyon saatte bir yapılır. Üyelik eşleşmesi ödemeye değil yönetici tarafından girilen kayda bağlıdır.

## Sınırlar
- Ödeme sağlayıcısı, otomatik ödeme doğrulama ve web ödeme ekranı **yok**. Üyelik açma hâlâ manuel.
- Gerçek X/Telegram yayınları varsayılan olarak kapalıdır. API kimliklerini ve mevcut config bayraklarını kullanıcı ayarlamalıdır.
- Mevcut sinyal tetikleyicisi temel Binance fiyat/hacim kuralıdır; önceki ML modelleri entegre edilmemiştir. Performans doğrulanmamıştır.
- Telegram katılım isteklerinin bot tarafından alınabilmesi için bot yöneticiliği ve uygun haklar gerekir. Gönderilen davet bağlantısı tek başına kullanıcı kimliği garanti etmez; gerçek kontrol `chat_join_request.from.id` üzerinden yapılır.
- Yerel panel sadece 127.0.0.1 üzerinde çalışır.

## Testler
`py -3 -m unittest discover -v` ve `py -3 signal_bot.py --self-test`.
