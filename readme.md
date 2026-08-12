# Short-Term Rental Platform with AI Review Moderation

> A property rental API with built-in ML sentiment analysis that automatically flags negative guest reviews — helping hosts and admins respond faster and protect platform reputation.

[![Python](https://img.shields.io/badge/Python-3.11-blue)]()
[![Django](https://img.shields.io/badge/Django-5.x-green)]()
[![DRF](https://img.shields.io/badge/DRF-3.x-red)]()
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.x-orange)]()
[![F1](https://img.shields.io/badge/F1-1.00-brightgreen)]()
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green)]()

---

## Business Problem

Property rental platforms lose guest trust when negative experiences go unnoticed — slow host response and unmoderated complaints directly increase churn and lower ratings. Manual moderation of thousands of daily reviews is expensive and inconsistent. This platform provides a full-featured rental API (listings, bookings, favorites, roles) and automatically classifies every review as positive or negative at the moment it's displayed, enabling instant escalation without extra staff.

---

## Project Structure

```
ml_AirBNB_Comments_drf/
├── .gitignore
├── readme.md
├── requirements.txt
└── AirBNB_Comments_drf/
    ├── .env
    ├── AirBNB_comments.ipynb           # ML training notebook
    ├── Dockerfile
    ├── docker-compose.yml
    ├── manage.py
    ├── airbnb_comments.csv             # 5,000-row Russian review corpus
    ├── model_nb_airbnb_comments.pkl    # deployed model (MultinomialNB)
    ├── vector_airbnb_comments.pkl      # fitted CountVectorizer
    ├── airbnb/                         # Django project settings
    ├── my_app/
    │   ├── models.py                   # UserProfile, Property, Booking, Review, Favorite, Amenity
    │   ├── serializers.py              # ML inference lives in ReviewListSerializers.get_sentiment()
    │   ├── views.py
    │   ├── permissions.py              # IsOwner, IsGuest, CheckAdminRoleReviews (unused — see below)
    │   ├── filters.py
    │   └── translation.py              # EN/RU via modeltranslation
    ├── nginx/
    └── datasets/
        ├── AirBNB.docx
        └── movie_comments.csv
```

---

## Demo

**List properties:**
```bash
curl http://localhost/en/
```

**Create a booking (guest role required):**
```bash
curl -X POST http://localhost/en/booking_create/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"property": 1, "check_in": "2025-08-01T14:00:00", "check_out": "2025-08-05T12:00:00"}'
```

**Get property details with auto-classified reviews:**
```bash
curl http://localhost/en/1/
```

**Response excerpt** (actual field name from `ReviewListSerializers`):
```json
{
  "id": 1,
  "title": "Cozy studio in city center",
  "reviews": [
    {
      "rating": 2,
      "comment": "Соседи шумели всю ночь. Плохая звукоизоляция.",
      "sentiment": "negative"
    },
    {
      "rating": 5,
      "comment": "Обязательно приедем ещё раз. Просторная кухня!",
      "sentiment": "positive"
    }
  ]
}
```

> The field is `sentiment` and returns a plain string (`"positive"`/`"negative"`), not a list — `get_sentiment()` explicitly casts the model's numpy output with `str(...)`. The code comment next to it (`# переименовано: понятнее`) confirms this replaced an earlier, less clear field name.

**Swagger UI:** `http://localhost/en/api/docs/`

---

## Results (ML Sentiment Module)

| Metric | Score |
|---|---|
| Accuracy | 100% |
| F1-score | 1.00 |
| Precision | 1.00 |
| Recall | 1.00 |

*(997-row test set: 505 negative / 492 positive — both classes at 1.00 precision/recall/F1)*

**Model:** Multinomial Naive Bayes + `CountVectorizer` (bag-of-words, Russian stopwords removed via NLTK), 80/20 split.

> Perfect scores reflect a synthetically balanced, domain-specific Russian-language corpus (5,000 rows, exactly 2,500/2,500). Production performance on noisy, real-world reviews is expected to be meaningfully lower — treat this as a validated pipeline, not a production accuracy claim.

---

## Dataset (ML Module)

- **Source:** Custom Russian-language rental review corpus (`airbnb_comments.csv`)
- **Size:** 5,000 records
- **Features:** 1 text column (`text`), 1 label column (`label`)
- **Class balance:** Perfectly balanced — 2,500 positive / 2,500 negative
- **Vectorized shape:** train `(3984, 466)`, test `(997, 466)` after `CountVectorizer` with stopword removal

---

## Approach

**Backend API:**
1. Domain models: `UserProfile` (guest/owner roles), `Property`, `Booking`, `Review`, `Favorite`, `Amenity`
2. JWT auth (register / login / logout with token blacklist)
3. Role-based permissions (`IsOwner`, `IsGuest`)
4. Filtering, ordering, search, pagination via DRF + `django-filters`
5. `django-allauth` for GitHub/Google OAuth
6. `django-modeltranslation` for EN/RU property descriptions
7. Docker Compose (web + db + nginx)

**ML Sentiment Module:**
1. Loaded the Russian-language corpus, verified zero nulls
2. Removed Russian stopwords via NLTK
3. Vectorized with `CountVectorizer` (bag-of-words)
4. Trained `MultinomialNB` on an 80/20 split
5. Serialized model + vectorizer with `joblib`
6. Loaded both once at module level in `serializers.py`; called inline per-review in `ReviewListSerializers.get_sentiment()`

---

## Key Challenges & Solutions

**Integrating ML into the DRF serializer lifecycle**
Needed inference on every review without a separate endpoint → loaded `model_nb.pkl`/`vector.pkl` once at module level in `serializers.py` via `os.path.join(settings.BASE_DIR, ...)`, called from `get_sentiment()` → model loaded once at server startup, not per request.

**Secret key exposure in version control**
`SECRET_KEY` was a hardcoded risk → moved to `.env` with `python-dotenv`, added to `.gitignore` → no credentials in repo history.

**Static files not served in production**
Gunicorn doesn't serve static files → added `collectstatic` to the Docker startup command, configured Nginx to serve `/staticfiles/` and `/media/` volumes directly → eliminated 404s on assets.

---

## Known Gaps (worth fixing before calling this "production-ready")

- `CheckAdminRoleReviews` is defined in `permissions.py` but never referenced in `views.py` — either wire it into `ReviewCreateAPIView`/`ReviewListSerializers` or remove it
- `settings.py` has `DEBUG = True` hardcoded — should read from `.env` alongside `SECRET_KEY`
- No dedicated test coverage visible for `get_sentiment()` itself (only the empty `tests.py` scaffold)

---

## Tech Stack

| Category | Tools |
|---|---|
| Language | Python 3.11 |
| Backend | Django 5, Django REST Framework |
| ML | scikit-learn (MultinomialNB), NLTK, joblib |
| Auth | JWT (SimpleJWT), django-allauth (GitHub/Google) |
| Database | PostgreSQL (prod), SQLite (dev) |
| Deploy | Docker Compose, Gunicorn, Nginx |
| Filtering | django-filters, DRF OrderingFilter/SearchFilter |
| i18n | django-modeltranslation (EN/RU) |
| API Docs | drf-spectacular (Swagger UI) |

---

## How to Run

```bash
git clone https://github.com/your-username/rental-platform
cd rental-platform
cp .env.example .env   # add your SECRET_KEY
```

```bash
docker-compose up --build
# migrations run automatically on container start
```

```bash
docker-compose exec web python manage.py createsuperuser   # optional
```

API: `http://localhost/en/` · Swagger: `http://localhost/en/api/docs/`

---

## Deployment

| Service | Role |
|---|---|
| `web` | Django + Gunicorn on port 8000 |
| `db` | PostgreSQL with persistent volume |
| `nginx` | Reverse proxy on port 80, serves static/media |

Startup sequence: `collectstatic → makemigrations → migrate → gunicorn`

---

## Business Impact

- ↑ Faster identification of negative guest experiences vs. manually reading every review (estimated)
- ↓ Lower moderation staff time by auto-flagging negative reviews at display time (estimated)
- ↑ Host response rate improves when negative signals surface immediately in the review feed
- ↑ Platform scales to more listings without proportional moderation cost, since flagging is automated
- ↓ Guest churn risk reduced by enabling faster host-side escalation on complaints (estimated)

---

[//]: # (## Author)

[//]: # ()
[//]: # ([Your Name] — [LinkedIn]&#40;#&#41; | [GitHub]&#40;#&#41;)