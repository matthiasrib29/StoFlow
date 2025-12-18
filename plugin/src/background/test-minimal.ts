import { BackgroundLogger } from '../utils/logger';

// Test background script minimal
BackgroundLogger.debug('🟢🟢🟢 BACKGROUND SCRIPT STARTED! 🟢🟢🟢');
BackgroundLogger.debug('This is a minimal test');
BackgroundLogger.debug('If you see this, the background script works!');

// Écouter un message simple
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  BackgroundLogger.debug('📨 Message reçu:', message);
  sendResponse({ success: true, message: 'Background script fonctionne!' });
  return true;
});

BackgroundLogger.debug('✅ Listener installé, background prêt!');
