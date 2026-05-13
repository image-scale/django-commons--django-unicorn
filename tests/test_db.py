from dk_unicorn.db import DbModel


class FakeModel:
    pass


def test_dbmodel_basic():
    db = DbModel("author", FakeModel)
    assert db.name == "author"
    assert db.model_class is FakeModel
    assert db.defaults == {}


def test_dbmodel_with_defaults():
    defaults = {"name": "Unknown", "active": True}
    db = DbModel("book", FakeModel, defaults=defaults)
    assert db.defaults == {"name": "Unknown", "active": True}


def test_dbmodel_defaults_none():
    db = DbModel("item", FakeModel, defaults=None)
    assert db.defaults == {}


def test_dbmodel_defaults_isolated():
    db1 = DbModel("a", FakeModel)
    db2 = DbModel("b", FakeModel)
    db1.defaults["key"] = "val"
    assert "key" not in db2.defaults
