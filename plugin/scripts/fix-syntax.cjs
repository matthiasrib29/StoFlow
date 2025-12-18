#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

let fixCount = 0;

function fixFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  const original = content;

  // Fix 1: );. → ).
  content = content.replace(/\);\.([a-zA-Z])/g, ').$1');

  // Fix 2: Imports doublés (import.*import {)
  content = content.replace(/import\s+{([^}]+)}import\s+{([^}]+)}/g, 'import { $2 }');

  // Fix 3: );); → ))
  content = content.replace(/\);\)/g, '))');

  // Fix 4: image(s); → image(s)
  content = content.replace(/image\(s\);/g, 'image(s)');

  if (content !== original) {
    fs.writeFileSync(filePath, content, 'utf8');
    fixCount++;
    console.log(`✅ Fixed: ${filePath}`);
  }
}

function fixDirectory(dir) {
  const files = fs.readdirSync(dir);

  files.forEach(file => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      if (!['node_modules', 'dist', '.git'].includes(file)) {
        fixDirectory(fullPath);
      }
    } else if (file.endsWith('.ts') && !file.endsWith('.test.ts') && !file.endsWith('.d.ts')) {
      fixFile(fullPath);
    }
  });
}

console.log('🔧 Correction des erreurs de syntaxe...\n');

fixDirectory('./src');

console.log(`\n✅ ${fixCount} fichiers corrigés`);
