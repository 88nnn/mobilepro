from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from usage_DB import User, Product, Purchase

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recommendations.db'
db = SQLAlchemy(app)

# API to fetch usage details
@app.route('/api/usage/<int:user_id>', methods=['GET'])
def get_usage_details(user_id):
    purchases = Purchase.query.filter_by(user_id=user_id).all()
    usage_details = []
    total_cost = 0

    for purchase in purchases:
        product = Product.query.get(purchase.product_id)
        if product:
            cost = (product.price_per_minute / 60) * purchase.duration_seconds
            total_cost += cost
            usage_details.append({
                "product_name": product.name,
                "duration_seconds": purchase.duration_seconds,
                "cost": round(cost)
            })

    return jsonify({
        "usage_details": usage_details,
        "total_cost": round(total_cost)
    })

# API to save purchase
@app.route('/api/save_purchase', methods=['POST'])
def save_purchase():
    try:
        data = request.json
        user_id = data.get('user_id')
        product_id = data.get('product_id')

        if not user_id or not product_id:
            return jsonify({'error': 'Missing user_id or product_id'}), 400

        # Check if the purchase is a repeat
        is_repeat = Purchase.query.filter_by(user_id=user_id, product_id=product_id).count() > 0

        # Save the purchase to the database
        new_purchase = Purchase(user_id=user_id, product_id=product_id, is_repeat=is_repeat)
        db.session.add(new_purchase)
        db.session.commit()

        # Update purchase_count and repurchase_count
        product = Product.query.get(product_id)
        if product:
            product.purchase_count += 1
            if is_repeat:
                product.repurchase_count += 1
            db.session.commit()

        return jsonify({'message': 'Purchase saved successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)