poetry run black konnector tests --preview

# stop the build if there are Python syntax errors or undefined names.  The GitHub editor is 127 chars wide
poetry run flake8 --count --select=E9,F63,F7,F82 --max-line-length=88 --extend-ignore=E203 --show-source --statistics konnector

# exit-zero treats all errors as warnings.
poetry run flake8 --count --exit-zero --max-line-length=88 --extend-ignore=E203 --statistics konnector

poetry run pytest -vv