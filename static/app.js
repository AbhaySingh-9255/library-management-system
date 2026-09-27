document.addEventListener('DOMContentLoaded', () => {
    // --- 1. Live Preview Logic ---
    const titleInput = document.getElementById('titleInput');
    const authorInput = document.getElementById('authorInput');
    const isbnInput = document.getElementById('isbnInput');

    const previewTitle = document.getElementById('previewTitle');
    const previewAuthor = document.getElementById('previewAuthor');
    const previewImg = document.getElementById('previewImg');
    const bookScene = document.querySelector('.book-3d-scene');
    const spineText = document.querySelector('.book-spine');

    function updatePreview() {
        const t = titleInput.value || "Untitled";
        const a = authorInput.value || "Unknown";

        previewTitle.textContent = t.length > 25 ? t.substring(0, 25) + "..." : t;
        previewAuthor.textContent = "by " + (a.length > 20 ? a.substring(0, 20) + "..." : a);
        spineText.textContent = t.toUpperCase();

        // Dynamic Color Generation based on Title Hash
        let hash = 0;
        for (let i = 0; i < t.length; i++) {
            hash = t.charCodeAt(i) + ((hash << 5) - hash);
        }
        const hue = Math.abs(hash % 360);
        const bgColor = `hsl(${hue}, 60%, 40%)`;

        // Update placeholder image URL dynamically
        previewImg.src = `https://placehold.co/400x600/${hue.toString(16).padStart(2, '0')}88cc/white?text=${encodeURIComponent(t.split(' ')[0])}`;

        // Add subtle glow to the card based on color
        bookScene.style.boxShadow = `0 20px 50px ${bgColor}40`;
    }

    if (titleInput && authorInput) {
        titleInput.addEventListener('input', updatePreview);
        authorInput.addEventListener('input', updatePreview);
    }

    // --- 2. Smart ISBN Auto-Fill Simulation ---
    if (isbnInput) {
        isbnInput.addEventListener('input', (e) => {
            const val = e.target.value.trim();
            const btn = document.getElementById('smartFillBtn');

            if (val.length >= 10) {
                btn.classList.remove('hidden');
                btn.onclick = () => {
                    // Simulate API Call
                    btn.textContent = "Loading...";
                    setTimeout(() => {
                        if (titleInput) titleInput.value = `Secret Code: ${val.slice(-4)}`;
                        if (authorInput) authorInput.value = "Digital Archivist";
                        updatePreview();
                        btn.textContent = "Done!";
                        setTimeout(() => btn.classList.add('hidden'), 1000);
                    }, 800);
                };
            } else {
                btn.classList.add('hidden');
            }
        });
    }

    // --- 3. 3D Tilt Effect on Mouse Move ---
    if (bookScene) {
        const handleTilt = (e) => {
            const rect = bookScene.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = ((y - centerY) / centerY) * -10; // Max 10 deg
            const rotateY = ((x - centerX) / centerX) * 10;  // Max 10 deg

            bookScene.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        };

        bookScene.parentElement.addEventListener('mousemove', handleTilt);
        bookScene.parentElement.addEventListener('mouseleave', () => {
            bookScene.style.transform = `rotateX(0deg) rotateY(0deg)`;
        });
    }

    // --- 4. Confetti Explosion on Submit ---
    const form = document.getElementById('addBookForm');
    if (form) {
        form.addEventListener('submit', (e) => {
            // Prevent immediate submit to show confetti first
            e.preventDefault();
            fireConfetti();

            // Small delay then submit
            setTimeout(() => {
                form.submit();
            }, 1500);
        });
    }
});

// --- Simple Vanilla Confetti Engine ---
function fireConfetti() {
    const canvas = document.getElementById('confettiCanvas');
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles = [];
    const colors = ['#6366f1', '#ec4899', '#10b981', '#f59e0b'];

    for (let i = 0; i < 100; i++) {
        particles.push({
            x: window.innerWidth / 2,
            y: window.innerHeight / 2,
            vx: (Math.random() - 0.5) * 20,
            vy: (Math.random() - 0.5) * 20 - 5,
            size: Math.random() * 10 + 5,
            color: colors[Math.floor(Math.random() * colors.length)],
            life: 100
        });
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach((p, index) => {
            p.x += p.vx;
            p.y += p.vy;
            p.vy += 0.5; // Gravity
            p.life--;

            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.life / 100;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fill();

            if (p.life <= 0) particles.splice(index, 1);
        });

        if (particles.length > 0) requestAnimationFrame(draw);
    }
    draw();
}