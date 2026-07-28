from decimal import Decimal

from app.domain.common import Provenance, SourcedValue


def test_inferred_value_retains_source_and_confidence() -> None:
    value = SourcedValue(
        value="Model X",
        provenance=Provenance.INFERRED,
        confidence=Decimal("0.70"),
        sources=("https://example.invalid/model",),
    )
    assert value.provenance is Provenance.INFERRED
    assert value.confidence == Decimal("0.70")
    assert value.sources == ("https://example.invalid/model",)


def test_unknown_value_has_no_sources_by_default() -> None:
    value: SourcedValue[str] = SourcedValue(
        value=None, provenance=Provenance.UNKNOWN, confidence=Decimal("0")
    )
    assert value.value is None
    assert value.sources == ()
