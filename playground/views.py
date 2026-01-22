from django.core.mail import send_mail, BadHeaderError
from django.shortcuts import render


def hello_view(request, name):
    try:
        send_mail("subject", "message", "matyostsegay@gmail.com", ["mati@gamil.com"])
    except BadHeaderError:
        pass
    context = {"name": name}
    return render(request, "playground/email.html", context)
