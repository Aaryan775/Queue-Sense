/* =============================================
   QueueSense - Auth Module
   Handles authentication state and guards
   ============================================= */

// =============================================
// Auth State Management
// =============================================
const Auth = {
    // Get current user from localStorage
    getUser: () => {
        const userStr = localStorage.getItem('qs_user');
        return userStr ? JSON.parse(userStr) : null;
    },

    // Get auth token
    getToken: () => {
        return localStorage.getItem('qs_token');
    },

    // Check if user is logged in
    isLoggedIn: () => {
        return !!localStorage.getItem('qs_token');
    },

    // Check if user is admin
    isAdmin: () => {
        const user = Auth.getUser();
        return user && user.role === 'admin';
    },

    // Check if user is staff
    isStaff: () => {
        const user = Auth.getUser();
        return user && (user.role === 'staff' || user.role === 'admin');
    },

    // Check if user is elder
    isElder: () => {
        const user = Auth.getUser();
        return user && user.category === 'elder';
    },

    // Get user role
    getRole: () => {
        const user = Auth.getUser();
        return user ? user.role : null;
    },

    // Save auth data
    saveAuth: (token, user) => {
        localStorage.setItem('qs_token', token);
        localStorage.setItem('qs_user', JSON.stringify(user));
    },

    // Clear auth data and redirect
    logout: () => {
        localStorage.removeItem('qs_token');
        localStorage.removeItem('qs_user');
        window.location.href = '/login.html';
    },

    // Update user data in localStorage
    updateUser: (userData) => {
        const currentUser = Auth.getUser();
        const updatedUser = { ...currentUser, ...userData };
        localStorage.setItem('qs_user', JSON.stringify(updatedUser));
    }
};

// =============================================
// Route Guards
// Protect pages based on authentication
// =============================================
const RouteGuard = {
    // Require login
    requireAuth: () => {
        if (!Auth.isLoggedIn()) {
            window.location.href = '/login.html';
            return false;
        }
        return true;
    },

    // Require admin role
    requireAdmin: () => {
        if (!Auth.isLoggedIn()) {
            window.location.href = '/login.html';
            return false;
        }
        if (!Auth.isAdmin()) {
            window.location.href = '/user/dashboard.html';
            return false;
        }
        return true;
    },

    // Require staff role
    requireStaff: () => {
        if (!Auth.isLoggedIn()) {
            window.location.href = '/login.html';
            return false;
        }
        if (!Auth.isStaff()) {
            window.location.href = '/user/dashboard.html';
            return false;
        }
        return true;
    },

    // Redirect logged-in users away from auth pages
    redirectIfLoggedIn: () => {
        if (Auth.isLoggedIn()) {
            const role = Auth.getRole();
            if (role === 'admin') {
                window.location.href = '/admin/dashboard.html';
            } else if (role === 'staff') {
                window.location.href = '/staff/dashboard.html';
            } else {
                window.location.href = '/user/dashboard.html';
            }
            return true;
        }
        return false;
    },

    // Get dashboard URL based on role
    getDashboardUrl: () => {
        const role = Auth.getRole();
        if (role === 'admin') return '/admin/dashboard.html';
        if (role === 'staff') return '/staff/dashboard.html';
        return '/user/dashboard.html';
    }
};

// =============================================
// Auto-check auth on page load
// =============================================
function initAuthGuard() {
    const path = window.location.pathname;

    // Pages that require authentication
    const protectedPaths = ['/user/', '/staff/', '/admin/'];
    const adminPaths = ['/admin/'];
    const staffPaths = ['/staff/'];

    // Check if current path needs protection
    for (const protectedPath of adminPaths) {
        if (path.includes(protectedPath)) {
            RouteGuard.requireAdmin();
            return;
        }
    }

    for (const protectedPath of staffPaths) {
        if (path.includes(protectedPath)) {
            RouteGuard.requireStaff();
            return;
        }
    }

    for (const protectedPath of protectedPaths) {
        if (path.includes(protectedPath)) {
            RouteGuard.requireAuth();
            return;
        }
    }
}

// Export for use in other modules
window.Auth = Auth;
window.RouteGuard = RouteGuard;
window.initAuthGuard = initAuthGuard;
