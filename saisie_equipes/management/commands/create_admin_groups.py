# saisie_equipes/management/commands/create_admin_groups.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps


class Command(BaseCommand):
    help = 'Crée les groupes d\'admins volleyball avec les permissions appropriées'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-user',
            type=str,
            help='Créer un nouvel utilisateur admin avec ce nom d\'utilisateur',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin.volley@example.com',
            help='Email pour le nouvel utilisateur',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Mot de passe pour le nouvel utilisateur (si non fourni, sera demandé)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('🏐 Configuration des groupes d\'admins volleyball...'))

        # 1. Créer le groupe "Admins Volleyball"
        group, created = Group.objects.get_or_create(name='Admins Volleyball')

        if created:
            self.stdout.write(self.style.SUCCESS('✅ Groupe "Admins Volleyball" créé'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Groupe "Admins Volleyball" existe déjà'))

        # 2. Découvrir automatiquement tous les modèles de saisie_equipes
        app = apps.get_app_config('saisie_equipes')
        models_volleyball = app.get_models()

        self.stdout.write(f'📋 Modèles trouvés: {[model.__name__ for model in models_volleyball]}')

        permissions_added = 0

        for model in models_volleyball:
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(content_type=content_type)

            for perm in permissions:
                if not group.permissions.filter(id=perm.id).exists():
                    group.permissions.add(perm)
                    permissions_added += 1
                    self.stdout.write(
                        f'  ➕ Permission ajoutée: {perm.name} pour {model.__name__}'
                    )

        self.stdout.write(
            self.style.SUCCESS(f'✅ {permissions_added} permissions ajoutées au groupe')
        )

        # 3. Créer un utilisateur si demandé
        if options['create_user']:
            username = options['create_user']
            email = options['email']

            # Vérifier si l'utilisateur existe déjà
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.ERROR(f'❌ L\'utilisateur "{username}" existe déjà')
                )
                return

            # Demander le mot de passe si non fourni
            password = options['password']
            if not password:
                from getpass import getpass
                password = getpass('Mot de passe pour le nouvel admin: ')
                password_confirm = getpass('Confirmer le mot de passe: ')

                if password != password_confirm:
                    self.stdout.write(self.style.ERROR('❌ Les mots de passe ne correspondent pas'))
                    return

            # Créer l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.is_staff = True  # Accès à l'admin Django
            user.save()

            # Ajouter au groupe
            user.groups.add(group)

            self.stdout.write(
                self.style.SUCCESS(f'✅ Utilisateur admin "{username}" créé et ajouté au groupe')
            )
            self.stdout.write(
                self.style.HTTP_INFO(f'📧 Email: {email}')
            )

        # 4. Résumé des permissions
        self.stdout.write(self.style.HTTP_INFO('\n📋 Résumé des permissions du groupe "Admins Volleyball":'))

        for model in models_volleyball:
            self.stdout.write(f'  🏐 {model.__name__}:')
            content_type = ContentType.objects.get_for_model(model)
            model_permissions = group.permissions.filter(content_type=content_type)

            for perm in model_permissions:
                action = perm.codename.split('_')[0]
                action_fr = {
                    'add': 'Ajouter',
                    'change': 'Modifier',
                    'delete': 'Supprimer',
                    'view': 'Voir'
                }.get(action, action)
                self.stdout.write(f'    ✓ {action_fr}')

        self.stdout.write(self.style.SUCCESS('\n🎉 Configuration terminée avec succès !'))
