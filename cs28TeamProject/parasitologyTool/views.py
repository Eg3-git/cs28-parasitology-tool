from django.shortcuts import render
from .models import Post, UserProfile, Parasite, Article
from django.http import HttpResponse
from .forms import PostForm, UserForm, UserProfileForm , ArticleForm, ParasiteForm, ResearchPostForm
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views import View
from django.utils.decorators import method_decorator

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
        form = PostForm(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.parasite = parasite
            post.save()
            return redirect(reverse("parasitologyTool:clinical_parasite_page", args=[parasite_id]))
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

class ProfileView(View):
    def get_user_details(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        user_profile = UserProfile.objects.get_or_create(user=user)[0]
        form = UserProfileForm({'picture': user_profile.profile_picture,
                                'role': user_profile.role})

        return (user, user_profile, form)

    @method_decorator(login_required)
    def get(self, request, username):
        try:
            (user, user_profile, form) = self.get_user_details(username)
        except TypeError:
            return redirect(reverse('parasitologyTool:index'))

        context_dict = {'user_profile': user_profile,
                        'selected_user': user,
                        'form': form}

        return render(request, 'parasitologyTool/profile.html', context_dict)

    @method_decorator(login_required)
    def post(self, request, username):
        try:
            (user, user_profile, form) = self.get_user_details(username)
        except TypeError:
            return redirect(reverse('parasitologyTool:index'))

        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        if form.is_valid():
            form.save(commit=True)
            return redirect('parasitologyTool:profile', user.username)
        else:
            print(form.errors)

        context_dict = {'user_profile': user_profile,
                        'selected_user': user,
                        'form': form}

        return render(request, 'parasitologyTool/profile.html', context_dict)


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

def research_portal(request):
    context_dict = {}
    parasite_list = Parasite.objects.order_by('name')
    context_dict['parasite_list'] = parasite_list
    return render(request, 'parasitologyTool/research_portal.html', context = context_dict)

def clinical_parasite_page(request, parasite_id):
    context_dict = {}
    try:
        parasite = Parasite.objects.get(id=parasite_id)
        posts = parasite.post_set.all()
    except Parasite.DoesNotExist:
        return not_found(request)

    context_dict['parasite'] = parasite
    context_dict['posts'] = posts
    return render(request, 'parasitologyTool/clinical_parasite_page.html', context=context_dict)

def research_parasite_page(request, parasite_id):
    context_dict = {}
    try:
        parasite = Parasite.objects.get(id=parasite_id)
        research_posts = parasite.researchpost_set.all()
    except Parasite.DoesNotExist:
        return not_found(request)

    context_dict['parasite'] = parasite
    context_dict['research_posts'] = research_posts
    return render(request, 'parasitologyTool/research_parasite_page.html', context=context_dict)

def add_research_post(request, parasite_id):
    try:
        parasite = Parasite.objects.get(id=parasite_id)
    except Parasite.DoesNotExist:
        return not_found(request)

    form = ResearchPostForm()
    if request.method == 'POST':
        form = ResearchPostForm(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.parasite = parasite
            post.save()
            return redirect(reverse("parasitologyTool:research_parasite_page", args=[parasite_id]))
        else:
            print(form.errors)

    return render(request, 'parasitologyTool/add_research_post.html', {'form':form})
