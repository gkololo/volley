/**
 * ═══════════════════════════════════════════════════
 * 🏐 GESTION DYNAMIQUE DES NOMS D'ÉQUIPES + POULES
 * Fichier : static/js/noms_equipes.js
 * Version : Approche 3 Hybride
 * ═══════════════════════════════════════════════════
 *
 * Fonctionnalités :
 * - Génère dynamiquement les champs nom pour chaque équipe
 * - Lit window.TOURNOIS_POULES pour afficher les selects de poule
 * - Adapte les options de poule selon le tournoi sélectionné
 * - Si tournoi sans poule → pas de select affiché
 * - Régénère les champs si le tournoi ou le nombre change
 */

document.addEventListener('DOMContentLoaded', function() {
    const nombreEquipesInput = document.getElementById('id_nombre_equipes');
    const clubSelect = document.getElementById('id_club');
    const tournoiSelect = document.getElementById('id_tournoi');
    const nomsEquipesContainer = document.getElementById('noms-equipes-container');

    if (!nombreEquipesInput || !nomsEquipesContainer) {
        console.warn('Éléments pour noms équipes non trouvés');
        return;
    }

    /**
     * Labels lisibles pour les poules
     */
    const POULES_LABELS = {
        'HAUTE': 'Poule Haute',
        'BASSE': 'Poule Basse',
        'UNIQUE': 'Poule Unique'
    };

    /**
     * Récupère les poules disponibles pour le tournoi actuellement sélectionné
     * @returns {Array} Liste des codes poule (ex: ['HAUTE', 'BASSE']) ou []
     */
    function getPoulesDisponibles() {
        if (!tournoiSelect || !window.TOURNOIS_POULES) {
            return [];
        }

        const tournoiId = tournoiSelect.value;
        if (!tournoiId) {
            return [];
        }

        // window.TOURNOIS_POULES est un objet { "tournoiId": ["HAUTE", "BASSE"], ... }
        return window.TOURNOIS_POULES[tournoiId] || [];
    }

    /**
     * Génère le HTML d'un select de poule pour une équipe
     * @param {number} index - Numéro de l'équipe (1, 2, 3...)
     * @param {Array} poules - Liste des poules disponibles
     * @returns {string} HTML du bloc poule
     */
    function genererSelectPoule(index, poules) {
        if (!poules || poules.length === 0) {
            return '';
        }

        let optionsHtml = '<option value="">— Aucune poule —</option>';
        poules.forEach(function(poule) {
            const label = POULES_LABELS[poule] || poule;
            optionsHtml += `<option value="${poule}">${label}</option>`;
        });

        return `
            <div class="poule-equipe-bloc">
                <label for="poule_equipe_${index}" class="poule-equipe-label">
                    🏆 Poule
                </label>
                <select 
                    id="poule_equipe_${index}" 
                    name="poule_equipe_${index}" 
                    class="form-control poule-equipe-select"
                    data-equipe="${index}"
                >
                    ${optionsHtml}
                </select>
            </div>
        `;
    }

    /**
     * Génère les champs de saisie des noms d'équipes (+ poules si applicable)
     */
    function genererChampsNoms() {
        const nombre = parseInt(nombreEquipesInput.value) || 0;
        const nomClub = clubSelect ? clubSelect.options[clubSelect.selectedIndex]?.text : 'Club';
        const poulesDisponibles = getPoulesDisponibles();
        const aDesPoules = poulesDisponibles.length > 0;

        // Vider le conteneur
        nomsEquipesContainer.innerHTML = '';

        if (nombre <= 0 || nombre > 10) {
            nomsEquipesContainer.style.display = 'none';
            nomsEquipesContainer.classList.remove('visible');
            return;
        }

        // Créer le titre de section
        const titre = document.createElement('div');
        titre.className = 'noms-equipes-titre';

        let sousTitre = 'Les noms sont pré-remplis. Vous pouvez les personnaliser ou les garder tels quels.';
        if (aDesPoules) {
            sousTitre += '<br><strong>🏆 Ce tournoi propose des poules — vous pouvez assigner chaque équipe à une poule.</strong>';
        }

        titre.innerHTML = `
            <h3>
                <span class="icon">🏐</span>
                Noms de vos ${nombre} équipe${nombre > 1 ? 's' : ''}
            </h3>
            <p class="help-text">${sousTitre}</p>
        `;
        nomsEquipesContainer.appendChild(titre);

        // Créer le conteneur de la grille
        const grille = document.createElement('div');
        grille.className = 'noms-equipes-grille';

        // Générer les champs
        for (let i = 1; i <= nombre; i++) {
            const champDiv = document.createElement('div');
            champDiv.className = 'nom-equipe-item';

            // Ajouter classe si poules actives (pour le CSS)
            if (aDesPoules) {
                champDiv.classList.add('avec-poule');
            }

            // Nom pré-rempli : "NomClub Équipe 1", "NomClub Équipe 2", etc.
            const nomParDefaut = `${nomClub} Équipe ${i}`;

            // HTML du select poule (vide si pas de poules)
            const pouleHtml = genererSelectPoule(i, poulesDisponibles);

            champDiv.innerHTML = `
                <label for="nom_equipe_${i}" class="nom-equipe-label">
                    <span class="numero-equipe">${i}</span>
                    Nom de l'équipe ${i} <span class="required">*</span>
                </label>
                <input 
                    type="text" 
                    id="nom_equipe_${i}" 
                    name="nom_equipe_${i}" 
                    class="form-control nom-equipe-input" 
                    value="${nomParDefaut}"
                    placeholder="${nomParDefaut}"
                    maxlength="100"
                    required
                    autocomplete="off"
                    data-club-initial="${nomClub}"
                >
                <small class="help-text">Ex: ${nomClub} ${i === 1 ? 'Masters' : i === 2 ? 'Juniors' : 'Équipe ' + String.fromCharCode(64 + i)}</small>
                ${pouleHtml}
            `;

            grille.appendChild(champDiv);
        }

        nomsEquipesContainer.appendChild(grille);

        // Afficher le conteneur avec animation
        nomsEquipesContainer.style.display = 'block';
        setTimeout(function() {
            nomsEquipesContainer.classList.add('visible');
        }, 10);

        // Attacher les événements de changement de poule (bordure colorée)
        if (aDesPoules) {
            attacherEvenementsPoule();
        }
    }

    /**
     * Attache les événements de changement sur les selects de poule
     * pour appliquer les bordures colorées
     */
    function attacherEvenementsPoule() {
        const selects = nomsEquipesContainer.querySelectorAll('.poule-equipe-select');
        selects.forEach(function(select) {
            select.addEventListener('change', function() {
                const item = this.closest('.nom-equipe-item');
                if (!item) return;

                // Retirer toutes les classes de poule
                item.classList.remove('poule-haute', 'poule-basse', 'poule-unique', 'poule-aucune');

                // Appliquer la classe selon la valeur
                const valeur = this.value;
                if (valeur === 'HAUTE') {
                    item.classList.add('poule-haute');
                } else if (valeur === 'BASSE') {
                    item.classList.add('poule-basse');
                } else if (valeur === 'UNIQUE') {
                    item.classList.add('poule-unique');
                } else {
                    item.classList.add('poule-aucune');
                }
            });
        });
    }

    /**
     * Mettre à jour les noms pré-remplis si le club change
     */
    function mettreAJourNomsParDefaut() {
        const nombre = parseInt(nombreEquipesInput.value) || 0;
        const nomClub = clubSelect ? clubSelect.options[clubSelect.selectedIndex]?.text : 'Club';

        for (let i = 1; i <= nombre; i++) {
            const input = document.getElementById(`nom_equipe_${i}`);
            if (input) {
                // Ne mettre à jour que si le champ a encore sa valeur par défaut
                const ancienClub = input.getAttribute('data-club-initial');
                if (!ancienClub || input.value.startsWith(ancienClub)) {
                    const nouveauNom = `${nomClub} Équipe ${i}`;
                    input.value = nouveauNom;
                    input.setAttribute('placeholder', nouveauNom);
                    input.setAttribute('data-club-initial', nomClub);
                }
            }
        }
    }

    // ═══════════════════════════════════════════════════
    // 🎯 ÉVÉNEMENTS
    // ═══════════════════════════════════════════════════

    // Nombre d'équipes change → régénérer
    nombreEquipesInput.addEventListener('change', genererChampsNoms);
    nombreEquipesInput.addEventListener('input', genererChampsNoms);

    // Club change → mettre à jour les noms pré-remplis
    if (clubSelect) {
        clubSelect.addEventListener('change', function() {
            const nombre = parseInt(nombreEquipesInput.value) || 0;
            if (nombre > 0) {
                mettreAJourNomsParDefaut();
            }
        });
    }

    // 🆕 Tournoi change → régénérer (les poules peuvent changer)
    if (tournoiSelect) {
        tournoiSelect.addEventListener('change', function() {
            const nombre = parseInt(nombreEquipesInput.value) || 0;
            if (nombre > 0) {
                genererChampsNoms();
            }
        });
    }

    // Générer au chargement si un nombre est déjà défini
    if (nombreEquipesInput.value) {
        genererChampsNoms();
    }

    // ═══════════════════════════════════════════════════
    // ✅ VALIDATION EN TEMPS RÉEL
    // ═══════════════════════════════════════════════════

    nomsEquipesContainer.addEventListener('input', function(e) {
        if (e.target.classList.contains('nom-equipe-input')) {
            const input = e.target;
            const valeur = input.value.trim();

            // Retirer les classes de validation
            input.classList.remove('input-valide', 'input-invalide');

            // Validation
            if (valeur.length === 0) {
                input.classList.add('input-invalide');
            } else if (valeur.length < 2) {
                input.classList.add('input-invalide');
            } else if (valeur.length > 100) {
                input.classList.add('input-invalide');
            } else {
                input.classList.add('input-valide');
            }
        }
    });

    // ═══════════════════════════════════════════════════
    // 🛡️ VALIDATION AVANT SOUMISSION
    // ═══════════════════════════════════════════════════

    const form = nombreEquipesInput.closest('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const nombre = parseInt(nombreEquipesInput.value) || 0;
            let erreurs = [];

            for (let i = 1; i <= nombre; i++) {
                const input = document.getElementById(`nom_equipe_${i}`);
                if (input) {
                    const valeur = input.value.trim();
                    if (!valeur) {
                        erreurs.push(`Le nom de l'équipe ${i} est obligatoire`);
                        input.classList.add('input-invalide');
                    }
                }
            }

            if (erreurs.length > 0) {
                e.preventDefault();
                alert('Erreur de validation :\n\n' + erreurs.join('\n'));

                // Scroller vers le premier champ en erreur
                const premierErreur = document.querySelector('.input-invalide');
                if (premierErreur) {
                    premierErreur.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    premierErreur.focus();
                }
            }
        });
    }
});
