// ============================================
// MemoryGraph - Interactive Terminal Effects
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initTypingEffect();
    initCopyCommand();
    initSmoothScroll();
});

// Tab switching for install panels
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const panels = document.querySelectorAll('.install-panel');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;

            // Update buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update panels
            panels.forEach(p => p.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
        });
    });
}

// Typing effect for hero terminal
function initTypingEffect() {
    const commands = document.querySelectorAll('.hero .terminal-body .command');

    commands.forEach((cmd, index) => {
        const text = cmd.textContent;
        cmd.textContent = '';
        cmd.style.borderRight = '2px solid var(--green-primary)';

        // Delay each command
        setTimeout(() => {
            typeText(cmd, text, () => {
                cmd.style.borderRight = 'none';
            });
        }, index * 1500);
    });
}

function typeText(element, text, callback) {
    let i = 0;
    const speed = 30; // ms per character

    function type() {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            setTimeout(type, speed);
        } else if (callback) {
            callback();
        }
    }

    type();
}

// Copy command to clipboard
function copyCommand() {
    const cmdElement = document.getElementById('install-cmd');
    const copyIcon = document.getElementById('copy-icon');
    const text = cmdElement.textContent;

    navigator.clipboard.writeText(text).then(() => {
        // Show success feedback
        copyIcon.textContent = '✓';
        copyIcon.style.color = 'var(--green-primary)';

        setTimeout(() => {
            copyIcon.textContent = '📋';
            copyIcon.style.color = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Make copyCommand available globally
window.copyCommand = copyCommand;

// Smooth scroll for anchor links
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Optional: Add glitch effect on hover for certain elements
function initGlitchEffect() {
    const glitchElements = document.querySelectorAll('.glitch-hover');

    glitchElements.forEach(el => {
        el.addEventListener('mouseenter', () => {
            el.classList.add('glitching');
            setTimeout(() => {
                el.classList.remove('glitching');
            }, 200);
        });
    });
}

// Optional: Terminal cursor following effect
function initCursorFollow() {
    const cursor = document.createElement('div');
    cursor.className = 'custom-cursor';
    document.body.appendChild(cursor);

    document.addEventListener('mousemove', (e) => {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
    });
}

// Intersection Observer for fade-in animations
function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.1
    });

    document.querySelectorAll('.fade-in').forEach(el => {
        observer.observe(el);
    });
}

// Console easter egg
console.log(`
%c
 _ __ ___   ___ _ __ ___   ___  _ __ _   _  __ _ _ __ __ _ _ __ | |__
| '_ \` _ \\ / _ \\ '_ \` _ \\ / _ \\| '__| | | |/ _\` | '__/ _\` | '_ \\| '_ \\
| | | | | |  __/ | | | | | (_) | |  | |_| | (_| | | | (_| | |_) | | | |
|_| |_| |_|\\___|_| |_| |_|\\___/|_|   \\__, |\\__, |_|  \\__,_| .__/|_| |_|
                                     |___/ |___/          |_|

Give your AI a memory: pip install memorygraphMCP
`, 'color: #00FF00; font-family: monospace;');
