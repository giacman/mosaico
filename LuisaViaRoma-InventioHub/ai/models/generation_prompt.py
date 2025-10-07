import importlib
import io
import json
import os
import random
from importlib import import_module
from importlib.resources import files  # <-- importlib.resources

from datauri import DataURI
from langchain.callbacks.tracers import ConsoleCallbackHandler
from langchain.globals import set_debug
from langchain.globals import set_verbose
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import (
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)
from pydantic import ValidationError

from utils.task import GenerationTask


def create_few_shot_prompt_template(example_module_path, input_cls, output_cls):
    # Carichiamo dinamicamente il modulo indicato
    try:
        res_pkg = import_module(example_module_path, package=__package__)
    except Exception:
        return False

    # files(res_pkg) ci restituisce un Traversable; usiamo rglob per cercare ricorsivamente
    resource_root = files(res_pkg)
    input_paths = [p for p in resource_root.rglob("input_*.json")]

    if input_paths:
        chosen_input = random.choice(input_paths)
        chosen_output = chosen_input.with_name(
            chosen_input.name.replace("input_", "output_")
        )

        # Carichiamo e validiamo JSON
        raw_in = json.loads(chosen_input.read_text(encoding="utf-8"))["data"]
        raw_out = json.loads(chosen_output.read_text(encoding="utf-8"))

        examples = [
            {
                "input": input_cls.model_validate(raw_in).model_dump(mode="json"),
                "output": output_cls.model_validate(raw_out).model_dump(mode="json"),
            }
        ]

        example_prompt = ChatPromptTemplate.from_messages(
            [
                ("human", "Here is an EXAMPLE of processing:"),
                ("human", "Starting JSON:\n```json\n{input}\n```"),
                ("ai", "Generated output:\n{output}\n"),
            ]
        )

        return FewShotChatMessagePromptTemplate(
            example_prompt=example_prompt,
            examples=examples,
        )
    else:
        # Se non ci sono esempi disponibili, ritorniamo un prompt vuoto
        return False


def create_context_prompt_template(model, task: GenerationTask,
                                   gpt_uploaded_files) -> HumanMessagePromptTemplate | bool:
    context_prompt = []

    # IMAGES
    images_list = []

    if task.images:
        images_list = [{'image_url': {'url': str(data_uri), 'detail': 'high'}} for data_uri in task.images]

    # PDFs
    pdf_list = []
    texts_list = []
    if task.documents:

        for i, pdf_data in enumerate(task.documents):
            if type(pdf_data) != DataURI:
                continue

            if "openai" in task.llm_name:
                raw = io.BytesIO(pdf_data.data)
                raw.name = f'temp_pdf_{i}.pdf'
                # raw.mode = 'rb'
                gpt_uploaded_files.append(model.root_client.files.create(
                    file=raw,
                    # file=io.BufferedReader(raw),
                    purpose="user_data"
                ))

                pdf_list.append({
                    "type": "file",
                    "file": {"file_id": gpt_uploaded_files[-1].id},
                })
            elif "genai" in task.llm_name:
                pdf_list.append({
                    "type": "media",
                    "source_type": "base64",
                    "mime_type": "application/pdf",
                    "data": str(pdf_data).split("base64,")[-1],
                })
            else:
                pdf_list.append({
                    "type": "file",
                    "source_type": "base64",
                    "mime_type": "application/pdf",
                    "data": str(pdf_data).split("base64,")[-1],
                })

        # TEXTs
        texts_list = ["-" * 15 + f" Text Resource n.{i}" + "-" * 15 + f"\n{text}\n" + "-" * 40 for i, text in
                      enumerate(task.documents) if type(text) == str]

    if len(images_list) + len(pdf_list) + len(texts_list) > 0:
        context_prompt = ["Use the following resources as context for output generation:"]

    if len(images_list) + len(pdf_list) + len(texts_list) > 0:
        return HumanMessagePromptTemplate.from_template(
            context_prompt +
            images_list +
            pdf_list +
            texts_list
        )
    else:
        return False


async def generate(model, task: GenerationTask):

    prompt_module = importlib.import_module(f"models.{task.content_type.value.lower()}.prompt")
    chain, prompt_inputs, uploaded_files = getattr(prompt_module, "generate")(model, task)

    try:
        debug_config = {}

        if os.getenv("AI_DEBUG_MODE", "0").lower() in ("1", "true", "yes") and os.getenv("AI_VERBOSE_MODE",
                                                                                         "0").lower() in ("1", "true",
                                                                                                          "yes"):
            debug_config = {'callbacks': [ConsoleCallbackHandler()]}
            set_debug(True)
            set_verbose(True)

        generation_result = await chain.with_config(task.llm_config.model_dump() | debug_config).ainvoke(prompt_inputs)
        return getattr(prompt_module, "validate")(task, generation_result)

    except (ValueError, OutputParserException, ValidationError) as err:
        raise err
    finally:
        for f in uploaded_files:
            model.root_client.files.delete(f.id)
