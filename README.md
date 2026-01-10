```markdown
# SBFL Execution Pipeline

## Overview
The SBFL Execution Pipeline is a modular execution system that ingests a GitHub Python repository, extracts executable source files, runs spectrum-based fault localization (SBFL) on test coverage data, and highlights fault-prone code regions for analysis. The project focuses on translating SBFL research concepts into a reproducible, end-to-end debugging pipeline.

---

## Prerequisites
- Python 3.9+
- Node.js 16+ and npm
- Git
- pytest (used internally for execution and coverage generation)
- A public GitHub repository containing Python code and tests

---

## Directory Structure
```
sbfl-execution-pipeline/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── sbfl/
│   │   └── main.py
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── README.md
````
---

## Tech Stack
**Backend**
- FastAPI (Python) for lightweight execution orchestration
- GitHub REST APIs for repository ingestion

**Frontend**
- React (Vite) for fault localization visualization

**Database**
- None (stateless, transient execution model)

**Algorithms / Techniques**
- Spectrum-Based Fault Localization (SBFL)
- Ochiai suspiciousness metric

---

## Backend Setup

### Setup
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux / Mac
   venv\Scripts\activate      # Windows
````

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the FastAPI server:

   ```bash
   uvicorn main:app --reload
   ```

---

## Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Start the development server:

   ```bash
   npm run dev
   ```

---

## Usage

1. Open the frontend in your browser.
2. Provide a public GitHub repository URL containing Python source files.
3. The backend:

   * Fetches repository contents using GitHub APIs
   * Extracts Python source files
   * Executes tests and gathers execution data
   * Computes SBFL suspiciousness scores using the Ochiai metric
4. The frontend visualizes fault-prone regions by mapping suspiciousness scores to color gradients.

---

## Functional Features

* GitHub repository ingestion and Python source extraction
* Execution data processing for SBFL computation
* Suspiciousness score generation using the Ochiai metric
* Visual fault localization through color-based highlighting

---

## System Architecture

The system follows a pipeline-driven architecture where a FastAPI backend orchestrates repository ingestion, source code extraction, and fault localization computation. Given a GitHub repository URL, the backend fetches Python files, processes execution-related inputs, and computes suspiciousness scores using the Ochiai SBFL metric. Results are exposed through REST endpoints and consumed by a React frontend, which renders fault localization by mapping scores to visual highlights. The system is stateless and operates on on-demand analysis without persistent storage.

---

## Key Technical Decisions

* Adopted a stateless, pipeline-oriented backend design to ensure deterministic execution and simplify reasoning about fault localization results.
* Chose FastAPI to keep the backend lightweight and focused on orchestration rather than framework overhead.
* Selected the Ochiai metric as the initial SBFL technique due to its strong empirical performance and simplicity for validating end-to-end pipeline correctness.

---

## Most Complex Part

The most complex aspect of the project was ensuring correct end-to-end propagation of SBFL suspiciousness scores from backend computation to frontend visualization. This required maintaining a stable API contract, preserving numerical precision during serialization, and ensuring that frontend color-mapping logic accurately reflected backend-generated scores.

---

## Current Limitations

* Relies on pytest-based execution, which introduces runtime overhead and slows analysis for larger repositories.
* Validated only on relatively small GitHub repositories.
* Supports only single execution at a time with no concurrency.

---

## Future Improvements

* Introduce Docker-based containerized execution for safer and more predictable analysis.
* Add backend concurrency support to allow parallel analysis of multiple repositories.
* Extend ingestion support to private GitHub repositories through authenticated access.

---

## Summary

This project demonstrates how Spectrum-Based Fault Localization techniques can be translated from research papers into a structured, reproducible execution pipeline. By emphasizing clear separation of concerns, stateless execution, and deterministic analysis, the SBFL Execution Pipeline serves as a foundation for building more advanced automated debugging tools.

```
