import os
from datetime import datetime, timezone
from enum import Enum
from typing import List, Any, Self

import requests
from datauri import DataURI
from pydantic import BaseModel, Field, model_validator, computed_field
from pydantic_extra_types.language_code import LanguageAlpha2
from pydantic_extra_types.country import CountryAlpha2

from models.classes import ContentType
from utils.files import S3File

if not os.getenv('BACKEND_API_BASE_URL'):
    raise RuntimeError("You must set the BACKEND_API_BASE_URL environment variable")

if not os.getenv('BACKEND_API_TOKEN'):
    raise RuntimeError("You must set the BACKEND_API_TOKEN environment variable")


class ModelConfig(BaseModel):
    temperature: float = Field(default=0.5, gt=0, lt=1,
                               description="Controls the randomness of the model's output. Higher values (e.g., 1.0) yield more creative results, while lower values (e.g., 0.0) make the responses more deterministic.")
    timeout: float = Field(default=180, gt=0,
                           description="Maximum time (in seconds) to wait for the model’s response before aborting the request.")
    max_retries: int = Field(default=3, gt=0,
                             description="Maximum number of retry attempts if a request fails (e.g., due to network issues or rate limits).")


class TaskState(str, Enum):
    SUCCESS = 'success'
    FAILED = 'failed'
    PENDING = 'pending'
    SENT = 'sent'


class Language(BaseModel):
    id: int = Field(-1, description="The language id of the language")
    name: str = Field(...)
    lang_alpha2: LanguageAlpha2 = Field(...)
    country_alpha2: CountryAlpha2 = Field(...)

    @computed_field
    @property
    def complete_name(self) -> str:
        return f"{self.name}({self.lang_alpha2}-{self.country_alpha2})"



class Task(BaseModel):
    id: int = Field(..., description="Unique identifier of the task.")
    state: TaskState = Field(TaskState.SENT,
                             description="Current lifecycle state of the task: sent, pending, success, or failed.")
    state_message: str = Field("",
                               description="Optional human-readable message providing additional details about the current state.")
    sent_at: datetime | None = Field(datetime.now(timezone.utc),
                              description="Datetime at which the task is queued or scheduled to be sent to the LLM.")
    generated_at: datetime | None = Field(None,
                                          description="Datetime when the output was generated, if generation has already occurred.")
    content_type: ContentType = Field(...,
                                      description="Category of content the task handles (e.g., blog post, product description).")
    data: Any = Field(...,
                      description="Payload consumed by the task; its structure must match the specified content_type and the concrete task subclass.")
    llm_name: str = Field(default="openai:gpt-4o",
                          description="Fully-qualified name of the large-language model to invoke.")
    llm_config: ModelConfig = Field(default_factory=ModelConfig,
                                    description="Configuration parameters passed to the model (temperature, timeout, etc.).")

    @model_validator(mode='after')
    def check_gptO_temperature(self) -> Self:
        if "openai:o" in self.llm_name:
            self.llm_config.temperature = 1
        return self


class GenerationTask(Task):
    language: Language = Field(default_factory = Language, description="Target language for the generated content.")
    s3files: List[S3File] = Field([], description="Reference files (images or documents) stored on S3 for this task.")
    images: List[DataURI] = Field([], description="Inline reference images provided as Data-URI strings.")
    documents: List[DataURI] = Field([],
                                     description="Inline reference documents (e.g., plain text, PDF) provided as Data-URI strings.")
    custom_prompt: str = Field("", description="Additional prompt instructions to guide the generation.")


class Translation(BaseModel):
    id: int = Field(..., description="Unique identifier of the translation record.")
    state: TaskState = Field(..., description="")
    state_message: str = Field("", description="")
    language: Language = Field(..., description="Language into which the content is (or will be) translated.")
    data: Any = Field({}, description="Translated content following the structure defined by the parent task.")


class TranslationTask(Task):
    translations: List[Translation] = Field([],
                                            description="List of translations, each respecting the structure dictated by content_type and the task type.")


def get_translation_tasks(state: TaskState = TaskState.SENT) -> List[TranslationTask]:
    if os.getenv("AI_DEBUG_MODE", "0").lower() in ("1", "true", "yes"):
        return []
    headers = {'TaskToken': os.getenv('BACKEND_API_TOKEN')}
    resp = requests.get(f'{os.getenv("BACKEND_API_BASE_URL")}/get_trans_tasks/', params={"state": state},
                        headers=headers)
    resp.raise_for_status()
    tasks = resp.json()
    for i in range(len(tasks)):
        tasks[i] = TranslationTask.model_validate(tasks[i])
    return tasks


def get_generation_tasks(state: TaskState) -> List[GenerationTask]:
    if os.getenv("AI_DEBUG_MODE", "0").lower() in ("1", "true", "yes"):
        return []
    headers = {'TaskToken': os.getenv('BACKEND_API_TOKEN')}
    resp = requests.get(f'{os.getenv("BACKEND_API_BASE_URL")}/get_generation_tasks/', params={"state": state},
                        headers=headers)
    resp.raise_for_status()
    tasks = resp.json()
    for i in range(len(tasks)):
        tasks[i] = GenerationTask.model_validate(tasks[i])
    return tasks


def update_translation_task(task: TranslationTask):
    if os.getenv("AI_DEBUG_MODE", "0").lower() in ("1", "true", "yes"):
        return
    headers = {"TaskToken": os.getenv('BACKEND_API_TOKEN'), "Content-Type": "application/json"}
    response = requests.put(f'{os.getenv("BACKEND_API_BASE_URL")}/update_trans_tasks/', headers=headers,
                            json=[task.model_dump(mode="json")])
    response.raise_for_status()


def update_generation_task(task: GenerationTask):
    if os.getenv("AI_DEBUG_MODE", "0").lower() in ("1", "true", "yes"):
        return
    headers = {"TaskToken": os.getenv('BACKEND_API_TOKEN'), "Content-Type": "application/json"}
    response = requests.put(f'{os.getenv("BACKEND_API_BASE_URL")}/update_generation_task/', headers=headers,
                            json=task.model_dump(mode="json"))
    response.raise_for_status()


def update_task(task: GenerationTask | TranslationTask, state: TaskState, state_message: str = ""):
    if isinstance(task, GenerationTask):
        task.state = state
        task.state_message = state_message
        update_generation_task(task)
    elif isinstance(task, TranslationTask):
        for translation in task.translations:
            translation.state = state
            translation.state_message = state_message
        update_translation_task(task)
    else:
        raise NotImplementedError
