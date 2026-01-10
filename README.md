Project Name

SBFL Execution Pipeline

One-line Problem Statement

A modular SBFL execution pipeline that ingests a GitHub Python repository, extracts executable source files, runs spectrum-based fault localization on test coverage data, and highlights fault-prone code regions for analysis.

Target Users

Developers and researchers building automated debugging or fault-localization tools, particularly those experimenting with Spectrum-Based Fault Localization (SBFL) techniques on Python codebases.

Why this project exists

Existing SBFL research largely focuses on benchmarking algorithms in isolation, but offers limited guidance on how to translate those ideas into an end-to-end, reproducible debugging tool. This project bridges that gap by turning SBFL concepts from research papers into a concrete execution pipeline that handles repository ingestion, execution data processing, and fault visualization in a structured software-engineering manner.

Tech Stack

Backend: FastAPI (Python) for building a lightweight execution and orchestration API

Frontend: React (Vite) for visualizing fault localization results

Database: None; the pipeline operates on transient execution data without persistence

Algorithms / Techniques

Spectrum-Based Fault Localization (SBFL)

Ochiai suspiciousness metric

GitHub REST APIs for repository ingestion and source code extraction

Core Features

Repository ingestion pipeline that accepts a GitHub repository URL, extracts Python source files, and prepares them for analysis.

Execution data processing and SBFL computation using the Ochiai metric to assign suspiciousness scores to code elements.

Visual fault localization that maps suspiciousness scores to color gradients, highlighting fault-prone regions in the source code.

System Architecture (high-level)

The system follows a pipeline-driven architecture where a FastAPI backend orchestrates repository ingestion, source code extraction, and fault localization computation. Given a GitHub repository URL, the backend fetches Python files using GitHub APIs, processes execution-related inputs, and computes suspiciousness scores using the Ochiai SBFL metric. The results are exposed via REST endpoints and consumed by a React frontend, which renders fault localization by mapping scores to visual highlights in the source code. The system is stateless and operates on on-demand analysis without persistent storage.

Key Technical Decisions

Chose a stateless, pipeline-oriented backend design to ensure deterministic execution and simplify reasoning about fault localization results without managing persistent state.

Used FastAPI as the backend framework to keep the execution layer lightweight and focused on orchestration of ingestion and analysis steps rather than heavy framework abstractions.

Selected the Ochiai metric as the initial SBFL technique due to its strong empirical performance in fault localization research and its simplicity for validating end-to-end pipeline correctness.

Most complex part of the project

The most complex part was ensuring correct end-to-end propagation of SBFL suspiciousness scores from the backend computation layer to the frontend visualization layer. This required defining a stable API contract, preserving numerical precision during serialization, and ensuring that the frontend’s color-mapping logic accurately reflected backend-generated scores without introducing interpretation errors.

Current Limitations

The pipeline relies on pytest-based execution, which introduces non-trivial runtime overhead and results in slower analysis for larger codebases.

The system is currently validated only on relatively small GitHub repositories and has not been optimized for large, multi-module projects.

The backend operates in a single-execution mode without concurrency support, limiting simultaneous analyses to one repository at a time.

What you would improve with more time

Introduce containerized code execution using Docker to isolate repository analysis, improve execution safety, and enable more predictable performance characteristics.

Add concurrency support in the backend to allow parallel analysis of multiple repositories, improving throughput and enabling multi-user usage.

Extend the ingestion layer to support private GitHub repositories through authenticated access while preserving security boundaries.

How to Run Locally

Clone the repository

git clone <repository-url>
cd <project-directory>


Backend setup

python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn main:app --reload


Frontend setup

cd frontend
npm install
npm run dev


Usage

Provide a public GitHub repository URL through the frontend.

The backend ingests Python source files, runs SBFL analysis using the Ochiai metric, and returns suspiciousness scores.

The frontend visualizes fault-prone code regions based on the computed scores.