# Allure Reporter
A tool for embedding Allure reports in ci pipeline.

The utility stores results of previous starts for each revision to render all retries. The history of reports is preserved within the project branch.

Report generation example.
```
export BRANCH=branch_name
export REVISION=revision_name
export PROJECT=project_name
export URL_EMAIL_REPORT=http%3A%2F%2Flocalhost%3A8080%2F
export FILE_RESULTS_PATH=results.zip

# request returns generated report in zip archive
curl -i "http://localhost:8000/api/generate?branch=$BRANCH&revision=$REVISION&project=$PROJECT&url_email_report=$URL_EMAIL_REPORT" -X POST --form results=@$FILE_RESULTS_PATH --output report.zip
```

#### Install

Edit environment variables in file `.env`. Install dependencies:
```
poetry install --no-dev
```
#### Running
```
poetry shell
uvicorn allure_reporter.main:app --env-file .env --reload --reload-dir allure_reporter
```
