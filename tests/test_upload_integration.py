from fastapi.testclient import TestClient

EXPECTED_SECTIONS = {
    "source_metadata",
    "validation",
    "data_profile",
    "quality_score",
    "quality_gate",
    "preparation",
    "transformation_log",
    "manipulation_summary",
    "trend_analysis",
    "forecast_analysis",
    "kpis",
    "security",
    "anomalies",
    "charts",
    "insights",
    "recommendation_plan",
    "workflow_improvement_plan",
    "audit_events",
}


def test_upload_canonical_success(client: TestClient) -> None:
    csv_content = (
        "order_id,order_date,customer_id,region,product,sales_rep,quantity,unit_price,discount,revenue\n"
        "1,2023-01-01,CUST1,North,ProdA,RepA,10,5.0,0.1,45.0"
    )
    files = {"file": ("canonical.csv", csv_content, "text/csv")}
    response = client.post("/analysis/upload", files=files)
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == EXPECTED_SECTIONS
    assert payload["source_metadata"]["source_type"] == "uploaded_csv"
    assert payload["source_metadata"]["file_name"] == "canonical.csv"


def test_upload_classic_sales_sample_mapped_success(client: TestClient) -> None:
    csv_content = (
        "ORDERNUMBER,ORDERDATE,CUSTOMERNAME,TERRITORY,PRODUCTLINE,CONTACTFIRSTNAME,CONTACTLASTNAME,QUANTITYORDERED,PRICEEACH,SALES\n"
        "10107,2/24/2003 0:00,Land of Toys Inc.,APAC,Motorcycles,Yu,Kwai,30,95.7,2871"
    )
    files = {"file": ("classic_sample.csv", csv_content, "text/csv")}
    response = client.post("/analysis/upload", files=files)
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == EXPECTED_SECTIONS
    assert payload["source_metadata"]["source_type"] == "uploaded_csv"
    assert payload["source_metadata"]["file_name"] == "classic_sample.csv"
    assert payload["source_metadata"]["file_size_bytes"] == len(csv_content)
    assert (
        "Schema mapped from classic_sales_sample" in payload["source_metadata"]["notes"]
    )
    assert "Discount was defaulted to 0" in payload["source_metadata"]["notes"]


def test_upload_classic_sales_sample_cp1252_success(client: TestClient) -> None:
    headers = "ORDERNUMBER,ORDERDATE,CUSTOMERNAME,TERRITORY,PRODUCTLINE,CONTACTFIRSTNAME,CONTACTLASTNAME,QUANTITYORDERED,PRICEEACH,SALES\n"
    row = (
        "10107,2/24/2003 0:00,Land of € Toys Inc.,APAC,Motorcycles,Yu,Kwai,30,95.7,2871"
    )
    csv_bytes = headers.encode("cp1252") + row.encode("cp1252")
    files = {"file": ("classic_sample_cp1252.csv", csv_bytes, "text/csv")}
    response = client.post("/analysis/upload", files=files)
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == EXPECTED_SECTIONS
    assert payload["source_metadata"]["file_name"] == "classic_sample_cp1252.csv"
    assert "CSV was decoded using Windows-1252" in payload["source_metadata"]["notes"]


def test_upload_incompatible_returns_400(client: TestClient) -> None:
    csv_content = "order_date,customer_id,region\n2023-01-01,CUST-A,North"
    files = {"file": ("incompatible.csv", csv_content, "text/csv")}
    response = client.post("/analysis/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    detail = data["detail"]
    assert "CSV schema is not compatible with InsightOps-AI" in detail
    assert "Missing required columns" in detail
    assert "Detected columns" in detail
    assert "Supported schemas" in detail


def test_upload_unreadable_binary_returns_400(client: TestClient) -> None:
    csv_bytes = b"order_id,order_date\n\x00\x00\x00\x00\n"
    files = {"file": ("test_binary.csv", csv_bytes, "text/csv")}
    response = client.post("/analysis/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert "could not be decoded" in data["detail"]
    assert "Supported encodings" in data["detail"]


def test_upload_report_classic_sales_sample_cp1252_success(client: TestClient) -> None:
    headers = "ORDERNUMBER,ORDERDATE,CUSTOMERNAME,TERRITORY,PRODUCTLINE,CONTACTFIRSTNAME,CONTACTLASTNAME,QUANTITYORDERED,PRICEEACH,SALES\n"
    row = (
        "10107,2/24/2003 0:00,Land of € Toys Inc.,APAC,Motorcycles,Yu,Kwai,30,95.7,2871"
    )
    csv_bytes = headers.encode("cp1252") + row.encode("cp1252")
    files = {"file": ("classic_sample_cp1252.csv", csv_bytes, "text/csv")}
    response = client.post("/analysis/upload/report?format=markdown", files=files)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "Executive Sales Report" in response.text
