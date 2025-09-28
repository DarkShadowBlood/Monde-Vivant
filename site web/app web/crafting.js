document.addEventListener('DOMContentLoaded', () => {
    const charNameEl = document.getElementById('char-name');
    const currencyShardsEl = document.getElementById('currency-shards');
    const currencyGemsEl = document.getElementById('currency-gems');
    const itemComponentsEl = document.getElementById('item-components');
    const recipesListEl = document.getElementById('recipes-list');
    const craftingStatusEl = document.getElementById('crafting-status');

    let activeCharacterName = 'Varkis';
    let recipes = [];
    let characterInventory = {};

    async function loadData() {
        try {
            const activeCharButton = document.querySelector('.character-selector button.active');
            if (activeCharButton) activeCharacterName = activeCharButton.dataset.char;

            charNameEl.textContent = `Atelier de ${activeCharacterName}`;

            const [recipesRes, inventoryRes] = await Promise.all([
                fetch('crafting_recipes.json'),
                fetch(`/api/gamification/inventory?character=${activeCharacterName}`)
            ]);

            if (!recipesRes.ok) throw new Error("Les recettes n'ont pas pu être chargées.");
            recipes = await recipesRes.json();

            if (inventoryRes.ok) {
                const inventoryResult = await inventoryRes.json();
                characterInventory = inventoryResult.success ? inventoryResult.data : {};
            } else {
                characterInventory = {};
            }

            updateUI();

        } catch (error) {
            console.error("Erreur de chargement des données d'artisanat:", error);
            recipesListEl.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    }

    function updateUI() {
        // Mettre à jour les matériaux
        currencyShardsEl.textContent = (characterInventory.currencies?.steel_shards || 0).toLocaleString('fr-FR');
        currencyGemsEl.textContent = (characterInventory.currencies?.soul_gems || 0).toLocaleString('fr-FR');
        itemComponentsEl.textContent = (characterInventory.items?.ancient_components || 0).toLocaleString('fr-FR');

        // Afficher les recettes
        recipesListEl.innerHTML = '';
        recipes.forEach(recipe => {
            const canCraft = checkCanCraft(recipe);
            const costsHtml = Object.entries(recipe.cost).map(([material, amount]) => {
                const materialName = {
                    'steel_shards': "Éclats d'Acier",
                    'soul_gems': "Gemmes d'Âme",
                    'ancient_components': "Composants Anciens"
                }[material] || material;
                return `<li>${amount} ${materialName}</li>`;
            }).join('');

            const recipeEl = document.createElement('div');
            recipeEl.className = `recipe-card ${canCraft ? '' : 'disabled'}`;
            recipeEl.innerHTML = `
                <div class="recipe-icon">${recipe.icon}</div>
                <div class="recipe-details">
                    <h3>${recipe.name}</h3>
                    <p>${recipe.description}</p>
                    <ul class="recipe-cost">
                        ${costsHtml}
                    </ul>
                </div>
                <button class="craft-btn" data-recipe-id="${recipe.id}" ${!canCraft ? 'disabled' : ''}>Fabriquer</button>
            `;
            recipesListEl.appendChild(recipeEl);
        });
    }

    function checkCanCraft(recipe) {
        return Object.entries(recipe.cost).every(([material, amount]) => {
            const userAmount = (characterInventory.currencies?.[material] || characterInventory.items?.[material] || 0);
            return userAmount >= amount;
        });
    }

    async function handleCraft(recipeId) {
        const recipe = recipes.find(r => r.id === recipeId);
        if (!recipe) {
            showStatus("Recette non trouvée.", true);
            return;
        }

        if (!checkCanCraft(recipe)) {
            showStatus("Matériaux insuffisants.", true);
            return;
        }

        try {
            const response = await fetch('/api/gamification/craft', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    character: activeCharacterName,
                    recipe_id: recipeId
                })
            });

            const result = await response.json();
            if (response.ok && result.success) {
                showStatus(`Vous avez fabriqué : ${recipe.name} !`);
                // Recharger les données pour mettre à jour l'inventaire et les recettes
                loadData();
            } else {
                throw new Error(result.error || "Erreur inconnue du serveur.");
            }
        } catch (error) {
            console.error("Erreur lors de la fabrication:", error);
            showStatus(`Erreur: ${error.message}`, true);
        }
    }

    function showStatus(message, isError = false) {
        craftingStatusEl.textContent = message;
        craftingStatusEl.style.color = isError ? '#ef5350' : '#66bb6a';
        craftingStatusEl.style.display = 'block';
        setTimeout(() => {
            craftingStatusEl.style.display = 'none';
        }, 4000);
    }

    recipesListEl.addEventListener('click', (e) => {
        if (e.target.classList.contains('craft-btn')) {
            handleCraft(e.target.dataset.recipeId);
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