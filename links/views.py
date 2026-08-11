from datetime import timezone

from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.views import View
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q

from analytics.models import Click
from analytics.tasks import record_click
from .serializers import LinkSerializer
from .models import Link


#Lets ANYONE (logged in or not) shorten a URL. Anonymous links get user=None
# and can be claimed by an account later (see ClaimLinksView).
class PublicShortenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LinkSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # If someone is logged in we tag the link to their account right away.
            user = request.user if request.user.is_authenticated else None
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#Claims anonymous links (user=None) to the currently logged-in account.
#Called after a visitor logs in/signs up so the link they shortened on the
#landing page shows up in their dashboard with full analytics.
class ClaimLinksView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        short_codes = request.data.get('short_codes', [])
        if not isinstance(short_codes, list) or not short_codes:
            return Response({'claimed': 0}, status=status.HTTP_200_OK)

        # Idempotent: only claims links that still have no owner; already-owned
        # or unknown codes are simply ignored.
        links = Link.objects.filter(
            user__isnull=True,
            is_active=True
        ).filter(
            Q(short_code__in=short_codes) | Q(custom_alias__in=short_codes)
        )
        claimed = links.count()
        links.update(user=request.user)
        return Response({'claimed': claimed}, status=status.HTTP_200_OK)


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

        # We call the Celery task using .delay() 
        # This sends the data to Redis and continues IMMEDIATELY.
        record_click.delay(
            link_id=link.id,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'), #consists of information about browser and device. We will parse this in the analytics/tasks.py to extract clean browser and device names.
            referrer=request.META.get('HTTP_REFERER'),
        )

        # 4. Redirect to the original long URL
        return redirect(link.original_url)