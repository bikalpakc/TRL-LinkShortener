from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .serializers import RegisterSerializer, UserSerializer
from .models import MyUser


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'msg': 'User registered successfully',
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=email, password=password)

        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


#Signs the user in (or creates an account) using Google's "Sign in with Google".
#The frontend's Google button returns an ID token (JWT) as `credential`; we
#verify its signature/audience with Google's public keys, then issue our own
#JWT pair so the rest of the app works exactly like email/password auth.
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        credential = request.data.get('credential')
        if not credential:
            return Response(
                {'error': 'credential is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
        if not client_id:
            return Response(
                {'error': 'Google login is not configured on the server'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        try:
            # Verifies signature, expiry, issuer, and that the token was issued
            # for OUR client ID (audience).
            idinfo = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                client_id,
            )
        except ValueError:
            return Response(
                {'error': 'Invalid Google credential'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Google only confirms the address when it's verified on their side.
        if not idinfo.get('email_verified'):
            return Response(
                {'error': 'Google email is not verified'},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = idinfo.get('email')
        name = idinfo.get('name', '') or email

        # Reuse the account if this Google address is already registered,
        # otherwise create one. password=None => unusable password, so this
        # account can only sign in through Google.
        user = MyUser.objects.filter(email__iexact=email).first()
        is_new = user is None
        if not user:
            user = MyUser.objects.create_user(email=email, name=name, password=None)

        refresh = RefreshToken.for_user(user)
        return Response({
            'msg': 'Google sign-in successful',
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'is_new_user': is_new,
        }, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)