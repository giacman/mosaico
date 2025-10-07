import os
import random

from config.custom_logging import setup_logging
from config.scheduler import create_scheduler
from fastapi import FastAPI
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

from utils.LLMs import initialize_llm_models, activate_model, deactivate_model
from utils.task_service import (
    manage_generation_task,
    manage_translation_task, check_pending_generation_tasks, check_pending_translation_tasks,
    check_new_generation_tasks, check_new_translation_tasks, manage_retry_translation_task
)
from utils.task import TranslationTask, GenerationTask


# ============================================================================
# CONFIGURAZIONE GLOBALE
# ============================================================================

# Inizializza i logger
main_logger, gen_logger, trans_logger, sched_logger = setup_logging()

# Crea lo scheduler
scheduler = create_scheduler()


# ============================================================================
# FASTAPI LIFECYCLE MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestisce il ciclo di vita dell'applicazione"""
    # Startup
    main_logger.info("=== SERVER STARTUP ===")

    if os.getenv("AI_DEBUG_MODE", "0").lower() in ("1", "true", "yes"):
        main_logger.info("!!!!!! DEBUG MODE ENABLED !!!!!!")

    main_logger.info("Initializing LLM models...")
    await initialize_llm_models()

    main_logger.info("Initializing APScheduler...")

    scheduler.start()

    main_logger.info("APScheduler started successfully")

    # Controlla task pendenti al startup
    await check_new_generation_tasks(scheduler)
    await check_new_translation_tasks(scheduler)
    await check_pending_generation_tasks(scheduler)
    await check_pending_translation_tasks(scheduler)

    # Aggiunta job ricorrenti
    scheduler.add_job(
        check_pending_generation_tasks,
        args=[scheduler],
        trigger=IntervalTrigger(seconds=int(os.getenv('AI_GENERATION_CHECK_PENDING_SCHED_TIME', 60))),
        id='check_pending_generation_tasks',
        name='PendingGenerationTasksCheck'
    )

    scheduler.add_job(
        check_pending_translation_tasks,
        args=[scheduler],
        trigger=IntervalTrigger(seconds=int(os.getenv('AI_TRANSLATION_CHECK_PENDING_SCHED_TIME', 60))),
        id='check_pending_translation_tasks',
        name='PendingGenerationTasksCheck'
    )

    scheduler.add_job(
        check_new_generation_tasks,
        args=[scheduler],
        trigger=IntervalTrigger(seconds=int(os.getenv('AI_GENERATION_CHECK_NEW_SCHED_SECONDS', 180))),
        id='check_new_generation_tasks',
        name='NewGenerationTasksCheck'
    )

    scheduler.add_job(
        check_new_translation_tasks,
        args=[scheduler],
        trigger=IntervalTrigger(seconds=int(os.getenv('AI_TRANSLATION_CHECK_NEW_SCHED_SECONDS', 180))),
        id='check_new_translation_tasks',
        name='NewTranslationTasksCheck'
    )

    sched_logger.info("Recurring jobs configured (pending: 1min, new: 5min)")
    main_logger.info("=== SERVER READY ===")

    yield

    # Shutdown
    main_logger.info("=== SERVER SHUTDOWN ===")
    main_logger.info("Stopping APScheduler...")
    scheduler.shutdown(wait=True)
    main_logger.info("APScheduler stopped successfully")
    main_logger.info("=== SHUTDOWN COMPLETE ===")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(lifespan=lifespan)


@app.post("/generate/")
async def generate(task: GenerationTask):
    """Endpoint per sottomettere un task di generazione"""
    try:
        scheduler.add_job(
            func=manage_generation_task,
            args=[task],
            id=f"generation_{task.id}",
            name=f"Generation-{task.id}",
            executor = "asyncio"
        )

        gen_logger.info(f"Task [{task.id}] received and queued")
        return {"status": "received", "task_id": task.id}

    except Exception as e:
        gen_logger.error(f"Failed to queue task [{task.id}]: {str(e)}")
        return {"status": "failed", "error": str(e)}


@app.post("/translate/")
async def translate(task: TranslationTask):
    """Endpoint per sottomettere un task di traduzione"""
    try:
        scheduler.add_job(
            func=manage_translation_task,
            args=[task],
            id=f"translation_{task.id}",
            name=f"Translation-{task.id}",
            executor="asyncio"
        )

        trans_logger.info(f"Task [{task.id}] received and queued")
        return {"status": "received", "task_id": task.id}

    except Exception as e:
        trans_logger.error(f"Failed to queue task [{task.id}]: {str(e)}")
        return {"status": "failed", "error": str(e)}


@app.post("/retry_translate/")
async def translate(task: TranslationTask, retry_custom_prompt: str):
    """Endpoint per sottomettere un task di traduzione"""
    try:
        scheduler.add_job(
            func=manage_retry_translation_task,
            args=[task, retry_custom_prompt],
            id=f"retry_translation_{task.id}",
            name=f"RetryTranslation-{task.id}",
            executor="asyncio"
        )

        trans_logger.info(f"Task [{task.id}] received and queued")
        return {"status": "received", "task_id": task.id}

    except Exception as e:
        trans_logger.error(f"Failed to queue task [{task.id}]: {str(e)}")
        return {"status": "failed", "error": str(e)}


@app.post("/generate/delayed/{delay_seconds}")
async def generate_delayed(task: GenerationTask, delay_seconds: int = 60):
    """Endpoint per sottomettere un task di generazione con ritardo"""
    try:
        run_date =  datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)

        scheduler.add_job(
            func=manage_generation_task,
            args=[task],
            trigger=DateTrigger(run_date=run_date),
            id=f"generation_delayed_{task.id}",
            name=f"DelayedGeneration-{task.id}",
            executor = "asyncio"
        )

        gen_logger.info(f"Task [{task.id}] scheduled for {run_date.strftime('%H:%M:%S')} (+{delay_seconds}s)")
        return {
            "status": "scheduled",
            "task_id": task.id,
            "scheduled_time": run_date.isoformat()
        }

    except Exception as e:
        gen_logger.error(f"Failed to schedule delayed task [{task.id}]: {str(e)}")
        return {"status": "failed", "error": str(e)}


@app.get("/scheduler/status")
async def scheduler_status():
    """Endpoint per controllare lo stato dello scheduler"""
    jobs = scheduler.get_jobs()

    # Raggruppa i job per tipo
    job_summary = {
        'generation': len([j for j in jobs if 'generation' in j.id.lower()]),
        'translation': len([j for j in jobs if 'translation' in j.id.lower()]),
        'system': len([j for j in jobs if j.id in ['check_pending_tasks', 'check_new_tasks']]),
        'total': len(jobs)
    }

    sched_logger.info(f"Status requested - Jobs: {job_summary}")

    return {
        "running": scheduler.running,
        "job_summary": job_summary,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "pending": job.pending
            }
            for job in jobs
        ]
    }


@app.delete("/scheduler/cancel/{job_id}")
async def cancel_job(job_id: str):
    """Cancella un job specifico"""
    try:
        scheduler.remove_job(job_id)
        sched_logger.info(f"Job [{job_id}] cancelled successfully")
        return {"status": "cancelled", "job_id": job_id}
    except Exception as e:
        sched_logger.error(f"Failed to cancel job [{job_id}]: {str(e)}")
        return {"status": "failed", "error": str(e)}


@app.post("/scheduler/pause")
async def pause_scheduler():
    """Pausa lo scheduler"""
    scheduler.pause()
    sched_logger.info("Scheduler paused")
    return {"status": "paused"}


@app.post("/scheduler/resume")
async def resume_scheduler():
    """Riprende lo scheduler"""
    scheduler.resume()
    sched_logger.info("Scheduler resumed")
    return {"status": "resumed"}


@app.post("/llm_models/activate")
async def activate_llm_model(provider: str, name: str):
    try:

        job_id = f"activate_llm_model_{random.randint(0, 10000)}"
        scheduler.add_job(
            func=activate_model,
            args=[provider, name],
            trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
            id=job_id,
            executor="asyncio"
        )

        sched_logger.info(f"Activating model scheduled for {provider}:{name}")
        return {"status": "received", "job_id": job_id}

    except Exception as e:
        sched_logger.error(f"Failed to schedule activate [{provider}:{name}]: {str(e)}")
        return {"status": "failed", "error": str(e)}

@app.post("/llm_models/deactivate")
async def deactivate_llm_model(provider:str, name:str):
    try:

        job_id = f"deactivate_llm_model_{random.randint(0, 10000)}"
        scheduler.add_job(
            func=deactivate_model,
            args=[provider, name],
            trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
            id=job_id,
            executor="asyncio"
        )

        sched_logger.info(f"De-activating model scheduled for {provider}:{name}")
        return {"status": "received", "job_id": job_id}

    except Exception as e:
        sched_logger.error(f"Failed to schedule de-activation [{provider}:{name}]: {str(e)}")
        return {"status": "failed", "error": str(e)}