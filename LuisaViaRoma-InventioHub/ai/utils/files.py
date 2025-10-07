import os
import tempfile
from typing import List

import requests
from datauri import DataURI
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_community.document_loaders import TextLoader
from pydantic import BaseModel, Field

if not os.getenv('BACKEND_API_BASE_URL'):
    raise RuntimeError("Devi impostare la variabile d'ambiente BACKEND_API_BASE_URL")

if not os.getenv('BACKEND_API_TOKEN'):
    raise RuntimeError("Devi impostare la variabile d'ambiente BACKEND_API_TOKEN")

# Estensioni per immagini e per documenti testuali
# TODO Limitare a queste estensioni il caricamento dei file
IMAGE_EXTENSIONS = set(os.getenv("AI_ALLOWED_IMAGE_EXTENSIONS", 'jpg,jpeg,png,webp').split(","))
DOCUMENT_EXTENSIONS = set(os.getenv("AI_ALLOWED_DOCS_EXTENSIONS", 'txt,pdf,docx,md').split(","))

TXT_DOCUMENTS_EXTENSIONS = {'txt', 'md'}


class S3File(BaseModel):
    name: str = Field(default='', description="The name of the file to upload.")
    key: str = Field(default='', description="The key of the file to upload.")


def filter_s3_files(files: List[S3File]) -> (List[S3File], List[S3File]):
    """
        Restituisce due liste:
          - documents: i file con estensione da DOCUMENT_EXTENSIONS
          - images: i file con estensione da IMAGE_EXTENSIONS
        Eventuali file con estensione non riconosciuta vengono messi in documents.
        """
    documents: List[S3File] = []
    images: List[S3File] = []

    for file in files:
        # Estrae l'estensione (incluso il punto) e la normalizza in minuscolo
        _, ext = os.path.splitext(file.name)
        ext = ext.lower().strip(".")

        if ext in IMAGE_EXTENSIONS:
            images.append(file)
        elif ext in DOCUMENT_EXTENSIONS:
            documents.append(file)
        else:
            # documents.append(file)
            continue

    return documents, images


async def load_and_convert(file: S3File, only_text: bool = False,
                           file_format: str | None = None) -> DataURI | str | None:
    """Carica e converte file in base al tipo"""

    params = {}

    if file_format:
        params = {"file_format": file_format}

        # 1) Scarico i bytes
        resp = requests.get(
            f'{os.getenv('BACKEND_API_BASE_URL')}/get_s3_file/{file.key}/{file.name}/',
            headers={'TaskToken': os.getenv('BACKEND_API_TOKEN')}, params=params
        )
    else:
        resp = requests.get(
            f'{os.getenv('BACKEND_API_BASE_URL')}/get_s3_file/{file.key}/{file.name}/',
            headers={'TaskToken': os.getenv('BACKEND_API_TOKEN')}
        )

    resp.raise_for_status()
    file_bytes = resp.content

    # 2) Estrazione estensione
    _, extension = os.path.splitext(file.name)
    extension = extension.lower().strip(".")

    # 3) Scrivo i bytes su file temporaneo
    with tempfile.NamedTemporaryFile(suffix="." + extension, delete=False) as tmp_file:
        tmp_file.write(file_bytes)
        tmp_path = tmp_file.name

    try:

        # 4.a) Immagini → DataURI
        if extension in IMAGE_EXTENSIONS:
            if only_text:
                return None
            return DataURI.from_file(tmp_path)

        # 4.b) Word → solo testo
        elif extension in {'docx', 'doc'}:
            loader = Docx2txtLoader(tmp_path)
            docs = loader.load()
            return "\n".join(doc.page_content for doc in docs)
        # 4.c) PDF → testo o DataURI
        elif extension == 'pdf':
            if only_text:
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
                return "\n".join(doc.page_content for doc in docs)
            else:
                return DataURI.from_file(tmp_path)

        # 4.d) Tutto il resto → testo (UTF-8)
        elif extension in TXT_DOCUMENTS_EXTENSIONS:
            loader = TextLoader(tmp_path, encoding='utf-8', autodetect_encoding=True)
            docs = loader.load()
            return "\n".join(doc.page_content for doc in docs)
        else:
            raise NotImplementedError

    finally:
        # 5) Pulizia file temporaneo
        try:
            os.remove(tmp_path)
        except OSError:
            pass


