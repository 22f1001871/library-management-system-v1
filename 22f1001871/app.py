import datetime
from flask_restful import Api,Resource,fields,marshal_with,reqparse
from flask import Flask,render_template,request,redirect,url_for
from sqlalchemy import asc,desc
from flask_sqlalchemy import SQLAlchemy
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

app=Flask(__name__)

api=Api(app)

parser=reqparse.RequestParser()

parser.add_argument('sname')
parser.add_argument('description')

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///LIBRARY.sqlite3'
db=SQLAlchemy(app)

user=None
sections=None

#model for username and password
class USER(db.Model):
    __tablename__="USER"
    uid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    uname=db.Column(db.String,nullable=False)
    password=db.Column(db.String,nullable=False)
    isadmin=db.Column(db.Boolean,default=False)

#model for sections
class SECTIONS(db.Model):
    __tablename__="SECTIONS"
    sid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    sname=db.Column(db.String,nullable=False,unique=True)
    sdate=db.Column(db.Date,nullable=False)
    description=db.Column(db.String)
    rawname=db.Column(db.String)

#model for ebooks
class BOOKS(db.Model):
    __tablename__="BOOKS"
    bid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    biid=db.Column(db.Boolean,default=False)
    sid=db.Column(db.Integer,db.ForeignKey('SECTIONS.sid'))
    bname=db.Column(db.String,nullable=False)
    bauthours=db.Column(db.String,nullable=False)
    rating=db.Column(db.Integer,default=0)
    user_issued=db.Column(db.Integer,db.ForeignKey('USER.uid'),default=0)
    bookissueddate=db.Column(db.Date,default=None)
    bookreturndate=db.Column(db.Date,default=None)
    bookprice=db.Column(db.Integer,default=100)
    rawbook=db.Column(db.String)
    rawauth=db.Column(db.String)

#model for cart
class CART(db.Model):
    __tablename__="CART"
    cid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    userid=db.Column(db.Integer,db.ForeignKey('USER.uid'))
    bookid=db.Column(db.Integer,db.ForeignKey('BOOKS.bid'))
    requestdate=db.Column(db.Date,nullable=False)   
    days=db.Column(db.Integer) 

#model for book issued details
class RATING(db.Model):
    __tablename__="RATING"
    rid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    uid=db.Column(db.Integer,db.ForeignKey('USER.uid'))
    bookid=db.Column(db.Integer,db.ForeignKey('BOOKS.bid'))
    rating=db.Column(db.Integer)

#model to show  book
class MYBOOKS(db.Model):
    __tablename__="MYBOOKS"
    mbid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    uid=db.Column(db.Integer,db.ForeignKey('USER.uid'))
    bookid=db.Column(db.Integer,db.ForeignKey('BOOKS.bid'))
    bname=db.Column(db.String)
    amountpaid=db.Column(db.Integer)

with app.app_context():
    db.create_all()

#route for homepage
@app.route("/")
def index():
    return render_template("HOME.html")

#route for registering normal user
@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        userdb=USER(uname=request.form.get("Username"),password=request.form.get("Password"))
        db.session.add(userdb)
        db.session.commit()
        return redirect(url_for("ulogin"))
    return render_template("REGISTER.html")

#route for userlogin
@app.route("/userlogin",methods=["GET","POST"])
def ulogin():
    global user,sections
    if request.method=="POST":
        user=USER.query.filter_by(uname=request.form.get("Username")).all()
        sections=SECTIONS.query.all()
        for j in user:
            if j.password==request.form.get("Password") and j.isadmin==False:
                a=BOOKS.query.filter_by(user_issued=j.uid).all()
                for i in a:
                    if i.bookissueddate==None:
                        break
                    elif i.bookreturndate<=datetime.datetime.now().date():
                        i.biid=False
                        db.session.commit()
                        i.user_issued=0
                        db.session.commit()
                        i.bookissueddate=None
                        db.session.commit()
                        i.bookreturndate=None
                        db.session.commit()
                    else:
                        continue
                user=j
                return render_template("DASHBOARD.html",username=j.uname,isadmin=j.isadmin,section=sections)
    return render_template("ULOGIN.html")

#route for sepearate librianlogin
@app.route("/libraianlogin",methods=["GET","POST"])
def llogin():
    global user,sections
    if request.method=="POST":
        user=USER.query.filter_by(uname=request.form.get("Username")).first()
        sections=SECTIONS.query.all()
        if user.isadmin and user.password==request.form.get("Password"):
            return render_template("LIBRDASHBOARD.html",username=user.uname,isadmin=user.isadmin,section=sections)
    return render_template("LLOGIN.html")

#route for dashboard for user
@app.route("/dashboard",methods=["GET","POST"])
def dashboard():
    if request.method=="POST":
        return render_template("DASHBOARD.html")
    
#route for home
@app.route("/home")
def home():
    global user,sections
    sections=SECTIONS.query.all()
    if user.isadmin==True:
        return render_template("LIBRDASHBOARD.html",username=user.uname,isadmin=user.isadmin,section=sections)
    else:
        return render_template("DASHBOARD.html",username=user.uname,isadmin=user.isadmin,section=sections)

#route for logout
@app.route("/logout")
def logout():
    global user
    user=None
    return redirect(url_for("index"))

    
#route for adding an book
@app.route("/addbook/<id>",methods=["GET","POST"])
def addbook(id):
    if request.method=="POST":
        bname=request.form.get("bname")
        sid=id
        bauth=request.form.get("author")
        book=BOOKS(bname=bname,sid=sid,bauthours=bauth,rawbook=raw(bname),rawauth=raw(bauth))
        db.session.add(book)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("/ADDBOOK.html",sid=id)

#route for adding an section
@app.route("/addsection",methods=["GET","POST"])
def addsection():
    if request.method=="POST":
        sname=request.form.get("sname")
        description=request.form.get("description")
        sdate=datetime.datetime.now()
        sraw=raw(sname)
        section=SECTIONS(sname=sname,sdate=sdate,description=description,rawname=sraw)
        db.session.add(section)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("/ADDSECTION.html")

#route for deleting a book
@app.route("/deletebook/<id>")
def delbook(id):
    delete=BOOKS.query.filter_by(bid=id).first()
    db.session.delete(delete)
    db.session.commit()
    return redirect(url_for("home"))


#route for deleting a section
@app.route("/delete/<id>")
def delsec(id):
    delete=SECTIONS.query.filter_by(sid=id).first()
    deletebook=BOOKS.query.filter_by(sid=id).all()
    db.session.delete(delete)
    db.session.commit()
    for i in deletebook:
        db.session.delete(i)
        db.session.commit()
    return redirect(url_for("home"))

#route for requests recived form user to show in librian page
@app.route("/requests")
def requests():
    req=CART.query.all()
    uname=USER.query.all()
    bname=BOOKS.query.all()
    return render_template("REQUESTS.html",requests=req,uname=uname,bname=bname)


#route for showing books on click on section for libraian
@app.route("/books/<id>")
def books(id):
    books=BOOKS.query.filter_by(sid=id).order_by(desc(BOOKS.rating)).all()
    uname=USER.query.all()
    return render_template("BOOKS.html",book=books,uname=uname)

#rotue for showing books on click section for user
@app.route("/book/<id>")
def book(id):
    books=BOOKS.query.filter_by(sid=id).all()
    uname=USER.query.all()
    return render_template("USERBOOKS.html",book=books,uname=uname)


#route for editing a section
@app.route("/edit/<id>",methods=["GET","POST"])
def editsection(id):
    if request.method=="POST":
        sname=request.form.get("sectionname")
        description=request.form.get("description")
        section=SECTIONS.query.filter_by(sid=id).first()
        section.sname=sname
        section.description=description
        section.sid=id
        section.rawname=raw(sname)
        #section.sdate=datetime.datetime.now()
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("SECTIONUPDATE.html",sid=id)


#route for editing a book
@app.route("/editbook/<id>",methods=["GET","POST"])
def editbook(id):
    if request.method=="POST":
        bname=request.form.get("bookname")
        bauth=request.form.get("author")
        #rating=request.form.get("rating")
        #userid=request.form.get("userid")
        book=BOOKS.query.filter_by(bid=id).first()
        book.bname=bname
        book.bauthours=bauth
        #book.ratings=rating
        #book.user_issued=userid
        book.rawbook=raw(bname)
        book.bookauth=raw(bauth)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("BOOKUPDATE.html",bid=id)

#route for requesting book and add it to cart
@app.route("/days/<id>",methods=["GET","POST"])
def days(id):
    global user
    if request.method=="POST":
        days_requested=request.form.get("days")
        cart=CART(userid=user.uid,bookid=id,requestdate=datetime.datetime.now(),days=days_requested)
        db.session.add(cart)
        db.session.commit()
        a=BOOKS.query.filter_by(bid=id).first()
        a.user_issued=user.uid
        db.session.add(a)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("DAYS.html",id=id)
    
#route for showing the requested book details in cart
@app.route("/cart",methods=["GET","POST"])
def usercart():
    global user
    book=BOOKS.query.filter_by(user_issued=user.uid).all()
    cart=CART.query.filter_by(userid=user.uid).all()
    return render_template("CART.html",cart=cart,book=book)

#route to accept the request or deny by user
@app.route("/accept/<id>",methods=["GET","POST"])
def accept(id):
    global user
    req=CART.query.filter_by(cid=id).first()
    bookissue=BOOKS.query.filter_by(bid=req.bookid).first()
    bookissue.biid=True
    db.session.commit()
    bookissue.bookissueddate=datetime.datetime.now().date()
    db.session.commit()
    bookissue.bookreturndate=bookissue.bookissueddate+datetime.timedelta(req.days)
    db.session.commit()
    db.session.delete(CART.query.filter_by(cid=id).first())
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/deny/<id>",methods=["GET","POST"])
def deny(id):
    global user
    req=CART.query.filter_by(cid=id).first()
    db.session.delete(req)
    db.session.commit()
    a=BOOKS.query.filter_by(bid=req.bookid).first()
    a.user_issued=0
    db.session.add(a)
    db.session.commit()
    return redirect(url_for("home"))

#route for MYBOOS
@app.route("/mybooks",methods=["GET","POST"])
def mybooks():
    global user
    req=BOOKS.query.filter_by(user_issued=user.uid,biid=True).all()
    paidbooks=MYBOOKS.query.filter_by(uid=user.uid).all()
    return render_template("MYBOOKS.html",mybooks=req,paidbooks=paidbooks)

#route for BOOK LIST ISSUED
@app.route("/bookissuedlist",methods=["GET","POST"])
def booklistissued():
    req=BOOKS.query.filter_by(biid=True).all()
    uname=USER.query.all()
    return render_template("LIBRIBOOKISSUED.html",bookissued=req,uname=uname)

#route for book revoking
@app.route("/deletebookissued/<id>",methods=["GET","POST"])
def bookrevoke(id):
    req=BOOKS.query.filter_by(bid=id).first()
    req.user_issued=0
    db.session.commit()
    req.biid=False
    req.bookissueddate=None
    db.session.commit()
    req.bookreturndate=None
    db.session.commit()
    return redirect(url_for('home'))

def raw(text):
    split_list=text.split()
    scrch_word=''
    for word in split_list:
        scrch_word+=word.lower()
    return scrch_word

#route for search
@app.route('/search')
def search():
    srch_word=request.args.get('srch_wrd')
    srch_word="%"+raw(srch_word)+"%"
    srch_word=SECTIONS.query.filter(SECTIONS.rawname.like(srch_word)).all()
    return render_template("SEARCH.html",section=srch_word)

#route for usersearch
@app.route('/usearch')
def srch():
    srch_word=request.args.get('srch_wrd')
    srch_word="%"+raw(srch_word)+"%"
    srch_word=SECTIONS.query.filter(SECTIONS.rawname.like(srch_word)).all()
    return render_template("USERSEARCH.html",section=srch_word)

#route for search
@app.route('/booksearch')
def ebook():
    srch_word=request.args.get('srch_wrd')
    srch_word="%"+raw(srch_word)+"%"
    src_word=BOOKS.query.filter(BOOKS.rawbook.like(srch_word)).all()
    src_wrd=BOOKS.query.filter(BOOKS.rawauth.like(srch_word)).all()
    return render_template("BOOKSEARCH.html",books=src_word,authors=src_wrd)


#route for rating
@app.route('/rating/<id>',methods=['GET','POST'])
def rating(id):
    global user
    a=0
    b=0
    if request.method=='POST':
        rating=request.form.get('rating')
        book=BOOKS.query.filter_by(bid=id).first()
        db.session.add(RATING(uid=user.uid,bookid=id,rating=rating))
        db.session.commit()
        bookrating=RATING.query.filter_by(bookid=id).all()
        for i in bookrating:
            b+=1
            a+=i.rating
            print(a/b)
        book.rating=a/b
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('RATING.html',id=id)

#route for buying
@app.route('/buy/<id>',methods=['GET','POST'])
def buy(id):
    global user
    if request.method=='POST':
        buy=request.form.get('buy')
        book=BOOKS.query.filter_by(bid=id).first()
        db.session.add(MYBOOKS(uid=user.uid,bookid=id,bname=book.bname,amountpaid=buy))
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('BUY.html',id=id)

#route for histogram
@app.route('/stats')
def show_stats():
    books=db.session.query(BOOKS.bname,BOOKS.rating).order_by(desc(BOOKS.rating)).limit(5).all()
    bookname,rating=[],[]
    for book in books:
        bookname.append(book.bname)
        rating.append(book.rating)
    #plt.switch_backend('Agg')
    plt.clf()
    #plt.figure()
    plt.bar(bookname,rating,color='skyblue')
    plt.title('TOP 5 RATED BOOKS')
    plt.savefig('static/img.png')
    return render_template('STATISTICS.html')

#route for showing image
@app.route('/img')
def img():
    return render_template('img.html')

#route for display pdf
@app.route('/pdf')
def pdf():
    return render_template('demo.html')

#api part
class LibApi(Resource):
    def get(self,sec_id):
        books=BOOKS.query.filter_by(sid=sec_id).all()
        booknames=[]
        for i in books:
            booklist={}
            booklist["bid"]=i.bid
            booklist["bname"]=i.bname
            booklist["bauth"]=i.bauthours
            booklist["rating"]=i.rating
            booklist["sid"]=i.sid
            booknames.append(booklist)
        return booknames
    
    def post(self,sec_id):
        addsection=parser.parse_args()
        newsec=SECTIONS(sname=addsection["sname"],sdate=datetime.datetime.now(),description=addsection["description"],rawname=raw(addsection["sname"]))
        db.session.add(newsec)
        db.session.commit()
        return "SECTION CREATED SUCCESSFULLY",201
    
    def put(self,sec_id):
        up_sec=SECTIONS.query.filter_by(sid=sec_id).first()
        addsection=parser.parse_args()
        up_sec.sname=addsection["sname"]
        up_sec.description=addsection["description"]
        up_sec.rawname=raw(addsection["sname"])
        db.session.commit()
        return "SECTION UPDATED SUCCESSFULLY",201
    
    def delete(self,sec_id):
        delete=SECTIONS.query.filter_by(sid=sec_id).first()
        db.session.delete(delete)
        db.session.commit()
        return "SECTION DELETED SUCCESSFULLY",201


api.add_resource(LibApi,'/api/getbooks/<int:sec_id>')

if __name__=="__main__":
    app.run(debug=True)