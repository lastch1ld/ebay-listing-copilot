from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum


class Provenance(StrEnum):
    USER_PROVIDED = "USER_PROVIDED"
    OBSERVED = "OBSERVED"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Money:
    currency: str
    value: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            raise TypeError("Money.value must be Decimal")
        if len(self.currency) != 3 or self.currency.upper() != self.currency:
            raise ValueError("currency must be an uppercase ISO-4217 code")


@dataclass(frozen=True)
class SourcedValue[T]:
    value: T | None
    provenance: Provenance
    confidence: Decimal
    sources: tuple[str, ...] = field(default_factory=tuple)
