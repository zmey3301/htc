from app import db


class Categories(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    spending = db.relation("Spending", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"


class Spending(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime)
    month = db.Column(db.String, index=True)

    def __repr__(self):
        return f"<Spending with amount {self.amount} on {self.date}>"


class CustomPeriods(db.Model):
    id = db.Column(db.String(7), primary_key=True)
    limit = db.Column(db.Float)

    def __repr__(self):
        return f"<CustomPeriod with limit {self.limit} 4 {self.id}>"
