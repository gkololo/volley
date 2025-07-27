from django import forms
from django.utils import timezone
from .models import Declaration

class DeclarationForm(forms.ModelForm):
    # 🍯 HONEYPOT - Champ piège invisible pour robots
    website = forms.CharField(
        required=False,
        label='',  # Pas de label visible
        widget=forms.TextInput(attrs={
            'style': 'position:absolute;left:-9999px;width:1px;height:1px;',
            'tabindex': '-1',
            'autocomplete': 'nope',
            'aria-hidden': 'true'
        })
    )

    class Meta:
        model = Declaration
        exclude = ['date_declaration']
        widgets = {
            "date_tournoi": forms.DateInput(attrs={"type": "date"}),
            "declarant": forms.TextInput(attrs={
                "placeholder": "Exemple: Jean Dupont",
                "class": "form-control"
            }),
            "email_club": forms.EmailInput(attrs={
                "placeholder": "exemple@monclub.re",
                "class": "form-control"
            }),
            "remarques": forms.Textarea(attrs={
                "placeholder": "Remarques éventuelles concernant cette déclaration (optionnel)",
                "rows": 3,
                "class": "form-control"
            }),
            "nombre_equipes": forms.NumberInput(attrs={
                "min": "1",
                "max": "10",
                "class": "form-control"
            })
        }

    def clean_website(self):
        """Honeypot: si rempli par un robot = erreur"""
        value = self.cleaned_data['website']
        if value:
            raise forms.ValidationError("Requête invalide détectée")
        return value

    def clean_date_tournoi(self):
        """Validation date tournoi"""
        date = self.cleaned_data["date_tournoi"]
        if date < timezone.now().date():
            raise forms.ValidationError("La date du tournoi ne peut pas être dans le passé.")
        return date

    def clean_declarant(self):
        """Validation du nom du déclarant - anti-spam + blocage valeurs par défaut"""
        declarant = self.cleaned_data.get('declarant', '')

        # 🚫 BLOQUER LES VALEURS PAR DÉFAUT
        valeurs_interdites = [
            'inconnu', 'unknown', 'test', 'exemple', 'example',
            'admin', 'administrateur', 'user', 'utilisateur'
        ]

        if declarant.lower().strip() in valeurs_interdites:
            raise forms.ValidationError("Veuillez saisir votre vrai nom (les valeurs d'exemple ne sont pas autorisées)")

        # Minimum 2 mots (prénom + nom)
        mots = declarant.strip().split()
        if len(mots) < 2:
            raise forms.ValidationError("Veuillez saisir votre prénom et nom complets")

        # Pas que des chiffres
        if declarant.replace(' ', '').isdigit():
            raise forms.ValidationError("Le nom ne peut pas être uniquement des chiffres")

        # Longueur minimum raisonnable
        if len(declarant.strip()) < 5:
            raise forms.ValidationError("Le nom semble trop court")

        # Pas de caractères suspects répétés
        if any(char * 5 in declarant for char in 'abcdefghijklmnopqrstuvwxyz'):
            raise forms.ValidationError("Format de nom invalide")

        return declarant.strip().title()  # Première lettre en majuscule

    def clean_email_club(self):
        """Validation email anti-spam + blocage valeurs par défaut"""
        email = self.cleaned_data.get('email_club', '')

        # 🚫 BLOQUER LES EMAILS PAR DÉFAUT
        emails_interdits = [
            'inconnu@exemple.com', 'unknown@example.com', 'test@test.com',
            'admin@admin.com', 'user@user.com', 'example@example.com',
            'test@example.com', 'noreply@example.com'
        ]

        if email.lower().strip() in emails_interdits:
            raise forms.ValidationError("Veuillez saisir l'adresse email réelle de votre club")

        # Domaines email temporaires/suspects à bloquer
        spam_domains = [
            'tempmail.org', '10minutemail.com', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email', 'temp-mail.org',
            'maildrop.cc', 'sharklasers.com', 'yopmail.com',
            'example.com', 'exemple.com', 'test.com'
        ]

        email_lower = email.lower().strip()

        for domain in spam_domains:
            if domain in email_lower:
                raise forms.ValidationError("Les adresses email temporaires ou d'exemple ne sont pas autorisées")

        # Vérification format basique supplémentaire
        if email_lower.count('@') != 1:
            raise forms.ValidationError("Format d'email invalide")

        # Vérifier que le domaine a au moins un point
        partie_domaine = email_lower.split('@')[1] if '@' in email_lower else ''
        if '.' not in partie_domaine:
            raise forms.ValidationError("Le domaine de l'email semble invalide")

        return email_lower

    def clean_nombre_equipes(self):
        """Validation nombre d'équipes"""
        nombre = self.cleaned_data.get('nombre_equipes')

        if nombre is None:
            raise forms.ValidationError("Le nombre d'équipes est requis")

        if nombre <= 0:
            raise forms.ValidationError("Le nombre d'équipes doit être supérieur à 0")

        if nombre > 10:
            raise forms.ValidationError("Maximum 10 équipes par déclaration")

        return nombre

    def clean_remarques(self):
        """Validation remarques - anti-spam"""
        remarques = self.cleaned_data.get('remarques', '')

        # Détecter les URLs (spam fréquent)
        mots_suspects = ['http://', 'https://', 'www.', '.com', '.org', '.net']
        if any(mot in remarques.lower() for mot in mots_suspects):
            raise forms.ValidationError("Les liens ne sont pas autorisés dans les remarques")

        # Limiter la longueur
        if len(remarques) > 500:
            raise forms.ValidationError("Les remarques ne peuvent pas dépasser 500 caractères")

        return remarques.strip()

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()

        # Vérification croisée : cohérence des données
        declarant = cleaned_data.get('declarant', '')
        email = cleaned_data.get('email_club', '')

        # Si l'email contient le nom du déclarant, c'est suspect
        if declarant and email:
            nom_parties = declarant.lower().split()
            for partie in nom_parties:
                if len(partie) > 3 and partie in email.lower():
                    # C'est normal, pas d'erreur
                    pass

        return cleaned_data