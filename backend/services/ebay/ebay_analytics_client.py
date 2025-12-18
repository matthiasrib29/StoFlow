"""
eBay Analytics API Client.

Client pour récupérer les métriques de performance des listings.

Permet de suivre:
- Trafic (impressions, vues, clics)
- Taux de conversion
- Ventes
- Performance par marketplace

Endpoints implémentés:
- GET /sell/analytics/v1/traffic_report - Rapport de trafic

Documentation officielle:
https://developer.ebay.com/api-docs/sell/analytics/overview.html

Author: Claude
Date: 2025-12-10
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from services.ebay.ebay_base_client import EbayBaseClient


class EbayAnalyticsClient(EbayBaseClient):
    """
    Client eBay Analytics API.

    Usage:
        >>> from datetime import datetime, timedelta, timezone
        >>>
        >>> client = EbayAnalyticsClient(db_session, user_id=1, marketplace_id="EBAY_FR")
        >>>
        >>> # Rapport trafic des 30 derniers jours
        >>> now = datetime.now(timezone.utc)
        >>> start = now - timedelta(days=30)
        >>> report = client.get_traffic_report(start_date=start, end_date=now)
        >>>
        >>> print(f"Impressions: {report['totalImpressions']}")
        >>> print(f"Clics: {report['totalClicks']}")
        >>> print(f"Taux de clic: {report['clickThroughRate']}%")
    """

    def get_traffic_report(
        self,
        start_date: datetime,
        end_date: datetime,
        dimension: str = "LISTING",
        metric: str = "CLICK_THROUGH_RATE",
        listing_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Récupère un rapport de trafic pour les listings.

        Args:
            start_date: Date début (datetime UTC)
            end_date: Date fin (datetime UTC)
            dimension: Dimension du rapport
                - "LISTING": Par listing
                - "DAY": Par jour
            metric: Métrique principale
                - "CLICK_THROUGH_RATE": Taux de clic
                - "LISTING_IMPRESSION_TOTAL": Impressions totales
                - "LISTING_VIEWS_TOTAL": Vues totales
            listing_ids: Liste d'IDs de listings (optionnel, max 200)

        Returns:
            Dict avec métriques:
            {
                "dimensionValues": [
                    {
                        "dimensionKey": "listing_id",
                        "dimensionValue": "v1|123456789012|0",
                        "metrics": {
                            "clickThroughRate": "2.5",
                            "listingImpressionTotal": "1000",
                            "listingViewsTotal": "25"
                        }
                    }
                ],
                "totalRecords": 10
            }

        Examples:
            >>> from datetime import datetime, timedelta, timezone
            >>>
            >>> # Rapport des 7 derniers jours
            >>> now = datetime.now(timezone.utc)
            >>> week_ago = now - timedelta(days=7)
            >>> report = client.get_traffic_report(
            ...     start_date=week_ago,
            ...     end_date=now,
            ...     dimension="LISTING",
            ...     metric="CLICK_THROUGH_RATE"
            ... )
            >>>
            >>> # Analyser résultats
            >>> for item in report.get("dimensionValues", []):
            ...     listing_id = item["dimensionValue"]
            ...     metrics = item["metrics"]
            ...     ctr = metrics.get("clickThroughRate", "0")
            ...     print(f"Listing {listing_id}: CTR {ctr}%")
        """
        # Formater dates pour eBay (ISO 8601)
        start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        # Construire filter
        filter_parts = [
            f"startDate:{start_str}",
            f"endDate:{end_str}",
        ]

        if listing_ids:
            # Limiter à 200 listings (max eBay)
            listing_ids = listing_ids[:200]
            listing_filter = "|".join(listing_ids)
            filter_parts.append(f"listingIds:{listing_filter}")

        filter_str = ",".join(filter_parts)

        params = {
            "dimension": dimension,
            "metric": metric,
            "filter": filter_str,
        }

        scopes = ["sell.analytics", "sell.analytics.readonly"]

        result = self.api_call(
            "GET",
            "/sell/analytics/v1/traffic_report",
            params=params,
            scopes=scopes,
        )

        return result or {}

    def get_traffic_summary(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Récupère un résumé du trafic (toutes listings agrégées).

        Helper method qui agrège les métriques.

        Args:
            start_date: Date début
            end_date: Date fin

        Returns:
            Dict avec métriques agrégées:
            {
                "total_impressions": 5000,
                "total_clicks": 125,
                "total_views": 100,
                "click_through_rate": 2.5,
                "period_days": 7
            }

        Examples:
            >>> from datetime import datetime, timedelta, timezone
            >>>
            >>> now = datetime.now(timezone.utc)
            >>> month_ago = now - timedelta(days=30)
            >>> summary = client.get_traffic_summary(month_ago, now)
            >>>
            >>> print(f"📊 Performance 30 derniers jours:")
            >>> print(f"   Impressions: {summary['total_impressions']:,}")
            >>> print(f"   Clics: {summary['total_clicks']:,}")
            >>> print(f"   CTR: {summary['click_through_rate']:.2f}%")
        """
        # Récupérer rapport détaillé
        report = self.get_traffic_report(
            start_date=start_date,
            end_date=end_date,
            dimension="DAY",  # Agréger par jour
            metric="CLICK_THROUGH_RATE",
        )

        # Agréger métriques
        total_impressions = 0
        total_clicks = 0
        total_views = 0

        for item in report.get("dimensionValues", []):
            metrics = item.get("metrics", {})
            total_impressions += int(metrics.get("listingImpressionTotal", 0))
            total_clicks += int(metrics.get("listingClickTotal", 0))
            total_views += int(metrics.get("listingViewsTotal", 0))

        # Calculer CTR
        click_through_rate = (
            (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        )

        # Calculer nombre de jours
        period_days = (end_date - start_date).days

        return {
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_views": total_views,
            "click_through_rate": round(click_through_rate, 2),
            "period_days": period_days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    def get_listing_performance(
        self,
        listing_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Récupère les métriques de performance d'un listing spécifique.

        Args:
            listing_id: ID du listing eBay
            start_date: Date début
            end_date: Date fin

        Returns:
            Métriques du listing

        Examples:
            >>> from datetime import datetime, timedelta, timezone
            >>>
            >>> now = datetime.now(timezone.utc)
            >>> week_ago = now - timedelta(days=7)
            >>>
            >>> perf = client.get_listing_performance(
            ...     listing_id="v1|123456789012|0",
            ...     start_date=week_ago,
            ...     end_date=now
            ... )
            >>>
            >>> print(f"Listing performance:")
            >>> print(f"  Impressions: {perf['impressions']}")
            >>> print(f"  Clics: {perf['clicks']}")
            >>> print(f"  Vues: {perf['views']}")
            >>> print(f"  CTR: {perf['ctr']}%")
        """
        report = self.get_traffic_report(
            start_date=start_date,
            end_date=end_date,
            dimension="LISTING",
            metric="CLICK_THROUGH_RATE",
            listing_ids=[listing_id],
        )

        # Extraire métriques du listing
        for item in report.get("dimensionValues", []):
            if item["dimensionValue"] == listing_id:
                metrics = item.get("metrics", {})
                return {
                    "listing_id": listing_id,
                    "impressions": int(metrics.get("listingImpressionTotal", 0)),
                    "clicks": int(metrics.get("listingClickTotal", 0)),
                    "views": int(metrics.get("listingViewsTotal", 0)),
                    "ctr": float(metrics.get("clickThroughRate", 0)),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                }

        # Listing non trouvé
        return {
            "listing_id": listing_id,
            "impressions": 0,
            "clicks": 0,
            "views": 0,
            "ctr": 0.0,
            "error": "Listing not found in report",
        }
