/**
 * Dashboard JavaScript Module
 * Módulo JavaScript para el Dashboard Ejecutivo
 */

class DashboardManager {
    constructor() {
        this.charts = {};
        this.data = {};
        this.init();
    }

    init() {
        this.loadUserInfo();
        this.loadDashboardData();
        this.setupAutoRefresh();
    }

    loadUserInfo() {
        const userStr = localStorage.getItem('user');
        if (userStr) {
            const user = JSON.parse(userStr);
            document.getElementById('userName').textContent = user.full_name;
            document.getElementById('userRole').textContent = this.translateRole(user.role);
        }
    }

    translateRole(role) {
        const roles = {
            'admin': 'Administrador',
            'manager': 'Gerente',
            'staff': 'Personal'
        };
        return roles[role] || role;
    }

    async loadDashboardData() {
        try {
            // Show loading
            document.getElementById('loadingState').style.display = 'flex';

            // Load all dashboard data in parallel
            const [
                summary,
                stats,
                alerts,
                weeklyConsumption,
                categoryDistribution,
                topProducts,
                quickActions
            ] = await Promise.allSettled([
                this.fetchData('/api/dashboard/summary'),
                this.fetchData('/api/dashboard/stats-cards'),
                this.fetchData('/api/dashboard/alerts'),
                this.fetchData('/api/dashboard/weekly-consumption'),
                this.fetchData('/api/dashboard/category-distribution'),
                this.fetchData('/api/dashboard/top-products?limit=10'),
                this.fetchData('/api/dashboard/quick-actions')
            ]);

            // Process results
            this.processSummary(summary);
            this.processStatsCards(stats);
            this.processAlerts(alerts);
            this.processWeeklyConsumption(weeklyConsumption);
            this.processCategoryDistribution(categoryDistribution);
            this.processTopProducts(topProducts);
            this.processQuickActions(quickActions);

            // Hide loading
            document.getElementById('loadingState').style.display = 'none';

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            document.getElementById('loadingState').innerHTML = `
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
                    <p class="text-gray-600">Error al cargar datos</p>
                    <button onclick="dashboardManager.loadDashboardData()" class="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                        Reintentar
                    </button>
                </div>
            `;
        }
    }

    async fetchData(endpoint) {
        const token = localStorage.getItem('access_token');
        const response = await fetch(endpoint, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    processSummary(result) {
        if (result.status === 'fulfilled' && result.value) {
            this.data.summary = result.value;
        }
    }

    processStatsCards(result) {
        if (result.status === 'fulfilled' && result.value) {
            this.renderStatsCards(result.value.cards);
        }
    }

    processAlerts(result) {
        if (result.status === 'fulfilled' && result.value) {
            this.renderAlerts(result.value.alerts);
        }
    }

    processWeeklyConsumption(result) {
        if (result.status === 'fulfilled' && result.value) {
            this.renderWeeklyConsumptionChart(result.value);
        }
    }

    processCategoryDistribution(result) {
        if (result.status === 'fulfilled' && result.value) {
            this.renderCategoryChart(result.value);
        }
    }

    processTopProducts(result) {
        if (result.status === 'fulfilled' && result.value) {
            this.renderTopProductsTable(result.value.products);
        }
    }

    processQuickActions(result) {
        if (result.status === 'fulfilled' && result.value) {
            this.renderQuickActions(result.value.actions);
        }
    }

    renderStatsCards(cards) {
        const container = document.getElementById('statsCards');
        container.innerHTML = '';

        cards.forEach(card => {
            const changeClass = card.change_type === 'increase' ? 'text-green-600' :
                card.change_type === 'decrease' ? 'text-red-600' : 'text-gray-600';
            const changeIcon = card.change_type === 'increase' ? 'fa-arrow-up' :
                card.change_type === 'decrease' ? 'fa-arrow-down' : 'fa-minus';

            const cardElement = document.createElement('div');
            cardElement.className = 'stats-card bg-white rounded-xl shadow-sm p-6';
            cardElement.innerHTML = `
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">${card.title}</p>
                        <p class="text-2xl font-bold text-gray-900 mt-2">${card.value}</p>
                        <div class="flex items-center mt-2">
                            <i class="fas ${changeIcon} ${changeClass} text-xs mr-1"></i>
                            <span class="text-sm ${changeClass}">
                                ${card.change > 0 ? '+' : ''}${card.change}
                            </span>
                        </div>
                    </div>
                    <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                        <span class="text-2xl">${card.icon}</span>
                    </div>
                </div>
            `;
            container.appendChild(cardElement);
        });

        container.style.display = 'grid';
    }

    renderAlerts(alerts) {
        const container = document.getElementById('alertsList');
        const countElement = document.getElementById('alertCount');

        container.innerHTML = '';
        countElement.textContent = alerts.length;

        if (alerts.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-check-circle text-green-500 text-3xl mb-2"></i>
                    <p class="text-gray-600">No hay alertas activas</p>
                </div>
            `;
            return;
        }

        alerts.forEach(alert => {
            const severityColors = {
                critical: 'bg-red-100 text-red-800 border-red-200',
                high: 'bg-orange-100 text-orange-800 border-orange-200',
                medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
                low: 'bg-blue-100 text-blue-800 border-blue-200'
            };

            const alertElement = document.createElement('div');
            alertElement.className = `alert-item p-3 rounded-lg border ${severityColors[alert.severity] || severityColors.medium}`;
            alertElement.innerHTML = `
                <div class="flex items-start">
                    <i class="fas fa-exclamation-triangle mt-1 mr-2"></i>
                    <div class="flex-1">
                        <h4 class="font-medium">${alert.title}</h4>
                        <p class="text-sm mt-1">${alert.message}</p>
                        <p class="text-xs mt-2 opacity-75">
                            ${new Date(alert.created_at).toLocaleString()}
                        </p>
                    </div>
                </div>
            `;
            container.appendChild(alertElement);
        });
    }

    renderWeeklyConsumptionChart(data) {
        const ctx = document.getElementById('weeklyConsumptionChart').getContext('2d');

        // Destroy existing chart
        if (this.charts.weeklyConsumption) {
            this.charts.weeklyConsumption.destroy();
        }

        this.charts.weeklyConsumption = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.chart_data.labels,
                datasets: [{
                    label: 'Consumo ($)',
                    data: data.chart_data.values,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45
                        }
                    }
                }
            }
        });
    }

    renderCategoryChart(data) {
        const ctx = document.getElementById('categoryChart').getContext('2d');

        // Destroy existing chart
        if (this.charts.category) {
            this.charts.category.destroy();
        }

        const labels = data.categories.map(cat => cat.name);
        const values = data.categories.map(cat => cat.value);
        const backgroundColors = [
            '#3b82f6',
            '#10b981',
            '#f59e0b',
            '#ef4444',
            '#8b5cf6',
            '#06b6d4',
            '#84cc16',
            '#f97316'
        ];

        this.charts.category = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: backgroundColors,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    renderTopProductsTable(products) {
        const tbody = document.getElementById('topProductsTable');
        tbody.innerHTML = '';

        if (products.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-8 text-gray-500">
                        No hay productos para mostrar
                    </td>
                </tr>
            `;
            return;
        }

        products.forEach(product => {
            const statusColor = this.getStockStatusColor(product.current_stock, product.min_stock || 0);
            const statusText = product.current_stock <= (product.min_stock || 0) ? 'Bajo' : 'Normal';

            const row = document.createElement('tr');
            row.className = 'border-b border-gray-100 hover:bg-gray-50';
            row.innerHTML = `
                <td class="py-3 px-4">
                    <div class="font-medium text-gray-900">${product.name}</div>
                    <div class="text-sm text-gray-500">${product.category}</div>
                </td>
                <td class="py-3 px-4 text-gray-600">${product.category}</td>
                <td class="py-3 px-4">
                    <span class="font-medium">${product.current_stock}</span>
                    <span class="text-sm text-gray-500">${product.unit}</span>
                </td>
                <td class="py-3 px-4">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full ${statusColor}">
                        ${statusText}
                    </span>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    renderQuickActions(actions) {
        const container = document.getElementById('quickActions');
        container.innerHTML = '';

        if (actions.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-check-circle text-green-500 text-3xl mb-2"></i>
                    <p class="text-gray-600">No hay acciones pendientes</p>
                </div>
            `;
            return;
        }

        actions.forEach(action => {
            const priorityColors = {
                high: 'border-red-200 bg-red-50 text-red-800',
                medium: 'border-yellow-200 bg-yellow-50 text-yellow-800',
                low: 'border-green-200 bg-green-50 text-green-800'
            };

            const actionIcons = {
                count: 'fa-clipboard-check',
                invoice: 'fa-file-invoice',
                stock: 'fa-boxes',
                waste: 'fa-trash-alt'
            };

            const actionElement = document.createElement('div');
            actionElement.className = `p-4 rounded-lg border ${priorityColors[action.priority]} cursor-pointer hover:shadow-md transition-all`;
            actionElement.innerHTML = `
                <div class="flex items-center">
                    <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center mr-3">
                        <i class="fas ${actionIcons[action.type]} text-gray-600"></i>
                    </div>
                    <div class="flex-1">
                        <h4 class="font-medium">${action.title}</h4>
                        <p class="text-sm mt-1">${action.description}</p>
                    </div>
                    <i class="fas fa-chevron-right"></i>
                </div>
            `;

            actionElement.addEventListener('click', () => {
                this.handleQuickAction(action.action);
            });

            container.appendChild(actionElement);
        });
    }

    handleQuickAction(action) {
        const actions = {
            start_count: () => window.location.href = 'count.html',
            process_invoices: () => window.location.href = 'ocr.html',
            restock_products: () => window.location.href = 'inventory.html',
            register_waste: () => window.location.href = 'waste.html'
        };

        if (actions[action]) {
            actions[action]();
        }
    }

    getStockStatusColor(current, minimum) {
        if (current <= minimum) {
            return 'bg-red-100 text-red-800';
        } else if (current <= minimum * 1.5) {
            return 'bg-yellow-100 text-yellow-800';
        } else {
            return 'bg-green-100 text-green-800';
        }
    }

    setupAutoRefresh() {
        // Auto-refresh dashboard every 5 minutes
        setInterval(() => {
            this.loadDashboardData();
        }, 5 * 60 * 1000);
    }

    async filterByCategory() {
        const select = document.getElementById('categoryFilter');
        const category = select.value;

        let endpoint = '/api/dashboard/top-products?limit=20';
        if (category) {
            endpoint = `/api/dashboard/products-by-category?category_name=${category}`;
        }

        try {
            const data = await this.fetchData(endpoint);
            const products = data.products || [];
            this.renderTopProductsTable(products);
        } catch (error) {
            console.error('Error filtering:', error);
        }
    }

    async printCategory() {
        const select = document.getElementById('categoryFilter');
        const category = select.value;

        let url = '/reports.html';
        if (category) {
            url += `?category=${encodeURIComponent(category)}`;
        }

        window.open(url, '_blank');
    }
}

// Initialize dashboard manager
const dashboardManager = new DashboardManager();

// Export for global access
window.dashboardManager = dashboardManager;