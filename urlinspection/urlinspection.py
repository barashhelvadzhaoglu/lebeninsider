import time
import requests
import random
import os
import xml.etree.ElementTree as ET
from DrissionPage import ChromiumPage, ChromiumOptions

def google_index_otomasyon():
    # 1. Aşama: Linkleri Topla ve Karıştır
    print("Sitemapler analiz ediliyor...")
    sitemap_main = "https://share-hub-eu.online/sitemap.xml"
    content_urls = []
    try:
        r = requests.get(sitemap_main)
        root = ET.fromstring(r.content)
        sub_sitemaps = [loc.text for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        for sub_url in sub_sitemaps:
            sub_r = requests.get(sub_url)
            sub_root = ET.fromstring(sub_r.content)
            urls = [loc.text for loc in sub_root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
            content_urls.extend([u for u in urls if "/tags/" not in u and "/categories/" not in u and u != "https://share-hub-eu.online/"])
        
        random.shuffle(content_urls)
        print(f"Toplam {len(content_urls)} adet içerik karıştırıldı.")
    except Exception as e:
        print(f"Sitemap hatası: {e}")
        return

    # 2. Aşama: Tarayıcı Ayarları
    co = ChromiumOptions()
    page = ChromiumPage(co)
    page.get('https://search.google.com/search-console?resource_id=sc-domain:share-hub-eu.online')
    print("Oturum kontrol ediliyor...")
    time.sleep(10)

    # 3. Aşama: Akıllı Kontrol ve Indexleme Döngüsü
    for url in content_urls:
        try:
            print(f"\n--- İşleniyor: {url} ---")
            
            # URL'i arat
            search_input = page.ele('tag:input@@placeholder^Inspect any URL')
            if not search_input: search_input = page.ele('@type=text')
            search_input.clear()
            search_input.input(url + '\n')
            
            # Google'ın ilk veritabanı sorgusu için kısa bir süre (5-8 sn) bekle
            print("Google veritabanı sorgulanıyor (İlk kontrol)...")
            time.sleep(8)
            
            # DURUM KONTROLÜ: Sayfa zaten dizinde mi?
            # JS ile sayfa içeriğinde "URL is on Google" metnini arıyoruz
            check_status_js = """
            (function() {
                if (document.body.innerText.includes('URL is on Google')) return "INDEXED";
                if (document.body.innerText.includes('URL is not on Google') || document.body.innerText.includes('URL is unknown')) return "NOT_INDEXED";
                if (document.body.innerText.includes('Quota exceeded')) return "LIMIT";
                return "RETRIEVING";
            })()
            """
            
            status = page.run_js(check_status_js)
            
            if status == "INDEXED":
                print(f">>> ATLANIYOR: {url} zaten Google dizininde. Teste gerek yok.")
                continue # Bir sonraki rastgele linke geç
            
            elif status == "LIMIT":
                print("!!! KOTA HATASI: Bugünlük limit dolmuş. Script durduruluyor.")
                break

            # EĞER DİZİNDE DEĞİLSE İŞLEMLERE BAŞLA
            print(">>> Sayfa dizinde değil. Test aşamasına geçiliyor (20 sn)...")
            time.sleep(20) # Test ekranı için istediğin süre
            
            # Request Indexing butonuna basmayı dene
            js_click = """
            (function() {
                const buttons = Array.from(document.querySelectorAll('div[role="button"]'));
                const target = buttons.find(b => b.innerText.includes('REQUEST INDEXING'));
                if (target && !target.disabled) {
                    target.click();
                    return "CLICKED";
                }
                return "NOT_FOUND";
            })()
            """
            
            if page.run_js(js_click) == "CLICKED":
                print(">>> TALEP GÖNDERİLDİ: Onay için 20 saniye bekleniyor...")
                time.sleep(20) # Onay penceresi için istediğin süre
                
                # Onay (Got it) butonuna bas
                page.run_js("const btn = Array.from(document.querySelectorAll('span, div')).find(s => s.innerText.includes('Got it') || s.innerText.includes('GOT IT')); if(btn) btn.click();")
                print(">>> ONAYLANDI: Link kaydedildi.")
            else:
                print(">>> UYARI: Buton aktifleşmedi veya limit takıldı.")

            # Linkler arası rastgele mola
            time.sleep(random.randint(5, 10))

        except Exception as e:
            print(f"Hata: {e}")
            continue

if __name__ == "__main__":
    google_index_otomasyon()