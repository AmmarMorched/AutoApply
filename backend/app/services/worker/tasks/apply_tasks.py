from celery import shared_task
from app.services.application.bot import ApplicationBot

@shared_task
def process_ready_applications():
    """Called by Celery Beat every ~15 minutes"""
    bot = ApplicationBot()
    pending = bot.get_pending_applications()  # Status = 'tailored'
    
    for app in pending:
        apply_application.delay(str(app.id))

@shared_task(bind=True, max_retries=3)
def apply_application(self, application_id: str):
    """Fill out the application form but stop before submit"""
    bot = ApplicationBot()
    result = bot.pre_fill_application(application_id)
    
    if result.status == "ready_for_review":
        notify_user.delay(application_id)

@shared_task
def notify_user(application_id: str):
    """Send notification to review dashboard"""
    from app.services.notification.telegram import TelegramNotifier
    
    notifier = TelegramNotifier()
    notifier.send_application_ready(application_id)