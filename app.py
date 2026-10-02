
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "learn-loop-dev-secret-change-me")
DB = os.environ.get("DATABASE_PATH", "learn_loop.db")

SKILLS = [
    ("Python", "Coding & Technology", "🐍"),
    ("Baking & Culinary", "Food & Creativity", "🍰"),
    ("Video Editing", "Media & Design", "🎬"),
    ("Photography", "Arts & Media", "📷"),
    ("Public Speaking", "Communication", "🎤"),
    ("Calligraphy", "Arts & Creativity", "✒️"),
]

TUTORS = [
    ("Aarav Mehta", "Python", "3+ years teaching Python, automation and beginner programming.", "aarav@learnloop.demo", "₹399 / session", "A"),
    ("Maya Kulkarni", "Baking & Culinary", "Home baker specialising in breads, desserts and plated basics.", "maya@learnloop.demo", "₹499 / session", "M"),
    ("Riya Shah", "Video Editing", "Reels, short-form content, Premiere Pro and storytelling.", "riya@learnloop.demo", "₹449 / session", "R"),
    ("Kabir Rao", "Photography", "Portrait, mobile and street photography with practical projects.", "kabir@learnloop.demo", "₹399 / session", "K"),
    ("Ananya Joshi", "Public Speaking", "Presentation confidence, speeches, interviews and storytelling.", "ananya@learnloop.demo", "₹349 / session", "A"),
    ("Vihaan Patil", "Calligraphy", "Modern calligraphy, lettering and creative journaling.", "vihaan@learnloop.demo", "₹299 / session", "V"),
]

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        teach TEXT DEFAULT '',
        learn TEXT DEFAULT '',
        bio TEXT DEFAULT '',
        verified INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS tutors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        skill TEXT NOT NULL,
        bio TEXT NOT NULL,
        email TEXT NOT NULL,
        price TEXT NOT NULL,
        initial TEXT NOT NULL,
        verified INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        skill TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        UNIQUE(sender_id, receiver_id, skill)
    );
    """)
    for tutor in TUTORS:
        exists = c.execute("SELECT id FROM tutors WHERE email=?", (tutor[3],)).fetchone()
        if not exists:
            c.execute(
                "INSERT INTO tutors (name,skill,bio,email,price,initial,verified) VALUES (?,?,?,?,?,?,1)",
                tutor
            )
    c.commit()
    c.close()
    init_db()

@app.context_processor
def inject():
    return {"skills": SKILLS}

@app.route("/")
def home():
    c = db()
    tutors = c.execute("SELECT * FROM tutors WHERE verified=1 ORDER BY id").fetchall()
    c.close()
    return render_template("index.html", tutors=tutors)

@app.route("/skills")
def skills_page():
    c = db()
    tutors = c.execute("SELECT * FROM tutors WHERE verified=1 ORDER BY skill").fetchall()
    c.close()
    return render_template("skills.html", tutors=tutors)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        c = db()
        u = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        c.close()
        if u and check_password_hash(u["password"], password):
            session["user_id"] = u["id"]
            return redirect(url_for("dashboard"))
        flash("Email or password is incorrect.")
    return render_template("login.html")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if len(password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for("signup"))
        c = db()
        try:
            c.execute(
                "INSERT INTO users (name,email,password) VALUES (?,?,?)",
                (name,email,generate_password_hash(password))
            )
            c.commit()
        except sqlite3.IntegrityError:
            c.close()
            flash("That email is already registered.")
            return redirect(url_for("signup"))
        c.close()
        flash("Welcome to LEARN LOOP! Complete your profile to start exchanging skills.")
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/profile", methods=["GET","POST"])
def profile():
    if "user_id" not in session: return redirect(url_for("login"))
    c = db()
    if request.method == "POST":
        c.execute(
            "UPDATE users SET teach=?, learn=?, bio=? WHERE id=?",
            (request.form.get("teach",""), request.form.get("learn",""), request.form.get("bio",""), session["user_id"])
        )
        c.commit()
        flash("Profile saved.")
    user = c.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    c.close()
    return render_template("profile.html", user=user)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session: return redirect(url_for("login"))
    c = db()
    user = c.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    incoming = c.execute("""
        SELECT x.*, u.name AS sender_name FROM connections x
        JOIN users u ON u.id=x.sender_id
        WHERE x.receiver_id=? ORDER BY x.id DESC
    """, (session["user_id"],)).fetchall()
    outgoing = c.execute("""
        SELECT x.*, u.name AS receiver_name FROM connections x
        JOIN users u ON u.id=x.receiver_id
        WHERE x.sender_id=? ORDER BY x.id DESC
    """, (session["user_id"],)).fetchall()
    c.close()
    return render_template("dashboard.html", user=user, incoming=incoming, outgoing=outgoing)

@app.route("/discover")
def discover():
    if "user_id" not in session: return redirect(url_for("login"))
    q = request.args.get("q","").strip()
    c = db()
    if q:
        like = f"%{q}%"
        users = c.execute("""
            SELECT * FROM users WHERE id != ? AND
            (name LIKE ? OR teach LIKE ? OR learn LIKE ? OR bio LIKE ?)
            ORDER BY name
        """, (session["user_id"], like, like, like, like)).fetchall()
    else:
        users = c.execute("SELECT * FROM users WHERE id != ? ORDER BY name", (session["user_id"],)).fetchall()
    c.close()
    return render_template("discover.html", users=users, q=q)

@app.route("/connect/<int:user_id>", methods=["POST"])
def connect(user_id):
    if "user_id" not in session: return redirect(url_for("login"))
    skill = request.form.get("skill","Skill exchange")
    if user_id == session["user_id"]:
        flash("You can't connect with your own profile.")
        return redirect(url_for("discover"))
    c = db()
    try:
        c.execute(
            "INSERT INTO connections (sender_id,receiver_id,skill) VALUES (?,?,?)",
            (session["user_id"], user_id, skill)
        )
        c.commit()
        flash("Connection request sent — user-to-user exchanges are free.")
    except sqlite3.IntegrityError:
        flash("You already sent this request.")
    c.close()
    return redirect(url_for("discover"))

@app.route("/connection/<int:connection_id>/<action>")
def connection_action(connection_id, action):
    if "user_id" not in session: return redirect(url_for("login"))
    status = "Accepted" if action == "accept" else "Declined"
    c = db()
    c.execute(
        "UPDATE connections SET status=? WHERE id=? AND receiver_id=?",
        (status, connection_id, session["user_id"])
    )
    c.commit(); c.close()
    return redirect(url_for("dashboard"))

@app.route("/tutor/<int:tutor_id>")
def tutor(tutor_id):
    c = db()
    t = c.execute("SELECT * FROM tutors WHERE id=? AND verified=1", (tutor_id,)).fetchone()
    c.close()
    if not t: return redirect(url_for("skills_page"))
    return render_template("tutor.html", tutor=t)

@app.route("/pay/<int:tutor_id>", methods=["GET","POST"])
def pay(tutor_id):
    c = db()
    t = c.execute("SELECT * FROM tutors WHERE id=? AND verified=1", (tutor_id,)).fetchone()
    c.close()
    if not t: return redirect(url_for("skills_page"))
    # Demo payment flow. For live payments, connect Stripe/Razorpay keys in Render.
    if request.method == "POST":
        flash(f"Payment demo completed for {t['name']}. Add a payment gateway to accept real payments.")
        return redirect(url_for("tutor", tutor_id=tutor_id))
    return render_template("payment.html", tutor=t)

@app.route("/search")
def search():
    q = request.args.get("q","").strip()
    if not q:
        return redirect(url_for("skills_page"))
    c = db()
    like = f"%{q}%"
    tutors = c.execute("""
        SELECT * FROM tutors WHERE verified=1 AND
        (skill LIKE ? OR name LIKE ? OR bio LIKE ?)
        ORDER BY skill
    """, (like,like,like)).fetchall()
    users = c.execute("""
        SELECT * FROM users WHERE teach LIKE ? OR name LIKE ? OR bio LIKE ?
        ORDER BY name
    """, (like,like,like)).fetchall()
    c.close()
    return render_template("search.html", q=q, tutors=tutors, users=users)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
