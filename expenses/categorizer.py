"""Keyword based category prediction.

Each category has a list of keywords. A description is split into words and the
category with the most keyword hits wins. To improve it later, replace
``predict_category`` with an NLP / ML model - the rest of the app only calls
this one function.
"""
import re

CATEGORY_KEYWORDS = {
    'Food': [
        'pizza', 'burger', 'biryani', 'lunch', 'dinner', 'breakfast', 'snack', 'snacks',
        'coffee', 'tea', 'restaurant', 'cafe', 'swiggy', 'zomato', 'dominos', 'kfc',
        'mcdonalds', 'grocery', 'groceries', 'vegetables', 'fruits', 'milk', 'bakery',
        'juice', 'food', 'meal', 'dosa', 'idli', 'icecream', 'chocolate',
    ],
    'Travel': [
        'uber', 'ola', 'rapido', 'taxi', 'cab', 'auto', 'bus', 'train', 'metro', 'flight',
        'petrol', 'diesel', 'fuel', 'toll', 'parking', 'irctc', 'redbus', 'ticket',
        'airport', 'travel', 'trip', 'hotel',
    ],
    'Shopping': [
        'amazon', 'flipkart', 'myntra', 'shirt', 'jeans', 'shoes', 'dress', 'clothes',
        'watch', 'bag', 'mall', 'shopping', 'gift', 'headphones', 'earphones', 'phone',
        'laptop', 'charger',
    ],
    'Bills': [
        'electricity', 'water', 'wifi', 'internet', 'broadband', 'recharge', 'rent',
        'gas', 'bill', 'insurance', 'emi', 'loan', 'airtel', 'jio', 'postpaid',
        'subscription', 'maintenance',
    ],
    'Entertainment': [
        'movie', 'netflix', 'spotify', 'hotstar', 'prime', 'youtube', 'concert', 'game',
        'games', 'gaming', 'steam', 'playstation', 'cinema', 'pvr', 'bookmyshow', 'party',
    ],
    'Health': [
        'doctor', 'medicine', 'medicines', 'pharmacy', 'hospital', 'clinic', 'dentist',
        'gym', 'checkup', 'tablets', 'apollo', 'medplus', 'lab', 'therapy',
    ],
    'Education': [
        'book', 'books', 'course', 'udemy', 'coursera', 'tuition', 'fees', 'fee', 'exam',
        'stationery', 'pen', 'notebook', 'college', 'certification', 'workshop',
    ],
}

DEFAULT_CATEGORY = 'Other'


def predict_category(description):
    words = re.findall(r'[a-z0-9]+', (description or '').lower())
    if not words:
        return DEFAULT_CATEGORY
    word_set = set(words)

    best_category, best_score = DEFAULT_CATEGORY, 0
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for k in keywords if k in word_set)
        if score > best_score:
            best_category, best_score = category, score
    return best_category
