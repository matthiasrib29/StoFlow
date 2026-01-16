"""
Email preview routes - For development/testing email templates.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from services.email_service import EmailService

router = APIRouter(prefix="/preview", tags=["preview"])


@router.get("/beta-confirmation", response_class=HTMLResponse)
async def preview_beta_confirmation_email(
    name: str = "Jean Dupont",
    vendor_type: str = "professionnel",
    monthly_volume: str = "10-50"
):
    """
    Preview beta confirmation email template.

    Args:
        name: User's name for preview
        vendor_type: Type of vendor (particulier/professionnel)
        monthly_volume: Monthly volume range

    Returns:
        HTML email template
    """
    html_content = EmailService._get_beta_confirmation_email_html(
        name=name,
        vendor_type=vendor_type,
        monthly_volume=monthly_volume
    )

    return HTMLResponse(content=html_content)
