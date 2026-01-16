"""
Email service using Brevo (ex-Sendinblue) API.
Handles transactional emails: verification, password reset, notifications.
"""
import logging
from typing import Optional

import httpx

from shared.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending transactional emails via Brevo API."""

    BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

    @classmethod
    def _get_headers(cls) -> dict:
        """Get Brevo API headers."""
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": settings.brevo_api_key,
        }

    @classmethod
    async def send_email(
        cls,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email via Brevo API.

        Args:
            to_email: Recipient email address.
            to_name: Recipient name.
            subject: Email subject.
            html_content: HTML body content.
            text_content: Plain text body (optional).

        Returns:
            True if email was sent successfully, False otherwise.
        """
        if not settings.brevo_enabled:
            logger.warning("Brevo not configured, email not sent to %s", to_email)
            return False

        payload = {
            "sender": {
                "name": settings.brevo_sender_name,
                "email": settings.brevo_sender_email,
            },
            "to": [{"email": to_email, "name": to_name}],
            "subject": subject,
            "htmlContent": html_content,
        }

        if text_content:
            payload["textContent"] = text_content

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    cls.BREVO_API_URL,
                    headers=cls._get_headers(),
                    json=payload,
                )

            if response.status_code in (200, 201):
                logger.info("Email sent successfully to %s", to_email)
                return True
            else:
                logger.error(
                    "Failed to send email to %s: %s - %s",
                    to_email,
                    response.status_code,
                    response.text,
                )
                return False

        except httpx.RequestError as e:
            logger.error("Network error sending email to %s: %s", to_email, str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error sending email to %s: %s", to_email, str(e))
            return False

    @classmethod
    async def send_verification_email(
        cls,
        to_email: str,
        to_name: str,
        verification_token: str,
    ) -> bool:
        """
        Send email verification link to new user.

        Args:
            to_email: User's email address.
            to_name: User's full name.
            verification_token: Token for email verification.

        Returns:
            True if email was sent successfully.
        """
        verification_url = (
            f"{settings.frontend_url}/auth/verify-email?token={verification_token}"
        )

        subject = "Confirmez votre adresse email - StoFlow"

        html_content = cls._get_verification_email_html(to_name, verification_url)
        text_content = cls._get_verification_email_text(to_name, verification_url)

        return await cls.send_email(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

    @classmethod
    def _get_verification_email_html(cls, name: str, verification_url: str) -> str:
        """Generate HTML content for verification email."""
        return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Confirmez votre email</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f5;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f4f4f5;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 20px 40px;">
                            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #18181b;">
                                StoFlow
                            </h1>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <h2 style="margin: 0 0 20px 0; font-size: 22px; font-weight: 600; color: #18181b;">
                                Bienvenue {name} !
                            </h2>
                            <p style="margin: 0 0 20px 0; font-size: 16px; line-height: 24px; color: #52525b;">
                                Merci de vous être inscrit sur StoFlow. Pour activer votre compte et commencer à gérer vos ventes multi-plateformes, veuillez confirmer votre adresse email.
                            </p>
                        </td>
                    </tr>

                    <!-- Button -->
                    <tr>
                        <td align="center" style="padding: 10px 40px 30px 40px;">
                            <a href="{verification_url}"
                               style="display: inline-block; padding: 16px 32px; font-size: 16px; font-weight: 600; color: #ffffff; background-color: #2563eb; text-decoration: none; border-radius: 8px;">
                                Confirmer mon email
                            </a>
                        </td>
                    </tr>

                    <!-- Alternative link -->
                    <tr>
                        <td style="padding: 0 40px 30px 40px;">
                            <p style="margin: 0; font-size: 14px; line-height: 20px; color: #71717a;">
                                Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :
                            </p>
                            <p style="margin: 10px 0 0 0; font-size: 14px; line-height: 20px; color: #2563eb; word-break: break-all;">
                                {verification_url}
                            </p>
                        </td>
                    </tr>

                    <!-- Expiration notice -->
                    <tr>
                        <td style="padding: 0 40px 30px 40px;">
                            <p style="margin: 0; padding: 16px; font-size: 14px; line-height: 20px; color: #71717a; background-color: #fafafa; border-radius: 8px;">
                                Ce lien expire dans <strong>24 heures</strong>. Si vous n'avez pas créé de compte StoFlow, vous pouvez ignorer cet email.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; border-top: 1px solid #e4e4e7;">
                            <p style="margin: 0; font-size: 12px; line-height: 18px; color: #a1a1aa; text-align: center;">
                                StoFlow - Gestion multi-plateformes pour e-commerce<br>
                                Cet email a été envoyé à {name}
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    @classmethod
    def _get_verification_email_text(cls, name: str, verification_url: str) -> str:
        """Generate plain text content for verification email."""
        return f"""
Bienvenue sur StoFlow, {name} !

Merci de vous être inscrit. Pour activer votre compte, veuillez confirmer votre adresse email en cliquant sur le lien ci-dessous :

{verification_url}

Ce lien expire dans 24 heures.

Si vous n'avez pas créé de compte StoFlow, vous pouvez ignorer cet email.

---
StoFlow - Gestion multi-plateformes pour e-commerce
"""

    @classmethod
    async def send_beta_confirmation_email(
        cls,
        to_email: str,
        to_name: str,
        vendor_type: str,
        monthly_volume: str,
    ) -> bool:
        """
        Send beta signup confirmation email.

        Args:
            to_email: User's email address.
            to_name: User's full name.
            vendor_type: Type of vendor (particulier/professionnel).
            monthly_volume: Monthly sales volume.

        Returns:
            True if email was sent successfully.
        """
        subject = "🚀 Bienvenue dans la beta StoFlow !"

        html_content = cls._get_beta_confirmation_email_html(
            to_name, vendor_type, monthly_volume
        )
        text_content = cls._get_beta_confirmation_email_text(
            to_name, vendor_type, monthly_volume
        )

        return await cls.send_email(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

    @classmethod
    def _get_beta_confirmation_email_html(
        cls, name: str, vendor_type: str, monthly_volume: str
    ) -> str:
        """Generate HTML content for beta confirmation email (minimal version)."""
        return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bienvenue dans la beta StoFlow</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f5f5f5;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden;">

                    <!-- Header simple -->
                    <tr>
                        <td style="padding: 40px 40px 0 40px;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #1a1a1a;">
                                StoFlow
                            </h1>
                        </td>
                    </tr>

                    <!-- Message principal -->
                    <tr>
                        <td style="padding: 32px 40px;">
                            <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 24px; color: #1a1a1a;">
                                Bonjour {name},
                            </p>
                            <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 24px; color: #52525b;">
                                Merci de votre inscription à la beta StoFlow.
                            </p>
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #52525b;">
                                Vous recevrez un email de notre part le <strong>14 février 2026</strong> avec vos identifiants de connexion.
                            </p>

                            <!-- Avantages - liste simple -->
                            <p style="margin: 0 0 8px 0; font-size: 14px; font-weight: 500; color: #1a1a1a;">
                                En tant que beta-testeur :
                            </p>
                            <ul style="margin: 0 0 24px 0; padding-left: 20px; color: #52525b; font-size: 14px; line-height: 22px;">
                                <li style="margin-bottom: 4px;">1 mois gratuit</li>
                                <li style="margin-bottom: 4px;">-50% à vie sous condition de feedback régulier</li>
                                <li style="margin-bottom: 4px;">Support prioritaire</li>
                            </ul>

                            <p style="margin: 0; font-size: 14px; line-height: 22px; color: #71717a;">
                                À bientôt,<br>
                                L'équipe StoFlow
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px; background-color: #fafafa; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0; font-size: 12px; line-height: 18px; color: #71717a; text-align: center;">
                                Des questions ? Répondez à cet email.
                            </p>
                            <p style="margin: 0; font-size: 12px; line-height: 18px; color: #a1a1aa; text-align: center;">
                                <strong style="color: #facc15;">STOFLOW</strong> • Publiez sur Vinted & eBay en 10 secondes<br>
                                © 2026 StoFlow. Tous droits réservés.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    @classmethod
    def _get_beta_confirmation_email_text(
        cls, name: str, vendor_type: str, monthly_volume: str
    ) -> str:
        """Generate plain text content for beta confirmation email."""
        return f"""
STOFLOW - Confirmation inscription beta

Bonjour {name},

Merci de votre inscription à la beta StoFlow.

Vous recevrez un email de notre part le 14 février 2026 avec vos identifiants de connexion.

En tant que beta-testeur :
- 1 mois gratuit
- -50% à vie sous condition de feedback régulier
- Support prioritaire

À bientôt,
L'équipe StoFlow

---

Des questions ? Répondez à cet email.

STOFLOW • Publiez sur Vinted & eBay en 10 secondes
© 2026 StoFlow. Tous droits réservés.
"""
