from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import jsonify
from sqlalchemy import func
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenseDB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    cost_type =  db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Expense {self.name}>'

def calculate_total_expense():
    total_expense = db.session.query(db.func.sum(Expense.amount)).scalar()
    return total_expense or 0.0

@app.route('/')
def home():
    expenses = Expense.query.all()
    total_expense = calculate_total_expense()
    return render_template('index.html', expenses=expenses, total_expense=total_expense)



@app.route('/add', methods=['POST'])
def add_expense():
    name = request.form['name']
    amount = request.form['amount']
    cost_type = request.form['cost_type']
    date = datetime.strptime(request.form['date'], '%Y-%m-%d')
    new_expense = Expense(name=name, amount=float(amount), date=date, cost_type = cost_type)

    try:
        db.session.add(new_expense)
        db.session.commit()
        return redirect('/')
    except Exception as e:
        return f"An error occurred while adding the expense: {e}"

@app.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    expense_to_delete = Expense.query.get_or_404(id)

    try:
        db.session.delete(expense_to_delete)
        db.session.commit()
        return redirect('/')
    except Exception as e:
        return f"An error occurred while deleting the expense: {e}"

@app.route('/clear', methods=['POST'])
def clear_database():
    try:
        db.session.query(Expense).delete()
        db.session.commit()
        return redirect('/')
    except Exception as e:
        return f"An error occurred while clearing the database: {e}"
    

@app.route('/graphs')
def graphs():
    expenses = Expense.query.all()

    # Prepare data for the pie chart
    cost_type_totals = {}
    for expense in expenses:
        if expense.cost_type in cost_type_totals:
            cost_type_totals[expense.cost_type] += expense.amount
        else:
            cost_type_totals[expense.cost_type] = expense.amount

    labels = list(cost_type_totals.keys())
    amounts = list(cost_type_totals.values())

  
    return render_template('graphs.html', labels=labels, amounts=amounts)

@app.route('/line')
def line():
    time_unit = request.args.get('time_unit', 'day')  # Default to 'day' if not provided

    expenses = Expense.query.all()

    # Find the earliest and latest dates in the expenses
    start_date = min(expense.date for expense in expenses).date()
    end_date = max(expense.date for expense in expenses).date()
    date_format = '%Y-%m-%d'
    total_expenses_labels = []
    total_expenses_amounts = []

    current_date = start_date
    cumulative_total = 0

    while current_date <= end_date:
        if time_unit == 'day':
            next_date = current_date + timedelta(days=1)
        elif time_unit == 'week':
            next_date = current_date + timedelta(weeks=1)
        elif time_unit == 'month':
            next_date = current_date + relativedelta(months=1)
        else:
            next_date = current_date + timedelta(days=1)  # Fallback to day

        total_amount = sum(expense.amount for expense in expenses if current_date <= expense.date.date() < next_date)
        cumulative_total += total_amount
        
        total_expenses_labels.append(current_date.strftime(date_format))
        total_expenses_amounts.append(cumulative_total)

        current_date = next_date

    return render_template('line.html', total_expenses_labels=total_expenses_labels, total_expenses_amounts=total_expenses_amounts)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
