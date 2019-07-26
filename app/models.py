from app import db
from datetime import datetime
from pytz import timezone

Kyiv = timezone('Europe/Kiev')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500))
    amount = db.Column(db.Float)
    currency = db.Column(db.String(12))
    timestamp = db.Column(db.DateTime, default=datetime.now(tz=Kyiv))

    def __repr__(self):
        return '<description {}>'.format(self.description)


