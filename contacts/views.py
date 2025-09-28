from rest_framework import viewsets, permissions
from .models import Contact
from .serializers import ContactSerializer


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            # только админ может изменять и удалять
            permission_classes = [permissions.IsAdminUser]
        else:
            # все могут читать и добавлять
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

