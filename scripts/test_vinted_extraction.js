// Script de test extraction Vinted v4 - Ultra Robuste
// Fonctionne quel que soit le format d'echappement

(function extractVintedData() {
  console.log('🚀 Extraction Vinted v4 (Ultra Robuste) en cours...\n');

  const result = {
    vinted_id: null,
    title: null,
    description: null,
    price: null,
    brand: null,
    brand_id: null,
    size: null,
    size_id: null,
    condition: null,
    condition_id: null,
    catalog_id: null,
    color: null,
    material: null,
    seller_id: null,
    seller_login: null,
    photos: []
  };

  // === COLLECTER ET NORMALISER LE CONTENU ===
  const scripts = document.querySelectorAll('script:not([src])');
  let raw = '';
  scripts.forEach(function(s) { raw += s.textContent || ''; });

  // Normaliser: supprimer les echappements pour avoir du JSON standard
  let normalized = raw
    .replace(/\\"/g, '"')      // \" -> "
    .replace(/\\\\/g, '\\')    // \\ -> \
    .replace(/\\n/g, '\n')     // \n -> newline
    .replace(/\\t/g, '\t');    // \t -> tab

  console.log('📄 Contenu: ' + raw.length + ' chars (raw) / ' + normalized.length + ' chars (normalized)\n');

  // === HELPER: chercher avec plusieurs patterns ===
  function findFirst(content, patterns) {
    for (let p of patterns) {
      let m = content.match(p);
      if (m) return m;
    }
    return null;
  }

  // === EXTRACTION VINTED_ID ===
  // Depuis URL
  let urlMatch = window.location.pathname.match(/items\/(\d+)/);
  if (urlMatch) {
    result.vinted_id = parseInt(urlMatch[1]);
    console.log('✅ vinted_id (URL): ' + result.vinted_id);
  }

  // === EXTRACTION TITLE ===
  let titlePatterns = [
    /"item":\{[^}]*"id":\d+,"title":"([^"]+)"/,
    /"title":"([^"]{20,}[^"]+)"/,
    /item":\{"id":\d+,"title":"([^"]+)"/,
    /"value":"([^"]+)","style":"title"/
  ];
  let titleMatch = findFirst(normalized, titlePatterns);
  if (titleMatch) {
    result.title = titleMatch[1];
    console.log('✅ title: ' + result.title.substring(0, 50) + '...');
  }

  // === EXTRACTION CATALOG_ID ===
  let catalogPatterns = [
    /"catalog_id":(\d+)/,
    /catalog_id":(\d+)/,
    /"catalog_id": (\d+)/
  ];
  let catalogMatch = findFirst(normalized, catalogPatterns);
  if (catalogMatch) {
    result.catalog_id = parseInt(catalogMatch[1]);
    console.log('✅ catalog_id: ' + result.catalog_id);
  }

  // === EXTRACTION SIZE (depuis attributs) ===
  let sizePatterns = [
    /"code":"size","data":\{[^}]*"value":"([^"]+)"[^}]*"id":(\d+)/,
    /"code":"size"[^}]*"value":"([^"]+)"[^}]*"id":(\d+)/,
    /code":"size","data":\{"title":"[^"]+","value":"([^"]+)","id":(\d+)/,
    /code":"size"[^}]*value":"([^"]+)"[^}]*id":(\d+)/
  ];
  let sizeMatch = findFirst(normalized, sizePatterns);
  if (sizeMatch) {
    result.size = sizeMatch[1];
    result.size_id = parseInt(sizeMatch[2]);
    console.log('✅ size: ' + result.size + ' (id: ' + result.size_id + ')');
  }

  // === EXTRACTION CONDITION/STATUS ===
  let statusPatterns = [
    /"code":"status","data":\{[^}]*"value":"([^"]+)"[^}]*"id":(\d+)/,
    /"code":"status"[^}]*"value":"([^"]+)"[^}]*"id":(\d+)/,
    /code":"status","data":\{"title":"[^"]+","value":"([^"]+)","id":(\d+)/,
    /code":"status"[^}]*value":"([^"]+)"[^}]*id":(\d+)/
  ];
  let statusMatch = findFirst(normalized, statusPatterns);
  if (statusMatch) {
    result.condition = statusMatch[1];
    result.condition_id = parseInt(statusMatch[2]);
    console.log('✅ condition: ' + result.condition + ' (id: ' + result.condition_id + ')');
  }

  // === EXTRACTION COLOR ===
  let colorPatterns = [
    /"code":"color","data":\{[^}]*"value":"([^"]+)"/,
    /"code":"color"[^}]*"value":"([^"]+)"/,
    /code":"color","data":\{"title":"[^"]+","value":"([^"]+)"/,
    /code":"color"[^}]*value":"([^"]+)"/
  ];
  let colorMatch = findFirst(normalized, colorPatterns);
  if (colorMatch) {
    result.color = colorMatch[1];
    console.log('✅ color: ' + result.color);
  }

  // === EXTRACTION BRAND ===
  let brandPatterns = [
    /"brand_dto":\{"id":(\d+),"title":"([^"]+)"/,
    /brand_dto":\{"id":(\d+),"title":"([^"]+)"/,
    /"brand_dto":\{[^}]*"id":(\d+)[^}]*"title":"([^"]+)"/,
    /brand_dto[^}]*id":(\d+)[^}]*title":"([^"]+)"/
  ];
  let brandMatch = findFirst(normalized, brandPatterns);
  if (brandMatch) {
    result.brand_id = parseInt(brandMatch[1]);
    result.brand = brandMatch[2];
    console.log('✅ brand: ' + result.brand + ' (id: ' + result.brand_id + ')');
  }

  // === EXTRACTION PRICE ===
  let pricePatterns = [
    /"price":\{"amount":"([\d.]+)","currency_code":"EUR"\}/,
    /"price":\{"amount":"([\d.]+)"/,
    /price":\{"amount":"([\d.]+)"/,
    /"amount":"([\d.]+)","currency_code":"EUR"/
  ];
  let priceMatch = findFirst(normalized, pricePatterns);
  if (priceMatch) {
    result.price = parseFloat(priceMatch[1]);
    console.log('✅ price: ' + result.price + ' EUR');
  }

  // === EXTRACTION SELLER ===
  let sellerPatterns = [
    /"seller_id":(\d+)[^"]*"[^"]*"[^"]*"[^"]*"login":"([^"]+)"/,
    /"seller_id":(\d+)/,
    /seller_id":(\d+)/
  ];
  let sellerMatch = findFirst(normalized, sellerPatterns);
  if (sellerMatch) {
    result.seller_id = parseInt(sellerMatch[1]);
    if (sellerMatch[2]) result.seller_login = sellerMatch[2];
    console.log('✅ seller_id: ' + result.seller_id);
  }

  // Login separement si pas trouve
  if (!result.seller_login) {
    let loginPatterns = [
      /"login":"([a-zA-Z0-9_.]+)"/,
      /login":"([a-zA-Z0-9_.]+)"/
    ];
    let loginMatch = findFirst(normalized, loginPatterns);
    if (loginMatch) {
      result.seller_login = loginMatch[1];
      console.log('✅ seller_login: ' + result.seller_login);
    }
  }

  // === EXTRACTION DESCRIPTION ===
  // La vraie description est dans: self.__next_f.push([1,"TITRE - DESCRIPTION..."])
  // Elle contient des emojis produit (✨📦🏷️) et des hashtags, PAS de HTML (\u003c)

  let bestDesc = null;

  // Methode 1: Chercher le texte qui commence par le titre du produit
  if (result.title) {
    let titleStart = result.title.substring(0, 30);
    let titleIdx = normalized.indexOf(titleStart + ' - ');
    if (titleIdx !== -1) {
      // Extraire jusqu'au prochain guillemet ou fin de push
      let endIdx = normalized.indexOf('"', titleIdx + titleStart.length + 10);
      if (endIdx !== -1 && endIdx - titleIdx < 5000) {
        let fullText = normalized.substring(titleIdx, endIdx);
        let dashIdx = fullText.indexOf(' - ');
        if (dashIdx > 0) {
          bestDesc = fullText.substring(dashIdx + 3);
        }
      }
    }
  }

  // Methode 2: Chercher dans les push RSC (fallback)
  if (!bestDesc) {
    let allPushes = normalized.matchAll(/self\.__next_f\.push\(\[1,"([^"]+)"\]\)/g);

    for (let match of allPushes) {
      let text = match[1];

      // IGNORER les textes HTML (politique de confidentialite, etc.)
      if (text.includes('\\u003c') || text.includes('<p>') || text.includes('<ol>')) {
        continue;
      }

      // Chercher des indicateurs de vraie description produit
      let hasProductEmojis = text.includes('✨') || text.includes('📦') || text.includes('🏷️')
                          || text.includes('📋') || text.includes('🔥') || text.includes('👖');
      let hasHashtags = text.includes('#');
      let hasDash = text.includes(' - ');

      if ((hasProductEmojis || hasHashtags) && text.length > 100 && text.length < 5000) {
        // Separer titre et description
        if (hasDash) {
          let dashIdx = text.indexOf(' - ');
          if (dashIdx > 20 && dashIdx < 150) {
            bestDesc = text.substring(dashIdx + 3);
            break;
          }
        }
      }
    }
  }

  if (bestDesc) {
    result.description = bestDesc;
    console.log('✅ description: ' + result.description.substring(0, 60) + '...');
  }

  // === EXTRACTION PHOTOS ===
  let photoPatterns = [
    /"full_size_url":"(https:\/\/images1\.vinted\.net\/[^"]+)"/g,
    /full_size_url":"(https:\/\/images1\.vinted\.net\/[^"]+)"/g,
    /"url":"(https:\/\/images1\.vinted\.net\/[^"]+f800[^"]+)"/g
  ];

  for (let pattern of photoPatterns) {
    let matches = normalized.matchAll(pattern);
    for (let m of matches) {
      if (!result.photos.includes(m[1])) {
        result.photos.push(m[1]);
      }
    }
    if (result.photos.length > 0) break;
  }

  if (result.photos.length > 0) {
    console.log('✅ photos: ' + result.photos.length + ' images');
  }

  // === FALLBACK: Extraction depuis texte structure ===
  // Si on n'a pas trouve size/condition/color, chercher dans le texte visible
  if (!result.size || !result.condition || !result.color) {
    // Pattern pour les lignes de details: "Taille","value":"S"
    let detailPattern = /"title":"(Taille|État|Couleur|Marque)","value":"([^"]+)"/g;
    let details = normalized.matchAll(detailPattern);

    for (let d of details) {
      let label = d[1];
      let value = d[2];

      if (label === 'Taille' && !result.size) {
        result.size = value;
        console.log('✅ size (fallback): ' + result.size);
      }
      if (label === 'État' && !result.condition) {
        result.condition = value;
        console.log('✅ condition (fallback): ' + result.condition);
      }
      if (label === 'Couleur' && !result.color) {
        result.color = value;
        console.log('✅ color (fallback): ' + result.color);
      }
      if (label === 'Marque' && !result.brand) {
        result.brand = value;
        console.log('✅ brand (fallback): ' + result.brand);
      }
    }
  }

  // === AFFICHAGE FINAL ===
  console.log('\n' + '='.repeat(60));
  console.log('📊 RESULTATS FINAUX');
  console.log('='.repeat(60));

  const fields = [
    ['vinted_id', result.vinted_id],
    ['title', result.title ? result.title.substring(0, 50) + '...' : null],
    ['description', result.description ? result.description.substring(0, 50) + '...' : null],
    ['price', result.price],
    ['brand', result.brand],
    ['brand_id', result.brand_id],
    ['size', result.size],
    ['size_id', result.size_id],
    ['condition', result.condition],
    ['condition_id', result.condition_id],
    ['catalog_id', result.catalog_id],
    ['color', result.color],
    ['seller_id', result.seller_id],
    ['seller_login', result.seller_login],
    ['photos', result.photos.length + ' images']
  ];

  let success = 0;
  let missing = [];

  fields.forEach(function(field) {
    const name = field[0];
    const value = field[1];
    const isOk = value !== null && value !== '0 images';
    const status = isOk ? '✅' : '❌';
    console.log(status + ' ' + name.padEnd(15) + ': ' + value);
    if (isOk) success++;
    else missing.push(name);
  });

  console.log('\n' + '='.repeat(60));
  console.log('📈 Score: ' + success + '/15 champs extraits');
  if (missing.length > 0) {
    console.log('⚠️ Manquants: ' + missing.join(', '));
  } else {
    console.log('🎉 EXTRACTION COMPLETE !');
  }
  console.log('='.repeat(60));

  // Debug
  window.vintedExtracted = result;
  window.vintedRaw = raw;
  window.vintedNormalized = normalized;

  console.log('\n💡 Debug: window.vintedExtracted, window.vintedNormalized');

  return result;
})();
