import json
import logging

import pytest

from doc_assistant.logging_setup import setup_logging


def test_json_log_contains_extra_fields(capsys: pytest.CaptureFixture[str]) -> None:
    setup_logging("INFO", as_json=True)
    logging.getLogger("test").info("chunk indexé", extra={"document": "a.pdf", "page": 4})
    line = capsys.readouterr().err.strip().splitlines()[-1]
    record = json.loads(line)
    assert record["msg"] == "chunk indexé"
    assert record["document"] == "a.pdf"
    assert record["page"] == 4
    assert record["level"] == "INFO"
