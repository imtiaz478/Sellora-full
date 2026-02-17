from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super-secret-key"
jwt = JWTManager(app)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sellora.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)



class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(100), nullable=False)
    user_or_merchant = db.Column(db.String(100), nullable=False)
    product = db.Column(db.String(200), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    buy_date = db.Column(db.Date, nullable=False)
    sell_date = db.Column(db.Date, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    

@app.route("/api/transactions", methods=["POST"])
def create_transaction():
    current_user_id = get_jwt_identity()
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
   


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    
    hashed_password = generate_password_hash(data["password"])
    
    new_user = User(
        username=data["username"],
        email=data["email"],
        password=hashed_password
    )
    
    db.session.add(new_user)    
    db.session.commit()
    
    return jsonify({"message": "User registered successfully"}), 201

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    
    user = User.query.filter_by(email=data["email"]).first()
    
    if not user or not check_password_hash(user.password, data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401
    
    access_token = create_access_token(identity=user.id)
    
    return jsonify({"token": access_token}) 
    



@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    current_user_id = get_jwt_identity()

    transactions = Transaction.query.filter_by(user_id=current_user_id).all()
    
    result = []
    for t in transactions:

        date_diff = None
        if t.sell_date:
            date_diff = (t.sell_date - t.buy_date).days

        result.append({
            "id": t.id,
            "source": t.source,
            "user_or_merchant": t.user_or_merchant,
            "product": t.product,
            "total_price": t.total_price,
            "buy_date": t.buy_date.strftime("%Y-%m-%d"),
            "sell_date": t.sell_date.strftime("%Y-%m-%d") if t.sell_date else None,
            "date_diff_days": date_diff
        })

    return jsonify(result)


@app.route("/api/transactions/<int:id>", methods=["DELETE"])
def delete_transaction(id):
    transaction = Transaction.query.get(id)
    
    if not transaction:
        return jsonify({"error": "Transaction not found"}), 404
    
    db.session.delete(transaction)
    db.session.commit()
    
    return jsonify({"message": "Transaction deleted successfully"}) 


@app.route("/api/transactions/<int:id>", methods=["PUT"])
def update_transaction(id):
    transaction = Transaction.query.get(id)
    
    if not transaction:
        return jsonify({"error": "Transaction not found"}), 404
    
    data = request.get_json()
    try:
        transaction.source = data.get("source", transaction.source)
        transaction.user_or_merchant = data.get("user_or_merchant", transaction.user_or_merchant)
        transaction.product = data.get("product", transaction.product)
        transaction.total_price = data.get("total_price", transaction.total_price)
        
        if data.get("buy_date"):
            transaction.buy_date = datetime.strptime(data["buy_date"], "%Y-%m-%d")
        
        if data.get("sell_date"):
            transaction.sell_date = datetime.strptime(data["sell_date"], "%Y-%m-%d")
        
        db.session.commit()
        
        return jsonify({"message": "Transaction updated successfully"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    
@app.route("/")
def home():
    return {"message": "Sellora Backend Running "}




if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)