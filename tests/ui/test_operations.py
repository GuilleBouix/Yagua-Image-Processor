from concurrent.futures import ThreadPoolExecutor
from threading import Event

from app.ui.operations import OperationCoordinator


def test_coordinator_allows_only_one_global_operation():
    coordinator = OperationCoordinator()
    first_owner = object()
    second_owner = object()

    first = coordinator.begin(first_owner, "convert")

    assert first is not None
    assert coordinator.begin(second_owner, "resize") is None
    assert coordinator.is_busy()
    assert coordinator.is_busy(first_owner)
    assert not coordinator.is_busy(second_owner)

    assert coordinator.finish(first.id)
    assert coordinator.active is None
    assert not coordinator.is_busy()


def test_stale_completion_cannot_release_new_operation():
    coordinator = OperationCoordinator()
    first = coordinator.begin(object(), "first")
    assert first is not None
    assert coordinator.finish(first.id)

    second = coordinator.begin(object(), "second")
    assert second is not None

    assert not coordinator.finish(first.id)
    assert coordinator.active == second


def test_simultaneous_starts_grant_exactly_one_slot():
    coordinator = OperationCoordinator()
    owners = [object() for _ in range(16)]
    with ThreadPoolExecutor(max_workers=len(owners)) as pool:
        operations_started = list(pool.map(lambda owner: coordinator.begin(owner, "batch"), owners))

    assert sum(operation is not None for operation in operations_started) == 1


def test_submit_entrega_resultado_y_libera_slot_en_drain():
    coordinator = OperationCoordinator()
    completed = []
    owner = object()
    assert coordinator.submit(owner, "work", lambda: 42, completed.append, completed.append)

    for _ in range(100):
        if not coordinator._completions.empty():
            break
        Event().wait(0.01)
    coordinator.drain()

    assert completed == [42]
    assert coordinator.active is None


def test_submit_entrega_erro_y_libera_slot():
    coordinator = OperationCoordinator()
    errors = []
    owner = object()
    assert coordinator.submit(
        owner, "work", lambda: (_ for _ in ()).throw(ValueError("bad input")),
        lambda result: None, errors.append,
    )
    for _ in range(100):
        if not coordinator._completions.empty():
            break
        Event().wait(0.01)
    coordinator.drain()

    assert len(errors) == 1
    assert isinstance(errors[0], ValueError)
    assert coordinator.active is None
