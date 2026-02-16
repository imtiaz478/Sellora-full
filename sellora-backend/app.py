from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sellora.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(100), nullable=False)
    user_or_merchant = db.Column(db.String(100), nullable=False)
    product = db.Column(db.String(200), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    buy_date = db.Column(db.Date, nullable=False)
    sell_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    

@app.route("/api/transactions", methods=["POST"])
def create_transaction():
    data = request.get_json()
    
    try:
        new_transaction = Transaction(
            source=data["source"],
            user_or_merchant = data["user_or_merchant"],    
            product=data["product"],    
            total_price = data["total_price"],
            buy_date=datetime.strptime(data["buy_date"], "%Y-%m-%d"),
            sell_date=datetime.strptime(data["sell_date"], "%Y-%m-%d") if data.get("sell_date") else None
        )
        
        db.session.add(new_transaction)
        db.session.commit()
        
        return jsonify({"message": "Transaction created successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@app.route("/api/transactions", methods=["GET"])    
def get_transactions():
    transactions = Transaction.query.all()
    
    result = []
    
    for t in transactions:
        result.append({
            "id": t.id,
            "source": t.source,
            "user_or_merchant": t.user_or_merchant,
            "product": t.product,
            "total_price": t.total_price,
            "buy_date": t.buy_date.strftime("%Y-%m-%d"),
            "sell_date": t.sell_date.strftime("%Y-%m-%d") if t.sell_date else None
        })
    
    return jsonify(result)    
    
@app.route("/")
def home():
    return {"message": "Sellora Backend Running "}




if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)