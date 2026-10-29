# AdSense "Low value content" — Yapılacaklar

Tarih: 2026-10-28 · Kaynak: Memorlex oturumundaki site incelemesi

AdSense başvurusu "Low value content" (değeri düşük içerik) gerekçesiyle reddedildi. Aşağıdakiler önem sırasına göre.

## 1. Yasal sayfalar (EN KRİTİK)
- [ ] **Gizlilik politikası** (TR/DE/EN, sonra diğer diller): çerezler, Google AdSense, kişiselleştirilmiş reklam, Google'ın gizlilik sayfasına link, analytics varsa o da.
- [ ] **Impressum** (§5 DDG — Almanya'da reklam geliri olan sitede zorunlu): ad soyad, adres, e-posta.
  - Karar bekliyor: ev adresi mi, c/o Impressum adres hizmeti mi? (Ev adresini yayımlamamak için c/o önerilir.)
- [ ] **Çerez onay banner'ı / CMP**: AEA'da AdSense için Google sertifikalı CMP gerekiyor (AdSense > Gizlilik ve mesajlaşma > GDPR mesajı en kolayı).
- [ ] Footer'a Gizlilik + Impressum + İletişim linkleri.

## 2. Toplu makine çevirisi (scaled content sinyali)
- TR 80 yazı → EN/DE/ES/AR/HI'de de ~80'er çeviri, ~400 yazı 21–25 Ekim'de toplu yayımlandı.
- HI çeviriler ortalama 4.422 kelime, TR orijinaller 1.814 → model metni şişirmiş.
- [ ] İnceleme bitene kadar **HI ve AR'yi noindex** (veya yayından kaldır).
- [ ] Kontrol edilen diller açık kalsın: TR, DE, EN (ES opsiyonel).
- [ ] Çeviri job'unu (com.barash.lebeninsider-translate) yavaşlat: günde birkaç yazı, toplu batch yok.
- [ ] Gelecek tarihli otomatik yazı akışını gözden geçir.

## 3. Kısa yazılar (<300 kelime) — genişlet veya birleştir
Kendi deneyiminden 2–3 paragraf ekle, ya da ilgili olanları birleştir.

| Kelime | Dosya |
|---|---|
| 145 | content/tr/kariyer/yapay-zeka-ile-cv-2-format.md |
| 176 | content/tr/kariyer/yapay-zeka-ile-cv-1-hedef-pazar.md |
| 181 | content/tr/kariyer/yapay-zeka-ile-cv-3-kendini-anlat.md |
| 168 | content/tr/almanya/yasam/almanyada-disarida-yemek-fiyatlari.md |
| 180 | content/tr/almanya/yasam/kleingarten-almanya-sehir-icinde-bahce.md |
| 185 | content/tr/almanya/yasam/bavyera-evleri-ve-yapi-kurallari.md |
| 241 | content/tr/kariyer/kendi-profilini-cikar.md |
| 247 | content/tr/almanya/yasam/cocuk-buyutmek-turkiye-almanya.md |
| 254 | content/tr/almanya/yasam/calisma-hayati-ve-sosyal-sistem-turkiye-almanya.md |
| 264 | content/tr/almanya/yasam/almanyada-pazar-gunu-ve-resmi-tatiller.md |
| 268 | content/tr/kariyer/once-kendini-tani-sonra-meslegi-sec.md |
| 269 | content/tr/almanya/yasam/egitim-ve-ausbildung-turkiye-almanya.md |
| 273 | content/tr/almanya/yasam/turkiye-mi-almanya-mi-karsilastirmadan-once.md |
| 285 | content/tr/almanya/yasam/bolgesel-trenler-ve-bebek-arabasi-alani.md |
| 287 | content/tr/almanya/yasam/konut-ve-yasam-alani-turkiye-almanya.md |
| 289 | content/tr/kariyer/dil-bilmek-ile-konusabilmek.md |
| 295 | content/tr/almanya/yasam/almanyaya-tasinma-kararim-kriterler.md |

- [ ] CV serisi (1-2-3) → tek güçlü rehber + eski URL'lere yönlendirme (Hugo `aliases`).
- [ ] "Türkiye vs Almanya" karşılaştırma yazıları → ya birleştir ya her birine kişisel örnek ekle.
- Değişiklik TR'de bitince çevirileri yeniden üret.

## 4. Boş/zayıf bölüm sayfaları
- [ ] content/tr/yemek/_index.md — 0 kelime
- [ ] content/tr/_index.md — 29 kelime
- [ ] content/tr/kariyer/_index.md — 40 kelime
- [ ] content/tr/almanya/yasam/_index.md — 122 kelime
Her birine 150–250 kelimelik tanıtım: bölüm ne anlatıyor, kimin için, öne çıkan yazılar.

## 5. Güven / E-E-A-T
- Güçlü: Hakkımda sayfası (gerçek kişi, gerçek deneyimler), yazılar kendi ham notlarından.
- [ ] Yazı altına kısa **yazar kutusu** (foto + 2 cümle + Hakkımda linki).
- [ ] Mümkün olan yazılara **kendi fotoğrafların**.
- [ ] AI destekli yazılarda kısa şeffaflık notu ("Kendi notlarımdan, yapay zekâ desteğiyle düzenlendi") — AB AI Act Madde 50 ile de uyumlu.
- [ ] İç linkler: her yazıdan 2–3 ilgili yazıya link.

## 6. Yeniden başvuru
- [ ] Yukarıdakiler yayında → 2–3 hafta bekle.
- [ ] Search Console'da yeni/güncellenen sayfaların tarandığını kontrol et.
- [ ] AdSense > Siteler > lebeninsider > **Request review**.

## İş bölümü
| İş | Kim |
|---|---|
| Gizlilik politikası, Impressum şablonu, footer linkleri, bölüm girişleri, HI/AR noindex, yazar kutusu | Claude |
| Impressum adres kararı, CMP'yi AdSense panelinden açmak | Barash |
| Kısa yazılara kişisel ekler | Birlikte (Barash not verir, Claude yazar) |
| Push + Request review | Barash |

---

## Araştırma notları (29 Ekim 2026)

### Sitenin şu anki durumu (repo taraması)
- **Gizlilik politikası ve Impressum sayfası YOK.** `content/tr/` altında sadece hakkimda ve iletisim var; footer menüsü de yok. → 1. madde gerçekten en kritik.
- Yayındaki yazı sayısı / ortalama kelime: TR 79 / 1.708 · EN 92 / 2.118 · DE 79 / 982 · ES 79 / 2.317 · AR 79 / 1.879 · HI 79 / 2.403. (HI'nin 4.422 kelime tespiti farklı bir sayımdan; yine de ES/HI çevirileri TR'den belirgin uzun → şişirme var.)
- 300 kelime altı: TR 18, EN 8, DE 12, ES 6, AR 9, HI 5.
- Asıl zayıf nokta muhtemelen kısa yazılar değil: eski Gemini şablonlu uzun yazılar ("Şehir hakkında / Gezilecek yerler / Nerede yenir" kalıbı, sahte Google Maps arama linkleri, genel ansiklopedik paragraflar, örn. paylaşım kültürü yazısı 23 KB). Bunlar "kişisel bakış açısı olmayan AI içeriği" sinyali veriyor ve 6 dile çoğaltılmış durumda.

### Google ne diyor?
- **Makine çevirisi:** Google'ın spam politikasında "scaled content abuse" kapsamında "çevirme gibi otomatik dönüşümlerle, kullanıcıya az değer katan çok sayıda sayfa üretmek" sayılıyor. Google 2025'te "AI ile çevrilmiş içerik tek başına spam değildir" dedi; belirleyici olan kaynağın kalitesi ve kullanıcıya değer. Öneri: önce kaliteli/özgün kaynağı çevir, toplu AI içeriğini çevirip çoğaltma, çevirileri insan gözüyle kontrol et, küçük başla. ([GSQI özeti](https://www.gsqi.com/marketing-blog/auto-translating-content-google-scaled-content-abuse/))
- **AdSense red sebepleri (genel deneyim):** ince/az içerik, kişisel bakış açısı olmayan AI içerik, makine çevirisi, odak dağınıklığı, eksik Gizlilik/Hakkımda/İletişim sayfaları, zayıf navigasyon. Ret sonrası değişiklik yapıp 1–2 hafta beklemek; çok sık tekrar başvuru bekleme süresine yol açabiliyor. ([eastondev rehberi](https://eastondev.com/blog/en/posts/media/20260319-adsense-approval-guide))
- **CMP (çerez onayı):** AEA/UK'de 16 Ocak 2024'ten beri, kişiselleştirilmiş reklam için Google sertifikalı, TCF entegre CMP zorunlu. AdSense > Gizlilik ve mesajlaşma > "Avrupa düzenlemeleri" mesajı sertifikalı sayılıyor → ayrı CMP satın almaya gerek yok. ([AdSense yardım](https://support.google.com/adsense/answer/13554116?hl=en))
- **Impressum (§5 DDG):** "Ladungsfähige Anschrift" gerekiyor: posta kutusu (Postfach) yetmez; c/o Impressum hizmeti, posta gerçekten size iletiliyorsa ve orada tebligat alınabiliyorsa yaygın olarak kullanılıyor ama hukuken tartışmalı/riskli olabiliyor. Ev adresi yerine c/o hizmeti tercih edilecekse sözleşmesinde tebligatın (Zustellung) kabul edildiği yazmalı. Kesin karar için avukat/IHK bilgisi önerilir.

### Önerilen sıra (araştırmaya göre güncel)
1. Gizlilik politikası + Impressum + footer (yasal ve AdSense için zorunlu).
2. AdSense panelinden AB onay mesajını (CMP) aç.
3. **AR ve HI'yi noindex** (sitemap'ten de çıkar); ES'yi şimdilik açık bırakmak yerine noindex düşünülebilir (ES'de de şişirme var). TR/EN/DE açık kalsın.
4. Eski Gemini şablon yazılarını ele al: ya kişisel deneyimle yeniden yaz, ya noindex/taslak. Önce TR'deki en zayıf 10–15 tanesi.
5. Kısa yazıları kişisel eklerle genişlet / CV serisini birleştir.
6. Bölüm girişleri, yazar kutusu, iç linkler.
7. Çeviri job'u: şimdi her dilde günde 1; AR/HI/ES noindex kararından sonra sadece EN/DE'ye çevirmek düşünülebilir.
8. 2–3 hafta sonra Request review.
