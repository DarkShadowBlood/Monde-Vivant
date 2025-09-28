document.addEventListener('DOMContentLoaded', () => {
    const unclaimedLootList = document.getElementById('unclaimed-loot-list');
    const lootModal = document.getElementById('loot-modal');
    const closeLootModalBtn = document.getElementById('close-loot-modal');
    const lootResultsList = document.getElementById('loot-results');

    let allActivities = [];
    let characterData = {};
    let characterProfile = {}; // Pour stocker le profil complet avec les stats
    let activeCharacterName = 'Varkis'; // Personnage par défaut

    // Fonction pour charger les données nécessaires
    async function loadData() {
        try {
            // Déterminer le personnage actif AVANT les fetchs
            const activeCharButton = document.querySelector('.character-selector button.active');
            if (activeCharButton) activeCharacterName = activeCharButton.dataset.char;

            const [activitiesRes, characterDataRes, profileRes] = await Promise.all([
                fetch('activities.json'),
                fetch('gamification_data.json'), // Fichier des monnaies/butins réclamés
                fetch(`/api/gamification/profile?character=${activeCharacterName}`) // Profil complet avec stats
            ]);
            allActivities = await activitiesRes.json();

            // Gérer le cas où gamification_data.json n'existe pas (404)
            if (characterDataRes.ok) {
                characterData = await characterDataRes.json();
            } else {
                characterData = {}; // Initialiser avec un objet vide si le fichier n'existe pas
            }

            // Gérer le profil du personnage
            if (profileRes.ok) {
                const profileResult = await profileRes.json();
                characterProfile = profileResult.success ? profileResult.data : {};
            } else {
                characterProfile = {};
            }
            
            displayUnclaimedLoot();
        } catch (error) {
            console.error("Erreur de chargement des données pour le système de butin:", error);
            unclaimedLootList.innerHTML = '<li>Erreur de chargement des activités.</li>';
        }
    }

    // Affiche les activités qui n'ont pas encore de butin réclamé
    function displayUnclaimedLoot() {
        unclaimedLootList.innerHTML = '';
        // S'assurer que characterData a bien la structure attendue
        const claimedLootForChar = characterData[activeCharacterName]?.claimed_loot || [];

        const unclaimedActivities = allActivities
            .filter(act => !claimedLootForChar.includes(act.html_file))
            .sort((a, b) => new Date(b.date) - new Date(a.date)) // Plus récentes en premier
            .slice(0, 5); // Limite à 5 pour ne pas surcharger

        if (unclaimedActivities.length === 0) {
            unclaimedLootList.innerHTML = '<li>Aucun nouveau butin à réclamer.</li>';
            return;
        }

        unclaimedActivities.forEach(activity => {
            const li = document.createElement('li');
            li.className = 'loot-item';
            li.innerHTML = `
                <span>${new Date(activity.date).toLocaleDateString('fr-FR')} - ${activity.type}</span>
                <button class="claim-loot-btn" data-activity-id="${activity.html_file}">Récupérer le butin</button>
            `;
            unclaimedLootList.appendChild(li);
        });
    }

    // Génère un objet de butin structuré avec une logique améliorée
    function generateLoot(activityId) {
        const activity = allActivities.find(act => act.html_file === activityId);
        if (!activity) return null;

        const stats = characterProfile.stats || { instinct: 0, volonté: 0 };
        const instinctBonus = (stats.instinct || 0) * 0.01; // Chaque point d'instinct = +1% de chance

        // Structure de butin améliorée pour distinguer monnaies et objets
        const loot = {
            currencies: {
                steel_shards: 0,
                soul_gems: 0,
            },
            items: {}
        };

        // --- Monnaies de base (Éclats d'Acier) ---
        const calories = parseInt(activity.calories, 10) || 0;
        const distance = parseFloat(activity.distance) || 0;
        const shardsFound = Math.floor(calories / 25) + Math.floor(distance * 2); // Basé sur calories et distance
        if (shardsFound > 0) {
            loot.currencies.steel_shards = shardsFound;
        }

        // --- Monnaie rare (Gemmes d'Âme) ---
        // Chance de base + bonus de performance + bonus de stat
        let gemChance = 0.05 + instinctBonus; // 5% de chance de base + bonus d'instinct
        if (calories > 600) gemChance += 0.05; // +5% si grosse dépense
        if (distance > 10) gemChance += 0.05; // +5% si longue distance
        if (Math.random() < gemChance) {
            loot.currencies.soul_gems = 1;
        }

        // --- Objets d'artisanat (Composants Anciens) ---
        // Chance de base + bonus de stat (Volonté, pour la persévérance)
        const componentChance = 0.15 + ((stats.volonté || 0) * 0.01); // 15% de chance de base
        if (Math.random() < componentChance) {
            loot.items['ancient_components'] = (loot.items['ancient_components'] || 0) + (Math.floor(Math.random() * 3) + 1);
        }

        // --- Objets de quête (Fragments de Carte) ---
        // Chance très faible, augmentée par l'instinct
        const mapFragmentChance = 0.02 + instinctBonus; // 2% de chance de base
        if (Math.random() < mapFragmentChance) {
            loot.items['map_fragments'] = (loot.items['map_fragments'] || 0) + 1;
        }

        // --- NOUVEAU: Objets consommables (Potions) ---
        const potionChance = 0.08 + instinctBonus; // 8% de chance de base
        if (activity.type === 'course' && Math.random() < potionChance) {
            loot.items['stamina_potion_1'] = (loot.items['stamina_potion_1'] || 0) + 1;
        }

        // Ne retourne un objet que si au moins une récompense a été trouvée
        const totalCurrencies = Object.values(loot.currencies).reduce((a, b) => a + b, 0);
        const totalItems = Object.values(loot.items).reduce((a, b) => a + b, 0);
        if (totalCurrencies === 0 && totalItems === 0) {
            return null;
        }

        return loot;
    }

    // Gère le clic sur le bouton "Récupérer le butin"
    unclaimedLootList.addEventListener('click', (e) => {
        if (e.target.classList.contains('claim-loot-btn')) {
            const button = e.target;
            const activityId = button.dataset.activityId;
            
            const lootObject = generateLoot(activityId);
            
            if (lootObject) {
                // Formate le butin pour l'affichage dans la modale
                const lootForDisplay = [];
                if (lootObject.currencies?.steel_shards > 0) lootForDisplay.push(`<li>⚙️ ${lootObject.currencies.steel_shards} Éclats d'Acier</li>`);
                if (lootObject.currencies?.soul_gems > 0) lootForDisplay.push(`<li>💎 ${lootObject.currencies.soul_gems} Gemme d'Âme</li>`);
                
                if (lootObject.items?.ancient_components > 0) lootForDisplay.push(`<li>🔩 ${lootObject.items.ancient_components} Composant(s) Ancien(s)</li>`);
                if (lootObject.items?.map_fragments > 0) lootForDisplay.push(`<li>🗺️ ${lootObject.items.map_fragments} Fragment(s) de Carte</li>`);
                if (lootObject.items?.stamina_potion_1 > 0) lootForDisplay.push(`<li>🧪 ${lootObject.items.stamina_potion_1} Potion d'Endurance Mineure</li>`);
                
                lootResultsList.innerHTML = lootForDisplay.join('');
                lootModal.style.display = 'flex';

                // Envoie le butin au serveur pour sauvegarde
                saveLootToServer(activityId, lootObject, button);

            } else {
                alert("Aucun butin trouvé pour cette activité.");
                // Marquer comme réclamé même si vide pour ne pas le reproposer
                saveLootToServer(activityId, {}, button);
            }
        }
    });

    // Fonction pour envoyer le butin au serveur
    async function saveLootToServer(activityId, lootObject, buttonElement) {
        try {
            const response = await fetch('/api/gamification/claim-loot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    character: activeCharacterName,
                    activity_id: activityId,
                    loot: lootObject
                })
            });

            const result = await response.json();
            if (response.ok && result.success) {
                console.log("Butin sauvegardé avec succès !");
                buttonElement.closest('.loot-item').remove(); // Retire l'élément de la liste

                // Mettre à jour l'affichage des monnaies en temps réel
                if (result.updated_currencies) {
                    const currencyShardsEl = document.getElementById('currency-shards');
                    const currencyGemsEl = document.getElementById('currency-gems');
                    if (currencyShardsEl) currencyShardsEl.textContent = (result.updated_currencies.steel_shards || 0).toLocaleString('fr-FR');
                    if (currencyGemsEl) currencyGemsEl.textContent = (result.updated_currencies.soul_gems || 0).toLocaleString('fr-FR');
                }
            } else {
                throw new Error(result.error || "Erreur inconnue du serveur.");
            }
        } catch (error) {
            console.error("Erreur lors de la sauvegarde du butin:", error);
            alert("Une erreur est survenue lors de la réclamation du butin. Veuillez réessayer.");
        }
    }

    // Ferme la modale
    closeLootModalBtn.addEventListener('click', () => {
        lootModal.style.display = 'none';
    });

    // Lancement
    loadData();

    // Met à jour le personnage actif si l'utilisateur le change
    document.querySelector('.character-selector').addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON') {
            activeCharacterName = e.target.dataset.char;
            loadData(); // Recharge les données pour le nouveau personnage
        }
    });
});