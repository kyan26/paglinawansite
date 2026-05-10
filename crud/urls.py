from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('gender/list', views.gender_list),
    path('gender/add', views.add_gender),
    path('gender/edit/<int:genderId>', views.edit_gender),
    path('gender/delete/<int:genderId>', views.delete_gender),
    path('user/list', views.user_list),
    path('user/add', views.add_user),
    path('user/edit/<int:user_id>', views.user_edit, name='user_edit'),
    path('user/delete/<int:user_id>', views.user_delete, name='user_delete'),
    path('user/search-suggestions/', views.user_search_suggestions, name='user_search_suggestions'),
    path('user/delete-picture/<int:user_id>', views.user_delete_picture, name='user_delete_picture'),  # 👈 new
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)