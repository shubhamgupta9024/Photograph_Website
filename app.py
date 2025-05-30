from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Neon DB Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_v0uxLU7CeoDt@ep-cold-term-a8gmm3bc-pooler.eastus2.azure.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CATEGORIES = {
    'films': ['.mp4', '.mov', '.avi'],
    'projects': ['.mp4', '.mov', '.avi'],
    'stills': ['.jpg', '.jpeg', '.png'],
    'artworks': ['.jpg', '.jpeg', '.png']
}

# Create category folders
for category in CATEGORIES:
    os.makedirs(os.path.join(UPLOAD_FOLDER, category), exist_ok=True)


class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    upload_time = db.Column(db.DateTime, server_default=db.func.now())

def get_media_files(exclude_still=None):
    media = {category: [] for category in CATEGORIES}
    for category, extensions in CATEGORIES.items():
        folder = os.path.join(UPLOAD_FOLDER, category)
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if f.lower().endswith(tuple(extensions))]
            if category == 'stills' and exclude_still:
                files = [f for f in files if f != exclude_still]
            media[category] = [url_for('static', filename=f'uploads/{category}/{f}') for f in files]
    return media

def get_related_images(image_name):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], 'stills')
    all_images = [f for f in os.listdir(folder) if f.lower().endswith(tuple(CATEGORIES['stills']))]
    image_base = os.path.splitext(image_name)[0].lower()

    related = [
        url_for('static', filename=f'uploads/stills/{img}')
        for img in all_images
        if image_base in os.path.splitext(img)[0].lower() and img != image_name
    ]

    if not related:
        all_images.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
        related = [
            url_for('static', filename=f'uploads/stills/{img}')
            for img in all_images if img != image_name
        ][:6]

    return related

@app.route('/')
def home():
    return redirect(url_for('stills'))

@app.route('/films')
def films():
    return render_template('films.html', media=get_media_files())

@app.route('/projects')
def projects():
    return render_template('projects.html', media=get_media_files())

@app.route('/stills')
def stills():
    media = get_media_files()
    media['stills'] = [img for img in media['stills'] if 'related' not in os.path.basename(img).lower()]
    return render_template('stills.html', media=media)

@app.route('/artworks')
def artworks():
    return render_template('artworks.html', media=get_media_files())

@app.route('/stills/<image_name>')
def view_image(image_name):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], 'stills')
    file_path = os.path.join(folder, secure_filename(image_name))

    if not os.path.isfile(file_path):
        abort(404)

    # Get all still images including related ones
    all_images = [
        f for f in os.listdir(folder)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]

    return render_template(
        'view_image.html',
        image_name=image_name,
        all_stills=all_images  # no 'related' filtering
    )


@app.route('/admin-xyz123', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('admin_logged_in'):
        flash("Please login as admin to access this page.", "error")
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        category = request.form.get('category')
        file = request.files.get('file')
        base_image = request.form.get('base_image')

        if not category or category not in CATEGORIES:
            flash("Invalid category selected!", "error")
            return redirect(url_for('admin_panel'))

        if not file or file.filename == '':
            flash("No file selected!", "error")
            return redirect(url_for('admin_panel'))

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in CATEGORIES[category]:
            flash("Invalid file format!", "error")
            return redirect(url_for('admin_panel'))

        original_filename = secure_filename(file.filename)

        if category == 'stills' and base_image:
            base_name, _ = os.path.splitext(secure_filename(base_image))
            filename = f"{base_name}related_{original_filename}"
        else:
            filename = original_filename

        save_path = os.path.join(app.config['UPLOAD_FOLDER'], category, filename)
        counter = 1
        while os.path.exists(save_path):
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{counter}{ext}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], category, filename)
            counter += 1

        file.save(save_path)

        new_file = UploadedFile(filename=filename, category=category)
        db.session.add(new_file)
        db.session.commit()

        flash("File uploaded successfully!", "success")
        return redirect(url_for('admin_panel'))

    still_images = [
        f for f in os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], 'stills')) if 'related' not in f
    ]

    return render_template('admin.html', media=get_media_files(), still_images=still_images)

@app.route('/delete-file/<category>/<filename>', methods=['POST'])
def delete_file(category, filename):
    if not session.get('admin_logged_in'):
        flash("Unauthorized access!", "error")
        return redirect(url_for('admin_login'))

    if category not in CATEGORIES:
        flash("Invalid category!", "error")
        return redirect(url_for('admin_panel'))

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], category, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash("File deleted successfully!", "success")
        file_entry = UploadedFile.query.filter_by(filename=filename, category=category).first()
        if file_entry:
            db.session.delete(file_entry)
            db.session.commit()
    else:
        flash("File not found!", "error")

    return redirect(url_for('admin_panel'))

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == "admin" and password == "admin123":
            session['admin_logged_in'] = True
            flash("Logged in as admin.", "success")
            return redirect(url_for('admin_panel'))
        else:
            flash("Invalid credentials!", "error")
            return redirect(url_for('admin_login'))

    return render_template('admin.html')

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))

@app.template_filter('replace_extension')
def replace_extension(filename):
    return os.path.splitext(filename)[0]

if __name__ == '__main__':
    app.run(debug=True)












# from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
# from flask_sqlalchemy import SQLAlchemy
# from werkzeug.utils import secure_filename
# import os 

# app = Flask(__name__)
# app.secret_key = "your_secret_key"

# # Configure your Neon DB connection string
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_v0uxLU7CeoDt@ep-cold-term-a8gmm3bc-pooler.eastus2.azure.neon.tech/neondb?sslmode=require'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(app)

# UPLOAD_FOLDER = 'static/uploads'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# CATEGORIES = {
#     'films': ['.mp4', '.mov', '.avi'],
#     'projects': ['.mp4', '.mov', '.avi'],
#     'stills': ['.jpg', '.jpeg', '.png'],
#     'artworks': ['.jpg', '.jpeg', '.png']
# }

# # Ensure category folders exist
# for category in CATEGORIES:
#     os.makedirs(os.path.join(UPLOAD_FOLDER, category), exist_ok=True)


# # Database Model
# class UploadedFile(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     filename = db.Column(db.String(255), nullable=False)
#     category = db.Column(db.String(50), nullable=False)
#     upload_time = db.Column(db.DateTime, server_default=db.func.now())

#     def __repr__(self):
#         return f"<UploadedFile {self.filename}>"


# # Helper functions
# def get_media_files(exclude_still=None):
#     media = {category: [] for category in CATEGORIES}
#     for category, extensions in CATEGORIES.items():
#         folder = os.path.join(UPLOAD_FOLDER, category)
#         if os.path.exists(folder):
#             files = [f for f in os.listdir(folder) if f.lower().endswith(tuple(extensions))]

#             if category == 'stills' and exclude_still:
#                 files = [f for f in files if f != exclude_still]

#             media[category] = [url_for('static', filename=f'uploads/{category}/{f}') for f in files]
#     return media


# def get_related_images(image_name):
#     folder = os.path.join(app.config['UPLOAD_FOLDER'], 'stills')
#     all_images = [f for f in os.listdir(folder) if f.lower().endswith(tuple(CATEGORIES['stills']))]
#     image_base = os.path.splitext(image_name)[0].lower()

#     related = [
#         url_for('static', filename=f'uploads/stills/{img}')
#         for img in all_images
#         if image_base in os.path.splitext(img)[0].lower() and img != image_name
#     ]

#     if not related:
#         all_images.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
#         related = [
#             url_for('static', filename=f'uploads/stills/{img}')
#             for img in all_images if img != image_name
#         ][:6]

#     return related


# # Routes


# @app.route('/')
# def home():
#     return redirect(url_for('stills'))



# @app.route('/films')
# def films():
#     return render_template('films.html', media=get_media_files())


# @app.route('/projects')
# def projects():
#     return render_template('projects.html', media=get_media_files())


# @app.route('/stills')
# def stills():
#     media = get_media_files()
#     media['stills'] = [img for img in media['stills'] if 'related' not in os.path.basename(img).lower()]
#     return render_template('stills.html', media=media)


# @app.route('/artworks')
# def artworks():
#     return render_template('artworks.html', media=get_media_files())


# @app.route('/stills/<image_name>')
# def view_image(image_name):
#     safe_image_name = secure_filename(image_name)
#     base_name, ext = os.path.splitext(safe_image_name)
#     folder = os.path.join(app.config['UPLOAD_FOLDER'], 'stills')
#     file_path = os.path.join(folder, safe_image_name)

#     if not os.path.isfile(file_path):
#         abort(404)

#     all_files = os.listdir(folder)
#     related_images = [
#         url_for('static', filename=f'uploads/stills/{f}')
#         for f in all_files if f.startswith(f"{base_name}related")
#     ]

#     return render_template(
#         'view_image.html',
#         image_name=image_name,
#         image=url_for('static', filename=f'uploads/stills/{image_name}'),
#         images=related_images,
#         media=get_media_files(exclude_still=image_name)
#     )


# @app.route('/admin-xyz123', methods=['GET', 'POST'])
# def admin_panel():
#     if not session.get('admin_logged_in'):
#         flash("Please login as admin to access this page.", "error")
#         return redirect(url_for('admin_login'))

#     if request.method == 'POST':
#         category = request.form.get('category')
#         file = request.files.get('file')
#         base_image = request.form.get('base_image')

#         if not category or category not in CATEGORIES:
#             flash("Invalid category selected!", "error")
#             return redirect(url_for('admin_panel'))

#         if not file or file.filename == '':
#             flash("No file selected!", "error")
#             return redirect(url_for('admin_panel'))

#         ext = os.path.splitext(file.filename)[1].lower()
#         if ext not in CATEGORIES[category]:
#             flash("Invalid file format!", "error")
#             return redirect(url_for('admin_panel'))

#         original_filename = secure_filename(file.filename)

#         if category == 'stills' and base_image:
#             base_name, _ = os.path.splitext(secure_filename(base_image))
#             filename = f"{base_name}related_{original_filename}"
#         else:
#             filename = original_filename

#         save_path = os.path.join(app.config['UPLOAD_FOLDER'], category, filename)
#         counter = 1
#         while os.path.exists(save_path):
#             name, ext = os.path.splitext(filename)
#             filename = f"{name}_{counter}{ext}"
#             save_path = os.path.join(app.config['UPLOAD_FOLDER'], category, filename)
#             counter += 1

#         file.save(save_path)

#         # Save file metadata to Neon DB
#         new_file = UploadedFile(filename=filename, category=category)
#         db.session.add(new_file)
#         db.session.commit()

#         flash("File uploaded successfully!", "success")
#         return redirect(url_for('admin_panel'))

#     still_images = [
#         f for f in os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], 'stills')) if 'related' not in f
#     ]

#     return render_template('admin.html', media=get_media_files(), still_images=still_images)


# @app.route('/delete-file/<category>/<filename>', methods=['POST'])
# def delete_file(category, filename):
#     if not session.get('admin_logged_in'):
#         flash("Unauthorized access!", "error")
#         return redirect(url_for('admin_login'))

#     if category not in CATEGORIES:
#         flash("Invalid category!", "error")
#         return redirect(url_for('admin_panel'))

#     filepath = os.path.join(app.config['UPLOAD_FOLDER'], category, filename)
#     if os.path.exists(filepath):
#         os.remove(filepath)
#         flash("File deleted successfully!", "success")
#         # Remove from DB
#         file_entry = UploadedFile.query.filter_by(filename=filename, category=category).first()
#         if file_entry:
#             db.session.delete(file_entry)
#             db.session.commit()
#     else:
#         flash("File not found!", "error")

#     return redirect(url_for('admin_panel'))


# @app.route('/admin-login', methods=['GET', 'POST'])
# def admin_login():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')

#         if username == "admin" and password == "admin123":
#             session['admin_logged_in'] = True
#             flash("Logged in as admin.", "success")
#             return redirect(url_for('admin_panel'))
#         else:
#             flash("Invalid credentials!", "error")
#             return redirect(url_for('admin_login'))

#     return render_template('admin.html')


# @app.route('/admin-logout')
# def admin_logout():
#     session.pop('admin_logged_in', None)
#     flash("Logged out successfully.", "info")
#     return redirect(url_for('home'))


# @app.template_filter('replace_extension')
# def replace_extension(filename):
#     return os.path.splitext(filename)[0]


# if __name__ == '__main__':
#     app.run(debug=True)
