import pytest

from app.domain.shipping import ShippingZone, UnsupportedDestinationError, classify_country


def test_italy_is_the_domestic_zone():
    assert classify_country("IT") is ShippingZone.ITALY


def test_germany_is_eu_continental():
    assert classify_country("DE") is ShippingZone.EU_CONTINENTAL


def test_switzerland_is_non_eu_continental():
    assert classify_country("CH") is ShippingZone.NON_EU_CONTINENTAL


def test_norway_is_non_eu_continental():
    assert classify_country("NO") is ShippingZone.NON_EU_CONTINENTAL


def test_unsupported_destination_raises():
    with pytest.raises(UnsupportedDestinationError):
        classify_country("US")


def test_classify_country_is_case_insensitive():
    assert classify_country("it") is ShippingZone.ITALY
