from decimal import Decimal

import pytest

from app.domain.common import Money


def test_money_rejects_binary_float() -> None:
    with pytest.raises(TypeError):
        Money(currency="EUR", value=19.99)  # type: ignore[arg-type]


def test_money_rejects_lowercase_currency() -> None:
    with pytest.raises(ValueError, match="currency"):
        Money(currency="eur", value=Decimal("19.99"))


def test_money_accepts_valid_decimal_and_currency() -> None:
    money = Money(currency="EUR", value=Decimal("19.99"))
    assert money.currency == "EUR"
    assert money.value == Decimal("19.99")
