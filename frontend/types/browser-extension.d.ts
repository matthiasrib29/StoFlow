/**
 * Browser Extension API Type Declarations
 * For Chrome/Firefox extension communication from web pages
 */

declare namespace chrome {
  namespace runtime {
    function sendMessage(
      extensionId: string,
      message: any,
      responseCallback?: (response: any) => void
    ): Promise<any>
  }
}

declare const browser: {
  runtime?: {
    sendMessage: (
      extensionId: string,
      message: any,
      responseCallback?: (response: any) => void
    ) => Promise<any>
  }
}

// Extend Window interface for extension detection
declare global {
  interface Window {
    chrome?: typeof chrome
    browser?: typeof browser
  }
}

export {}
