Project Title: [Adobe, e.g., Smart PDF Outline & Insights]
Overview
This project is designed for Round 1 of Adobe's "Connecting the Dots" Hackathon. It focuses on extracting and analyzing structured data from PDFs, and is split into two primary components:

Round 1A – Understand Your Document: Extracts the document title and a hierarchical structure (H1, H2, H3 headings) including their page numbers.

Round 1B – Persona-Driven Document Intelligence: Based on a specified persona and job-to-be-done, it analyzes multiple documents to identify and rank relevant sections and produces a refined summary of key sub-sections.

Features
Round 1A:
Heading Detection: Uses heuristics such as font size, bold formatting, spacing, and common patterns to classify headings into H1, H2, and H3.

Title Identification: Detects the document’s main title.

JSON Output Format: Produces structured output with a nested JSON format.

Bonus - Multilingual Support (Basic): Incorporates initial support for recognizing heading patterns in languages like Japanese via simple matching. (Full multilingual NLP would require a specialized model, if allowed within size limits.)

Round 1B:
Relevance Calculation Based on Persona: Scores each section’s relevance using persona and task definitions.

Section Prioritization: Orders document sections by calculated relevance (importance_rank).

Granular Subsection Analysis: Extracts refined summaries (extractive) for relevant sub-sections, contributing to the bonus criterion for quality extraction and ranking.

Challenge-Compatible Output: Generates results in the required challenge1b_output.json structure.

Setup Instructions
Prerequisites:
Docker Desktop: Install from https://www.docker.com/products/docker-desktop/

Git (Optional): For cloning repositories

Steps to Run the Project:
Clone the Repository or Prepare Files:

bash
Copy
Edit
git clone [your-repo-url]
cd [your-project-name]
If not using Git, ensure your working directory includes:

main.py, pdf_parser.py, outline_extractor.py, persona_analyser.py

requirements.txt, Dockerfile, README.md

Optionally, a models/ directory for any pre-trained NLP models

Prepare Input Folder:

Create an input/ folder.

For Round 1A: Place your .pdf files inside input/.

For Round 1B: Include both the .pdf files and a challenge_input.json file in input/.

Example of challenge_input.json:

json
Copy
Edit
{
  "challenge_info": {
    "challenge_id": "round_1b_001",
    "test_case_name": "Travel Planner",
    "description": "France Travel"
  },
  "documents": [
    {"filename": "South of France - Cities.pdf", "title": "South of France - Cities"},
    {"filename": "South of France - Cuisine.pdf", "title": "South of France - Cuisine"}
  ],
  "persona": {"role": "Travel Planner"},
  "job_to_be_done": {"task": "Plan a trip of 4 days for a group of 10 college friends."}
}
Create Output Directory:

Add an empty output/ folder to the project root.

Build Docker Image:
Navigate to the project directory and run:

bash
Copy
Edit
docker build --platform linux/amd64 -t adobe-hackathon-solution:latest .
--platform linux/amd64: Ensures platform compatibility.

-t adobe-hackathon-solution:latest: Tags the Docker image.

.: Uses the Dockerfile in the current directory.

Run the Container:

bash
Copy
Edit
docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" --network none adobe-hackathon-solution:latest
--rm: Removes the container after it finishes.

-v "$(pwd)/input:/app/input": Mounts your local input/ directory.

-v "$(pwd)/output:/app/output": Mounts your local output/ directory.

--network none: Enforces offline execution (mandatory).

Inspect Output:
After execution completes:

For Round 1A: Output JSON files for each input PDF will appear in output/.

For Round 1B: You will find a challenge1b_output.json file.

Troubleshooting
Issue	Solution
docker: command not found	Ensure Docker is installed and added to your PATH
Error processing PDF	Review pdf_parser.py or outline_extractor.py for logic issues.
Missing challenge_input.json	Check that your input folder is correctly structured.
Model not found	Manually download and place required models in models/ and verify paths.
Slow performance	Profile and optimize parsing logic and NLP calls. Use lightweight models for Round 1B.