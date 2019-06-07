from django.shortcuts import render, redirect
from django.views import View
from .forms import ShoppingCartForm
from django.urls import reverse


class ShoppingCart(View):
    template = 'products/cart.html'

    def get(self, request):
        form = ShoppingCartForm()
        context = {
            'form': form,
            'title': 'Shopping cart'
        }
        return render(request,
                      self.template,
                      context)

    def post(self, request):
        form = ShoppingCartForm(request.POST)
        if form.is_valid():
            return redirect(reverse('success'))
        context = {
            'form': form,
            'title': 'Shopping cart'
        }
        return render(request,
                      self.template,
                      context)

class SuccessPage(View):
    template = 'products/success.html'

    def get(self, request):
        return render(request,
                       self.template,
                       {'title': "Order has been placed"})