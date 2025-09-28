document.addEventListener('DOMContentLoaded', () => {
    const charNameEl = document.getElementById('char-name');
    const currencyShardsEl = document.getElementById('currency-shards');
    const currencyGemsEl = document.getElementById('currency-gems');
    const sellableItemsListEl = document.getElementById('sellable-items-list');
    const buyableItemsListEl = document.getElementById('buyable-items-list');
    const merchantStatusEl = document.getElementById('merchant-status');

    let activeCharacterName = 'Varkis';
    let itemDefinitions = {};
    let merchantWares = [];

    async function loadData() {
        try {
            const activeCharButton = document.querySelector('.character-selector button.active');
            if (activeCharButton) activeCharacterName = activeCharButton.dataset.char;

            charNameEl.textContent = `Échoppe du Marchand`;

            const [inventoryRes, itemsDefRes, waresRes] = await Promise.all([
                fetch(`/api/gamification/inventory?character=${activeCharacterName}`),
                fetch('items_definitions.json'),
                fetch('merchant_wares.json')
            ]);

            if (!inventoryRes.ok) throw new Error("L'inventaire n'a pas pu être chargé.");
            if (!itemsDefRes.ok) throw new Error("Les définitions d'objets n'ont pas pu être chargées.");
            
            const inventoryResult = await inventoryRes.json();
            const characterInventory = inventoryResult.success ? inventoryResult.data : {};
            itemDefinitions = await itemsDefRes.json();
            
            if (!waresRes.ok) throw new Error("Le stock du marchand n'a pas pu être chargé.");
            merchantWares = await waresRes.json();

            updateUI(characterInventory);

        } catch (error) {
            console.error("Erreur de chargement des données du marchand:", error);
            sellableItemsListEl.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    }

    function updateUI(inventory) {
        currencyShardsEl.textContent = (inventory.currencies?.steel_shards || 0).toLocaleString('fr-FR');
        currencyGemsEl.textContent = (inventory.currencies?.soul_gems || 0).toLocaleString('fr-FR');

        // --- Section Vente ---
        sellableItemsListEl.innerHTML = '';
        const playerItems = inventory.items || {};
        let hasSellableItems = false;

        for (const [itemId, quantity] of Object.entries(playerItems)) {
            const itemDef = itemDefinitions[itemId];
            if (quantity > 0 && itemDef && itemDef.sell_price) {
                hasSellableItems = true;
                const itemEl = document.createElement('div');
                itemEl.className = 'item-card';
                itemEl.innerHTML = `
                    <div class="item-icon">${itemDef.icon}</div>
                    <div class="item-details">
                        <h3>${itemDef.name} <span class="item-quantity">(x${quantity})</span></h3>
                        <p>${itemDef.description}</p>
                    </div>
                    <div class="item-actions">
                        <div class="item-price">Prix: ${itemDef.sell_price} ⚙️</div>
                        <button class="sell-btn" data-item-id="${itemId}">Vendre 1</button>
                    </div>
                `;
                sellableItemsListEl.appendChild(itemEl);
            }
        }

        if (!hasSellableItems) {
            sellableItemsListEl.innerHTML = '<p>Vous n\'avez aucun objet à vendre.</p>';
        }

        // --- Section Achat ---
        buyableItemsListEl.innerHTML = '';
        merchantWares.forEach(ware => {
            const itemDef = itemDefinitions[ware.item_id];
            if (itemDef) {
                const canBuy = (inventory.currencies?.steel_shards || 0) >= ware.buy_price;
                const itemEl = document.createElement('div');
                itemEl.className = `item-card ${canBuy ? '' : 'disabled'}`;
                itemEl.innerHTML = `
                    <div class="item-icon">${itemDef.icon}</div>
                    <div class="item-details">
                        <h3>${itemDef.name}</h3>
                        <p>${itemDef.description}</p>
                    </div>
                    <div class="item-actions">
                        <div class="item-price">Coût: ${ware.buy_price} ⚙️</div>
                        <button class="buy-btn" data-item-id="${ware.item_id}" ${!canBuy ? 'disabled' : ''}>Acheter 1</button>
                    </div>
                `;
                buyableItemsListEl.appendChild(itemEl);
            }
        });
        if (merchantWares.length === 0) {
            buyableItemsListEl.innerHTML = '<p>Le marchand n\'a rien à vendre pour le moment.</p>';
        }
    }

    async function handleSell(itemId) {
        const itemDef = itemDefinitions[itemId];
        if (!itemDef) {
            showStatus("Objet inconnu.", true);
            return;
        }

        try {
            const response = await fetch('/api/gamification/sell', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    character: activeCharacterName,
                    item_id: itemId,
                    quantity: 1
                })
            });

            const result = await response.json();
            if (response.ok && result.success) {
                showStatus(`Vous avez vendu 1x ${itemDef.name} pour ${itemDef.sell_price} ⚙️.`);
                loadData(); // Recharger pour mettre à jour l'UI
            } else {
                throw new Error(result.error || "Erreur inconnue du serveur.");
            }
        } catch (error) {
            console.error("Erreur lors de la vente:", error);
            showStatus(`Erreur: ${error.message}`, true);
        }
    }

    async function handleBuy(itemId) {
        const ware = merchantWares.find(w => w.item_id === itemId);
        const itemDef = itemDefinitions[itemId];
        if (!ware || !itemDef) {
            showStatus("Objet inconnu.", true);
            return;
        }

        try {
            const response = await fetch('/api/gamification/buy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    character: activeCharacterName,
                    item_id: itemId,
                    quantity: 1
                })
            });

            const result = await response.json();
            if (response.ok && result.success) {
                showStatus(`Vous avez acheté 1x ${itemDef.name} pour ${ware.buy_price} ⚙️.`);
                loadData(); // Recharger pour mettre à jour l'UI
            } else {
                throw new Error(result.error || "Erreur inconnue du serveur.");
            }
        } catch (error) {
            console.error("Erreur lors de l'achat:", error);
            showStatus(`Erreur: ${error.message}`, true);
        }
    }

    function showStatus(message, isError = false) {
        merchantStatusEl.textContent = message;
        merchantStatusEl.style.color = isError ? '#ef5350' : '#66bb6a';
        merchantStatusEl.style.display = 'block';
        setTimeout(() => {
            merchantStatusEl.style.display = 'none';
        }, 4000);
    }

    document.querySelector('.merchant-container').addEventListener('click', (e) => {
        if (e.target.classList.contains('sell-btn')) {
            handleSell(e.target.dataset.itemId);
        }
        if (e.target.classList.contains('buy-btn')) {
            handleBuy(e.target.dataset.itemId);
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