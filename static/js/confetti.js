/**
 * Confetti Celebration Effect
 * Lightweight confetti animation for achievements
 */

class ConfettiCelebration {
    constructor(options = {}) {
        this.options = {
            particleCount: 150,
            spread: 70,
            startVelocity: 45,
            decay: 0.9,
            gravity: 1,
            ticks: 200,
            scalar: 1.2,
            shapes: ['circle', 'square'],
            colors: ['#ff6b6b', '#4dabf7', '#51cf66', '#ffd43b', '#b197fc', '#ff922b'],
            ...options
        };
        
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.animationId = null;
    }

    createCanvas() {
        if (this.canvas) return;
        
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'confetti-canvas';
        this.canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 99999;
        `;
        document.body.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
        this.resizeCanvas();
        
        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        if (!this.canvas) return;
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    createParticle(x, y) {
        const angle = Math.random() * Math.PI * 2;
        const velocity = this.options.startVelocity * (0.5 + Math.random() * 0.5);
        
        return {
            x,
            y,
            vx: Math.cos(angle) * velocity * (Math.random() - 0.5) * 2,
            vy: Math.sin(angle) * velocity * -1,
            color: this.options.colors[Math.floor(Math.random() * this.options.colors.length)],
            size: Math.random() * 10 + 5,
            rotation: Math.random() * 360,
            rotationSpeed: (Math.random() - 0.5) * 10,
            shape: Math.random() > 0.5 ? 'rect' : 'circle',
            ticks: this.options.ticks
        };
    }

    burst(x = window.innerWidth / 2, y = window.innerHeight / 2) {
        this.createCanvas();
        
        for (let i = 0; i < this.options.particleCount; i++) {
            this.particles.push(this.createParticle(x, y));
        }
        
        if (!this.animationId) {
            this.animate();
        }
    }

    /**
     * Fire confetti from the sides (like cannons)
     */
    cannon() {
        this.createCanvas();
        
        // Left cannon
        for (let i = 0; i < this.options.particleCount / 2; i++) {
            const particle = this.createParticle(0, window.innerHeight);
            particle.vx = Math.abs(particle.vx) + 5;
            particle.vy = -Math.abs(particle.vy) - 5;
            this.particles.push(particle);
        }
        
        // Right cannon
        for (let i = 0; i < this.options.particleCount / 2; i++) {
            const particle = this.createParticle(window.innerWidth, window.innerHeight);
            particle.vx = -Math.abs(particle.vx) - 5;
            particle.vy = -Math.abs(particle.vy) - 5;
            this.particles.push(particle);
        }
        
        if (!this.animationId) {
            this.animate();
        }
    }

    /**
     * Rain confetti from the top
     */
    rain() {
        this.createCanvas();
        
        for (let i = 0; i < this.options.particleCount; i++) {
            const particle = this.createParticle(
                Math.random() * window.innerWidth,
                -20
            );
            particle.vy = Math.abs(particle.vy) * 0.3;
            particle.vx = particle.vx * 0.3;
            this.particles.push(particle);
        }
        
        if (!this.animationId) {
            this.animate();
        }
    }

    /**
     * Firework-style burst
     */
    firework(x = window.innerWidth / 2, y = window.innerHeight / 2) {
        this.createCanvas();
        
        const colors = this.options.colors[Math.floor(Math.random() * this.options.colors.length)];
        
        for (let i = 0; i < 50; i++) {
            const angle = (i / 50) * Math.PI * 2;
            const velocity = 10 + Math.random() * 10;
            
            this.particles.push({
                x,
                y,
                vx: Math.cos(angle) * velocity,
                vy: Math.sin(angle) * velocity,
                color: colors,
                size: 4 + Math.random() * 4,
                rotation: 0,
                rotationSpeed: 0,
                shape: 'circle',
                ticks: 100
            });
        }
        
        if (!this.animationId) {
            this.animate();
        }
    }

    /**
     * Multiple fireworks
     */
    celebration() {
        const positions = [
            { x: window.innerWidth * 0.25, y: window.innerHeight * 0.4 },
            { x: window.innerWidth * 0.5, y: window.innerHeight * 0.3 },
            { x: window.innerWidth * 0.75, y: window.innerHeight * 0.4 }
        ];
        
        positions.forEach((pos, i) => {
            setTimeout(() => this.firework(pos.x, pos.y), i * 300);
        });
        
        setTimeout(() => this.cannon(), 900);
    }

    animate() {
        if (!this.ctx || !this.canvas) return;
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.particles = this.particles.filter(p => {
            p.x += p.vx;
            p.y += p.vy;
            p.vy += this.options.gravity;
            p.vx *= this.options.decay;
            p.vy *= this.options.decay;
            p.rotation += p.rotationSpeed;
            p.ticks--;
            
            if (p.ticks <= 0) return false;
            if (p.y > this.canvas.height + 50) return false;
            
            this.drawParticle(p);
            return true;
        });
        
        if (this.particles.length > 0) {
            this.animationId = requestAnimationFrame(() => this.animate());
        } else {
            this.animationId = null;
            this.cleanup();
        }
    }

    drawParticle(p) {
        this.ctx.save();
        this.ctx.translate(p.x, p.y);
        this.ctx.rotate(p.rotation * Math.PI / 180);
        this.ctx.fillStyle = p.color;
        this.ctx.globalAlpha = Math.min(1, p.ticks / 50);
        
        if (p.shape === 'rect') {
            this.ctx.fillRect(-p.size / 2, -p.size / 4, p.size, p.size / 2);
        } else {
            this.ctx.beginPath();
            this.ctx.arc(0, 0, p.size / 2, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        this.ctx.restore();
    }

    cleanup() {
        if (this.canvas && this.particles.length === 0) {
            setTimeout(() => {
                if (this.particles.length === 0 && this.canvas) {
                    this.canvas.remove();
                    this.canvas = null;
                    this.ctx = null;
                }
            }, 1000);
        }
    }

    /**
     * Stop all animations
     */
    stop() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        this.particles = [];
        this.cleanup();
    }
}

// Create global instance
const confetti = new ConfettiCelebration();
window.confetti = confetti;

// Convenience functions
window.celebrate = () => confetti.celebration();
window.confettiBurst = (x, y) => confetti.burst(x, y);
window.confettiCannon = () => confetti.cannon();
window.confettiRain = () => confetti.rain();
window.confettiFirework = (x, y) => confetti.firework(x, y);

// Auto-celebrate on achievements (if achievement system exists)
document.addEventListener('achievement-unlocked', (e) => {
    confetti.celebration();
});

// Example usage:
// confetti.burst()           - Burst from center
// confetti.burst(100, 200)   - Burst from specific position
// confetti.cannon()          - Fire from both sides
// confetti.rain()            - Rain from top
// confetti.firework()        - Single firework
// confetti.celebration()     - Full celebration sequence



