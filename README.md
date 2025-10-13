# Chicken Chicken Banana – Beauty Product Assistant with LLM

A multi-page Streamlit application for answering cosmetic product inquiries, analyzing reviews with Tool Calling, and retrieving answers using RAG.

This project was developed for the course 204203 COMPUTER SCIENCE TECHNOLOGY

## Table Of Contents
- [Installation and Setup](#installation-and-setup)
- [How to run](#how-to-run)
- [Features](#features)
- [Project Structure](#project-structure)
- [Data & Schemas](#data--schemas)
- [RAG Components](#rag-components)
- [Contributors](#contributors)

## Installation and Setup
It is recommended to use Python 3.10+ and create a virtual environment before installing the dependencies.

```sh
# 1) Create and activate a virtual environment.
python3 -m venv .venv
source .venv/bin/activate # On Windows: venv\Scripts\activate

# 2) Install the project dependencies
pip install -r requirements.txt
```

## How to run
The app runs with Streamlit, and the starting page is Home.py.

```sh
streamlit run Home.py
```

When successfully running, you can access other pages from the sidebar, such as product pages and the Business Analyze page.

## Features
- Chat/Completion: For asking and answering product-related questions (uses data in data/ and RAG)
- Product Review Analysis: Analyze product reviews in reviews/ to summarize real user perspectives
- Product Pages: Separate pages by category, e.g., Brush, Concealer, Cushion, Lip, Mascara
- Business Analyze Page: View business insights
- RAG Module (RAG/): For document ingestion and querying internal knowledge

## Project Structure

*Main files and folders to know*
```
/assets/                 # Images for the UI
/data/                   # Product, FAQ, and complaint data in JSON files
/pages/                  # Streamlit multi-page app
/schemas/                # Data schemas for products and reviews (JSON & Python)
Home.py                  # Streamlit home page
config.py                # General project configuration
requirements.txt         # List of dependencies
```

## Data & Schemas
- Product/FAQ/Complaint data is stored in the data/ folder, separated by category and product ID, e.g., product_C001.json, faq_B001.json
- Data structure is defined by schemas in schemas/, e.g., product_schema.json, review_schema.json

## RAG Components
- ingest.py: For ingesting text from corpus.jsonl or other text files
- index.py: For creating/updating the knowledge index
-	query.py: For querying the knowledge base and generating answers (knowledge-based Q&A)

Example usage of RAG (run as needed before launching the app):
```sh
# Ingest documents into the corpus
python ingest.py

# Create or update the knowledge index
python index.py

# (Optional) Test querying the knowledge base
python query.py
```

## Contributors
* [Natthanicha Rodaree](https://github.com/Jellyfrist) 670510653 - Frontend and Backend
* [Noorfadilah Prayunto](https://github.com/n00raw) 670510666 - Backend
* [Wannee Thanomworrakul](https://github.com/cutecupca-ke) 670510679 - Backend
* [Poramet Thammakrong](https://github.com/Poramet-tham) 670510716 - Frontend

## Slide Presentation
- https://www.canva.com/design/DAG1d7W8Bbw/Uu4mZ3VKYfOVsS3FU2WxFg/edit?utm_content=DAG1d7W8Bbw&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton
