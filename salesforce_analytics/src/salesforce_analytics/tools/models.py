from pydantic import BaseModel
from typing import List, Dict

class DataExtractOutput(BaseModel):
    csv_path: str
    record_count: int
    columns: List[str]
    sample_rows: List[Dict]

class DataAnalysisOutput(BaseModel):
    json_path: str
    cluster_count: int
    summary: str

class SummaryOutput(BaseModel):
    summary_md_path: str
    summary_text: str

class TranslationOutput(BaseModel):
    translated_md_path: str
    translated_text: str

class ReportOutput(BaseModel):
    report_path: str
    sf_record_id: str
