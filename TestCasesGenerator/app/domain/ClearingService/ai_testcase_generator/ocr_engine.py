import os
from typing import Any, Dict, List

_ocr_engine = None

def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr import RapidOCR
        _ocr_engine = RapidOCR()
    return _ocr_engine

def flatten_rapidocr_result(result: Any) -> List[Dict[str, Any]]:
    raw = result
    if isinstance(result, tuple) and result:
        raw = result[0]

    if hasattr(raw, "txts"):
        txts = list(raw.txts or [])
        scores = list(getattr(raw, "scores", []) or [])
        boxes = list(getattr(raw, "boxes", []) or [])
        return [
            {
                "text": text,
                "confidence": scores[idx] if idx < len(scores) else None,
                "box": boxes[idx] if idx < len(boxes) else None,
            }
            for idx, text in enumerate(txts)
        ]

    items = []
    if isinstance(raw, list):
        for entry in raw:
            if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                text = entry[1]
                score = entry[2] if len(entry) >= 3 else None
                items.append({"text": str(text), "confidence": score, "box": entry[0]})
            elif isinstance(entry, dict):
                items.append(entry)
    return items

def extract_pdf_text(path: str) -> str:
    import fitz
    parts = []
    with fitz.open(path) as doc:
        for page in doc:
            text = page.get_text("text")
            if text:
                parts.append(text)
    return "\n".join(parts).strip()

def render_pdf_pages(path: str) -> List[str]:
    import fitz
    rendered_paths = []
    with fitz.open(path) as doc:
        for index, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            output_path = f"{path}.page-{index + 1}.png"
            pix.save(output_path)
            rendered_paths.append(output_path)
    return rendered_paths

def run_image_ocr(path: str) -> List[Dict[str, Any]]:
    engine = get_ocr_engine()
    result = engine(path)
    return flatten_rapidocr_result(result)

def process_file_in_process(input_path: str, suffix: str) -> Dict[str, Any]:
    temp_paths = []
    try:
        if suffix == ".pdf":
            text = extract_pdf_text(input_path)
            if text:
                lines = [{"text": line.strip(), "confidence": 1.0} for line in text.splitlines() if line.strip()]
                return {"engine": "pymupdf-text", "text": text, "lines": lines}

            page_paths = render_pdf_pages(input_path)
            temp_paths.extend(page_paths)
            lines = []
            for page_path in page_paths:
                lines.extend(run_image_ocr(page_path))
            return {"engine": "rapidocr", "text": "\n".join(item.get("text", "") for item in lines), "lines": lines}

        # Otherwise treat as image
        lines = run_image_ocr(input_path)
        return {"engine": "rapidocr", "text": "\n".join(item.get("text", "") for item in lines), "lines": lines}
    finally:
        for path in temp_paths:
            try:
                os.remove(path)
            except OSError:
                pass
