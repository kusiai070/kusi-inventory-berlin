/**
 * Waste Management JavaScript Module
 * Módulo JavaScript para Gestión de Mermas
 */

class WasteManager {
    constructor() {
        this.wasteRecords = [];
        this.products = [];
        this.wasteTypes = [];
        this.chart = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.setDefaultDates();
    }

    setupEventListeners() {
        // Add waste button
        document.getElementById('addWasteBtn').addEventListener('click', () => this.openModal());
        
        // Modal controls
        document.getElementById('closeModal').addEventListener('click', () => this.closeModal());
        document.getElementById('cancelWaste').addEventListener('click', () => this.closeModal());
        document.getElementById('wasteForm').addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Product selection
        document.getElementById('wasteProduct').addEventListener('change', (e) => this.updateCost(e.target.value));
        document.getElementById('wasteQuantity').addEventListener('input', () => this.calculateCost());
        
        // Filters
        document.getElementById('dateFrom').addEventListener('change', () => this.applyFilters());
        document.getElementById('dateTo').addEventListener('change', () => this.applyFilters());
        document.getElementById('wasteTypeFilter').addEventListener('change', () => this.applyFilters());
        document.getElementById('clearFilters').addEventListener('click', () => this.clearFilters());
        
        // Export
        document.getElementById('exportBtn').addEventListener('click', () => this.exportWaste());
        
        // Stats
        document.getElementById('statsBtn').addEventListener('click', () => this.showStats());
        
        // Close modal on outside click
        document.getElementById('wasteModal').addEventListener('click', (e) => {
            if (e.target.id === 'wasteModal') {
                this.closeModal();
            }
        });
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadProducts(),
                this.loadWasteTypes(),
                this.loadWasteRecords(),
                this.loadStats()
            ]);
            
            this.renderWasteChart();
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    async loadProducts() {
        try {
            const response = await authManager.authenticatedFetch('/api/products?limit=1000');
            this.products = await response.json();
            this.populateProductSelect();
        } catch (error) {
            console.error('Error loading products:', error);
        }
    }

    populateProductSelect() {
        const select = document.getElementById('wasteProduct');
        select.innerHTML = '<option value="">Seleccionar producto</option>';
        
        this.products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = `${product.name} (${product.category_name}) - Stock: ${product.current_stock} ${product.unit}`;
            select.appendChild(option);
        });
    }

    async loadWasteTypes() {
        try {
            const response = await authManager.authenticatedFetch('/api/wastes/types');
            this.wasteTypes = response.waste_types;
        } catch (error) {
            console.error('Error loading waste types:', error);
            // Fallback
            this.wasteTypes = [
                { type: 'preparation', name: 'Preparación' },
                { type: 'expired', name: 'Vencido' },
                { type: 'damaged', name: 'Dañado' }
            ];
        }
    }

    async loadWasteRecords() {
        try {
            const dateFrom = document.getElementById('dateFrom').value;
            const dateTo = document.getElementById('dateTo').value;
            const wasteType = document.getElementById('wasteTypeFilter').value;
            
            let url = '/api/wastes?limit=100';
            if (dateFrom) url += `&date_from=${dateFrom}`;
            if (dateTo) url += `&date_to=${dateTo}`;
            if (wasteType) url += `&waste_type=${wasteType}`;
            
            const response = await authManager.authenticatedFetch(url);
            this.wasteRecords = await response.json();
            
            this.renderWasteTable();
            this.updateWasteCount();
        } catch (error) {
            console.error('Error loading waste records:', error);
        }
    }

    async loadStats() {
        try {
            const response = await authManager.authenticatedFetch('/api/wastes/stats/summary?days=30');
            const stats = await response.json();
            this.renderStatsCards(stats);
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    renderStatsCards(stats) {
        const container = document.getElementById('statsCards');
        container.innerHTML = `
            <div class="bg-white rounded-xl shadow-sm p-6">
                <div class="flex items-center">
                    <div class="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                        <i class="fas fa-exclamation-triangle text-red-600 text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Total Mermas (30 días)</p>
                        <p class="text-2xl font-bold text-gray-900">${Utils.formatCurrency(stats.total_waste_value)}</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-xl shadow-sm p-6">
                <div class="flex items-center">
                    <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                        <i class="fas fa-list text-purple-600 text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Total Registros</p>
                        <p class="text-2xl font-bold text-gray-900">${stats.total_records}</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-xl shadow-sm p-6">
                <div class="flex items-center">
                    <div class="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                        <i class="fas fa-percentage text-yellow-600 text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Promedio Diario</p>
                        <p class="text-2xl font-bold text-gray-900">${Utils.formatCurrency(stats.total_waste_value / 30)}</p>
                    </div>
                </div>
            </div>
        `;
    }

    renderWasteTable() {
        const tbody = document.getElementById('wasteTable');
        tbody.innerHTML = '';

        if (this.wasteRecords.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-8 text-gray-500">
                        <i class="fas fa-trash-alt text-4xl mb-4"></i>
                        <p>No hay registros de merma</p>
                    </td>
                </tr>
            `;
            return;
        }

        this.wasteRecords.forEach(record => {
            const row = document.createElement('tr');
            row.className = 'border-b border-gray-100 hover:bg-gray-50';
            
            row.innerHTML = `
                <td class="py-3 px-4">
                    <div class="font-medium text-gray-900">${record.product_name}</div>
                </td>
                <td class="py-3 px-4">${Utils.formatNumber(record.quantity)} ${record.unit}</td>
                <td class="py-3 px-4">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full ${this.getWasteTypeClass(record.waste_type)}">
                        ${this.translateWasteType(record.waste_type)}
                    </span>
                </td>
                <td class="py-3 px-4 font-semibold text-red-600">${Utils.formatCurrency(record.cost)}</td>
                <td class="py-3 px-4 text-gray-600">${record.reason || '-'}</td>
                <td class="py-3 px-4">${new Date(record.created_at).toLocaleDateString()}</td>
                <td class="py-3 px-4">${record.user_name}</td>
                <td class="py-3 px-4">
                    <div class="flex space-x-2">
                        <button onclick="wasteManager.viewDetails(${record.id})" class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button onclick="wasteManager.deleteRecord(${record.id})" class="text-red-600 hover:text-red-800">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;

            tbody.appendChild(row);
        });
    }

    renderWasteChart() {
        const ctx = document.getElementById('wasteChart')?.getContext('2d');
        if (!ctx) return;

        // Group waste by type
        const wasteByType = {};
        this.wasteRecords.forEach(record => {
            if (!wasteByType[record.waste_type]) {
                wasteByType[record.waste_type] = 0;
            }
            wasteByType[record.waste_type] += record.cost;
        });

        const labels = Object.keys(wasteByType).map(type => this.translateWasteType(type));
        const values = Object.values(wasteByType);

        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        '#ef4444', '#f59e0b', '#8b5cf6'
                    ],
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

    updateWasteCount() {
        document.getElementById('wasteCount').textContent = `${this.wasteRecords.length} registros`;
    }

    getWasteTypeClass(type) {
        switch (type) {
            case 'preparation': return 'bg-blue-100 text-blue-800';
            case 'expired': return 'bg-red-100 text-red-800';
            case 'damaged': return 'bg-yellow-100 text-yellow-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }

    translateWasteType(type) {
        const translations = {
            preparation: 'Preparación',
            expired: 'Vencido',
            damaged: 'Dañado'
        };
        return translations[type] || type;
    }

    setDefaultDates() {
        const today = new Date();
        const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
        
        document.getElementById('dateFrom').value = thirtyDaysAgo.toISOString().split('T')[0];
        document.getElementById('dateTo').value = today.toISOString().split('T')[0];
    }

    updateCost(productId) {
        const product = this.products.find(p => p.id == productId);
        if (product) {
            const quantity = parseFloat(document.getElementById('wasteQuantity').value) || 0;
            const cost = quantity * product.cost_price;
            document.getElementById('wasteCost').value = cost.toFixed(2);
        }
    }

    calculateCost() {
        const productId = document.getElementById('wasteProduct').value;
        this.updateCost(productId);
    }

    openModal() {
        document.getElementById('wasteModal').classList.add('active');
        document.getElementById('wasteForm').reset();
        document.getElementById('wasteCost').value = '';
    }

    closeModal() {
        document.getElementById('wasteModal').classList.remove('active');
        document.getElementById('wasteForm').reset();
    }

    async handleSubmit(e) {
        e.preventDefault();

        const productId = document.getElementById('wasteProduct').value;
        const quantity = parseFloat(document.getElementById('wasteQuantity').value);
        const wasteType = document.getElementById('wasteType').value;
        const reason = document.getElementById('wasteReason').value;

        if (!productId || !quantity || !wasteType) {
            Utils.showNotification('Por favor complete todos los campos requeridos', 'error');
            return;
        }

        const product = this.products.find(p => p.id == productId);
        if (!product) {
            Utils.showNotification('Producto no válido', 'error');
            return;
        }

        if (quantity > product.current_stock) {
            Utils.showNotification('La cantidad no puede exceder el stock actual', 'error');
            return;
        }

        const cost = quantity * product.cost_price;

        try {
            const hideLoading = Utils.showLoading('Registrando merma...');

            const response = await authManager.authenticatedFetch('/api/wastes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    product_id: productId,
                    quantity: quantity,
                    waste_type: wasteType,
                    reason: reason,
                    cost: cost
                })
            });

            hideLoading();

            if (response.ok) {
                Utils.showNotification('Merma registrada exitosamente', 'success');
                this.closeModal();
                
                // Update stock locally
                product.current_stock -= quantity;
                
                // Reload data
                await this.loadWasteRecords();
                await this.loadStats();
                this.renderWasteChart();
            } else {
                const error = await response.json();
                Utils.showNotification(error.detail || 'Error al registrar merma', 'error');
            }
        } catch (error) {
            console.error('Error registering waste:', error);
            Utils.showNotification('Error de conexión', 'error');
        }
    }

    async applyFilters() {
        await this.loadWasteRecords();
        this.renderWasteChart();
    }

    clearFilters() {
        this.setDefaultDates();
        document.getElementById('wasteTypeFilter').value = '';
        this.applyFilters();
    }

    async exportWaste() {
        try {
            const dateFrom = document.getElementById('dateFrom').value;
            const dateTo = document.getElementById('dateTo').value;
            const wasteType = document.getElementById('wasteTypeFilter').value;
            
            let url = '/api/wastes?limit=1000';
            if (dateFrom) url += `&date_from=${dateFrom}`;
            if (dateTo) url += `&date_to=${dateTo}`;
            if (wasteType) url += `&waste_type=${wasteType}`;
            
            const response = await authManager.authenticatedFetch(url);
            const records = await response.json();
            
            // Generate CSV content
            const headers = ['Producto', 'Cantidad', 'Unidad', 'Tipo', 'Costo', 'Motivo', 'Fecha', 'Usuario'];
            const csvContent = [
                headers.join(','),
                ...records.map(record => [
                    `"${record.product_name}"`,
                    record.quantity,
                    `"${record.unit}"`,
                    `"${this.translateWasteType(record.waste_type)}"`,
                    record.cost,
                    `"${record.reason || ''}"`,
                    `"${new Date(record.created_at).toLocaleDateString()}"`,
                    `"${record.user_name}"`
                ].join(','))
            ].join('\n');
            
            // Create and download file
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            Utils.downloadFile(blob, `mermas_${new Date().toISOString().split('T')[0]}.csv`);
            
            Utils.showNotification('Mermas exportadas exitosamente', 'success');
        } catch (error) {
            console.error('Error exporting waste:', error);
            Utils.showNotification('Error al exportar', 'error');
        }
    }

    viewDetails(id) {
        // Implementation for viewing waste details
        Utils.showNotification('Función no implementada', 'info');
    }

    async deleteRecord(id) {
        const confirmed = confirm('¿Está seguro de que desea eliminar este registro de merma?');
        if (!confirmed) return;

        try {
            const hideLoading = Utils.showLoading('Eliminando registro...');
            
            const response = await authManager.authenticatedFetch(`/api/wastes/${id}`, {
                method: 'DELETE'
            });
            
            hideLoading();
            
            if (response.ok) {
                Utils.showNotification('Registro eliminado exitosamente', 'success');
                await this.loadWasteRecords();
                await this.loadStats();
                this.renderWasteChart();
            } else {
                const error = await response.json();
                Utils.showNotification(error.detail || 'Error al eliminar registro', 'error');
            }
        } catch (error) {
            console.error('Error deleting waste record:', error);
            Utils.showNotification('Error de conexión', 'error');
        }
    }

    showStats() {
        // Implementation for showing detailed statistics
        Utils.showNotification('Estadísticas detalladas no implementadas', 'info');
    }
}

// Initialize waste manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (typeof authManager !== 'undefined' && authManager.isAuthenticated()) {
        window.wasteManager = new WasteManager();
    }
});