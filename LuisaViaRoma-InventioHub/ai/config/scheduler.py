import os

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler


def create_scheduler():
    """Crea e configura lo scheduler con supporto per concorrenza"""

    # Configurazione dello scheduler
    job_stores = {
        'default': MemoryJobStore(),
    }

    executors = {
        'asyncio': AsyncIOExecutor(),
        'blocking': ThreadPoolExecutor(max_workers=int(os.getenv('AI_BLOCKING_JOB_WORKERS', 5)))
    }

    job_defaults = {
        'coalesce': False,
        'max_instances': int(os.getenv('AI_JOB_MAX_INSTANCES', 1)),
        'misfire_grace_time': 30
    }

    scheduler = AsyncIOScheduler(
        jobstores=job_stores,
        executors=executors,
        job_defaults=job_defaults
    )

    return scheduler
