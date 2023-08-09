from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import User, Listing, Bid, Comment, Watchlist

NOIMAGE = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/2048px-No_image_available.svg.png"

def index(request):

    if Listing.objects.filter(active=True).exists():
        listings = Listing.objects.filter(active=True).all()

        # Add default image if no image is provided
        formated_listings = []
        for l in listings:
            if l.image == "":
                l.image = NOIMAGE

            if bids := Bid.objects.filter(listing=l).all():
                l.price = max([b.amount for b in bids])

            formated_listings.append(l)

        return render(request, "auctions/index.html", {
            "listings": formated_listings
        })

    return render(request, "auctions/index.html")


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

@login_required
def create(request):

    if request.method == "GET":

        title = request.GET.get("title")
        description = request.GET.get("description")
        price = request.GET.get("price")
        image = request.GET.get("image")
        category = request.GET.get("category")

        if title and description and price and category:

            listing = Listing(
                title=title,
                description=description,
                price=float(price),
                image=image if image else "",
                category=category,
                user=request.user
                )
            listing.save()
            
            return HttpResponseRedirect(reverse("index"))

    return render(request, "auctions/create.html")

def listing(request, listing_id):
    
        if request.method == "GET":
    
            user_logged_in = request.user.is_authenticated
            watchlisted = False

            if listing := Listing.objects.get(id=listing_id):
                bids = Bid.objects.filter(listing=listing).all()
                highest_bid = None
                owner = request.user == listing.user
                err = None

                if user_logged_in:

                    if Watchlist.objects.filter(user=request.user, listing=listing).first():
                        watchlisted = True

                    if request.GET.get("remove_wl"):
                        if watchlisted:
                            Watchlist.objects.filter(user=request.user, listing=listing).delete()
                            return HttpResponseRedirect(reverse("listing", args=(listing_id,)))
                    
                    if request.GET.get("add_wl"):
                        if not watchlisted:
                            wl = Watchlist(user=request.user, listing=listing)
                            wl.save()
                            return HttpResponseRedirect(reverse("listing", args=(listing_id,)))
                        
                elif any([request.GET.get("remove_wl"), request.GET.get("add_wl")]):
                    return HttpResponseRedirect(reverse("login"))

                if bids:
                    highest_bid = max([b.amount for b in bids])
                    highest_bidder = bids.get(amount=highest_bid).user
                    
                if bid := request.GET.get("bid"):

                    if not user_logged_in:
                        return HttpResponseRedirect(reverse("login"))

                    if not highest_bid:
                        # If no bids, set bid to starting price - 0.01
                        # to allow for bids to be placed equal to starting price in the future
                        highest_bid = float(listing.price) - 0.01

                    if float(bid) > highest_bid:
                        nbid = Bid(amount=float(bid), user=request.user, listing=listing)
                        nbid.save()
                        return HttpResponseRedirect(reverse("listing", args=(listing_id,)))
                    
                    else:
                        err = "Bid must be higher than current bid"

                if text := request.GET.get("comment"):
                    comment = Comment(text=text, user=request.user, listing=listing)
                    comment.save()
                    return HttpResponseRedirect(reverse("listing", args=(listing_id,)))

                if request.GET.get("close") and owner:

                    if not user_logged_in:
                        return HttpResponseRedirect(reverse("login"))

                    if listing := Listing.objects.get(id=listing_id):
                        listing.active = False
                        listing.save()

                # Add default image if no image is provided
                if listing.image == "":
                    listing.image = NOIMAGE
    
                return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "owner": owner,
                    "bid": {
                        "bid": highest_bid,
                        "user": highest_bidder
                    } if bids else None,
                    "comments": Comment.objects.filter(listing=listing).all(),
                    "watchlisted": watchlisted,
                    "err": err if err else None
                })
    
        return HttpResponseRedirect(reverse("index"))

def categories(request):


    categories = Listing.objects.values_list("category", flat=True).distinct()

    return render(request, "auctions/categories.html", {
        "categories": zip(categories, map(lambda c: c.capitalize(), categories))
    })

def category(request, category):
    
        listings = Listing.objects.filter(category=category).all()
    
        # Add default image if no image is provided
        formated_listings = []
        for l in listings:

            if not l.active:
                continue

            if l.image == "":
                l.image = NOIMAGE

            if bids := Bid.objects.filter(listing=l).all():
                l.price = max([b.amount for b in bids])
    
            formated_listings.append(l)
    
        return render(request, "auctions/category.html", {
            "listings": formated_listings,
            "category": category.capitalize()
        })

@login_required
def watchlist(request):

    if request.method == "GET":

        wl = Watchlist.objects.filter(user=request.user).all()
        listings = [w.listing for w in wl]

        # Add default image if no image is provided
        formated_listings = []
        for l in listings:

            if l.image == "":
                l.image = NOIMAGE

            if bids := Bid.objects.filter(listing=l).all():
                l.price = max([b.amount for b in bids])

            formated_listings.append(l)

        return render(request, "auctions/watchlist.html", {
            "listings": formated_listings
        })