# Resume draft — Thailand Regional Banking Intelligence

Use this under **Projects** (or **Academic Projects** if submitted as coursework), not Work Experience. Replace the date and add a public repository link only after publishing the project. Keep only technologies and design choices you can explain in an interview.

**Thailand Regional Banking Intelligence | Data Engineering & Analytics Project**  
*Python · PostgreSQL · Apache Airflow · Grafana · Streamlit · FastAPI · LangChain · LangGraph · Gemini API*

Business question behind the project: **Which provinces merit a closer banking-market study when loan/deposit growth, branch coverage, and economic context are considered together?** The public datasets needed to compare them have different identifiers, time periods, and release dates. This is a project framing, not a claim that a bank commissioned or used the analysis.

- Addressed a provincial market-screening challenge—comparing loan/deposit trends and branch coverage alongside economic context—by integrating five real public-data sources, including the Bank of Thailand and World Bank REST API, into a 77-province × 25-month warehouse (1,925 analytical rows).
- Built an Airflow-orchestrated ETL pipeline with province-code mapping, release-aware temporal joins, source lineage, and validation; delivered 13 Grafana panels and an interactive regional market-screening dashboard.
- Developed a constrained Thai natural-language analytics interface using Gemini and LangGraph: structured `QueryPlan` output, allowlisted SQL generation, read-only database access, and result tables/charts with source disclosure. Verified one live Gemini end-to-end query and 38 automated tests.

Shorter version for a one-page resume:

- Built a provincial banking market-screening view to compare growth, branch coverage, and economic context, integrating five public sources into a 1,925-row warehouse and delivering 13 Grafana panels plus a Streamlit dashboard.
- Added a constrained Gemini/LangGraph natural-language query flow that returns validated SQL, tables, charts, and provenance; verified 38 automated tests and one live LLM query.

Accuracy notes: The project uses public aggregate data, not customer or individual-bank records. The Airflow DAG is configured for daily runs, but a continuous month of scheduled operation has not been verified. One successful live Gemini query does not establish chatbot accuracy across all question types. Do not claim bank deployment, business impact, or production use.
