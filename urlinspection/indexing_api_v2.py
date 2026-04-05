#!/usr/bin/env python3
"""
Google Akıllı Indexleme Scripti v2
- URL Inspection API ile önce kontrol eder
- Sadece indexlenmemiş URL'leri gönderir
- 3 site için: share-hub-eu.online, barashhelvadzhaoglu.com, memorlex.com
- Mac'te cron ile her gece otomatik çalışır

Kurulum:
  pip install google-auth google-auth-httplib2 requests

Çalıştırma:
  python3 indexing_api_v2.py
"""

import json
import os
import sys
import time
import random
import datetime
import subprocess
import xml.etree.ElementTree as ET
import requests
from pathlib import Path

try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request as GoogleRequest
except ImportError:
    print("❌ Eksik paket. Çalıştır: pip install google-auth google-auth-httplib2")
    sys.exit(1)

# =============================================================================
# iMESSAGE BİLDİRİM
# =============================================================================

IMESSAGE_TARGET = "baris.helvacioglu@outlook.com"

def send_imessage(message: str):
    """Mac iMessage ile bildirim gönder."""
    subprocess.run(["open", "-a", "Messages"], check=False)
    time.sleep(2)
    script = f'''tell application "Messages"
      set targetService to 1st service whose service type = iMessage
      set targetBuddy to buddy "{IMESSAGE_TARGET}" of targetService
      send "{message}" to targetBuddy
    end tell'''
    try:
        subprocess.run(["osascript", "-e", script], check=True)
        print(f"📱 iMessage gönderildi → {IMESSAGE_TARGET}")
    except Exception as e:
        print(f"⚠️  iMessage gönderilemedi: {e}")

# =============================================================================
# AYARLAR
# =============================================================================

SERVICE_ACCOUNT_FILE = os.path.expanduser(
    "~/Documents/sharehub/urlinspection/sharehub-service-account.json"
)

LOG_FILE = os.path.expanduser(
    "~/Documents/sharehub/urlinspection/indexing_log_v2.json"
)

# Günlük limitler
INSPECTION_LIMIT = 1800   # URL Inspection API: 2000/gün, güvenli 1800
SUBMIT_LIMIT = 180        # Indexing API: 200/gün, güvenli 180

# Siteler
SITES = [
    {
        "name": "Share Hub EU",
        "domain": "share-hub-eu.online",
        "sitemap": "https://share-hub-eu.online/sitemap.xml",
        "priority": 1,
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

EXCLUDE_PATTERNS = ["/tags/", "/categories/", "/page/", "?", "#"]

# =============================================================================
# LOG SİSTEMİ
# =============================================================================

def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return {
        "urls": {},           # url -> {status, last_checked, last_submitted}
        "daily": {},          # tarih -> {inspected, submitted}
        "last_run": None
    }

def save_log(log):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

def today():
    return datetime.date.today().isoformat()

def get_counts(log):
    d = log.get("daily", {}).get(today(), {})
    return d.get("inspected", 0), d.get("submitted", 0)

def inc_inspected(log):
    log.setdefault("daily", {}).setdefault(today(), {"inspected": 0, "submitted": 0})
    log["daily"][today()]["inspected"] += 1

def inc_submitted(log):
    log.setdefault("daily", {}).setdefault(today(), {"inspected": 0, "submitted": 0})
    log["daily"][today()]["submitted"] += 1

def needs_recheck(log, url):
    """URL'in yeniden kontrol edilmesi gerekiyor mu?"""
    if url not in log.get("urls", {}):
        return True
    entry = log["urls"][url]
    status = entry.get("status")
    last_checked = entry.get("last_checked")
    
    if status == "indexed":
        # İndexlenmişse 7 günde bir kontrol et
        if last_checked:
            days_ago = (datetime.date.today() - datetime.date.fromisoformat(last_checked[:10])).days
            return days_ago >= 7
        return True
    elif status == "submitted":
        # Gönderilmişse 2 günde bir kontrol et (indexlendi mi?)
        if last_checked:
            days_ago = (datetime.date.today() - datetime.date.fromisoformat(last_checked[:10])).days
            return days_ago >= 2
        return True
    elif status == "not_indexed":
        # İndexlenmemişse her gün kontrol et
        return True
    
    return True

# =============================================================================
# SİTEMAP
# =============================================================================

def fetch_urls(sitemap_url):
    all_urls = []
    try:
        r = requests.get(sitemap_url, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        
        subs = root.findall(f".//{ns}sitemap/{ns}loc")
        if subs:
            for s in subs:
                all_urls.extend(fetch_urls(s.text))
        else:
            for u in root.findall(f".//{ns}url/{ns}loc"):
                url = u.text.strip()
                if not any(p in url for p in EXCLUDE_PATTERNS):
                    all_urls.append(url)
    except Exception as e:
        print(f"  ⚠️  Sitemap hatası: {e}")
    return all_urls

# =============================================================================
# GOOGLE API
# =============================================================================

def get_credentials():
    scopes = [
        "https://www.googleapis.com/auth/indexing",
        "https://www.googleapis.com/auth/webmasters.readonly",
    ]
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=scopes
    )
    creds.refresh(GoogleRequest())
    return creds

def inspect_url(url, site_url, creds):
    """
    URL Inspection API ile URL'in indexlenip indexlenmediğini kontrol et.
    Returns: "INDEXED", "NOT_INDEXED", "ERROR"
    """
    endpoint = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {creds.token}",
    }
    payload = {
        "inspectionUrl": url,
        "siteUrl": f"sc-domain:{site_url}",
        "languageCode": "en-US",
    }
    
    try:
        r = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            result = data.get("inspectionResult", {})
            index_result = result.get("indexStatusResult", {})
            coverage_state = index_result.get("coverageState", "")
            
            if "Submitted and indexed" in coverage_state or coverage_state == "Indexed, not submitted in sitemap":
                return "INDEXED", coverage_state
            elif "Crawled" in coverage_state or "Discovered" in coverage_state:
                return "NOT_INDEXED", coverage_state
            elif "Submitted" in coverage_state:
                return "SUBMITTED", coverage_state
            else:
                return "NOT_INDEXED", coverage_state
                
        elif r.status_code == 429:
            return "RATE_LIMIT", ""
        elif r.status_code == 403:
            return "FORBIDDEN", ""
        else:
            return "ERROR", f"HTTP {r.status_code}"
            
    except Exception as e:
        return "ERROR", str(e)

def submit_url(url, creds):
    """Indexing API ile URL gönder."""
    endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {creds.token}",
    }
    payload = {"url": url, "type": "URL_UPDATED"}
    
    try:
        r = requests.post(endpoint, headers=headers, json=payload, timeout=10)
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"error": str(e)}

# =============================================================================
# ANA FONKSİYON
# =============================================================================

def main():
    print("=" * 60)
    print("🧠 Google Akıllı Indexleme v2 - Önce Kontrol, Sonra Gönder")
    print(f"📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"❌ Service account bulunamadı: {SERVICE_ACCOUNT_FILE}")
        sys.exit(1)
    
    log = load_log()
    inspected_today, submitted_today = get_counts(log)
    
    print(f"📊 Bugün: {inspected_today}/{INSPECTION_LIMIT} kontrol, {submitted_today}/{SUBMIT_LIMIT} gönderim")
    
    if submitted_today >= SUBMIT_LIMIT and inspected_today >= INSPECTION_LIMIT:
        print("⚠️  Tüm limitler dolmuş. Yarın tekrar.")
        sys.exit(0)
    
    # Credentials al
    print("\n🔑 Kimlik doğrulanıyor...")
    try:
        creds = get_credentials()
        print("✅ Kimlik doğrulandı")
    except Exception as e:
        print(f"❌ Hata: {e}")
        sys.exit(1)
    
    total_indexed = 0
    total_submitted = 0
    total_skipped = 0
    total_errors = 0
    
    for site in sorted(SITES, key=lambda x: x["priority"]):
        
        rem_inspect = INSPECTION_LIMIT - inspected_today
        rem_submit = SUBMIT_LIMIT - submitted_today
        
        if rem_inspect <= 0 and rem_submit <= 0:
            print(f"\n⚠️  Limitler doldu.")
            break
        
        print(f"\n{'='*40}")
        print(f"🌐 {site['name']} ({site['domain']})")
        print(f"{'='*40}")
        
        urls = fetch_urls(site["sitemap"])
        if not urls:
            print("  ⚠️  URL bulunamadı")
            continue
        
        print(f"  📋 Toplam URL: {len(urls)}")
        
        # Kontrol gerekenleri filtrele
        to_check = [u for u in urls if needs_recheck(log, u)]
        print(f"  🔍 Kontrol edilecek: {len(to_check)}")
        
        random.shuffle(to_check)
        
        for url in to_check:
            rem_inspect = INSPECTION_LIMIT - inspected_today
            rem_submit = SUBMIT_LIMIT - submitted_today
            
            if rem_inspect <= 0:
                print(f"  ⚠️  Inspection limiti doldu")
                break
            
            # Token yenile (her 50 istekte)
            if inspected_today % 50 == 0 and inspected_today > 0:
                try:
                    creds.refresh(GoogleRequest())
                except:
                    pass
            
            # 1. Önce kontrol et
            status, detail = inspect_url(url, site["domain"], creds)
            inc_inspected(log)
            inspected_today += 1
            
            # Log'a kaydet
            log.setdefault("urls", {})[url] = {
                "status": status.lower(),
                "detail": detail,
                "last_checked": datetime.datetime.now().isoformat(),
                "site": site["domain"],
            }
            
            if status == "INDEXED":
                print(f"  ✅ İndexli: {url.split('/')[-2] or url.split('/')[-1]}/")
                total_indexed += 1
                
            elif status in ("NOT_INDEXED", "SUBMITTED"):
                if rem_submit <= 0:
                    print(f"  ⚠️  Submit limiti doldu, {url} atlandı")
                    total_skipped += 1
                    continue
                
                # 2. İndexlenmemişse gönder
                code, resp = submit_url(url, creds)
                
                if code == 200:
                    print(f"  🚀 Gönderildi: {url}")
                    log["urls"][url]["status"] = "submitted"
                    log["urls"][url]["last_submitted"] = datetime.datetime.now().isoformat()
                    inc_submitted(log)
                    submitted_today += 1
                    total_submitted += 1
                elif code == 429:
                    print(f"  ⏳ Rate limit, 60sn bekleniyor...")
                    time.sleep(60)
                    break
                elif code == 403:
                    print(f"  ❌ Yetki hatası: {url}")
                    total_errors += 1
                    break
                else:
                    print(f"  ⚠️  Hata ({code}): {url}")
                    total_errors += 1
                    
            elif status == "RATE_LIMIT":
                print(f"  ⏳ API rate limit, 30sn bekleniyor...")
                time.sleep(30)
                break
                
            elif status == "FORBIDDEN":
                print(f"  ❌ 403 Yetki hatası - Search Console owner kontrolü gerekli")
                break
                
            else:
                print(f"  ⚠️  Hata ({status}): {url}")
                total_errors += 1
            
            # İstekler arası bekleme
            time.sleep(random.uniform(0.5, 1.5))
        
        # Log kaydet (her site sonrası)
        save_log(log)
        print(f"\n  📈 Bu siteden: kontrol edildi, {total_submitted} gönderildi")
    
    # Final log
    log["last_run"] = datetime.datetime.now().isoformat()
    save_log(log)
    
    inspected_today, submitted_today = get_counts(log)

    # Özet
    print(f"\n{'='*60}")
    print(f"📊 ÖZET")
    print(f"{'='*60}")
    print(f"✅ Zaten indexli:  {total_indexed}")
    print(f"🚀 Gönderilen:     {total_submitted}")
    print(f"⏭️  Atlanan:        {total_skipped}")
    print(f"❌ Hata:           {total_errors}")
    print(f"🔍 Bugün kontrol:  {inspected_today}/{INSPECTION_LIMIT}")
    print(f"📤 Bugün gönderim: {submitted_today}/{SUBMIT_LIMIT}")
    print(f"{'='*60}")

    # Site bazlı rapor
    site_reports = []
    for site in SITES:
        domain = site["domain"]
        site_urls = [u for u, d in log.get("urls", {}).items() if d.get("site") == domain]
        indexed = sum(1 for u in site_urls if log["urls"][u].get("status") == "indexed")
        submitted = sum(1 for u in site_urls if log["urls"][u].get("status") == "submitted")
        site_reports.append(f"• {site['name']}: {indexed} indexli, {submitted} gönderildi")

    # iMessage raporu
    report = (
        f"📊 İndexleme Raporu — {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        f"{'—'*30}\n"
        + "\n".join(site_reports) +
        f"\n{'—'*30}\n"
        f"✅ Zaten indexli: {total_indexed}\n"
        f"🚀 Gönderilen: {total_submitted}\n"
        f"❌ Hata: {total_errors}\n"
        f"🔍 Kontrol: {inspected_today}/{INSPECTION_LIMIT}\n"
        f"📤 Gönderim: {submitted_today}/{SUBMIT_LIMIT}"
    )
    send_imessage(report)

if __name__ == "__main__":
    main()