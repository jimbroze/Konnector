if ! poetry run pytest tests -m "not integration"
then
  echo "Unit tests failed. Exiting..."
  exit
fi

poetry run pytest tests -m "integration"
