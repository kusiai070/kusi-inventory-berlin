/**
 * Authentication JavaScript Module
 * Módulo de autenticación JavaScript
 */

class AuthManager {
    constructor() {
        this.token = localStorage.getItem('access_token');
        this.user = null;
        this.init();
    }

    init() {
        // Load user info if token exists
        if (this.token) {
            this.loadUserInfo();
        }
    }

    async login(email, password) {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                // Store authentication data
                this.token = data.access_token;
                this.user = data.user;
                
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                
                return {
                    success: true,
                    user: data.user
                };
            } else {
                return {
                    success: false,
                    error: data.detail || 'Login failed'
                };
            }
        } catch (error) {
            return {
                success: false,
                error: 'Connection error. Please try again.'
            };
        }
    }

    async logout() {
        try {
            // Call logout endpoint
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear local data
            this.clearAuthData();
        }
    }

    clearAuthData() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        localStorage.removeItem('pendingActions');
    }

    async loadUserInfo() {
        try {
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                this.user = userData;
                localStorage.setItem('user', JSON.stringify(userData));
                return userData;
            } else {
                // Token is invalid, clear auth data
                this.clearAuthData();
                return null;
            }
        } catch (error) {
            console.error('Error loading user info:', error);
            return null;
        }
    }

    isAuthenticated() {
        return this.token !== null;
    }

    getToken() {
        return this.token;
    }

    getUser() {
        if (!this.user) {
            const userStr = localStorage.getItem('user');
            if (userStr) {
                this.user = JSON.parse(userStr);
            }
        }
        return this.user;
    }

    hasRole(role) {
        const user = this.getUser();
        return user && user.role === role;
    }

    hasAnyRole(roles) {
        const user = this.getUser();
        return user && roles.includes(user.role);
    }

    async refreshToken() {
        try {
            const response = await fetch('/api/auth/refresh', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.token = data.access_token;
                localStorage.setItem('access_token', data.access_token);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Token refresh error:', error);
            return false;
        }
    }

    // Middleware for API calls
    async authenticatedFetch(url, options = {}) {
        const token = this.getToken();
        if (!token) {
            throw new Error('No authentication token available');
        }

        const config = {
            ...options,
            headers: {
                ...options.headers,
                'Authorization': `Bearer ${token}`
            }
        };

        let response = await fetch(url, config);

        // If token expired, try to refresh
        if (response.status === 401) {
            const refreshed = await this.refreshToken();
            if (refreshed) {
                config.headers['Authorization'] = `Bearer ${this.getToken()}`;
                response = await fetch(url, config);
            } else {
                // Refresh failed, redirect to login
                this.redirectToLogin();
                throw new Error('Authentication required');
            }
        }

        return response;
    }

    redirectToLogin() {
        this.clearAuthData();
        window.location.href = '/';
    }

    // Check authentication status
    async checkAuth() {
        if (!this.isAuthenticated()) {
            return false;
        }

        try {
            const response = await this.authenticatedFetch('/api/test-auth');
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    // Get user permissions
    can(permission) {
        const user = this.getUser();
        if (!user) return false;

        const permissions = {
            admin: ['view_all', 'edit_all', 'delete_all', 'manage_users', 'manage_settings'],
            manager: ['view_all', 'edit_products', 'edit_inventory', 'view_reports'],
            staff: ['view_products', 'edit_count', 'register_waste']
        };

        return permissions[user.role] && permissions[user.role].includes(permission);
    }

    // Restaurant access check
    canAccessRestaurant(restaurantId) {
        const user = this.getUser();
        if (!user) return false;

        if (user.role === 'admin') {
            return true; // Admin can access all restaurants
        }

        return user.restaurant_id === restaurantId;
    }
}

// Offline sync manager
class OfflineSyncManager {
    constructor(authManager) {
        this.authManager = authManager;
        this.pendingActions = this.loadPendingActions();
        this.isOnline = navigator.onLine;
        this.init();
    }

    init() {
        // Listen for connection changes
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());

        // Try to sync when coming back online
        if (this.isOnline && this.pendingActions.length > 0) {
            this.syncPendingActions();
        }
    }

    loadPendingActions() {
        const stored = localStorage.getItem('pendingActions');
        return stored ? JSON.parse(stored) : [];
    }

    savePendingActions() {
        localStorage.setItem('pendingActions', JSON.stringify(this.pendingActions));
    }

    addAction(action) {
        const actionWithMetadata = {
            ...action,
            id: this.generateId(),
            timestamp: new Date().toISOString(),
            attempts: 0
        };

        this.pendingActions.push(actionWithMetadata);
        this.savePendingActions();

        // Try to sync immediately if online
        if (this.isOnline) {
            this.syncPendingActions();
        }
    }

    async syncPendingActions() {
        if (!this.isOnline || this.pendingActions.length === 0) {
            return;
        }

        const syncedActions = [];

        for (const action of this.pendingActions) {
            try {
                const response = await this.authManager.authenticatedFetch(action.url, action.options);
                
                if (response.ok) {
                    syncedActions.push(action.id);
                    console.log('Synced action:', action.id);
                } else {
                    // Increment attempt counter
                    action.attempts = (action.attempts || 0) + 1;
                    
                    // Remove if too many failed attempts
                    if (action.attempts >= 3) {
                        syncedActions.push(action.id);
                        console.warn('Removing failed action after 3 attempts:', action.id);
                    }
                }
            } catch (error) {
                console.error('Sync error for action', action.id, error);
                // Keep the action for later retry
            }
        }

        // Remove successfully synced actions
        this.pendingActions = this.pendingActions.filter(action => !syncedActions.includes(action.id));
        this.savePendingActions();

        // Show notification if actions were synced
        if (syncedActions.length > 0) {
            this.showSyncNotification(syncedActions.length);
        }
    }

    handleOnline() {
        this.isOnline = true;
        console.log('Connection restored, syncing pending actions...');
        this.syncPendingActions();
    }

    handleOffline() {
        this.isOnline = false;
        console.log('Connection lost, storing actions locally...');
    }

    showSyncNotification(count) {
        // Create and show a temporary notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        notification.innerHTML = `
            <i class="fas fa-check-circle mr-2"></i>
            ${count} acción(es) sincronizada(s) exitosamente
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    generateId() {
        return Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
    }

    getPendingCount() {
        return this.pendingActions.length;
    }
}

// Initialize auth manager
const authManager = new AuthManager();
const offlineSyncManager = new OfflineSyncManager(authManager);

// Export for global access
window.authManager = authManager;
window.offlineSyncManager = offlineSyncManager;