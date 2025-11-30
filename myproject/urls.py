from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def home(request):
    return HttpResponse("""
        <h1>PriceTrackerFuel está funcionando! 🎉</h1>
        <p>Deploy no Render realizado com sucesso!</p>
        <a href="/admin/">Admin</a>
    """)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
]