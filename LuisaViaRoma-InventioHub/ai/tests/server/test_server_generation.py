import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import requests
from dotenv import load_dotenv

load_dotenv()

from utils.task import GenerationTask, TranslationTask, Translation

# Lock per thread-safe printing
print_lock = Lock()


def safe_print(*args, **kwargs):
    """Thread-safe print function"""
    with print_lock:
        print(*args, **kwargs)


def make_request(task_data, request_id, url):
    """
  Esegue una singola richiesta HTTP

  Args:
      task_data: I dati del task da inviare
      request_id: ID univoco per identificare la richiesta
      url: URL dell'endpoint

  Returns:
      dict: Risultato della richiesta con metadati
  """
    start_time = time.time()

    try:
        safe_print(f"🚀 Avvio richiesta #{request_id}")

        # Esegui la richiesta HTTP
        resp = requests.post(url, json=task_data, timeout=30)
        resp.raise_for_status()

        end_time = time.time()
        duration = end_time - start_time

        safe_print(f"✅ Richiesta #{request_id} completata in {duration:.2f}s")

        return {
            "request_id": request_id,
            "success": True,
            "response": resp.json(),
            "duration": duration,
            "status_code": resp.status_code
        }

    except requests.exceptions.RequestException as e:
        end_time = time.time()
        duration = end_time - start_time

        safe_print(f"❌ Richiesta #{request_id} fallita dopo {duration:.2f}s: {str(e)}")

        return {
            "request_id": request_id,
            "success": False,
            "error": str(e),
            "duration": duration,
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }

def process_single_file(task_type: str, task, request_id):
    """Processa un singolo file e fa la richiesta"""
    try:
        url = "http://127.0.0.1:8081/"

        if type(task) == str:
            # Carica i dati del task per questo specifico file
            with open(task, encoding="utf-8") as f:
                json_task = json.load(f)

            if task_type.lower() == "generation":
                task = GenerationTask.model_validate(json_task)
                url += "generate/"
            elif task_type.lower() == "translation":
                task = TranslationTask.model_validate(json_task)
                task.translations = [
                    Translation(id=0, language="de"),
                    Translation(id=1, language="en"),
                    Translation(id=2, language="fr"),
                ]
                url += "translate/"
            else:
                raise NotImplementedError
        else:

            if task_type.lower() == "generation":
                url += "generate/"
            elif task_type.lower() == "translation":
                url += "translate/"
            else:
                raise NotImplementedError

        # _____________________________________________________
        # __   WRITE HERE TO CHANGE MANUALLY task PROPERTIES __
        # _____________________________________________________

        task.id = request_id

        # _________________________

        task_data = task.model_dump(mode="json")

        # Esegui la richiesta per questo task
        return make_request(task_data, request_id, url)

    except Exception as e:
        print(f"❌ Errore nel caricamento del task: {e}")
        return {
            "request_id": request_id,
            "success": False,
            "error": f"Errore caricamento file: {str(e)}",
            "duration": 0,
            "input_file": task if type(task) == str else None,
        }

def run_concurrent_requests(task_type: str, input_files, max_workers=3):
    """
    Esegue multiple richieste concorrenti usando file di input diversi

    Args:
        input_files: Lista dei path dei file JSON di input
        max_workers: Numero massimo di thread concorrenti
    """

    num_requests = len(input_files)

    print(f"🎯 Avvio di {num_requests} richieste concorrenti (max {max_workers} workers)")
    print("=" * 60)

    start_time = time.time()
    results = []

    # Esegui le richieste concorrenti
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Sottometti tutti i job, ognuno con il suo file
        future_to_data = {
            executor.submit(process_single_file, task_type, input_file, i + 1): (i + 1, input_file)
            for i, input_file in enumerate(input_files)
        }

        # Raccogli i risultati man mano che arrivano
        for future in as_completed(future_to_data):
            request_id, input_file = future_to_data[future]
            try:
                result = future.result()
                if "input_file" not in result:
                    result["input_file"] = input_file
                results.append(result)
            except Exception as exc:
                safe_print(f"❌ Richiesta #{request_id} ({input_file}) ha generato un'eccezione: {exc}")
                results.append({
                    "request_id": request_id,
                    "success": False,
                    "error": str(exc),
                    "duration": 0,
                    "input_file": input_file
                })

    end_time = time.time()
    total_duration = end_time - start_time

    # Stampa statistiche finali
    print("=" * 60)
    print("📊 STATISTICHE FINALI")
    print("=" * 60)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"✅ Richieste riuscite: {len(successful)}/{num_requests}")
    print(f"❌ Richieste fallite: {len(failed)}/{num_requests}")
    print(f"⏱️  Tempo totale: {total_duration:.2f}s")

    if successful:
        avg_duration = sum(r["duration"] for r in successful) / len(successful)
        min_duration = min(r["duration"] for r in successful)
        max_duration = max(r["duration"] for r in successful)

        print(f"📈 Durata media richieste: {avg_duration:.2f}s")
        print(f"📈 Durata minima: {min_duration:.2f}s")
        print(f"📈 Durata massima: {max_duration:.2f}s")

        # Calcola il throughput
        throughput = len(successful) / total_duration
        print(f"🚀 Throughput: {throughput:.2f} richieste/secondo")

    print("\n🔍 DETTAGLI RICHIESTE:")
    print("-" * 40)

    # Ordina i risultati per request_id
    results.sort(key=lambda x: x["request_id"])

    for result in results:
        status = "✅" if result["success"] else "❌"
        duration = f"{result['duration']:.2f}s"
        file_name = result.get("input_file", "").split("/")[-1] if result.get("input_file") else "N/A"

        if result["success"]:
            print(f"{status} Richiesta #{result['request_id']:2d} ({file_name}): {duration}")
        else:
            print(f"{status} Richiesta #{result['request_id']:2d} ({file_name}): {duration} - {result['error']}")

    return results


if __name__ == "__main__":
    # Configurazione
    NUM_REQUESTS = 1  # Numero di richieste da eseguire
    MAX_WORKERS = 1  # Numero massimo di thread concorrenti

    MODEL_ENTRIES = [
        "openai:gpt-4o",
        # "openai:gpt-4o-mini",
        # "openai:gpt-4.1",
        # "openai:gpt-4.1-mini",
        # "openai:o1-2024-12-17",
        # "openai:o3-2025-04-16",
        # "openai:o3-mini-2025-01-31",
        # "openai:o4-mini-2025-04-16",
        # "google_genai:gemini-2.5-pro",
        # "google_genai:gemini-2.5-flash",
        # "google_genai:gemini-2.0-flash",
        # "google_genai:gemini-2.0-flash-lite",
        # "google_genai:gemini-1.5-pro",
        # "google_genai:gemini-1.5-flash",
        # "anthropic:claude-opus-4-20250514",
        # "anthropic:claude-sonnet-4-20250514",
        # "anthropic:claude-3-7-sonnet-latest",
        # "anthropic:claude-3-5-sonnet-latest",
        # "anthropic:claude-3-5-haiku-latest",
        # "groq:deepseek-r1-distill-llama-70b",
        # "groq:qwen/qwen3-32b",
        # "groq:llama-3.3-70b-versatile",
    ]

    # Carica i dati del task per questo specifico file
    with open("./tests/inputs/editorial/1.json", encoding="utf-8") as f:
        task = GenerationTask.model_validate(json.load(f))

        for i, llm_name in enumerate(MODEL_ENTRIES):
            task.llm_name = llm_name
            process_single_file("generation", task, i)


    # results = run_concurrent_requests("translation",
    #     ["outputs/generation/editorial/1.json"]
    # )

    # # Optional: Salva i risultati in un file JSON
    # timestamp = time.strftime("%Y%m%d_%H%M%S")
    # output_file = f"concurrent_requests_results_{timestamp}.json"
    #
    # try:
    #     with open(output_file, 'w', encoding='utf-8') as f:
    #         json.dump(results, f, indent=2, ensure_ascii=False)
    #     print(f"\n💾 Risultati salvati in: {output_file}")
    # except Exception as e:
    #     print(f"❌ Errore nel salvataggio: {e}")