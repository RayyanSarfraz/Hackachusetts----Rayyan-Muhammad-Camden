from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class EngineStatusView(APIView):
    """Lightweight status endpoint for the engine module."""

    permission_classes = [AllowAny]

    def get(self, _request):
        return Response({"module": "engine", "status": "ok"})
