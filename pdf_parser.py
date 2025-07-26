# pdf_parser.py
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar

def extract_text_and_properties_from_pdf(pdf_path):
    """
    Extracts text blocks with their properties (font size, bold, page number, position)
    from a PDF document.
    """
    text_blocks_with_properties = []
    
    try:
        for page_num, page_layout in enumerate(extract_pages(pdf_path)):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    for text_line in element:
                        line_text = text_line.get_text().strip()
                        if not line_text:
                            continue

                        font_size = None
                        is_bold = False
                        if hasattr(text_line, '_objs') and text_line._objs:
                            # Iterate through characters to find average font size and bold status
                            # This is a more robust way than just checking the first char
                            char_sizes = []
                            bold_chars = 0
                            total_chars = 0
                            for char in text_line._objs:
                                if isinstance(char, LTChar):
                                    char_sizes.append(char.size)
                                    if "bold" in char.fontname.lower() or "bd" in char.fontname.lower():
                                        bold_chars += 1
                                    total_chars += 1
                            
                            if char_sizes:
                                font_size = round(sum(char_sizes) / len(char_sizes), 2)
                            if total_chars > 0 and bold_chars / total_chars > 0.5: # Consider bold if most chars are bold
                                is_bold = True
                        
                        text_blocks_with_properties.append({
                            "text": line_text,
                            "page": page_num,
                            "x0": round(text_line.x0, 2),
                            "y0": round(text_line.y0, 2),
                            "x1": round(text_line.x1, 2),
                            "y1": round(text_line.y1, 2),
                            "font_size": font_size,
                            "is_bold": is_bold,
                            "line_height": round(text_line.height, 2)
                        })
    except Exception as e:
        print(f"Error extracting from PDF {pdf_path}: {e}")
        return [] # Return empty list on error
    
    text_blocks_with_properties.sort(key=lambda x: (x['page'], -x['y0'])) # Sort by page, then Y-position (top to bottom)
    
    return text_blocks_with_properties

def get_document_title(text_blocks):
    """
    Identifies the document title. Typically the largest, boldest text
    at the top of the first page.
    """
    if not text_blocks:
        return ""

    first_page_blocks = [b for b in text_blocks if b['page'] == 0]
    if not first_page_blocks:
        return ""

    # Heuristic: Sort by font size (desc), then Y-position (desc, to get higher elements first)
    first_page_blocks.sort(key=lambda x: (x['font_size'] if x['font_size'] else 0, x['y0']), reverse=True)

    # Consider the first few largest, boldest blocks as candidates
    title_candidates = [b for b in first_page_blocks if b.get('is_bold', False) and b.get('font_size', 0) >= first_page_blocks[0].get('font_size',0)]
    
    if title_candidates:
        # A simple approach: take the text of the highest-ranked candidate.
        # More advanced: check if multiple large lines form a cohesive title.
        return title_candidates[0]['text'].strip()
    return ""