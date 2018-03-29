from django.contrib import auth, messages
from django.shortcuts import render, redirect, render_to_response, HttpResponse
from django.template.context_processors import csrf
from accounts.forms import UserRegistrationForm, UserLoginForm, EditProfileForm, ProfilePictureForm, StatusForm
from django.contrib.auth.decorators import login_required
from models import Crush, Status, Likers, Wink, Notification
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Q
from django.template import RequestContext
import json
User = get_user_model()


###########################################################

#Authentication#




def register(request, register_form=UserRegistrationForm):



    if request.user.is_authenticated():
        return redirect(profile)

    if request.method == 'POST':


            form = register_form(request.POST)
            if form.is_valid():

                form.save()
                user = auth.authenticate(email=request.POST.get('email'), password=request.POST.get('password1'))

                if user:


                    email = request.POST.get('email')
                    first = request.POST.get('first_name')
                    sur = request.POST.get('last_name')

                    users = User.objects.all().count()

                    message = first + ' ' + sur + ' just registered with email: ' + email + ',' + ' Total users now: ' + str(users)

                    send_mail('New Fleeky User', message, 'ronanhiggins8@gmail.com', ['ronan.higgins@ucdconnect.ie'], fail_silently=False)

                    messages.error(request, "Congratulations you have successfully registered! Please log in above.")
                    return redirect(logout)

                elif not user:
                    messages.error(request, "You have made an error. Please register again.")
                    return redirect(register)


    form = register_form()
    form2 = UserLoginForm()


    args = {'form': form, 'form2': form2}
    args.update(csrf(request))

    return render(request, 'landing.html', args)


def login(request, success_url=None):



    if request.method == 'POST':

        form = UserLoginForm(request.POST)

        if form.is_valid():
            user = auth.authenticate(email=request.POST.get('email'), password=request.POST.get('password'))

            if user is not None:
                auth.login(request, user)




                return redirect(profile)

            else:
                messages.error(request, "Unable to log you in! Please try again.")

                return redirect(register)

        else:

            messages.error(request, "Unable to log you in! Please try again.")

            return redirect(register)


def logout(request):
    auth.logout(request)
    return redirect(register)




###########################################################


#Profile#


def edit_profile(request):

    notifications = Notification.objects.filter(user=request.user, viewed=False)

    whichuser = request.user

    if request.method == 'POST':

        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(profile)




    form = EditProfileForm(instance=request.user)


    args = {'whichuser': whichuser, 'notifications': notifications}
    args.update(csrf(request))
    args['form'] = form

    return render(request, 'editprofile.html', args)

def edit_profilepicture(request):


    if request.method == 'POST':

        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(profile)






@login_required
def profile(request, id=None):

    sent = 2

    first_login = User.objects.filter(pk=request.user.id).values_list('first_login', flat=True)

    user_first_login = first_login[0]

    if request.user.date_joined.date() == request.user.last_login.date() and user_first_login:


        User.objects.filter(pk=request.user.id).update(first_login = False)

        #Notification.objects.create(message="Welcome " + request.user.first_name + "!", user=request.user)

        print '1'

        first_time_login = 1

    else:

        print '2'

        first_time_login = 2

    unlock = False

    fleekyvalue = 0


    #get everything that request.user has liked and if the status == to a liked status then change the html

    likers = Likers.objects.filter(liker=request.user)

    notifications = Notification.objects.filter(user=request.user, viewed=False)





    if request.method == "POST":

        form = StatusForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.wall = request.user
            print post.author
            post.save()
            return redirect(profile)


    if id: #if navigating to another page

        first_otherprofile = User.objects.filter(pk=request.user.id).values_list('first_otherprofile', flat=True)


        user_first_login2 = first_otherprofile[0]

        if request.user.date_joined.date() == request.user.last_login.date() and user_first_login2:

            User.objects.filter(pk=request.user.id).update(first_otherprofile = False)

            first_time_login = 3


        users = None



        whichuser = User.objects.get(pk=id)

        whichuser.page_views += 1

        whichuser.save()


        switch = True
        posts = Status.objects.filter(Q(author_id=id) | Q(wall_id=id)).order_by('-created_date')

        #Queries a list of all the crushes of the users page navigated to and excludes to current authorised user
        crushes = Crush.objects.filter(Q(creator=whichuser) | Q(crush=whichuser)).exclude(Q(creator=request.user) | Q(crush=request.user)) #should be and?

        if Wink.objects.filter(initiator=request.user, receiver=whichuser):

            sent = 1

        #Queries the crush databse to check if the profile navigated to is already a friend or not.
        if Crush.objects.filter(creator=request.user, crush=whichuser) or Crush.objects.filter(creator=whichuser, crush=request.user):



            #checks if the relationships points are >= 3. If true, it unlocks a new feature on the page.
            if Crush.objects.filter(creator=request.user, crush=whichuser):

                points1 = Crush.objects.get(creator=request.user, crush=whichuser)

                fleekyvalue = points1.points

                if points1.points >= 5:

                    unlock = True

            elif Crush.objects.filter(creator=whichuser, crush=request.user):

                points2 = Crush.objects.get(creator=whichuser, crush=request.user)

                fleekyvalue = points2.points

                if points2.points >= 5:

                    unlock = True



            isprofilefriend = True

        else:

            isprofilefriend = False





    else: #if navigating to users page

        users = None


        mycrushes = Crush.objects.filter(Q(creator=request.user) | Q(crush=request.user)).values_list('crush', flat=True)

        mycrushes2 = Crush.objects.filter(Q(creator=request.user) | Q(crush=request.user)).values_list('creator', flat=True)


        if request.user.seeking == None:

            print '5'

            users = User.objects.order_by('?').exclude(Q(id=request.user.id) | Q(id__in=mycrushes) | Q(id__in=mycrushes2))[:4] #potential to slow down server big time, find alternative to '?'




        #Gay man seeking man
        if request.user.seeking == 'Male' and request.user.gender == 'Male':

            number_users = User.objects.filter(gender='Male').count()

            users = User.objects.filter(Q(gender='Male') & Q(seeking='Male')).exclude(Q(id=request.user.id) | Q(id__in=mycrushes) | Q(id__in=mycrushes2))[:4]



        #Straight man seeking woman
        elif request.user.seeking == 'Female' and request.user.gender == 'Male':

            number_users = User.objects.filter(gender='Female').count()

            users = User.objects.filter(Q(gender='Female') & Q(seeking='Male')).exclude(Q(id=request.user.id) | Q(id__in=mycrushes) | Q(id__in=mycrushes2))[:4]


        #Straight woman seeking man
        elif request.user.seeking == 'Male' and request.user.gender == 'Female':

            number_users = User.objects.filter(gender='Male').count()

            users = User.objects.filter(Q(gender='Male') & Q(seeking='Female')).exclude(Q(id=request.user.id) | Q(id__in=mycrushes) | Q(id__in=mycrushes2))[:4]


        #Gay woman seeking woman
        elif request.user.seeking == 'Female' and request.user.gender == 'Female':

            number_users = User.objects.filter(gender='Female').count()

            users = User.objects.filter(Q(gender='Female') & Q(seeking='Female')).exclude(Q(id=request.user.id) | Q(id__in=mycrushes) | Q(id__in=mycrushes2))[:4]




        whichuser = request.user
        switch = False
        crushes = Crush.objects.filter(Q(creator=whichuser) | Q(crush=whichuser)).order_by('-points')
        isprofilefriend = False
        posts = Status.objects.filter(Q(author_id=request.user) | Q(wall_id=request.user)).order_by('-created_date')

    statusform = StatusForm()
    profilepicform = ProfilePictureForm()


    return render(request, 'profile.html', {'sent': sent, 'first_time_login': first_time_login, 'users': users, 'fleekyvalue': fleekyvalue, 'unlock': unlock,'notifications':notifications, 'likers': likers, 'posts': posts, 'profilepicform': profilepicform, 'statusform': statusform, 'whichuser': whichuser, 'switch': switch, 'crushes': crushes, 'isprofilefriend': isprofilefriend})


def wall(request, id):

    whichuser = User.objects.get(pk=id)

    if request.method == "POST":

        form = StatusForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.wall = whichuser
            print post.author
            post.save()
            Notification.objects.create(message=request.user.first_name + ' ' + request.user.last_name + " posted on your wall", user=whichuser)
            #Notification.objects.create(message=creator.first_name + ' ' + creator.last_name + " added you!", user=crush)

            return redirect(profile, id=id)



def like(request):


    usercheck = request.user

    #likers = Likers.objects.filter(liker=usercheck)

    if request.method == 'GET':


        cat_id = request.GET['category_id']
        whichbutton = request.GET['button_type']


        if whichbutton =='like' or whichbutton == 'dislike':


            likes = Status.objects.get(id=cat_id)

            if whichbutton == 'like':


                if usercheck != likes.author and not Likers.objects.filter(status=likes, liker=usercheck).exists():

                    theuser = User.objects.get(pk=likes.author_id)

                    Notification.objects.create(message=usercheck.first_name + ' ' + usercheck.last_name + " liked your fleek!", user=theuser)
                    Likers.objects.create(status=likes, liker=usercheck)

                    likes.likes += 1
                    likes.save()

                    #

                    if Crush.objects.filter(creator=usercheck, crush=theuser) or Crush.objects.filter(creator=theuser, crush=usercheck):

                        if Crush.objects.filter(creator=usercheck, crush=theuser):

                            points = Crush.objects.get(creator=usercheck, crush=theuser)

                            points.points += 1
                            points.save()

                        elif Crush.objects.filter(creator=theuser, crush=usercheck):

                            points = Crush.objects.get(creator=theuser, crush=usercheck)

                            points.points += 1
                            points.save()

                likers = Likers.objects.get(liker=request.user, status=likes)

                print likers


                payload = {'payload1': likes.likes, 'payload2': 1}

                return HttpResponse(json.dumps(payload), content_type='application/json')



            elif whichbutton == 'dislike':

                theuser = User.objects.get(pk=likes.author_id)

                if Crush.objects.filter(creator=usercheck, crush=theuser) or Crush.objects.filter(creator=theuser, crush=usercheck):

                        if Crush.objects.filter(creator=usercheck, crush=theuser):

                            points = Crush.objects.get(creator=usercheck, crush=theuser)

                            points.points -= 1
                            points.save()

                        elif Crush.objects.filter(creator=theuser, crush=usercheck):

                            points = Crush.objects.get(creator=theuser, crush=usercheck)

                            points.points -= 1
                            points.save()



                if usercheck != likes.author and Likers.objects.filter(status=likes, liker=usercheck).exists():

                    Likers.objects.filter(status=likes, liker=usercheck).delete()

                    likes.likes -= 1
                    likes.save()


        elif whichbutton == 'wink':


            initiator = request.user
            receiver = User.objects.get(pk=cat_id)

            theuser = User.objects.get(pk=receiver.id)



            if Wink.objects.filter(Q(initiator=initiator, receiver=receiver) | Q(initiator=receiver, receiver=initiator)):



                #increments the relationships points by 1 if a poke is returned after initiated
                if Crush.objects.filter(creator=initiator, crush=receiver) or Crush.objects.filter(creator=receiver, crush=initiator):

                    if Crush.objects.filter(creator=initiator, crush=receiver):

                        points = Crush.objects.get(creator=initiator, crush=receiver)

                        if points.points < 5:

                            points.points += 1
                            points.save()

                    elif Crush.objects.filter(creator=receiver, crush=initiator):

                        points = Crush.objects.get(creator=receiver, crush=initiator)

                        if points.points <5:

                            points.points += 1
                            points.save()





                a = Wink.objects.filter(Q(initiator=initiator, receiver=receiver) | Q(initiator=receiver, receiver=initiator))

                a.delete()

                b = Wink.objects.create(initiator=initiator, receiver=receiver)
                b.save()

                Notification.objects.create(message=usercheck.first_name + ' ' + usercheck.last_name + " winked at you!", user=theuser)

                return HttpResponse()


            else:

                a = Wink.objects.create(initiator=initiator, receiver=receiver)
                a.save()
                #Notification.objects.create(message=usercheck.first_name + ' ' + usercheck.last_name + " winked at you!", user=theuser)

                return HttpResponse()


        elif whichbutton == 'delete':

            status = Status.objects.get(id=cat_id)

            status.delete()

            return HttpResponse()

        elif whichbutton == 'markasread':

            print "got to this point"

            #Notification.objects.filter(pk=cat_id).update(viewed=True)

            Notification.objects.filter(pk=cat_id).delete()

            return HttpResponse()

        elif whichbutton == 'crush':

            creator = request.user

            #the friend is always the id
            crush = User.objects.get(pk=cat_id)

            Notification.objects.create(message=creator.first_name + ' ' + creator.last_name + " added you!", user=crush)

            newcrush = Crush.objects.create(creator=creator, crush=crush)
            newcrush.save()

            return HttpResponse()






        payload = {'payload1': likes.likes, 'payload2': 2}
        return HttpResponse(json.dumps(payload), content_type='application/json')



def fleekyvalue(request):

    user_id = request.GET['user_id']

    print "then user id is: " + user_id


    notif = Notification.objects.filter(user_id=user_id).order_by('-id')[0]

    if notif.viewed == False:

        payload = {'message': notif.message, 'messageid': notif.id}

        return HttpResponse(json.dumps(payload), content_type='application/json')

    else:

        payload = {'message': 1}
        return HttpResponse(json.dumps(payload), content_type='application/json')



























def search_titles(request):


    """crushes = Crush.objects.filter(Q(creator=request.user) | Q(crush=request.user)).values_list('crush', flat=True)

    crushes2 = Crush.objects.filter(Q(creator=request.user) | Q(crush=request.user)).values_list('creator', flat=True)"""



    if request.method == "POST":

        search_text = request.POST['search_text']

    else:

        search_text = ''

    users = User.objects.filter(first_name__contains=search_text).exclude(id=request.user.id)




    """#man seeking man
    if request.user.seeking == 'Male' and request.user.gender == 'Male':

        users = User.objects.filter(Q(first_name__contains=search_text) & Q(gender='Male') & Q(seeking='Male')).exclude(id=request.user.id)



    #man seeking woman
    elif request.user.seeking == 'Female' and request.user.gender == 'Male':

        users = User.objects.filter(Q(first_name__contains=search_text) & Q(gender='Female') & Q(seeking='Male')).exclude(id=request.user.id)


    #woman seeking man
    elif request.user.seeking == 'Male' and request.user.gender == 'Female':

        users = User.objects.filter(Q(gender='Male') & Q(seeking='Female')).exclude(id=request.user.id)


    #woman seeking woman
    elif request.user.seeking == 'Female' and request.user.gender == 'Female':

        users = User.objects.filter(Q(first_name__contains=search_text) & Q(gender='Female') & Q(seeking='Female')).exclude(id=request.user.id)"""



    return render_to_response('ajax_search.html', {'results' : users})



def addcrush(request, id, id2=None):

    #the creator is always the user
    creator = request.user

    #the friend is always the id
    crush = User.objects.get(pk=id)

    #Notification.objects.create(message=creator.first_name + ' ' + creator.last_name + " added you as a crush!", user=crush)

    if Crush.objects.filter(creator=creator, crush=crush) or Crush.objects.filter(creator=crush, crush=creator) :

        return redirect(profile)

    else:

        newcrush = Crush.objects.create(creator=creator, crush=crush)
        newcrush.save()

        Notification.objects.create(message=creator.first_name + ' ' + creator.last_name + " added you!", user=crush)


        if id2 != str(1):

            return redirect(profile, id=id)

        else:

            return redirect(users)





def removecrush(request, id):

    #the creator is always the user
    creator = request.user

    #the friend is always the id
    crush = User.objects.get(pk=id)

    Crush.objects.filter(Q(creator=creator, crush=crush) | Q(creator=crush, crush=creator)).delete()

    return redirect(profile, id=id)





def createwink(request, id, id2=None):


    initiator = request.user
    receiver = User.objects.get(pk=id)

    if Wink.objects.filter(Q(initiator=initiator, receiver=receiver) | Q(initiator=receiver, receiver=initiator)):

        a = Wink.objects.filter(Q(initiator=initiator, receiver=receiver) | Q(initiator=receiver, receiver=initiator))

        a.delete()

        b = Wink.objects.create(initiator=initiator, receiver=receiver)
        b.save()

        if id2 == str(1): #used as a trigger to determine whether on newsfeed or not. Passes number 1 from feed in order for correct redirection.

            return redirect(newsfeed)


        else:

            return redirect(profile, id=id)



    else:

        a = Wink.objects.create(initiator=initiator, receiver=receiver)
        a.save()


        if id2 == str(1):

            return redirect(newsfeed)

        else:

            return redirect(profile, id=id)








###########################################################


#Newsfeed#



def newsfeed(request):

    first_feed = User.objects.filter(pk=request.user.id).values_list('first_feed', flat=True)

    user_first_feed = first_feed[0]

    if request.user.date_joined.date() == request.user.last_login.date() and user_first_feed:

        User.objects.filter(pk=request.user.id).update(first_feed = False)

        #Notification.objects.create(message="All your notifictions will appear here! ", user=request.user)

        print '1'

        first_time_login = 1

    else:

        print '2'

        first_time_login = 2

    likers = Likers.objects.filter(liker=request.user)

    whichuser = request.user


    if request.method == "POST":

        form = StatusForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.wall = request.user
            print post.author
            post.save()
            return redirect(newsfeed)

    else:

        form = StatusForm()


    winks = Wink.objects.filter(receiver=request.user)

    crushes = Crush.objects.filter(Q(creator=request.user) | Q(crush=request.user)).values_list('crush', flat=True)

    crushes2 = Crush.objects.filter(Q(creator=request.user) | Q(crush=request.user)).values_list('creator', flat=True)

    crushcount = Crush.objects.filter(Q(creator=request.user) | Q(crush=request.user)).count()
    statuscount = Status.objects.filter(author_id=request.user).count()
    posts = Status.objects.order_by('-created_date').filter(Q(author_id__in=crushes) | Q(author_id__in=crushes2) | Q(author_id=request.user))


    return render(request, 'newsfeed.html', {'crushcount': crushcount, 'statuscount': statuscount ,'first_time_login': first_time_login,'whichuser': whichuser, 'likers': likers, 'form': form, 'posts': posts, 'winks': winks})





###########################################################


#Users#


def users(request):

    crushes = Crush.objects.filter(Q(creator=request.user) | Q(crush=request.user)).values_list('crush', flat=True)

    crushes2 = Crush.objects.filter(Q(creator=request.user) | Q(crush=request.user)).values_list('creator', flat=True)

    whichuser = request.user

    #man seeking man
    if request.user.seeking == 'Male' and request.user.gender == 'Male':

        number_users = User.objects.filter(gender='Male').count()

        users = User.objects.filter(Q(gender='Male') & Q(seeking='Male')).exclude(Q(id=request.user.id) | Q(id__in=crushes) | Q(id__in=crushes2))



    #man seeking woman
    elif request.user.seeking == 'Female' and request.user.gender == 'Male':

        number_users = User.objects.filter(gender='Female').count()

        users = User.objects.filter(Q(gender='Female') & Q(seeking='Male')).exclude(Q(id=request.user.id) | Q(id__in=crushes) | Q(id__in=crushes2))


    #woman seeking man
    elif request.user.seeking == 'Male' and request.user.gender == 'Female':

        number_users = User.objects.filter(gender='Male').count()

        users = User.objects.filter(Q(gender='Male') & Q(seeking='Female')).exclude(Q(id=request.user.id) | Q(id__in=crushes) | Q(id__in=crushes2))


    #woman seeking woman
    elif request.user.seeking == 'Female' and request.user.gender == 'Female':

        number_users = User.objects.filter(gender='Female').count()

        users = User.objects.filter(Q(gender='Female') & Q(seeking='Female')).exclude(Q(id=request.user.id) | Q(id__in=crushes) | Q(id__in=crushes2))


    return render(request, 'users.html', {'number_users': number_users, 'whichuser': whichuser, 'users': users})


