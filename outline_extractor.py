# outline_extractor.py
import json
from pdf_parser import extract_text_and_properties_from_pdf, get_document_title

def detect_headings(text_blocks_with_properties):
    """
    Detects H1, H2, H3 headings using a combination of heuristics:
    font size, bold status, vertical spacing, and relative position.
    Also includes a basic check for common heading patterns for bonus points (multilingual handling).
    """
    outline = []
    
    # 1. Analyze font sizes to find dominant sizes for potential headings
    font_sizes = sorted(list(set([block['font_size'] for block in text_blocks_with_properties if block['font_size'] is not None])), reverse=True)
    
    # Map font sizes to initial assumed levels. This is a heuristic and might need tuning.
    # We are looking for significant drops in font size to distinguish levels.
    level_font_map = {}
    if len(font_sizes) > 0: level_font_map["H1"] = font_sizes[0]
    if len(font_sizes) > 1 and font_sizes[0] - font_sizes[1] > 2: # Significant size difference for H2
        level_font_map["H2"] = font_sizes[1]
    elif len(font_sizes) > 0 and len(font_sizes) <=1 : # If only one large font found consider it H1
        level_font_map["H2"] = font_sizes[0] - 2 # A smaller derived size
    if len(font_sizes) > 2 and font_sizes[1] - font_sizes[2] > 1: # Significant size difference for H3
        level_font_map["H3"] = font_sizes[2]
    elif len(font_sizes) > 1 and len(font_sizes) <= 2:
        level_font_map["H3"] = font_sizes[1] - 1 # A smaller derived size

    # Reverse map for quick lookup: font_size -> potential_level
    font_to_level = {v: k for k, v in level_font_map.items()}

    # Common heading patterns for multilingual bonus (can expand this list)
    # Simple regex for chapter numbers, introduction, conclusion in English and Japanese examples
    # This is a basic implementation of multilingual handling for bonus points.
    import re
    heading_patterns = {
        "H1": [r"^(Chapter|Section)\s+\d+", r"^\d+\.?\s+Introduction", r"^\d+\.?\s+Conclusion"],
        "H2": [r"^\d+\.\d+\s+"],
        "H3": [r"^\d+\.\d+\.\d+\s+"],
        # Japanese examples (very basic, requires specific font/encoding handling in pdfminer for full support)
        "H1_JP": [r"^(第\d+章|概要|はじめに)"], # Chapter X, Overview, Introduction
        "H2_JP": [r"^\d+\.\d+\s*[\u3040-\u30ff\u4e00-\u9faf\u0020-\u007f]+"], # D.D + Japanese text
    }

    def is_likely_heading(block, prev_block=None):
        if not block['text'].strip():
            return False

        # Rule 1: Font size and bold status
        if block.get('is_bold', False) and block.get('font_size') in font_to_level:
            return True

        # Rule 2: Check for common patterns (can indicate heading even if font style isn't primary)
        text_lower = block['text'].strip()
        for level_key, patterns in heading_patterns.items():
            for pattern in patterns:
                if re.match(pattern, text_lower, re.IGNORECASE):
                    return True # Or assign a specific level based on pattern_key
        
        # Rule 3: Vertical spacing (needs context from previous block)
        if prev_block and block['page'] == prev_block['page']:
            vertical_gap = prev_block['y0'] - block['y1'] # Assuming y increases upwards
            # A significantly larger gap than normal text lines
            if vertical_gap > (prev_block['line_height'] * 1.5 if prev_block['line_height'] else 10): # Adjust threshold
                 # Combine with some text property (e.g., text is capitalized, short)
                if len(text_lower.split()) < 10 and text_lower == text_lower.title():
                    return True
        return False

    current_h1 = None
    current_h2 = None
    for i, block in enumerate(text_blocks_with_properties):
        prev_block = text_blocks_with_properties[i-1] if i > 0 else None
        
        if is_likely_heading(block, prev_block):
            level = None
            text = block['text'].strip()
            
            # Refined logic for assigning H1, H2, H3 based on combined cues
            # Prioritize larger font sizes for higher levels
            if block.get('font_size') == level_font_map.get("H1") and block.get('is_bold', False):
                level = "H1"
            elif block.get('font_size') == level_font_map.get("H2") and block.get('is_bold', False):
                level = "H2"
            elif block.get('font_size') == level_font_map.get("H3") and block.get('is_bold', False):
                level = "H3"
            else: # Fallback to pattern matching if font size isn't clear
                for lvl, patterns in heading_patterns.items():
                    for pattern in patterns:
                        if re.match(pattern, text, re.IGNORECASE):
                            level = lvl.replace("_JP", "") # Assign generic H1/H2/H3
                            break
                    if level: break
            
            if level:
                outline.append({
                    "level": level,
                    "text": text,
                    "page": block['page']
                })
    return outline

def process_pdf_for_outline(pdf_path):
    """
    Main function for Round 1A: extracts outline from a single PDF.
    """
    text_blocks = extract_text_and_properties_from_pdf(pdf_path)
    
    title = get_document_title(text_blocks)
    outline = detect_headings(text_blocks)
    
    return {"title": title, "outline": outline}

def get_document_sections_from_outline(pdf_path):
    """
    Parses PDF and organizes text content into sections and subsections
    based on detected headings. This is crucial for Round 1B.
    """
    text_blocks = extract_text_and_properties_from_pdf(pdf_path)
    detected_headings = detect_headings(text_blocks)

    sections = []
    current_h1_section = None
    current_h2_section = None

    # Helper function to check if a block matches a detected heading
    def block_is_heading(block, heading):
        return (block['text'].strip() == heading['text'].strip() and
                block['page'] == heading['page'] and
                abs(block['y0'] - text_blocks[text_blocks.index(block)]['y0']) < 2) # Check position precisely

    for i, block in enumerate(text_blocks):
        is_heading = False
        
        # Check if the current block is one of our detected headings
        for heading in detected_headings:
            if block_is_heading(block, heading):
                is_heading = True
                
                # Determine the level and update current sections
                if heading['level'] == "H1":
                    current_h1_section = {
                        "section_title": heading['text'],
                        "text": "",
                        "page_number": heading['page'],
                        "level": "H1",
                        "subsections": []
                    }
                    sections.append(current_h1_section)
                    current_h2_section = None # Reset H2 for new H1
                elif heading['level'] == "H2" and current_h1_section:
                    current_h2_section = {
                        "subsection_title": heading['text'],
                        "text": "",
                        "page_number": heading['page'],
                        "level": "H2"
                    }
                    current_h1_section['subsections'].append(current_h2_section)
                elif heading['level'] == "H3" and current_h2_section:
                    # Treat H3 as text belonging to the current H2 subsection
                    # Or create a nested subsection if needed by 1B output format
                    current_h2_section['text'] += " " + block['text'].strip()
                break # Matched a heading, move to next block
            if not is_heading:
                 # Add non-heading text to the most recently active section/subsection
             if current_h2_section:
                   current_h2_section['text'] += " " + block['text'].strip()
             elif current_h1_section:
                   current_h1_section['text'] += " " + block['text'].strip()
    
                # Clean up accumulated text (remove excessive whitespace)
             for section in sections:
                   section['text'] = ' '.join(section['text'].split()).strip()
             for subsection in section['subsections']:
                   subsection['text'] = ' '.join(subsection['text'].split()).strip()

            return sections