#Designed By Mustafa Öztaş
#twitter.com/oztas_py


from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)
app.secret_key = "btblog" #flask mesajları için

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "btblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

#login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu Sayfayı Görüntülemek İçin Yeterli Yetkiniz Yok!","danger")
            return redirect(url_for("login"))

    return decorated_function


#Kullanıcı kayıt formu 
class RegisterForm(Form):
    name = StringField("İsim-Soyisim: ",validators=[validators.length(min= 2,max=20),validators.DataRequired(message= "Devam etmek için lütfen burayı doldurunuz..!")])
    username = StringField("Kullanıcı Adı: ",validators=[validators.length(min= 5,max=15),validators.DataRequired(message="Devam etmek için lütfen burayı doldurunuz..!")])
    email = StringField("E-Posta: ",validators=[validators.Email(message="Lütfen Geçerli Bir E-Posta Adresi Giriniz..!")])
    password = PasswordField("Parola: ", validators=[
        validators.length(min=6,max=18,message="Lütfen 6-18 Karakter Arası Bir Şifre Belirleyiniz!"),
        validators.DataRequired(message= "Burası Boş Bırakılamaz!!"),
        validators.EqualTo(fieldname="confirm",message="Parolalar Uyuşmuyor!Tekrar Deneyiniz..")
    ])
    confirm = PasswordField("Parolayı Tekrar Giriniz: ")

#login form
class LoginForm(Form):
    username = StringField("Kullanıcı Adı: ",validators=[validators.length(min=5,max=15,message="Kullanıcı Adı 5-15 Karakter Arasındadır!"),validators.DataRequired(message="Devam etmek için lütfen burayı doldurunuz..!")])
    password = PasswordField("Parola: ",validators=[validators.length(min=6,max=18,message="Lütfen 6-18 Karakterden Oluşan Şifrenizi Giriniz!"),validators.DataRequired(message="Devam etmek için lütfen burayı doldurunuz..!")])

#Makale Ekleme Formu
class ArticleForm(Form):
    title = StringField("Makale Adı ",validators=[validators.length(min=5,max=50,message="Makale Adı 5-50 Karakter Arasındadır!"),validators.DataRequired(message="Makale Adı Boş Bırakılamaz!")])
    content = TextAreaField("Makale İçeriği ",validators=[validators.length(min=20,message="Makale En Az 20 Karakterden Oluşmalıdır!"),validators.DataRequired(message="İçerik Boş Bırakılamaz!")])
    
    
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

#kayıt ol sayfası
@app.route("/register",methods = ["GET","POST"])
def register():
    
    form = RegisterForm(request.form) #post yapıldığında verilerin alınması için request.form

    if request.method == "POST" and form.validate(): #validate:form doğruysa true verir.

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit() #veritabanını güncellerken mutlaka kullanılır

        cursor.close() # işlem bittikten sonra kapatmamız gerekir.Sistem yükünü azaltır.

        flash("Kayıt Başarılı!","success") #flask message

        return redirect(url_for("login")) #ilgili olan url'ye götürür.
    else:
        return render_template("register.html",form = form)

#login işlemi
@app.route("/login",methods =["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
       username = form.username.data
       password_entered = form.password.data

       cursor = mysql.connection.cursor()

       sorgu = "Select * From users where username = %s"

       result = cursor.execute(sorgu,(username,))

       if result > 0: #result 0'dan büyükse kullanıcı var
           data = cursor.fetchone() #kullanıcının bütün bilgilerini alır
           real_pass = data["password"] #verinin üzerinde gezinerek password'u çekiyoruz
           if sha256_crypt.verify(password_entered,real_pass): #verify() ile parolanın eşleşip eşleşmediğini kontrol ediyoruz
               flash("Giriş Başarılı! Hoşgeldiniz..","success")
               
               session["logged_in"] = True
               session["username"] = username


               return redirect(url_for("index")) 
           else:
               flash("Hatalı Parola!","danger")
               return redirect(url_for("login")) 
            

       else: #result 0 ise kullanıcı yok
           flash("Kullanıcı Adı Hatalı!","danger")
           return redirect(url_for("login"))        

    return render_template("login.html",form= form)


@app.route("/logout")
def logout(): #Oturum verileri temizleniyor
    session.clear() 
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required #Kullanıcı girişi kontrolü gerektiren bütün fonksiyonlardan önce bu decorator kullanılabilir
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")



    return render_template("dashboard.html")

#makale ekleme
@app.route("/dashboard/addarticle", methods= ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()

        flash("Makale Başarıyla Eklendi","success")

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html",form = form)

#Article Pages
@app.route("/articles")
def article():
    
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles"

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")

#article detail page
@app.route("/article/<string:id>")
def detail(id):
    cursor = mysql.connection.cursor()
    
    sorgu = "Select * from articles where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")

#article deleted
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "Delete from articles where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()
        cursor.close()
        return redirect(url_for("dashboard"))
    else:
        flash("Bu İşlemi Gerçekleştirmek İçin Yeterli Yetkiniz Yok!","danger")
        return redirect(url_for("index"))

#article updates
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):

    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "Select * From articles where id = %s and author = %s"

        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("Sayfa Bulunamıyor Yada Bu İşlemi Gerçekleştirmek İçin Yeterli Yetkiniz Yok!","danger")
            return redirect(url_for("index"))

        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)


    else: #POST request

        form = ArticleForm(request.form)

        yeni_isim = form.title.data
        yeni_icerik = form.content.data

        sorgu2 = "Update articles Set title = %s,content = %s where id = %s "

        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2,(yeni_isim,yeni_icerik,id))

        mysql.connection.commit()
        cursor.close()

        flash("Makale başarıyla güncellendi","success")

        return redirect(url_for("dashboard"))

        
#article search
@app.route("/search",methods = ["GET","POST"])
def search():
    
    if request.method == "GET":
        return redirect(url_for("index"))

    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()

        sorgu = "Select * From articles where title like '%" + keyword + "%' "

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Veritabanında Böyle Bir Makale Bulunmuyor!","danger")
            return redirect(url_for("dashboard"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)


#user profile
@app.route("/dashboard/profile/<string:id>")
@login_required
def profile(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from users where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        user = cursor.fetchone()
        return render_template("profile.html", user = user)

    else:
        return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)
