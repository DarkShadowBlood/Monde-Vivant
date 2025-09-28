document.addEventListener('DOMContentLoaded', () => {
    const questsListEl = document.getElementById('daily-quests-list');
    const weeklyQuestsListEl = document.getElementById('weekly-quests-list');
    const questStatusEl = document.getElementById('quest-status');
    let activeCharacterName = 'Varkis';
    let dailyQuestsDefinitions = [];
    let weeklyQuestsDefinitions = [];

    async function loadAllQuests() {
        try {
            const activeCharButton = document.querySelector('.character-selector button.active');
            if (activeCharButton) activeCharacterName = activeCharButton.dataset.char;

            const [questsDefRes, questStatusRes] = await Promise.all([
                fetch('daily_quests.json'),
                fetch(`/api/gamification/quests?character=${activeCharacterName}`)
            ]);

            if (!questsDefRes.ok) throw new Error("Les définitions de quêtes n'ont pas pu être chargées.");
            dailyQuestsDefinitions = await questsDefRes.json();

            if (!questStatusRes.ok) throw new Error("Le statut des quêtes n'a pas pu être chargé.");
            const statusResult = await questStatusRes.json();
            const questsStatus = statusResult.success ? statusResult.data : {};

            // Charger et afficher les quêtes journalières et hebdomadaires
            updateQuestsUI(questsListEl, dailyQuestsDefinitions, questsStatus.daily);
            updateQuestsUI(weeklyQuestsListEl, weeklyQuestsDefinitions, questsStatus.weekly);

        } catch (error) {
            console.error("Erreur de chargement des quêtes:", error);
            questsListEl.innerHTML = `<p style="color: red;">${error.message}</p>`;
            weeklyQuestsListEl.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    }

    // Fonction générique pour afficher n'importe quel type de quête
    function updateQuestsUI(containerEl, definitions, statuses) {
        containerEl.innerHTML = '';
        if (!definitions || definitions.length === 0) {
            containerEl.innerHTML = '<p>Aucune quête disponible pour le moment.</p>';
            return;
        }

        if (!statuses) {
            containerEl.innerHTML = '<p>Statut des quêtes non disponible.</p>';
            return;
        }

        definitions.forEach(quest => {
            const status = statuses[quest.id] || { progress: 0, completed: false, claimed: false, type: 'daily' };
            const progressPercent = Math.min((status.progress / quest.objective.target) * 100, 100);

            const questEl = document.createElement('div');
            questEl.className = 'quest-item';
            if (status.claimed) questEl.classList.add('claimed');

            const progressValue = quest.objective.type === 'distance' ? status.progress.toFixed(1) : Math.floor(status.progress);

            questEl.innerHTML = `
                <div class="quest-details">
                    <h4>${quest.title}</h4>
                    <p>${quest.description}</p>
                    <div class="quest-progress-bar">
                        <div class="quest-progress" style="width: ${progressPercent}%;"></div>
                    </div>
                    <span class="progress-text">${progressValue} / ${quest.objective.target}</span>
                </div>
                <button class="claim-quest-btn" data-quest-id="${quest.id}" ${!status.completed || status.claimed ? 'disabled' : ''}>
                    ${status.claimed ? 'Réclamé' : 'Réclamer'}
                </button>
            `;
            containerEl.appendChild(questEl);
        });
    }

    async function handleClaimQuest(questId) {
        try {
            const response = await fetch('/api/gamification/claim-quest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    character: activeCharacterName,
                    quest_id: questId
                })
            });

            const result = await response.json();
            if (response.ok && result.success) {
                showStatus(result.message || 'Récompense réclamée !');
                loadAllQuests(); // Recharger pour mettre à jour l'UI
                // On pourrait aussi vouloir rafraîchir les monnaies sur la page
                if (window.loadProfile) window.loadProfile();
            } else {
                throw new Error(result.error || "Erreur inconnue du serveur.");
            }
        } catch (error) {
            console.error("Erreur lors de la réclamation de la quête:", error);
            showStatus(`Erreur: ${error.message}`, true);
        }
    }

    function showStatus(message, isError = false) {
        questStatusEl.textContent = message;
        questStatusEl.style.color = isError ? '#ef5350' : '#66bb6a';
        questStatusEl.style.display = 'block';
        setTimeout(() => {
            questStatusEl.style.display = 'none';
        }, 4000);
    }

    document.querySelector('.quests-section').addEventListener('click', (e) => {
        if (e.target.classList.contains('claim-quest-btn')) {
            handleClaimQuest(e.target.dataset.questId);
        }
    });

    // Recharger les quêtes quand le personnage change
    document.querySelector('.character-selector').addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON' && !e.target.classList.contains('active')) {
            // Le script principal (gamification.js) gère déjà le changement de personnage
            // et recharge le profil. On peut écouter cet événement ou simplement recharger ici aussi.
            setTimeout(loadAllQuests, 50); // Petit délai pour s'assurer que le personnage actif est bien mis à jour
        }
    });

    // Exposer la fonction de chargement pour qu'elle puisse être appelée par gamification.js
    window.loadQuests = loadAllQuests;

    // Chargement initial
    loadAllQuests();
});