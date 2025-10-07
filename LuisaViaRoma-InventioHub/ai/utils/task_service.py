import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone

from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.date import DateTrigger

from models.generation_prompt import generate
from models.translation_prompt import translate, retry_translate
from utils.LLMs import MODELS, MULTIMODAL_PROVIDERS
from utils.files import load_and_convert, filter_s3_files
from utils.task import TranslationTask, GenerationTask, update_task, TaskState, get_translation_tasks, \
    get_generation_tasks

# Ottieni i logger configurati
gen_logger = logging.getLogger('server.generation')
trans_logger = logging.getLogger('server.translation')
sched_logger = logging.getLogger('server.scheduler')
main_logger = logging.getLogger('server')

BLOCKED_GENERATION_TASK_THRESHOLD_SECONDS = int(os.getenv('AI_BLOCKED_GENERATION_TASK_THRESHOLD_SECONDS', 300))
BLOCKED_TRANSLATION_TASK_THRESHOLD_SECONDS = int(os.getenv('AI_BLOCKED_TRANSLATION_TASK_THRESHOLD_SECONDS', 300))


async def manage_generation_task(task: GenerationTask):
    """Gestisce i task di generazione con logging migliorato"""
    try:

        await asyncio.to_thread(update_task, task, TaskState.PENDING)
        gen_logger.info(f"Started processing task [{task.id}] - Type: {task.content_type.value}")

        # Gestisci il caricamento e conversione di immagini e documenti
        is_multimodal = task.llm_name.split(":")[0] in MULTIMODAL_PROVIDERS

        if len(task.s3files) > 0:
            documents, images = filter_s3_files(task.s3files)

            coroutines = []
            if is_multimodal:
                gen_logger.info(f"Processing {len(images)} images for task [{task.id}]")
                coroutines.extend(load_and_convert(img) for img in images)

            gen_logger.info(f"Processing {len(documents)} documents for task [{task.id}]")
            coroutines.extend(
                load_and_convert(doc, only_text=not is_multimodal)
                for doc in documents
            )

            results = await asyncio.gather(*coroutines)

            offset = len(images) if is_multimodal else 0

            if is_multimodal:
                task.images.extend(results[:offset])
            elif len(images) > 0:
                raise Exception(f"{task.llm_name} not supports images")

            task.documents.extend(results[offset:])

        # Importa dinamicamente la giusta funzione "generate"
        gen_logger.info(f"Calling model '{task.llm_name}' for task [{task.id}]")
        model = MODELS[task.llm_name]

        # Chiama la funzione "generate(model, task)" del package corrispondente
        generation_result = await generate(model, task)
        task.data = generation_result

        if os.getenv("AI_DEBUG_MODE", "0").lower() in ("1", "true", "yes"):
            os.makedirs(f"tests/outputs/generation/{task.content_type.value.lower()}/", exist_ok=True)
            with open(
                    f"tests/outputs/generation/{task.content_type.value.lower()}/{task.llm_name.replace(':', '_').replace('/', '')}_{task.id}.json",
                    'w', encoding='utf-8') as f:
                json.dump(task.model_dump(mode="json"), f, ensure_ascii=False, indent=4)

        await asyncio.to_thread(update_task, task, TaskState.SUCCESS)
        gen_logger.info(f"Task [{task.id}] completed successfully")

    except Exception as e:
        gen_logger.error(f"Task [{task.id}] failed: {str(e)}")
        try:
            await asyncio.to_thread(update_task, task, TaskState.FAILED, str(e))
        except Exception as update_error:
            gen_logger.error(f"Failed to update task [{task.id}] status: {str(update_error)}")


async def manage_translation_task(task: TranslationTask):
    """Gestisce i task di traduzione con logging migliorato"""
    try:
        await asyncio.to_thread(update_task, task, TaskState.PENDING)

        trans_logger.info(f"Started processing TRANSLATION task [{task.id}]")

        await translate(model=MODELS[task.llm_name], task=task)

        if os.getenv("AI_DEBUG_MODE", "0").lower() in ("1", "true", "yes"):
            os.makedirs(f"tests/outputs/translation/{task.content_type.value.lower()}/", exist_ok=True)
            with open(
                    f"tests/outputs/translation/{task.content_type.value.lower()}/{task.llm_name.replace(':', '_').replace('/', '')}_{task.id}.json",
                    'w', encoding='utf-8') as f:
                json.dump(task.model_dump(mode="json"), f, ensure_ascii=False, indent=4)

        await asyncio.to_thread(update_task, task, TaskState.SUCCESS)
        trans_logger.info(f"Task [{task.id}] completed successfully")

    except Exception as e:
        trans_logger.error(f"Task [{task.id}] failed: {str(e)}")
        try:
            await asyncio.to_thread(update_task, task, TaskState.FAILED, str(e))
        except Exception as update_error:
            trans_logger.error(f"Failed to update task [{task.id}] status: {str(update_error)}")


async def manage_retry_translation_task(task: TranslationTask, retry_custom_prompt:str):
    """Gestisce i task di traduzione con logging migliorato"""
    try:
        await asyncio.to_thread(update_task, task, TaskState.PENDING)

        trans_logger.info(f"Started processing RETRY TRANSLATION task [{task.id}]")

        await retry_translate(model=MODELS[task.llm_name], task=task, retry_custom_prompt=retry_custom_prompt)

        await asyncio.to_thread(update_task, task, TaskState.SUCCESS)
        trans_logger.info(f"Task [{task.id}] completed successfully")

    except Exception as e:
        trans_logger.error(f"Task [{task.id}] failed: {str(e)}")
        try:
            await asyncio.to_thread(update_task, task, TaskState.FAILED, str(e))
        except Exception as update_error:
            trans_logger.error(f"Failed to update task [{task.id}] status: {str(update_error)}")


async def check_new_generation_tasks(scheduler):
    """Controlla nuovi generation task (state=SENT) e li schedula subito."""
    try:
        sched_logger.info("Scanning database for new generation tasks...")
        tasks = await asyncio.to_thread(get_generation_tasks, TaskState.SENT)

        if not tasks:
            sched_logger.info("No new generation tasks found")
            return

        sched_logger.info(f"Found {len(tasks)} new generation tasks")

        for task in tasks:
            try:
                scheduler.add_job(
                    func=manage_generation_task,
                    trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
                    args=[task],
                    id=f"generation_{task.id}",
                    name=f"Generation-{task.id}",
                    executor="asyncio"
                )
                gen_logger.info(f"Generation task [{task.id}] queued for execution")

            except Exception as e:
                sched_logger.error(f"Failed to queue generation task {task.id}: {e}")

    except Exception as e:
        sched_logger.error(f"Error scanning new generation tasks: {e}")


async def check_new_translation_tasks(scheduler):
    """Controlla nuovi translation task (state=SENT) e li schedula subito."""
    try:
        sched_logger.info("Scanning database for new translation tasks...")
        tasks = await asyncio.to_thread(get_translation_tasks, TaskState.SENT)

        if not tasks:
            sched_logger.info("No new translation tasks found")
            return

        sched_logger.info(f"Found {len(tasks)} new translation tasks")

        for task in tasks:
            try:
                scheduler.add_job(
                    func=manage_translation_task,
                    trigger=DateTrigger(run_date= datetime.now(timezone.utc)),
                    args=[task],
                    id=f"translation_{task.id}",
                    name=f"Translation-{task.id}",
                    executor="asyncio"
                )
                trans_logger.info(f"Translation task [{task.id}] queued for execution")

            except Exception as e:
                sched_logger.error(f"Failed to queue translation task {task.id}: {e}")

    except Exception as e:
        sched_logger.error(f"Error scanning new translation tasks: {e}")


async def check_pending_generation_tasks(scheduler):
    """Verifica e rischedula generation task in stato PENDING
       solo se pendenti da più di PENDING_TASK_THRESHOLD_SECONDS."""
    try:
        sched_logger.info("Checking for pending generation tasks...")
        tasks = await asyncio.to_thread(get_generation_tasks, TaskState.PENDING)

        if not tasks:
            sched_logger.info("No pending generation tasks")
            return

        threshold_time = datetime.now(timezone.utc) - timedelta(seconds=BLOCKED_GENERATION_TASK_THRESHOLD_SECONDS)
        sched_logger.info(
            f"Pending-generation threshold: {BLOCKED_GENERATION_TASK_THRESHOLD_SECONDS}s (tasks older than {threshold_time})")

        for task in tasks:
            if task.sent_at <= threshold_time:
                try:
                    scheduler.remove_job(f"generation_{task.id}")
                    await update_task(task, TaskState.FAILED, "Pending for too much time: BLOCKED")
                    main_logger.error(f"Generation task {task.id}: BLOCKED. Removed...")

                except JobLookupError as e:

                    scheduler.add_job(
                        func=manage_generation_task,
                        trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
                        args=[task],
                        id=f"generation_{task.id}",
                        name=f"Generation-{task.id}",
                        executor="asyncio"
                    )

                    gen_logger.info(f"Re-scheduled pending generation task [{task.id}] (pending since {task.sent_at})")

                except Exception as e:
                    main_logger.error(f"Failed to reschedule generation task {task.id}: {e}")
                    await update_task(task, TaskState.FAILED, "Failed to reschedule generation task")
            else:
                sched_logger.debug(f"Skipping generation task [{task.id}]: only pending since {task.sent_at}")

    except Exception as e:
        sched_logger.error(f"Error checking pending generation tasks: {e}")


async def check_pending_translation_tasks(scheduler):
    """Verifica e rischedula translation task in stato PENDING
       solo se pendenti da più di PENDING_TASK_THRESHOLD_SECONDS."""
    try:
        sched_logger.info("Checking for pending translation tasks...")
        tasks = await asyncio.to_thread(get_translation_tasks, TaskState.PENDING)

        if not tasks:
            sched_logger.info("No pending translation tasks")
            return

        threshold_time =  datetime.now(timezone.utc) - timedelta(seconds=BLOCKED_TRANSLATION_TASK_THRESHOLD_SECONDS)
        sched_logger.info(
            f"Pending-translation threshold: {BLOCKED_TRANSLATION_TASK_THRESHOLD_SECONDS}s (tasks older than {threshold_time})")

        for task in tasks:
            if task.sent_at <= threshold_time:
                try:
                    scheduler.remove_job(f"translation_{task.id}")
                    await update_task(task, TaskState.FAILED, "Pending for too much time: BLOCKED")
                    main_logger.error(f"Translation task {task.id}: BLOCKED. Removed...")

                except JobLookupError as e:
                    scheduler.add_job(
                        func=manage_translation_task,
                        trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
                        args=[task],
                        id=f"translation_{task.id}",
                        name=f"Translation-{task.id}",
                        executor="asyncio"
                    )

                    trans_logger.info(f"Re-scheduled pending translation task [{task.id}] (pending since {task.sent_at})")

                except Exception as e:
                    main_logger.error(f"Failed to reschedule translation task {task.id}: {e}")
                    await update_task(task, TaskState.FAILED, "Failed to reschedule translation task")
            else:
                sched_logger.debug(f"Skipping translation task [{task.id}]: only pending since {task.sent_at}")

    except Exception as e:
        sched_logger.error(f"Error checking pending translation tasks: {e}")
