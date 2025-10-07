import asyncio
import os

from langchain.chat_models import init_chat_model
from langchain_core.rate_limiters import InMemoryRateLimiter

import requests

class NoApiKeyError(Exception):
    pass


class LLMNotSupported(Exception):
    pass


class InitializationError(Exception):
    pass


## GLOBAL VARIABLES

provider_to_apikey_name = {
    "openai": "OPENAI_API_KEY",
    "google_genai": "GOOGLE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "mistralai": "MISTRAL_API_KEY",
    "qroq": "GROQ_API_KEY",
}


MODELS = {}
MULTIMODAL_PROVIDERS = set()
MODEL_ENTRIES = []


async def initialize_model(provider, model_name):

    # Check API KEY
    if provider in provider_to_apikey_name and provider_to_apikey_name[provider] not in os.environ:
        raise NoApiKeyError(f"{provider}:{model_name} -> NO API KEY in environment")

    name = f"{provider}:{model_name}"

    rate_limiter = InMemoryRateLimiter(
        requests_per_second=int(os.getenv("AI_LLM_MAX_REQUEST_PER_SECOND", 5)),
        check_every_n_seconds=float(os.getenv("AI_LLM_CHECK_PER_SECOND", 0.1)),
        # Wake up every 100 ms to check whether allowed to make a request,
        max_bucket_size=int(os.getenv("AI_LLM_MAX_BUCKET_SIZE", 10)),  # Controls the maximum burst size.
    )

    if os.getenv("AI_DEBUG_MODE", "0").lower() in ("1", "true", "yes"):
        return {name: init_chat_model(name, configurable_fields=("temperature", "max_tokens", "timeout", "max_retries"),
                                      rate_limiter=rate_limiter)}

    llm = init_chat_model(name, configurable_fields=("temperature", "max_tokens", "timeout", "max_retries"),
                          rate_limiter=rate_limiter)
    try:

        await llm.ainvoke("Respond YES if you are here")
        print(f"{name} -> LOADED")

    except (ValueError, ImportError) as e:
        raise LLMNotSupported(f"{name} -> {str(e)}")

    except Exception as e:
        raise InitializationError(f"{name} -> {str(e)}")

    return {name: llm}


async def activate_model(provider:str, name:str):
    global MODELS
    if MODELS.get(f"{provider}:{name}"):
        return
    try:
        result = await initialize_model(provider, name)
        MODELS |= result
        active = True
        state_message = ""

    except Exception as e:
        active = False
        state_message = str(e)

    headers = {"TaskToken": os.getenv('BACKEND_API_TOKEN'), "Content-Type": "application/json"}
    payload = {
        "provider_name": provider,
        "model_name": name,
        "active": active,
        "state_message": state_message,
    }
    resp = requests.put(
        f'{os.getenv('BACKEND_API_BASE_URL')}/llm_models/',
        headers=headers,
        json=payload
    )

    resp.raise_for_status()


def deactivate_model(provider:str, name:str):
    model_name = f"{provider}:{name}"
    global MODELS
    try:
        MODELS.pop(model_name)
        active = False
        state_message = ""

    except Exception as e:
        active = model_name in MODELS
        state_message = str(e)

    headers = {"TaskToken": os.getenv('BACKEND_API_TOKEN'), "Content-Type": "application/json"}
    payload = {
        "provider_name": provider,
        "model_name": name,
        "active": active,
        "state_message": state_message,
    }
    resp = requests.put(
        f'{os.getenv('BACKEND_API_BASE_URL')}/llm_models/',
        headers=headers,
        json=payload
    )

    resp.raise_for_status()

async def initialize_llm_models():
    try:
        if os.getenv("AI_DEBUG_MODE", "0").lower() in ("1", "true", "yes"):
            raise Exception

        resp = requests.get(
            f'{os.getenv('BACKEND_API_BASE_URL')}/llm_models/?active=true',
            headers={'TaskToken': os.getenv('BACKEND_API_TOKEN')}
        )
        resp.raise_for_status()

        for model in resp.json():
            MODEL_ENTRIES.append(model)

        resp = requests.get(
            f'{os.getenv('BACKEND_API_BASE_URL')}/llm_providers/?multimodal=true',
            headers={'TaskToken': os.getenv('BACKEND_API_TOKEN')}
        )
        resp.raise_for_status()

        for provider in resp.json():
            MULTIMODAL_PROVIDERS.add(provider["name"])



    except Exception as err:
        print("Error while connecting to DB to retrieve LLM MODELS", )
        print("Backup model list loaded.")
        for model in [
            {'provider':{"name":"openai"}, 'name': "gpt-4o"},
            # "openai:gpt-4o-mini",
            # "openai:gpt-4.1",
            # "openai:gpt-4.1-mini",
            # "openai:o1-2024-12-17",
            # "openai:o3-2025-04-16",
            # "openai:o4-mini-2025-04-16",
            # "google_genai:gemini-2.5-pro",
             {'provider':{"name":"google_genai"}, 'name': "gemini-2.5-flash"},
            # "google_genai:gemini-2.0-flash",
            # "google_genai:gemini-2.0-flash-lite",
            # "google_genai:gemini-1.5-pro",
            # "google_genai:gemini-1.5-flash",
            # "anthropic:claude-opus-4-20250514",
              {'provider':{"name":"anthropic"}, 'name': "claude-sonnet-4-20250514"},
            # "anthropic:claude-3-7-sonnet-latest",
            # "anthropic:claude-3-5-sonnet-latest",
            # "anthropic:claude-3-5-haiku-latest",
            # "groq:deepseek-r1-distill-llama-70b",
            # "groq:qwen/qwen3-32b",
            # "groq:llama-3.3-70b-versatile",
        ]:
            MODEL_ENTRIES.append(model)

        for provider in ["openai","google_genai","anthropic"]:
            MULTIMODAL_PROVIDERS.add(provider)



    sem = asyncio.Semaphore(5)

    async def guarded_init(provider:str, name:str):
        async with sem:
            try:
                result = await initialize_model(provider, name)
                active, state_message = True, ""
            except Exception as e:
                result = {}
                active, state_message = False, str(e)

            payload = {
                "provider_name": provider,
                "model_name": name,
                "active": active,
                "state_message": state_message,
            }
            headers = {
                "TaskToken": os.getenv("BACKEND_API_TOKEN"),
                "Content-Type": "application/json"
            }
            requests.put(
                f"{os.getenv('BACKEND_API_BASE_URL')}/llm_models/",
                headers=headers,
                json=payload
            )


            MODELS.update(result)

    await asyncio.gather(*(guarded_init(model["provider"]["name"], model["name"]) for model in MODEL_ENTRIES))
