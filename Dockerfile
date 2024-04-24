FROM python:3.10-slim-buster
MAINTAINER "Rohan Rustagi"
WORKDIR /app
ADD . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
