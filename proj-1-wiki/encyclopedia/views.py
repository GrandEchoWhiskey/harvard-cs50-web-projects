from django.shortcuts import render, redirect

from . import util


def index(request):

    if "random" in request.GET:
        if title := util.random_entry():
            return redirect("wiki", title)
        else:
            return render(request, "encyclopedia/error.html", {
                "error": "Page not found"
            })

    if query := request.GET.get("q"):
        if entry := util.get_entry(query):
            return render(request, "encyclopedia/wiki.html", {
                "entry": entry,
                "title": query
            })
        else:
            return render(request, "encyclopedia/index.html", {
                "title": "Search Results",
                "entries": util.search_entries(query)
            })
                            
    return render(request, "encyclopedia/index.html", {
        "title": "All Pages",
        "entries": util.list_entries()
    })

def wiki(request, title):

    if entry := util.get_entry(title):
        return render(request, "encyclopedia/wiki.html", {
            "entry": entry,
            "title": title
        })
    
    return render(request, "encyclopedia/error.html", {
        "error": "Page not found"
    })

def new(request):

    if title := request.GET.get("title"):
        content = request.GET.get("content")
        if util.get_entry(title):
            return render(request, "encyclopedia/error.html", {
                "error": "Page already exists"
            })
        else:
            util.save_entry(title, content)
            return render(request, "encyclopedia/wiki.html", {
                "entry": util.get_entry(title),
                "title": title
            })

    return render(request, "encyclopedia/new.html")

def edit(request):

    if title := request.GET.get("title"):

        if content := request.GET.get("content"):
            util.save_entry(title, content)
            return render(request, "encyclopedia/wiki.html", {
                "entry": util.get_entry(title),
                "title": title
            })

        if entry := util.get_entry(title, html=False):
            return render(request, "encyclopedia/edit.html", {
                "title": title,
                "entry": entry
            })

    return render(request, "encyclopedia/error.html", {
        "error": "Page not found"
    })