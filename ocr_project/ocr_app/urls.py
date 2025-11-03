"""
URL configuration for ocr_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # صفحه اصلی = مدیریت افراد
    path('simple-ocr/', views.simple_ocr, name='simple_ocr'),  # OCR ساده
    path('extract-text/', views.extract_text, name='extract_text'),
    path('person-management/', views.person_management, name='person_management'),
    path('person/<int:person_id>/', views.person_detail, name='person_detail'),
    path('create-person/', views.create_person, name='create_person'),
    path('create-folder/<int:person_id>/', views.create_folder, name='create_folder'),
    path('upload-documents/<int:person_id>/', views.upload_documents, name='upload_documents'),
    path('get-folder-contents/<int:folder_id>/', views.get_folder_contents, name='get_folder_contents'),
    path('search/', views.search_documents, name='search_documents'),
    path('document-content/<int:document_id>/', views.document_content, name='document_content'),
    path('get-root-contents/<int:person_id>/', views.get_root_contents, name='get_root_contents'),
    path('get-person-folders/<int:person_id>/', views.get_person_folders, name='get_person_folders'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('user-management/', views.user_management, name='user_management'),
    path('create-user/', views.create_user, name='create_user'),
    path('user-permissions/<int:user_id>/', views.user_permissions, name='user_permissions'),
]