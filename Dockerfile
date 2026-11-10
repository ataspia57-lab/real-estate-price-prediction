FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Train at build time if no model was committed
RUN test -f models/model.joblib || (python data/generate_dataset.py && python -m src.train --no-eda)
ENV PORT=8000
EXPOSE 8000
CMD gunicorn -w 2 -b 0.0.0.0:$PORT "app.server:create_app()"
