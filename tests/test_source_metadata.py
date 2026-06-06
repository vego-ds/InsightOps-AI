from insightops.sources.source_metadata import (
    DatasetSourceMetadata,
    create_sample_source_metadata,
    create_uploaded_source_metadata,
)


def test_sample_source_metadata_is_deterministic() -> None:
    metadata = create_sample_source_metadata(
        "data/sample/sales_sample.csv",
        record_count=5,
    )

    assert isinstance(metadata, DatasetSourceMetadata)
    assert metadata.source_type == "sample_csv"
    assert metadata.file_name == "sales_sample.csv"
    assert metadata.collection_method == "bundled_sample_file"
    assert metadata.file_size_bytes > 0
    assert metadata.record_count == 5


def test_uploaded_source_metadata_sanitizes_file_name() -> None:
    metadata = create_uploaded_source_metadata(
        "../../sales_upload.csv",
        file_size_bytes=123,
        record_count=7,
    )

    assert metadata.source_type == "uploaded_csv"
    assert metadata.file_name == "sales_upload.csv"
    assert metadata.collection_method == "api_upload"
    assert metadata.file_size_bytes == 123
    assert metadata.record_count == 7
