# bookstore/urls.py
from django.urls import path
from .views import home, signup, user_login, catalogue, user_logout, book_details, add_to_cart, view_cart, rate_book, remove_from_cart, place_order

urlpatterns = [
    path('', home, name='home'),
    path('catalogue/', catalogue, name='catalogue'),
    path('book/<int:book_id>/', book_details, name='book_details'),
    path('rate/<int:book_id>/', rate_book, name='rate_book'),
    path('signup/', signup, name='signup'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('add_to_cart/<int:book_id>/', add_to_cart, name='add_to_cart'),
    path('view_cart/', view_cart, name='view_cart'),
    path('remove_from_cart/<int:cart_book_id>/', remove_from_cart, name='remove_from_cart'),
    path('place_order/', place_order, name='place_order'),
]
