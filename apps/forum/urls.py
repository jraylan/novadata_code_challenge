from django.urls import path

from . import views

urlpatterns = [
     path('', views.PostListView.as_view(), name='post_list'),
     path('create/', views.PostCreationView.as_view(), name='post_create'),
     path('<int:pk>/',
            views.PostDetailView.as_view(), name='post_detail'),
     path('<int:pk>/apagar/',
         views.PostDeletionView.as_view(), name='post_delete'),
     path('comment/<int:pk>/apagar/',
         views.CommentDeletionView.as_view(), name='post_comment_delete'),

     # api
     ## Postagens
     path('api/posts/',
        views.PostAPIView.as_view(), name="post_api_view"),
     path('api/posts/<int:pk>/',
        views.PostAPIView.as_view(), name="post_api_view"),
     path('api/posts/<int:pk>/comments/',
         views.PostCommentsAPIView.as_view(), name="post_comments_api_view"),
     ## Comentários
     path('api/comments/',
        views.CommentAPIView.as_view(), name="comment_api_view"),
     path('api/comments/<int:pk>/',
         views.CommentAPIView.as_view(), name="comment_api_view"),
]
