# utils/heading_classifier.py

def classify_heading_level(block):
    size = block["size"]
    font = block["font"].lower()
    text = block["text"].strip()

    is_bold = ("bold" in font) or (block.get("flags", 0) & 2)

    if not is_bold:
        return None
    if len(text.split()) > 8:
        return None  # Too long for a heading
    if text.endswith('.') or text.endswith(':'):
        return None  # Looks like a sentence or subtitle
    if not any(c.isalpha() for c in text):
        return None  # No alphabetical characters

    if size >= 13.5:
        return "H1"
    elif 12.5 <= size < 13.5:
        return "H2"
    elif size <= 12.0:
        return "H3"
    return None


def classify_title_subtitle_headings(all_pages_blocks):
    if not all_pages_blocks or not all_pages_blocks[0]:
        return "", "", []

    first_page = all_pages_blocks[0]
    title = ""
    subtitle = ""
    title_blocks = []

    for i, block in enumerate(first_page):
        if (block.get("flags", 0) & 2) or classify_heading_level(block):
            title_blocks.append(block)
            for next_block in first_page[i+1:]:
                if (
                    next_block["size"] == block["size"] and
                    next_block["font"] == block["font"] and
                    next_block["flags"] == block["flags"] and
                    abs(next_block["y"] - block["y"]) < 100
                ):
                    title_blocks.append(next_block)
                    block = next_block
                else:
                    break
            break

    if title_blocks:
        title = " ".join([b["text"].strip() for b in title_blocks])

    used_y = set(b["y"] for b in title_blocks)
    for block in first_page:
        if block["y"] not in used_y:
            subtitle = block["text"].strip()
            break

    outline = []
    seen = set()

    for blocks in all_pages_blocks:
        for block in blocks:
            text = block["text"].strip()
            if not text or text == title or text == subtitle:
                continue
            sig = f"{block['page']}|{text}"
            if sig in seen:
                continue
            seen.add(sig)
            level = classify_heading_level(block)
            if level:
                outline.append({
                    "level": level,
                    "text": text,
                    "page": block["page"]
                })

    return title, subtitle, outline
