from django.shortcuts import render
from .models import Category, Product, Cart, CartItem, Order
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from .forms import OrderForm, RegistrationForm, LoginForm
from decimal import Decimal
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth import login, authenticate
from django.db.models import Sum, Count
from django.db.models import Q
from django.views import View
# для прогнозирования
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pmdarima.arima import auto_arima
# для кластерного анализа
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import *
from matplotlib import rc
from sklearn.cluster import KMeans
from mpl_toolkits.mplot3d import Axes3D
from sklearn import preprocessing
# для рассылки по электронной почте
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
import openpyxl
import xlrd


def base_view(request):
    try:
        cart_id = request.session['cart_id']
        cart = Cart.objects.get(id=cart_id)
        request.session['total'] = cart.items.count()
    except:
        cart = Cart()
        cart.save()
        cart_id = cart.id
        request.session['cart_id'] = cart_id
        cart = Cart.objects.get(id=cart_id)
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    context = {
        'categories': categories,
        'products': products,
        'cart': cart,
    }
    return render(request, 'base.html', context)


# детальная страница товара
def product_view(request, product_slug):
    try:
        cart_id = request.session['cart_id']
        cart = Cart.objects.get(id=cart_id)
        request.session['total'] = cart.items.count()
    except:
        cart = Cart()
        cart.save()
        cart_id = cart.id
        request.session['cart_id'] = cart_id
        cart = Cart.objects.get(id=cart_id)
    categories = Category.objects.all()
    product = Product.objects.get(slug=product_slug)
    context = {
        'product': product,
        'categories': categories,
        'cart': cart,
    }
    return render(request, 'product.html', context)


# страница категории товаров, с фильтрацией по категории
def category_view(request, category_slug):
    categories = Category.objects.all()
    category = Category.objects.get(slug=category_slug)
    products_of_category = category.product_set.all()
    context = {
        'categories': categories,
        'category': category,
        'products_of_category': products_of_category,
    }
    return render(request, 'category.html', context)


# корзина товаров
def cart_view(request):
    try:
        cart_id = request.session['cart_id']
        cart = Cart.objects.get(id=cart_id)
        request.session['total'] = cart.items.count()
    except:
        cart = Cart()
        cart.save()
        cart_id = cart.id
        request.session['cart_id'] = cart_id
        cart = Cart.objects.get(id=cart_id)
    context = {
        'cart': cart,
    }
    return render(request, 'cart.html', context)


# добавление в корзину
def add_to_cart_view(request):
    try:
        cart_id = request.session['cart_id']
        cart = Cart.objects.get(id=cart_id)
        request.session['total'] = cart.items.count()
    except:
        cart = Cart()
        cart.save()
        cart_id = cart.id
        request.session['cart_id'] = cart_id
        cart = Cart.objects.get(id=cart_id)
    product_slug = request.GET.get('product_slug')
    product = Product.objects.get(slug=product_slug)
    cart.add_to_cart(product.slug)
    new_cart_total = 0.00
    for item in cart.items.all():
        new_cart_total += float(item.item_total)
    cart.cart_total = new_cart_total
    cart.save()
    return JsonResponse({'cart_total': cart.items.count(),
                         'cart_total_price': cart.cart_total})


# удаление из корзины
def remove_from_cart_view(request):
    try:
        cart_id = request.session['cart_id']
        cart = Cart.objects.get(id=cart_id)
        request.session['total'] = cart.items.count()
    except:
        cart = Cart()
        cart.save()
        cart_id = cart.id
        request.session['cart_id'] = cart_id
        cart = Cart.objects.get(id=cart_id)
    product_slug = request.GET.get('product_slug')
    product = Product.objects.get(slug=product_slug)
    cart.remove_from_cart(product.slug)
    new_cart_total = 0.00
    for item in cart.items.all():
        new_cart_total += float(item.item_total)
    cart.cart_total = new_cart_total
    cart.save()
    return JsonResponse({'cart_total': cart.items.count(),
                         'cart_total_price': cart.cart_total})


# изменение количества определённого товара в корзине
def change_item_qty(request):
    try:
        cart_id = request.session['cart_id']
        cart = Cart.objects.get(id=cart_id)
        request.session['total'] = cart.items.count()
    except:
        cart = Cart()
        cart.save()
        cart_id = cart.id
        request.session['cart_id'] = cart_id
        cart = Cart.objects.get(id=cart_id)
    qty = request.GET.get('qty')
    item_id = request.GET.get('item_id')
    cart.charge_qty(qty, item_id)
    cart_item = CartItem.objects.get(id=int(item_id))
    return JsonResponse({'cart_total': cart.items.count(),
                         'item_total': cart_item.item_total,
                         'cart_total_price': cart.cart_total})


# формирование предварительного заказа
def check_out_view(request):
    try:
        cart_id = request.session['cart_id']
        cart = Cart.objects.get(id=cart_id)
        request.session['total'] = cart.items.count()
    except:
        cart = Cart()
        cart.save()
        cart_id = cart.id
        request.session['cart_id'] = cart_id
        cart = Cart.objects.get(id=cart_id)
    context = {
        'cart': cart
    }
    return render(request, 'checkout.html', context)


# сздание заказа
def order_create_view(request):
    try:
        cart_id = request.session['cart_id']
        cart = Cart.objects.get(id=cart_id)
        request.session['total'] = cart.items.count()
    except:
        cart = Cart()
        cart.save()
        cart_id = cart.id
        request.session['cart_id'] = cart_id
        cart = Cart.objects.get(id=cart_id)

    form = OrderForm(request.POST or None)
    categories = Category.objects.all()
    context = {
        'form': form,
        'cart': cart,
        'categories': categories,
    }
    return render(request, 'order.html', context)


# оформление заказа
def make_order_view(request):
    try:
        cart_id = request.session['cart_id']
        cart = Cart.objects.get(id=cart_id)
        request.session['total'] = cart.items.count()
    except:
        cart = Cart()
        cart.save()
        cart_id = cart.id
        request.session['cart_id'] = cart_id
        cart = Cart.objects.get(id=cart_id)
    form = OrderForm(request.POST or None)
    categories = Category.objects.all()
    if form.is_valid():
        name = form.cleaned_data['name']
        last_name = form.cleaned_data['last_name']
        phone = form.cleaned_data['phone']
        buying_type = form.cleaned_data['buying_type']
        address = form.cleaned_data['address']
        comments = form.cleaned_data['comments']
        new_order = Order()
        new_order.user = request.user
        new_order.save()
        new_order.items.add(cart)
        new_order.first_name = name
        new_order.last_name = last_name
        new_order.phone = phone
        new_order.address = address
        new_order.buying_type = buying_type
        new_order.comments = comments
        new_order.total = cart.cart_total
        new_order.save()
        del request.session['cart_id']
        del request.session['total']
        return HttpResponseRedirect(reverse('thank_you'))
    return render(request, 'order.html', {'categories': categories})


# личный кабинет клиента с историей заказов
def account_view(request):
    order = Order.objects.filter(user=request.user).order_by('-id')
    context = {
        'order': order
    }
    return render(request, 'account.html', context)


def registration_view(request):
    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        new_user = form.save(commit=False)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        email = form.cleaned_data['email']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        new_user.username = username
        new_user.set_password(password)
        new_user.email = email
        new_user.last_name = last_name
        new_user.first_name = first_name
        new_user.save()
        login_user = authenticate(username=username, password=password)
        if login_user:
            login(request, login_user)
            return HttpResponseRedirect(reverse('base'))
    context = {
        'form': form,
    }
    return render(request, 'registration.html', context)


def login_view(request):
    form = LoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        login_user = authenticate(username=username, password=password)
        if login_user:
            login(request, login_user)
            return HttpResponseRedirect(reverse('base'))
    context = {
        'form': form
    }
    return render(request, 'login.html', context)


# график продаж
def orders_graf(request):
    order = Order.objects.values('date').annotate(total_day=Sum('total')) # получение данных из БД об общей сумме продаж за день
    category_description = Category.objects.all() # данные для отобрежения на странице
    product_description = Product.objects.all() # данные из БД для отобрадения таблици с перечнем товаров
    context = {
        'order': order,
        'product_description': product_description,
        'category_description': category_description
    }
    return render(request, 'orders_graf.html', context)


# график продаж отпределённого товара
def products_graf(request):
    number = request.GET.get('n') # получение номера товара из формы
    n = int(number)
    newprod = CartItem.objects.filter(Q(product=n)).values('date').annotate(sum_total=Sum('item_total')) # получение из БД данних об определённом продукте с общей суммой продаж за день
    product_name = Product.objects.filter(id=n) # получение названия продукта для отображения на странице
    context = {
        'newprod': newprod,
        'product_name': product_name
    }
    return render(request, 'products_graf.html', context)


# график продаж по категории
def category_graf(request):
    cat = request.GET.get('c') # получение данных из формы с номером категории
    c = int(cat)
    category = CartItem.objects.filter(Q(product__category_id=c)).values('date').annotate(sum_total=Sum('item_total')) # получение данных о продажах товаров определённой категории за день
    category_name = Category.objects.filter(id=c) # получение названия выбраной категории
    context = {
        'category': category,
        'category_name': category_name
    }
    return render(request, 'category_graf.html', context)


# график покупок отперелённого пользователя
class UserOrdersGrafView(View):
    template_name = 'user_orders_graf.html'

    def get(self, request, *args, **kwargs):
        query = self.request.GET.get('q') # из формы получение логина пользователя
        founded_user = Order.objects.filter(Q(user_id__username__contains=query)) # поиск в БД имени коиента в таблице с заказами
        context = {
            'founded_user': founded_user,
        }
        return render(self.request, self.template_name, context)


# прогнозирование продаж
def sales_forecasting(request):
    sales = Order.objects.values('date').annotate(total_day=Sum('total')) # получение данных из БД об общей сумме продаж за день
    data = pd.DataFrame(sales) # формирование pandas data frame

    # divide into train and validation set
    train = data[:int(0.9 * (len(data)))]
    valid = data[int(0.9 * (len(data))):]

    # preprocessing (since arima takes univariate series as input)
    train.drop('date', axis=1, inplace=True)
    valid.drop('date', axis=1, inplace=True)

    model = auto_arima(train, trace=True, error_action='ignore', suppress_warnings=True)
    forecast = model.predict(n_periods=len(valid))
    forecast = pd.DataFrame(forecast, index=valid.index, columns=['Prediction'])
    plt.figure(figsize=(16, 10))
    plt.plot(train, label='Train')
    plt.plot(valid, label='Valid')
    plt.plot(forecast, label='Prediction')
    plt.savefig('/home/olegsamsnote/PycharmProjects/CTshop/shop/ecomapp/static/graph/sales_forecasting.png') # сохранение результатов прогнозирования
    dataF = data # получение данных до анализа
    dataF['forecast'] = forecast # добавление к исходным данным столбец с пронозом
    # сохранение результатов прогноза в документ
    writer = pd.ExcelWriter('forecast.xls')
    dataF.to_excel(writer, 'forecast')
    writer.save()
    rb = xlrd.open_workbook('/home/olegsamsnote/PycharmProjects/CTshop/shop/forecast.xls', formatting_info=True) # отерытие созданного документа
    sheet = rb.sheet_by_index(0)
    Y = 0
    koef = []
    koef2 = []
    # оценка прогнозирования
    for i in range(83, 92):
        yR = sheet.cell_value(i, 2) # выбор ячейки столбца с реальными значениями
        yF = sheet.cell_value(i, 3) # выбор столбца с прогнозироваными значениями
        y = float(yR) - float(yF)
        koef.append(yR)
        koef2.append(yF)
        Y += y

    context = {
        'koef': koef,
        'koef2': koef2,
        'Y': Y

    }

    return render(request, 'sales_forecasting.html', context)


# прогнозирование продаж товаров определённой категории
def category_sales_forecasting(request):
    cat = request.GET.get('fc') # получение значение категории из формы
    c = int(cat)
    category = CartItem.objects.filter(Q(product__category_id=c)).values('date').annotate(sum_total=Sum('item_total'))
    category_name = Category.objects.filter(id=c)
    data = pd.DataFrame(category)

    # divide into train and validation set
    train = data[:int(0.6 * (len(data)))]
    valid = data[int(0.6 * (len(data))):]

    # preprocessing (since arima takes univariate series as input)
    train.drop('date', axis=1, inplace=True)
    valid.drop('date', axis=1, inplace=True)

    model = auto_arima(train, trace=True, error_action='ignore', suppress_warnings=True)
    forecast = model.predict(n_periods=len(valid))
    forecast = pd.DataFrame(forecast, index=valid.index, columns=['Prediction'])
    plt.figure(figsize=(16, 10))
    plt.plot(train, label='Train')
    plt.plot(valid, label='Valid')
    plt.plot(forecast, label='Prediction')
    plt.savefig('/home/olegsamsnote/PycharmProjects/CTshop/shop/ecomapp/static/graph/category_sales_forecasting.png')
    dataF = data
    dataF['forecast'] = forecast

    context = {
        # 'result': result,
        'dataF': dataF,
        'category_name': category_name,
    }
    return render(request, 'category_sales_forecasting.html', context)


# прогнозирование продаж определённого товара
def product_sales_forecasting(request):
    number = request.GET.get('fn')
    n = int(number)
    newprod = CartItem.objects.filter(Q(product=n)).values('date').annotate(sum_total=Sum('item_total'))
    product_name = Product.objects.filter(id=n)
    data = pd.DataFrame(newprod)

    # divide into train and validation set
    train = data[:int(0.6 * (len(data)))]
    valid = data[int(0.6 * (len(data))):]

    # preprocessing (since arima takes univariate series as input)
    train.drop('date', axis=1, inplace=True)
    valid.drop('date', axis=1, inplace=True)

    model = auto_arima(train, trace=True, error_action='ignore', suppress_warnings=True)
    forecast = model.predict(n_periods=len(valid))
    forecast = pd.DataFrame(forecast, index=valid.index, columns=['Prediction'])
    plt.figure(figsize=(16, 10))
    plt.plot(train, label='Train')
    plt.plot(valid, label='Valid')
    plt.plot(forecast, label='Prediction')
    plt.savefig('/home/olegsamsnote/PycharmProjects/CTshop/shop/ecomapp/static/graph/product_sales_forecasting.png')
    dataF = data
    dataF['forecast'] = forecast

    context = {
        # 'result': result,
        'dataF': dataF,
        'product_name': product_name,
    }
    return render(request, 'product_sales_forecasting.html', context)


# прогнозирование покупок клиента
def user_sales_forecasting(request):
    query = request.GET.get('fq')
    founded_user = Order.objects.filter(Q(user_id__username__contains=query)).values('date', 'total')
    data = pd.DataFrame(founded_user)

    # divide into train and validation set
    train = data[:int(0.6 * (len(data)))]
    valid = data[int(0.6 * (len(data))):]

    # preprocessing (since arima takes univariate series as input)
    train.drop('date', axis=1, inplace=True)
    valid.drop('date', axis=1, inplace=True)

    model = auto_arima(train, trace=True, error_action='ignore', suppress_warnings=True)
    forecast = model.predict(n_periods=len(valid))
    forecast = pd.DataFrame(forecast, index=valid.index, columns=['Prediction'])
    plt.figure(figsize=(16, 10))
    plt.plot(train, label='Train')
    plt.plot(valid, label='Valid')
    plt.plot(forecast, label='Prediction')
    plt.savefig('/home/olegsamsnote/PycharmProjects/CTshop/shop/ecomapp/static/graph/user_sales_forecasting.png')
    dataF = data
    dataF['forecast'] = forecast
    result = dataF.to_html()
    context = {
        'result': result,
        'dataF': dataF
    }
    return render(request, 'user_sales_forecasting.html', context)


# показывает рекомендуемое количество кластеров
def clusters_num(request):
    data_num = CartItem.objects.values('user_num', 'product_id', 'qty', 'item_total') # из БД получение данных определённых столбцов
    data_cn = pd.DataFrame(data_num) # формирование pandas data frame
    dataNorm = preprocessing.scale(data_cn) # нормализация данних

    data_dist = pdist(dataNorm, 'euclidean')
    data_linkage = linkage(data_dist, method='average')

    last = data_linkage[-10:, 2]
    last_rev = last[::-1]
    idxs = np.arange(1, len(last) + 1)
    plt.plot(idxs, last_rev)

    acceleration = np.diff(last, 2)
    acceleration_rev = acceleration[::-1]
    plt.plot(idxs[:-2] + 1, acceleration_rev)
    plt.savefig('/home/olegsamsnote/PycharmProjects/CTshop/shop/ecomapp/static/graph/clusters_num.png') # сохранения графика
    k = acceleration_rev.argmax() + 2
    context = {
        'k': k
    }
    return render(request, 'clusters_num.html', context)


# проведение кластерного анализа
def cluster_analysis(request):
    data_num = CartItem.objects.values('user_num', 'product_id', 'qty', 'item_total') # из БД получение данных определённых столбцов
    datac = pd.DataFrame(data_num) # формирование pandas data frame
    data_for_clust = datac.drop(datac.columns[0], axis=1).values # удаление первого столбца
    dataNorm = preprocessing.scale(datac) #  нормальзация данных

    kk = request.GET.get('ca') #  получение значение количества кластеров
    ca = int(kk)
    km = KMeans(n_clusters=ca).fit(dataNorm)

    fig = plt.figure(figsize=(15, 13)) # опредиление размера диаграммы рассеяния
    ax = fig.add_subplot(111, projection='3d') # указать, что график имеет три оси
    ax.scatter(data_for_clust[:, 0], data_for_clust[:, 1], data_for_clust[:, 2], c=km.labels_, cmap="Set2_r", s=60)
    ax.set_xlabel("Товар")
    ax.set_ylabel("Количество купленного товара")
    ax.set_zlabel("Стоимость")
    ax.set_title("Результат кластерного анализа")
    plt.savefig('/home/olegsamsnote/PycharmProjects/CTshop/shop/ecomapp/static/graph/analysis.png') # сохранение графика
    dataI = datac
    dataI['cluster_no'] = km.labels_
    writer = pd.ExcelWriter('clients.xls')
    dataI.to_excel(writer, 'KMeans')
    writer.save()
    return render(request, 'cluster_analysis.html')


# электронная рассылка всем клиентам, которые купили зерновой кофе
def coffee_zer_mail(request):
    email_data = Order.objects.values_list('user_id__id', 'user_id__email') # получение из таблицы оформленых заказов информацию о клиентах, которые уже совершили покупку
    clients_emails = pd.DataFrame(email_data)
    writer = pd.ExcelWriter('clients_emails.xls')
    clients_emails.to_excel(writer, 'emails')
    writer.save()
    user_list = []
    category_list = [36, 37, 38, 39, 51, 54] # список с номерами продуктов соответствующей категории
    rb = xlrd.open_workbook('/home/olegsamsnote/PycharmProjects/CTshop/shop/clients.xls', formatting_info=True)
    sheet = rb.sheet_by_index(0)
    # поиск клиентов, которые купили зерновой кофе
    for i in range(1, 865):
        valF = sheet.cell_value(i, 2) # столбец с номером продукта
        if valF in category_list: # если номер товара соответствует категории, то клиент добавляется в список клиентов для рассылки
            valB = sheet.cell_value(i, 1) # столбец с номером клиента
            if valB not in user_list:
                valU = int(valB)
                user_list.append(valU)
    user_email = []
    rb2 = xlrd.open_workbook('/home/olegsamsnote/PycharmProjects/CTshop/shop/clients_emails.xls', formatting_info=True) # открытие таблици с клиентами и их электронными адресами
    sheet2 = rb2.sheet_by_index(0)
    for j in range(1, 392):
        valC = sheet2.cell_value(j, 1) # столбец с номером клиента
        if valC in user_list: # если клинт есть с списке для рассылки, то его почта добавляется в список адресов
            valE = sheet2.cell_value(j, 2) # столбец с электронной почтой
            if valE not in user_email: # проверка наличия адреса в списке, если нет, то добавить
                user_email.append(valE)
    msg_html = render_to_string('send_content/assort_zer_coffee.html') # путь к html сообщению
    # указание темы письма, сообщения, адреса отправителя и списка получателей
    email = EmailMessage(subject='Расширение ассортимента в магазине CTshop!', body=msg_html, from_email='ctshop.project@gmail.com', to=user_email, )
    email.content_subtype = "html" # тип письма
    email.send() # отправка
    return render(request, 'coffee_zer_mail.html', context={'user_email': user_email})


# электронная рассылка всем клиентам, которые купили молотый кофе
def coffee_molot_mail(request):
    email_data = Order.objects.values_list('user_id__id', 'user_id__email')
    clients_emails = pd.DataFrame(email_data)
    writer = pd.ExcelWriter('clients_emails.xls')
    clients_emails.to_excel(writer, 'emails')
    writer.save()
    user_list = []
    category_list = [55, 56, 57, 58, 61, 62]
    rb = xlrd.open_workbook('/home/olegsamsnote/PycharmProjects/CTshop/shop/clients.xls', formatting_info=True)
    sheet = rb.sheet_by_index(0)
    for i in range(1, 865):
        # x = i + 1
        valF = sheet.cell_value(i, 2)
        if valF in category_list:
            valB = sheet.cell_value(i, 1)
            if valB not in user_list:
                valU = int(valB)
                user_list.append(valU)
    user_email = []
    rb2 = xlrd.open_workbook('/home/olegsamsnote/PycharmProjects/CTshop/shop/clients_emails.xls', formatting_info=True)
    sheet2 = rb2.sheet_by_index(0)
    for j in range(1, 392):
        valC = sheet2.cell_value(j, 1)
        if valC in user_list:
            valE = sheet2.cell_value(j, 2)
            if valE not in user_email:
                user_email.append(valE)
    msg_html = render_to_string('send_content/assort_molot_coffee.html')
    email = EmailMessage(subject='Расширение ассортимента в магазине CTshop!', body=msg_html, from_email='ctshop.project@gmail.com', to=user_email, )
    email.content_subtype = "html"
    email.send()
    return render(request, 'coffee_molot_mail.html', context={'user_email': user_email})


# электронная рассылка всем клиентам, которые купили растворимый кофе
def coffee_rastvor_mail(request):
    email_data = Order.objects.values_list('user_id__id', 'user_id__email')
    clients_emails = pd.DataFrame(email_data)
    writer = pd.ExcelWriter('clients_emails.xls')
    clients_emails.to_excel(writer, 'emails')
    writer.save()
    user_list = []
    category_list = [32, 33, 34, 35, 52, 53]
    rb = xlrd.open_workbook('/home/olegsamsnote/PycharmProjects/CTshop/shop/clients.xls', formatting_info=True)
    sheet = rb.sheet_by_index(0)
    for i in range(1, 865):
        valF = sheet.cell_value(i, 2)
        if valF in category_list:
            valB = sheet.cell_value(i, 1)
            if valB not in user_list:
                valU = int(valB)
                user_list.append(valU)
    user_email = []
    rb2 = xlrd.open_workbook('/home/olegsamsnote/PycharmProjects/CTshop/shop/clients_emails.xls', formatting_info=True)
    sheet2 = rb2.sheet_by_index(0)
    for j in range(1, 392):
        valC = sheet2.cell_value(j, 1)
        if valC in user_list:
            valE = sheet2.cell_value(j, 2)
            if valE not in user_email:
                user_email.append(valE)
    msg_html = render_to_string('send_content/assort_rastvor_coffee.html')
    email = EmailMessage(subject='Расширение ассортимента в магазине CTshop!', body=msg_html, from_email='ctshop.project@gmail.com', to=user_email, )
    email.content_subtype = "html"
    email.send()
    return render(request, 'coffee_rastvor_mail.html', context={'user_email': user_email})


# электронная рассылка всем клиентам, которые купили чай в пакетиках
def tea_paket_mail(request):
    email_data = Order.objects.values_list('user_id__id', 'user_id__email')
    clients_emails = pd.DataFrame(email_data)
    writer = pd.ExcelWriter('clients_emails.xls')
    clients_emails.to_excel(writer, 'emails')
    writer.save()
    user_list = []
    category_list = [40, 41, 42, 43, 44, 45, 47, 50]
    rb = xlrd.open_workbook('/home/olegsamsnote/PycharmProjects/CTshop/shop/clients.xls', formatting_info=True)
    sheet = rb.sheet_by_index(0)
    for i in range(1, 865):
        valF = sheet.cell_value(i, 2)
        if valF in category_list:
            valB = sheet.cell_value(i, 1)
            if valB not in user_list:
                valU = int(valB)
                user_list.append(valU)
    user_email = []
    rb2 = xlrd.open_workbook('/home/olegsamsnote/PycharmProjects/CTshop/shop/clients_emails.xls', formatting_info=True)
    sheet2 = rb2.sheet_by_index(0)
    for j in range(1, 392):
        valC = sheet2.cell_value(j, 1)
        if valC in user_list:
            valE = sheet2.cell_value(j, 2)
            if valE not in user_email:
                user_email.append(valE)
    msg_html = render_to_string('send_content/assort_tea_paket_mail.html')
    email = EmailMessage(subject='Расширение ассортимента в магазине CTshop!', body=msg_html, from_email='ctshop.project@gmail.com', to=user_email, )
    email.content_subtype = "html"
    email.send()
    return render(request, 'tea_paket_mail.html', context={'user_email': user_email})


# электронная рассылка всем клиентам, которые купили листовой чай
def tea_listov_mail(request):
    email_data = Order.objects.values_list('user_id__id', 'user_id__email')
    clients_emails = pd.DataFrame(email_data)
    writer = pd.ExcelWriter('clients_emails.xls')
    clients_emails.to_excel(writer, 'emails')
    writer.save()
    user_list = []
    category_list = [46, 48, 49, 59, 60]
    rb = xlrd.open_workbook('/home/olegsamsnote/PycharmProjects/CTshop/shop/clients.xls', formatting_info=True)
    sheet = rb.sheet_by_index(0)
    for i in range(1, 865):
        valF = sheet.cell_value(i, 2)
        if valF in category_list:
            valB = sheet.cell_value(i, 1)
            if valB not in user_list:
                valU = int(valB)
                user_list.append(valU)
    user_email = []
    rb2 = xlrd.open_workbook('/home/olegsamsnote/PycharmProjects/CTshop/shop/clients_emails.xls', formatting_info=True)
    sheet2 = rb2.sheet_by_index(0)
    for j in range(1, 392):
        valC = sheet2.cell_value(j, 1)
        if valC in user_list:
            valE = sheet2.cell_value(j, 2)
            if valE not in user_email:
                user_email.append(valE)
    msg_html = render_to_string('send_content/assort_tea_listov_mail.html')
    email = EmailMessage(subject='Расширение ассортимента в магазине CTshop!', body=msg_html, from_email='ctshop.project@gmail.com', to=user_email, )
    email.content_subtype = "html"
    email.send()
    return render(request, 'tea_listov_mail.html', context={'user_email': user_email})


# рассылка для всех пользователей
def message_for_new_year(request):
    email_data = Order.objects.values_list('user_id__id', 'user_id__email')
    clients_emails = pd.DataFrame(email_data)
    writer = pd.ExcelWriter('clients_emails.xls')
    clients_emails.to_excel(writer, 'emails')
    writer.save()

    user_email = []
    rb2 = xlrd.open_workbook('/home/olegsamsnote/PycharmProjects/CTshop/shop/clients_emails.xls', formatting_info=True)
    sheet2 = rb2.sheet_by_index(0)
    for j in range(1, 392):
        valE = sheet2.cell_value(j, 2)
        if valE not in user_email:
            user_email.append(valE)

    msg_html = render_to_string('send_content/message_for_new_year_mail.html')
    email = EmailMessage(subject='CTshop поздравляет Вас с Новым Годом!', body=msg_html, from_email='ctshop.project@gmail.com', to=user_email, )
    email.content_subtype = "html"
    email.send()

    return render(request, 'message_for_new_year.html', context={'user_email': user_email})
