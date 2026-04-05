"""
expand_posts.py
---------------
Hugo MD dosyalarini Gemini API ile genisletir.
- Tum modelleri + tum keyleri donusumlu kullanir
- Site ici link haritasini otomatik olusturur
- Restoran/mekan/otel icin dis link (Google Maps, Booking.com) ekler

Kullanim:
  python3 script/expand_posts.py content/tr/seyahat/bosna.md --force
  python3 script/expand_posts.py content/tr/seyahat/
  python3 script/expand_posts.py content/tr/ --recursive --force

Gereksinimler:
  pip3 install google-genai
  script/apikeys.txt:
    GEMINI_API_KEY_1=AIza...
    GEMINI_API_KEY_2=AIza...
"""

import os
import sys
import time
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import quote_plus

try:
    from google import genai
except ImportError:
    print("Eksik: pip3 install google-genai")
    sys.exit(1)

# ── Sabitler ─────────────────────────────────────────────────────────────────

MODEL_SEQUENCE = [
    "gemini-2.5-flash",
    "gemini-3-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.1-pro",
    "gemini-2.5-flash-lite",
]

DELAY_SECONDS = 13
MIN_WORDS     = 400
BACKUP_DIR    = "backups"

TRAVEL_DIRS = {"seyahat", "travel", "reisen"}
EXPAT_DIRS  = {"almanya", "germany", "deutschland"}

# Dil → site base URL yolu
LANG_BASE = {
    "tr": "/tr/",
    "en": "/en/",
    "de": "/de/",
}

# ── API Key ───────────────────────────────────────────────────────────────────

def load_api_keys() -> list:
    keys = []
    script_dir = Path(__file__).parent

    for keyfile in [
        script_dir / "apikeys.txt",
        script_dir.parent / "apikeys.txt",
        script_dir / ".env",
        script_dir.parent / ".env",
    ]:
        if keyfile.exists():
            print(f"Key dosyasi: {keyfile}")
            for line in keyfile.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key = line.split("=", 1)[1].strip()
                    if key and len(key) > 10:
                        keys.append(key)
            if keys:
                print(f"{len(keys)} key yuklendi")
                return keys

    for i in range(1, 10):
        val = os.environ.get(f"GEMINI_API_KEY_{i}", "")
        if val and len(val) > 10:
            keys.append(val)
    val = os.environ.get("GEMINI_API_KEY", "")
    if val and len(val) > 10 and val not in keys:
        keys.append(val)

    return keys


# ── Site İçi Link Haritası ───────────────────────────────────────────────────

def build_site_map(content_root: Path, lang: str) -> str:
    """
    content/ klasorunu tarar, mevcut tum yazilarin baslik + URL bilgisini
    string olarak dondurur — prompt'a eklenir.
    """
    base = LANG_BASE.get(lang, "/tr/")
    entries = []

    # Dile gore taranacak kok klasorler
    lang_dirs = {
        "tr": ["tr"],
        "en": ["en"],
        "de": ["de"],
    }
    scan_dirs = lang_dirs.get(lang, ["tr"])

    for scan_dir in scan_dirs:
        scan_path = content_root / scan_dir
        if not scan_path.exists():
            continue

        for md_file in sorted(scan_path.rglob("*.md")):
            # _index ve backup klasorlerini atla
            if md_file.name.startswith("_"):
                continue
            if BACKUP_DIR in md_file.parts:
                continue

            try:
                text = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # Front matter'dan title ve slug cek
            fm_match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
            if not fm_match:
                continue
            fm = fm_match.group(1)

            title_m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
            slug_m  = re.search(r'^slug:\s*["\']?(.+?)["\']?\s*$',  fm, re.MULTILINE)

            title = title_m.group(1).strip() if title_m else md_file.stem
            if slug_m:
                slug = slug_m.group(1).strip()
            else:
                # slug yoksa dosya yolundan uret
                rel = md_file.relative_to(content_root / scan_dir)
                parts = list(rel.parts)
                if parts[-1] == "index.md":
                    parts = parts[:-1]
                else:
                    parts[-1] = parts[-1].replace(".md", "")
                slug = "/".join(parts)

            url = f"https://share-hub-eu.online{base}{slug}/"
            entries.append(f"- [{title}]({url})")

    if not entries:
        return ""

    return "MEVCUT SITE YAZILARI (ilgili olanlara link ver):\n" + "\n".join(entries)


# ── Dış Link Yardımcıları ────────────────────────────────────────────────────

def google_maps_link(place_name: str, city: str = "") -> str:
    query = f"{place_name} {city}".strip()
    return f"https://www.google.com/maps/search/{quote_plus(query)}"


def booking_link(hotel_name: str, city: str = "") -> str:
    query = f"{hotel_name} {city}".strip()
    return f"https://www.booking.com/search.html?ss={quote_plus(query)}"


def tripadvisor_link(place_name: str) -> str:
    return f"https://www.tripadvisor.com/Search?q={quote_plus(place_name)}"


def external_links_section(lang: str) -> str:
    """Prompt'a dis link kullanim talimati ekle"""
    if lang == "tr":
        return """
DIS LINK KURALLARI (zorunlu):
- Her restoran/kafe isminin yanina Google Maps linki ekle:
  Ornek: **Cafe Roma** ([Google Maps]({maps_url}))
- Her otel/hostel isminin yanina hem Google Maps hem Booking.com linki ekle:
  Ornek: **Hotel Muster** ([Google Maps]({maps_url}) | [Booking.com]({booking_url}))
- Her turistik mekan icin Google Maps linki ekle:
  Ornek: **Marienplatz** ([Google Maps]({maps_url}))
- Linkleri Markdown formatinda yaz: [Metin](URL)
- Linkleri UYDURMA — sehir adi + mekan adi ile Google Maps arama URL'si kullan:
  Format: https://www.google.com/maps/search/MEKAN+ADI+SEHIR+ADI
  Format: https://www.booking.com/search.html?ss=OTEL+ADI+SEHIR
"""
    elif lang == "en":
        return """
EXTERNAL LINK RULES (mandatory):
- Add a Google Maps link next to every restaurant/cafe name:
  Example: **Cafe Roma** ([Google Maps]({maps_url}))
- Add both Google Maps and Booking.com links next to every hotel/hostel:
  Example: **Hotel Muster** ([Google Maps]({maps_url}) | [Booking.com]({booking_url}))
- Add a Google Maps link for every tourist attraction:
  Example: **Marienplatz** ([Google Maps]({maps_url}))
- Write links in Markdown format: [Text](URL)
- DO NOT invent links — use Google Maps search URL with place + city name:
  Format: https://www.google.com/maps/search/PLACE+NAME+CITY
  Format: https://www.booking.com/search.html?ss=HOTEL+NAME+CITY
"""
    else:
        return """
EXTERNE LINK-REGELN (Pflicht):
- Neben jedem Restaurant-/Cafe-Namen einen Google Maps-Link einfügen:
  Beispiel: **Cafe Roma** ([Google Maps]({maps_url}))
- Neben jedem Hotel/Hostel sowohl Google Maps als auch Booking.com verlinken:
  Beispiel: **Hotel Muster** ([Google Maps]({maps_url}) | [Booking.com]({booking_url}))
- Für jede Sehenswürdigkeit einen Google Maps-Link einfügen:
  Beispiel: **Marienplatz** ([Google Maps]({maps_url}))
- Links im Markdown-Format schreiben: [Text](URL)
- Keine erfundenen Links — Google Maps Suche mit Orts- und Stadtname verwenden:
  Format: https://www.google.com/maps/search/ORTSNAME+STADTNAME
  Format: https://www.booking.com/search.html?ss=HOTELNAME+STADT
"""


# ── Prompt Builder'lar ────────────────────────────────────────────────────────

def build_travel_prompt(content: str, lang: str, site_map: str) -> str:
    if lang == "tr":
        lang_inst = "Türkçe yaz."
        b = {
            "giris":     "Şehir / Destinasyon Hakkında",
            "gezilecek": "Gezilecek Yerler",
            "yemek":     "Nerede Yenir? Öne Çıkan Restoranlar",
            "konaklama": "Konaklama",
            "ulasim":    "Nasıl Gidilir? Ulaşım",
            "deneyim":   "Bizim Deneyimimiz",
            "sss":       "Sık Sorulan Sorular",
        }
    elif lang == "en":
        lang_inst = "Write in English."
        b = {
            "giris":     "About the Destination",
            "gezilecek": "Places to Visit",
            "yemek":     "Where to Eat",
            "konaklama": "Accommodation",
            "ulasim":    "Getting There & Getting Around",
            "deneyim":   "Our Experience",
            "sss":       "Frequently Asked Questions",
        }
    else:
        lang_inst = "Schreibe auf Deutsch."
        b = {
            "giris":     "Über das Reiseziel",
            "gezilecek": "Sehenswürdigkeiten",
            "yemek":     "Restaurants & Essen",
            "konaklama": "Unterkunft",
            "ulasim":    "Anreise & Transport",
            "deneyim":   "Unsere Erfahrung",
            "sss":       "Häufig Gestellte Fragen",
        }

    site_map_block = f"\n{site_map}\n" if site_map else ""

    return f"""Sen profesyonel bir seyahat ve expat blog yazarisin. share-hub-eu.online icin yazi yaziyorsun.

GOREV: Asagidaki Hugo Markdown dosyasini bu FORMAT'a gore yeniden yaz. Cok daha uzun ve detayli olmali.
DIL: {lang_inst}
{site_map_block}
{external_links_section(lang)}
=== ZORUNLU YAZI YAPISI (bu siraya birebir uy) ===

## {b['giris']}
- Destinasyonun nerede oldugu, hangi ulkede/bolgede, nufusu
- Kisaca tarihcesi (2-3 cumle, ilginc bir detay)
- Onemli merkezlere uzakligi (km ve sure)
- Sehrin karakterini anlatan 3-4 paragraf — hava, atmosfer, insan profili
- Neden gidilmeli — ziyaretciye ilham ver, merak uyandır

## {b['gezilecek']}
- Az turistik sehir: 5-7 mekan | Cok turistik: 12-15 mekan
- Her mekan icin ### Mekan Adi baslik
- Her mekan: 2-3 paragraf — ne, nerede, neden gorulmeli
- Varsa: giris ucreti, acilis saati, en iyi ziyaret saati
- En az 2-3 mekanda kisisel gozlem ("biz gittigimizde...")
- Her mekan basligina Google Maps linki ekle

## {b['yemek']}
- 4-6 restoran veya kafe onerisi
- Her biri: isim (Google Maps linkli), tur, fiyat araligi, neden oneriliyor
- Mutlaka denenecek yerel lezzetler tablosu:
  | Yemek | Aciklama | Yaklasik Fiyat |

## {b['konaklama']}
- 3-5 konaklama secenegi (butce / orta / luks)
- Her biri: isim (Google Maps + Booking.com linkli), bolge, EUR/gece araligi, kisa aciklama
- Hangi bolgede kalmak daha iyi ve neden

## {b['ulasim']}
- Munih, Frankfurt, Istanbul gibi merkezlerden ulasim
- Tren, otobus, ucak — sure ve yaklasik fiyat tablosu
- Deutschlandticket gecerli mi?
- Sehir ici ulasim (metro, tramvay, yuruyus, bisiklet)

## {b['deneyim']}
- "Ben/biz" bakis acisindan samimi, kisisel notlar
- Neleri cok begendik, neler beklentinin altinda kaldi
- Bebek arabasi / kucuk cocukla nasil? (varsa)
- SITE ICI LINK: ilgili diger sehir/destinasyon yazilarina buradan link ver

## {b['sss']}
- En az 6 soru-cevap (her biri 2-4 cumle)
- Tipik sorular: vize, para, dil, guvenlik, en iyi donem, kac gun

=== MUTLAK KURALLAR ===
1. Front matter'i (--- ile cevrili ilk blok) HICBIR SEKILDE DEGISTIRME
2. SADECE Markdown ciktisi ver — hic aciklama, yorum veya onsouz YAZMA
3. ``` veya ```markdown bloklari KULLANMA — direkt yaz
4. Onemli kelimeleri **kalin** yap
5. H2 (##) ana bolumler, H3 (###) alt basliklar
6. Tablolar kullan — fiyat, ulasim, karsilastirma
7. Minimum 1500 kelime, ideal 2000-2500

=== MEVCUT YAZI (genislet) ===
{content}"""


def build_expat_prompt(content: str, lang: str, site_map: str) -> str:
    if lang == "tr":
        lang_inst = "Türkçe yaz."
        b = {
            "giris":    "Genel Bakış",
            "adimlar":  "Adım Adım Süreç",
            "gerekli":  "Gerekli Belgeler",
            "maliyet":  "Maliyetler ve Süreler",
            "ipuclari": "Pratik İpuçları",
            "deneyim":  "Bizim Deneyimimiz",
            "sss":      "Sık Sorulan Sorular",
        }
    elif lang == "en":
        lang_inst = "Write in English."
        b = {
            "giris":    "Overview",
            "adimlar":  "Step-by-Step Process",
            "gerekli":  "Required Documents",
            "maliyet":  "Costs & Timelines",
            "ipuclari": "Practical Tips",
            "deneyim":  "Our Experience",
            "sss":      "Frequently Asked Questions",
        }
    else:
        lang_inst = "Schreibe auf Deutsch."
        b = {
            "giris":    "Überblick",
            "adimlar":  "Schritt-für-Schritt-Anleitung",
            "gerekli":  "Erforderliche Dokumente",
            "maliyet":  "Kosten & Fristen",
            "ipuclari": "Praktische Tipps",
            "deneyim":  "Unsere Erfahrung",
            "sss":      "Häufig Gestellte Fragen",
        }

    site_map_block = f"\n{site_map}\n" if site_map else ""

    return f"""Sen Almanya'da yasayan Turkce konusan bir expat blog yazarisin. share-hub-eu.online icin yazi yaziyorsun.
Hedef kitle: Almanya'da yasayan veya tasınmayı planlayan Turk/Turk asilli okuyucular.

GOREV: Asagidaki Hugo Markdown dosyasini bu FORMAT'a gore yeniden yaz. Pratik, detayli ve deneyim odakli olmali.
DIL: {lang_inst}
{site_map_block}
=== ZORUNLU YAZI YAPISI (bu siraya birebir uy) ===

## {b['giris']}
- Konunun ne oldugu ve neden onemli oldugu (2-3 paragraf)
- Almanya'daki genel durum / resmi tablo
- Hangi durumlarda bu konu gecerli — hedef kitleyi tanimla
- Okuyucunun bu yaziyi okumasi icin motivasyon

## {b['adimlar']}
- Her adim icin ### Adim N: Baslik formati
- Her adim: nerede, nasil, ne kadar surer, dikkat edilecekler
- Resmi kurum adlari (Bürgeramt, KFZ-Zulassungsstelle vs.) — kurum adina Google Maps linki ekle
- Online mi, yuz yuze mi, randevu gerekli mi

## {b['gerekli']}
- Tam belge listesi — tablo formatinda:
  | Belge | Nereden Alinir | Aciklama |
- Tercume, apostil, onay gerektiren belgeler ayrica belirtilmeli

## {b['maliyet']}
- Resmi ucretler tablosu:
  | Islem | Ucret (EUR) | Sure |
- Gizli maliyetler (tercume, postane, fotograf vs.)
- Toplam tahmini maliyet ve sure

## {b['ipuclari']}
- En az 6 madde — gercek hayattan pratik bilgiler
- Sikca yapilan hatalar ve nasil kacinilir
- Almanca bilmeyenler icin ozel notlar
- SITE ICI LINK: ilgili diger expat yazilarina link ver

## {b['deneyim']}
- "Ben/biz" bakis acisindan samimi, kisisel notlar
- Neler beklenmedik cikti, neler kolay oldu

## {b['sss']}
- En az 7 soru-cevap (her biri 2-4 cumle)
- Tipik sorular: sure, maliyet, dil, red durumu, itiraz yollari

=== MUTLAK KURALLAR ===
1. Front matter'i (--- ile cevrili ilk blok) HICBIR SEKILDE DEGISTIRME
2. SADECE Markdown ciktisi ver — hic aciklama, yorum veya onsouz YAZMA
3. ``` veya ```markdown bloklari KULLANMA — direkt yaz
4. Onemli kelimeleri **kalin** yap
5. H2 (##) ana bolumler, H3 (###) alt basliklar
6. Tablolar kullan — belge, ucret, sure karsilastirmasi
7. Minimum 1500 kelime, ideal 2000-2500

=== MEVCUT YAZI (genislet) ===
{content}"""


# ── Yardımcı Fonksiyonlar ─────────────────────────────────────────────────────

def count_words(text: str) -> int:
    c = re.sub(r'^---.*?---', '', text, flags=re.DOTALL)
    return len(c.split())


def detect_content_type(filepath: Path) -> str:
    # Sadece klasor adi tam olarak 'expat' olanlari expat say
    for part in filepath.parts:
        if part == "expat":
            return "expat"
    return "travel"


def detect_lang(filepath: Path) -> str:
    for part in filepath.parts:
        if part in ("tr", "en", "de"):
            return part
    return "tr"


def find_content_root(filepath: Path) -> Path:
    """Dosya yolundan content/ klasorunu bul"""
    for parent in filepath.parents:
        if (parent / "content").exists():
            return parent / "content"
        if parent.name == "content":
            return parent
    return Path("content")


def extract_front_matter(content: str):
    match = re.match(r'^(---.*?---\n)', content, re.DOTALL)
    if match:
        return match.group(1), content[match.end():]
    return "", content


def call_gemini(prompt: str, api_key: str, model: str) -> str:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    return response.text.strip()


# ── Dosya İşleme ──────────────────────────────────────────────────────────────

def process_file(filepath: Path, api_keys: list, content_root: Path, force: bool = False) -> str:
    content      = filepath.read_text(encoding="utf-8")
    word_count   = count_words(content)
    lang         = detect_lang(filepath)
    content_type = detect_content_type(filepath)

    print(f"\n  {filepath.name}")
    print(f"   Dil: {lang.upper()} | Tip: {content_type} | Kelime: {word_count}")

    # Daha once islendiyse atla (backups/ klasorunde varsa)
    backup_path = filepath.parent / BACKUP_DIR / filepath.name
    if backup_path.exists() and not force:
        print(f"   Atlaniyor — daha once islendi (backup mevcut). --force ile zorla.")
        return "skipped"

    if word_count >= MIN_WORDS and not force:
        print(f"   Atlaniyor ({word_count} >= {MIN_WORDS}). --force ile zorla.")
        return "skipped"

    # Yedek al
    backup_dir = filepath.parent / BACKUP_DIR
    backup_dir.mkdir(exist_ok=True)
    backup_path = backup_dir / filepath.name
    backup_path.write_text(content, encoding="utf-8")
    print(f"   Yedek: .../{filepath.parent.name}/{BACKUP_DIR}/{filepath.name}")

    # Site haritasini olustur
    site_map = build_site_map(content_root, lang)
    print(f"   Site haritasi: {site_map.count(chr(10))} yazi bulundu")

    # Prompt sec
    if content_type == "expat":
        prompt = build_expat_prompt(content, lang, site_map)
    else:
        prompt = build_travel_prompt(content, lang, site_map)

    # Model + key dongusu
    for model in MODEL_SEQUENCE:
        for ki, api_key in enumerate(api_keys):
            key_num = ki + 1
            try:
                print(f"   [{model}] key #{key_num} deneniyor...")
                expanded = call_gemini(prompt, api_key, model)

                # Temizle
                expanded = re.sub(r'^```[a-z]*\n?', '', expanded)
                expanded = re.sub(r'\n?```$', '', expanded)

                # Front matter koru
                orig_fm, _ = extract_front_matter(content)
                new_fm, new_body = extract_front_matter(expanded)
                if orig_fm and not new_fm:
                    expanded = orig_fm + expanded
                elif orig_fm and new_fm:
                    expanded = orig_fm + new_body

                new_count = count_words(expanded)
                print(f"   OK [{model}] key #{key_num}: {word_count} -> {new_count} kelime (+{new_count - word_count})")
                filepath.write_text(expanded, encoding="utf-8")
                return "expanded"

            except Exception as e:
                err = str(e)
                if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                    print(f"   Rate limit [{model}] key #{key_num} — {DELAY_SECONDS}s bekleniyor...")
                    time.sleep(DELAY_SECONDS)
                elif "not found" in err.lower() or "404" in err or "invalid" in err.lower():
                    print(f"   Model mevcut degil: {model} — sonrakine geciliyor")
                    break
                else:
                    print(f"   HATA [{model}] key #{key_num}: {err[:120]}")
                    time.sleep(DELAY_SECONDS)

    print(f"   TUM DENEMELER BASARISIZ — orijinal dosya korundu")
    filepath.write_text(content, encoding="utf-8")
    return "error"


# ── Ana Fonksiyon ─────────────────────────────────────────────────────────────

def main():
    api_keys = load_api_keys()
    if not api_keys:
        print("\nAPI key bulunamadi!")
        print("  script/apikeys.txt icine ekle:")
        print("  GEMINI_API_KEY_1=AIza...")
        sys.exit(1)

    print(f"Modeller: {' > '.join(MODEL_SEQUENCE)}")
    print(f"Key sayisi: {len(api_keys)} | Bekleme: {DELAY_SECONDS}s")
    print(f"Yedek: {BACKUP_DIR}/ (her klasorde ayri)")

    args      = [a for a in sys.argv[1:] if not a.startswith("--")]
    force     = "--force"     in sys.argv
    recursive = "--recursive" in sys.argv

    if not args:
        print("\nKullanim:")
        print("  python3 script/expand_posts.py <dosya.md> --force")
        print("  python3 script/expand_posts.py content/tr/seyahat/ --force")
        print("  python3 script/expand_posts.py content/tr/ --recursive --force")
        sys.exit(1)

    target = Path(args[0])
    files  = []

    if target.is_file() and target.suffix == ".md":
        files = [target]
    elif target.is_dir():
        pattern = "**/*.md" if recursive else "*.md"
        files   = [f for f in target.glob(pattern)
                   if not f.name.startswith("_") and BACKUP_DIR not in f.parts]
    else:
        print(f"Gecersiz: {target}")
        sys.exit(1)

    # content_root'u ilk dosyadan veya target'tan bul
    sample = files[0] if files else target
    content_root = find_content_root(sample.resolve())
    print(f"Content root: {content_root}")
    print(f"\n{len(files)} dosya | Min: {MIN_WORDS} kelime | Force: {force}")
    print("=" * 60)

    counts = {"expanded": 0, "skipped": 0, "error": 0}
    start  = datetime.now()

    for i, filepath in enumerate(sorted(files)):
        result = process_file(filepath, api_keys, content_root=content_root, force=force)
        counts[result] += 1

        if i < len(files) - 1 and result == "expanded":
            print(f"   {DELAY_SECONDS}s bekleniyor...")
            time.sleep(DELAY_SECONDS)

    elapsed = str(datetime.now() - start).split(".")[0]
    print(f"\n{'='*60}")
    print(f"Tamamlandi — {elapsed}")
    print(f"  Genisletilen : {counts['expanded']}")
    print(f"  Atlanan      : {counts['skipped']}")
    print(f"  Hata         : {counts['error']}")
    print(f"{'='*60}")

    if counts["expanded"] > 0:
        print("\nGit push icin:")
        print("  git add -A && git commit -m 'feat: expand posts with Gemini' && git push")


if __name__ == "__main__":
    main()