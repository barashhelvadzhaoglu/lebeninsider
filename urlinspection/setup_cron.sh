#!/bin/bash
# =============================================================================
# Mac Cron Kurulum Scripti
# Google Indexing API'yi her gece 23:00'de çalıştırır
# Çalıştırma: bash setup_cron.sh
# =============================================================================

SCRIPT_PATH="$HOME/Documents/sharehub/urlinspection/indexing_api.py"
VENV_PYTHON="$HOME/Documents/sharehub/.venv/bin/python3"
LOG_PATH="$HOME/Documents/sharehub/urlinspection/cron_output.log"

echo "🔧 Cron job kurulumu başlıyor..."
echo ""

# Python ve venv kontrol
if [ ! -f "$VENV_PYTHON" ]; then
    echo "⚠️  venv bulunamadı: $VENV_PYTHON"
    echo "   Sistem Python kullanılacak."
    PYTHON_PATH=$(which python3)
else
    PYTHON_PATH="$VENV_PYTHON"
fi

echo "🐍 Python: $PYTHON_PATH"
echo "📄 Script: $SCRIPT_PATH"
echo "📝 Log: $LOG_PATH"
echo ""

# Gerekli paketleri kur
echo "📦 Gerekli paketler kuruluyor..."
$PYTHON_PATH -m pip install google-auth google-auth-httplib2 requests --quiet
echo "✅ Paketler kuruldu"
echo ""

# Mevcut cron'ları göster
echo "📋 Mevcut cron jobs:"
crontab -l 2>/dev/null || echo "  (boş)"
echo ""

# Yeni cron job — her gece 23:00
CRON_JOB="0 23 * * * $PYTHON_PATH $SCRIPT_PATH >> $LOG_PATH 2>&1"

# Mevcut cron'lara ekle (indexing_api varsa güncelle, yoksa ekle)
(crontab -l 2>/dev/null | grep -v "indexing_api.py"; echo "$CRON_JOB") | crontab -

echo "✅ Cron job eklendi: Her gece 23:00"
echo ""
echo "📋 Güncel cron jobs:"
crontab -l
echo ""
echo "🎉 Kurulum tamamlandı!"
echo ""
echo "Manuel test için:"
echo "  $PYTHON_PATH $SCRIPT_PATH"
echo ""
echo "Log takibi için:"
echo "  tail -f $LOG_PATH"
