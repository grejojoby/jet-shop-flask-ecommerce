from flask import render_template, url_for, flash, redirect, request
from store import app, db, bcrypt
from store.forms import RegistrationForm, LoginForm, UpdateAccountForm, ProductForm
from store.models import User, Products, Cart
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import func, update

def getLoginDetails():
    if current_user.is_authenticated:
        noOfItems = Cart.query.filter_by(buyer=current_user).count()
    else:
        noOfItems = 0
    return noOfItems

@app.route("/")
@app.route("/home")
def home():
    noOfItems = getLoginDetails()
    products = Products.query.all()
    return render_template('home.html', products=products,noOfItems=noOfItems)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(lastname=form.lastname.data,firstname=form.firstname.data,email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.lastname = form.lastname.data
        current_user.firstname = form.firstname.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.lastname.data = current_user.lastname
        form.firstname.data = current_user.firstname
        form.email.data = current_user.email
    return render_template('account.html', title='Account',
                           form=form)

@app.route("/select_products", methods=['GET', 'POST'])
def select_products():
    noOfItems = getLoginDetails()
    products = Products.query.all()
    return render_template('select_products.html', products=products,noOfItems=noOfItems)

@app.route("/addToCart/<int:product_id>")
@login_required
def addToCart(product_id):
    row = Cart.query.filter_by(product_id=product_id, buyer=current_user).first()
    if row:
        row.quantity += 1
        db.session.commit()
        flash('This item is already in your cart, 1 quantity added!', 'success')
    else:
        user = User.query.get(current_user.id)
        user.add_to_cart(product_id)
    return redirect(url_for('select_products'))

@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    noOfItems = getLoginDetails()
    cart = Products.query.join(Cart).add_columns(Cart.quantity, Products.price, Products.name, Products.id).filter_by(buyer=current_user).all()
    subtotal = 0
    for item in cart:
        subtotal+=int(item.price)*int(item.quantity)

    if request.method == "POST":
        qty = request.form.get("qty")
        idpd = request.form.get("idpd")
        cartitem = Cart.query.filter_by(product_id=idpd).first()
        cartitem.quantity = qty
        db.session.commit()
        cart = Products.query.join(Cart).add_columns(Cart.quantity, Products.price, Products.name, Products.id).filter_by(buyer=current_user).all()
        subtotal = 0
        for item in cart:
            subtotal+=int(item.price)*int(item.quantity)
    return render_template('cart.html', cart=cart, noOfItems=noOfItems, subtotal=subtotal)

@app.route("/removeFromCart/<int:product_id>")
@login_required
def removeFromCart(product_id):
    item_to_remove = Cart.query.filter_by(product_id=product_id, buyer=current_user).first()
    db.session.delete(item_to_remove)
    db.session.commit()
    flash('Your item has been removed from your cart!', 'success')
    return redirect(url_for('cart'))

@app.route("/checkout")
@login_required
def checkout():
    item_to_remove = Cart.query.filter_by(buyer=current_user).all()
    print(item_to_remove)
    for item in item_to_remove:
        db.session.delete(item)
        db.session.commit()
    flash('Your purchase is successful!', 'success')
    return redirect(url_for('home'))

@app.route("/add_product", methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.is_authenticated and current_user.email == "admin@jetstore.com":
        
        form = ProductForm()
        if form.validate_on_submit():
            product = Products(name=form.name.data,price=form.price.data,description=form.description.data)
            db.session.add(product)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('select_products'))
        
        return render_template('add_product.html', title='Add Product', form=form)

    flash('You do not have access to the page!', 'danger')
    return redirect(url_for('home'))

@app.route("/delete_product", methods=['GET', 'POST'])
@login_required
def delete_product():
    if current_user.is_authenticated and current_user.email == "admin@jetstore.com":
        noOfItems = getLoginDetails()
        products = Products.query.all()
        return render_template('delete_product.html', products=products,noOfItems=noOfItems)
        
    flash('You do not have access to the page!', 'danger')
    return redirect(url_for('home'))

@app.route("/product/delete/<int:product_id>")
@login_required
def remove_product(product_id):
    if current_user.is_authenticated and current_user.email == "admin@jetstore.com":
        item_to_remove = Products.query.filter_by(id=product_id).first()
        db.session.delete(item_to_remove)
        db.session.commit()
        flash('The product have been removed from the database!', 'success')
        return redirect(url_for('delete_product'))