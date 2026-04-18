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

        # --- BROADCAST TO WEBSOCKET ---
        channel_layer = get_channel_layer()
        user_group = f"user_{link.user.id}"
        total_clicks = link.clicks.count()

        async_to_sync(channel_layer.group_send)(
            user_group,
            {
                "type": "click_update", # This matches the method name in consumers.py
                "link_id": link.id,
                "total_clicks": total_clicks
            }
        )
        return f"Recorded and Broadcasted for link with id: {link_id}"
    except Link.DoesNotExist:
        return "Link not found"