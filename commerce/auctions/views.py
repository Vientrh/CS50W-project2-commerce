from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Category, Listing, Comment, Bid


def index(request):
    activeListings = Listing.objects.filter(active=True)
    allCategory = Category.objects.all()
    return render(request, "auctions/index.html",{
        "categories": allCategory,
        "listings":activeListings
    })

def createListing(request):
    if request.method == "GET":
        allCategory = Category.objects.all()
        return render(request, "auctions/create.html", {
            "categories": allCategory
        })
    else:
        #Get the data from the form
        title = request.POST["title"]
        description = request.POST["description"]
        price = request.POST["price"]
        imageurl = request.POST["imageurl"]
        category = request.POST["category"]

        currentUser = request.user
        categoryData = Category.objects.get(categoryName=category)
        #Create a bid
        bid = Bid(bid=float(price), user=currentUser)
        bid.save()
        #Create a new listing object & insert to DB
        newListing = Listing(
            title = title,
            description = description,
            price = bid,
            imageUrl = imageurl,
            category = categoryData,
            owner = currentUser
        )
        newListing.save()
        #redirect to index page
        return HttpResponseRedirect(reverse("index"))

def addBid(request,id):
    newBid = request.POST['newBid']
    listingData = Listing.objects.get(pk=id)
    allCmt = Comment.objects.filter(listing=listingData)
    #boolean
    isListing = request.user in listingData.watchlist.all()
    isOwner = request.user.username == listingData.owner.username
    if int(newBid) > listingData.price.bid:
        updateBid = Bid(
            user=request.user,
            bid=int(newBid)
        )
        updateBid.save()
        listingData.price = updateBid
        listingData.save()
        return render(request, "auctions/listing.html", {
            "listing":listingData,
            "message":"successfully updated bid",
            "update": True,
            "isListing": isListing,
            "allComment":allCmt,
            "isOwner": isOwner,
        })
    else:
        return render(request, "auctions/listing.html", {
            "listing":listingData,
            "message":"Fail to updated bid",
            "update": False,
            "isListing": isListing,
            "allComment":allCmt,
            "isOwner": isOwner,
        })

def listing(request, id):
    listingData = Listing.objects.get(pk=id)
    allCmt = Comment.objects.filter(listing=listingData)
    #boolean
    isListing = request.user in listingData.watchlist.all()
    isOwner = request.user.username == listingData.owner.username

    return render(request, "auctions/listing.html", {
        "listing":listingData,
        "isListing": isListing,
        "allComment":allCmt,
        "isOwner": isOwner,
    })

def closeAuction(request, id):
    listingData = Listing.objects.get(pk=id)
    listingData.active = False
    listingData.save()
    allCmt = Comment.objects.filter(listing=listingData)
    #boolean
    isListing = request.user in listingData.watchlist.all()
    isOwner = request.user.username == listingData.owner.username
    return render(request, "auctions/listing.html", {
        "listing":listingData,
        "message":"Congrats ! The auction was succesfully closed",
        "isListing": isListing,
        "allComment":allCmt,
        "isOwner": isOwner,
    })
    
def removeWatchlisting(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    #watchlist in models.Listing
    listingData.watchlist.remove(currentUser)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def addWatchlisting(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.add(currentUser)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def addComent(request, id):
    currentUser = request.user
    listingData = Listing.objects.get(pk=id)
    message = request.POST['newComment']

    newComment = Comment(
        author = currentUser,
        listing = listingData,
        message = message,
    )
    newComment.save()
    return HttpResponseRedirect(reverse("listing",args=(id, )))

def displayWatchlist(request):
    currentUser = request.user
    listings = currentUser.watchlist.all()
    return render(request, "auctions/watchlist.html",{
            "listings":listings,
    })

def displayCategory(request):
    if request.method == "POST":
        category = Category.objects.get(categoryName=request.POST['category'])
        activeListings = Listing.objects.filter(active=True, category=category)
        allCategory = Category.objects.all()
        return render(request, "auctions/index.html",{
            "categories": allCategory,
            "listings":activeListings,
        })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
