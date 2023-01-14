from flask import Flask,render_template,flash,redirect,url_for,session,logging,request,g
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

app=Flask(__name__)
app.secret_key="sinalcelik"

app.config["MYSQL_HOST"]="muratkavak.mysql.pythonanywhere-services.com"
app.config["MYSQL_USER"]="muratkavak"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="sinalcelik"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql=MySQL(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giris yapınız.","danger")
            return redirect(url_for("login"))
    return decorated_function

class LoginForm(Form):
    username=StringField("Kullanıcı Adı:")
    password=PasswordField("Parola:")

class passchange(Form):
    newpass=PasswordField("Yeni Parola:")
    newpassconfirm=PasswordField("Parola Tekrar:")

class ArticleFrom(Form):
    title=StringField("Makale Baslıgı:",validators=[validators.length(min=5,max=100)])
    content=TextAreaField("İcerik:",validators=[validators.length(min=20)])

@app.route("/login",methods=["GET","POST"])
def login():
    loginform=LoginForm(request.form)
    if request.method=="POST":
        username=loginform.username.data
        password=loginform.password.data
        cursor=mysql.connection.cursor()
        result=cursor.execute("SELECT * FROM users WHERE username=%s",(username,))
        if result:
            data=cursor.fetchone()
            realPassword=data["password"]
            if sha256_crypt.verify(password,realPassword):
                flash("Basariyla giris yaptiniz.","success")
                session["logged_in"]=True
                session["username"]=username
                cursor.close()
                return redirect(url_for("index"))
            else:
                flash("Sifre hatali.","danger")
                cursor.close()
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunamadı.","danger")
            return redirect(url_for("login"))
            cursor.close()
    else:
        return render_template("login.html",loginform=loginform)
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/article/<string:id>")
def article(id):
    cur=mysql.connection.cursor()
    result=cur.execute("SELECT * FROM articles WHERE id=%s",(id,))

    if result:
        data=cur.fetchone()
        return render_template("article.html",article=data)
    else:
        return render_template("article.html")

@app.route("/addarticle",methods=["GET","POST"])
@login_required
def addarticle():
    form=ArticleFrom(request.form)

    if request.method=="POST" and form.validate():
        title=form.title.data
        content=form.content.data
        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO articles(title,content) VALUES(%s,%s)",(title,content))
        mysql.connection.commit()
        cur.close()
        flash("Makale Kaydı Basariyla Gerceklesti !","success")
        return redirect(url_for("dashboard"))
    else:
        return render_template("addarticle.html",form=form)

@app.route("/logout")
def logout():
    session.clear()
    flash("Basariyla cikis yapildi.","success")
    return redirect(url_for("index"))

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cur=mysql.connection.cursor()
    sorgu="SELECT * FROM articles WHERE id=%s"
    result=cur.execute(sorgu,(id,))

    if result>0:
        cur.execute("DELETE FROM articles WHERE id=%s",(id,))
        mysql.connection.commit()
        flash("Makale silme basarili.","success")
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok.","danger")
        return redirect(url_for("index"))

@app.route("/edit/<string:id>",methods=["POST","GET"])
@login_required
def update(id):
    
    if request.method=="GET":
        cur=mysql.connection.cursor()
        result=cur.execute("SELECT * FROM articles WHERE id=%s",(id,))
        if result==0:
            flash("Böyle bir makale yok.","danger")
            return redirect(url_for("index"))
        else:
            article=cur.fetchone()
            form=ArticleFrom()
            form.title.data=article["title"]
            form.content.data=article["content"]
            return render_template("update.html",form=form)
    else:
        form=ArticleFrom(request.form)
        newtitle=form.title.data
        newcontent=form.content.data
        cur=mysql.connection.cursor()
        cur.execute("UPDATE articles SET title=%s,content=%s WHERE id=%s",(newtitle,newcontent,id))
        mysql.connection.commit()

        flash("Makale basariyla güncellendi.","success")
        return redirect(url_for("dashboard"))

@app.route("/dashboard")
@login_required
def dashboard():
    cur=mysql.connection.cursor()

    result=cur.execute("SELECT * FROM articles")
    if result:
        data=cur.fetchall()
        return render_template("dashboard.html",articles=data)
    else:
        flash("")
        return render_template("dashboard.html")

@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")
        cur=mysql.connection.cursor()
        result=cur.execute("SELECT * FROM articles WHERE title LIKE '%"+ keyword +"%'")
        if result:
            articles=cur.fetchall()
            return render_template("articles.html",articles=articles)
        else:
            flash("Aranan kelimeye uygun makale bulanamadı.","warning")
            return redirect(url_for("articles"))


@app.route("/articles")
def articles():
    cur=mysql.connection.cursor()
    result=cur.execute("SELECT * FROM articles")
    if result:
        data=cur.fetchall()
        return render_template("articles.html",articles=data)
    else:
        return render_template("articles.html")

@app.route("/changepassword",methods=["POST","GET"])
@login_required
def changePass():
    form=passchange(request.form)
    cur=mysql.connection.cursor()
    if request.method=="POST":
        newpass=form.newpass.data
        newpassconfirm=form.newpassconfirm.data
        if newpass==newpassconfirm:
            newpass=sha256_crypt.encrypt(newpass)
            cur.execute("UPDATE users SET password=%s WHERE username=%s",(newpass,'alaeddin'))
            mysql.connection.commit()
            cur.close()
            flash("Sifre Degistirme Basarili.","success")
            return redirect(url_for("index"))
        else:
            flash("Girilen sifreler uyusmuyor.","warning")
            return redirect(url_for("changePass"))
    else:
        return render_template("changepassword.html",form=form)

@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/")
def index():
    return render_template("index.html")
    
    
if __name__=="__main__":
    app.run()