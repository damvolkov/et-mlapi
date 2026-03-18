"""Tests for models/core.py."""

from et_mlapi.models.core import BodyType, UploadFile

##### BODY TYPE ENUM #####


async def test_body_type_values() -> None:
    assert BodyType.PYDANTIC == "pydantic"
    assert BodyType.JSONABLE == "jsonable"
    assert BodyType.RAW == "raw"
    assert BodyType.FILE == "file"


async def test_body_type_membership() -> None:
    assert "pydantic" in [e.value for e in BodyType]
    assert len(list(BodyType)) == 4


##### UPLOAD FILE #####


async def test_upload_file_empty() -> None:
    uf = UploadFile()
    assert not uf
    assert uf.keys() == []


async def test_upload_file_with_data() -> None:
    uf = UploadFile(files={"doc.pdf": b"pdf-bytes"})
    assert uf
    assert uf.get("doc.pdf") == b"pdf-bytes"
    assert uf.get("missing") is None


async def test_upload_file_keys() -> None:
    uf = UploadFile(files={"a.txt": b"a", "b.txt": b"b"})
    assert sorted(uf.keys()) == ["a.txt", "b.txt"]


async def test_upload_file_iter() -> None:
    uf = UploadFile(files={"x": b"1", "y": b"2"})
    items = list(uf)
    assert len(items) == 2
    names = {name for name, _ in items}
    assert names == {"x", "y"}


async def test_upload_file_bool_false() -> None:
    assert not UploadFile(files={})


async def test_upload_file_bool_true() -> None:
    assert UploadFile(files={"f": b"data"})
