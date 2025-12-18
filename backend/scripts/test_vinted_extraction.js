// ============================================================
// STOFLOW - Script de test d'extraction Vinted
// Lancer dans la console sur une page produit Vinted
// Usage: Copier-coller dans la console F12 sur une page produit
// ============================================================

(function() {
    const html = document.documentElement.innerHTML;
    const results = {
        meta: {},
        json: {},
        details: {},
        description_parsed: {},
        raw_samples: {}
    };

    console.log("🔍 STOFLOW - Analyse de la page Vinted...\n");

    // ===== 1. META TAGS =====
    console.log("📋 1. META TAGS:");

    const metaDesc = document.querySelector('meta[name="description"]');
    results.meta.description = metaDesc ? metaDesc.content : null;
    console.log("  description:", results.meta.description ? results.meta.description.substring(0, 100) + "..." : "null");

    const ogTitle = document.querySelector('meta[property="og:title"]');
    results.meta.title = ogTitle ? ogTitle.content : null;
    console.log("  og:title:", results.meta.title);

    const ogUrl = document.querySelector('meta[property="og:url"]');
    results.meta.url = ogUrl ? ogUrl.content : null;
    const idMatch = results.meta.url ? results.meta.url.match(/items\/(\d+)-/) : null;
    results.meta.vinted_id = idMatch ? idMatch[1] : null;
    console.log("  vinted_id:", results.meta.vinted_id);

    // ===== 2. JSON PATTERNS =====
    console.log("\n📦 2. JSON PATTERNS:");

    // Strategy 1: "code":"X"..."data":{..."value":"Y"}
    const codeDataPattern = /"code"\s*:\s*"([^"]+)"[^}]*"data"\s*:\s*\{([^}]+)\}/g;
    let match;
    const codeDataMatches = [];
    while ((match = codeDataPattern.exec(html)) !== null) {
        const code = match[1];
        const dataContent = match[2];
        const valueMatch = dataContent.match(/"value"\s*:\s*"([^"]*)"/);
        if (valueMatch) {
            codeDataMatches.push({ code: code, value: valueMatch[1] });
        }
    }
    results.json.code_data = codeDataMatches;
    console.log("  Strategy 1 (code/data):", codeDataMatches.length > 0 ? codeDataMatches : "AUCUN");

    // Strategy 2: Direct patterns
    const sizePattern = /"size"\s*:\s*\{\s*"id"\s*:\s*(\d+)\s*,\s*"title"\s*:\s*"([^"]+)"/;
    const sizeMatch = html.match(sizePattern);
    results.json.size = sizeMatch ? { id: sizeMatch[1], title: sizeMatch[2] } : null;
    console.log("  size:", results.json.size);

    const statusPattern = /"status"\s*:\s*\{\s*"id"\s*:\s*(\d+)\s*,\s*"title"\s*:\s*"([^"]+)"/;
    const statusMatch = html.match(statusPattern);
    results.json.condition = statusMatch ? { id: statusMatch[1], title: statusMatch[2] } : null;
    console.log("  condition:", results.json.condition);

    const colorPattern = /"color1"\s*:\s*\{[^}]*"title"\s*:\s*"([^"]+)"/;
    const colorMatch = html.match(colorPattern);
    results.json.color = colorMatch ? colorMatch[1] : null;
    if (!results.json.color) {
        const colorSimple = html.match(/"color"\s*:\s*"([^"]+)"/);
        results.json.color = colorSimple ? colorSimple[1] : null;
    }
    console.log("  color:", results.json.color);

    const materialPattern = /"material"\s*:\s*\{[^}]*"title"\s*:\s*"([^"]+)"/;
    const materialMatch = html.match(materialPattern);
    results.json.material = materialMatch ? materialMatch[1] : null;
    if (!results.json.material) {
        const materialSimple = html.match(/"material"\s*:\s*"([^"]+)"/);
        results.json.material = materialSimple ? materialSimple[1] : null;
    }
    console.log("  material:", results.json.material);

    const brandPattern = /"brand_dto"\s*:\s*\{\s*"id"\s*:\s*(\d+)\s*,\s*"title"\s*:\s*"([^"]+)"/;
    const brandMatch = html.match(brandPattern);
    results.json.brand = brandMatch ? { id: brandMatch[1], title: brandMatch[2] } : null;
    console.log("  brand:", results.json.brand);

    const pricePattern = /"price"\s*:\s*\{\s*"amount"\s*:\s*"([^"]+)"/;
    const priceMatch = html.match(pricePattern);
    results.json.price = priceMatch ? priceMatch[1] : null;
    console.log("  price:", results.json.price);

    // ===== 3. DETAILS ARRAY =====
    console.log("\n📝 3. DETAILS ARRAY:");
    const detailsPattern = /"details"\s*:\s*\[(.*?)\]/s;
    const detailsMatch = html.match(detailsPattern);
    if (detailsMatch) {
        const detailItems = detailsMatch[1].matchAll(/\{"title"\s*:\s*"([^"]+)"[^}]*"value"\s*:\s*"([^"]+)"/g);
        for (const item of detailItems) {
            results.details[item[1]] = item[2];
        }
    }
    console.log("  Found:", Object.keys(results.details).length > 0 ? results.details : "AUCUN");

    // ===== 4. DESCRIPTION PARSING =====
    console.log("\n📄 4. DESCRIPTION PARSING:");

    const descPattern = /"description":\s*\{\s*"section_title"[^}]*"description":\s*"([^"]*)"/;
    let fullDesc = html.match(descPattern);
    fullDesc = fullDesc ? fullDesc[1] : '';
    if (!fullDesc) {
        const altDesc = html.match(/"description"\s*:\s*"([^"]{10,})"/);
        fullDesc = altDesc ? altDesc[1] : (results.meta.description || '');
    }
    fullDesc = fullDesc.replace(/\\n/g, '\n').replace(/\\r/g, '');

    console.log("  Description brute (100 chars):", fullDesc.substring(0, 100));

    const patterns = {
        material: [
            /(?:🧵|matière|matiere|composition|tissu)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])/i,
            /(?:fabric|material)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])/i,
            /en\s+(coton|lin|laine|soie|polyester|denim|cuir|velours|cachemire)/i
        ],
        color: [
            /(?:🎨|couleur|color)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])/i,
            /(?:coloris|teinte)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])/i
        ],
        size: [
            /(?:📏|taille|size)\s*(?:estimée|estimate)?\s*[:\-=]\s*(.+?)(?:\n|$|[,;])/i,
            /taille\s+([A-Z]{1,3}|\d{2,3}(?:\/\d{2,3})?|W\d+(?:\/L\d+)?)/i
        ],
        condition: [
            /(?:✨|état|etat|condition)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])/i,
            /(neuf|très bon état|bon état|satisfaisant)/i
        ],
        brand: [
            /(?:👔|🏷️|marque|brand)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])/i
        ]
    };

    for (const attr in patterns) {
        const patternList = patterns[attr];
        for (let i = 0; i < patternList.length; i++) {
            const pattern = patternList[i];
            const match = fullDesc.match(pattern);
            if (match) {
                results.description_parsed[attr] = match[1].trim();
                break;
            }
        }
    }
    console.log("  Parsed from description:", Object.keys(results.description_parsed).length > 0 ? results.description_parsed : "AUCUN");

    // ===== 5. RAW SAMPLES =====
    console.log("\n🔬 5. RAW SAMPLES (pour debug):");

    const allCodes = [];
    const codeRegex = /"code"\s*:\s*"([^"]+)"/g;
    let codeMatch;
    while ((codeMatch = codeRegex.exec(html)) !== null) {
        allCodes.push(codeMatch[1]);
    }
    const uniqueCodes = allCodes.filter(function(v, i, a) { return a.indexOf(v) === i; }).slice(0, 20);
    results.raw_samples.all_codes = uniqueCodes;
    console.log("  Tous les 'code' trouves:", uniqueCodes);

    const nextFPushes = html.match(/self\.__next_f\.push/g);
    results.raw_samples.next_f_count = nextFPushes ? nextFPushes.length : 0;
    console.log("  __next_f.push count:", results.raw_samples.next_f_count);

    // ===== RESUME =====
    console.log("\n" + "============================================================");
    console.log("📊 RESUME FINAL:");
    console.log("============================================================");

    const summary = {
        vinted_id: results.meta.vinted_id,
        title: results.meta.title,
        price: results.json.price,
        brand: (results.json.brand ? results.json.brand.title : null) || results.description_parsed.brand || null,
        size: (results.json.size ? results.json.size.title : null) || results.details['Taille'] || results.description_parsed.size || null,
        color: results.json.color || results.details['Couleur'] || results.description_parsed.color || null,
        material: results.json.material || results.details['Matiere'] || results.description_parsed.material || null,
        condition: (results.json.condition ? results.json.condition.title : null) || results.details['Etat'] || results.description_parsed.condition || null,
        description: fullDesc ? 'OUI (' + fullDesc.length + ' chars)' : 'NON'
    };

    console.table(summary);

    console.log("\n💾 Resultats complets dans: window.stoflowExtraction");
    window.stoflowExtraction = results;

    return summary;
})();
