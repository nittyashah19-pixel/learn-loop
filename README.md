# LEARN LOOP — Skill Exchange Platform

A polished Flask starter for the LEARN LOOP college project.

## Included
- Aesthetic pink + green visual system with a small neutral palette
- Creative text/SVG-style loop logo made in CSS/HTML (no external image required)
- Home page, skills directory, verified tutor profiles
- Six featured skills: Python, Baking & Culinary, Video Editing, Photography, Public Speaking, Calligraphy
- Login and signup
- User profiles with skills they teach/want to learn
- Search for skills/tutors/community members
- User-to-user free connection requests
- Verified tutor paid-session flow (demo checkout)
- SQLite database and Render configuration

## Run locally
```bash
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Render
Create a Web Service from the GitHub repository.
Build command:
`pip install -r requirements.txt`
Start command:
`gunicorn app:app`

`render.yaml` also contains these settings.

## Real payments
The included `/pay/<tutor_id>` route is a safe demo checkout. For real money movement, integrate a payment provider such as Stripe or Razorpay and store the provider's secret key in Render Environment Variables. Never put payment secrets in frontend code or GitHub.
