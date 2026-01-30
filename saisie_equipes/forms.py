from django import forms
from django.utils import timezone
from .models import Declaration, Candidature, Tournoi, Club


# ═══════════════════════════════════════════════════
# 🔧 MIXIN ANTI-SPAM RÉUTILISABLE
# ═══════════════════════════════════════════════════

class AntiSpamFormMixin:
    """
    Mixin pour ajouter honeypot et validations anti-spam communes
    Réutilisable dans tous les formulaires du projet
    """
    
    def add_honeypot(self):
        """Ajoute le champ honeypot invisible au formulaire"""
        self.fields['website'] = forms.CharField(
            required=False,
            label='',
            widget=forms.TextInput(attrs={
                'style': 'position:absolute;left:-9999px;width:1px;height:1px;',
                'tabindex': '-1',
                'autocomplete': 'nope',
                'aria-hidden': 'true'
            })
        )
    
    def clean_website(self):
        """Honeypot: si rempli par un robot = erreur"""
        value = self.cleaned_data.get('website', '')
        if value:
            raise forms.ValidationError("Requête invalide détectée")
        return value
    
    def validate_declarant(self, declarant):
        """Validation générique du nom du déclarant - anti-spam"""
        # 🚫 BLOQUER LES VALEURS PAR DÉFAUT
        valeurs_interdites = [
            'inconnu', 'unknown', 'test', 'exemple', 'example',
            'admin', 'administrateur', 'user', 'utilisateur'
        ]
        
        if declarant.lower().strip() in valeurs_interdites:
            raise forms.ValidationError("Veuillez saisir votre vrai nom")
        
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
        
        return declarant.strip().title()
    
    def validate_email(self, email):
        """Validation générique email anti-spam"""
        # 🚫 BLOQUER LES EMAILS PAR DÉFAUT
        emails_interdits = [
            'inconnu@exemple.com', 'unknown@example.com', 'test@test.com',
            'admin@admin.com', 'user@user.com', 'example@example.com',
            'test@example.com', 'noreply@example.com'
        ]
        
        if email.lower().strip() in emails_interdits:
            raise forms.ValidationError("Veuillez saisir une adresse email réelle")
        
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
                raise forms.ValidationError("Les adresses email temporaires ne sont pas autorisées")
        
        # Vérification format basique supplémentaire
        if email_lower.count('@') != 1:
            raise forms.ValidationError("Format d'email invalide")
        
        # Vérifier que le domaine a au moins un point
        partie_domaine = email_lower.split('@')[1] if '@' in email_lower else ''
        if '.' not in partie_domaine:
            raise forms.ValidationError("Le domaine de l'email semble invalide")
        
        return email_lower
    
    def validate_remarques(self, remarques, max_length=500):
        """Validation générique des remarques - anti-spam"""
        # Détecter les URLs (spam fréquent)
        mots_suspects = ['http://', 'https://', 'www.', '.com', '.org', '.net']
        if any(mot in remarques.lower() for mot in mots_suspects):
            raise forms.ValidationError("Les liens ne sont pas autorisés dans les remarques")
        
        # Limiter la longueur
        if len(remarques) > max_length:
            raise forms.ValidationError(f"Les remarques ne peuvent pas dépasser {max_length} caractères")
        
        return remarques.strip()


# ═══════════════════════════════════════════════════
# 📝 FORMULAIRE DE DÉCLARATION D'ÉQUIPES
# ═══════════════════════════════════════════════════

class DeclarationForm(AntiSpamFormMixin, forms.ModelForm):
    """Formulaire de déclaration d'équipes pour un tournoi"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_honeypot()
    
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
                "placeholder": "Remarques éventuelles concernant cette déclaration (ceci est optionnel)",
                "rows": 3,
                "class": "form-control"
            }),
            "nombre_equipes": forms.NumberInput(attrs={
                "min": "1",
                "max": "10",
                "class": "form-control"
            })
        }
    
    def clean_date_tournoi(self):
        """Validation date tournoi"""
        date = self.cleaned_data["date_tournoi"]
        if date < timezone.now().date():
            raise forms.ValidationError("La date du tournoi ne peut pas être dans le passé.")
        return date
    
    def clean_declarant(self):
        """Validation du nom du déclarant - utilise le mixin"""
        declarant = self.cleaned_data.get('declarant', '')
        return self.validate_declarant(declarant)
    
    def clean_email_club(self):
        """Validation email - utilise le mixin"""
        email = self.cleaned_data.get('email_club', '')
        return self.validate_email(email)
    
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
        """Validation remarques - utilise le mixin"""
        remarques = self.cleaned_data.get('remarques', '')
        return self.validate_remarques(remarques, max_length=500)
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        
        # Vérification croisée : cohérence des données
        declarant = cleaned_data.get('declarant', '')
        email = cleaned_data.get('email_club', '')
        
        # Si l'email contient le nom du déclarant, c'est normal
        if declarant and email:
            nom_parties = declarant.lower().split()
            for partie in nom_parties:
                if len(partie) > 3 and partie in email.lower():
                    pass  # C'est normal, pas d'erreur
        
        return cleaned_data


# ═══════════════════════════════════════════════════
# 📋 FORMULAIRE DE CANDIDATURE À L'ORGANISATION
# ═══════════════════════════════════════════════════

class CandidatureForm(AntiSpamFormMixin, forms.ModelForm):
    """Formulaire pour qu'un club candidate à l'organisation d'un tournoi"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_honeypot()
    
    class Meta:
        model = Candidature
        fields = ['tournoi', 'club', 'declarant', 'email_contact', 'telephone_contact', 'lieu', 'remarques']
        widgets = {
            'tournoi': forms.HiddenInput(),  # Caché car déjà sélectionné
            'club': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'declarant': forms.TextInput(attrs={
                'placeholder': 'Exemple: Jean Dupont',
                'class': 'form-control',
                'required': True
            }),
            'email_contact': forms.EmailInput(attrs={
                'placeholder': 'votre.email@monclub.re',
                'class': 'form-control',
                'required': True
            }),
            'telephone_contact': forms.TextInput(attrs={
                'placeholder': '0692123456 (optionnel)',
                'class': 'form-control'
            }),
            'lieu': forms.TextInput(attrs={
                'placeholder': 'Exemple: Gymnase Municipal de Saint-Denis',
                'class': 'form-control',
                'required': True
            }),
            'remarques': forms.Textarea(attrs={
                'placeholder': 'Motivations, équipements disponibles, expérience... (optionnel)',
                'rows': 4,
                'class': 'form-control'
            })
        }
    
    def clean_declarant(self):
        """Validation du nom du déclarant - utilise le mixin"""
        declarant = self.cleaned_data.get('declarant', '')
        return self.validate_declarant(declarant)
    
    def clean_email_contact(self):
        """Validation email - utilise le mixin"""
        email = self.cleaned_data.get('email_contact', '')
        return self.validate_email(email)
    
    def clean_lieu(self):
        """Validation du lieu proposé"""
        lieu = self.cleaned_data.get('lieu', '')
        
        if len(lieu.strip()) < 5:
            raise forms.ValidationError("Le nom du lieu semble trop court")
        
        if len(lieu) > 200:
            raise forms.ValidationError("Le nom du lieu ne peut pas dépasser 200 caractères")
        
        # Détecter URLs (spam)
        mots_suspects = ['http://', 'https://', 'www.']
        if any(mot in lieu.lower() for mot in mots_suspects):
            raise forms.ValidationError("Les liens ne sont pas autorisés")
        
        return lieu.strip()
    
    def clean_remarques(self):
        """Validation remarques - utilise le mixin"""
        remarques = self.cleaned_data.get('remarques', '')
        return self.validate_remarques(remarques, max_length=1000)
    
    def clean(self):
        """Validation globale - vérifier unicité"""
        cleaned_data = super().clean()
        
        tournoi = cleaned_data.get('tournoi')
        club = cleaned_data.get('club')
        
        # Vérifier qu'une candidature n'existe pas déjà
        if tournoi and club:
            candidature_existante = Candidature.objects.filter(
                tournoi=tournoi,
                club=club
            ).exclude(
                statut='RETIREE'  # On peut recandidater si on a retiré
            ).first()
            
            if candidature_existante:
                raise forms.ValidationError(
                    f"Votre club a déjà candidaté pour ce tournoi. "
                    f"Statut actuel : {candidature_existante.get_statut_display()}"
                )
        
        return cleaned_data


# ═══════════════════════════════════════════════════
# 🗓️ FORMULAIRE TOURNOI (STAFF)
# ═══════════════════════════════════════════════════

class TournoiForm(AntiSpamFormMixin, forms.ModelForm):
    """
    Formulaire de création/modification de tournoi
    Réservé au staff uniquement
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_honeypot()
        
        # Rendre club_organisateur et lieu optionnels visuellement
        self.fields['club_organisateur'].required = False
        self.fields['lieu'].required = False
        self.fields['remarques'].required = False
    
    class Meta:
        model = Tournoi
        fields = [
            'date', 'categorie_age', 'sexe', 'zone',
            'statut', 'club_organisateur', 'lieu',
            'est_publie', 'remarques'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'categorie_age': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'sexe': forms.RadioSelect(),
            'zone': forms.Select(attrs={
                'class': 'form-control'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'club_organisateur': forms.Select(attrs={
                'class': 'form-control'
            }),
            'lieu': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Exemple: Gymnase Municipal de Saint-Denis'
            }),
            'est_publie': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'remarques': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Remarques internes (non visibles publiquement)'
            })
        }
        labels = {
            'date': 'Date du tournoi',
            'categorie_age': 'Catégorie d\'âge',
            'sexe': 'Sexe',
            'zone': 'Zone géographique',
            'statut': 'Statut',
            'club_organisateur': 'Club organisateur',
            'lieu': 'Lieu / Gymnase',
            'est_publie': 'Publié (visible publiquement)',
            'remarques': 'Remarques internes'
        }
        help_texts = {
            'date': 'Date à laquelle le tournoi aura lieu',
            'zone': 'Laisser vide si pas de zone spécifique',
            'club_organisateur': 'Sera défini lors de la validation d\'une candidature',
            'lieu': 'Sera défini lors de la validation d\'une candidature',
            'est_publie': 'Si décoché, seul le staff verra ce tournoi',
            'remarques': 'Notes internes (non visibles par le public)'
        }
    
    def clean_date(self):
        """Validation date tournoi"""
        date = self.cleaned_data.get('date')
        
        # Avertissement si date dans le passé (mais autorisé pour créer historique)
        if date and date < timezone.now().date():
            # On n'empêche pas, juste un warning via messages
            pass
        
        return date
    
    def clean_lieu(self):
        """Validation du lieu"""
        lieu = self.cleaned_data.get('lieu', '')
        
        if not lieu:  # Optionnel
            return ''
        
        if len(lieu.strip()) < 3:
            raise forms.ValidationError("Le nom du lieu semble trop court")
        
        if len(lieu) > 200:
            raise forms.ValidationError("Le nom du lieu ne peut pas dépasser 200 caractères")
        
        # Détecter URLs (spam)
        mots_suspects = ['http://', 'https://', 'www.']
        if any(mot in lieu.lower() for mot in mots_suspects):
            raise forms.ValidationError("Les liens ne sont pas autorisés")
        
        return lieu.strip()
    
    def clean_remarques(self):
        """Validation remarques - utilise le mixin"""
        remarques = self.cleaned_data.get('remarques', '')
        if not remarques:  # Optionnel
            return ''
        return self.validate_remarques(remarques, max_length=1000)
    
    def clean(self):
        """Validation globale - vérifier unicité"""
        cleaned_data = super().clean()
        
        date = cleaned_data.get('date')
        categorie_age = cleaned_data.get('categorie_age')
        sexe = cleaned_data.get('sexe')
        zone = cleaned_data.get('zone')
        
        # Vérifier qu'un tournoi identique n'existe pas déjà
        if date and categorie_age and sexe:
            tournois_existants = Tournoi.objects.filter(
                date=date,
                categorie_age=categorie_age,
                sexe=sexe,
                zone=zone if zone else ''
            )
            
            # Si on modifie, exclure le tournoi actuel
            if self.instance and self.instance.pk:
                tournois_existants = tournois_existants.exclude(pk=self.instance.pk)
            
            if tournois_existants.exists():
                raise forms.ValidationError(
                    f"Un tournoi identique existe déjà : "
                    f"{tournois_existants.first()}"
                )
        
        # Si un organisateur est défini, le lieu devrait l'être aussi
        club_org = cleaned_data.get('club_organisateur')
        lieu = cleaned_data.get('lieu')
        
        if club_org and not lieu:
            self.add_error('lieu', "Veuillez préciser le lieu si un organisateur est défini")
        
        return cleaned_data
