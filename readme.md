# SG-UJEPH - Système de Gestion de l'Université Jérusalem de Pignon Haïti

[![Django](https://img.shields.io/badge/Django-5.2.3-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13.3-blue.svg)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.3-purple.svg)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-Academic-lightgrey.svg)](LICENSE)

**Application web de gestion académique** développée sur mesure pour moderniser et automatiser la gestion pédagogique de l'Université Jérusalem de Pignon (UJEPH).

## 🌐 Accès en Ligne
**URL de démonstration :** https://sg.bittonik.com  
**Code source :** https://github.com/blessedwingtech/ujeph

## 📋 Table des Matières
- [🎯 Contexte et Problématique](#-contexte-et-problématique)
- [🚀 Fonctionnalités](#-fonctionnalités)
- [🏗️ Architecture Technique](#️-architecture-technique)
- [🛠️ Technologies Utilisées](#️-technologies-utilisées)
- [📁 Structure du Projet](#-structure-du-projet)
- [⚙️ Installation et Configuration](#️-installation-et-configuration)
- [▶️ Démonstration Rapide](#️-démonstration-rapide)
- [🧪 Tests](#-tests)
- [📊 Captures d'Écran](#-captures-décran)
- [🤝 Équipe de Développement](#-équipe-de-développement)
- [📚 Documentation](#-documentation)
- [📄 Licence](#-licence)

## 🎯 Contexte et Problématique

# Le Problème
L'UJEPH gérait ses processus académiques de manière **entièrement manuelle** :
- ✅ **Inscriptions** sur papier
- ✅ **Notes** dans des fichiers Excel non synchronisés
- ✅ **Calculs manuels** des moyennes
- ✅ **Retards** dans la publication des résultats
- ✅ **Manque de transparence** pour les étudiants

# La Solution
**SG-UJEPH** : Une application web centralisée qui :
- ✅ Automatise les processus académiques
- ✅ Élimine les erreurs de saisie
- ✅ Fournit une plateforme unique accessible 24h/24
- ✅ Garantit la traçabilité et la sécurité

## 🚀 Fonctionnalités

### 👨‍💼 **Administrateurs**
- Gestion complète des facultés, cours et programmes
- Inscription et gestion des étudiants
- Validation et publication des notes
- Tableaux de bord de supervision
- Journalisation complète des activités

### 👨‍🏫 **Professeurs**
- Consultation des cours assignés
- Saisie des notes avec état "Brouillon"
- Soumission des notes pour validation
- Interface intuitive de saisie par tableau

### 👨‍🎓 **Étudiants**
- Consultation des notes publiées
- Calcul automatique de la moyenne générale
- Visualisation de la progression académique
- Accès sécurisé 24h/24

### 🔄 **Workflow des Notes**
1. **Brouillon** → Saisie par le professeur
2. **Soumise** → Validation par l'administration  
3. **Publiée** → Visible par l'étudiant
4. **Rejetée** → Retour au professeur avec motif

## 🏗️ Architecture Technique
Architecture Django MVT



### Stack Technique Complète
- **Backend :** Django 5.2.3 (Python 3.13.3)
- **Base de données :** MySQL 8.0
- **Frontend :** HTML5, CSS3, JavaScript, Bootstrap 5.3.3
- **Serveur :** Nginx + Gunicorn
- **Hébergement :** VPS Cloud (Ubuntu 22.04)
- **Sécurité :** HTTPS/TLS, bcrypt, CSRF Protection

## 🛠️ Technologies Utilisées

### **Backend**
- Python 3.13.3
- Django 5.2.3
- Django REST Framework
- MySQL Connector
- Gunicorn

### **Frontend**
- Bootstrap 5.3.3
- Font Awesome 6.4.0
- SweetAlert2
- jQuery 3.6.0
- Chart.js

### **Sécurité**
- bcrypt pour le hachage des mots de passe
- CSRF Tokens
- Session management avancé
- Journalisation complète (audit logs)

 
 
## ⚙️ Installation et Configuration

### Prérequis
- Python 3.13.3
- MySQL 8.0
- Git

### Installation Locale

1. **Cloner le dépôt**
```bash
git clone https://github.com/blessedwingtech/ujeph.git
cd ujeph

creer environnement virtuel
python -m venv venv 
source venv/bin/activate

## Installer les dependances
pip install -r requirements.txt

#configuration base de donnees avec l'utilisateur sg_user
CREATE DATABASE db_sg_ujeph CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sg_user'@'localhost' IDENTIFIED BY 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON db_sg_ujeph.* TO 'sg_user'@'localhost';
FLUSH PRIVILEGES;

##ajuster le fichier settings.py
```from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure--tvx4&f+v6$$aa)+v6!ynyts4@$16mmk&#+qu=h-jev#!)qh)$'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '192.168.241.229', '127.0.0.1', '192.168.1.27', '10.219.252.229', '10.88.162.229']
SITE_URL = 'http://127.0.0.1:8000'

AUTH_USER_MODEL = 'accounts.User'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'academics',
    'grades',
    'crispy_forms',
    'crispy_bootstrap5',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900
AUTO_LOGOUT_TIMEOUT = 300

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.AutoLogoutMiddleware',
]

ROOT_URLCONF = 'sg_ujeph.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sg_ujeph.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'db_sg_ujeph',
        'USER': 'root',
        'PASSWORD': 'votre_mot_de_passe',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'blessedwingtech@gmail.com'
EMAIL_HOST_PASSWORD = 'xxwp dook dxjk senm'
DEFAULT_FROM_EMAIL = 'Système UJEPH <blessedwingtech@gmail.com>'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'fr-FR'

TIME_ZONE = 'America/Port-au-Prince'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/comptes/login/'

LOGIN_REDIRECT_URL = '/accounts/dashboard/'```

#appliquer les migrations
python manage.py makemigrations
python manage.py migrate

#creer le suoerutilisateur
python manage.py createsuperuser

#lancer le serveur
python manage.py runserver

###acceder a l'application
http://localhost:8000