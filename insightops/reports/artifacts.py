from pydantic import BaseModel


class ReportArtifact(BaseModel):
    report_id: str
    title: str
    file_path: str
    file_name: str
    format: str
