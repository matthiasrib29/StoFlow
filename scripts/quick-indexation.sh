#!/bin/bash
# Script d'accélération de l'indexation Stoflow

echo "🚀 Accélération de l'indexation Stoflow..."
echo ""

# Ping Google
echo "📍 Ping Google..."
curl -s "https://www.google.com/ping?sitemap=https://stoflow.io/sitemap.xml"
echo ""

# Ping Bing
echo "📍 Ping Bing..."
curl -s "https://www.bing.com/ping?sitemap=https://stoflow.io/sitemap.xml"
echo ""
echo ""

# Vérifications techniques
echo "🔍 Vérifications techniques :"
echo ""

echo "1️⃣ Site accessible :"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://stoflow.io)
if [ "$HTTP_CODE" = "200" ]; then
  echo "   ✅ OK (HTTP $HTTP_CODE)"
else
  echo "   ⚠️  HTTP $HTTP_CODE"
fi
echo ""

echo "2️⃣ robots.txt accessible :"
ROBOTS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://stoflow.io/robots.txt)
if [ "$ROBOTS_CODE" = "200" ]; then
  echo "   ✅ OK (HTTP $ROBOTS_CODE)"
else
  echo "   ⚠️  HTTP $ROBOTS_CODE"
fi
echo ""

echo "3️⃣ sitemap.xml accessible :"
SITEMAP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://stoflow.io/sitemap.xml)
if [ "$SITEMAP_CODE" = "200" ]; then
  echo "   ✅ OK (HTTP $SITEMAP_CODE)"
else
  echo "   ⚠️  HTTP $SITEMAP_CODE"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Pings envoyés avec succès !"
echo ""
echo "📊 Prochaines étapes :"
echo "   1. Configure Google Search Console (URGENT)"
echo "   2. Vérifie dans 24-48h avec : site:stoflow.io"
echo "   3. Partage sur LinkedIn/Twitter"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
