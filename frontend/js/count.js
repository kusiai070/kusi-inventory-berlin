/**
 * Physical Count JavaScript Module
 * Módulo JavaScript para Conteo Físico de Inventario
 */

class CountManager {
    constructor() {
        this.currentCount = null;
        this.countItems = [];
        this.categories = [];
        this.products = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
    }

    setupEventListeners() {
        // Count type selection
        document.getElementById('countType').addEventListener('change', (e) => {
            this.toggleCategorySelect(e.target.value);
        });

        // Start count
        document.getElementById('startCountBtn').addEventListener('click', () => this.startCount());

        // Count actions
        document.getElementById('savePartialBtn').addEventListener('click', () => this.savePartial());
        document.getElementById('finalizeBtn').addEventListener('click', () => this.finalizeCount());

        // Export
        document.getElementById('exportExcel').addEventListener('click', () => this.exportToExcel());
        document.getElementById('exportPDF').addEventListener('click', () => this.exportToPDF());

        // History
        document.getElementById('historyBtn').addEventListener('click', () => this.showHistory());
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadCategories(),
                this.checkActiveCount()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    async loadCategories() {
        try {
            const response = await authManager.authenticatedFetch('/api/products/categories/list');
            this.categories = await response.json();
            this.populateCategorySelect();
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    populateCategorySelect() {
        const select = document.getElementById('categoryId');
        select.innerHTML = '<option value="">Seleccionar categoría</option>';

        this.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.name;
            select.appendChild(option);
        });
    }

    toggleCategorySelect(countType) {
        const categorySelect = document.getElementById('categorySelect');
        if (countType === 'category') {
            categorySelect.style.display = 'block';
        } else {
            categorySelect.style.display = 'none';
        }
    }

    async checkActiveCount() {
        try {
            const response = await authManager.authenticatedFetch('/api/counts/current');
            const data = await response.json();

            if (data.count) {
                this.currentCount = data.count;
                this.countItems = data.items || [];
                this.showActiveCount();
            }
        } catch (error) {
            console.error('Error checking active count:', error);
        }
    }

    async startCount() {
        const countType = document.getElementById('countType').value;
        const categoryId = document.getElementById('categoryId').value;

        if (countType === 'category' && !categoryId) {
            Utils.showNotification('Por favor seleccione una categoría', 'error');
            return;
        }

        try {
            const hideLoading = Utils.showLoading('Iniciando conteo...');

            // Build URL with query parameters
            const url = `/api/counts/start?count_type=${countType}${categoryId ? `&category_id=${categoryId}` : ''}`;

            const response = await authManager.authenticatedFetch(url, {
                method: 'POST'
            });

            hideLoading();

            if (response.ok) {
                const result = await response.json();
                this.currentCount = {
                    id: result.count_id,
                    count_type: countType,
                    started_at: new Date().toISOString()
                };
                this.countItems = result.items || [];

                Utils.showNotification('Conteo iniciado exitosamente', 'success');
                this.showActiveCount();
            } else {
                const error = await response.json();
                Utils.showNotification(error.detail || 'Error al iniciar conteo', 'error');
            }
        } catch (error) {
            console.error('Error starting count:', error);
            Utils.showNotification('Error de conexión', 'error');
        }
    }

    showActiveCount() {
        document.getElementById('startSection').style.display = 'none';
        document.getElementById('activeCountSection').style.display = 'block';
        document.getElementById('countItemsSection').style.display = 'block';
        document.getElementById('summarySection').style.display = 'grid';
        document.getElementById('exportSection').style.display = 'block';

        // Update count info
        document.getElementById('currentCountType').textContent = this.translateCountType(this.currentCount.count_type);
        document.getElementById('countStartTime').textContent = new Date(this.currentCount.started_at).toLocaleString();

        this.renderCountItems();
        this.updateSummary();
    }

    translateCountType(type) {
        const types = {
            daily: 'Diario',
            weekly: 'Semanal',
            category: 'Por Categoría'
        };
        return types[type] || type;
    }

    renderCountItems() {
        const tbody = document.getElementById('countItemsTable');
        tbody.innerHTML = '';

        this.countItems.forEach((item, index) => {
            const difference = item.physical_count - item.system_stock;
            const differenceClass = difference > 0 ? 'difference-positive' : difference < 0 ? 'difference-negative' : '';

            const row = document.createElement('tr');
            row.className = 'border-b border-gray-100 hover:bg-gray-50';

            row.innerHTML = `
                <td class="py-3 px-4">
                    <div class="font-medium text-gray-900">${item.product_name}</div>
                    <div class="text-sm text-gray-500">${item.product?.barcode || ''}</div>
                </td>
                <td class="py-3 px-4">${item.product?.unit || 'unidad'}</td>
                <td class="py-3 px-4 font-medium">${Utils.formatNumber(item.system_stock)}</td>
                <td class="py-3 px-4">
                    <input type="number" value="${item.physical_count}" step="0.01" min="0"
                           class="w-20 px-2 py-1 border border-gray-300 rounded text-center"
                           onchange="countManager.updatePhysicalCount(${index}, this.value)">
                </td>
                <td class="py-3 px-4 font-medium ${differenceClass}">
                    ${difference > 0 ? '+' : ''}${Utils.formatNumber(difference)}
                </td>
                <td class="py-3 px-4">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full ${this.getStatusClass(difference)}">
                        ${this.getStatusText(difference)}
                    </span>
                </td>
            `;

            tbody.appendChild(row);
        });

        this.updateProgress();
    }

    updatePhysicalCount(index, value) {
        const physicalCount = parseFloat(value) || 0;
        this.countItems[index].physical_count = physicalCount;
        this.countItems[index].difference = physicalCount - this.countItems[index].system_stock;

        this.renderCountItems();
        this.updateSummary();
    }

    getStatusClass(difference) {
        if (difference > 0) return 'bg-green-100 text-green-800';
        if (difference < 0) return 'bg-red-100 text-red-800';
        return 'bg-blue-100 text-blue-800';
    }

    getStatusText(difference) {
        if (difference > 0) return 'Sobrante';
        if (difference < 0) return 'Faltante';
        return 'Correcto';
    }

    updateProgress() {
        const total = this.countItems.length;
        const counted = this.countItems.filter(item => item.physical_count > 0).length;
        const progress = total > 0 ? (counted / total) * 100 : 0;

        document.getElementById('progressCounter').textContent = `${counted}/${total}`;
        document.getElementById('progressBar').style.width = `${progress}%`;
    }

    updateSummary() {
        const total = this.countItems.length;
        const counted = this.countItems.filter(item => item.physical_count > 0).length;
        const differences = this.countItems.filter(item => item.difference !== 0).length;

        document.getElementById('totalItems').textContent = total;
        document.getElementById('countedItems').textContent = counted;
        document.getElementById('differences').textContent = differences;
    }

    async savePartial() {
        const itemsToSave = this.countItems.filter(item => item.physical_count > 0);

        if (itemsToSave.length === 0) {
            Utils.showNotification('No hay items para guardar', 'warning');
            return;
        }

        try {
            const hideLoading = Utils.showLoading('Guardando progreso...');

            const response = await authManager.authenticatedFetch('/api/counts/save-partial', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    items: itemsToSave.map((item, index) => ({
                        item_id: item.id || index,
                        physical_count: item.physical_count
                    }))
                })
            });

            hideLoading();

            if (response.ok) {
                const result = await response.json();
                Utils.showNotification(`Progreso guardado: ${result.updated_items} items`, 'success');
            } else {
                const error = await response.json();
                Utils.showNotification(error.detail || 'Error al guardar progreso', 'error');
            }
        } catch (error) {
            console.error('Error saving partial:', error);
            Utils.showNotification('Error de conexión', 'error');
        }
    }

    async finalizeCount() {
        const counted = this.countItems.filter(item => item.physical_count > 0).length;

        if (counted < this.countItems.length) {
            const confirmed = await this.showConfirmDialog(
                'Finalizar Conteo',
                `Aún faltan ${this.countItems.length - counted} productos por contar. ¿Desea finalizar de todas formas?`
            );

            if (!confirmed) return;
        }

        const applyAdjustments = await this.showConfirmDialog(
            'Aplicar Ajustes',
            '¿Desea aplicar los ajustes al inventario automáticamente?'
        );

        try {
            const hideLoading = Utils.showLoading('Finalizando conteo...');

            const response = await authManager.authenticatedFetch('/api/counts/finalize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    apply_adjustments: applyAdjustments
                })
            });

            hideLoading();

            if (response.ok) {
                const result = await response.json();
                Utils.showNotification(`Conteo finalizado: ${result.adjustments_made} ajustes aplicados`, 'success');

                // Reset to start state
                this.resetToStart();
            } else {
                const error = await response.json();
                Utils.showNotification(error.detail || 'Error al finalizar conteo', 'error');
            }
        } catch (error) {
            console.error('Error finalizing count:', error);
            Utils.showNotification('Error de conexión', 'error');
        }
    }

    resetToStart() {
        this.currentCount = null;
        this.countItems = [];

        document.getElementById('startSection').style.display = 'block';
        document.getElementById('activeCountSection').style.display = 'none';
        document.getElementById('countItemsSection').style.display = 'none';
        document.getElementById('summarySection').style.display = 'none';
        document.getElementById('exportSection').style.display = 'none';
    }

    async exportToExcel() {
        try {
            const hideLoading = Utils.showLoading('Exportando a Excel...');

            // Create CSV content
            const headers = ['Producto', 'Unidad', 'Stock Sistema', 'Conteo Real', 'Diferencia', 'Estado'];
            const csvContent = [
                headers.join(','),
                ...this.countItems.map(item => [
                    `"${item.product_name}"`,
                    `"${item.product?.unit || 'unidad'}"`,
                    item.system_stock,
                    item.physical_count,
                    item.physical_count - item.system_stock,
                    `"${this.getStatusText(item.physical_count - item.system_stock)}"`
                ].join(','))
            ].join('\n');

            // Create and download file
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            Utils.downloadFile(blob, `conteo_${new Date().toISOString().split('T')[0]}.csv`);

            hideLoading();
            Utils.showNotification('Conteo exportado exitosamente', 'success');
        } catch (error) {
            console.error('Error exporting to Excel:', error);
            Utils.showNotification('Error al exportar', 'error');
        }
    }

    async exportToPDF() {
        Utils.showNotification('Función no implementada', 'info');
    }

    async showHistory() {
        try {
            const response = await authManager.authenticatedFetch('/api/counts/history?limit=20');
            const history = await response.json();

            // Show history modal or navigate to history page
            console.log('Count history:', history);
            Utils.showNotification('Historial cargado en consola', 'info');

        } catch (error) {
            console.error('Error loading history:', error);
            Utils.showNotification('Error al cargar historial', 'error');
        }
    }

    showConfirmDialog(title, message) {
        return new Promise((resolve) => {
            const confirmed = confirm(`${title}\n\n${message}`);
            resolve(confirmed);
        });
    }
}

// Initialize count manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    if (typeof authManager !== 'undefined' && authManager.isAuthenticated()) {
        window.countManager = new CountManager();
    }
});