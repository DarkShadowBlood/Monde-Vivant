// script.js
document.addEventListener('DOMContentLoaded', () => {
    // --- Éléments du DOM ---
    const gameContainer = document.getElementById('game-container');
    const target = document.getElementById('target');
    const crosshair = document.getElementById('crosshair');
    const throwButton = document.getElementById('throw-button');
    const resultDisplay = document.getElementById('result');
    const axe = document.getElementById('axe');
    const crystalCountDisplay = document.getElementById('crystal-count');
    const multiplierDisplay = document.getElementById('multiplier-display');

    // --- Paramètres du jeu ---
    const prizes = [
        { text: "+1", value: 1 },
        { text: "x2", value: 'multiplier' },
        { text: "0", value: 0 },
        { text: "-1", value: -1 },
        { text: "+1", value: 1 },
        { text: "x2", value: 'multiplier' },
        { text: "0", value: 0 },
        { text: "-1", value: -1 },
    ];
    const crosshairMoveInterval = 400; // en ms, vitesse de déplacement du viseur
    let crosshairIntervalId = null;
    let gameInProgress = false;

    // --- État du joueur ---
    let crystals = 10;
    let multiplier = 1;

    /**
     * Déplace le viseur à une position aléatoire dans le conteneur de jeu.
     */
    function moveCrosshair() {
        const containerRect = gameContainer.getBoundingClientRect();
        const crosshairRect = crosshair.getBoundingClientRect();

        const maxX = containerRect.width - crosshairRect.width;
        const maxY = containerRect.height - crosshairRect.height;

        const randomX = Math.random() * maxX;
        const randomY = Math.random() * maxY;

        crosshair.style.left = `${randomX}px`;
        crosshair.style.top = `${randomY}px`;
    }

    /**
     * Met à jour l'affichage des cristaux et du multiplicateur.
     */
    function updateUI() {
        crystalCountDisplay.textContent = crystals;
        multiplierDisplay.textContent = multiplier;
        if (crystals <= 0 && !gameInProgress) {
            throwButton.disabled = true;
            resultDisplay.textContent = "Plus de cristaux ! Rechargez la page pour rejouer.";
        }
    }

    /**
     * Calcule le prix en fonction de l'endroit où la hache a atterri.
     */
    function calculatePrize() {
        // 1. Obtenir l'angle de rotation actuel de la cible
        const style = window.getComputedStyle(target);
        const matrix = new DOMMatrixReadOnly(style.transform);
        const currentRotation = Math.atan2(matrix.b, matrix.a) * (180 / Math.PI);

        // 2. Obtenir la position du viseur par rapport au centre de la cible
        const targetRect = target.getBoundingClientRect();
        const crosshairRect = crosshair.getBoundingClientRect();
        
        const targetCenterX = targetRect.left + targetRect.width / 2;
        const targetCenterY = targetRect.top + targetRect.height / 2;
        
        const crosshairCenterX = crosshairRect.left + crosshairRect.width / 2;
        const crosshairCenterY = crosshairRect.top + crosshairRect.height / 2;

        // 3. Vérifier si le viseur est sur la cible
        const distance = Math.sqrt(Math.pow(crosshairCenterX - targetCenterX, 2) + Math.pow(crosshairCenterY - targetCenterY, 2));
        if (distance > targetRect.width / 2) {
            return { text: "Manqué !", value: 'missed' };
        }

        // 4. Calculer l'angle du "hit"
        const angleRad = Math.atan2(crosshairCenterY - targetCenterY, crosshairCenterX - targetCenterX);
        let hitAngle = angleRad * (180 / Math.PI);
        if (hitAngle < 0) {
            hitAngle += 360;
        }

        // 5. Ajuster avec la rotation de la cible pour trouver le segment touché
        const finalAngle = (hitAngle - currentRotation + 360) % 360;
        const segmentAngle = 360 / prizes.length;
        const prizeIndex = Math.floor(finalAngle / segmentAngle);

        return prizes[prizeIndex]; // Retourne l'objet complet {text, value}
    }

    /**
     * Gère l'action de lancer la hache.
     */
    function throwAxe() {
        if (gameInProgress || crystals <= 0) return;
        gameInProgress = true;

        // Chaque lancer coûte 1 cristal
        crystals--;
        updateUI();

        // Arrêter le mouvement du viseur et la rotation de la cible
        clearInterval(crosshairIntervalId);
        target.style.animationPlayState = 'paused';
        throwButton.disabled = true;

        // Animer la hache
        axe.style.left = crosshair.style.left;
        axe.style.top = crosshair.style.top;
        axe.style.display = 'block';
        axe.style.transform = 'scale(1) rotate(-90deg)';

        // Calculer le résultat
        const prize = calculatePrize();
        
        setTimeout(() => {
            let resultText = "";
            switch(prize.value) {
                case 'multiplier':
                    multiplier *= 2;
                    resultText = `BONUS ! Prochain lancer sera en x${multiplier} !`;
                    break;
                case 'missed':
                    resultText = "Manqué ! Vous perdez votre lancer et votre bonus.";
                    multiplier = 1; // Le multiplicateur est perdu si on manque
                    break;
                default: // C'est un gain/perte numérique (0, 1, -1)
                    const change = prize.value * multiplier;
                    crystals += change;
                    resultText = `Vous touchez "${prize.text}" (x${multiplier})! Résultat : ${change >= 0 ? '+' : ''}${change} cristaux.`;
                    multiplier = 1; // Le multiplicateur est consommé après utilisation
                    break;
            }
            resultDisplay.textContent = resultText;
            updateUI();
            // Réinitialiser après un délai
            setTimeout(resetGame, 3000);
        }, 600); // Délai pour "voir" la hache plantée
    }

    /**
     * Réinitialise le jeu pour un nouveau tour.
     */
    function resetGame() {
        target.style.animationPlayState = 'running';
        resultDisplay.textContent = '';
        throwButton.disabled = (crystals <= 0);
        axe.style.display = 'none';
        axe.style.transform = 'scale(0)';
        crosshairIntervalId = setInterval(moveCrosshair, crosshairMoveInterval);
        gameInProgress = false;
        updateUI(); // S'assurer que tout est à jour pour le prochain tour
    }
    
    /**
     * Initialise les textes sur les segments de la cible.
     */
    function setupTargetText() {
        const segmentAngle = 360 / prizes.length; // 45
        const radius = target.offsetWidth / 2 * 0.45; // 45% du rayon pour placer le début du texte

        prizes.forEach((prize, index) => {
            const text = document.createElement('div');
            text.classList.add('segment-text');
            text.textContent = prize.text; // Utilise la propriété text de l'objet
            
            const angle = (segmentAngle * index) + (segmentAngle / 2); // Centre du segment
            const rad = angle * Math.PI / 180;
            
            const x = Math.cos(rad) * radius;
            const y = Math.sin(rad) * radius;
            
            // Positionne et oriente le texte sur la roue.
            // On assume que le CSS pour .segment-text le place au centre de son parent.
            // La transformation le déplace ensuite à la bonne position radiale et le fait pivoter.
            text.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%) rotate(${angle + 90}deg)`;
            target.appendChild(text);
        });
    }

    // --- Démarrage du jeu ---
    setupTargetText();
    updateUI(); // Affichage initial des stats
    crosshairIntervalId = setInterval(moveCrosshair, crosshairMoveInterval);
    throwButton.addEventListener('click', throwAxe);
});
