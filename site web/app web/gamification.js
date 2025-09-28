document.addEventListener('DOMContentLoaded', () => {
    const charNameEl = document.getElementById('char-name');
    const charLevelEl = document.getElementById('char-level');
    const charRankEl = document.getElementById('char-rank');
    const xpValuesEl = document.getElementById('xp-values');
    const xpProgressEl = document.getElementById('xp-progress');
    const statsListEl = document.getElementById('stats-list');
    const selectorButtons = document.querySelectorAll('.character-selector button');
    const passiveSkillContainer = document.getElementById('passive-skill-container');
    const passiveSkillNameEl = document.getElementById('passive-skill-name');
    const passiveSkillDescEl = document.getElementById('passive-skill-desc');
    const currencyShardsEl = document.getElementById('currency-shards');
    const currencyGemsEl = document.getElementById('currency-gems');
    const giftMessageContainer = document.getElementById('gift-message-container');
    const giftMessageEl = document.getElementById('gift-message');


    const statTranslations = {
        force: 'Force',
        endurance: 'Endurance',
        agilité: 'Agilité',
        volonté: 'Volonté',
        instinct: 'Instinct'
    };

    async function fetchProfile(characterName) {
        try {
            const response = await fetch(`/api/gamification/profile?character=${characterName}`);
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            const result = await response.json();
            if (result.success) {
                updateUI(result.data);
            } else {
                console.error("Erreur API:", result.error);
                charNameEl.textContent = "Erreur";
            }
        } catch (error) {
            console.error("Impossible de charger le profil:", error);
            charNameEl.textContent = "Erreur de connexion";
        }
    }

    function updateUI(profile) {
        charNameEl.textContent = profile.name;
        charLevelEl.textContent = profile.level;
        charRankEl.textContent = profile.rank;
        xpValuesEl.textContent = `${profile.xp} / ${profile.xp_to_next_level}`;
        
        const xpPercentage = (profile.xp / profile.xp_to_next_level) * 100;
        xpProgressEl.style.width = `${xpPercentage}%`;

        statsListEl.innerHTML = '';
        for (const [stat, value] of Object.entries(profile.stats)) {
            const li = document.createElement('li');
            const translatedStat = statTranslations[stat] || stat.charAt(0).toUpperCase() + stat.slice(1);
            li.innerHTML = `<strong>${translatedStat}</strong><span>${value}</span>`;
            statsListEl.appendChild(li);
        }

        if (profile.passive_skill) {
            passiveSkillNameEl.textContent = profile.passive_skill.name;
            passiveSkillDescEl.textContent = profile.passive_skill.description;
            passiveSkillContainer.style.display = 'block';
        } else {
            passiveSkillContainer.style.display = 'none';
        }

        if (profile.currencies) {
            currencyShardsEl.textContent = profile.currencies.steel_shards.toLocaleString('fr-FR');
            currencyGemsEl.textContent = profile.currencies.soul_gems.toLocaleString('fr-FR');
        }

        if (profile.gift_message) {
            giftMessageEl.textContent = profile.gift_message;
            giftMessageContainer.style.display = 'block';
        } else {
            giftMessageContainer.style.display = 'none';
        }
    }

    selectorButtons.forEach(button => {
        button.addEventListener('click', () => {
            selectorButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            const char = button.dataset.char;
            fetchProfile(char);
        });
    });

    // Charger le profil du personnage par défaut (Varkis) au démarrage
    fetchProfile('Varkis');
});