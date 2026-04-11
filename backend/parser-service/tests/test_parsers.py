import pytest
import json
import groq
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.extraction import extract_from_text
from app.parsers.txt_parser import parse_txt

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/internal/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_txt_parser_utf8():
    raw_bytes = b"John Doe\nPython, React"
    result = parse_txt(raw_bytes)
    assert "John Doe" in result
    assert "Python, React" in result

def test_txt_parser_latin1():
    raw_bytes = b"Caf\xe9"
    result = parse_txt(raw_bytes)
    assert isinstance(result, str)
    assert "Caf" in result

@patch("app.routers.parse.httpx.AsyncClient.get", new_callable=AsyncMock)
def test_unsupported_file_type(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = b"dummy content"
    
    response = client.post("/internal/parse", json={"file_url": "http://example.com/test.xlsx", "file_type": "xlsx"})
    assert response.status_code == 422

@patch("app.extraction.client")
def test_extract_from_text_success(mock_groq):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps({
        "name": "Jane Smith",
        "email": "jane@example.com",
        "raw_skills": ["Python", "FastAPI"],
        "confidence_score": 0.92,
        "warnings": []
    })
    mock_groq.chat.completions.create.return_value = mock_response
    
    result = extract_from_text("Some resume text")
    assert result.name == "Jane Smith"
    assert result.confidence_score == 0.92

@patch("app.extraction.client")
def test_extract_groq_timeout_returns_fallback(mock_groq):
    mock_groq.chat.completions.create.side_effect = groq.APITimeoutError(request=MagicMock())
    result = extract_from_text("Some resume text")
    assert result.confidence_score == 0.0
    assert "LLM timeout" in result.warnings

@patch("app.routers.parse.extract_from_text")
@patch("app.routers.parse.parse_pdf")
@patch("app.routers.parse.httpx.AsyncClient.get", new_callable=AsyncMock)
def test_full_parse_endpoint(mock_get, mock_parse_pdf, mock_extract):
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = b"dummy pdf"
    
    mock_parse_pdf.return_value = "Mocked PDF Markdown"
    
    mock_extracted = MagicMock()
    mock_extracted.name = "John Doe"
    mock_extracted.model_dump.return_value = {"name": "John Doe", "email": "john@test.com", "confidence_score": 0.9}
    mock_extract.return_value = mock_extracted

    response = client.post("/internal/parse", json={"file_url": "http://example.com/test.pdf", "file_type": "pdf"})
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["name"] == "John Doe"
