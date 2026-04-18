from celery import shared_task
from .models import Click
from links.models import Link

@shared_task
def record_click(link_id, ip_address, browser, referrer):
    try:
        link = Link.objects.get(id=link_id)
        # Here we can also add logic to detect country from IP. 
        Click.objects.create(
            link=link,
            ip_address=ip_address,
            browser=browser,
            referrer=referrer
        )
        return f"Click recorded for link with id: {link_id}"
    except Link.DoesNotExist:
        return "Link not found"