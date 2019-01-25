from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#Kullanıcı Giriş Decorator`ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
         if "logged_in" in session:
            return f(*args, **kwargs)
         else:
            flash("Bu Sayfayı Görüntüleyebilmek İçin Giriş Yapmalısınız","danger")
            return redirect(url_for("login"))
    return decorated_function

#Kullanıcı Kayıt Formu
class RegisterForm(Form):
   name= StringField("Ad Soyad",validators=[validators.Length(min=4,max=25,message="Minimum 4, Maksimum 25 Karakterr Uzunluğunda Olmalıdır")])
   username= StringField("Kullanıcı Adı",validators=[validators.Length(min=5,max=35,message="Minimum 5, Maksimum 25 Karakterr Uzunluğunda Olmalıdır")])
   email= StringField("E-Mail Adresi",validators=[validators.Email(message="Lütfen Geçerli Bir E-Mail Adresi Girin")])
   password=PasswordField("Parola:",validators=[
      validators.DataRequired(),
      validators.equal_to(fieldname="confirm", message="Parolanız Uyuşmuyor")
   ])
   confirm=PasswordField("Parola Doğrula")
   
#Giriş Formu
class LoginForm(Form):
   username=StringField("Kullanıcı Adı",validators=[validators.DataRequired(message="Lütfen Bir Parola Giriniz")])
   password=PasswordField("Parola",validators=[validators.DataRequired(message="Lütfen Şifrenizi Giriniz")])

#Makale Formu
class ArticleForm(Form):
   title=StringField("Makale Başlığı",validators=[validators.length(min=5,max=100)])
   content=TextAreaField("Makale İçeriği",validators=[validators.length(min=10)])


app= Flask(__name__)
app.secret_key="birhanblog"

app.config["MYSQL_HOST"]='localhost'
app.config["MYSQL_USER"]='root'
app.config["MYSQL_PASSWORD"]=''
app.config["MYSQL_DB"]='birhanblog'
app.config["MYSQL_CURSORCLASS"]='DictCursor'

mysql= MySQL(app)



@app.route('/')
def index():
   cursor=mysql.connection.cursor()
   date =cursor.execute("SELECT DATE_FORMAT('2009-10-04 22:23:00', '%Y-%m-%d');")
   return render_template("index.html",date=date)

@app.route('/articles')
def articles():
   cursor=mysql.connection.cursor()
   result=cursor.execute("select * from articles")
   if result>0:
      articles=cursor.fetchall()
      return render_template("articles.html",articles=articles)
   else:
      return render_template("articles.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/articles/<string:id>')
def detail(id):
   return "article id: " + id

@app.route("/dashboard")
@login_required
def dashboard():
   cursor=mysql.connection.cursor()
   result= cursor.execute("select * from articles where author= %s",(session["username"],))
   if result>0:
      articles=cursor.fetchall()
      return render_template("dashboard.html",articles=articles)
   else:
      return render_template("dashboard.html")

#Kayıt Olma
@app.route('/register',methods=["GET","POST"])
def register():
   form=RegisterForm(request.form)
   if request.method=="POST" and form.validate():
      #veritabanına ekleme
      name=form.name.data
      username=form.username.data
      email=form.email.data
      password=sha256_crypt.encrypt(form.password.data)
      cursor=mysql.connection.cursor()
      
      sorgu="Insert into users (name,email,username,password) VALUES (%s,%s,%s,%s)"
      cursor.execute(sorgu,(name,email,username,password))
      mysql.connection.commit()
      cursor.close()

      flash("Başarıyla Kayıt Oldunuz..","success")
      return redirect(url_for("login"))
   else:
      return render_template("register.html",form=form)


#Login İşlemi
@app.route('/login',methods=["GET","POST"])
def login():
   form=LoginForm(request.form)
   if request.method=="POST":
      username=form.username.data
      password=form.password.data

      cursor=mysql.connection.cursor()
      result=cursor.execute("Select * From users where username = %s",(username,))
      if result>0:
         data=cursor.fetchone()
         real_password=data["password"]
         if sha256_crypt.verify(password,real_password):
            flash("Başarıyla Giriş Yaptınız","success")
            session["logged_in"]=True
            session["username"]=username
            return redirect(url_for("index"))
         else:
            flash("Parola veya Şifre Yanlış. Lütfen Tekrar Deneyiniz.","danger")
            return redirect(url_for("login"))
      else:
         flash("Parola veya Şifre Yanlış. Lütfen Tekrar Deneyiniz.","danger")
         return redirect(url_for("login"))
   else:
      return render_template("login.html",form=form)


#Logut İşlemi
@app.route('/logout')
def logout():
   session.clear() 
   flash("Çıkış Yapıldı.","danger")
   return redirect(url_for("index"))


#Detay Sayfası
@app.route('/article/<string:id>')
def method_name(id):
   cursor=mysql.connection.cursor()
   result=cursor.execute("select * from articles where id=%s",(id,))

   if result>0:
      article=cursor.fetchone()
      return render_template("article.html",article=article)
   else:
      return render_template("article.html")



#Makale Ekleme
@app.route('/addarticle',methods=["GET","POST"])
@login_required
def addarticle():
   form=ArticleForm(request.form)
   if request.method=="POST" and form.validate():
      title=form.title.data
      content=form.content.data
      cursor=mysql.connection.cursor()
      cursor.execute("INSERT INTO articles(title,author,content) values (%s,%s,%s)",(title,session["username"],content))
      mysql.connection.commit()
      cursor.close() 
      flash("Makale Başarıyla Eklendi","success")
      return redirect(url_for("dashboard"))
   return render_template("addarticle.html",form=form)

#Makale Silme
@app.route('/delete/<string:id>')
@login_required
def delete(id):
   cursor=mysql.connection.cursor()
   result=cursor.execute("select * from articles where author=%s and id=%s" ,(session["username"],id))
   if result>0:
      cursor.execute("Delete from articles where id=%s",(id,))
      mysql.connection.commit()
      cursor.close()
      flash("Makale silme işlemi başarılı","success")
      return redirect(url_for("dashboard"))
   else:
      flash("Böyle bir makale bulunmamaktadır veya bu işlem için yetkiniz bulunmamaktadır","danger")
      return redirect(url_for("index"))

#Makale Güncelleme
@app.route('/edit/<string:id>',methods=["GET","POST"])
@login_required
def update(id):
   if request.method=="GET":
      cursor=mysql.connection.cursor()
      result=cursor.execute("select * from articles where id=%s and author=%s",(id,session["username"]))
      if result==0:
         flash("Böyle bir makale yok veya bu işlem için yetkiniz bulunmuyor.","danger")
         return redirect(url_for("index"))
      else:
         article=cursor.fetchone()
         form= ArticleForm()
         form.title.data=article["title"]
         form.content.data=article["content"]
         return render_template("update.html",form=form)
   else:
      form=ArticleForm(request.form)  
      newTitle=form.title.data
      newContent=form.content.data
      cursor=mysql.connection.cursor()
      cursor.execute("update articles set title= %s,content=%s where id=%s",(newTitle,newContent,id))
      mysql.connection.commit()
      flash("Makalle Güncelleme İşlemi Başarıılı","success")
      return redirect(url_for("dashboard"))



#Arama Url
@app.route('/search',methods=["GET","POST"])
def search():
   if request.method=="GET":
      return redirect(url_for("index"))
   else:
      keyword=request.form.get("keyword")
      cursor=mysql.connection.cursor()
      result=cursor.execute("select * from articles where title like '%"+keyword +"%' ")
      if result==0:
         flash("Aranan Kelimeye uygun makale bulunamadı","danger")
         return redirect(url_for("articles"))
      else:
         articles=cursor.fetchall()
         return render_template("articles.html",articles=articles)

if __name__ == "__main__":
    app.run(debug=True)  