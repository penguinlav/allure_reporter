# Allure Reporter
A tool for embedding Allure reports in ci pipeline.

The utility stores the results of previous starts for each revision to render all retries. The history of reports is preserved within the project branch.

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
uvicorn allure_reporter.main:app --env-file .env
```

#### Example ci job
Suppose we have an image with tests that run in the image.
```
test:
  stage: testing
  image: image_with_pytests
  variables:
    GIT_STRATEGY: none
  before_script:
    - rm -rf page
  script:
    - py.test --alluredir=allure-results /path_to_package_with_pytests/tests
  after_script:
    - # branch name, project.. you can get for environment from script
    - python /path_to_package_with_pytests/scripts/generate_report.py --input=allure-results --output=report.zip  # write for yourself
    - unzip -q report.zip -d page
    - # script for sending page/mail.html with results for subscribers
  artifacts:
    paths:
      - page/
    expire_in: 1 week
    when: always
```
Then you will be able to see the report in artifacts with `Browse` button.
