from app import app, db

# Run inside application context
with app.app_context():
    db.create_all()
    print("✅ Tables created successfully in Neon PostgreSQL!")
