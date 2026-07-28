from collections.abc import Iterator

import pytest

from app.persistence.database import SessionFactory, create_session_factory
from app.persistence.models import Base
from app.persistence.repositories import OperationRepository


@pytest.fixture
def session_factory() -> Iterator[SessionFactory]:
    factory = create_session_factory("sqlite:///:memory:")
    engine = factory.kw["bind"]
    Base.metadata.create_all(engine)
    yield factory
    Base.metadata.drop_all(engine)


def test_operation_key_is_unique_and_survives_restart(session_factory: SessionFactory) -> None:
    first = OperationRepository(session_factory).begin("publish:item-1:draft-3")
    second = OperationRepository(session_factory).begin("publish:item-1:draft-3")
    assert first.id == second.id
    assert second.status == "PENDING"


def test_different_operation_keys_create_different_operations(
    session_factory: SessionFactory,
) -> None:
    first = OperationRepository(session_factory).begin("publish:item-1:draft-3")
    second = OperationRepository(session_factory).begin("publish:item-2:draft-1")
    assert first.id != second.id
