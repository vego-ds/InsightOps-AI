from fastapi.testclient import TestClient


def test_preview_canonical_csv(client: TestClient) -> None:
    csv_content = "order_id,order_date,customer_id,region,product,sales_rep,quantity,unit_price,discount,revenue\n1,2023-01-01,CUST1,North,ProdA,RepA,10,5.0,0.1,45.0"
    files = {"file": ("test.csv", csv_content, "text/csv")}
    response = client.post("/analysis/upload/preview", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.csv"
    assert data["detected_schema"] == "canonical"
    assert data["compatible"] is True
    assert data["is_canonical"] is True
    assert data["is_mappable"] is False
    assert len(data["missing_required_columns"]) == 0
    assert data["detected_encoding"] in ("utf-8", "utf-8-sig")


def test_preview_canonical_utf8_sig(client: TestClient) -> None:
    bom = b"\xef\xbb\xbf"
    csv_bytes = (
        bom
        + b"order_id,order_date,customer_id,region,product,sales_rep,quantity,unit_price,discount,revenue\n1,2023-01-01,CUST1,North,ProdA,RepA,10,5.0,0.1,45.0"
    )
    files = {"file": ("test_bom.csv", csv_bytes, "text/csv")}
    response = client.post("/analysis/upload/preview", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["detected_schema"] == "canonical"
    assert data["detected_encoding"] == "utf-8-sig"
    assert data["compatible"] is True


def test_preview_canonical_cp1252(client: TestClient) -> None:
    headers = "order_id,order_date,customer_id,region,product,sales_rep,quantity,unit_price,discount,revenue\n"
    # Euro symbol (€) is byte 0x80 in Windows-1252 (cp1252)
    row = "1,2023-01-01,CUST€,North,ProdA,RepA,10,5.0,0.1,45.0"
    csv_bytes = headers.encode("cp1252") + row.encode("cp1252")
    files = {"file": ("test_cp1252.csv", csv_bytes, "text/csv")}
    response = client.post("/analysis/upload/preview", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["detected_schema"] == "canonical"
    assert data["detected_encoding"] == "cp1252"
    assert data["compatible"] is True
    assert any("decoded using Windows-1252" in w for w in data["warnings"])


def test_preview_canonical_iso_8859_1(client: TestClient) -> None:
    headers = "order_id,order_date,customer_id,region,product,sales_rep,quantity,unit_price,discount,revenue\n"
    row = "1,2023-01-01,CUST_é,North,ProdA,RepA,10,5.0,0.1,45.0"
    csv_bytes = headers.encode("iso-8859-1") + row.encode("iso-8859-1")
    files = {"file": ("test_iso.csv", csv_bytes, "text/csv")}
    response = client.post("/analysis/upload/preview", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["detected_schema"] == "canonical"
    assert data["detected_encoding"] in ("cp1252", "iso-8859-1")
    assert data["compatible"] is True
    assert any("decoded using" in w for w in data["warnings"])


def test_preview_classic_sales_sample_csv(client: TestClient) -> None:
    csv_content = (
        "ORDERNUMBER,ORDERDATE,CUSTOMERNAME,TERRITORY,PRODUCTLINE,CONTACTFIRSTNAME,CONTACTLASTNAME,QUANTITYORDERED,PRICEEACH,SALES\n"
        "10107,2/24/2003 0:00,Land of Toys Inc.,APAC,Motorcycles,Yu,Kwai,30,95.7,2871"
    )
    files = {"file": ("test_classic.csv", csv_content, "text/csv")}
    response = client.post("/analysis/upload/preview", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_classic.csv"
    assert data["detected_schema"] == "classic_sales_sample"
    assert data["compatible"] is True
    assert data["is_canonical"] is False
    assert data["is_mappable"] is True
    assert len(data["missing_required_columns"]) == 0


def test_preview_classic_sales_sample_cp1252(client: TestClient) -> None:
    headers = "ORDERNUMBER,ORDERDATE,CUSTOMERNAME,TERRITORY,PRODUCTLINE,CONTACTFIRSTNAME,CONTACTLASTNAME,QUANTITYORDERED,PRICEEACH,SALES\n"
    # Euro symbol (€) in customer name
    row = (
        "10107,2/24/2003 0:00,Land of € Toys Inc.,APAC,Motorcycles,Yu,Kwai,30,95.7,2871"
    )
    csv_bytes = headers.encode("cp1252") + row.encode("cp1252")
    files = {"file": ("test_classic_cp1252.csv", csv_bytes, "text/csv")}
    response = client.post("/analysis/upload/preview", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["detected_schema"] == "classic_sales_sample"
    assert data["detected_encoding"] == "cp1252"
    assert data["compatible"] is True
    assert any("decoded using Windows-1252" in w for w in data["warnings"])


def test_preview_incompatible_csv(client: TestClient) -> None:
    csv_content = "order_date,customer_id,region\n2023-01-01,CUST1,North"
    files = {"file": ("incompatible.csv", csv_content, "text/csv")}
    response = client.post("/analysis/upload/preview", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "incompatible.csv"
    assert data["detected_schema"] == "unknown"
    assert data["compatible"] is False
    assert data["is_canonical"] is False
    assert data["is_mappable"] is False
    assert len(data["missing_required_columns"]) > 0


def test_preview_unreadable_binary(client: TestClient) -> None:
    # Use .csv extension so it passes filename guardrail
    csv_bytes = b"order_id,order_date\n\x00\x00\x00\x00\n"
    files = {"file": ("test_binary.csv", csv_bytes, "text/csv")}
    response = client.post("/analysis/upload/preview", files=files)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "could not be decoded" in detail
    assert "Supported encodings" in detail
    assert "Windows-1252" in detail
    assert "ISO-8859-1" in detail


def test_preview_non_csv(client: TestClient) -> None:
    files = {"file": ("test.txt", "some text data", "text/plain")}
    response = client.post("/analysis/upload/preview", files=files)
    assert response.status_code == 400
    assert "must be a CSV file" in response.json()["detail"]


def test_preview_empty_upload(client: TestClient) -> None:
    files = {"file": ("empty.csv", "", "text/csv")}
    response = client.post("/analysis/upload/preview", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_preview_respects_upload_size_limit(monkeypatch, client: TestClient) -> None:
    from app.main import settings

    monkeypatch.setattr(settings, "max_upload_bytes", 10)
    csv_content = "order_id,order_date,customer_id\n"
    files = {"file": ("test_limit.csv", csv_content, "text/csv")}
    response = client.post("/analysis/upload/preview", files=files)
    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"]
