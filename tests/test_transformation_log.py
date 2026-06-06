from insightops.lineage.transformation_log import (
    TransformationLog,
    TransformationLogEntry,
    create_transformation_log,
)


def test_create_transformation_log_wraps_entries() -> None:
    entry = TransformationLogEntry(
        step_name="clean",
        description="Clean text fields.",
        records_affected=3,
        fields_modified=["region"],
    )

    log = create_transformation_log([entry])

    assert isinstance(log, TransformationLog)
    assert log.entries == [entry]
