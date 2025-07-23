# utils/extract_layout.py
import fitz

MERGE_Y_THRESHOLD = 5

def extract_pdf_layout(pdf_path):
    doc = fitz.open(pdf_path)
    pages_blocks = []

    for page_num, page in enumerate(doc):
        raw_blocks = []
        for b in page.get_text("dict")["blocks"]:
            if b["type"] != 0:
                continue
            for line in b["lines"]:
                line_spans = []
                for span in line["spans"]:
                    text = span["text"].strip()
                    if text:
                        line_spans.append({
                            "text": text,
                            "size": span["size"],
                            "font": span["font"],
                            "flags": span["flags"],
                            "x": span["bbox"][0],
                            "y": span["bbox"][1],
                            "page": page_num + 1
                        })
                if not line_spans:
                    continue
                line_spans.sort(key=lambda x: x["x"])
                merged_text = " ".join([s["text"] for s in line_spans])
                first = line_spans[0]
                block = {
                    "text": merged_text,
                    "size": first["size"],
                    "font": first["font"],
                    "flags": first["flags"],
                    "y": first["y"],
                    "page": first["page"]
                }
                raw_blocks.append(block)

        merged_blocks = []
        for block in raw_blocks:
            if not merged_blocks:
                merged_blocks.append(block)
            else:
                prev = merged_blocks[-1]
                is_same = (
                    block["size"] == prev["size"] and
                    block["font"] == prev["font"] and
                    block["flags"] == prev["flags"] and
                    abs(block["y"] - prev["y"]) <= MERGE_Y_THRESHOLD and
                    block["page"] == prev["page"]
                )
                if is_same:
                    prev["text"] += " " + block["text"]
                else:
                    merged_blocks.append(block)

        pages_blocks.append(merged_blocks)

    return pages_blocks
