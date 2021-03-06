import re
import json
from config import app, bcrypt, db
from flask import Flask, flash, redirect, render_template, request, session, jsonify, url_for
from models import Users, FBUsers, Videos, Streams
from sqlalchemy.sql import func
from flask_bcrypt import Bcrypt


#Index
@app.route("/")
def index():
    return render_template("login_reg.html")
    
#Registration
@app.route("/register", methods=["POST"])
def registration():
    validation_check = Users.validate_user(request.form)
    found = False
    found_user = Users.query.filter_by(email=request.form['email']).all()
    if found_user:
        found = True
        flash("That email already exists in the database", "reg_error")
        return redirect('/')
    if not validation_check:
        print("something went wrong")
        return redirect('/')
    new_user = Users.add_new_user(request.form)
    print(new_user)
    session['logged_in'] = True
    session['user_id'] = new_user.id
    return redirect('/user/' + str(session["user_id"]))

#Email Check
@app.route('/email', methods=["POST"])
def username():
    found = False
    found_user = Users.query.filter_by(email=request.form['email']).all()
    if found_user:
        found = True
    return render_template('/partials/username.html', found=found)

# @app.route("/handle_json", methods=["POST"])
# def handler():
#     data = request.get_json()
#     print(data)
#     return redirect('/user')

#Login 
@app.route("/login", methods=["POST"])
def login():
    user = Users.query.filter_by(email=request.form['lemail']).all()
    is_valid = True if len(user) == 1 and bcrypt.check_password_hash(user[0].passwordHash, request.form['lpassword']) else False
    if is_valid:
        session["logged_in"] = True
        session["user_id"] = user[0].id
        return redirect ('/user/' + str(session["user_id"]))
    else: 
        flash("Invalid Login Credentials", "log_error")
        return redirect('/')
        
#User Profile Page
@app.route("/user/<userID>")
def userRoute(userID):
    if 'user_id' in session:
        thisUser = Users.query.get(session['user_id']) 
        userOwner = Users.query.get(userID)
        return render_template("user.html", thisUser = thisUser, userOwner = userOwner)
    else:
        return redirect('/')


#Stream Page
@app.route("/stream/<userID>")
def stream(userID):
    thisUser = Users.query.get(session['user_id'])
    streamOwner = Users.query.get(userID)
    return render_template('stream.html', streamOwner = streamOwner, thisUser = thisUser)



#Stats Page
@app.route("/stats")
def statsRoute():
    if "user_id" in session:
        thisUser = Users.query.get(session['user_id'])    #will need to check what it's actually called in session
        return render_template('stats.html', thisUser = thisUser)
    else:
        testUser = Users.query.get(1) #TEST USER ID
        return render_template('stats.html', thisUser = testUser)


#Create Page
@app.route("/create")
def createPage():
    if "user_id" in session:
        thisUser = Users.query.get(session['user_id'])    #will need to check what it's actually called in session
        return render_template('create.html', thisUser = thisUser)
    else:
        testUser = Users.query.get(1) #TEST USER ID
        return render_template('create.html', thisUser = testUser)

#Create Video
@app.route("/createVideo/<userID>", methods=['POST'])
def createVideo(userID):
    if "user_id" in session:
        thisUser = Users.query.get(session['user_id'])
        newVid = Videos(title = request.form['title'], video_link = request.form['video_link'], description = request.form['description'], video_author_id = session['user_id'])
        db.session.add(newVid)
        db.session.commit()
        return redirect('/create')
    else:
        return redirect('/create')


#Admin Page
@app.route("/admin")
def adminPage():
    testUser = Users(first_name = "NOT", last_name = "A", email = "USER", admin = False, creator_name = "testcase", description = "description")
    db.session.add(testUser)
    db.session.commit()
    allUsers = Users.query.all()

    # adminUser = Users.query.get(7)
    # adminUser.admin = True
    # db.session.commit()
    
    # Check if User is Admin, if so allow them access
    if "user_id" in session:
        thisUser = Users.query.get(session['user_id'])
        if thisUser.admin == True:
            return render_template('admin.html', thisUser = thisUser, allUsers = allUsers)
        else:
            return redirect('/')
    else:
        testUser = Users.query.get(1) #TEST USER ID
        return render_template('admin.html', thisUser = testUser, allUsers = allUsers)


#Edit User Page
@app.route("/editUser/<userID>")
def editUserPage(userID):
    userToEdit = Users.query.get(userID)
    # Check if User is Admin, if so allow them access
    if "user_id" in session:
        thisUser = Users.query.get(session['user_id'])
        if thisUser.admin == True:
            return render_template('edituser.html', thisUser = thisUser, userToEdit = userToEdit)
        else:
            return redirect('/')
    else:
        testUser = Users.query.get(1) #TEST USER ID
        return render_template('edituser.html', thisUser = testUser, userToEdit = userToEdit)


#Update User POST Route
@app.route("/updateUser/<userID>", methods=["POST"])
def updateUser(userID):
    userToEdit = Users.query.get(userID)

    admin = request.form['admin']
    firstName = request.form['first_name']
    lastName = request.form['last_name']
    email = request.form['email']
    creator_name = request.form['creator_name']
    earnings_tips = request.form['earnings_tips']
    earnings_donations = request.form['earnings_donations']
    earnings_watcher_seconds = request.form['earnings_watcher_seconds']
    fb_user_id = request.form['fb_user_id'] # currently not working, do not use

    userToEdit.admin = admin == "True"
    userToEdit.first_name = firstName
    userToEdit.last_name = lastName
    userToEdit.email = email
    userToEdit.creator_name = creator_name
    userToEdit.earnings_tips = earnings_tips
    userToEdit.earnings_donations = earnings_donations
    userToEdit.earnings_watcher_seconds = earnings_watcher_seconds

    db.session.add(userToEdit)
    db.session.commit()


    return redirect("/admin")


#Delete User Route
@app.route("/deleteUser/<userID>")
def deleteUser(userID):
    if "user_id" in session:
        thisUser = Users.query.get(session['user_id'])    #will need to check what it's actually called in session
    else:
        thisUser = Users.query.get(1) #TEST USER
    userToEdit = Users.query.get(userID)
    if thisUser.admin == True:   #make sure person trying to delete this User is an admin
        db.session.delete(userToEdit)
        db.session.commit()
        return redirect("/admin")
    else:
        return redirect("/")

# LOGOUT
@app.route('/logout', methods=['POST','GET'])
def logout():
    session.clear()
    return redirect('/')

# if __name__ == "__main__":
#     app.run(debug=True, ssl_context='adhoc')

if __name__ == "__main__":
    app.run(debug=True)
