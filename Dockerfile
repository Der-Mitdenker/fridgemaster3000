FROM python:3.11.2-slim-buster
WORKDIR /project-folder
COPY ./requirements.txt .
RUN python -m pip install --upgrade pip && python -m pip install --upgrade -r requirements.txt
COPY /_default ./apps/_default

# Remove database folders and Python caches
RUN rm -rf apps/_default/databases/ \
    && find . -type d -name "__pycache__" -exec rm -rf {} +
RUN touch apps/__init__.py
CMD ["py4web", "run", "apps", "--host=0.0.0.0"]
