from flask import Flask, render_template, redirect, request, url_for, flash, session
import wtforms as wt
from wtforms import validators
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt


class RegisterForm(wt.Form):
    name = wt.StringField("Name",validators=[wt.validators.DataRequired()])
    username = wt.StringField("Username",validators=[wt.validators.DataRequired(), wt.validators.Length(min=6, max=35)])
    email = wt.StringField('Email Address', validators=[wt.validators.DataRequired(), wt.validators.Length(min=6, max=35)])
    password =wt.PasswordField('New Password',validators=[wt.validators.DataRequired(),wt.validators.EqualTo('confirm', message='Passwords must match'),wt.validators.Length(min=6, max=35)])
    confirm = wt.PasswordField('Repeat Password',validators=[wt.validators.DataRequired(),wt.validators.Length(min=6)])
    company = wt.StringField("Company Name",validators=[wt.validators.DataRequired()])


class LoginForm(wt.Form):
    username = wt.StringField("username", validators=[wt.validators.DataRequired()])
    password = wt.PasswordField("Password",validators=[wt.validators.DataRequired()])


class ProductForm(wt.Form):
    product = wt.StringField("Product", validators=[wt.validators.DataRequired(), wt.validators.Length(min=6, max=25)])
    features = wt.TextAreaField("Features",validators=[wt.validators.DataRequired(), wt.validators.Length(min=25)])
 


app = Flask(__name__)
mysql = MySQL(app)
app.secret_key = "project"


app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"]= ""
app.config["MYSQL_DB"] = "project"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

@app.route("/addproduct", methods=["GET", "POST"])
def addproduct():
    form = ProductForm(request.form)

    if request.method == "POST" and form.validate():
        product = form.product.data
        features = form.features.data

        cursor = mysql.connection.cursor()

        entry = "INSERT INTO products(product,sharing,features) VALUES (%s,%s,%s)"

        cursor.execute(entry,(product,session["username"],features))

        mysql.connection.commit()

        cursor.close()

        flash("The product has been successfully installed", "info")
        return redirect(url_for("dashboard"))

    else:
        return render_template("addproduct.html", form=form)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/index")
def index1():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/products")
def products():
    cursor = mysql.connection.cursor()
    
    query = " SELECT * FROM products"

    cursor.execute(query)

    products = cursor.fetchall()

    return render_template("products.html" , products = products)
    
@app.route("/products/<string:id>")
def products_detail(id):

    cursor = mysql.connection.cursor()

    query = " SELECT * FROM products WHERE id = %s"

    result = cursor.execute(query,(id,))

    if result > 0:
        products = cursor.fetchall()

        return render_template("product_detail.html",products=products)

    else:
        flash("The article you were looking for was not found", "danger")
        return render_template("product_detail.html")

    





@app.route("/register", methods=['GET', 'POST'])
def register():



    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data) 
        company = form.company.data

        cursor = mysql.connection.cursor()
        entry = "INSERT INTO users(name,username,email,password,company) VALUES(%s,%s,%s,%s,%s)"
        cursor.execute(entry,(name,username,email,password,company))
        mysql.connection.commit()

        cursor.close()

        flash("Register is Okay" , "success")


        return redirect(url_for("index"))
    else:
        return render_template("register.html", form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():

    form = LoginForm(request.form)

    if request.method == "POST" and form.validate():
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        query = "SELECT * FROM users WHERE username  = %s"

        result = cursor.execute(query,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password= data["password"]
            
            if sha256_crypt.verify(password_entered,real_password):
                session["logged_in"] = True
                session["username"] = username
                flash("Login successful", "info")
                return redirect(url_for("index"))
            else:
                flash("password incorrect","danger")
                return redirect(url_for("login"))

        else: 
            flash("Username incorrect", "danger")
            return redirect (url_for("login"))
    else:
            return render_template("login.html", form=form)

    

@app.route("/logout")
def logout():
    
    session.clear()
    flash("logged out","info")
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():


    if session:
        cursor = mysql.connection.cursor()

        query = "SELECT * FROM products WHERE sharing= %s"

        cursor.execute(query,(session["username"],))

        products = cursor.fetchall()

        return render_template("dashboard.html", products = products)
    else:
        flash("Only users can access the Dashboard.","danger")

        return redirect(url_for("login"))
    
@app.route("/delete/<string:id>")
def delete(id):
    if session:
        cursor = mysql.connection.cursor()

        query = "SELECT * FROM products WHERE sharing= %s and id = %s"

        result = cursor.execute(query,(session["username"],id))

        if result > 0:
            query2 = "DELETE FROM products WHERE id=%s"

            cursor.execute(query2,(id,))

            mysql.connection.commit()

            cursor.close()

            flash("Deleted is successful","info")

            return redirect(url_for("dashboard"))

        else:
            flash("unauthorized action", "danger")
            return redirect(url_for("index"))
                


    else:
        flash("You are not authorized for this action", "danger")
        return redirect(url_for("index"))



@app.route("/update/<string:id>", methods=["POST", "GET"])
def update(id):

    if session:
        if request.method == "GET":
            cursor = mysql.connection.cursor()

            query = "SELECT * FROM products WHERE id = %s and  sharing= %s"

            result = cursor.execute(query,(id,session["username"]))


            
            if result > 0:
                form =ProductForm()

                product = cursor.fetchone()

                form.product.data = product["product"]

                form.features.data = product["features"]

                return render_template("update.html",form=form)               

            
            else:

                flash("unauthorized action", "danger")
                return redirect(url_for("index"))
        else:
            form = ProductForm(request.form)

            new_product = form.product.data
            new_features = form.features.data

            cursor = mysql.connection.cursor()

            update = "UPDATE products SET product=%s , features=%s WHERE id=%s"

            cursor.execute(update, (new_product, new_features,id))

            mysql.connection.commit()

            cursor.close()

            flash("Update is succesful", "info")

            return redirect(url_for("dashboard"))


           
    else:
        return render_template("dashboard.html")










if __name__ =="__main__":
    app.run(debug=True)