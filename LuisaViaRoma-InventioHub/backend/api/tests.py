from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import ContentType, Language, Content, CustomUser
#from django.contrib.auth.models import User

class CreateContentTest(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='testuser9999')
        self.content_type = ContentType.objects.create(name='content di test')
        self.lang1 = Language.objects.create(name='it')
        self.lang2 = Language.objects.create(name='en')

    def test_create_content(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('create_content')
        data = {
            "creator": self.user.id,
            "title": "title example",
            "content_type": self.content_type.id,
            "languages": [self.lang1.id, self.lang2.id],
        }
        response = self.client.post(url, data, format='json')
        print(f'POST response\n\n {response.data} \n\n')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Content.objects.count(), 1)
        self.assertEqual(Content.objects.first().creator, self.user)

        url = reverse('get_contents')
        response = self.client.get(url)
        print(f'GET response\n\n {response.data} \n\n')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content_data = response.data[0]
        self.assertIn('content_type', content_data)
        self.assertIn('languages', content_data)
