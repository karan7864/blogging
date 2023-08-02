# appname/views.py
from .models import BlogPost, UserProfile,Comment, CommentReaction
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from .forms import CommentForm, RegistrationForm
from rest_framework import views, permissions
from rest_framework.response import Response
from rest_framework import status
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required


@login_required(login_url='login')
def like_comment(request, comment, blog):
    print("comment and blog", comment, blog)
    user_id = request.user
    users = get_object_or_404(UserProfile, email=user_id)
    username = users.fname
    print("username", username)
    blogs = BlogPost.objects.all()
    b = get_object_or_404(BlogPost, pk=blog)
    comments = b.comments.all()
    comment = get_object_or_404(Comment, id=comment)
    # Check if the user has already reacted to the comment
    reacted = CommentReaction.objects.filter(user=user_id, comment=comment).first()
    print(reacted)

    # If the user has not disliked the comment, create a new CommentReaction with reaction=False (dislike)
    if not reacted:
        print("new reaction will added")
        CommentReaction.objects.create(user=user_id, comment=comment, reaction=True)
        comment.likes += 1
        comment.save()
    if reacted:
        warning = "already reacted"
        return redirect('blog_post_list', blog=blog)

    # If the user has already disliked the comment, do nothing

    return redirect('blog_post_list', blog=blog)


@login_required(login_url='login')
def dislike_comment(request, comment, blog):
    # comments=Comment.objects.filter(id=blog)

    user_id = request.user
    users = get_object_or_404(UserProfile, email=user_id)
    username = users.fname

    print("username", username)
    blogs = BlogPost.objects.all()
    b = get_object_or_404(BlogPost, pk=blog)
    comments = b.comments.all()
    comment = get_object_or_404(Comment, id=comment)
    # Check if the user has already reacted to the comment
    reacted = CommentReaction.objects.filter(user=user_id, comment=comment, reaction=False).first()
    # If the user has not disliked the comment, create a new CommentReaction with reaction=False (dislike)
    if not reacted:
        print("hello world this karan")
        CommentReaction.objects.create(user=user_id, comment=comment, reaction=False)
        comment.dislikes += 1
        comment.save()
    else:
        warning = "already reacted"
        print("aadat hai kya")
        return redirect('blog_post_list', blog=blog)

    # If the user has already disliked the comment, do nothing

    return redirect('blog_post_list', blog=blog)


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = form.data["email"]
            password = form.data["password"]
            fname = form.data["fname"]
            lname = form.data["lname"]

            # Check if user with the given email already exists
            user_exists = UserProfile.objects.filter(email=email).exists()

            if not user_exists:
                # Create and save the User model instance
                new_user = User.objects.create_user(first_name=fname, last_name=lname, username=email, email=email,
                                                    password=password, is_active=True)

                # Create and save the UserProfile model instance
                user_profile = UserProfile(fname=fname, lname=lname, password=password, email=email)
                user_profile.save()

                return redirect('login')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {"form": form})


def process_button_click(request):
    if request.method == "POST":
        blog = request.POST.get('blog', '')
        comment = request.POST.get('comment', '')
        print(blog, comment)

        if 'like' in request.POST:
            return redirect('like_comment', comment=comment, blog=blog)
        if 'dislike' in request.POST:
            print("hello")
            return redirect('dislike_comment', comment=comment, blog=blog)
        return redirect("login")


@login_required(login_url='login')
def blog_post(request, blog):
    user_id = request.user
    user = get_object_or_404(UserProfile, email=user_id)
    username = user.fname
    blogs = BlogPost.objects.all()
    b = get_object_or_404(BlogPost, pk=blog)
    if request.method == 'POST':

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog_post = b
            comment.author = username
            comment.save()
            return redirect('blog_post_list', blog)


    else:
        form = CommentForm()

    comments = b.comments.all()

    return render(request, 'blog.html', {'blog': b, 'form': form, 'comments': comments, "username": username})

    # return render(request, 'blog.html', {'blog': b})


def user_login(request):
    # if request.user.is_authenticated:
    #     messages.add_message(request, messages.WARNING, "You already logged in.")
    #     return redirect('home')
    # else:
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(username=email, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            pass
    return render(request, 'login.html')


@login_required(login_url='login')
def home(request):
    user_id = request.user
    user = get_object_or_404(UserProfile, email=user_id)
    username = user.fname
    blogs = BlogPost.objects.all()
    return render(request, 'home.html', {'blogs': blogs, "username": username})


def get_user_totp_device(self, user, confirmed=None):
    devices = devices_for_user(user, confirmed=confirmed)
    for device in devices:
        if isinstance(device, TOTPDevice):
            return device


class TOTPCreateView(views.APIView):
    """
    Use this endpoint to set up a new TOTP device
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        device = get_user_totp_device(self, user)
        if not device:
            device = user.totpdevice_set.create(confirmed=False)
        url = device.config_url
        return Response(url, status=status.HTTP_201_CREATED)


class TOTPVerifyView(views.APIView):
    """
    Use this endpoint to verify/enable a TOTP device
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, token, format=None):
        user = request.user
        device = get_user_totp_device(self, user)
        if not device == None and device.verify_token(token):
            if not device.confirmed:
                device.confirmed = True
                device.save()
            return Response(True, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
