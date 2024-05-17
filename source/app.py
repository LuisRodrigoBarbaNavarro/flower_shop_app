# ----- Imports -----

# Flask Imports
from flask_restful import Api, Resource
from flask_mysqldb import MySQL
from flask_login import *
from flask import *
# Flask Imports

# Spyne Imports
from spyne import Application, rpc, ServiceBase, String, Integer, Unicode
from spyne.server.wsgi import WsgiApplication
from spyne.protocol.soap import Soap11
# Spyne Imports

# Python Imports
from suds.client import Client
from functools import wraps
from config import config
import threading
import socket
# Python Imports

# Models Imports
from models.model_users import ModelUsers
from models.model_orders import ModelOrders
from models.model_products import ModelProducts
from models.model_shopping_cart import ModelShoppingCart
from models.model_transaction_log import ModelTransactionLog
# Models Imports

# Entities Imports
from models.entities.users import Users
from models.entities.orders import Orders
from models.entities.products import Products
from models.entities.shopping_cart import ShoppingCart
from models.entities.transaction_log import TransactionLog
# Entities Imports

# ----- Imports -----





# ----- App Configuration -----

# Flask Configuration
app = Flask(__name__)
db = MySQL(app)

api = Api(app)
# Flask Configuration

# Login Configuration
login_manager_app = LoginManager(app)
# Login Configuration

# ----- App Configuration -----





# ----- Authentication -----

# Root Route
@app.route("/")

def index():

    return redirect("login")
# Root Route

# Login Route
@app.route("/login", methods=["GET", "POST"])

def login():
    if current_user.is_authenticated == False:
        if request.method == "POST":
            user = Users (
                0,
                request.form["usernameInput"],
                request.form["passwordInput"],
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                ""
            )
            
            logged_user = ModelUsers.login(db, user)

            if logged_user is not None:
                if logged_user.user_type == 1 or logged_user.user_type == 2 or logged_user.user_type == 0:  
                    login_user(logged_user)
                    return redirect(url_for("dashboard"))
            else:
                flash("Usuario o contraseña incorrectos.")
                return render_template("auth/login.html")
        else:
            return render_template("auth/login.html")
    else:
        return redirect(url_for("dashboard"))
# Login Route

# Sign Up Route
@app.route("/signup", methods=["GET", "POST"])

def signup():

    if request.method == "POST":
        confirm_password = request.form["confirmPasswordInput"]
        user = Users (
            0,
            request.form["usernameInput"],
            request.form["passwordInput"],
            request.form["firstnameInput"],
            request.form["lastnameInput"],
            request.form["emailInput"],
            request.form["addressInput"],
            request.form["phoneInput"],
            "None",
            "None",
            0
        )

        try:
            if user.password != confirm_password:
                flash("Las contraseñas no coinciden.")
                return render_template("auth/signup.html")
            else:
                ModelUsers.add_user(db, user)
                
                flash("Usuario registrado correctamente.")
                return redirect(url_for("login"))
        except Exception as e:
            flash("Error al registrar usuario. %s" % e)
    else:
        return render_template("auth/signup.html")
# Sign Up Route

# Error 401 Route
@app.route("/error-401")

def error_401():
    
    return render_template("auth/error-401.html")
# Error 401 Route

# Error 403 Route
@app.route("/error-403")

def error_403():
    
    return render_template("auth/error-403.html")
# Error 403 Route

# Login Required Decorator
def login_is_required(func):
    
    @wraps(func)
    
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("error_401"))
        else:
            return func(*args, **kwargs)
    
    return decorated_view
# Login Required Decorator

# Admin Required Decorator
def admin_required(func):

    @wraps(func)
    
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != 1:
            return redirect(url_for("error_403"))
        else:
            return func(*args, **kwargs)
    
    return decorated_view
# Admin Required Decorator

# Employee Required Decorator
def employee_required(func):

    @wraps(func)
    
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != 2:
            return redirect(url_for("error_403"))
        else:
            return func(*args, **kwargs)
    
    return decorated_view
# Employee Required Decorator

# Permission Tagger Decorator
def permission_tagger(func):

    @wraps(func)
    
    def decorated_view(*args, **kwargs):
        if current_user.is_authenticated or current_user.user_type > 0:
            return func(*args, **kwargs)
        else:
            return redirect(url_for("error_403"))
            
    
    return decorated_view
# Permission Tagger Decorator

# Logout Route
@app.route("/logout")
@login_is_required

def logout():

    logout_user()
    return redirect(url_for("login"))
# Logout Route

# User Loader
@login_manager_app.user_loader

def load_user(id):

    return ModelUsers.get_users_by_id(db, id)
# User Loader

# ----- Authentication -----





# ----- Dashboard -----

# Get IP Function
def get_ip():

    try:
        # Create a connection socket with the IP address 8.8.8.8 (Google's DNS server) on port 80
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]  # Get the IP address of the socket
        s.close()
        return ip
    except Exception as e:
        print("Error obtaining IP address:", e)
        return None
# Get IP Function

# Get Count Shopping Cart Function
def get_count_shopping_cart(user_id):
    
    return ModelShoppingCart.get_count_shopping_cart(db, user_id)
# Get Count Shopping Cart Function

# Get Count Notifications Function
def get_count_notifications():
    
    return len(ModelProducts.reorder_product_alert(db))
# Get Count Notifications Function

# Get Notifications Function
def get_notifications():
        
        return ModelProducts.reorder_product_alert(db)
# Get Notifications Function

# Dashboard Route
@app.route("/dashboard")
@login_is_required

def dashboard():
    
    return render_template (
        "public/dashboard.html",
        get_count_shopping_cart=get_count_shopping_cart(current_user.id),
        get_count_notifications=get_count_notifications()
    )
# Dashboard Route

# ----- Dashboard -----





# ----- Notifications -----
@app.route("/notifications")
@login_is_required
@permission_tagger

def notifications():
        return render_template (
            "public/notifications.html",
            get_count_shopping_cart=get_count_shopping_cart(current_user.id),
            get_count_notifications=get_count_notifications(),
            notifications=get_notifications()
        )
# ----- Notifications -----





# ----- Products -----

# Validate Form Function
def validate_form(product) -> bool:
    if len(product.name) == 0:
        flash("Nombre no puede estar vacío.")
    if len(product.description) == 0:
        flash("Descripción no puede estar vacío.")
    if len(product.price) == 0:
        flash("Precio no puede estar vacío.")
    if float(product.price) < 0:
        flash("Precio no puede ser negativo.")
    return True
# Validate Form Function

# Products Route
@app.route("/products")
@login_is_required
@admin_required

def products():

    try:
        products = ModelProducts.get_products(db)
        
        return render_template (
            "public/products-add.html", 
            get_count_shopping_cart=get_count_shopping_cart(current_user.id),
            get_count_notifications=get_count_notifications(),
            products=products
        )
    except Exception as e:
        raise Exception(e)
# Products Route

# Products Read Only Route
@app.route("/products-readonly")
@login_is_required
@employee_required

def productsReadOnly():

    try:
        products = ModelProducts.get_products(db)
        
        return render_template (
            "public/products-employee.html", 
            get_count_shopping_cart=get_count_shopping_cart(current_user.id),
            get_count_notifications=get_count_notifications(),
            products=products
        )
    except Exception as e:
        raise Exception(e)
# Products Read Only Route

# Add Product Route
@app.route("/products/add", methods=["GET", "POST"])
@login_is_required
@admin_required

def add_product():

    if request.method == "POST":
        product = Products (
            0,
            request.form["nameInput"],
            request.form["descriptionInput"],
            request.form["quantityInput"],
            request.form["alertQuantityInput"],
            request.form["priceInput"],
            request.form["imageInput"]
        )

        if validate_form(product):      
            try:
                ModelProducts.add_product(db, product)

                flash("Producto agregado correctamente.")
                return redirect(url_for("products"))
            except Exception as e:
                flash("Error al actualizar producto. %s" % e)
        else:
            return render_template (
                "public/products-add.html",
                get_count_shopping_cart=get_count_shopping_cart(current_user.id),
                get_count_notifications=get_count_notifications()
            )
    return redirect(url_for("products"))
# Add Product Route

# Edit Product Route
@app.route("/products/edit/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required

def edit_product(id):

    if request.method == "POST":
        product = Products (
        id,
        request.form["nameInput"],
        request.form["descriptionInput"],
        request.form["quantityInput"],
        request.form["alertQuantityInput"],
        request.form["priceInput"],
        request.form["imageInput"]
        )
        
        if validate_form(product):
            try:
                ModelProducts.edit_product(db, product)

                flash("Producto actualizado correctamente.")
                return redirect(url_for("products"))
            except Exception as e:
                flash("Error al actualizar producto. %s" % e)
        
        return redirect(url_for("products"))
    else:
        return render_template (
            "public/products-edit.html", 
            get_count_shopping_cart=get_count_shopping_cart(current_user.id),
            get_count_notifications=get_count_notifications(), 
            product=ModelProducts.get_products_by_id(db, id),
            id=id
        )
# Edit Product Route

# Delete Product Route
@app.route("/products/delete/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required

def delete_product(id):

    if request.method == "POST":
        ModelProducts.delete_product(db, id)

        flash("Producto eliminado correctamente.")
        return redirect(url_for("products"))
    else:
        return render_template (
            "public/products-delete.html",
            get_count_shopping_cart=get_count_shopping_cart(current_user.id),
            get_count_notifications=get_count_notifications(),
            id=id
        )
# Delete Product Route

# ----- Products -----
    




# ----- Users -----

# Users Route
@app.route("/users")
@login_is_required
@admin_required

def users():
    
    try:
        users = ModelUsers.get_users(db)

        return render_template (
            "public/users-add.html",
            get_count_shopping_cart=get_count_shopping_cart(current_user.id),
            get_count_notifications=get_count_notifications(),
            users=users
        )
    except Exception as e:
        raise Exception(e)
# Users Route

# Users Read Only Route
@app.route("/users-readonly")
@login_is_required
@employee_required

def usersReadOnly():
    
    try:
        users = ModelUsers.get_users(db)

        return render_template (
            "public/users-employee.html",
            get_count_shopping_cart=get_count_shopping_cart(current_user.id),
            get_count_notifications=get_count_notifications(),
            users=users
        )
    except Exception as e:
        raise Exception(e)
# Users Read Only Route

# Add User Route
@app.route("/users/add", methods=["GET", "POST"])
@login_is_required
@admin_required

def add_user():

    if request.method == "POST":
        user_type = int()
        if (request.form["userTypeInput"] == "Cliente"):
            user_type = 0
        elif (request.form["userTypeInput"] == "Administrador"):
            user_type = 1
        elif (request.form["userTypeInput"] == "Empleado"):
            user_type = 2

        user = Users (
            0,
            request.form["usernameInput"],
            request.form["passwordInput"],
            request.form["firstnameInput"],
            request.form["lastnameInput"],
            request.form["emailInput"],
            request.form["addressInput"],
            request.form["phoneInput"],
            request.form["startTimeInput"],
            request.form["endTimeInput"],
            user_type
        )

        try:
            ModelUsers.add_user(db, user)

            flash("Usuario agregado correctamente.")
            return redirect(url_for("users"))
        except Exception as e:
            flash("Error al agregar usuario. %s" % e)
    else:
        return render_template (
            "public/users-add.html",
            get_count_shopping_cart=get_count_shopping_cart(current_user.id),
            get_count_notifications=get_count_notifications()
        )
# Add User Route

# Edit User Route
@app.route("/users/edit/<int:id>", methods=["GET", "POST"])
@login_is_required
@admin_required

def edit_user(id):
    
    if request.method == "POST":
        user_type = int()
        if (request.form["userTypeInput"] == "Cliente"):
            user_type = 0
        elif (request.form["userTypeInput"] == "Administrador"):
            user_type = 1
        elif (request.form["userTypeInput"] == "Empleado"):
            user_type = 2

        user = Users (
            id,
            request.form["usernameInput"],
            request.form["passwordInput"],
            request.form["firstnameInput"],
            request.form["lastnameInput"],
            request.form["emailInput"],
            request.form["addressInput"],
            request.form["phoneInput"],
            request.form["startTimeInput"],
            request.form["endTimeInput"],
            user_type
        )

        try:
            ModelUsers.edit_user(db, user)

            flash("Usuario actualizado correctamente.")
            return redirect(url_for("users"))
        except Exception as e:
            flash("Error al actualizar usuario. %s" % e)
    else:
        return render_template (
            "public/users-edit.html",
            get_count_shopping_cart=get_count_shopping_cart(current_user.id),
            get_count_notifications=get_count_notifications(),
            user=ModelUsers.get_users_by_id(db, id),
            id=id
        )
# Edit User Route

# Delete User Route
@app.route("/users/delete/<int:id>", methods=["GET", "POST"])
@login_is_required
@admin_required

def delete_user(id):

    if request.method == "POST":
        ModelUsers.delete_user(db, id)

        flash("Usuario eliminado correctamente.")
        return redirect(url_for("users"))
    else:
        return render_template (
            "public/users-delete.html",
            get_count_shopping_cart=get_count_shopping_cart(current_user.id),
            get_count_notifications=get_count_notifications(),
            id=id
        )
# Delete User Route

# ----- Users -----





# ----- Sales -----

# Sales Route
@app.route("/sales")
@login_required
@admin_required

def sales():

    try:
        get_best_sale = ModelOrders.get_best_sales(db)
        get_worst_sale = ModelOrders.get_worst_sales(db)
        get_total_sales = ModelOrders.get_total_sales(db)

        return render_template (
            "public/sales.html",
            get_count_shopping_cart=get_count_shopping_cart(current_user.id),
            get_count_notifications=get_count_notifications(),
            orders=ModelOrders.get_orders(db),
            total_sales=get_total_sales,
            worst_sale=get_worst_sale,
            best_sale=get_best_sale
        )
    except Exception as e:
        raise Exception(e)
# Sales Route

# Sales Read Only Route
@app.route("/sales-readonly")
@login_required
@employee_required

def salesReadOnly():
    
        try:
            get_best_sale = ModelOrders.get_best_sales(db)
            get_worst_sale = ModelOrders.get_worst_sales(db)
            get_total_sales = ModelOrders.get_total_sales(db)
    
            return render_template (
                "public/sales-employee.html",
                get_count_shopping_cart=get_count_shopping_cart(current_user.id),
                get_count_notifications=get_count_notifications(),
                orders=ModelOrders.get_orders(db),
                total_sales=get_total_sales,
                worst_sale=get_worst_sale,
                best_sale=get_best_sale
            )
        except Exception as e:
            raise Exception(e)
# Sales Read Only Route
        
# Sales Read Only Receipt Route
@app.route("/sales-readonly/receipt/<int:id>")
@login_required
@employee_required

def sales_read_only_receipt(id):
    
        essential_data = ModelOrders.get_essential_order_data(db, id)
        get_orders_by_id = ModelOrders.get_orders_by_id(db, id)
        get_users_by_id = ModelUsers.get_users_by_id(db, get_orders_by_id[2])
        total_price = ModelOrders.get_total_price_by_order(db, id)
    
        return render_template (
            "public/sales-read-only-receipt.html",
            get_count_notifications=get_count_notifications(),
            order_information=get_orders_by_id,
            user_information=get_users_by_id,
            shopping_cart=essential_data,
            total_price=total_price
        )
# Sales Read Only Receipt Route

# Sale Receipt Route
@app.route("/sales/receipt/<int:id>")
@login_required
@admin_required

def sales_receipt(id):

    essential_data = ModelOrders.get_essential_order_data(db, id)
    get_orders_by_id = ModelOrders.get_orders_by_id(db, id)
    get_users_by_id = ModelUsers.get_users_by_id(db, get_orders_by_id[2])
    total_price = ModelOrders.get_total_price_by_order(db, id)

    return render_template (
        "public/sales-receipt.html",
        get_count_notifications=get_count_notifications(),
        order_information=get_orders_by_id,
        user_information=get_users_by_id,
        shopping_cart=essential_data,
        total_price=total_price
    )
# Sale Receipt Route

# Delete Order Route
@app.route("/sales/delete/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required

def delete_order(id):
    
        if request.method == "POST":
            ModelOrders.delete_order(db, id)
    
            flash("Orden eliminada correctamente.")
            return redirect(url_for("sales"))
        else:
            return render_template (
                "public/sales-delete.html",
                get_count_shopping_cart=get_count_shopping_cart(current_user.id),
                get_count_notifications=get_count_notifications(),
                id=id
            )
# Delete Order Route
        
# Refund Order Route
@app.route("/sales/refund/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required

def refund_order(id):
    
        if request.method == "POST":
            ModelOrders.refund_order(db, id)
    
            flash("Orden reembolsada correctamente.")
            return redirect(url_for("sales"))
        else:
            return render_template (
                "public/sales-refund.html",
                get_count_shopping_cart=get_count_shopping_cart(current_user.id),
                get_count_notifications=get_count_notifications(),
                id=id
            )
# Refund Order Route

# ----- Sales -----
    




# ----- Shop -----

# Is Empty Shopping Cart Function
def is_empty_shopping_cart(user_id):
    
    if ModelShoppingCart.get_count_shopping_cart(db, user_id) == 0:
        return True
    else:
        return False
# Is Empty Shopping Cart Function

# Shop Route
@app.route("/point-sale")
@login_required

def point_sale():
    
    try:
        products = ModelProducts.get_products(db)
        shopping_cart_products = ModelShoppingCart.get_essential_data(db, current_user.id)

        return render_template (
            "public/shop-point-sale.html",
            get_total_price=ModelShoppingCart.get_total_price(db, current_user.id),
            get_count_shopping_cart=get_count_shopping_cart(current_user.id),
            is_empty_shopping_cart=is_empty_shopping_cart(current_user.id),
            get_count_notifications=get_count_notifications(),
            shopping_cart_products=shopping_cart_products,
            products=products
        )
    except Exception as e:
        raise Exception(e)
# Shop Route
    
# Shop Client Route
@app.route("/shop-client")
@login_required

def shop_client():
        
        try:
            products = ModelProducts.get_products(db)
            shopping_cart_products = ModelShoppingCart.get_essential_data(db, current_user.id)
    
            return render_template (
                "public/shop-client.html",
                get_total_price=ModelShoppingCart.get_total_price(db, current_user.id),
                get_count_shopping_cart=get_count_shopping_cart(current_user.id),
                is_empty_shopping_cart=is_empty_shopping_cart(current_user.id),
                get_count_notifications=get_count_notifications(),
                shopping_cart_products=shopping_cart_products,
                products=products
            )
        except Exception as e:
            raise Exception(e)
# Shop Client Route
        
# Shop Add Client Route
@app.route("/shop-client/add/<int:id>", methods=["GET", "POST"])
@login_required

def add_client(id):

    if request.method == "POST":
        shopping_cart = ShoppingCart (
            0,
            current_user.id,
            id,
            request.form["quantity"]
        )

        ModelShoppingCart.add_shopping_cart(db, shopping_cart)

        flash("Producto agregado al carrito de compras correctamente.")
        return redirect(url_for("shop_client"))
    else:
        return redirect(url_for("shop_client"))
# Shop Add Client Route
    
# Shop Remove Client Route
@app.route("/shop-client/remove/<int:id>", methods=["GET", "POST"])
@login_required

def remove_client(id):
    
        if request.method == "POST":
            ModelShoppingCart.remove_from_shopping_cart(db, current_user.id, id)
            
            flash("Producto eliminado del carrito de compras correctamente.")
            return redirect(url_for("shop_client"))
        else:
            return redirect(url_for("shop_client"))
# Shop Remove Client Route

# Shop Clear Client Route
@app.route("/shop-client/clear")
@login_required

def clear_client():
        
            ModelShoppingCart.clear_shopping_cart(db, current_user.id)
            
            flash("Carrito de compras vaciado correctamente.")
            return redirect(url_for("shop_client"))
# Shop Clear Client Route

# Add to Shopping Cart Route
@app.route("/point-sale/add/<int:id>", methods=["GET", "POST"])
@login_required
@employee_required

def add_shopping_cart(id):
    
    if request.method == "POST":
        shopping_cart = ShoppingCart (
            0,
            current_user.id,
            id,
            request.form["quantity"]
        )

        ModelShoppingCart.add_shopping_cart(db, shopping_cart)

        flash("Producto agregado al carrito de compras correctamente.")
        return redirect(url_for("point_sale"))
    else:
        return redirect(url_for("point_sale"))
# Add to Shopping Cart Route

# Remove from Shopping Cart Route
@app.route("/point-sale/remove/<int:id>", methods=["GET", "POST"])
@login_required
@employee_required

def remove_from_shopping_cart(id):

    if request.method == "POST":
        ModelShoppingCart.remove_from_shopping_cart(db, current_user.id, id)
        
        flash("Producto eliminado del carrito de compras correctamente.")
        return redirect(url_for("point_sale"))
    else:
        return redirect(url_for("point_sale"))
# Remove from Shopping Cart Route

# Clear Shopping Cart Route
@app.route("/point-sale/clear")
@login_required
@employee_required

def clear_shopping_cart():
    
    ModelShoppingCart.clear_shopping_cart(db, current_user.id)
    
    flash("Carrito de compras vaciado correctamente.")
    return redirect(url_for("point_sale"))
# Clear Shopping Cart Route

# ----- Shop -----





# ----- Receipt -----

# is Empty Receipt Function
def is_empty_receipt():
    
    if ModelOrders.get_count_orders_by_user(db, current_user.id) == 0:
        return True
    else:
        return False
# is Empty Receipt Function

# Receipt Route
@app.route("/point-sale/receipt", methods=["GET", "POST"])
@login_required

def receipt():

    if request.method == "POST":
        if is_empty_shopping_cart(current_user.id):
            flash("No se puede generar una orden vacía.")
            return redirect(url_for("point_sale"))
        else:
            try:
                essential_data = ModelShoppingCart.get_essential_data(db, current_user.id)
                shopping_cart = ModelShoppingCart.get_shopping_cart(db, current_user.id)

                get_total_price = ModelShoppingCart.get_total_price(db, current_user.id)
                get_users_by_id = ModelUsers.get_users_by_id(db, current_user.id)       
                get_last_order_id = ModelOrders.get_last_order_id(db)
                
                for product in shopping_cart:
                    order = Orders (
                        get_last_order_id,
                        'completed', # 'completed' or 'pending payment'
                        current_user.id,
                        product[2],
                        product[3]
                    )
                    
                    ModelProducts.buy_product(db, product[2], product[3])

                ModelOrders.add_order(db, order)
                
                get_orders_by_id = ModelOrders.get_orders_by_id(db, get_last_order_id)
                ModelShoppingCart.clear_shopping_cart(db, current_user.id)
                
                return render_template (
                    "public/receipt.html",
                    get_count_notifications=get_count_notifications(),
                    order_information=get_orders_by_id,
                    user_information=get_users_by_id,
                    shopping_cart=essential_data,
                    total_price=get_total_price   
                )
            except Exception as e:
                raise Exception(e)
    else:
        return redirect(url_for("point_sale"))
# Receipt Route
    
# Receipt Client Route
@app.route("/shop-client/receipt", methods=["GET", "POST"])
@login_required

def shop_client_receipt():

    if request.method == "POST":
        if is_empty_shopping_cart(current_user.id):
            flash("No se puede generar una orden vacía.")
            return redirect(url_for("point_sale"))
        else:
            try:
                essential_data = ModelShoppingCart.get_essential_data(db, current_user.id)
                shopping_cart = ModelShoppingCart.get_shopping_cart(db, current_user.id)

                get_total_price = ModelShoppingCart.get_total_price(db, current_user.id)
                get_users_by_id = ModelUsers.get_users_by_id(db, current_user.id)       
                get_last_order_id = ModelOrders.get_last_order_id(db)
                
                for product in shopping_cart:
                    order = Orders (
                        get_last_order_id,
                        'completed', # 'completed' or 'pending payment'
                        current_user.id,
                        product[2],
                        product[3]
                    )
                    
                    ModelProducts.buy_product(db, product[2], product[3])

                ModelOrders.add_order(db, order)
                
                get_orders_by_id = ModelOrders.get_orders_by_id(db, get_last_order_id)
                ModelShoppingCart.clear_shopping_cart(db, current_user.id)
                
                return render_template (
                    "public/receipt.html",
                    get_count_notifications=get_count_notifications(),
                    order_information=get_orders_by_id,
                    user_information=get_users_by_id,
                    shopping_cart=essential_data,
                    total_price=get_total_price   
                )
            except Exception as e:
                raise Exception(e)
    else:
        return redirect(url_for("shop_client"))
# Receipt Client Route

# Receipts Route
@app.route("/receipts")
@login_required

def receipts():

    try:
        return render_template (
            "public/receipts.html",
            orders_by_user=ModelOrders.get_orders_by_user(db, current_user.id),
            get_count_shopping_cart=get_count_shopping_cart(current_user.id),
            get_count_notifications=get_count_notifications(),
            is_empty_receipt=is_empty_receipt()
        )
    except Exception as e:
        raise Exception(e)
# Receipts Route

# Receipts Order By Route
@app.route("/receipts/order-by/<int:id>")
@login_required

def receipts_order_by(id):

    essential_data = ModelOrders.get_essential_order_data(db, id)
    get_orders_by_id = ModelOrders.get_orders_by_id(db, id)
    get_users_by_id = ModelUsers.get_users_by_id(db, get_orders_by_id[2])
    total_price = ModelOrders.get_total_price_by_order(db, id)

    return render_template (
        "public/receipts-order-by.html",
        get_count_notifications=get_count_notifications(),
        order_information=get_orders_by_id,
        user_information=get_users_by_id,
        shopping_cart=essential_data,
        total_price=total_price
    )
# Receipts Order By Route
    
# ----- Receipt -----





# ----- About -----

# About Route
@app.route("/about")
@login_required

def about():

    return render_template (
        "public/about.html",
        get_count_shopping_cart=get_count_shopping_cart(current_user.id),
        get_count_notifications=get_count_notifications()
    )
# About Route

# ----- About -----





# ----- Web Services Log -----
def add_transaction_log(protocol, web_service, operation, section):
    try:
        ip = get_ip()
        ModelTransactionLog.add_transaction_log(db, protocol, web_service, operation, section, 0, ip)
    except Exception as e:
        raise Exception(e)


@app.route("/webservices-log")
@login_required
@admin_required

def webservices_log():
    return render_template("public/webservices-log.html",
        get_count_shopping_cart=get_count_shopping_cart(current_user.id),
        get_count_notifications=get_count_notifications(),
        logs=ModelTransactionLog.get_transaction_logs(db)
    )
# ----- Web Services Log -----





# ----- SOAP -----

# ----- Web Services -----

# Web Service Get Products
@app.route("/webservice/get-products", methods=["GET"])
def get_products():
    try:
        with app.app_context():
            client = Client('http://localhost:5002/soap?wsdl')
            result = client.service.get_products()
            add_transaction_log("SOAP", "/webservice/get-products", "GET", "Products")
            return result
    except Exception as e:
        return str(e)
    
@app.route("/webservice/get-product/<int:id>", methods=["GET"])
def get_products_by_id(id):
    try:
        with app.app_context():
            client = Client('http://localhost:5002/soap?wsdl')
            result = client.service.get_products_by_id(id)
            add_transaction_log("SOAP", "/webservice/get-product/<int:id>", "GET", "Products")
            return result
    except Exception as e:
        return str(e)
class WebServiceGetProducts(ServiceBase):
    @rpc(_returns=Unicode)
    def get_products(self):
        try:
            with app.app_context():
                products = ModelProducts.get_products(db)
                product_list = []
                for product in products:
                    product_info = [
                        product.id,
                        product.name,
                        product.description,
                        product.quantity,
                        product.alert_quantity,
                        float(product.price),
                        product.url_image
                    ]
                    product_list.append(product_info)
                return str(product_list)
        except Exception as ex:
            return str(ex)
        
    @rpc(Integer, _returns=Unicode)
    def get_products_by_id(self, id):
        try:
            with app.app_context():
                product = ModelProducts.get_products_by_id(db, id)
                product_info = [
                    product.id,
                    product.name,
                    product.description,
                    product.quantity,
                    product.alert_quantity,
                    float(product.price),
                    product.url_image
                ]
                return str(product_info)
        except Exception as ex:
            return str(ex)
# Web Service Get Products
        
# Web Service Get Users
@app.route("/webservice/get-users", methods=["GET"])
def get_users():
    try:
        with app.app_context():
            client = Client('http://localhost:5002/soap?wsdl')
            result = client.service.get_users()
            add_transaction_log("SOAP", "/webservice/get-users", "GET", "Users")
            return result
    except Exception as e:
        return str(e)
class WebServiceGetUsers(ServiceBase):
    @rpc(_returns=Unicode)
    def get_users(self):
        try:
            with app.app_context():
                list = []
                users = ModelUsers.get_users(db)
                user_list = [Users(user[0], user[1], user[2], user[3], user[4], user[5], user[6], user[7], user[8], user[9], user[10]) for user in users]
                for user in user_list:
                    user_info = [
                        user.id,
                        user.username,
                        user.password,
                        user.firstname,
                        user.lastname,
                        user.email,
                        user.physical_address,
                        user.phone,
                        user.start_time,
                        user.end_time,
                        user.user_type
                    ]
                    list.append(user_info)
                return str(list)
        except Exception as ex:
            return str(ex)
# Web Service Get Users

# Werb Service Get User
@app.route("/webservice/get-user/<int:id>", methods=["GET"])
def get_user_by_id(id):
    try:
        with app.app_context():
            client = Client('http://localhost:5002/soap?wsdl')
            result = client.service.get_user_by_id(id)
            add_transaction_log("SOAP", "/webservice/get-user/<int:id>", "GET", "Users")
            return result
    except Exception as e:
        return str(e)
class WebServiceGetUser(ServiceBase):
    @rpc(Integer, _returns=Unicode)
    def get_user_by_id(self, id):
        try:
            with app.app_context():
                user = ModelUsers.get_users_by_id(db, id)
                user_info = [
                    user.id,
                    user.username,
                    user.password,
                    user.firstname,
                    user.lastname,
                    user.email,
                    user.physical_address,
                    user.phone,
                    user.start_time,
                    user.end_time,
                    user.user_type
                ]
                return str(user_info)
        except Exception as ex:
            return str(ex)
# Werb Service Get User

# Web Service Add Users
@app.route("/webservice/add-user", methods=["POST"])
def add_user_soap():
    try:
        with app.app_context():
            user_type = int()
            if (request.json['user_type'] == "Cliente"):
                user_type = 0
            elif (request.json['user_type'] == "Administrador"):
                user_type = 1
            elif (request.json['user_type'] == "Empleado"):
                user_type = 2

            client = Client('http://localhost:5002/soap?wsdl')
            result = client.service.add_user(
                request.json['username'],
                request.json['password'],
                request.json['firstname'],
                request.json['lastname'],
                request.json['email'],
                request.json['address'],
                request.json['phone'],
                request.json['start_time'],
                request.json['end_time'],
                user_type
            )
            return result
    except Exception as e:
        return str(e)
class WebServiceAddUser(ServiceBase):
    @rpc(String, String, String, String, String, String, String, String, String, Integer, _returns=Unicode)
    def add_user(self, username, password, firstname, lastname, email, physical_address, phone, start_time, end_time, user_type):
        try:
            with app.app_context():
                user = Users (
                    0,
                    username,
                    password,
                    firstname,
                    lastname,
                    email,
                    physical_address,
                    phone,
                    start_time,
                    end_time,
                    user_type
                )
                ModelUsers.add_user(db, user)
                return "Usuario agregado correctamente."
        except Exception as ex:
            return str(ex)
# Web Service Add Users
        
# Web Service Edit Users
@app.route("/webservice/edit-user/<int:id>", methods=["POST"])
def edit_user_soap(id):
    try:
        with app.app_context():
            user_type = int()
            if (request.json['user_type'] == "Cliente"):
                user_type = 0
            elif (request.json['user_type'] == "Administrador"):
                user_type = 1
            elif (request.json['user_type'] == "Empleado"):
                user_type = 2

            client = Client('http://localhost:5002/soap?wsdl')
            result = client.service.edit_user(
                id,
                request.json['username'],
                request.json['password'],
                request.json['firstname'],
                request.json['lastname'],
                request.json['email'],
                request.json['address'],
                request.json['phone'],
                request.json['start_time'],
                request.json['end_time'],
                user_type
            )
            add_transaction_log("SOAP", "/webservice/edit-user/<int:id>", "POST", "Users")
            return result
    except Exception as e:
        return str(e)

class WebServiceEditUser(ServiceBase):
    @rpc(Integer, String, String, String, String, String, String, String, String, String, Integer, _returns=Unicode)
    def edit_user(self, id, username, password, firstname, lastname, email, physical_address, phone, start_time, end_time, user_type):
        try:
            with app.app_context():
                user = Users (
                    id,
                    username,
                    password,
                    firstname,
                    lastname,
                    email,
                    physical_address,
                    phone,
                    start_time,
                    end_time,
                    user_type
                )
                ModelUsers.edit_user(db, user)
                return "Usuario actualizado correctamente."
        except Exception as ex:
            return str(ex)
# Web Service Edit Users
        
# Web Service Delete Users
@app.route("/webservice/delete-user/<int:id>", methods=["POST"])
def delete_user_soap(id):
    try:
        with app.app_context():
            client = Client('http://localhost:5002/soap?wsdl')
            result = client.service.delete_user(id)
            add_transaction_log("SOAP", "/webservice/delete-user/<int:id>", "POST", "Users")
            return result
    except Exception as e:
        return str(e)

class WebServiceDeleteUser(ServiceBase):
    @rpc(Integer, _returns=Unicode)
    def delete_user(self, id):
        try:
            with app.app_context():
                ModelUsers.delete_user(db, id)
                return "Usuario eliminado correctamente."
        except Exception as ex:
            return str(ex)
# Web Service Delete Users

# Web Service Get Orders
@app.route("/webservice/get-orders", methods=["GET"])
def get_orders():
    try:
        with app.app_context():
            client = Client('http://localhost:5002/soap?wsdl')
            result = client.service.get_orders()
            add_transaction_log("SOAP", "/webservice/get-orders", "GET", "Orders")
            return result
    except Exception as e:
        return str(e)
class WebServiceGetOrders(ServiceBase):
    @rpc(_returns=Unicode)
    def get_orders(self):
        try:
            with app.app_context():
                orders = ModelOrders.get_orders(db)
                order_list = [[order[0], order[1], order[2], order[3], order[4], order[5], float(order[6]), float(order[7]), str(order[8])] for order in orders]
                return str(order_list)
        except Exception as ex:
            return str(ex)
# Web Service Get Orders
        
# Web Service Get Order Receipt
@app.route("/webservice/get-order-receipt/<int:id>", methods=["GET"])
def get_order_receipt(id):
    try:
        with app.app_context():
            client = Client('http://localhost:5002/soap?wsdl')
            result = client.service.get_order_receipt(id)
            add_transaction_log("SOAP", "/webservice/get-order-receipt/<int:id>", "GET", "Orders")
            return result
    except Exception as e:
        return str(e)
class WebServiceGetOrderReceipt(ServiceBase):
    @rpc(Integer, _returns=Unicode)
    def get_order_receipt(self, id):
        try:
            with app.app_context():
                essential_data_frame = ModelOrders.get_essential_order_data(db, id)
                get_orders_by_id = ModelOrders.get_orders_by_id(db, id)
                get_users_by_id = ModelUsers.get_users_by_id(db, get_orders_by_id[2])
                total_price = ModelOrders.get_total_price_by_order(db, id)
                
                essential_data = []
                for product in essential_data_frame:
                    product_info = [
                        product[0],
                        product[1],
                        product[2],
                        float(product[3]),
                        float(product[4])
                    ]
                essential_data.append(product_info)
                
                order_by_id = [
                    get_orders_by_id[0],
                    get_orders_by_id[1],
                    get_orders_by_id[2],
                    get_orders_by_id[3],
                    get_orders_by_id[4],
                    str(get_orders_by_id[5])
                ]

                user_by_id = [
                    get_users_by_id.id,
                    get_users_by_id.username,
                    get_users_by_id.password,
                    get_users_by_id.firstname,
                    get_users_by_id.lastname,
                    get_users_by_id.email,
                    get_users_by_id.physical_address,
                    get_users_by_id.phone,
                    get_users_by_id.start_time,
                    get_users_by_id.end_time,
                    get_users_by_id.user_type
                ]

                price = [float(total_price)]

                return str([essential_data, order_by_id, user_by_id, price])
        except Exception as ex:
            return str(ex)
# Web Service Get Order Receipt

# ----- Web Services -----   

# ----- SOAP -----





# ----- REST -----

# Products Resource
class Product(Resource):
    def get(self):
        try:
            product_list = ModelProducts.get_products(db)
            products = []
            for product in product_list:
                product_info = {
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'quantity': product.quantity,
                    'alert_quantity': product.alert_quantity,
                    'price': float(product.price),
                    'url_image': product.url_image
                }
                products.append(product_info)
            
            add_transaction_log("REST", "/api/products", "GET", "Products")
            return jsonify(products)
        except Exception as ex:
            return str(ex)

    def post(self):
        try:
            product = Products (
                0,
                request.json['name'],
                request.json['description'],
                request.json['quantity'],
                request.json['alert_quantity'],
                request.json['price'],
                request.json['url_image']
            )
            ModelProducts.add_product(db, product)
            add_transaction_log("REST", "/api/products", "POST", "Products")
            return "Producto agregado correctamente."
        except Exception as ex:
            return str(ex)
        
    def put(self):
        try:
            product = Products (
                request.json['id'],
                request.json['name'],
                request.json['description'],
                request.json['quantity'],
                request.json['alert_quantity'],
                request.json['price'],
                request.json['url_image']
            )
            ModelProducts.edit_product(db, product)
            add_transaction_log("REST", "/api/products", "PUT", "Products")
            return "Producto actualizado correctamente."
        except Exception as ex:
            return str(ex)
    
    def delete(self, id):
        try:
            ModelProducts.delete_product(db, id)
            add_transaction_log("REST", "/api/products", "DELETE", "Products")
            return "Producto eliminado correctamente."
        except Exception as ex:
            return str(ex)
        
class ProductParams(Resource):
    def get(self, id):
        try:
            product = ModelProducts.get_products_by_id(db, id)
            product_info = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'quantity': product.quantity,
                'alert_quantity': product.alert_quantity,
                'price': float(product.price),
                'url_image': product.url_image
            }
            add_transaction_log("REST", "/api/products-params/<int:id>", "GET", "Products")
            return jsonify(product_info)
        except Exception as ex:
            return str(ex)
# Products Resource

# Add Resource to API
api.add_resource(Product, '/api/products', '/api/products/<int:id>')
api.add_resource(ProductParams, '/api/products-params/<int:id>')
# ----- REST -----





# ----- Main -----

# Run SOAP Server Function
def run_soap_server():
    from wsgiref.simple_server import make_server
    soap_app = Application([WebServiceGetProducts, WebServiceGetUsers, WebServiceGetUser, WebServiceAddUser, WebServiceEditUser, WebServiceDeleteUser, WebServiceGetOrders, WebServiceGetOrderReceipt], 'example', in_protocol=Soap11(validator='lxml'), out_protocol=Soap11())
    soap_wsgi_app = WsgiApplication(soap_app)

    soap_server = make_server('localhost', 5002, soap_wsgi_app)
    print("Iniciando servidor SOAP en http://localhost:5002/soap")
    soap_server.serve_forever()
# Run SOAP Server Function

# Run Flask Server Function
def run_flask_server():
    print("Iniciando servidor Flask en http://localhost:5001")
    app.config.from_object(config['development'])

    app.run(port=5001, debug=True)
# Run Flask Server Function

# Create a thread to run the SOAP server and run the Flask server in the main thread
if __name__ == '__main__':
    soap_thread = threading.Thread(target=run_soap_server)
    soap_thread.start()
    run_flask_server()
# Create a thread to run the SOAP server and run the Flask server in the main thread

# ----- Main -----