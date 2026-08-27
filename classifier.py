import re

RULES = {
    "finance": ["invoice", "receipt", "payment", "bill", "billing", "bank", "transaction", "statement", "فاکتور", "پرداخت"],
    "orders": ["order", "shipping", "shipped", "delivery", "tracking", "purchase", "سفارش", "ارسال", "تحویل"],
    "github": ["github", "pull request", "repository", "commit", "issue", "dependabot"],
    "work": ["meeting", "project", "deadline", "work", "job", "company", "جلسه", "پروژه"],
    "education": ["school", "university", "course", "class", "assignment", "student", "teacher", "education"],
    "newsletter": ["newsletter", "unsubscribe", "weekly digest", "daily digest"],
}


def normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def classify_email(sender: str, subject: str, body: str = "", attachment_filenames=None) -> str:
    attachment_filenames = attachment_filenames or []
    text = normalize(f"{sender} {subject} {body} {' '.join(attachment_filenames)}")
    scores = {}
    for category, keywords in RULES.items():
        scores[category] = sum(1 for keyword in keywords if normalize(keyword) in text)
    best_category = max(scores, key=scores.get) if scores else "other"
    return best_category if scores.get(best_category, 0) else "other"
