# File: tests/test_crud_function.py

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from backendeldery.crud.function import CRUDFunction
from backendeldery.models import Function, Attendant


@pytest.fixture
def crud():
    return CRUDFunction()


@pytest.mark.asyncio
async def test_create_function(crud):
    db = MagicMock()
    fn = await crud.create(db, "TestFunction", "Description", 1, "127.0.0.1")
    # Verify that add, flush, and refresh were called with the new function instance.
    db.add.assert_called_with(fn)
    db.flush.assert_called_once()
    db.refresh.assert_called_with(fn)
    # Verify that the new function's fields are set
    assert fn.name == "TestFunction"
    assert fn.description == "Description"
    assert fn.created_by == 1
    assert fn.user_ip == "127.0.0.1"
    assert fn.updated_by is None


@pytest.mark.asyncio
async def test_get_by_name(crud):
    db = MagicMock()
    fake_function = Function(
        name="UniqueFunction",
        description="desc",
        created_by=1,
        user_ip="127.0.0.1",
        updated_by=None,
    )
    # Simulate the query chain: query().filter().first() returns fake_function
    db.query.return_value.filter.return_value.first.return_value = fake_function
    result = await crud.get_by_name(db, "UniqueFunction")
    assert result is fake_function
    db.query.assert_called_once_with(Function)


@pytest.mark.asyncio
async def test_update_function(crud):
    db = MagicMock()
    original = Function(
        name="OldName",
        description="OldDescription",
        created_by=1,
        user_ip="127.0.0.1",
        updated_by=None,
    )
    original.id = 10
    # Simulate query().filter().first() returning the original function.
    db.query.return_value.filter.return_value.first.return_value = original
    update_data = {"name": "NewName", "description": "NewDescription"}
    updated = await crud.update(db, 10, update_data, 2, "192.168.0.1")
    # Check that attributes were updated.
    assert updated.name == "NewName"
    assert updated.description == "NewDescription"
    assert updated.updated_by == 2
    assert updated.user_ip == "192.168.0.1"
    db.add.assert_called_with(original)
    db.commit.assert_called_once()
    db.refresh.assert_called_with(original)


@pytest.mark.asyncio
async def test_list_all_functions(crud):
    db = MagicMock()
    fn_list = [
        Function(
            name="A",
            description="desc",
            created_by=1,
            user_ip="127.0.0.1",
            updated_by=None,
        ),
        Function(
            name="B",
            description="desc",
            created_by=2,
            user_ip="127.0.0.1",
            updated_by=None,
        ),
    ]
    # Simulate query().all() returning a list of functions.
    db.query.return_value.all.return_value = fn_list
    result = await crud.list_all(db)
    assert result == fn_list


@pytest.mark.asyncio
async def test_list_attendants_found(crud):
    db = MagicMock()
    fake_function = Function(
        name="FuncWithAttendants",
        description="desc",
        created_by=1,
        user_ip="127.0.0.1",
        updated_by=None,
    )
    attendant1 = Attendant(user_id=100)
    attendant2 = Attendant(user_id=101)
    fake_function.attendants = [attendant1, attendant2]
    # Simulate query().filter().first() returning a function with attendants.
    db.query.return_value.filter.return_value.first.return_value = fake_function
    result = await crud.list_attendants(db, 10)
    assert result == [attendant1, attendant2]


@pytest.mark.asyncio
async def test_list_attendants_not_found(crud):
    db = MagicMock()
    # Simulate query().filter().first() returning None.
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException) as exc:
        await crud.list_attendants(db, -1)
    assert exc.value.status_code == 404
