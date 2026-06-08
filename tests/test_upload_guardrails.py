import asyncio
import io
from fastapi import UploadFile, HTTPException
import pytest
from insightops.io.upload_guardrails import persist_upload_temporarily, UploadedCsvFile


def test_persist_upload_temporarily_success() -> None:
    content = b"Date,Category,Revenue\n2023-01-01,Tech,100\n"
    upload_file = UploadFile(file=io.BytesIO(content), filename="sales.csv")

    async def run() -> UploadedCsvFile:
        return await persist_upload_temporarily(upload_file, max_bytes=1000)

    result = asyncio.run(run())

    assert isinstance(result, UploadedCsvFile)
    assert result.original_filename == "sales.csv"
    assert result.size_bytes == len(content)
    assert result.path.exists()
    assert result.path.suffix == ".csv"

    # Verify content was written correctly
    assert result.path.read_bytes() == content

    # Clean up
    result.path.unlink(missing_ok=True)


def test_persist_upload_temporarily_none_file() -> None:
    async def run() -> None:
        await persist_upload_temporarily(None, max_bytes=1000)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run())

    assert exc_info.value.status_code == 400
    assert "filename" in exc_info.value.detail


def test_persist_upload_temporarily_empty_filename() -> None:
    upload_file = UploadFile(file=io.BytesIO(b""), filename="")

    async def run() -> None:
        await persist_upload_temporarily(upload_file, max_bytes=1000)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run())

    assert exc_info.value.status_code == 400
    assert "filename" in exc_info.value.detail


def test_persist_upload_temporarily_non_csv() -> None:
    upload_file = UploadFile(file=io.BytesIO(b"Date,Category\n"), filename="sales.txt")

    async def run() -> None:
        await persist_upload_temporarily(upload_file, max_bytes=1000)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run())

    assert exc_info.value.status_code == 400
    assert "CSV file" in exc_info.value.detail


def test_persist_upload_temporarily_oversized() -> None:
    content = b"a" * 105
    upload_file = UploadFile(file=io.BytesIO(content), filename="sales.csv")

    async def run() -> None:
        await persist_upload_temporarily(upload_file, max_bytes=100)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run())

    assert exc_info.value.status_code == 413
    assert "exceeds" in exc_info.value.detail


def test_persist_upload_temporarily_empty_file() -> None:
    upload_file = UploadFile(file=io.BytesIO(b""), filename="sales.csv")

    async def run() -> None:
        await persist_upload_temporarily(upload_file, max_bytes=1000)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run())

    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail


def test_persist_upload_temporarily_read_failure() -> None:
    upload_file = UploadFile(file=io.BytesIO(b"some content"), filename="sales.csv")

    async def failing_read(*args, **kwargs):
        raise IOError("Read error simulation")

    upload_file.read = failing_read

    async def run() -> None:
        await persist_upload_temporarily(upload_file, max_bytes=1000)

    with pytest.raises(IOError):
        asyncio.run(run())
