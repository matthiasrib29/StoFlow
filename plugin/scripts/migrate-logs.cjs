#!/usr/bin/env node

/**
 * Script de Migration console.log → Logger
 *
 * Usage:
 *   node scripts/migrate-logs.js [--dry-run] [--file=path/to/file.ts]
 *
 * Options:
 *   --dry-run    : Affiche les changements sans les appliquer
 *   --file=PATH  : Migrer un seul fichier au lieu de tout src/
 *
 * Exemples:
 *   node scripts/migrate-logs.js --dry-run
 *   node scripts/migrate-logs.js --file=src/background/index.ts
 *   node scripts/migrate-logs.js
 */

const fs = require('fs');
const path = require('path');

// Configuration
const DRY_RUN = process.argv.includes('--dry-run');
const SINGLE_FILE = process.argv.find(arg => arg.startsWith('--file='))?.split('=')[1];

const STATS = {
  filesScanned: 0,
  filesModified: 0,
  consoleLogs: 0,
  consoleErrors: 0,
  consoleWarns: 0,
  separators: 0
};

/**
 * Détecte le contexte de logging depuis le chemin du fichier
 */
function detectContext(filePath) {
  if (filePath.includes('/background/')) return 'BackgroundLogger';
  if (filePath.includes('/content/vinted')) return 'VintedLogger';
  if (filePath.includes('/content/proxy')) return 'ProxyLogger';
  if (filePath.includes('/content/')) return 'ContentLogger';
  if (filePath.includes('/popup/')) return 'PopupLogger';
  if (filePath.includes('/composables/useAuth')) return 'AuthLogger';
  if (filePath.includes('/background/task-poller')) return 'TaskPollerLogger';
  if (filePath.includes('/api/')) return 'APILogger';
  return 'Logger';
}

/**
 * Ajoute l'import du Logger si nécessaire
 */
function addLoggerImport(content, context) {
  // Si import déjà présent, ne rien faire
  if (content.includes(`import { ${context} }`)) {
    return content;
  }

  // Trouver la position après les imports existants
  const importMatch = content.match(/^(import .*\n)+/m);

  if (importMatch) {
    // Ajouter après les imports existants
    const lastImportPos = importMatch[0].length;
    return (
      content.slice(0, lastImportPos) +
      `import { ${context} } from '../utils/logger';\n` +
      content.slice(lastImportPos)
    );
  } else {
    // Ajouter au début du fichier
    return `import { ${context} } from '../utils/logger';\n\n` + content;
  }
}

/**
 * Migre console.log → Logger.debug
 */
function migrateConsoleLogs(content, context) {
  let modified = content;

  // Compter occurrences avant
  const logsBefore = (content.match(/console\.log/g) || []).length;

  // Pattern 1: console.log simple
  modified = modified.replace(
    /console\.log\((.*?)\);?/g,
    (match, args) => {
      STATS.consoleLogs++;
      return `${context}.debug(${args});`;
    }
  );

  // Pattern 2: console.log multi-lignes (rares)
  modified = modified.replace(
    /console\.log\(\s*`([^`]+)`\s*\);?/g,
    (match, message) => {
      STATS.consoleLogs++;
      return `${context}.debug(\`${message}\`);`;
    }
  );

  return modified;
}

/**
 * Migre console.error → Logger.error
 */
function migrateConsoleErrors(content, context) {
  let modified = content;

  modified = modified.replace(
    /console\.error\((.*?)\);?/g,
    (match, args) => {
      STATS.consoleErrors++;
      return `${context}.error(${args});`;
    }
  );

  return modified;
}

/**
 * Migre console.warn → Logger.warn
 */
function migrateConsoleWarns(content, context) {
  let modified = content;

  modified = modified.replace(
    /console\.warn\((.*?)\);?/g,
    (match, args) => {
      STATS.consoleWarns++;
      return `${context}.warn(${args});`;
    }
  );

  return modified;
}

/**
 * Supprime les séparateurs ASCII inutiles
 */
function removeSeparators(content) {
  let modified = content;

  // Pattern 1: console.log('========...')
  const pattern1 = /console\.(log|debug)\(['"](={10,}|─{10,})['"]\);?\n?/g;
  const matches1 = content.match(pattern1) || [];
  STATS.separators += matches1.length;
  modified = modified.replace(pattern1, '');

  // Pattern 2: console.log('\n========...')
  const pattern2 = /console\.(log|debug)\(['"]\\n(={10,}|─{10,})['"]\);?\n?/g;
  const matches2 = content.match(pattern2) || [];
  STATS.separators += matches2.length;
  modified = modified.replace(pattern2, '');

  // Pattern 3: console.log('========...\n')
  const pattern3 = /console\.(log|debug)\(['"](={10,}|─{10,})\\n['"]\);?\n?/g;
  const matches3 = content.match(pattern3) || [];
  STATS.separators += matches3.length;
  modified = modified.replace(pattern3, '');

  return modified;
}

/**
 * Migre un fichier
 */
function migrateFile(filePath) {
  STATS.filesScanned++;

  let content = fs.readFileSync(filePath, 'utf8');
  const originalContent = content;

  const context = detectContext(filePath);

  // Ajouter import Logger
  content = addLoggerImport(content, context);

  // Migrer les logs
  content = migrateConsoleLogs(content, context);
  content = migrateConsoleErrors(content, context);
  content = migrateConsoleWarns(content, context);

  // Supprimer séparateurs
  content = removeSeparators(content);

  // Vérifier si le fichier a changé
  if (content !== originalContent) {
    STATS.filesModified++;

    if (DRY_RUN) {
      console.log(`\n📝 ${filePath}`);
      console.log(`   → Import ajouté: ${context}`);
      console.log(`   → console.log remplacés: ${(originalContent.match(/console\.log/g) || []).length}`);
    } else {
      fs.writeFileSync(filePath, content, 'utf8');
      console.log(`✅ Migrated: ${filePath}`);
    }
  }
}

/**
 * Parcourt tous les fichiers .ts d'un répertoire
 */
function migrateDirectory(dir) {
  const files = fs.readdirSync(dir);

  files.forEach(file => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      // Ignorer node_modules, dist, etc.
      if (!['node_modules', 'dist', '.git', 'tests'].includes(file)) {
        migrateDirectory(fullPath);
      }
    } else if (file.endsWith('.ts') && !file.endsWith('.test.ts') && !file.endsWith('.d.ts')) {
      migrateFile(fullPath);
    }
  });
}

/**
 * Main
 */
function main() {
  console.log('🔧 Migration console.log → Logger\n');

  if (DRY_RUN) {
    console.log('⚠️  Mode DRY-RUN (aucun fichier ne sera modifié)\n');
  }

  const startTime = Date.now();

  if (SINGLE_FILE) {
    console.log(`📁 Migration fichier: ${SINGLE_FILE}\n`);
    migrateFile(SINGLE_FILE);
  } else {
    console.log('📁 Migration répertoire: ./src\n');
    migrateDirectory('./src');
  }

  const duration = Date.now() - startTime;

  console.log('\n' + '='.repeat(60));
  console.log('📊 RÉSUMÉ');
  console.log('='.repeat(60));
  console.log(`Fichiers scannés      : ${STATS.filesScanned}`);
  console.log(`Fichiers modifiés     : ${STATS.filesModified}`);
  console.log(`console.log migrés    : ${STATS.consoleLogs}`);
  console.log(`console.error migrés  : ${STATS.consoleErrors}`);
  console.log(`console.warn migrés   : ${STATS.consoleWarns}`);
  console.log(`Séparateurs supprimés : ${STATS.separators}`);
  console.log(`Durée                 : ${duration}ms`);
  console.log('='.repeat(60));

  if (DRY_RUN) {
    console.log('\n💡 Pour appliquer les changements, exécutez sans --dry-run');
  } else {
    console.log('\n✅ Migration terminée avec succès!');
    console.log('\n📝 Prochaines étapes:');
    console.log('   1. Vérifier les changements: git diff');
    console.log('   2. Compiler: npm run build');
    console.log('   3. Tester: npm run test');
    console.log('   4. Commit: git commit -m "refactor: migrate console.log to Logger"');
  }
}

// Exécuter
try {
  main();
} catch (error) {
  console.error('❌ Erreur:', error.message);
  process.exit(1);
}
