document.addEventListener('DOMContentLoaded', () => {
    const charNameEl = document.getElementById('char-name');
    const currencyShardsEl = document.getElementById('currency-shards');
    const currencyGemsEl = document.getElementById('currency-gems');
    const itemComponentsEl = document.getElementById('item-components');
    const itemFragmentsEl = document.getElementById('item-fragments');
    const inventoryGridEl = document.getElementById('inventory-grid');

    let activeCharacterName = 'Varkis';
    let itemDefinitions = {};

    async function loadData() {
        try {
            const activeCharButton = document.querySelector('.character-selector button.active');
            if (activeCharButton) activeCharacterName = activeCharButton.dataset.char;

            charNameEl.textContent = `Inventaire de ${activeCharacterName}`;

            const [inventoryRes, itemsDefRes] = await Promise.all([
                fetch(`/api/gamification/inventory?character=${activeCharacterName}`),
                fetch('items_definitions.json')
            ]);

            if (!inventoryRes.ok) throw new Error("L'inventaire du personnage n'a pas pu être chargé.");
            if (!itemsDefRes.ok) throw new Error("Les définitions d'objets n'ont pas pu être chargées.");
            
            const inventoryResult = await inventoryRes.json();
            const characterInventory = inventoryResult.success ? inventoryResult.data : {};
            itemDefinitions = await itemsDefRes.json();

            updateUI(characterInventory);

        } catch (error) {
            console.error("Erreur de chargement des données d'inventaire:", error);
            inventoryGridEl.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    }

    function updateUI(inventory) {
        // Mettre à jour les monnaies et matériaux
        currencyShardsEl.textContent = (inventory.currencies?.steel_shards || 0).toLocaleString('fr-FR');
        currencyGemsEl.textContent = (inventory.currencies?.soul_gems || 0).toLocaleString('fr-FR');
        itemComponentsEl.textContent = (inventory.items?.ancient_components || 0).toLocaleString('fr-FR');
        itemFragmentsEl.textContent = (inventory.items?.map_fragments || 0).toLocaleString('fr-FR');

        // Vider et remplir la grille d'inventaire
        inventoryGridEl.innerHTML = '';
        const playerItems = inventory.items || {};
        const totalSlots = 20;
        let filledSlots = 0;

        // Afficher les objets que le joueur possède
        for (const [itemId, quantity] of Object.entries(playerItems)) {
            if (quantity > 0) {
                const itemDef = itemDefinitions[itemId];
                if (itemDef) {
                    const slotEl = document.createElement('div');
                    slotEl.className = 'inventory-slot has-item';
                    slotEl.dataset.itemId = itemId; // Important pour le drag-and-drop
                    slotEl.setAttribute('draggable', 'true');
                    slotEl.innerHTML = `
                        <div class="item-icon">${itemDef.icon}</div>
                        <div class="item-name">${itemDef.name}</div>
                        <div class="item-quantity">${quantity}</div>
                        <div class="item-tooltip">
                            <strong>${itemDef.name}</strong>
                            <p>${itemDef.description}</p>
                        </div>
                    `;
                    inventoryGridEl.appendChild(slotEl);
                    filledSlots++;
                }
            }
        }

        // Remplir le reste avec des slots vides
        for (let i = filledSlots; i < totalSlots; i++) {
            const slotEl = document.createElement('div');
            slotEl.className = 'inventory-slot';
            slotEl.setAttribute('draggable', 'false');
            inventoryGridEl.appendChild(slotEl);
        }
    }

    // --- Gestion des événements ---

    document.querySelector('.character-selector').addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON' && !e.target.classList.contains('active')) {
            document.querySelector('.character-selector button.active').classList.remove('active');
            e.target.classList.add('active');
            activeCharacterName = e.target.dataset.char;
            loadData();
        }
    });

    // --- Logique de Glisser-Déposer (Drag and Drop) ---
    let draggedItem = null;

    inventoryGridEl.addEventListener('dragstart', (e) => {
        if (e.target.classList.contains('has-item')) {
            draggedItem = e.target;
            // Ajoute un léger délai pour que le navigateur crée l'image fantôme
            setTimeout(() => {
                e.target.classList.add('dragging');
            }, 0);
        }
    });

    inventoryGridEl.addEventListener('dragend', (e) => {
        if (draggedItem) {
            draggedItem.classList.remove('dragging');
            draggedItem = null;
        }
    });

    inventoryGridEl.addEventListener('dragover', (e) => {
        e.preventDefault(); // Essentiel pour autoriser le 'drop'
        const targetSlot = e.target.closest('.inventory-slot');
        if (targetSlot && targetSlot !== draggedItem) {
            // Optionnel : ajouter un indicateur visuel sur la cible
        }
    });

    inventoryGridEl.addEventListener('drop', (e) => {
        e.preventDefault();
        const targetSlot = e.target.closest('.inventory-slot');

        if (targetSlot && draggedItem && targetSlot !== draggedItem) {
            // Si la cible est un slot vide
            if (!targetSlot.classList.contains('has-item')) {
                // Déplacer l'objet
                targetSlot.innerHTML = draggedItem.innerHTML;
                targetSlot.className = 'inventory-slot has-item';
                targetSlot.dataset.itemId = draggedItem.dataset.itemId;
                targetSlot.setAttribute('draggable', 'true');

                // Vider l'ancien slot
                draggedItem.innerHTML = '';
                draggedItem.className = 'inventory-slot';
                delete draggedItem.dataset.itemId;
                draggedItem.setAttribute('draggable', 'false');
            } else {
                // Si la cible contient un objet, on les échange (swap)
                const draggedContent = { html: draggedItem.innerHTML, id: draggedItem.dataset.itemId };
                const targetContent = { html: targetSlot.innerHTML, id: targetSlot.dataset.itemId };

                draggedItem.innerHTML = targetContent.html;
                draggedItem.dataset.itemId = targetContent.id;
                targetSlot.innerHTML = draggedContent.html;
                targetSlot.dataset.itemId = draggedContent.id;
            }
        }
    });

    // Chargement initial
    loadData();
});