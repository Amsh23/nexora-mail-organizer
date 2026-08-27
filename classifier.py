import re


RULES = {
    "finance": [
        "invoice",
        "receipt",
        "payment",
        "bill",
        "billing",
        "bank",
        "transaction",
        "فاکتور",
        "پرداخت",
    ],

    "orders": [
        "order",
        "shipping",
        "shipped",
        "delivery",
        "tracking",
        "purchase",
        "سفارش",
        "ارسال",
        "تحویل",
    ],

    "github": [
        "github",
        "pull request",
        "repository",
        "commit",
        "issue",
    ],

    "work": [
        "meeting",
        "project",
        "deadline",
        "work",
        "job",
        "company",
        "جلسه",
        "پروژه",
    ],

    "newsletter": [
        "newsletter",
        "unsubscribe",
        "weekly digest",
        "daily digest",
    ],
}


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def classify_email(sender: str, subject: str, body: str = "") -> str:

    text = normalize(
        f"{sender} {subject} {body}"
    )

    scores = {}

    for category, keywords in RULES.items():

        score = 0

        for keyword in keywords:

            if normalize(keyword) in text:
                score += 1

        scores[category] = score

    if not scores:
        return "other"

    best_category = max(
        scores,
        key=scores.get
    )

    if scores[best_category] == 0:
        return "other"

    return best_category