#libraries used
from flask import Flask,render_template,request,redirect,session,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
import smtplib
import random as r
import pygal
from passlib.context import CryptContext

pwd_context = CryptContext(                                             #pbkdf2_sha256 encryption used to save password        
        schemes=["pbkdf2_sha256"],                                              
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
)

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/voting'              
app.secret_key="hellothere"
secret_key='hello'
admin_username='admin'                                                          #default admin password
admin_password="1234"
db = SQLAlchemy(app)

class Voter(db.Model):                                                                  #DATABASE MODEL
    Sno = db.Column(db.Integer, primary_key=True)
    Name = db.Column(EncryptedType(db.String(30),secret_key,AesEngine,'pkcs5'), nullable=False)
    email = db.Column(EncryptedType(db.String(30),secret_key,AesEngine,'pkcs5'), nullable=False)
    DOB= db.Column(db.String(30), nullable=False)
    Register = db.Column(db.Integer, unique=True, nullable=False)
    Valid= db.Column(db.Boolean,nullable=False)
    Voted= db.Column(db.Boolean,nullable=False)
    Password=db.Column(db.String(120), nullable=False)

class Candidate(db.Model):
    Sno = db.Column(db.Integer, primary_key=True)
    Name = db.Column(EncryptedType(db.String(30),secret_key,AesEngine,'pkcs5'), nullable=False)
    Register = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(EncryptedType(db.String(30),secret_key,AesEngine,'pkcs5'), nullable=False)
    DOB= db.Column(db.String(30), nullable=False)
    Count = db.Column(db.Integer, nullable=False)

class temp(db.Model):                                                                  #DATABASE MODEL
    Sno = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    DOB= db.Column(db.String(30), nullable=False)
    Register = db.Column(db.Integer, unique=True, nullable=False)
    Valid= db.Column(db.Boolean,nullable=False)
    Voted= db.Column(db.Boolean,nullable=False)

@app.route('/')
def home():    
    session['adminlogin']=False
    session['voterlogin']=False                              
    session['votersignup']=False                                       #homepage
    return render_template("home.html")

@app.route('/about')                                                                #team details
def about():
    return render_template("about.html")
@app.route('/admin_login', methods=["GET","POST"])
def admin_login():                                                                  #admin loginpage 
    if request.method=="POST":
        username=request.form.get('username')
        password=request.form.get('password')
        if(admin_password==password and password==admin_password):
            session['adminlogin']=True
            return redirect(url_for("candidate_reg"))
        else:
            flash("Invalid Username and Password")
            return  render_template("admin_login.html")
    return render_template("admin_login.html")

@app.route('/candidate')
def candidate():      
    if session['adminlogin']==True:                                                      #to view list of candidates 
        candidates=Candidate.query.all()
        return render_template("candidate.html",candidates=candidates)
    else:
        return redirect('/')

@app.route('/voter')                                                        #to view list of voters
def voter():
    if session['adminlogin']==True:
        voters=Voter.query.filter(Voter.Valid.like(1)).all()
        return render_template("voter.html",voters=voters)
    else:
        return redirect('/')

@app.route('/delete',methods=["GET","POST"])                                #to delete voters who entered invalid details after validation
def delete():
    if request.method=="POST":
        Register=request.form.get('Delete')
        voter=Voter.query.filter(Voter.Register.like(Register)).first()
        db.session.delete(voter)
        db.session.commit()
    return redirect('/validatevoter')
        
@app.route('/validatevoter',methods=["GET","POST"])                         #to validate voters details
def validatevoter():
    if request.method=="POST" and session['adminlogin']==True:
        Register=request.form.get('Validate')
        voter=Voter.query.filter(Voter.Register.like(Register)).first()
        voter.Valid=True
        db.session.commit()
        voters=Voter.query.filter(Voter.Valid.like(0)).all()
        flash("Voter Validated Successfully")
        return render_template("validatevoter.html",voters=voters)
        
    elif session['adminlogin']== False:
        return redirect('/')
        
    else:
        print("1")
        voters=Voter.query.filter(Voter.Valid.like('0')).all()
        if(len(voters)>0):
            return render_template("validatevoter.html",voters=voters)
        else:
            flash("No voters to validate","info")
            return render_template("validatevoter.html")

@app.route('/candidate_reg', methods=["GET","POST"])                        #candidate registration (admin panel)
def candidate_reg():
    if request.method=="POST" and session['adminlogin']==True:
        try:
            Name=request.form.get('Name')
            email=request.form.get('email')
            DOB=request.form.get('DOB')
            Register=request.form.get('Register')
            entry= Candidate(Name=Name, email=email,DOB=DOB,Register=Register,Count=0)
            db.session.add(entry)
            db.session.commit()
            flash("Candidate Added Successfully!","info")
            return render_template("candireg.html")
        except:
            flash("Candidate Already Exist ","info")
            return render_template("candireg.html")
    elif session['adminlogin']==False:
        return render_template("home.html")
    else:
        return render_template("candireg.html")
        
@app.route('/otplogin',methods=["GET","POST"])                              #enter otp for login
def otp_login():
    if request.method=="POST" and session['voterlogin']==True:
        if session['otp']==request.form.get('otp'):
            candidates=Candidate.query.all()
            return render_template("castvote.html",candidates=candidates)
        else:
            return render_template("otplogin.html")
    elif session['voterlogin']==False:
        return redirect('/')
    else:
        return render_template('otplogin.html')

@app.route('/otpsignup',methods=["GET","POST"])
def otp_signup():
    if request.method=="POST" and session['votersignup']==True:
        if session['otp']==request.form.get('otp'):
            flash("Your email is verified successfully. You can Login after ur account details are validated")
            return render_template("login.html")
        else:
            flash("Invalid OTP")
            return render_template('otpsignup.html')
    elif session['votersignup']==False:
        return render_template("home.html")
    else:
        return render_template('otpsignup.html')

@app.route('/login', methods=["GET","POST"])                                #voters login after validation (voter's panel)
def login():
    if request.method=="POST":
        Register=request.form.get('Register')
        Password=request.form.get('Password')
        voter=Voter.query.filter(Voter.Register.like(Register)).first()
        hashed=voter.Password
        if(voter!=None and voter.Voted==False and voter.Valid==True and pwd_context.verify(Password, hashed)):     #to check that the voter cast only one vote and is validated by admin
            session['Register']=Register
            session['voterlogin']=True
            email=voter.email
            print(email)
            otp=""
            for i in range(4):
                otp+=str(r.randint(1,9))
            session['otp']=otp
            message="Your OTP for registration is {}".format(otp)
            server=smtplib.SMTP("smtp.gmail.com", 587)                                  #sending confirmation mail
            server.starttls()
            server.login("msdea.svh@gmail.com","msdea@svh2020")     
            server.sendmail("msdea.svh@gmail.com",email,message)
            flash("Enter the otp sent to your mail","info")
            return render_template("otplogin.html")
        elif(voter!=None and voter.Voted==True):
            flash("You Have Already Voted!")
            return render_template("login.html")
        elif(voter!=None and voter.Valid==False):
            flash("Your data is not validated yet retry after some time. If this problem continues contact Admin for enquiry.","info")
            return render_template("login.html")
        else:
            flash("Invalid Username or Password")
            return render_template("login.html") 
    else:
        return render_template('login.html')  

@app.route('/castvote',methods=["GET","POST"])                                      #casting vote to candidate
def castvote():
    if request.method=="POST" and session['voterlogin']==True:
        temp_candidate_register=request.form.get('vote')
        temp_register=session['Register']
        voter=Voter.query.filter(Voter.Register.like(temp_register)).first()
        candidate=Candidate.query.filter(Candidate.Register.like(temp_candidate_register)).first()
        candidate.Count+=1
        voter.Voted=True
        db.session.commit()
        flash("You Voted Sucessfully!","info")
        return render_template("login.html")
    elif session['voterlogin']==False:
        return redirect('/')
    else:
        return render_template("login.html")

@app.route('/graph',methods=["GET","POST"])                     
def graph():
    try:
        if(session['adminlogin']==True):
            candidates=Candidate.query.all()
            candiname=[]
            candivote=[]
            for i in candidates:
                candiname.append(i.Name)
                candivote.append(i.Count)
            line_chart = pygal.HorizontalBar()                              #bar graph
            line_chart.title = 'Vote Count'
            for i in range(len(candiname)):
                line_chart.add(candiname[i], candivote[i])
            line_chart=line_chart.render_data_uri()
            voter_voted=Voter.query.filter(Voter.Voted.like('1')).all()
            voter_not_voted=Voter.query.filter(Voter.Voted.like('0')).all()
            pie_chart = pygal.Pie()
            pie_chart.title = "Voting Turnout"
            pie_chart.add('Voted', len(voter_voted))
            pie_chart.add('Not Voted', len(voter_not_voted))
            pie_chart=pie_chart.render_data_uri()
            return render_template("graph.html",line_chart=line_chart,pie_chart=pie_chart)
        else:
            return redirect('/')
    except:
        flash("Error Loading Graph!","info")
        return render_template("graph.html")

@app.route('/signup', methods=["GET","POST"])                                       #Registration of voter
def signup():
    
    if request.method=="POST":
        Name=request.form.get('Name')
        email=request.form.get('email')
        DOB=request.form.get('DOB')
        Register=request.form.get('Register')
        session['votersignup']=True
        Password=pwd_context.encrypt(request.form.get('Password'))
        try:
            entry=Voter(Name=Name,email=email,DOB=DOB,Register=Register,Valid=False,Voted=False,Password=Password)
            db.session.add(entry)
            db.session.commit()
            otp=""
            for i in range(4):
                otp+=str(r.randint(1,9))
            session['otp']=otp
            message="Your OTP for registration is {}".format(otp)
            server=smtplib.SMTP("smtp.gmail.com", 587)                                  #sending confirmation mail
            server.starttls()
            server.login("msdea.svh@gmail.com","msdea@svh2020")     
            server.sendmail("msdea.svh@gmail.com",email,message)
            flash("Enter the otp sent to your mail","info")
            return render_template("otpsignup.html")
        except:
            flash("User Already Exist!","info")
            return render_template("signup.html")        
    else:
        return render_template('signup.html')


if __name__=='__main__':
    app.run(debug=True)