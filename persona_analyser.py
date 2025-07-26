# persona_analyser.py
import json
import os
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- BONUS FEATURE: Multilingual Handling (Conceptual) ---
# For true multilingual support beyond simple keyword matching, you would
# integrate a robust, pre-trained multilingual embedding model here.
# Ensure it's compatible with CPU and fits the 1GB model size constraint.
# You would need to download and package this model in your Docker image.

# Example if using sentence-transformers (requires model download and copying to /app/models/):
# from sentence_transformers import SentenceTransformer
# try:
#     # Adjust path based on where you copy the model in your Dockerfile
#     MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2" # Example small multilingual model
#     # You MUST download this model manually and place its files in your 'models/' directory
#     # e.g., SentenceTransformer('/app/models/paraphrase-multilingual-MiniLM-L12-v2')
#     embedding_model = SentenceTransformer(os.path.join(os.getcwd(), 'models', MODEL_NAME))
#     print(f"Successfully loaded embedding model: {MODEL_NAME}")
# except Exception as e:
#     print(f"WARNING: Could not load embedding model. Ensure model files are in 'models/' and dependencies are installed. Error: {e}")
embedding_model = None # Start with None, load if model files are present and desired.
# To use embedding_model, you would uncomment the above block and ensure the model is downloaded locally.


def calculate_relevance_score(text_to_evaluate, persona_text, job_text, model=None):
    """
    Calculates a relevance score. Uses Sentence Embeddings if model is provided
    and loaded, otherwise falls back to TF-IDF Cosine Similarity.
    """
    combined_query = persona_text + " " + job_text.strip()
    
    if not combined_query or not text_to_evaluate:
        return 0.0

    if model:
        try:
            query_embedding = model.encode(combined_query, convert_to_tensor=True).cpu().numpy()
            text_embedding = model.encode(text_to_evaluate, convert_to_tensor=True).cpu().numpy()
            score = cosine_similarity(query_embedding.reshape(1, -1), text_embedding.reshape(1, -1))[0][0]
            return float(score)
        except Exception as e:
            print(f"Error using embedding model, falling back to TF-IDF. Error: {e}")
            model = None # Disable embedding model for subsequent calls

    # Fallback to TF-IDF
    vectorizer = TfidfVectorizer().fit([combined_query, text_to_evaluate])
    vectors = vectorizer.transform([combined_query, text_to_evaluate])
    score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    return float(score)

def refine_subsection_text(subsection_text, persona_text, job_text, model=None, num_sentences=2):
    """
    Refines (summarizes) a subsection text to highlight relevant parts.
    This is an extractive summarization based on relevance to persona/job.
    """
    sentences = [s.strip() for s in subsection_text.split('.') if s.strip()]
    if not sentences:
        return ""

    combined_query = persona_text + " " + job_text.strip()
    if not combined_query:
        return sentences[0] if sentences else "" # Return first sentence if no query

    if model:
        try:
            query_embedding = model.encode(combined_query, convert_to_tensor=True).cpu().numpy()
            sentence_embeddings = model.encode(sentences, convert_to_tensor=True).cpu().numpy()
            similarities = cosine_similarity(query_embedding.reshape(1, -1), sentence_embeddings)[0]
        except Exception as e:
            print(f"Error using embedding model for refinement, falling back to TF-IDF. Error: {e}")
            model = None # Disable embedding model for subsequent calls

        if not model: # Fallback to TF-IDF for sentences
         vectorizer = TfidfVectorizer().fit([combined_query] + sentences)
         query_vector = vectorizer.transform([combined_query])
         sentence_vectors = vectorizer.transform(sentences)
         similarities = cosine_similarity(query_vector, sentence_vectors)[0]

    # Get indices of top N sentences based on similarity
    top_sentence_indices = np.argsort(similarities)[-num_sentences:][::-1]
    
    # Reconstruct refined text in original order of sentences
    refined_sentences = [sentences[i] for i in sorted(top_sentence_indices)]
    
    return ". ".join(refined_sentences) + ("." if refined_sentences and not refined_sentences[-1].endswith('.') else "")


def process_document_collection(challenge_input, get_sections_func):
    """
    Main function for Round 1B: processes multiple PDFs based on persona and job.
    """
    documents_info = challenge_input['documents']
    persona_info = challenge_input['persona']
    job_to_be_done_info = challenge_input['job_to_be_done']

    input_documents_metadata = []
    extracted_sections_output = []
    subsection_analysis_output = []

    persona_combined_text = persona_info['role'] + " " + persona_info.get('description', '') # Add description if present
    job_combined_text = job_to_be_done_info['task']

    for doc_item in documents_info:
        filename = doc_item['filename']
        title = doc_item['title'] # You might want to get this from the PDF directly for robustness
        pdf_path = os.path.join("/app/input", filename) 
        
        input_documents_metadata.append({"filename": filename, "title": title})

        # Get sections from PDF using the function from outline_extractor
        sections = get_sections_func(pdf_path) 
        
        for section in sections:
            # Only include sections if they have a title and some text
            if not section.get('section_title') or not section.get('text'):
                continue

            section_relevance_score = calculate_relevance_score(
                section['text'], persona_combined_text, job_combined_text, embedding_model
            )
            
            extracted_sections_output.append({
                "document": filename,
                "page_number": section['page_number'],
                "section_title": section['section_title'],
                "importance_rank": section_relevance_score
            })
    
    # Process subsections from the section's content
            # The get_document_sections_from_outline might need adjustment to give distinct subsections
            # For simplicity, if subsections are not parsed distinctly, you might treat parts of section['text']
            # as sub-sections for refinement.
            
            # --- BONUS FEATURE: Granular Subsection Extraction & Ranking ---
            # If your get_sections_func provides deeper nesting or explicit sub-sections,
            # iterate through them. Otherwise, dynamically break down the section's text.
            # For this example, let's assume get_sections_func provides 'subsections' list.
            
            # If sub_sections are directly provided by get_sections_func
            if section.get('subsections'):
                for sub_section in section['subsections']:
                    if not sub_section.get('text'):
                        continue
                    refined_text_content = refine_subsection_text(
                        sub_section['text'], persona_combined_text, job_combined_text, embedding_model
                    )
                    subsection_analysis_output.append({
                        "document": filename,
                        "page_number": sub_section['page_number'],
                        "refined_text": refined_text_content
                    })
            else: # If get_sections_func only gives main sections, you can try to break them down
                # Basic sentence-level "sub-section" for refinement
                sentences_in_section = [s.strip() for s in section['text'].split('.') if s.strip()]
                if sentences_in_section:
                    # Treat the entire section text as one large "subsection" for refinement
                    refined_text_content = refine_subsection_text(
                        section['text'], persona_combined_text, job_combined_text, embedding_model, num_sentences=5
                    ) # Get more sentences for a larger block
                    if refined_text_content:
                        subsection_analysis_output.append({
                            "document": filename,
                            "page_number": section['page_number'], # Use section's page
                            "refined_text": refined_text_content
                        })


    # Sort extracted sections by their relevance score (descending) and assign final ranks
    # This fulfills "proper stack ranking" for Section Relevance bonus.
    extracted_sections_output.sort(key=lambda x: x['importance_rank'], reverse=True)
    for i, item in enumerate(extracted_sections_output):
        item['importance_rank'] = i + 1 

    output_json = {
        "metadata": {
            "input_documents": input_documents_metadata,
            "persona": persona_info,
            "job_to_be_done": job_to_be_done_info,
            "processing_timestamp": datetime.now().isoformat()
        },
        "extracted_sections": extracted_sections_output,
        "subsection_analysis": subsection_analysis_output
    }

    return output_json
 