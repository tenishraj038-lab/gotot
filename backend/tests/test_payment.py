import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from app.services.payment_service import (
    get_plan,
    get_max_daily_downloads,
    has_feature,
    _cents_for_currency,
    _divisor,
    PLANS,
    PAY_PER_DOWNLOAD_CENTS,
)
from app.models.monetization import SubscriptionTier


class TestPlans:
    def test_get_pro_plan(self):
        plan = get_plan(SubscriptionTier.PRO)
        assert plan is not None
        assert plan["daily_downloads"] == 100
        assert plan["monthly_price"] == 4.99

    def test_get_unlimited_plan(self):
        plan = get_plan(SubscriptionTier.UNLIMITED)
        assert plan is not None
        assert plan["daily_downloads"] == 1000
        assert plan["monthly_price"] == 9.99

    def test_get_free_plan(self):
        plan = get_plan(SubscriptionTier.FREE)
        assert plan is None

    def test_has_mp3_feature_pro(self):
        assert has_feature(SubscriptionTier.PRO, "mp3_conversion") is True

    def test_has_mp3_feature_free(self):
        assert has_feature(SubscriptionTier.FREE, "mp3_conversion") is False

    def test_unlimited_has_all_features(self):
        assert has_feature(SubscriptionTier.UNLIMITED, "priority_support") is True
        assert has_feature(SubscriptionTier.UNLIMITED, "mp3_conversion") is True


class TestDailyLimits:
    def test_pro_limit(self):
        assert get_max_daily_downloads(SubscriptionTier.PRO) == 100

    def test_unlimited_limit(self):
        assert get_max_daily_downloads(SubscriptionTier.UNLIMITED) == 1000

    def test_free_limit(self):
        assert get_max_daily_downloads(SubscriptionTier.FREE) == 5


class TestDivisor:
    def test_divisor_returns_100(self):
        assert _divisor() == 100


class TestPayPerDownload:
    def test_pay_per_download_cents(self):
        assert PAY_PER_DOWNLOAD_CENTS == 50
