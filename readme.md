# 🏐 VolleyChamp - Gestion des déclarations d'équipes

Application Django complète pour la gestion des déclarations d'équipes de volleyball à La Réunion.

## ✨ **Fonctionnalités**

- 📝 **Déclaration d'équipes** avec protection anti-spam multicouche
- 👁️ **Consultation publique** des déclarations par tournoi
- 📚 **Archives** des tournois passés
- ⚙️ **Administration avancée** avec import/export CSV
- 🎨 **Design mobile-first** responsive
- 🛡️ **Sécurité renforcée** (honeypot, limitation IP, validation métier)

## 🛠️ **Technologies**

- **Backend** : Django 5.0.7, Python 3.12
- **Frontend** : HTML5, CSS3, JavaScript (Vanilla)
- **Base de données** : SQLite (dev) / MySQL (prod)
- **Design** : Mobile-first, responsive
- **Localisation** : Français (La Réunion, GMT+4)

## 🚀 **Installation locale**

```bash
# Cloner le repository
git clone https://github.com/[VOTRE-USERNAME]/volleychamp.git
cd volleychamp

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer dépendances
pip install -r requirements.txt

# Configuration base de données
python manage.py makemigrations
python manage.py migrate

# Créer superutilisateur
python manage.py createsuperuser

# Lancer serveur développement
python manage.py runserver