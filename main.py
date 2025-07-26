# main.py
import os
import json
import sys
from datetime import datetime

# Import your modules
from outline_extractor import process_pdf_for_outline, get_document_sections_from_outline
from persona_analyser import process_document_collection

# Define input and output directories as per Docker setup
INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

def run_round_1a():
    print("Running Round 1A: Understand Your Document.")
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print("No PDF files found in the input directory for Round 1A.")
        return

    for pdf_filename in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, pdf_filename)
        output_json_filename = pdf_filename.replace(".pdf", ".json")
        output_json_path = os.path.join(OUTPUT_DIR, output_json_filename)

        print(f"Processing PDF for Round 1A: {pdf_path}")
        try:
            result_1a = process_pdf_for_outline(pdf_path)
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(result_1a, f, indent=2, ensure_ascii=False)
            print(f"Generated output for {pdf_filename} to {output_json_path}")
        except Exception as e:
            print(f"Error processing {pdf_filename}: {e}")
            # Consider logging errors to a file or standard error for debugging

def run_round_1b():
    print("Running Round 1B: Persona-Driven Document Intelligence.")
    challenge_input_path = os.path.join(INPUT_DIR, "challenge_input.json")

    if not os.path.exists(challenge_input_path):
        print(f"Error: challenge_input.json not found at {challenge_input_path}. Cannot run Round 1B.")
        return

    try:
        with open(challenge_input_path, 'r', encoding='utf-8') as f:
            challenge_input_data = json.load(f)
        
        output_data = process_document_collection(challenge_input_data, get_document_sections_from_outline)
        
        output_filename = "challenge1b_output.json" # As specified in documentation
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Round 1B processing complete. Output saved to {output_path}")

    except json.JSONDecodeError as e:
        print(f"Error decoding challenge_input.json: {e}. Please check JSON format.")
    except Exception as e:
        print(f"An unexpected error occurred during Round 1B processing: {e}")

def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Determine which challenge round to run.
    # The hackathon likely provides test cases that trigger either 1A or 1B.
    # A common way to differentiate:
    # If challenge_input.json is present and well-formed, it's Round 1B.
    # Otherwise, it defaults to Round 1A, processing all PDFs.

    challenge_input_json_exists = False
    try:
        with open(os.path.join(INPUT_DIR, "challenge_input.json"), 'r') as f:
            # Try to load to ensure it's valid JSON for 1B
            json.load(f)
        challenge_input_json_exists = True
    except (FileNotFoundError, json.JSONDecodeError):
        challenge_input_json_exists = False
    except Exception as e:
        print(f"Warning: Could not check challenge_input.json due to {e}. Proceeding as if not 1B.")
        challenge_input_json_exists = False # Treat as not 1B if there's any read/parse error

    if challenge_input_json_exists:
        run_round_1b()
    else:
        run_round_1a()

if name == "main":
    main()