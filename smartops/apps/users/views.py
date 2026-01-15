from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserSerializer, PasswordSuggestionSerializer
from .utils import generate_random_password

class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class PasswordSuggestionView(views.APIView):
    permission_classes = [AllowAny] # Or IsAuthenticated, depending on requirement. Allowing any for signup assistance.
    serializer_class = PasswordSuggestionSerializer

    def get(self, request):
        length = int(request.query_params.get('length', 12))
        password = generate_random_password(length)
        serializer = PasswordSuggestionSerializer({'password': password, 'length': length})
        return Response(serializer.data)
