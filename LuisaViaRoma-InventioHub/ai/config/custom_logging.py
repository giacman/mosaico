import logging
import sys


class ColoredFormatter(logging.Formatter):
    """Formatter personalizzato con colori ANSI"""

    # Codici colore ANSI
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Verde
        'WARNING': '\033[33m',  # Giallo
        'ERROR': '\033[31m',  # Rosso
        'CRITICAL': '\033[35m',  # Magenta
    }

    RESET = '\033[0m'  # Reset colore
    BOLD = '\033[1m'  # Grassetto

    def format(self, record):
        # Ottieni il colore per il livello
        color = self.COLORS.get(record.levelname, self.RESET)

        # Formatta il messaggio base
        formatted = super().format(record)

        # Applica il colore
        return f"{color}{formatted}{self.RESET}"


class TaskFormatter(ColoredFormatter):
    """Formatter specifico per i task con icone e colori dedicati"""

    TASK_COLORS = {
        'generation': '\033[94m',  # Blu
        'translation': '\033[95m',  # Magenta
        'scheduler': '\033[36m',  # Cyan
        'system': '\033[32m',  # Verde
    }

    TASK_ICONS = {
        'generation': '🎨',
        'translation': '🌍',
        'scheduler': '⏰',
        'system': '⚙️',
        'success': '✅',
        'failed': '❌',
        'pending': '⏳',
        'started': '🚀',
    }

    def format(self, record):
        # Determina il tipo di task dal logger name o dal messaggio
        task_type = self._determine_task_type(record)
        icon = self._determine_icon(record)
        color = self.TASK_COLORS.get(task_type, self.COLORS.get(record.levelname, self.RESET))

        # Formatta con icona e colore
        timestamp = self.formatTime(record, self.datefmt)
        level = record.levelname.ljust(8)
        logger_name = record.name.split('.')[-1].ljust(12)  # Solo ultima parte del nome

        # Messaggio formattato
        message = f"{color}{icon} [{timestamp}] {level} {logger_name} | {record.getMessage()}{self.RESET}"

        return message

    def _determine_task_type(self, record):
        """Determina il tipo di task dal record"""
        logger_name = record.name.lower()
        message = record.getMessage().lower()

        if 'generation' in logger_name or 'generation' in message:
            return 'generation'
        elif 'translation' in logger_name or 'translation' in message:
            return 'translation'
        elif 'scheduler' in logger_name or 'apscheduler' in logger_name:
            return 'scheduler'
        else:
            return 'system'

    def _determine_icon(self, record):
        """Determina l'icona appropriata dal messaggio"""
        message = record.getMessage().lower()

        if 'completed' in message or 'success' in message:
            return self.TASK_ICONS['success']
        elif 'failed' in message or 'error' in message:
            return self.TASK_ICONS['failed']
        elif 'processing' in message or 'started' in message:
            return self.TASK_ICONS['started']
        elif 'pending' in message or 'checking' in message:
            return self.TASK_ICONS['pending']
        elif 'generation' in message:
            return self.TASK_ICONS['generation']
        elif 'translation' in message:
            return self.TASK_ICONS['translation']
        elif 'scheduler' in message:
            return self.TASK_ICONS['scheduler']
        else:
            return self.TASK_ICONS['system']


def setup_logging():
    """Configura il sistema di logging con formatter personalizzati"""

    # Configurazione base
    logging.basicConfig(level=logging.INFO, handlers=[])

    # Handler per console con formatter personalizzato
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Formatter per i task
    task_formatter = TaskFormatter(
        fmt='%(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(task_formatter)

    # Logger principale dell'applicazione
    app_logger = logging.getLogger('server')
    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(console_handler)
    app_logger.propagate = False

    # Logger specifici per i task
    generation_logger = logging.getLogger('server.generation')
    generation_logger.setLevel(logging.INFO)
    generation_logger.addHandler(console_handler)
    generation_logger.propagate = False

    translation_logger = logging.getLogger('server.translation')
    translation_logger.setLevel(logging.INFO)
    translation_logger.addHandler(console_handler)
    translation_logger.propagate = False

    scheduler_logger = logging.getLogger('server.scheduler')
    scheduler_logger.setLevel(logging.INFO)
    scheduler_logger.addHandler(console_handler)
    scheduler_logger.propagate = False

    # Configura i logger di APScheduler per essere meno verbosi
    logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
    logging.getLogger('apscheduler.scheduler').setLevel(logging.WARNING)

    return app_logger, generation_logger, translation_logger, scheduler_logger
