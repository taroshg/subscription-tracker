from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta, MO
from helper import login_required

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///subscription.db")

# bugs: next billing might be wrong since the app just adds 30 days

@app.route("/", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        subscription = request.form.get("subscription")
        recurrence = request.form.get("recurrence")
        payment = request.form.get("payment")

        # next billing date
        month = request.form.get("month")
        day = request.form.get("day")
        year = request.form.get("year")

        remove = request.form.get("remove")

        if subscription and recurrence and payment and month and day and year:

            billing_date = date(int(year), int(month), int(day))

            if is_valid_date(int(year), int(month), int(day)):
                if billing_date > datetime.now().date():
                    renewal = billing_date 
                    db.execute("INSERT INTO subscriptions "+
                            "(user_id, subscription, recurrence, payment, renewal) " +
                            "VALUES (?, ?, ?, ?, ?)", session["user_id"], subscription, 
                            recurrence, payment, renewal)
                    return redirect("/")
                else:
                    flash("The date that was given is in the past 🦖")
                    return redirect("/?error=date")
            else:
                flash("The date that was given is impossible 🤔")
                return redirect("/?error=date")

        elif remove:
            db.execute("DELETE FROM subscriptions WHERE subscription = ?",
            remove)
            return redirect("/")
        else:
            flash("Can't have any empty fields 📭")
            return redirect("/?error=empty")
        
    else:

        subscriptions = db.execute("SELECT * FROM subscriptions WHERE user_id = ?", 
        session["user_id"])

        # update the subscriptions
        for subscription in subscriptions:
            renewal = datetime.strptime(subscription["renewal"], '%Y-%m-%d').date()
            subscription_name = subscription["subscription"]
            recurrence = subscription["recurrence"]
            
            update_renewal_time(renewal, recurrence, subscription_name)

        # re-update and sort subsciptions

        if request.args.get("sort") in ["payment", "renewal", "recurrence"]:
            if request.args.get("sort") == "payment":
                subscriptions = db.execute(f"SELECT * FROM subscriptions WHERE user_id = ? ORDER BY {request.args.get('sort')} DESC", 
                session["user_id"])
            else:
                subscriptions = db.execute(f"SELECT * FROM subscriptions WHERE user_id = ? ORDER BY {request.args.get('sort')}", 
                session["user_id"])
        else: 
            subscriptions = db.execute("SELECT * FROM subscriptions WHERE user_id = ?", 
            session["user_id"])

        # get total spending
        total_spending = {
            "daily": 0,
            "weekly": 0,
            "monthly": 0,
            "yearly": 0
        }

        for subscription in subscriptions:

            renewal = datetime.strptime(subscription["renewal"], '%Y-%m-%d').date()
            subscription_name = subscription["subscription"]
            recurrence = subscription["recurrence"]

            now = (datetime.now()).date()
            # add more data
            subscription["days_left"] = (renewal - now).days
            subscription["year"] = renewal.year
            subscription["month"] = renewal.strftime("%b")
            subscription["day"] = renewal.day

            payment = subscription["payment"]

            # calculate and add subscriptions to the total spending
            spending_daily = payment / recurrence

            total_spending["daily"] += spending_daily
            total_spending["weekly"] += (spending_daily * 7)
            total_spending["monthly"] += (spending_daily * 30)
            total_spending["yearly"] += (spending_daily * 365)
        
        # round the spending to make it pretty
        total_spending["daily"] = round(total_spending["daily"], 2)
        total_spending["weekly"] = round(total_spending["weekly"], 2)
        total_spending["monthly"] = round(total_spending["monthly"], 2)
        total_spending["yearly"] = round(total_spending["yearly"], 2)

        # get username
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]

        # check if empty
        if len(subscriptions) < 1:
            empty = True
        else:
            empty = False

        return render_template("dashboard.html", subscriptions=subscriptions, 
        total=total_spending, username=username, empty=empty)


def update_renewal_time(renewal, recurrence, subscription):
    now = (datetime.now()).date()
    # check if the renewal date is past
    if now > renewal:
        if recurrence == 30: # check if its a monthly subscription
            new_renewal = renewal + relativedelta(months=1)
        elif recurrence == 7:  # check weekly subscription
            new_renewal = renewal + timedelta(weeks=1)
        else:
            new_renewal = renewal + timedelta(days=int(recurrence))
        db.execute("UPDATE subscriptions SET renewal= :new_renewal " +
            "WHERE user_id = :user_id AND subscription = :subscription ",
            user_id=session["user_id"], new_renewal=new_renewal,
            subscription=subscription)
        renewal = new_renewal
        update_renewal_time(renewal, recurrence, subscription)
    else:
        return True

@app.route("/register/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if username and password and confirm_password:

            users = db.execute("SELECT username FROM users")
            usernames = {user["username"] for user in users}
            if username not in usernames:

                if password == confirm_password:

                    hashed = generate_password_hash(password)
                    db.execute("INSERT INTO users (username, hash) VALUES(?, ?)",
                    username, hashed)
                    return redirect("/login/")

                else:
                    flash("The passwords don't match 😐")
                    return redirect("/register?error=passwords")
            else:
                flash("The user name already exists, sorry 😔")
                return redirect("/register?error=exists")
        else:
            flash("Can't have any empty fields 📭")
            return redirect("/register?error=empty")
    else:
        return render_template("register.html")


@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username and password:

            users = db.execute("SELECT * FROM users WHERE username=?", username)

            if len(users) == 1:
                user = db.execute("SELECT * FROM users WHERE username=?",
                username)
                if check_password_hash(user[0]["hash"], password):
                    session["user_id"] = users[0]["id"]
                    return redirect("/")
                else:
                    flash("Wrong password for the given username 😐")
                    return redirect("/login?error=password")
            else:
                flash("The user doesn't exist 😔")
                return redirect("/login?error=not_found")
        else:
            flash("Can't have any empty fields 📭")
            return redirect("/login?error=empty")
    else:
        return render_template("login.html")


@app.route("/logout/")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# https://stackoverflow.com/a/51981596
def is_valid_date(year, month, day):
    day_count_for_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if year%4==0 and (year%100 != 0 or year%400==0):
        day_count_for_month[2] = 29
    return (1 <= month <= 12 and 1 <= day <= day_count_for_month[month])

    
