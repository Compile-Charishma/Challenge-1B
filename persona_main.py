# multi_main.py

import os
import json
from datetime import datetime
from collections import defaultdict
from utils.extract_layout import extract_pdf_layout
from utils.heading_classifier import classify_title_subtitle_headings
import fitz
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

GENERIC_TITLES = {"introduction", "conclusion", "overview", "summary"}


def heading_level_weight(level):
    return {"H1": 1.2, "H2": 1.0, "H3": 0.8}.get(level, 1.0)

def extract_sections_with_text(pdf_path, outline):
    doc = fitz.open(pdf_path)
    sections = []

    for i, item in enumerate(outline):
        title = item['text'].strip()
        page = item['page']
        level = item['level']

        start_page = page - 1
        end_page = outline[i + 1]['page'] - 1 if i + 1 < len(outline) else doc.page_count - 1

        section_text = ""
        for pg in range(start_page, end_page + 1):
            section_text += doc[pg].get_text()

        snippet = section_text.strip().split('\n\n')[0]
        sentences = re.split(r'(?<=[.!?]) +', snippet)
        snippet = ' '.join(sentences[:3])

        sections.append({
            "section_title": title,
            "page": page,
            "level": level,
            "content": snippet.strip()
        })

    return sections

def rank_sections(sections, query, top_k=5, doc_limit=2):
    filtered = []
    seen_titles = set()

    # Only keep sections with non-blank, non-generic content
    for s in sections:
        title_lower = s["section_title"].strip().lower()
        content_clean = s["content"].strip()
        if title_lower in GENERIC_TITLES or not content_clean:
            continue
        if title_lower in seen_titles:
            continue
        seen_titles.add(title_lower)
        filtered.append(s)

    # If not enough, fill with additional non-blank sections from PDFs
    if len(filtered) < top_k:
        extra_sections = [s for s in sections if s["section_title"].strip().lower() not in GENERIC_TITLES and s["content"].strip() and s not in filtered]
        for s in extra_sections:
            filtered.append(s)
            if len(filtered) >= top_k:
                break

    # If still not enough, fill with any remaining sections (last resort)
    if len(filtered) < top_k:
        for s in sections:
            if s not in filtered:
                filtered.append(s)
            if len(filtered) >= top_k:
                break

    # Truncate to exactly top_k
    filtered = filtered[:top_k]

    if not filtered:
        print("[WARN] No usable sections after filtering.")
        return []

    docs = [s["section_title"] + " " + s["content"] for s in filtered]

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(docs + [query])
    query_vec = tfidf[-1]
    scores = cosine_similarity(query_vec, tfidf[:-1]).flatten()

    scored_sections = []
    for sec, score in zip(filtered, scores):
        weight = heading_level_weight(sec.get("level", "H2"))
        final_score = score * weight
        scored_sections.append((sec, final_score))

    scored_sections.sort(key=lambda x: x[1], reverse=True)

    # Always return exactly top_k sections
    return scored_sections[:top_k]

def process_collection(collection_path):
    print(f"\n[INFO] 📁 Processing collection: {collection_path}")
    input_path = os.path.join(collection_path, "input.json")
    pdf_dir = os.path.join(collection_path, "pdfs")
    output_path = os.path.join(collection_path, "output.json")

    with open(input_path, encoding='utf-8') as f:
        input_data = json.load(f)

    persona = input_data['persona']['role']
    job = input_data['job_to_be_done']['task']
    query = f"{persona}: {job}"
    documents = input_data['documents']

    all_sections = []

    for doc in documents:
        filename = doc['filename']
        full_path = os.path.join(pdf_dir, filename)

        print(f"[INFO] → Parsing: {filename}")
        layout = extract_pdf_layout(full_path)
        _, _, outline = classify_title_subtitle_headings(layout)

        if not outline:
            print(f"[WARN] No headings found. Using fallback (first page)")
            with fitz.open(full_path) as pdf:
                text = pdf[0].get_text()
                all_sections.append({
                    "section_title": "Document Start",
                    "page": 1,
                    "level": "H1",
                    "content": text.strip(),
                    "document": filename
                })
            continue

        sections = extract_sections_with_text(full_path, outline)
        for sec in sections:
            sec["document"] = filename
            all_sections.append(sec)

    print(f"[INFO] ✓ Extracted {len(all_sections)} sections total")

    ranked = rank_sections(all_sections, query, top_k=5, doc_limit=2)

    # Always select exactly 5 unique, non-blank sections with unique refined_text
    unique_sections = []
    seen_texts = set()
    for section, _ in ranked:
        refined_text_clean = re.sub(r'[\r\n]+', ' ', section["content"][:800]).strip()
        if not refined_text_clean:
            continue
        if refined_text_clean in seen_texts:
            continue
        seen_texts.add(refined_text_clean)
        unique_sections.append(section)
        if len(unique_sections) >= 5:
            break

    # If less than 5, fill with additional unique non-blank sections from all_sections
    if len(unique_sections) < 5:
        for s in all_sections:
            refined_text_clean = re.sub(r'[\r\n]+', ' ', s["content"][:800]).strip()
            if not refined_text_clean or s in unique_sections or refined_text_clean in seen_texts:
                continue
            seen_texts.add(refined_text_clean)
            unique_sections.append(s)
            if len(unique_sections) >= 5:
                break

    # If still less than 5, fill with any remaining unique sections
    if len(unique_sections) < 5:
        for s in all_sections:
            refined_text_clean = re.sub(r'[\r\n]+', ' ', s["content"][:800]).strip()
            if s in unique_sections or refined_text_clean in seen_texts:
                continue
            seen_texts.add(refined_text_clean)
            unique_sections.append(s)
            if len(unique_sections) >= 5:
                break

    # Truncate to exactly 5
    unique_sections = unique_sections[:5]

    output = {
        "metadata": {
            "input_documents": [doc["filename"] for doc in documents],
            "persona": persona,
            "job_to_be_done": job,
            "processing_timestamp": datetime.now().isoformat()
        },
        "extracted_sections": [],
        "subsection_analysis": []
    }

    # Use the same unique logic for subsection_analysis
    used_refined_texts = set()
    for i, section in enumerate(unique_sections):
        output["extracted_sections"].append({
            "document": section["document"],
            "section_title": section["section_title"],
            "importance_rank": i + 1,
            "page_number": section["page"]
        })
        refined_text_clean = re.sub(r'[\r\n]+', ' ', section["content"][:800]).strip()
        if refined_text_clean in used_refined_texts:
            continue
        used_refined_texts.add(refined_text_clean)
        output["subsection_analysis"].append({
            "document": section["document"],
            "refined_text": refined_text_clean,
            "page_number": section["page"]
        })

    # If less than 5 unique subsection_analysis, fill with additional unique content
    if len(output["subsection_analysis"]) < 5:
        for s in all_sections:
            refined_text_clean = re.sub(r'[\r\n]+', ' ', s["content"][:800]).strip()
            if not refined_text_clean or refined_text_clean in used_refined_texts:
                continue
            used_refined_texts.add(refined_text_clean)
            output["subsection_analysis"].append({
                "document": s["document"],
                "refined_text": refined_text_clean,
                "page_number": s["page"]
            })
            if len(output["subsection_analysis"]) >= 5:
                break

    # Truncate to exactly 5
    output["subsection_analysis"] = output["subsection_analysis"][:5]

    with open(output_path, 'w', encoding='utf-8') as f_out:
        json.dump(output, f_out, indent=2, ensure_ascii=False)

    print(f"[✅] Output written to: {output_path}")

def main():
    current_dir = '.'
    collections = [d for d in os.listdir(current_dir)
                   if d.startswith("collection") and os.path.isdir(d)]

    if not collections:
        print("[❌] No collection folders found.")
        return

    for collection in sorted(collections):
        process_collection(collection)

if __name__ == "__main__":
    main()
