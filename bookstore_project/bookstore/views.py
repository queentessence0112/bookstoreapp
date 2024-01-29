# myapp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from .forms import SignUpForm, LoginForm, RatingForm, OrderForm, CatalogueFilterForm
from .models import Book, Cart, CartBook, BookRating, Order, OrderItem
from django.core.cache import cache
from django.contrib import messages
from django.db.models import F
from django.db.models import Avg

def home(request):
    # Retrieve recently viewed books from the cache
    recently_viewed_books = cache.get(request.user.username + '_recently_viewed', [])
    recently_viewed_books = recently_viewed_books[:5]  # Display the last 5 recently viewed books

    # Retrieve book objects from the database based on the book IDs
    books = Book.objects.filter(id__in=recently_viewed_books)

    return render(request, 'bookstore/home.html', {'recently_viewed_books': books})

def about(request):
    return render(request, 'bookstore/about.html')

def catalogue(request):
    books = Book.objects.all()

    # Handle filtering
    form = CatalogueFilterForm(request.GET)
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        author = form.cleaned_data.get('author')
        category = form.cleaned_data.get('category')

        if search_query:
            books = books.filter(title__icontains=search_query)

        if author:
            books = books.filter(author=author)

        if category:
            books = books.filter(category=category)

    sort_by = request.GET.get('sort_by', '')

    if sort_by == 'lowest_price':
        books = Book.objects.all().order_by('price')
    elif sort_by == 'highest_price':
        books = Book.objects.all().order_by('-price')
    else:
        books = Book.objects.all()

    return render(request, 'bookstore/catalogue.html', {'books': books, 'form': form, 'sort_by': sort_by})

def book_details(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    ratings = BookRating.objects.filter(book=book)
    avg_rating = ratings.aggregate(Avg('rating'))['rating__avg']

    # Store recently viewed books in the cache
    recently_viewed_books = cache.get(request.user.username + '_recently_viewed', [])
    if book_id not in recently_viewed_books:
        recently_viewed_books.append(book_id)
        cache.set(request.user.username + '_recently_viewed', recently_viewed_books, timeout=300)  # Cache timeout in seconds

    return render(request, 'bookstore/book_details.html', {'book': book, 'ratings': ratings, 'avg_rating': avg_rating})

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')  # Change 'homepage' to the actual name/url of your homepage
    else:
        form = SignUpForm()
    return render(request, 'bookstore/signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)
                return redirect('home')  # Change 'homepage' to the actual name/url of your homepage
    else:
        form = LoginForm()
    return render(request, 'bookstore/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return render(request, 'bookstore/base.html', {'user_logged_out': True})

@login_required
def rate_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    user_rating = BookRating.objects.filter(book=book, user=request.user).first()

    if request.method == 'POST':
        form = RatingForm(request.POST, instance=user_rating)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.book = book
            rating.user = request.user
            rating.save()
            return redirect('book_details', book_id=book_id)
    else:
        form = RatingForm(instance=user_rating)

    return render(request, 'bookstore/rate_book.html', {'form': form, 'book': book})

@login_required
def add_to_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_book, cart_book_created = CartBook.objects.get_or_create(cart=cart, book=book)

    if not cart_book_created:
        # If the book is already in the cart, increase the quantity by 1
        CartBook.objects.filter(cart=cart, book=book).update(quantity=F('quantity') + 1)

    return redirect('view_cart')
    

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_books = cart.cartbook_set.all()

    for cart_book in cart_books:
        cart_book.total_price = cart_book.book.price * cart_book.quantity

    total_price = sum(cart_book.total_price for cart_book in cart_books)

    return render(request, 'bookstore/cart.html', {'cart_books': cart_books, 'total_price': total_price})

@login_required
def remove_from_cart(request, cart_book_id):
    cart_book = get_object_or_404(CartBook, id=cart_book_id)

    # Delete the CartBook instance
    cart_book.delete()

    return redirect('view_cart')


@login_required
def place_order(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_books = cart.cartbook_set.all()

    total_price = sum(cart_book.book.price * cart_book.quantity for cart_book in cart_books)  # Calculate the total price here

    # If the form is submitted
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Create a new order
            order = Order.objects.create(user=request.user, total_price=total_price)

            for cart_book in cart_books:
                # Create an order item for each book in the cart
                order_item = OrderItem.objects.create(order=order, book=cart_book.book, quantity=cart_book.quantity, item_price=cart_book.book.price * cart_book.quantity)

            # Clear the user's cart
            cart.books.clear()

            # Add user details to the order (customize as needed)
            order.first_name = form.cleaned_data['first_name']
            order.last_name = form.cleaned_data['last_name']
            order.phone_number = form.cleaned_data['phone_number']
            order.email = form.cleaned_data['email']
            order.address = form.cleaned_data['address']
            order.zip_code = form.cleaned_data['zip_code']
            order.save()

            messages.success(request, 'Order placed successfully!')
            return render(request, 'bookstore/place_order.html', {'order_placed': True, 'order': order})

    else:
        form = OrderForm()

    return render(request, 'bookstore/place_order.html', {'form': form, 'cart_books': cart_books, 'total_price': total_price})