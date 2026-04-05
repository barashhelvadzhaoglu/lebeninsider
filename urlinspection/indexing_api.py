#!/usr/bin/env python3
"""
Google Indexing API - Otomatik URL Submit Scripti
3 site için: share-hub-eu.online, barashhelvadzhaoglu.com, memorlex.com
Mac'te cron ile her gece otomatik çalışır.

Kurulum:
  pip install google-auth google-auth-httplib2 requests

Çalıştırma:
  python3 indexing_api.py
"""

import json
import os
import sys
import time
import random
import datetime
import xml.etree.ElementTree as ET
import requests
from pathlib import Path

# Google Auth
try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request as GoogleRequest
except ImportError:
    print("❌ Eksik paket. Çalıştır: pip install google-auth google-auth-httplib2")
    sys.exit(1)

# =============================================================================
# AYARLAR
# =============================================================================

# Service account JSON dosyasının yolu
SERVICE_ACCOUNT_FILE = os.path.expanduser(
    "~/Documents/sharehub/urlinspection/sharehub-service-account.json"
)

# Log dosyası
LOG_FILE = os.path.expanduser(
    "~/Documents/sharehub/urlinspection/indexing_log.json"
)

# Günlük limit (Google'ın limiti 200, güvenli kalmak için 180)
DAILY_LIMIT = 180

# Siteler ve sitemapleri
SITES = [
    {
        "name": "Share Hub EU",
        "domain": "share-hub-eu.online",
        "sitemap": "https://share-hub-eu.online/sitemap.xml",
        "priority": 1,  # En yüksek öncelik
    },
    {
        "name": "Barash Helvadzhaoglu",
        "domain": "barashhelvadzhaoglu.com",
        "sitemap": "https://barashhelvadzhaoglu.com/sitemap.xml",
        "priority": 2,
    },
    {
        "name": "Memorlex",
        "domain": "memorlex.com",
        "sitemap": "https://memorlex.com/sitemap.xml",
        "priority": 3,
    },
]

# Hariç tutulacak URL kalıpları
EXCLUDE_PATTERNS = [
    "/tags/",
    "/categories/",
    "/page/",
    "?",
    "#",
]

# =============================================================================
# LOG SİSTEMİ
# =============================================================================

def load_log():
    """Daha önce indexlenen URL'leri yükle."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return {"indexed_urls": {}, "daily_counts": {}, "last_run": None}

def save_log(log_data):
    """Log dosyasını kaydet."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

def get_today():
    return datetime.date.today().isoformat()

def get_daily_count(log_data):
    today = get_today()
    return log_data.get("daily_counts", {}).get(today, 0)

def increment_daily_count(log_data):
    today = get_today()
    if "daily_counts" not in log_data:
        log_data["daily_counts"] = {}
    log_data["daily_counts"][today] = log_data["daily_counts"].get(today, 0) + 1

# =============================================================================
# SİTEMAP OKUMA
# =============================================================================

def fetch_urls_from_sitemap(sitemap_url, exclude_patterns=None):
    """Sitemap'ten tüm URL'leri çek, alt sitemapları da dahil et."""
    if exclude_patterns is None:
        exclude_patterns = []
    
    all_urls = []
    
    try:
        print(f"  📄 Sitemap okunuyor: {sitemap_url}")
        response = requests.get(sitemap_url, timeout=15)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        
        # Sitemap index mi yoksa URL listesi mi?
        sub_sitemaps = root.findall(f".//{ns}sitemap/{ns}loc")
        
        if sub_sitemaps:
            # Sitemap index — alt sitemapları oku
            for sub in sub_sitemaps:
                sub_urls = fetch_urls_from_sitemap(sub.text, exclude_patterns)
                all_urls.extend(sub_urls)
        else:
            # Direkt URL listesi
            for url_elem in root.findall(f".//{ns}url/{ns}loc"):
                url = url_elem.text.strip()
                
                # Hariç tutulanları atla
                if any(pattern in url for pattern in exclude_patterns):
                    continue
                
                all_urls.append(url)
    
    except requests.RequestException as e:
        print(f"  ⚠️  Sitemap hatası ({sitemap_url}): {e}")
    except ET.ParseError as e:
        print(f"  ⚠️  XML parse hatası: {e}")
    
    return all_urls

# =============================================================================
# GOOGLE INDEXING API
# =============================================================================

def get_access_token():
    """Service account ile access token al."""
    scopes = ["https://www.googleapis.com/auth/indexing"]
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=scopes
    )
    credentials.refresh(GoogleRequest())
    return credentials.token

def submit_url(url, access_token):
    """Tek bir URL'i Google Indexing API'ye gönder."""
    endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = {
        "url": url,
        "type": "URL_UPDATED",
    }
    
    response = requests.post(endpoint, headers=headers, json=payload, timeout=10)
    return response.status_code, response.json()

def check_url_status(url, access_token):
    """URL'in indexleme durumunu kontrol et."""
    endpoint = f"https://indexing.googleapis.com/v3/urlNotifications/metadata?url={requests.utils.quote(url, safe='')}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(endpoint, headers=headers, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None

# =============================================================================
# ANA FONKSİYON
# =============================================================================

def main():
    print("=" * 60)
    print("🚀 Google Indexing API - Otomatik Submit")
    print(f"📅 Tarih: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # Service account dosyası var mı?
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"❌ Service account dosyası bulunamadı: {SERVICE_ACCOUNT_FILE}")
        sys.exit(1)
    
    # Log yükle
    log_data = load_log()
    
    # Günlük limit kontrolü
    daily_count = get_daily_count(log_data)
    if daily_count >= DAILY_LIMIT:
        print(f"⚠️  Günlük limit dolmuş ({daily_count}/{DAILY_LIMIT}). Yarın tekrar çalışacak.")
        sys.exit(0)
    
    remaining = DAILY_LIMIT - daily_count
    print(f"📊 Bugün kalan limit: {remaining}/{DAILY_LIMIT}")
    
    # Access token al
    print("\n🔑 Google ile kimlik doğrulanıyor...")
    try:
        access_token = get_access_token()
        print("✅ Kimlik doğrulandı")
    except Exception as e:
        print(f"❌ Kimlik doğrulama hatası: {e}")
        sys.exit(1)
    
    # Her site için işlem yap
    total_submitted = 0
    total_skipped = 0
    total_errors = 0
    
    for site in sorted(SITES, key=lambda x: x["priority"]):
        if total_submitted >= remaining:
            print(f"\n⚠️  Günlük limit doldu. Kalan siteler yarına bırakıldı.")
            break
        
        print(f"\n{'='*40}")
        print(f"🌐 Site: {site['name']} ({site['domain']})")
        print(f"{'='*40}")
        
        # URL'leri çek
        urls = fetch_urls_from_sitemap(site["sitemap"], EXCLUDE_PATTERNS)
        
        if not urls:
            print(f"  ⚠️  URL bulunamadı: {site['sitemap']}")
            continue
        
        print(f"  📋 Toplam URL: {len(urls)}")
        
        # Daha önce indexlenmeyenleri filtrele
        new_urls = []
        for url in urls:
            if url not in log_data.get("indexed_urls", {}):
                new_urls.append(url)
        
        print(f"  🆕 Yeni/Güncelleme gereken: {len(new_urls)}")
        
        if not new_urls:
            print(f"  ✅ Tüm URL'ler zaten gönderilmiş.")
            continue
        
        # Rastgele karıştır
        random.shuffle(new_urls)
        
        # Submit et
        site_submitted = 0
        for url in new_urls:
            if total_submitted >= remaining:
                break
            
            try:
                status_code, response = submit_url(url, access_token)
                
                if status_code == 200:
                    print(f"  ✅ Gönderildi: {url}")
                    log_data.setdefault("indexed_urls", {})[url] = {
                        "submitted_at": datetime.datetime.now().isoformat(),
                        "site": site["domain"],
                        "status": "submitted"
                    }
                    increment_daily_count(log_data)
                    total_submitted += 1
                    site_submitted += 1
                    
                elif status_code == 429:
                    print(f"  ⚠️  Rate limit! Bekleniyor...")
                    time.sleep(60)
                    total_errors += 1
                    break
                    
                elif status_code == 403:
                    print(f"  ❌ Yetki hatası: {url}")
                    print(f"     Search Console'da bu site için owner yetkisi var mı?")
                    total_errors += 1
                    break
                    
                else:
                    print(f"  ⚠️  Hata ({status_code}): {url} → {response}")
                    total_errors += 1
                
                # İstekler arası bekleme (spam gibi görünmesin)
                time.sleep(random.uniform(1.5, 3.0))
                
            except Exception as e:
                print(f"  ❌ İstek hatası: {url} → {e}")
                total_errors += 1
                time.sleep(5)
        
        print(f"\n  📈 Bu siteden gönderilen: {site_submitted}")
    
    # Log kaydet
    log_data["last_run"] = datetime.datetime.now().isoformat()
    save_log(log_data)
    
    # Özet
    print(f"\n{'='*60}")
    print(f"📊 ÖZET")
    print(f"{'='*60}")
    print(f"✅ Gönderilen URL:  {total_submitted}")
    print(f"⏭️  Atlanan URL:    {total_skipped}")
    print(f"❌ Hata:           {total_errors}")
    print(f"📅 Bugün toplam:   {get_daily_count(log_data)}/{DAILY_LIMIT}")
    print(f"{'='*60}")
    
    if total_submitted > 0:
        print(f"\n🎉 {total_submitted} URL Google'a bildirildi!")
        print(f"⏳ Indexleme genellikle 24-72 saat içinde tamamlanır.")

if __name__ == "__main__":
    main()
