from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import text, inspect
import os

# Initialize App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-change-in-production'

# Use absolute path for SQLite to avoid confusion
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'library.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Book(db.Model):
    __tablename__ = 'book' # Explicitly name table to match expectations
    
    id = db.Column(db.Integer, primary_key=True) # CRITICAL: Must have Primary Key
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    
    # New field for cover images
    image_url = db.Column(db.String(500), default='') 
    
    issued = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime, nullable=True)
    fine_per_day = db.Column(db.Integer, default=5)

    def is_overdue(self):
        return bool(self.issued and self.due_date and datetime.now() > self.due_date)

    def calculate_fine(self):
        if self.is_overdue():
            days_late = (datetime.now() - self.due_date).days
            return max(0, days_late * self.fine_per_day)
        return 0
    
    def get_display_image(self):
        """Returns user image or a generated placeholder based on title"""
        if self.image_url:
            return self.image_url
        
        # Generate a nice gray/blue placeholder using placehold.co
        # URL encode spaces for safety
        safe_title = self.title.replace(' ', '+')[:20] 
        return f"https://placehold.co/400x600/e2e8f0/1e293b?text={safe_title}"

# --- Database Migration Helper ---
def ensure_schema_up_to_date():
    """Checks if new columns exist in existing DB, adds them if missing."""
    inspector = inspect(db.engine)
    if 'book' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('book')]
        
        if 'image_url' not in columns:
            print("⚠️ Adding 'image_url' column to existing database...")
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE book ADD COLUMN image_url VARCHAR(500) DEFAULT ''"))
                    conn.commit()
                print("✅ Column added successfully.")
            except Exception as e:
                print(f"❌ Failed to add column: {e}")
    else:
        print("ℹ️ Table 'book' does not exist yet. Will be created by db.create_all().")

with app.app_context():
    # 1. Create tables if they don't exist
    db.create_all()
    # 2. Ensure schema matches latest model (adds missing columns like image_url)
    ensure_schema_up_to_date()

@app.route('/')
def index():
    filter_type = request.args.get('filter', 'all')
    search_query = request.args.get('search', '').strip()
    
    query = Book.query
    
    # Search Logic
    if search_query:
        pattern = f"%{search_query}%"
        from sqlalchemy import or_
        query = query.filter(or_(Book.title.ilike(pattern), Book.author.ilike(pattern)))
    
    # Filter Logic
    if filter_type == 'issued':
        query = query.filter_by(issued=True)
    elif filter_type == 'available':
        query = query.filter_by(issued=False)
    elif filter_type == 'overdue':
        # For SQLite date comparison reliability, we fetch issued books and check in Python
        all_books = Book.query.all()
        books = [b for b in all_books if b.is_overdue()]
        
        total = len(all_books)
        issued_count = sum(1 for b in all_books if b.issued)
        available_count = sum(1 for b in all_books if not b.issued)
        overdue_count = len(books)
        
        return render_template('index.html', books=books, current_filter='overdue', 
                               search_query=search_query, total=total, 
                               issued=issued_count, available=available_count, overdue=overdue_count)

    books = query.all()
    
    # Stats Calculation
    total = Book.query.count()
    issued_count = Book.query.filter_by(issued=True).count()
    available_count = Book.query.filter_by(issued=False).count()
    
    # Calculate overdue count accurately
    all_books_list = Book.query.all()
    overdue_count = sum(1 for b in all_books_list if b.is_overdue())

    return render_template('index.html', books=books, current_filter=filter_type,
                           search_query=search_query, total=total, 
                           issued=issued_count, available=available_count, overdue=overdue_count)

@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        image_url = request.form.get('image_url', '').strip()
        
        if not title or not author:
            flash("Title and Author are required.", "error")
            return redirect(url_for('add_book'))
            
        new_book = Book(title=title, author=author, image_url=image_url)
        db.session.add(new_book)
        db.session.commit()
        flash(f"'{title}' added successfully!", "success")
        return redirect(url_for('index'))
        
    return render_template('add.html')

@app.route('/issue/<int:id>', methods=['POST'])
def issue_book(id):
    book = db.session.get(Book, id)
    if not book:
        abort(404)
    
    if book.issued:
        flash("Book already issued.", "warning")
        return redirect(url_for('index'))

    try:
        days = int(request.form.get('days', 14))
        fine = int(request.form.get('fine_per_day', 5))
    except ValueError:
        flash("Invalid numbers.", "error")
        return redirect(url_for('index'))

    book.issued = True
    book.due_date = datetime.now() + timedelta(days=days)
    book.fine_per_day = fine
    db.session.commit()
    
    flash(f"Issued '{book.title}'. Due: {book.due_date.strftime('%d %b')}", "success")
    return redirect(url_for('index'))

@app.route('/return/<int:id>', methods=['POST'])
def return_book(id):
    book = db.session.get(Book, id)
    if not book:
        abort(404)
    
    if not book.issued:
        flash("Book was not issued.", "warning")
        return redirect(url_for('index'))

    book.issued = False
    book.due_date = None
    db.session.commit()
    flash(f"Returned '{book.title}'.", "info")
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete_book(id):
    book = db.session.get(Book, id)
    if not book:
        abort(404)
    
    title = book.title
    db.session.delete(book)
    db.session.commit()
    flash(f"Deleted '{title}'.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)