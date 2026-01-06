/**
 * Utility Functions Module
 * Módulo de funciones utilitarias
 */

class Utils {
    /**
     * Format currency values
     * @param {number} amount - Amount to format
     * @param {string} currency - Currency code (default: USD)
     * @returns {string} Formatted currency string
     */
    static formatCurrency(amount, currency = 'EUR') {
        const num = parseFloat(amount);
        if (isNaN(num)) return '0,00 €';

        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(num);
    }

    /**
     * Format date to locale string
     * @param {string|Date} date - Date to format
     * @param {Object} options - Format options
     * @returns {string} Formatted date string
     */
    static formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };

        const formatOptions = { ...defaultOptions, ...options };
        const dateObj = typeof date === 'string' ? new Date(date) : date;

        return dateObj.toLocaleDateString('es-ES', formatOptions);
    }

    /**
     * Format number with thousands separator
     * @param {number} number - Number to format
     * @param {number} decimals - Number of decimal places
     * @returns {string} Formatted number string
     */
    static formatNumber(number, decimals = 0) {
        const num = parseFloat(number);
        if (isNaN(num)) return '0';

        return new Intl.NumberFormat('es-ES', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(num);
    }

    /**
     * Debounce function calls
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} Debounced function
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Throttle function calls
     * @param {Function} func - Function to throttle
     * @param {number} limit - Limit in milliseconds
     * @returns {Function} Throttled function
     */
    static throttle(func, limit) {
        let inThrottle;
        return function (...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * Generate random ID
     * @param {number} length - ID length
     * @returns {string} Random ID
     */
    static generateId(length = 8) {
        return Math.random().toString(36).substr(2, length);
    }

    /**
     * Validate email format
     * @param {string} email - Email to validate
     * @returns {boolean} True if valid email
     */
    static isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Validate required field
     * @param {*} value - Value to validate
     * @returns {boolean} True if not empty
     */
    static isRequired(value) {
        return value !== null && value !== undefined && value.toString().trim() !== '';
    }

    /**
     * Validate numeric value
     * @param {*} value - Value to validate
     * @param {number} min - Minimum value
     * @param {number} max - Maximum value
     * @returns {boolean} True if valid number
     */
    static isValidNumber(value, min = null, max = null) {
        const num = parseFloat(value);

        if (isNaN(num)) {
            return false;
        }

        if (min !== null && num < min) {
            return false;
        }

        if (max !== null && num > max) {
            return false;
        }

        return true;
    }

    /**
     * Show notification toast
     * @param {string} message - Message to show
     * @param {string} type - Notification type (success, error, warning, info)
     * @param {number} duration - Duration in milliseconds
     */
    static showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');

        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        notification.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 transform translate-x-full transition-transform duration-300`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${icons[type]} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);

        // Animate out and remove
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
    }

    /**
     * Show loading overlay
     * @param {string} message - Loading message
     * @returns {Function} Function to hide loading
     */
    static showLoading(message = 'Cargando...') {
        const overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        overlay.innerHTML = `
            <div class="bg-white rounded-lg p-6 text-center">
                <i class="fas fa-spinner fa-spin text-2xl text-blue-500 mb-4"></i>
                <p class="text-gray-700">${message}</p>
            </div>
        `;

        document.body.appendChild(overlay);

        return () => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        };
    }

    /**
     * Download file
     * @param {Blob} blob - File blob
     * @param {string} filename - File name
     */
    static downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;

        document.body.appendChild(a);
        a.click();

        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    /**
     * Copy text to clipboard
     * @param {string} text - Text to copy
     * @returns {Promise<boolean>} True if successful
     */
    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (error) {
            console.error('Failed to copy text:', error);
            return false;
        }
    }

    /**
     * Get user's preferred language
     * @returns {string} Language code
     */
    static getUserLanguage() {
        return navigator.language || navigator.userLanguage || 'en';
    }

    /**
     * Localize text
     * @param {string} key - Translation key
     * @param {Object} translations - Translation object
     * @returns {string} Localized text
     */
    static async loadTranslations(lang) {
        try {
            const response = await fetch(`/static/locales/${lang}.json`);
            this.translations = await response.json();
            this.translatePage();
            localStorage.setItem('preferred_language', lang);
        } catch (error) {
            console.error('Error loading translations:', error);
        }
    }

    static translatePage() {
        if (!this.translations) return;

        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const translation = this.getNestedTranslation(this.translations, key);
            if (translation) {
                if (el.tagName === 'INPUT' && el.placeholder) {
                    el.placeholder = translation;
                } else {
                    el.textContent = translation;
                }
            }
        });
    }

    static getNestedTranslation(obj, path) {
        return path.split('.').reduce((prev, curr) => prev ? prev[curr] : null, obj);
    }

    static localize(key, translations = {}) {
        const language = this.getUserLanguage().substr(0, 2);
        return translations[language]?.[key] || translations['en']?.[key] || key;
    }

    /**
     * Calculate percentage
     * @param {number} value - Current value
     * @param {number} total - Total value
     * @param {number} decimals - Decimal places
     * @returns {string} Percentage string
     */
    static calculatePercentage(value, total, decimals = 1) {
        if (total === 0) return '0%';
        const percentage = (value / total) * 100;
        return `${this.formatNumber(percentage, decimals)}%`;
    }

    /**
     * Validate form data
     * @param {Object} data - Form data
     * @param {Object} rules - Validation rules
     * @returns {Object} Validation result
     */
    static validateForm(data, rules) {
        const errors = {};
        let isValid = true;

        for (const [field, rule] of Object.entries(rules)) {
            const value = data[field];

            // Required validation
            if (rule.required && !this.isRequired(value)) {
                errors[field] = rule.requiredMessage || `${field} is required`;
                isValid = false;
                continue;
            }

            // Skip other validations if field is empty and not required
            if (!this.isRequired(value) && !rule.required) {
                continue;
            }

            // Email validation
            if (rule.type === 'email' && !this.isValidEmail(value)) {
                errors[field] = rule.emailMessage || 'Invalid email format';
                isValid = false;
            }

            // Number validation
            if (rule.type === 'number' && !this.isValidNumber(value, rule.min, rule.max)) {
                errors[field] = rule.numberMessage || 'Invalid number';
                isValid = false;
            }

            // Custom validation
            if (rule.custom && typeof rule.custom === 'function') {
                const customResult = rule.custom(value, data);
                if (customResult !== true) {
                    errors[field] = customResult;
                    isValid = false;
                }
            }
        }

        return {
            isValid,
            errors
        };
    }

    /**
     * Sanitize HTML content
     * @param {string} str - String to sanitize
     * @returns {string} Sanitized string
     */
    static sanitizeHtml(str) {
        const temp = document.createElement('div');
        temp.textContent = str;
        return temp.innerHTML;
    }

    /**
     * Parse query parameters
     * @returns {Object} Query parameters object
     */
    static getQueryParams() {
        const params = {};
        const queryString = window.location.search.slice(1);
        const pairs = queryString.split('&');

        for (const pair of pairs) {
            const [key, value] = pair.split('=');
            if (key) {
                params[decodeURIComponent(key)] = decodeURIComponent(value || '');
            }
        }

        return params;
    }

    /**
     * Build query string
     * @param {Object} params - Parameters object
     * @returns {string} Query string
     */
    static buildQueryString(params) {
        const pairs = [];
        for (const [key, value] of Object.entries(params)) {
            if (value !== null && value !== undefined) {
                pairs.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
            }
        }
        return pairs.join('&');
    }

    /**
     * Format file size
     * @param {number} bytes - Size in bytes
     * @returns {string} Formatted file size
     */
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Generate color from string
     * @param {string} str - Input string
     * @returns {string} Hex color
     */
    static stringToColor(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
        }

        const color = (hash & 0x00FFFFFF).toString(16).toUpperCase();
        return '00000'.substring(0, 6 - color.length) + color;
    }

    /**
     * Convert hex color to RGB
     * @param {string} hex - Hex color
     * @returns {Object} RGB values
     */
    static hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }

    /**
     * Get contrast color (black or white) for background
     * @param {string} hex - Background hex color
     * @returns {string} Contrast color (black or white)
     */
    static getContrastColor(hex) {
        const rgb = this.hexToRgb(hex);
        if (!rgb) return '#000000';

        const brightness = (rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000;
        return brightness > 128 ? '#000000' : '#ffffff';
    }
}

// Export for global access
window.Utils = Utils;