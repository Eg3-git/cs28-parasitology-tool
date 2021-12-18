from django.shortcuts import render
from .models import Post, UserProfile, Parasite, Article
from django.http import HttpResponse
from .forms import PostForm, UserForm, UserProfileForm , ArticleForm, ParasiteForm
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib.auth.decorators import login_required


def index(request):
    parasite_list = Parasite.objects.order_by('name')
    context_dict = {'parasites': parasite_list}

    return render(request, 'parasitologyTool/index.html', context=context_dict)

def about(request):
    return render(request, 'parasitologyTool/about.html')

def public_content(request):
    context_dict = {}

    parasite_list = Parasite.objects.order_by('name')
    top_viewed_parasite = Parasite.objects.order_by('-views')[0]
    article_list = Article.objects.order_by('views')
    context_dict['parasites'] = parasite_list
    context_dict['articles'] = article_list
    context_dict['top_viewed_parasite'] = top_viewed_parasite

    return render(request, 'parasitologyTool/public_content.html', context=context_dict)

def add_parasite(request):
    form = ParasiteForm()

    if request.method == 'POST':
        form = ParasiteForm(request.POST, request.FILES)

        if form.is_valid():
            name = form.cleaned_data['name']
            picture = form.cleaned_data['picture']
            parasite = Parasite(name = name, picture=picture)
            parasite.save()
            return redirect('/parasitologyTool/public_content')
        else:
            print(form.errors)

    return render(request, 'parasitologyTool/add_parasite.html', {'form': form})

def add_article(request, parasite_id):
    try:
        parasite = Parasite.objects.get(id=parasite_id)
    except Parasite.DoesNotExist:
        return not_found(request)
    
    form = ArticleForm()
    if request.method == 'POST':
        form = ArticleForm(request.POST)

        if form.is_valid():
            article = form.save(commit=False)
            article.parasite = parasite
            article.save()
            return redirect(reverse("parasitologyTool:public_parasite_page", args=[parasite_id]))
        else:
            print(form.errors)

    return render(request, 'parasitologyTool/add_article.html', {'form':form})

def add_post(request, parasite_id):
    try:
        parasite = Parasite.objects.get(id=parasite_id)
    except Parasite.DoesNotExist:
        return not_found(request)

    form = PostForm()
    if request.method == 'POST':
        form = PostForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.parasite = parasite
            post.save()
            return redirect('/parasitologyTool/')
    else:
        print(form.errors)

    return render(request, 'parasitologyTool/add_post.html', {'form':form})

def public_parasite_page(request, parasite_id):
    context_dict = {}
    try:
        parasite = Parasite.objects.get(id=parasite_id)
        article_list = parasite.article_set.all();
    except Parasite.DoesNotExist:
        return not_found(request)

    context_dict['parasite'] = parasite
    context_dict['articles'] = article_list
    return render(request, 'parasitologyTool/public_parasite_page.html', context=context_dict)

def goto_parasite(request):
    if request.method == 'GET':
        parasite_id = request.GET.get('parasite_id')

        try:
            selected_parasite = Parasite.objects.get(id=parasite_id)
        except Parasite.DoesNotExist:
            return redirect(reverse('parasitologyTool:public_content'))

        selected_parasite.views = selected_parasite.views + 1
        selected_parasite.save()

        return redirect(reverse('parasitologyTool:public_parasite_page', args=[parasite_id]))
    return redirect(reverse('parasitologyTool:public_content'))

def register(request):
    registered = False
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']

            profile.save()
            registered = True
        else:
            print(user_form.errors, profile_form.errors)
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()
    return render(request, 'parasitologyTool/register.html', context = {'user_form': user_form, 'profile_form': profile_form, 'registered': registered})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return redirect(reverse('parasitologyTool:index'))
            else:
                return HttpResponse("Your account is disabled")
        else:
            print(f"Invalid login details: {username}, {password}")
            return HttpResponse("Invalid login details supplied.")
    else:
        return render(request, 'parasitologyTool/login.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect(reverse('parasitologyTool:index'))

def clinical_portal(request):
    context_dict = {}
    parasite_list = Parasite.objects.order_by('name')
    context_dict['parasite_list'] = parasite_list
    return render(request, 'parasitologyTool/clinical_portal.html', context = context_dict)

def clinical_parasite_page(request, parasite_id):
    context_dict = {}
    try:
        parasite = Parasite.objects.get(id=parasite_id)
        posts = parasite.post_set.all();
    except Parasite.DoesNotExist:
        return not_found(request)

    context_dict['parasite'] = parasite
    context_dict['posts'] = posts
    return render(request, 'parasitologyTool/clinical_parasite_page.html', context=context_dict)