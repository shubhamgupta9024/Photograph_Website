from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key"

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CATEGORIES = {
    'films': ['.mp4', '.mov', '.avi'],
    'projects': ['.mp4', '.mov', '.avi'],
    'stills': ['.jpg', '.jpeg', '.png'],
    'artworks': ['.jpg', '.jpeg', '.png']
}

# Ensure upload directories exist
for category in CATEGORIES:
    os.makedirs(os.path.join(UPLOAD_FOLDER, category), exist_ok=True)

def get_media_files():
    media = {category: [] for category in CATEGORIES}
    for category, extensions in CATEGORIES.items():
        folder = os.path.join(UPLOAD_FOLDER, category)
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if f.endswith(tuple(extensions))]
            media[category] = [url_for('static', filename=f'uploads/{category}/{f}') for f in files]
    return media

@app.route('/')
def home():
    return render_template('website.html', media=get_media_files())

@app.route('/films')
def films():
    return render_template('films.html', media=get_media_files())

@app.route('/projects')
def projects():
    return render_template('projects.html', media=get_media_files())

@app.route('/stills')
def stills():
    return render_template('stills.html', media=get_media_files())

@app.route('/artworks')
def artworks():
    return render_template('artworks.html', media=get_media_files())

@app.route('/stills/<image_name>', methods=['GET', 'POST'])
def view_image(image_name):
    image_name = secure_filename(image_name)  # Prevent path traversal
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'stills', image_name)

    if not os.path.isfile(image_path):
        abort(404)  # Ensure it's a file

    if request.method == 'POST':
        if not session.get('admin_logged_in'):
            flash("Unauthorized access!", "error")
            return redirect(url_for('admin_login'))

        file = request.files.get('file')
        if not file or file.filename == '':
            flash("No file selected!", "error")
            return redirect(request.url)

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in CATEGORIES['stills']:
            flash("Invalid file format!", "error")
            return redirect(request.url)

        unique_filename = str(uuid.uuid4()) + ext
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'stills', unique_filename))

        flash("New still uploaded successfully!", "success")
        return redirect(url_for('stills'))

    image_url = url_for('static', filename=f'uploads/stills/{image_name}')
    return render_template('view_image.html', image=image_url, image_name=image_name)

@app.route('/admin-xyz123', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        category = request.form.get('category')
        file = request.files.get('file')

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

        unique_filename = str(uuid.uuid4()) + ext
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], category, unique_filename))

        flash("File uploaded successfully!", "success")
        return redirect(url_for('admin_panel'))

    return render_template('admin.html', media=get_media_files())

@app.route('/delete-file/<category>/<filename>', methods=['POST'])
def delete_file(category, filename):
    if category not in CATEGORIES:
        flash("Invalid category!", "error")
        return redirect(url_for('admin_panel'))

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], category, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash("File deleted successfully!", "success")
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

    return render_template('admin_login.html')

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))




if __name__ == '__main__':
    app.run(debug=True)




# from flask import Flask, render_template, request, redirect, url_for, flash, session
# import os
# import uuid  # To generate unique filenames

# app = Flask(__name__)
# app.secret_key = "your_secret_key"

# UPLOAD_FOLDER = 'static/uploads'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# CATEGORIES = {
#     'films': ['.mp4', '.mov', '.avi'],
#     'projects': ['.mp4', '.mov', '.avi'],
#     'stills': ['.jpg', '.png', '.jpeg'],
#     'artworks': ['.jpg', '.png', '.jpeg']
# }

# # Ensure upload directories exist
# for category in CATEGORIES.keys():
#     os.makedirs(os.path.join(UPLOAD_FOLDER, category), exist_ok=True)

# def get_media_files():
#     media = {category: [] for category in CATEGORIES.keys()}
#     for category, extensions in CATEGORIES.items():
#         folder_path = os.path.join(UPLOAD_FOLDER, category)
#         if os.path.exists(folder_path):
#             files = [f for f in os.listdir(folder_path) if f.endswith(tuple(extensions))]
#             media[category] = [url_for('static', filename=f'uploads/{category}/{f}') for f in files]
#     return media

# @app.route('/')
# def home():
#     media = get_media_files()
#     return render_template('website.html', media=media)

# @app.route('/films')
# def films():
#     media = get_media_files()
#     return render_template('films.html', media=media)

# @app.route('/projects')
# def projects():
#     media = get_media_files()
#     return render_template('projects.html', media=media)

# @app.route('/stills')
# def stills():
#     media = get_media_files()
#     return render_template('stills.html', media=media)

# @app.route('/artworks')
# def artworks():
#     media = get_media_files()
#     return render_template('artworks.html', media=media)

# @app.route('/stills/<image_name>', methods=['GET', 'POST'])
# def view_image(image_name):
#     if request.method == 'POST':
#         if not session.get('admin_logged_in'):
#             flash("Unauthorized access!", "error")
#             return redirect(url_for('admin_login'))

#         file = request.files.get('file')
#         if not file or file.filename == '':
#             flash("No file selected!", "error")
#             return redirect(request.url)

#         ext = os.path.splitext(file.filename)[1].lower()
#         if ext not in CATEGORIES['stills']:
#             flash("Invalid file format!", "error")
#             return redirect(request.url)

#         unique_filename = str(uuid.uuid4()) + ext
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'stills', unique_filename)
#         file.save(file_path)

#         flash("New still uploaded successfully!", "success")
#         return redirect(url_for('stills'))

#     image_path = f'/static/uploads/stills/{image_name}'
#     return render_template('view_image.html', image=image_path, image_name=image_name)


# @app.route('/admin-xyz123', methods=['GET', 'POST'])

# def admin_panel():
#     if request.method == 'POST':
#         category = request.form.get('category')
#         file = request.files.get('file')

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

#         unique_filename = str(uuid.uuid4()) + ext
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], category, unique_filename)
#         file.save(file_path)

#         flash("File uploaded successfully!", "success")
#         return redirect(url_for('admin_panel'))

#     return render_template('admin.html', media=get_media_files())

# @app.route('/delete-file/<category>/<filename>', methods=['POST'])
# def delete_file(category, filename):
#     if category not in CATEGORIES:
#         flash("Invalid category!", "error")
#         return redirect(url_for('admin_panel'))

#     file_path = os.path.join(app.config['UPLOAD_FOLDER'], category, filename)
#     if os.path.exists(file_path):
#         os.remove(file_path)
#         flash("File deleted successfully!", "success")
#     else:
#         flash("File not found!", "error")

#     return redirect(url_for('admin_panel'))

# @app.route('/admin-login', methods=['GET', 'POST'])
# def admin_login():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')

#         if username == "admin" and password == "admin123":  # Simple login
#             session['admin_logged_in'] = True
#             flash("Logged in as admin.", "success")
#             return redirect(url_for('admin_panel'))
#         else:
#             flash("Invalid credentials!", "error")
#             return redirect(url_for('admin_login'))

#     return render_template('admin_login.html')

# @app.route('/admin-logout')
# def admin_logout():
#     session.pop('admin_logged_in', None)
#     flash("Logged out successfully.", "info")
#     return redirect(url_for('home'))

# if __name__ == '__main__':
#     app.run(debug=True)




# from flask import Flask, render_template, request, redirect, url_for, flash
# import os
# import uuid  # To generate unique filenames

# app = Flask(__name__)
# app.secret_key = "your_secret_key"

# UPLOAD_FOLDER = 'static/uploads'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# CATEGORIES = {
#     'films': ['.mp4', '.mov', '.avi'],
#     'projects': ['.mp4', '.mov', '.avi'],
#     'stills': ['.jpg', '.png', '.jpeg'],
#     'artworks': ['.jpg', '.png', '.jpeg']
# }

# # Ensure upload directories exist
# for category in CATEGORIES.keys():
#     os.makedirs(os.path.join(UPLOAD_FOLDER, category), exist_ok=True)

# def get_media_files():
#     """Fetch media files dynamically and return them for each section."""
#     media = {category: [] for category in CATEGORIES.keys()}
    
#     for category, extensions in CATEGORIES.items():
#         folder_path = os.path.join(UPLOAD_FOLDER, category)
#         if os.path.exists(folder_path):
#             files = [f for f in os.listdir(folder_path) if f.endswith(tuple(extensions))]
#             media[category] = [url_for('static', filename=f'uploads/{category}/{f}') for f in files]
    
#     return media

# @app.route('/')
# def home():
#     media = get_media_files()
#     return render_template('website.html', media=media)

# @app.route('/films')
# def films():
#     media = get_media_files()
#     return render_template('films.html', media=media)

# @app.route('/projects')
# def projects():
#     media = get_media_files()
#     return render_template('projects.html', media=media)

# @app.route('/stills')
# def stills():
#     media = get_media_files()
#     return render_template('stills.html', media=media)

# @app.route('/stills/<image_name>')
# def view_image(image_name):
#     image_path = f'/static/stills/{image_name}'
#     return render_template('view_image.html', image=image_path)


# @app.route('/artworks')
# def artworks():
#     media = get_media_files()
#     return render_template('artworks.html', media=media)

# @app.route('/admin-xyz123', methods=['GET', 'POST'])
# def admin_panel():
#     if request.method == 'POST':
#         category = request.form.get('category')
#         file = request.files.get('file')

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

#         # Generate unique filename to prevent overwriting
#         unique_filename = str(uuid.uuid4()) + ext
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], category, unique_filename)
#         file.save(file_path)

#         flash("File uploaded successfully!", "success")
#         return redirect(url_for('admin_panel'))

#     return render_template('admin.html', media=get_media_files())

# @app.route('/delete-file/<category>/<filename>', methods=['POST'])
# def delete_file(category, filename):
#     if category not in CATEGORIES:
#         flash("Invalid category!", "error")
#         return redirect(url_for('admin_panel'))

#     file_path = os.path.join(app.config['UPLOAD_FOLDER'], category, filename)
#     if os.path.exists(file_path):
#         os.remove(file_path)
#         flash("File deleted successfully!", "success")
#     else:
#         flash("File not found!", "error")

#     return redirect(url_for('admin_panel'))

# if __name__ == '__main__':
#     app.run(debug=True)



