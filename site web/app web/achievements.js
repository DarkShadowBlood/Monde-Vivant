document.addEventListener('DOMContentLoaded', () => {
    const charNameEl = document.getElementById('char-name');
    const unlockedListEl = document.getElementById('unlocked-achievements-list');
    const lockedListEl = document.getElementById('locked-achievements-list');
    const statusEl = document.getElementById('achievement-status');

    let activeCharacterName = 'Varkis';
    let achievementDefinitions = [];

    async function loadData() {
        try {
            const activeCharButton = document.querySelector('.character-selector button.active');
            if (activeCharButton) activeCharacterName = activeCharButton.dataset.char;

            charNameEl.textContent = `Hauts Faits de ${activeCharacterName}`;

            const [defsRes, statusRes] = await Promise.all([
                fetch('achievements_definitions.json'),
                fetch(`/api/gamification/achievements?character=${activeCharacterName}`)
            ]);

            if (!defsRes.ok) throw new Error("Les définitions de hauts faits n'ont pas pu être chargées.");
            achievementDefinitions = await defsRes.json();

            if (!statusRes.ok) throw new Error("Le statut des hauts faits n'a pas pu être chargé.");
            const statusResult = await statusRes.json();
            const achievementsStatus = statusResult.success ? statusResult.data : {};

            updateUI(achievementsStatus);

        } catch (error) {
            console.error("Erreur de chargement des hauts faits:", error);
            unlockedListEl.innerHTML = `<p style="color: red;">${error.message}</p>`;
            lockedListEl.innerHTML = '';
        }
    }

    function updateUI(statuses) {
        unlockedListEl.innerHTML = '';
        lockedListEl.innerHTML = '';

        achievementDefinitions.forEach(ach => {
            const status = statuses[ach.id] || { unlocked: false, claimed: false };
            const cardHtml = `
                <div class="achievement-icon">${ach.icon}</div>
                <div class="achievement-details">
                    <h3>${ach.title}</h3>
                    <p>${ach.description}</p>
                </div>
                ${status.unlocked ? `<button class="claim-btn" data-achievement-id="${ach.id}" ${status.claimed ? 'disabled' : ''}>${status.claimed ? 'Réclamé' : 'Réclamer'}</button>` : ''}
            `;

            const cardEl = document.createElement('div');
            cardEl.className = 'achievement-card';

            if (status.unlocked) {
                if (status.claimed) cardEl.classList.add('claimed');
                cardEl.innerHTML = cardHtml;
                unlockedListEl.appendChild(cardEl);
            } else {
                cardEl.classList.add('locked');
                cardEl.innerHTML = cardHtml;
                lockedListEl.appendChild(cardEl);
            }
        });

        if (unlockedListEl.innerHTML === '') {
            unlockedListEl.innerHTML = '<p>Aucun haut fait débloqué pour le moment. Continuez vos efforts !</p>';
        }
    }

    async function handleClaim(achievementId) {
        try {
            const response = await fetch('/api/gamification/claim-achievement', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    character: activeCharacterName,
                    achievement_id: achievementId
                })
            });

            const result = await response.json();
            if (response.ok && result.success) {
                showStatus(result.message || 'Récompense réclamée !');
                loadData(); // Recharger pour mettre à jour l'UI
            } else {
                throw new Error(result.error || "Erreur inconnue du serveur.");
            }
        } catch (error) {
            console.error("Erreur lors de la réclamation:", error);
            showStatus(`Erreur: ${error.message}`, true);
        }
    }

    function showStatus(message, isError = false) {
        statusEl.textContent = message;
        statusEl.style.color = isError ? '#ef5350' : '#66bb6a';
        statusEl.style.display = 'block';
        setTimeout(() => {
            statusEl.style.display = 'none';
        }, 4000);
    }

    document.body.addEventListener('click', (e) => {
        if (e.target.classList.contains('claim-btn')) {
            handleClaim(e.target.dataset.achievementId);
        }
    });

    document.querySelector('.character-selector').addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON' && !e.target.classList.contains('active')) {
            document.querySelector('.character-selector button.active').classList.remove('active');
            e.target.classList.add('active');
            activeCharacterName = e.target.dataset.char;
            loadData();
        }
    });

    loadData();
});