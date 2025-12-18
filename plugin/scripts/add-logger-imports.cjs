#!/usr/bin/env node

/**
 * Script pour ajouter les imports Logger aux fichiers migrés
 */

const fs = require('fs');
const path = require('path');

let addCount = 0;

function detectContext(filePath) {
  if (filePath.includes('/background/task-poller')) return 'TaskPollerLogger';
  if (filePath.includes('/background/')) return 'BackgroundLogger';
  if (filePath.includes('/content/vinted')) return 'VintedLogger';
  if (filePath.includes('/content/proxy')) return 'ProxyLogger';
  if (filePath.includes('/content/')) return 'ContentLogger';
  if (filePath.includes('/popup/')) return 'PopupLogger';
  if (filePath.includes('/composables/useAuth')) return 'AuthLogger';
  if (filePath.includes('/api/')) return 'APILogger';
  return 'Logger';
}

function getRelativePath(filePath) {
  const depth = filePath.split('/').length - 2; // -2 for src/ and filename
  return '../'.repeat(depth) + 'utils/logger';
}

function addLoggerImport(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  const context = detectContext(filePath);

  // Vérifier si le fichier utilise le logger
  if (!content.includes(`${context}.`)) {
    return; // Pas besoin d'import
  }

  // Vérifier si l'import existe déjà
  if (content.includes(`import { ${context} }`)) {
    return; // Déjà importé
  }

  const relativePath = getRelativePath(filePath);

  // Trouver où insérer l'import
  const lines = content.split('\n');
  let insertIndex = 0;

  // Chercher la dernière ligne d'import
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim().startsWith('import ')) {
      insertIndex = i + 1;
    }
  }

  // Insérer l'import
  lines.splice(insertIndex, 0, `import { ${context} } from '${relativePath}';`);

  content = lines.join('\n');
  fs.writeFileSync(filePath, content, 'utf8');
  addCount++;
  console.log(`✅ Added import to: ${filePath} (${context})`);
}

function processDirectory(dir) {
  const files = fs.readdirSync(dir);

  files.forEach(file => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      if (!['node_modules', 'dist', '.git', 'tests'].includes(file)) {
        processDirectory(fullPath);
      }
    } else if (file.endsWith('.ts') && !file.endsWith('.test.ts') && !file.endsWith('.d.ts')) {
      addLoggerImport(fullPath);
    }
  });
}

console.log('🔧 Ajout des imports Logger\n');

const startTime = Date.now();
processDirectory('./src');
const duration = Date.now() - startTime;

console.log(`\n✅ ${addCount} imports ajoutés en ${duration}ms`);
console.log('\n📝 Prochaine étape: npm run build');
