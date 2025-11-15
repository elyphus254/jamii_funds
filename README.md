# Jamii Funds 💰👥

**Empower communities with transparent group savings & lending.**

> A mobile-first web app for *chamas* (Kenyan savings groups) to track contributions, loans, and payouts — built with love in Kenya.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![GitHub last commit](https://img.shields.io/github/last-commit/elyphus254/jamii_funds)
![Country](https://img.shields.io/badge/Country-Kenya-green)

---

## 📸 Screenshot (Add later)
![App Preview](./assets/screenshot.png)  
*Coming soon: Real-time contribution dashboard*

---

## ✨ Features
- [x] Member registration & profiles  
- [ ] Weekly/monthly contribution tracking  
- [ ] Loan requests & approvals  
- [ ] Automated payout scheduling  
- [ ] SMS alerts via Africa's Talking  
- [ ] USSD fallback (*#123#) for feature phones  

---

## 🛠 Tech Stack
| Layer       | Technology                  |
|------------|-----------------------------|
| Frontend   | HTML, CSS, JavaScript (Vanilla / React?) |
| Backend    | Node.js / Python (FastAPI)  |
| Database   | SQLite (dev) → PostgreSQL   |
| Hosting    | Vercel / Render / AWS       |
| SMS        | [Africa's Talking](https://africastalking.com) |

---

## 🚀 Quick Start (For Developers)

### 1. Clone the repo
```bash
git clone https://github.com/elyphus254/jamii_funds.git
cd jamii_funds

---

## Step-by-Step: Add This to Your Repo (VS Studio)

### 1. In Visual Studio
1. Open your `jamii_funds` project  
2. Right-click solution → **Open Folder in File Explorer**  
3. Create new file: `README.md`  
4. Paste the template above  
5. Edit:
   - Replace placeholder text
   - Add real screenshot later (`/assets/screenshot.png`)
   - Update tech stack

### 2. Commit & Push
```bash
git add README.md
git commit -m "Add professional README with Kenyan context"
git push
# Jamii Funds

A Django-based REST API for managing Kenyan Chama (savings groups) with M-Pesa integration. Handles contributions, loans, repayments, and more.

## Features
- **Chama Management**: Create groups, add members, track contributions.
- **Loans & Repayments**: Apply, approve, and repay with EMI calculations.
- **M-Pesa C2B**: STK Push for payments + webhook for confirmations.
- **Permissions**: Role-based (members vs. admins).
- **API Docs**: Auto-generated with DRF browsable API.

## Tech Stack
- Backend: Django 4.2+, DRF
- DB: PostgreSQL (recommended) or SQLite
- Payments: Safaricom Daraja API
- Tests: 100% coverage with pytest/factory-boy

## Quick Start
1. Clone: `git clone https://github.com/elyphus254/jamii_funds.git`
2. Install: `pip install -r requirements.txt`
3. Migrate: `python manage.py migrate`
4. Run: `python manage.py runserver`
5. API: `http://127.0.0.1:8000/api/`

### M-Pesa Setup
- Register on [Safaricom Daraja](https://developer.safaricom.co.ke).
- Add `CONSUMER_KEY` and `CONSUMER_SECRET` to `.env`.
- Test webhook: POST to `/api/mpesa/c2b/`.

## Endpoints
- `/api/chamas/` – List/create Chamas
- `/api/loans/{id}/approve/` – Approve loan (admin only)
- Full docs at `/api/` (browsable).

## Testing
`python manage.py test`

## Deployment
- Heroku/DigitalOcean with Gunicorn + Nginx.
- Env vars: `DEBUG=False`, `SECRET_KEY=...`

Built with ❤️ for Kenyan hustlers. Contributions welcome!
