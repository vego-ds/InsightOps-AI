from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import UploadFile, HTTPException
from pydantic import BaseModel


class UploadedCsvFile(BaseModel):
    path: Path
    original_filename: str
    size_bytes: int


async def persist_upload_temporarily(
    upload_file: UploadFile | None,
    max_bytes: int,
) -> UploadedCsvFile:
    if upload_file is None:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must have a filename.",
        )

    filename = upload_file.filename or ""
    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must have a filename.",
        )

    if not filename.casefold().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must be a CSV file.",
        )

    temp_file = NamedTemporaryFile(delete=False, suffix=".csv")
    temp_path = Path(temp_file.name)
    total_bytes = 0

    try:
        # Read in 64 KB chunks
        chunk_size = 65536
        while True:
            chunk = await upload_file.read(chunk_size)
            if not chunk:
                break

            total_bytes += len(chunk)
            if total_bytes > max_bytes:
                mb_limit = max_bytes // (1024 * 1024)
                limit_desc = f"{mb_limit} MB" if mb_limit >= 1 else f"{max_bytes} bytes"
                raise HTTPException(
                    status_code=413,
                    detail=f"Uploaded CSV file exceeds the {limit_desc} size limit.",
                )

            temp_file.write(chunk)

        temp_file.flush()
        temp_file.close()

        if total_bytes == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded CSV file is empty.",
            )

        return UploadedCsvFile(
            path=temp_path,
            original_filename=filename,
            size_bytes=total_bytes,
        )

    except Exception as e:
        temp_file.close()
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise e
