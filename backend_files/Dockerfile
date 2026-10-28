FROM python:3.13.15-slim
WORKDIR /app
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ENV HF_HOME=/app/huggingface
RUN python -c "from langchain_huggingface import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='HarishMaths/Hotel-Policy-Embedding', model_kwargs={'device':'cpu'}, encode_kwargs={'normalize_embeddings':True})"
COPY . .
ENV TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1
EXPOSE 7860
CMD ["gunicorn", "-w", "1", "--timeout", "300", "-b", "0.0.0.0:7860", "app:rag_api"]
