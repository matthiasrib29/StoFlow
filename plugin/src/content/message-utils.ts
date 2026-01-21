/**
 * Message Utilities for Content Scripts
 *
 * Provides helper functions for communicating with injected scripts
 * via postMessage pattern used throughout the plugin.
 */

import { VintedLogger } from '../utils/logger';
import { ENV } from '../config/environment';

/**
 * Response from the injected script
 */
interface PostMessageResponse {
  success: boolean;
  data?: any;
  error?: string;
  status?: number;
  statusText?: string;
}

/**
 * Options for postMessage request
 */
interface PostMessageRequestOptions {
  /** Message type to send */
  messageType: string;
  /** Response message type to listen for */
  responseType: string;
  /** Message payload (excluding type and requestId) */
  payload?: Record<string, any>;
  /** Timeout in milliseconds (default: ENV.VINTED_REQUEST_TIMEOUT) */
  timeout?: number;
  /** Context for logging */
  logContext?: string;
}

/**
 * Send a postMessage request to the injected script and wait for response.
 *
 * This helper encapsulates the common pattern of:
 * 1. Generating a unique requestId
 * 2. Setting up a response listener
 * 3. Setting up a timeout
 * 4. Sending the message
 * 5. Cleaning up after response or timeout
 *
 * @param options - Request options
 * @returns Promise that resolves with the response
 */
export function sendPostMessageRequest(options: PostMessageRequestOptions): Promise<PostMessageResponse> {
  const {
    messageType,
    responseType,
    payload = {},
    timeout = ENV.VINTED_REQUEST_TIMEOUT,
    logContext = ''
  } = options;

  return new Promise((resolve) => {
    const requestId = `${messageType.toLowerCase()}_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    let responseSent = false;

    const responseListener = (event: MessageEvent) => {
      if (event.source !== window) return;
      if (responseSent) return;

      const msg = event.data;

      if (msg.type === responseType && msg.requestId === requestId) {
        responseSent = true;
        window.removeEventListener('message', responseListener);
        clearTimeout(timeoutId);

        if (logContext) {
          VintedLogger.debug(`${logContext} Response received:`, msg.success ? 'success' : 'failed');
        }

        resolve({
          success: msg.success,
          data: msg.data,
          error: msg.error,
          status: msg.status,
          statusText: msg.statusText
        });
      }
    };

    window.addEventListener('message', responseListener);

    const timeoutId = setTimeout(() => {
      if (responseSent) return;
      responseSent = true;
      window.removeEventListener('message', responseListener);

      if (logContext) {
        VintedLogger.warn(`${logContext} Timeout (${timeout / 1000}s)`);
      }

      resolve({
        success: false,
        error: `Request timeout (${timeout / 1000}s)`,
        status: 408
      });
    }, timeout);

    // Send message to injected script (same origin for security)
    window.postMessage({
      type: messageType,
      requestId,
      ...payload
    }, window.location.origin);

    if (logContext) {
      VintedLogger.debug(`${logContext} Message sent to injected script`);
    }
  });
}
