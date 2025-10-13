# Project Guide: Beauty Product Assistant with LLM

## Repository Structure

- `Home.py`: Main entry point for the Streamlit application.
- `README.md`: Project overview and basic instructions.
- `requirements.txt`: Python dependencies for the project.
- `config.py`: General project configuration settings.
- `pages/`: Contains multi-page Streamlit application pages:
  - `1_Filter Brush.py`: Filter Brush product page.
  - `2_Fluffy Cloud Concealer & Corrector.py`: Concealer product page.
  - `3_Velvet Cloud Cushion.py`: Cushion product page.
  - `4_Syrup Glossy Lip.py`: Lip product page.
  - `5_Truebrow Mybrow Mascara.py`: Mascara product page.
  - `Business Analyze.py`: Business analysis dashboard.
- RAG (Retrieval-Augmented Generation) components:
  - `ingest.py`: Document ingestion for knowledge base.
  - `index.py`: Knowledge index creation and management.
  - `query.py`: Knowledge base querying functionality.
  - `corpus.jsonl`: Knowledge corpus data.   
- `data/`: Product, FAQ, and complaint data:
  - Product data: `product_*.json` files by category.
  - FAQ data: `faq_*.json` files by category.
  - Complaint data: `complaint_*.json` files by category.
- `schemas/`: Data structure definitions:
  - `product_schema.json` & `product_schema.py`: Product data schema.
  - `review_schema.json` & `review_schema.py`: Review data schema.
- `reviews/`: Product review CSV files for analysis.
- `assets/`: UI images and graphics.
- `tc_*.py`: Tool calling modules for various functionalities.

## Setup Instructions

1. **Install dependencies:**
   ```bash
   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install requirements
   pip install -r requirements.txt
   ```

2. **Prepare RAG knowledge base (optional but recommended):**
   ```bash
   # Ingest documents into corpus
   python RAG/ingest.py
   
   # Create knowledge index
   python RAG/index.py
   ```

3. **Run the application:**
   ```bash
   streamlit run Home.py
   ```

## Git Flow & Commands

- **Branching:**
  - Work on feature branches (e.g., `feature/product-page-update`) and merge into `main` via pull requests.
- **Basic commands:**
  ```bash
  git checkout -b feature/your-feature   # Create and switch to a new branch
  git add .                             # Stage changes
  git commit -m "Describe your changes" # Commit changes
  git push origin feature/your-feature  # Push branch to remote
  git pull origin main                  # Pull latest changes from main
  git merge feature/your-feature        # Merge your branch into main
  ```
- **Pull Requests:**
  - Open a PR for code review before merging to `main`.

## Tool Calling & RAG Integration

- **Tool Calling Modules:**
  - `tc_analyze_review.py`: Analyzes product reviews for insights.
  - `tc_complete.py`: Handles completion tasks.
  - `tc_get_product_info.py`: Retrieves product information.
- **RAG Components:**
  - When adding new knowledge sources:
    - Add documents to `corpus.jsonl` or update `ingest.py`.
    - Re-run `index.py` to update the knowledge index.
    - Test queries using `query.py`.
- **Data Management:**
  - Product data follows schemas defined in `schemas/`.
  - Review data is stored in CSV format in `reviews/`.
  - All data files should follow the naming convention: `{type}_{category}{id}.{extension}`.

## Development Guidelines

- **Adding New Product Pages:**
  - Create new page files in `pages/` directory.
  - Follow the naming convention: `{number}_{Product Name}.py`.
  - Import necessary modules and follow existing page structure.
- **Data Schema Updates:**
  - Update both JSON and Python schema files in `schemas/`.
  - Ensure data files in `data/` conform to updated schemas.
- **RAG Enhancement:**
  - Document new knowledge sources in code comments.
  - Test query functionality after index updates.
  - Maintain corpus quality and relevance.

---
For any questions, refer to the `README.md` or contact the project maintainers.
