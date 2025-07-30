from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.salesforce_analytics.crew import SalesforceCrewai
from datetime import datetime
from typing import List
import glob
import os

app = FastAPI()
crew_instance = SalesforceCrewai()

# CORS 설정
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 경로 상수
BASE_PATH = "src/salesforce_crewai/outputs"

class RunRequest(BaseModel):
    run: bool = True

@app.post("/run")
def run_crew(req: RunRequest):
    current_year = str(datetime.now().year)
    try:
        result = crew_instance.run(inputs={'current_year': current_year})
        output_pdf = os.path.abspath(
            f'src/salesforce_crewai/outputs/report_creator/salesforce_{current_year}_summary_report.pdf'
        )
        return {
            "message": "Crew execution completed successfully.",
            "year": current_year,
            "result": result,
            "report_pdf": output_pdf
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/summary")
def get_translated_summary(year: int = datetime.now().year):
    file_path = f"{BASE_PATH}/translator/translated_summary_{year}.md"
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as f:
            return {"year": year, "summary": f.read()}
    else:
        raise HTTPException(status_code=404, detail="Translated summary not found")

@app.get("/summary/en")
def get_english_summary(year: int = datetime.now().year):
    file_path = f"{BASE_PATH}/summary_generator/summary_{year}.md"
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as f:
            return {"year": year, "summary_en": f.read()}
    else:
        raise HTTPException(status_code=404, detail="English summary not found")

@app.get("/report")
def download_report(year: int = datetime.now().year):
    file_path = f"{BASE_PATH}/report_creator/salesforce_{year}_summary_report.pdf"
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            media_type='application/pdf',
            filename=f"Salesforce_Summary_{year}.pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Salesforce_Summary_{year}.pdf"
            }
        )
    else:
        raise HTTPException(status_code=404, detail="PDF report not found")

@app.get("/report/view")
def preview_report(year: int = datetime.now().year):
    file_path = f"{BASE_PATH}/report_creator/salesforce_{year}_summary_report.pdf"
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            media_type='application/pdf',
            filename=f"Salesforce_Summary_{year}.pdf",
            headers={
                "Content-Disposition": "inline"
            }
        )
    else:
        raise HTTPException(status_code=404, detail="PDF not found")


@app.get("/status")
def get_status(year: int = datetime.now().year):
    pdf_path = f"{BASE_PATH}/report_creator/salesforce_{year}_summary_report.pdf"
    summary_path = f"{BASE_PATH}/translator/translated_summary_{year}.md"
    return {
        "pdf_exists": os.path.exists(pdf_path),
        "translated_summary_exists": os.path.exists(summary_path),
        "year": year
    }

@app.post("/upload-summary")
def manual_upload_to_salesforce(year: int = datetime.now().year):
    from src.salesforce_analytics.main import upload_to_salesforce
    from simple_salesforce import Salesforce

    try:
        current_date = datetime.now().strftime('%y%m%d')
        sf = Salesforce(
            username=os.getenv('SF_USERNAME'),
            password=os.getenv('SF_PASSWORD'),
            security_token=os.getenv('SF_TOKEN')
        )

        csv_path = f"{BASE_PATH}/salesforce_connector/extracted_data_{year}.csv"
        json_path = f"{BASE_PATH}/data_analyzer/analysis_results_{year}.json"
        md_path = f"{BASE_PATH}/translator/translated_summary_{year}.md"
        pdf_path = f"{BASE_PATH}/report_creator/salesforce_{year}_summary_report.pdf"

        files = [f for f in [csv_path, json_path, md_path, pdf_path] if os.path.exists(f)]
        if not files:
            raise FileNotFoundError("업로드할 파일이 존재하지 않습니다.")

        upload_to_salesforce(sf, current_date, files)  # 여기서 핵심 함수 호출

        return {"message": "Salesforce 업로드 성공", "files_uploaded": files}
    except Exception as e:
        return {"error": str(e)}


@app.delete("/delete-summary")
def delete_summary_files(year: int = datetime.now().year):
    deleted_files = []
    summary_paths = glob.glob(f"{BASE_PATH}/**/*{year}*", recursive=True)
    for path in summary_paths:
        try:
            os.remove(path)
            deleted_files.append(path)
        except Exception:
            continue
    return {"message": "요약 관련 결과 삭제 완료", "files_deleted": deleted_files}