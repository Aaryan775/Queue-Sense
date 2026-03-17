/* =============================================
   QueueSense - Main Application Module
   Core functionality and utilities
   ============================================= */

// =============================================
// DOM Ready Helper
// =============================================
function ready(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}

// =============================================
// Scroll Reveal Animation
// =============================================
function initScrollReveal() {
    const revealElements = document.querySelectorAll('.scroll-reveal, .scroll-reveal-left, .scroll-reveal-right');

    if (revealElements.length === 0) return;

    const revealOnScroll = () => {
        revealElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;

            if (elementTop < windowHeight - 100) {
                element.classList.add('revealed');
            }
        });
    };

    // Initial check
    revealOnScroll();

    // Check on scroll
    window.addEventListener('scroll', revealOnScroll);
}

// =============================================
// Navbar Scroll Effect
// =============================================
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');

    if (!navbar) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.15)';
            navbar.style.padding = '0.75rem 0';
        } else {
            navbar.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
            navbar.style.padding = '1rem 0';
        }
    });
}

// =============================================
// Toast Notification System
// =============================================
const Toast = {
    container: null,

    init: () => {
        // Create toast container if it doesn't exist
        if (!Toast.container) {
            Toast.container = document.createElement('div');
            Toast.container.id = 'toast-container';
            Toast.container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(Toast.container);
        }
    },

    show: (message, type = 'info', duration = 3000) => {
        Toast.init();

        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type} animate-slideInRight`;
        toast.innerHTML = `
            <i class="fas ${Toast.getIcon(type)}"></i>
            <span>${message}</span>
            <button class="toast-close">&times;</button>
        `;

        // Style the toast
        toast.style.cssText = `
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 1rem 1.5rem;
            background: ${Toast.getBackground(type)};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            min-width: 300px;
            max-width: 400px;
        `;

        // Close button
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.style.cssText = `
            background: none;
            border: none;
            color: white;
            font-size: 1.25rem;
            cursor: pointer;
            margin-left: auto;
            opacity: 0.7;
        `;
        closeBtn.onclick = () => Toast.remove(toast);

        // Add to container
        Toast.container.appendChild(toast);

        // Auto remove
        setTimeout(() => Toast.remove(toast), duration);
    },

    remove: (toast) => {
        toast.style.animation = 'slideInRight 0.3s ease reverse forwards';
        setTimeout(() => toast.remove(), 300);
    },

    getIcon: (type) => {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    },

    getBackground: (type) => {
        const backgrounds = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#4A90E2'
        };
        return backgrounds[type] || backgrounds.info;
    },

    // Shorthand methods
    success: (msg, duration) => Toast.show(msg, 'success', duration),
    error: (msg, duration) => Toast.show(msg, 'error', duration),
    warning: (msg, duration) => Toast.show(msg, 'warning', duration),
    info: (msg, duration) => Toast.show(msg, 'info', duration)
};

// =============================================
// Voice Notification System (Web Speech API)
// =============================================
const Voice = {
    synth: window.speechSynthesis,
    enabled: true,
    repeatTimer: null,

    // Speak a message
    speak: (message, options = {}) => {
        if (!Voice.synth || !Voice.enabled) return;

        // Force stop any current/queued speech before starting new
        try {
            Voice.stop();
        } catch (e) {
            console.warn('Voice stop error', e);
        }

        const utterance = new SpeechSynthesisUtterance(message);
        utterance.rate = options.rate || 0.8;
        utterance.pitch = options.pitch || 1;
        utterance.volume = options.volume || 1;
        utterance.lang = 'en-US';

        const voices = Voice.synth.getVoices();
        const englishVoice = voices.find(v => v.lang.includes('en-'));
        if (englishVoice) utterance.voice = englishVoice;

        Voice.synth.speak(utterance);

        if (options.repeat) {
            Voice.repeatTimer = setTimeout(() => {
                Voice.synth.speak(utterance);
            }, 3000);
        }
    },

    announceToken: (token, counter) => {
        const message = `Attention please. Token number ${token}, please proceed to counter ${counter}. Token ${token}, counter ${counter}.`;
        Voice.speak(message, { rate: 0.7, repeat: true });
    },

    stop: () => {
        if (Voice.synth) {
            Voice.synth.cancel();
            // Clear any pending/queued speech
            if (Voice.synth.speaking) Voice.synth.cancel();
        }
        if (Voice.repeatTimer) {
            clearTimeout(Voice.repeatTimer);
            Voice.repeatTimer = null;
        }
    },

    toggle: (enabled) => {
        Voice.enabled = enabled;
        if (!enabled) Voice.stop();
    },

    isSupported: () => {
        return 'speechSynthesis' in window;
    },

    // Test speech synthesis
    test: () => {
        Voice.speak("Voice system is active and ready.");
    }
};

// =============================================
// Format Utilities
// =============================================
const Format = {
    // Format date to display string
    date: (dateStr) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    },

    // Format time to display string
    time: (timeStr) => {
        const [hours, minutes] = timeStr.split(':');
        const date = new Date();
        date.setHours(parseInt(hours), parseInt(minutes));
        return date.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    },

    // Format duration in minutes
    duration: (minutes) => {
        if (minutes < 60) {
            return `${minutes} min`;
        }
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
    },

    // Format relative time
    relative: (dateStr) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} min ago`;

        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;

        const diffDays = Math.floor(diffHours / 24);
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;

        return Format.date(dateStr);
    }
};

// =============================================
// Loading State Helpers
// =============================================
const Loading = {
    // Show loading overlay
    show: (container = document.body) => {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="spinner"></div>
            <p>Loading...</p>
        `;
        overlay.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.9);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 100;
        `;
        container.style.position = 'relative';
        container.appendChild(overlay);
    },

    // Hide loading overlay
    hide: (container = document.body) => {
        const overlay = container.querySelector('.loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    },

    // Button loading state
    buttonStart: (button) => {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Loading...`;
    },

    // Button normal state
    buttonStop: (button) => {
        button.disabled = false;
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
        }
    }
};

// =============================================
// Modal Helpers
// =============================================
const Modal = {
    // Show a confirmation modal
    confirm: (message, onConfirm, onCancel) => {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <p>${message}</p>
                <div class="modal-actions">
                    <button class="btn btn-secondary" id="modalCancel">Cancel</button>
                    <button class="btn btn-primary" id="modalConfirm">Confirm</button>
                </div>
            </div>
        `;
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        `;

        const content = modal.querySelector('.modal-content');
        content.style.cssText = `
            background: white;
            padding: 2rem;
            border-radius: 12px;
            max-width: 400px;
            text-align: center;
        `;

        const actions = modal.querySelector('.modal-actions');
        actions.style.cssText = `
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 1.5rem;
        `;

        document.body.appendChild(modal);

        modal.querySelector('#modalConfirm').onclick = () => {
            modal.remove();
            if (onConfirm) onConfirm();
        };

        modal.querySelector('#modalCancel').onclick = () => {
            modal.remove();
            if (onCancel) onCancel();
        };
    }
};

// =============================================
// Real-time Polling
// =============================================
class Poller {
    constructor(callback, interval = 5000) {
        this.callback = callback;
        this.interval = interval;
        this.timer = null;
        this.isRunning = false;
    }

    start() {
        if (this.isRunning) return;
        this.isRunning = true;
        this.poll();
    }

    stop() {
        this.isRunning = false;
        if (this.timer) {
            clearTimeout(this.timer);
            this.timer = null;
        }
    }

    async poll() {
        if (!this.isRunning) return;

        try {
            await this.callback();
        } catch (error) {
            console.error('Polling error:', error);
        }

        this.timer = setTimeout(() => this.poll(), this.interval);
    }

    setInterval(interval) {
        this.interval = interval;
    }
}

// =============================================
// Initialize on DOM Ready
// =============================================
ready(() => {
    // Initialize scroll reveal animations
    initScrollReveal();

    // Initialize navbar scroll effect
    initNavbarScroll();

    // Initialize auth guard
    if (typeof initAuthGuard === 'function') {
        initAuthGuard();
    }

    // Load voices for speech synthesis
    if (Voice.isSupported()) {
        speechSynthesis.onvoiceschanged = () => {
            speechSynthesis.getVoices();
        };
    }
});

// =============================================
// Export utilities
// =============================================
window.Toast = Toast;
window.Voice = Voice;
window.Format = Format;
window.Loading = Loading;
window.Modal = Modal;
window.Poller = Poller;
window.ready = ready;
