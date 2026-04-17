from datetime import timezone

from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.views import View
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q

from analytics.models import Click
from .serializers import LinkSerializer
from .models import Link


#Auto Handles Post and Get Requests for creating and listing links.
class LinkListCreateView(generics.ListCreateAPIView):
    serializer_class = LinkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Link.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


#Auto Handles Get, Put and Delete Requests for retrieving, updating and deleting a specific link.
class LinkDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LinkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Link.objects.filter(user=self.request.user)
    
class RedirectView(View):
    def get(self, request, short_code):
        print("Hello")
        # 1. Look for link by short_code OR custom_alias
        link = Link.objects.filter(
            Q(short_code=short_code) | Q(custom_alias=short_code),
            is_active=True
        ).first()

        if not link:
            return HttpResponseNotFound("Link not found or is inactive")

        # 2. Check if link has expired. Since the first part is False, Python stops looking and doesn't even try to run the second part. This saves our app from crashing with error "None<Time, Invalid comparison between None and datetime".
        if link.expires_at and link.expires_at < timezone.now():
            return HttpResponseForbidden("This link has expired")

        # 3. Save the click (We will move this to Celery in the next step!)
        # For now, we record it directly to make sure it works
        Click.objects.create(
            link=link,
            ip_address=request.META.get('REMOTE_ADDR'),
            browser=request.META.get('HTTP_USER_AGENT'),
            referrer=request.META.get('HTTP_REFERER')
        )

        # 4. Redirect to the original long URL
        return redirect(link.original_url)