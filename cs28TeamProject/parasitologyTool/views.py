from django.shortcuts import render

from parasitologyTool.decorators import clinicians_only, clinicians_researchers_only
from .models import *
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from .forms import *
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views import View, generic
from django.utils.decorators import method_decorator
from django.forms import formset_factory
from django.contrib.auth.mixins import LoginRequiredMixin
from itertools import chain


def index(request):
    parasite_list = Parasite.objects.order_by('name')
    context_dict = {'parasites': parasite_list}
    if (request.user.is_authenticated):
        context_dict['user_profile'] = UserProfile.objects.get(user=request.user)

    return render(request, 'parasitologyTool/index.html', context=context_dict)


def about(request):
    return render(request, 'parasitologyTool/about.html')


def public_content(request):
    context_dict = {}

    parasite_list = Parasite.objects.order_by('name')
    top_viewed_parasite = Parasite.objects.order_by('-views')[:5]
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
            parasite = Parasite(name=name, picture=picture)
            parasite.save()
            return redirect('/parasitologyTool/public_content')
        else:
            print(form.errors)

    return render(request, 'parasitologyTool/add_parasite.html', {'form': form})

@login_required
def add_article(request, parasite_id):
    try:
        parasite = Parasite.objects.get(id=parasite_id)
    except Parasite.DoesNotExist:
        return not_found(request)

    form = ArticleForm()
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)

        if form.is_valid():
            article = form.save(commit=False)
            article.parasite = parasite
            article.user = UserProfile.objects.get(user = request.user)
            article.save()
            return redirect(reverse("parasitologyTool:public_parasite_page", kwargs={'parasite_id':
                                                                                         parasite_id}))
        else:
            print(form.errors)

    context_dict = {'form': form, 'parasite': parasite}
    return render(request, 'parasitologyTool/add_article.html', context=context_dict)


@login_required
@clinicians_only
def add_post(request, parasite_id):
    try:
        parasite = Parasite.objects.get(id=parasite_id)
    except Parasite.DoesNotExist:
        return not_found(request)

    form = PostForm()
    if request.method == 'POST':
        form = PostForm(request.POST)
        images = request.FILES.getlist('images')
        if form.is_valid():
            post = form.save(commit=False)
            post.parasite = parasite
            post.user = UserProfile.objects.get(user=request.user)
            #post.likes = 0
            post.save()
            for image in images:
                ClinicalImage.objects.create(clinical_post=post, image=image, )
            return redirect(reverse("parasitologyTool:clinical_parasite_page", args=[parasite_id]))
        else:
            print(form.errors)

    return render(request, 'parasitologyTool/add_post.html', {'form': form})


def public_parasite_page(request, parasite_id):
    context_dict = {}
    try:
        parasite = Parasite.objects.get(id=parasite_id)
        article_list = parasite.article_set.all();
    except Parasite.DoesNotExist:
        return not_found(request)

    context_dict['parasite'] = parasite
    context_dict['articles'] = article_list
    context_dict['intro'] = parasite.intro
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
    if request.user.is_authenticated:
        return HttpResponse("cannot register while logged in")
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
    return render(request, 'parasitologyTool/register.html',
                  context={'user_form': user_form, 'profile_form': profile_form, 'registered': registered})


def user_login(request):
    if request.user.is_authenticated:
        return HttpResponse("you are already logged in")
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


@login_required
@clinicians_only
def clinical_portal(request):
    if UserProfile.objects.get(user=request.user).role != 'clinician':
        return HttpResponse("you are not authorised to view this page")
    context_dict = {}
    parasite_list = Parasite.objects.order_by('name')
    context_dict['parasite_list'] = parasite_list

    return render(request, 'parasitologyTool/clinical_portal.html', context=context_dict)


@login_required
@clinicians_researchers_only
def research_portal(request):
    context_dict = {}
    parasite_list = Parasite.objects.order_by('name')
    context_dict['parasite_list'] = parasite_list
    return render(request, 'parasitologyTool/research_portal.html', context=context_dict)


@login_required
@clinicians_only
def clinical_parasite_page(request, parasite_id):
    context_dict = {}
    try:
        parasite = Parasite.objects.get(id=parasite_id)
        posts = parasite.post_set.all()
    except Parasite.DoesNotExist:
        return not_found(request)

    pop_posts = Post.objects.order_by('-likes')[:5]

    context_dict['parasite'] = parasite
    context_dict['posts'] = posts
    context_dict['pop_posts'] = pop_posts
    return render(request, 'parasitologyTool/clinical_parasite_page.html', context=context_dict)


@login_required
@clinicians_researchers_only
def research_parasite_page(request, parasite_id):
    context_dict = {}
    try:
        parasite = Parasite.objects.get(id=parasite_id)
        research_posts = parasite.researchpost_set.all()
    except Parasite.DoesNotExist:
        return not_found(request)

    pop_posts = ResearchPost.objects.order_by('-likes')[:5]

    context_dict['parasite'] = parasite
    context_dict['research_posts'] = research_posts
    context_dict['pop_posts'] = pop_posts
    return render(request, 'parasitologyTool/research_parasite_page.html', context=context_dict)


@login_required
@clinicians_researchers_only
def add_research_post(request, parasite_id):
    try:
        parasite = Parasite.objects.get(id=parasite_id)
    except Parasite.DoesNotExist:
        return not_found(request)

    form = ResearchPostForm()
    if request.method == 'POST':
        form = ResearchPostForm(request.POST)
        images = request.FILES.getlist('images')
        files = request.FILES.getlist('files')
        if form.is_valid():
            post = form.save(commit=False)
            post.parasite = parasite
            post.user = UserProfile.objects.get(user=request.user)
            post.save()
            for image in images:
                ResearchImage.objects.create(research_post=post, image=image, )
            for file in files:
                ResearchFile.objects.create(research_post=post, file=file, )
            return redirect(reverse("parasitologyTool:research_parasite_page", args=[parasite_id]))
        else:
            print(form.errors)

    return render(request, 'parasitologyTool/add_research_post.html', {'form': form})


@login_required
@clinicians_researchers_only
def research_post_page(request, parasite_id, post_id):
    try:
        post = ResearchPost.objects.get(id=post_id)
    except ResearchPost.DoesNotExist:
        return not_found(request)

    context_dict = {}
    context_dict['post'] = post

    comment_form = CommentForm()
    reply_form = ReplyForm()
    if request.method == 'POST':
        if request.POST['comment_text'].strip() == "":
            return HttpResponseRedirect(request.path_info)
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.research_post = post
            comment.user = UserProfile.objects.get(user=request.user)
            comment.save()
            return redirect(reverse("parasitologyTool:research_post_page", args=[parasite_id, post_id]))
        else:
            print(comment_form.errors)

    context_dict['comment_form'] = comment_form
    context_dict['reply_form'] = reply_form
    return render(request, 'parasitologyTool/research_post_page.html', context=context_dict)


class LikePostView(View):
    @method_decorator(login_required)
    def get(self, request):
        post_id = request.GET['post_id']

        try:
            post = Post.objects.get(id=int(post_id))
        except Post.DoesNotExist:
            return HttpResponse(-1)
        except ValueError:
            return HttpResponse(-1)

        post.likes = post.likes + 1
        post.save()

        return HttpResponse(post.likes)


@login_required
@clinicians_only
def clinical_post_page(request, parasite_id, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except ResearchPost.DoesNotExist:
        return not_found(request)



    context_dict = {}
    context_dict['post'] = post

    comment_form = CommentForm()
    reply_form = ReplyForm()
    if request.method == 'POST':
        if request.POST['comment_text'].strip() == "":
            return HttpResponseRedirect(request.path_info)
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.clinical_post = post
            comment.user = UserProfile.objects.get(user=request.user)
            comment.save()
            return redirect(reverse("parasitologyTool:clinical_post_page", args=[parasite_id, post_id]))
        else:
            print(comment_form.errors)

    context_dict['comment_form'] = comment_form
    context_dict['reply_form'] = reply_form
    return render(request, 'parasitologyTool/clinical_post_page.html', context=context_dict)


def SearchPage(request):
    return render(request, 'parasitologyTool/search_page.html')

@login_required
def SearchResults(request):
    query = request.GET.get('q')
    object_list = User.objects.filter(username__icontains=query)
    user_list = []

    for user in object_list:
        user_list.append(UserProfile.objects.get(user=user))

    try:
        cur_user = UserProfile.objects.get(user=request.user)
        if cur_user.role == 'admin':
            is_admin = True
        else:
            is_admin = False
    except:
        return index(request)

    context_dict = {"results": user_list, "is_admin": is_admin}

    return render(request, 'parasitologyTool/search_results.html', context=context_dict)


@login_required
def AdminManage(request, username):
    try:
        cur_user = UserProfile.objects.get(user=request.user)
        if cur_user.role != 'admin':
            return index(request)
        user_s = User.objects.get(username=username)
        user = UserProfile.objects.get(user=user_s)
    except UserProfile.DoesNotExist:
        return not_found(request)

    context_dict = {}
    context_dict['user'] = user
    context_dict['changed'] = False

    if request.method == 'POST':
        prev_form = AdminManageForm(request.POST)
        if prev_form.is_valid():
            user.role = request.POST["role"]
            user.save()
            context_dict['changed'] = True
        else:
            print(prev_form.errors)

    manage_form = AdminManageForm(initial={'role': user.role})
    context_dict['form'] = manage_form
    context_dict['username'] = username
    return render(request, 'parasitologyTool/admin_manage.html', context=context_dict)


def UserPost(request, username):
    try:
        user_s = User.objects.get(username=username)
        user = UserProfile.objects.get(user=user_s)
        userpost1 = user.post_set.all()
        user_posts = chain(userpost1, user.researchpost_set.all())
    except User.DoesNotExist:
        return not_found(request)

    context_dict = {}
    context_dict['user_posts'] = user_posts

    return render(request, 'parasitologyTool/user_posts.html', context=context_dict)


def DeletePost(request, post_id, username):
    user_s = User.objects.get(username=username)
    user = UserProfile.objects.get(user=user_s)
    
    try:
        post = user.researchpost_set.get(id=post_id)
    except: 
        post = user.post_set.get(id=post_id)


    post.delete()

    return redirect(reverse('parasitologyTool:user_posts', args=[username]))


class AddLike(LoginRequiredMixin, View):
    def post(self, request, post_model, post_id, *args, **kwargs):
        if post_model == 'ResearchPost':
            post = ResearchPost.objects.get(id=post_id)
        else:
            post = Post.objects.get(id=post_id)
        print(post_model)
        is_like = False

        for like in post.likes.all():
            if like == request.user:
                is_like = True
                break

        if not is_like:
            post.likes.add(request.user)

        if is_like:
            post.likes.remove(request.user)

        data = {'message': "Successfully liked post.",
                'likes': post.likes.all().count(),
                'dislikes': post.dislikes.all().count()}
        return JsonResponse(data)


class AddDislike(LoginRequiredMixin, View):
    def post(self, request, post_model, post_id, *args, **kwargs):
        if post_model == 'ResearchPost':
            post = ResearchPost.objects.get(id=post_id)
        else:
            post = Post.objects.get(id=post_id)

        is_dislike = False

        for dislike in post.dislikes.all():
            if dislike == request.user:
                is_dislike = True
                break

        if not is_dislike:
            post.dislikes.add(request.user)

        if is_dislike:
            post.dislikes.remove(request.user)

        data = {'message': "Successfully disliked post.",
                'dislikes': post.dislikes.all().count(),
                'likes': post.likes.all().count()}
        return JsonResponse(data)

class CommentReplyView(View):
    def post(self, request, post_id, comment_id, *args, **kwargs):
        #post = ResearchPost.objects.get(id=post_id)
        parent_comment = Comment.objects.get(id=comment_id)
        form = ReplyForm(request.POST)
        if request.POST['reply_text'].strip() == "":
            return JsonResponse({'message':'empty string'})
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.parent_comment = parent_comment
            new_comment.user = UserProfile.objects.get(user=request.user)
            new_comment.save()
            data = {'reply_text': request.POST['reply_text'], 'comment_id':comment_id, 'username': new_comment.user.username}
            return JsonResponse(data)
        else:
            return JsonResponse({'message':'failed'})
