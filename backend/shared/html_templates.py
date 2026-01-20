"""
HTML Templates

Reusable HTML templates for OAuth callbacks and other redirect pages.
"""

import json


def build_oauth_success_html(result: dict, platform: str = "eBay") -> str:
    """
    Build HTML page for successful OAuth.

    Args:
        result: OAuth result dict to pass to parent window
        platform: Platform name for display (eBay, Etsy, etc.)

    Returns:
        HTML string
    """
    result_json = json.dumps(result)
    platform_lower = platform.lower()
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>{platform} Connected</title></head>
    <body>
        <h2>Connexion {platform} reussie !</h2>
        <p>Vous pouvez fermer cette fenetre.</p>
        <script>
            if (window.opener) {{
                window.opener.postMessage({{
                    type: '{platform_lower}_oauth_success',
                    data: {result_json}
                }}, '*');
                setTimeout(() => window.close(), 1000);
            }} else {{
                setTimeout(() => window.location.href = '/dashboard/platforms/{platform_lower}', 2000);
            }}
        </script>
    </body>
    </html>
    """


def build_oauth_error_html(error_message: str, platform: str = "eBay") -> str:
    """
    Build HTML page for OAuth error.

    Args:
        error_message: Error message to display
        platform: Platform name for display (eBay, Etsy, etc.)

    Returns:
        HTML string
    """
    platform_lower = platform.lower()
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>{platform} Connection Error</title></head>
    <body>
        <h2>Erreur de connexion {platform}</h2>
        <p>{error_message}</p>
        <p>Vous pouvez fermer cette fenetre et reessayer.</p>
        <script>
            if (window.opener) {{
                window.opener.postMessage({{
                    type: '{platform_lower}_oauth_error',
                    error: '{error_message}'
                }}, '*');
                setTimeout(() => window.close(), 3000);
            }}
        </script>
    </body>
    </html>
    """
