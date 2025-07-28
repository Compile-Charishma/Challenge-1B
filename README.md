#  Adobe India Hackathon - Round 1B

This project processes PDF collections to extract and rank relevant sections based on a persona and job-to-be-done, outputting results in JSON format. It is designed for tasks such as travel planning and menu preparation using structured PDF data.

## Preparing Collections

Before running the project, make sure to set up your collections as follows:

- Create a folder for each collection you want to process (e.g., `collection1`, `collection2`, `collection3`, ...).
- Inside each collection folder, add a `PDFs` subfolder and place all related PDF files there.
- Add an `input.json` file in the collection folder, listing the PDFs and specifying the persona and job to be done.
- When you run the project, it will generate an `output.json` file in the same collection folder with the results.

## Project Structure

- `persona_main.py` — Main script to process collections
- `requirements.txt` — Python dependencies
- `collection1/`, `collection2/`, `collection3/` — Example data collections with PDFs and input/output JSON files
- `utils/` — Utility scripts for PDF layout extraction and heading classification
- `Dockerfile` — Container setup for reproducible runs

## Prerequisites

- Docker installed ([Download Docker](https://www.docker.com/get-started/))
- Python 3.11+ (if running locally)

## Usage

### 1. Run the Project in Docker

#### Windows (PowerShell)
```powershell
docker run --rm -v ${PWD}:/app challenge-1b
```

#### Linux/Mac
```bash
docker run --rm -v $(pwd):/app challenge-1b
```

This mounts your project directory into the container so all PDFs and data files are accessible.

## Output

- Results are written to each collection's `output.json` file.
- See `collection1/output.json`, `collection2/output.json`, `collection3/output.json` for examples.

## Local Run (Optional)

If you prefer to run without Docker:

```bash
pip install -r requirements.txt
python persona_main.py
```