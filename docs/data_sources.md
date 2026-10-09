# Data source and visibility policy

## Prototype status

The bundled fixture `data/synthetic/sample_records.json` is synthetic and intentionally combines two source types (`synthetic_news_feed` and `synthetic_social_feed`) to demonstrate multi-source normalization. It is not evidence of a live connection to GDELT, NewsAPI, X/Twitter or any other provider.

## Candidate real sources to verify before enabling

- GDELT DOC 2.0 / GKG: https://www.gdeltproject.org/data.html — potential news/context source; preserve source URL and publication time, and document endpoint/query parameters.
- FinancialPhraseBank: https://huggingface.co/datasets/financial_phrasebank — candidate labelled financial-sentence dataset for sentiment evaluation; verify licence and exact dataset version before redistribution.
- NewsAPI Everything: https://newsapi.org/docs/endpoints/everything — API access is subject to plan and terms; do not assume the developer/free plan permits public production use or redistribution.
- Financial Tweets candidate: https://www.kaggle.com/datasets/davidwallach/financial-tweets — inspect the current dataset card, licence, provenance and columns before using or committing any records.

## Inclusion checklist

For every real source, record the exact endpoint/dataset version, access date, query/filter, licence/terms URL, attribution, fields used, retention constraints, and whether raw records may be redistributed. Publicly accessible does not mean redistributable. Do not commit credentials or data with unclear permission.

## Implemented ingestion adapters

- `source_adapters/gdelt.py` calls the GDELT DOC 2.0 Article List endpoint in JSON mode. It normalizes article titles (headline-only text), `seendate`, URL and available source metadata. See the [official GDELT DOC API documentation](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/). Headlines may be incomplete evidence; inspect the linked publisher page when permitted. The adapter writes results under ignored `data/runtime/` by default so retrieved content is not accidentally committed.
- `source_adapters/csv_text.py` accepts a local CSV and explicit column mappings. Use it for a second source, such as a properly licensed financial tweet dataset, only after checking the exact dataset card/licence. The code does not download or redistribute that dataset automatically.

Example commands are in the main README. Live calls are not required for unit tests.
