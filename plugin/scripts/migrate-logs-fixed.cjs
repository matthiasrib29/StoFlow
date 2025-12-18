#!/usr/bin/env node

/**
 * Script de Migration console.log → Logger (VERSION CORRIGÉE)
 *
 * Ce script migre SEULEMENT les console.log/error/warn
 * Il ne touche PAS aux imports, qui doivent être ajoutés manuellement
 */

const fs = require('fs');
const path = require('path');

const STATS = {
  filesScanned: 0,
  filesModified: 0,
  consoleLogs: 0,
  consoleErrors: 0,
  consoleWarns: 0,
};

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

function migrateConsoleLogs(content, context) {
  let modified = content;

  // Pattern 1: console.log(...)
  modified = modified.replace(/console\.log\(([^)]*)\)/g, (match, args) => {
    STATS.consoleLogs++;
    return `${context}.debug(${args})`;
  });

  return modified;
}

function migrateConsoleErrors(content, context) {
  let modified = content;

  modified = modified.replace(/console\.error\(([^)]*)\)/g, (match, args) => {
    STATS.consoleErrors++;
    return `${context}.error(${args})`;
  });

  return modified;
}

function migrateConsoleWarns(content, context) {
  let modified = content;

  modified = modified.replace(/console\.warn\(([^)]*)\)/g, (match, args) => {
    STATS.consoleWarns++;
    return `${context}.warn(${args})`;
  });

  return modified;
}

function migrateFile(filePath) {
  STATS.filesScanned++;

  let content = fs.readFileSync(filePath, 'utf8');
  const originalContent = content;

  const context = detectContext(filePath);

  // Migrer les logs
  content = migrateConsoleLogs(content, context);
  content = migrateConsoleErrors(content, context);
  content = migrateConsoleWarns(content, context);

  if (content !== originalContent) {
    STATS.filesModified++;
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`✅ Migrated: ${filePath} (${context})`);
  }
}

function migrateDirectory(dir) {
  const files = fs.readdirSync(dir);

  files.forEach(file => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      if (!['node_modules', 'dist', '.git', 'tests'].includes(file)) {
        migrateDirectory(fullPath);
      }
    } else if (file.endsWith('.ts') && !file.endsWith('.test.ts') && !file.endsWith('.d.ts')) {
      migrateFile(fullPath);
    }
  });
}

function main() {
  console.log('🔧 Migration console.log → Logger (STEP 1/2)\n');

  const startTime = Date.now();
  migrateDirectory('./src');
  const duration = Date.now() - startTime;

  console.log('\n' + '='.repeat(60));
  console.log('📊 RÉSUMÉ MIGRATION');
  console.log('='.repeat(60));
  console.log(`Fichiers scannés      : ${STATS.filesScanned}`);
  console.log(`Fichiers modifiés     : ${STATS.filesModified}`);
  console.log(`console.log migrés    : ${STATS.consoleLogs}`);
  console.log(`console.error migrés  : ${STATS.consoleErrors}`);
  console.log(`console.warn migrés   : ${STATS.consoleWarns}`);
  console.log(`Durée                 : ${duration}ms`);
  console.log('='.repeat(60));

  console.log('\n✅ Migration terminée !');
  console.log('\n📝 STEP 2/2 - Ajouter les imports manuellement');
  console.log('   Utilisez: node scripts/add-logger-imports.cjs');
}

try {
  main();
} catch (error) {
  console.error('❌ Erreur:', error.message);
  process.exit(1);
}
