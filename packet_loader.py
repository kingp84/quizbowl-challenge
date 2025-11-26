# packet_loader.py
# Utilities to load packets from JSON, CSV, DOCX, PDF across format folders,
# including your 'generated' subfolders. Automatically splits tossup text into
# pyramidal Hard/Medium/Easy clues based on sentence order.

import os
import json
import csv
import re

PACKETS_ROOT = "packets"

# Optional imports for DOCX/PDF
try:
    from docx import Document
except Exception:
    Document = None

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

# ----------------------------
# Sentence splitting → pyramidal clues
# ----------------------------
def split_into_clues(tossup_text: str):
    # Split into sentences (basic regex split on punctuation + whitespace)
    sentences = re.split(r'(?<=[.!?])\s+', tossup_text.strip())
    sentences = [s for s in sentences if s]

    clues = []
    if len(sentences) == 3:
        clues = [
            {"difficulty": "Hard", "text": sentences[0]},
            {"difficulty": "Medium", "text": sentences[1]},
            {"difficulty": "Easy", "text": sentences[2]},
        ]
    elif len(sentences) == 4:
        clues = [
            {"difficulty": "Hard", "text": sentences[0]},
            {"difficulty": "Medium", "text": sentences[1] + " " + sentences[2]},
            {"difficulty": "Easy", "text": sentences[3]},
        ]
    elif len(sentences) > 4:
        clues = [
            {"difficulty": "Hard", "text": sentences[0]},
            {"difficulty": "Medium", "text": " ".join(sentences[1:-1])},
            {"difficulty": "Easy", "text": sentences[-1]},
        ]
    else:
        clues = [{"difficulty": "Easy", "text": " ".join(sentences)}]

    return clues

# ----------------------------
# Folder helpers
# ----------------------------
def format_folder(format_name: str) -> str:
    return os.path.join(PACKETS_ROOT, format_name.lower())

def generated_format_folder(format_name: str) -> str:
    return os.path.join(PACKETS_ROOT, "generated", format_name.lower())

def get_packet_list(format_name: str):
    """
    Returns a sorted list of packet filenames available for the format.
    Searches generated first, then base folder.
    """
    if not format_name:
        return []

    base = format_folder(format_name)
    gen = generated_format_folder(format_name)
    files = []

    for folder in (gen, base):
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if f.lower().endswith((".json", ".csv", ".docx", ".pdf")):
                    files.append(f)

    # De-duplicate while preserving order (prefer generated occurrences)
    seen = set()
    result = []
    for f in files:
        if f not in seen:
            seen.add(f)
            result.append(f)

    return sorted(result)

# ----------------------------
# Loaders for each file type
# ----------------------------
def load_json_packet(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "questions" in data:
        data = data["questions"]

    questions = []
    for q in data:
        tossup_text = q.get("tossup") or q.get("text") or ""
        answer = q.get("answer", "")
        clues = q.get("clues") or split_into_clues(tossup_text)
        questions.append({
            "id": q.get("id"),
            "answer": answer,
            "clues": clues
        })
    return questions

def load_csv_packet(path: str):
    questions = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tossup_text = row.get("tossup") or row.get("text") or ""
            answer = row.get("answer", "")
            clues = split_into_clues(tossup_text)
            questions.append({
                "id": row.get("id"),
                "answer": answer,
                "clues": clues
            })
    return questions

def load_docx_packet(path: str):
    if Document is None:
        return []
    doc = Document(path)
    paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    questions = []
    # Assume each block separated by blank lines is a tossup
    block = []
    for para in paras:
        if para == "":
            if block:
                tossup_text = " ".join(block[:-1])
                answer = block[-1]
                clues = split_into_clues(tossup_text)
                questions.append({
                    "id": f"docx-{len(questions)+1}",
                    "answer": answer,
                    "clues": clues
                })
                block = []
        else:
            block.append(para)
    if block:
        tossup_text = " ".join(block[:-1])
        answer = block[-1]
        clues = split_into_clues(tossup_text)
        questions.append({
            "id": f"docx-{len(questions)+1}",
            "answer": answer,
            "clues": clues
        })
    return questions

def load_pdf_packet(path: str):
    if PyPDF2 is None:
        return []
    questions = []
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    for b in blocks:
        lines = [ln.strip() for ln in b.split("\n") if ln.strip()]
        if len(lines) >= 2:
            tossup_text = " ".join(lines[:-1])
            answer = lines[-1]
            clues = split_into_clues(tossup_text)
            questions.append({
                "id": f"pdf-{len(questions)+1}",
                "answer": answer,
                "clues": clues
            })
    return questions

# ----------------------------
# Path resolution + unified loader
# ----------------------------
def resolve_path(format_name: str, filename: str):
    gen = generated_format_folder(format_name)
    base = format_folder(format_name)
    gen_path = os.path.join(gen, filename)
    base_path = os.path.join(base, filename)
    if os.path.isfile(gen_path):
        return gen_path
    if os.path.isfile(base_path):
        return base_path
    return None

def load_packet_file(format_name: str, filename: str):
    path = resolve_path(format_name, filename)
    if not path:
        return []

    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        return load_json_packet(path)
    elif ext == ".csv":
        return load_csv_packet(path)
    elif ext == ".docx":
        return load_docx_packet(path)
    elif ext == ".pdf":
        return load_pdf_packet(path)
    return []