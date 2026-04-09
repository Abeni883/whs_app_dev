"""
Authentifizierung Blueprint für WHS Testprotokoll.

Enthält alle Routes für:
- Login/Logout
- Registrierung
- Profil-Verwaltung
- Admin-Benutzerverwaltung
"""

from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app
)
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)
from flask_bcrypt import Bcrypt

from models import db, User

# Blueprint erstellen
auth_bp = Blueprint('auth', __name__)

# Bcrypt-Instanz (wird mit init_app initialisiert)
bcrypt = Bcrypt()


def init_app(app):
    """Initialisiert bcrypt mit der Flask-App."""
    bcrypt.init_app(app)


# ==================== HELPER-FUNKTIONEN ====================

def admin_required(f):
    """Decorator für Admin-only Routen."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Sie haben keine Berechtigung für diese Seite.', 'error')
            return redirect(url_for('projekte.projekte'))
        return f(*args, **kwargs)
    return decorated_function


def check_first_user():
    """Prüft ob es bereits Benutzer gibt - wenn nicht, Registrierung ohne Login erlauben."""
    return User.query.count() == 0


# ==================== AUTHENTIFIZIERUNG ====================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login-Seite und Verarbeitung."""
    # Bereits eingeloggt?
    if current_user.is_authenticated:
        return redirect(url_for('projekte.projekte'))

    # Falls keine Benutzer existieren, zur Registrierung weiterleiten
    if check_first_user():
        flash('Willkommen! Bitte erstellen Sie den ersten Benutzer-Account.', 'info')
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        if not username or not password:
            flash('Bitte Benutzername und Passwort eingeben.', 'error')
            return render_template('auth/login.html')

        user = User.query.filter_by(username=username).first()

        if not user:
            flash('Ungültige Anmeldedaten.', 'error')
            return render_template('auth/login.html')

        # Account gesperrt?
        if user.is_locked():
            flash('Account temporär gesperrt. Bitte versuchen Sie es in 15 Minuten erneut.', 'error')
            return render_template('auth/login.html')

        # Account deaktiviert?
        if not user.is_active:
            flash('Dieser Account wurde deaktiviert.', 'error')
            return render_template('auth/login.html')

        # Passwort prüfen
        if bcrypt.check_password_hash(user.password_hash, password):
            # Erfolgreicher Login
            user.reset_failed_login()
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Session konfigurieren
            session.permanent = bool(remember)
            if remember:
                current_app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
            else:
                current_app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

            login_user(user, remember=bool(remember))
            flash(f'Willkommen zurück, {user.full_name}!', 'success')

            # Weiterleitung zur ursprünglich angeforderten Seite
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('projekte.projekte'))
        else:
            # Fehlgeschlagener Login
            user.increment_failed_login()
            db.session.commit()
            flash('Ungültige Anmeldedaten.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Selbstregistrierung für neue Benutzer."""
    # Bereits eingeloggt?
    if current_user.is_authenticated:
        return redirect(url_for('projekte.projekte'))

    is_first_user = check_first_user()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()

        # Validierung
        errors = []

        if not username or len(username) < 3:
            errors.append('Benutzername muss mindestens 3 Zeichen lang sein.')

        if not email or '@' not in email:
            errors.append('Bitte eine gültige E-Mail-Adresse eingeben.')

        if not password or len(password) < 8:
            errors.append('Passwort muss mindestens 8 Zeichen lang sein.')

        if password != password_confirm:
            errors.append('Passwörter stimmen nicht überein.')

        # Prüfe ob Benutzername oder Email bereits existieren
        if User.query.filter_by(username=username).first():
            errors.append('Dieser Benutzername ist bereits vergeben.')

        if User.query.filter_by(email=email).first():
            errors.append('Diese E-Mail-Adresse ist bereits registriert.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html', is_first_user=is_first_user)

        # Benutzer erstellen
        user = User(
            username=username,
            email=email,
            password_hash=bcrypt.generate_password_hash(password).decode('utf-8'),
            first_name=first_name or None,
            last_name=last_name or None,
            is_admin=is_first_user  # Erster Benutzer wird Admin
        )
        db.session.add(user)
        db.session.commit()

        if is_first_user:
            flash('Administrator-Account erfolgreich erstellt! Bitte melden Sie sich an.', 'success')
        else:
            flash('Registrierung erfolgreich! Bitte melden Sie sich an.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', is_first_user=is_first_user)


@auth_bp.route('/logout')
@login_required
def logout():
    """Benutzer ausloggen."""
    logout_user()
    flash('Sie wurden erfolgreich abgemeldet.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Passwort vergessen - Token generieren."""
    if current_user.is_authenticated:
        return redirect(url_for('projekte.projekte'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Bitte E-Mail-Adresse eingeben.', 'error')
            return render_template('auth/forgot_password.html')

        user = User.query.filter_by(email=email).first()

        # Immer gleiche Meldung (Sicherheit)
        flash('Falls ein Account mit dieser E-Mail existiert, wurde ein Reset-Link erstellt.', 'info')

        if user and user.is_active:
            token = user.generate_reset_token()
            db.session.commit()
            # In Produktion würde hier eine Email gesendet werden
            # Stattdessen: Admin kann den Link über /admin/users sehen

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Eigenes Profil bearbeiten."""
    if request.method == 'POST':
        action = request.form.get('action', 'profile')

        if action == 'profile':
            # Profildaten aktualisieren
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip().lower()

            # Email-Validierung
            if email != current_user.email:
                if User.query.filter(User.id != current_user.id, User.email == email).first():
                    flash('Diese E-Mail-Adresse ist bereits registriert.', 'error')
                    return render_template('auth/profile.html')

            current_user.first_name = first_name or None
            current_user.last_name = last_name or None
            current_user.email = email
            db.session.commit()
            flash('Profil erfolgreich aktualisiert.', 'success')

        elif action == 'password':
            # Passwort ändern
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            new_password_confirm = request.form.get('new_password_confirm', '')

            if not bcrypt.check_password_hash(current_user.password_hash, current_password):
                flash('Aktuelles Passwort ist falsch.', 'error')
                return render_template('auth/profile.html')

            if len(new_password) < 8:
                flash('Neues Passwort muss mindestens 8 Zeichen lang sein.', 'error')
                return render_template('auth/profile.html')

            if new_password != new_password_confirm:
                flash('Neue Passwörter stimmen nicht überein.', 'error')
                return render_template('auth/profile.html')

            current_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()
            flash('Passwort erfolgreich geändert.', 'success')

        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')


# ==================== ADMIN-BEREICH ====================

@auth_bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Admin: Benutzerverwaltung."""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('auth/admin_users.html', users=users)


@auth_bp.route('/admin/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def admin_toggle_user_active(user_id):
    """Admin: Benutzer aktivieren/deaktivieren."""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('Sie können sich nicht selbst deaktivieren.', 'error')
        return redirect(url_for('auth.admin_users'))

    user.is_active = not user.is_active
    db.session.commit()

    status = 'aktiviert' if user.is_active else 'deaktiviert'
    flash(f'Benutzer "{user.username}" wurde {status}.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def admin_toggle_user_admin(user_id):
    """Admin: Admin-Rechte vergeben/entziehen."""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('Sie können sich nicht selbst die Admin-Rechte entziehen.', 'error')
        return redirect(url_for('auth.admin_users'))

    user.is_admin = not user.is_admin
    db.session.commit()

    status = 'vergeben' if user.is_admin else 'entzogen'
    flash(f'Admin-Rechte für "{user.username}" wurden {status}.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Admin: Benutzer komplett löschen."""
    user = User.query.get_or_404(user_id)

    # Selbstlöschung verhindern
    if user.id == current_user.id:
        flash('Sie können sich nicht selbst löschen.', 'error')
        return redirect(url_for('auth.admin_users'))

    # Prüfen ob es der letzte Admin ist
    if user.is_admin:
        admin_count = User.query.filter_by(is_admin=True, is_active=True).count()
        if admin_count <= 1:
            flash('Der letzte Admin kann nicht gelöscht werden.', 'error')
            return redirect(url_for('auth.admin_users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()

    flash(f'Benutzer "{username}" wurde dauerhaft gelöscht.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    """Admin: Benutzer bearbeiten."""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('Bitte bearbeiten Sie Ihr eigenes Profil über die Profil-Seite.', 'warning')
        return redirect(url_for('auth.admin_users'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        new_password = request.form.get('new_password', '').strip()
        is_active = request.form.get('is_active') == 'on'
        is_admin = request.form.get('is_admin') == 'on'

        # Validierung
        if not username or not email:
            flash('Benutzername und E-Mail sind erforderlich.', 'error')
            return render_template('auth/admin_edit_user.html', user=user)

        # Prüfen ob Benutzername bereits existiert (außer bei diesem Benutzer)
        existing_user = User.query.filter(User.username == username, User.id != user.id).first()
        if existing_user:
            flash('Dieser Benutzername ist bereits vergeben.', 'error')
            return render_template('auth/admin_edit_user.html', user=user)

        # Prüfen ob E-Mail bereits existiert (außer bei diesem Benutzer)
        existing_email = User.query.filter(User.email == email, User.id != user.id).first()
        if existing_email:
            flash('Diese E-Mail-Adresse ist bereits registriert.', 'error')
            return render_template('auth/admin_edit_user.html', user=user)

        # Benutzer aktualisieren
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = is_active
        user.is_admin = is_admin

        # Passwort nur ändern wenn eingegeben
        if new_password:
            if len(new_password) < 6:
                flash('Das Passwort muss mindestens 6 Zeichen lang sein.', 'error')
                return render_template('auth/admin_edit_user.html', user=user)
            user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')

        db.session.commit()
        flash(f'Benutzer "{user.username}" wurde erfolgreich aktualisiert.', 'success')
        return redirect(url_for('auth.admin_users'))

    return render_template('auth/admin_edit_user.html', user=user)
