/**
 * Reports JavaScript Module
 * Módulo JavaScript para Sistema de Reportes
 */

class ReportsManager {
    constructor() {
        this.currentReport = null;
        this.categories = [];
        this.chart = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.setDefaultDates();
    }

    setupEventListeners() {
        // Generate button
        document.getElementById('generateBtn').addEventListener('click', () => this.generateCurrentReport());
        
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => this.refreshData());
        
        // Clear filters
        document.getElementById('clearFilters').addEventListener('click', () => this.clearFilters());
        
        // Date change listeners
        document.getElementById('dateFrom').addEventListener('change', () => this.validateDateRange());
        document.getElementById('dateTo').addEventListener('change', () => this.validateDateRange());
    }

    async loadInitialData() {
        try {
            await this.loadCategories();
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
        const select = document.getElementById('reportCategory');
        select.innerHTML = '<option value="">Todas</option>';
        
        this.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.name;
            select.appendChild(option);
        });
    }

    setDefaultDates() {
        const today = new Date();
        const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
        
        document.getElementById('dateFrom').value = thirtyDaysAgo.toISOString().split('T')[0];
        document.getElementById('dateTo').value = today.toISOString().split('T')[0];
    }

    validateDateRange() {
        const dateFrom = new Date(document.getElementById('dateFrom').value);
        const dateTo = new Date(document.getElementById('dateTo').value);
        
        if (dateFrom && dateTo && dateFrom > dateTo) {
            Utils.showNotification('La fecha de inicio no puede ser mayor a la fecha fin', 'error');
            return false;
        }
        
        return true;
    }

    generateReport(type) {
        this.currentReport = type;
        this.generateCurrentReport();
    }

    generateCurrentReport() {
        if (!this.currentReport) {
            Utils.showNotification('Por favor seleccione un tipo de reporte', 'warning');
            return;
        }

        if (!this.validateDateRange()) {
            return;
        }

        const dateFrom = document.getElementById('dateFrom').value;
        const dateTo = document.getElementById('dateTo').value;
        const categoryId = document.getElementById('reportCategory').value;

        this.showLoading();

        // Generate report based on type
        switch (this.currentReport) {
            case 'inventory-valuation':
                this.generateInventoryValuation();
                break;
            case 'consumption':
                this.generateConsumptionReport(dateFrom, dateTo, categoryId);
                break;
            case 'waste-analysis':
                this.generateWasteAnalysis(dateFrom, dateTo);
                break;
            case 'purchases':
                this.generatePurchasesReport(dateFrom, dateTo);
                break;
            case 'rotation-analysis':
                this.generateRotationAnalysis();
                break;
            case 'obsolete-products':
                this.generateObsoleteProducts();
                break;
            default:
                Utils.showNotification('Tipo de reporte no válido', 'error');
                this.hideLoading();
        }
    }

    async generateInventoryValuation() {
        try {
            const response = await authManager.authenticatedFetch('/api/reports/inventory-valuation');
            const report = await response.json();
            
            this.renderInventoryValuation(report);
        } catch (error) {
            console.error('Error generating inventory valuation:', error);
            Utils.showNotification('Error al generar reporte', 'error');
        }
    }

    async generateConsumptionReport(dateFrom, dateTo, categoryId) {
        try {
            let url = `/api/reports/consumption?date_from=${dateFrom}&date_to=${dateTo}`;
            if (categoryId) url += `&category_id=${categoryId}`;
            
            const response = await authManager.authenticatedFetch(url);
            const report = await response.json();
            
            this.renderConsumptionReport(report);
        } catch (error) {
            console.error('Error generating consumption report:', error);
            Utils.showNotification('Error al generar reporte', 'error');
        }
    }

    async generateWasteAnalysis(dateFrom, dateTo) {
        try {
            const response = await authManager.authenticatedFetch(`/api/reports/waste-analysis?date_from=${dateFrom}&date_to=${dateTo}`);
            const report = await response.json();
            
            this.renderWasteAnalysis(report);
        } catch (error) {
            console.error('Error generating waste analysis:', error);
            Utils.showNotification('Error al generar reporte', 'error');
        }
    }

    async generatePurchasesReport(dateFrom, dateTo) {
        try {
            const response = await authManager.authenticatedFetch(`/api/reports/purchases?date_from=${dateFrom}&date_to=${dateTo}`);
            const report = await response.json();
            
            this.renderPurchasesReport(report);
        } catch (error) {
            console.error('Error generating purchases report:', error);
            Utils.showNotification('Error al generar reporte', 'error');
        }
    }

    async generateRotationAnalysis() {
        try {
            const response = await authManager.authenticatedFetch('/api/reports/rotation-analysis');
            const report = await response.json();
            
            this.renderRotationAnalysis(report);
        } catch (error) {
            console.error('Error generating rotation analysis:', error);
            Utils.showNotification('Error al generar reporte', 'error');
        }
    }

    async generateObsoleteProducts() {
        try {
            const response = await authManager.authenticatedFetch('/api/reports/obsolete-products');
            const report = await response.json();
            
            this.renderObsoleteProducts(report);
        } catch (error) {
            console.error('Error generating obsolete products report:', error);
            Utils.showNotification('Error al generar reporte', 'error');
        }
    }

    renderInventoryValuation(report) {
        const container = document.getElementById('reportData');
        container.innerHTML = `
            <div class="flex items-center justify-between mb-6">
                <h3 class="text-xl font-semibold text-gray-800">Inventario Valorizado</h3>
                <div class="flex space-x-2">
                    <button onclick="reportsManager.exportToExcel('inventory')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                        <i class="fas fa-file-excel mr-2"></i>Excel
                    </button>
                    <button onclick="reportsManager.exportToPDF('inventory')" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
                        <i class="fas fa-file-pdf mr-2"></i>PDF
                    </button>
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div class="bg-blue-50 rounded-lg p-4">
                    <p class="text-sm text-gray-600">Total Productos</p>
                    <p class="text-2xl font-bold text-blue-600">${report.total_products}</p>
                </div>
                <div class="bg-green-50 rounded-lg p-4">
                    <p class="text-sm text-gray-600">Valor Total</p>
                    <p class="text-2xl font-bold text-green-600">${Utils.formatCurrency(report.total_inventory_value)}</p>
                </div>
                <div class="bg-purple-50 rounded-lg p-4">
                    <p class="text-sm text-gray-600">Promedio por Producto</p>
                    <p class="text-2xl font-bold text-purple-600">${Utils.formatCurrency(report.total_inventory_value / report.total_products)}</p>
                </div>
            </div>
            
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead>
                        <tr class="border-b border-gray-200">
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Producto</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Categoría</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Stock</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Precio Costo</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Valor Total</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${report.items.map(item => `
                            <tr class="border-b border-gray-100 hover:bg-gray-50">
                                <td class="py-3 px-4">
                                    <div class="font-medium text-gray-900">${item.product_name}</div>
                                </td>
                                <td class="py-3 px-4 text-gray-600">${item.category}</td>
                                <td class="py-3 px-4">${Utils.formatNumber(item.current_stock)} ${item.unit}</td>
                                <td class="py-3 px-4">${Utils.formatCurrency(item.cost_price)}</td>
                                <td class="py-3 px-4 font-semibold text-green-600">${Utils.formatCurrency(item.total_value)}</td>
                                <td class="py-3 px-4">
                                    <span class="px-2 py-1 text-xs font-semibold rounded-full ${this.getStockStatusClass(item.stock_status)}">
                                        ${item.stock_status}
                                    </span>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        this.hideLoading();
    }

    renderConsumptionReport(report) {
        const container = document.getElementById('reportData');
        
        // Create chart data
        const chartData = {
            labels: report.items.map(item => item.name),
            values: report.items.map(item => item.cost_value)
        };

        container.innerHTML = `
            <div class="flex items-center justify-between mb-6">
                <h3 class="text-xl font-semibold text-gray-800">Consumo por ${report.grouped_by}</h3>
                <div class="flex space-x-2">
                    <button onclick="reportsManager.exportToExcel('consumption')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                        <i class="fas fa-file-excel mr-2"></i>Excel
                    </button>
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div class="bg-blue-50 rounded-lg p-4">
                    <p class="text-sm text-gray-600">Período</p>
                    <p class="text-lg font-bold text-blue-600">${report.period.from} - ${report.period.to}</p>
                </div>
                <div class="bg-green-50 rounded-lg p-4">
                    <p class="text-sm text-gray-600">Total Consumido</p>
                    <p class="text-2xl font-bold text-green-600">${Utils.formatCurrency(report.total_consumption_value)}</p>
                </div>
            </div>
            
            <div class="h-64 mb-6">
                <canvas id="consumptionChart"></canvas>
            </div>
            
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead>
                        <tr class="border-b border-gray-200">
                            <th class="text-left py-3 px-4 font-medium text-gray-700">${report.grouped_by === 'category' ? 'Categoría' : 'Producto'}</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Cantidad</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Costo</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">%</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${report.items.map(item => `
                            <tr class="border-b border-gray-100 hover:bg-gray-50">
                                <td class="py-3 px-4 font-medium">${item.name}</td>
                                <td class="py-3 px-4">${Utils.formatNumber(item.quantity)}</td>
                                <td class="py-3 px-4 font-semibold">${Utils.formatCurrency(item.cost_value)}</td>
                                <td class="py-3 px-4">${item.percentage}%</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        this.renderChart('consumptionChart', 'pie', chartData);
        this.hideLoading();
    }

    renderWasteAnalysis(report) {
        const container = document.getElementById('reportData');
        
        container.innerHTML = `
            <div class="flex items-center justify-between mb-6">
                <h3 class="text-xl font-semibold text-gray-800">Análisis de Mermas</h3>
                <div class="flex space-x-2">
                    <button onclick="reportsManager.exportToExcel('waste')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                        <i class="fas fa-file-excel mr-2"></i>Excel
                    </button>
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div class="bg-red-50 rounded-lg p-4">
                    <p class="text-sm text-gray-600">Total Mermas</p>
                    <p class="text-2xl font-bold text-red-600">${Utils.formatCurrency(report.total_waste_value)}</p>
                </div>
                <div class="bg-yellow-50 rounded-lg p-4">
                    <p class="text-sm text-gray-600">Porcentaje de Merma</p>
                    <p class="text-2xl font-bold text-yellow-600">${report.waste_percentage}%</p>
                </div>
                <div class="bg-orange-50 rounded-lg p-4">
                    <p class="text-sm text-gray-600">Estado</p>
                    <p class="text-lg font-bold ${report.is_abnormal ? 'text-red-600' : 'text-green-600'}">
                        ${report.is_abnormal ? 'ANORMAL' : 'NORMAL'}
                    </p>
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                    <h4 class="font-medium text-gray-700 mb-3">Distribución por Tipo</h4>
                    <div class="space-y-3">
                        ${report.waste_types.map(type => `
                            <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                                <div>
                                    <p class="font-medium">${this.translateWasteType(type.type)}</p>
                                    <p class="text-sm text-gray-600">${type.count} registros</p>
                                </div>
                                <div class="text-right">
                                    <p class="font-semibold">${Utils.formatCurrency(type.cost)}</p>
                                    <p class="text-sm text-gray-600">${type.percentage}%</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div>
                    <h4 class="font-medium text-gray-700 mb-3">Productos con Mayor Merma</h4>
                    <div class="space-y-3">
                        ${report.waste_types[0]?.items?.slice(0, 5).map(item => `
                            <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                                <div>
                                    <p class="font-medium">${item.product_name}</p>
                                    <p class="text-sm text-gray-600">${item.quantity} ${item.unit}</p>
                                </div>
                                <p class="font-semibold">${Utils.formatCurrency(item.cost)}</p>
                            </div>
                        `).join('') || '<p class="text-gray-500 text-center py-4">No hay datos disponibles</p>'}
                    </div>
                </div>
            </div>
        `;

        this.hideLoading();
    }

    renderPurchasesReport(report) {
        const container = document.getElementById('reportData');
        
        container.innerHTML = `
            <div class="flex items-center justify-between mb-6">
                <h3 class="text-xl font-semibold text-gray-800">Historial de Compras</h3>
                <div class="flex space-x-2">
                    <button onclick="reportsManager.exportToExcel('purchases')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                        <i class="fas fa-file-excel mr-2"></i>Excel
                    </button>
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div class="bg-purple-50 rounded-lg p-4">
                    <p class="text-sm text-gray-600">Total Compras</p>
                    <p class="text-2xl font-bold text-purple-600">${Utils.formatCurrency(report.total_purchases)}</p>
                </div>
                <div class="bg-blue-50 rounded-lg p-4">
                    <p class="text-sm text-gray-600">Facturas</p>
                    <p class="text-2xl font-bold text-blue-600">${report.invoice_count}</p>
                </div>
                <div class="bg-green-50 rounded-lg p-4">
                    <p class="text-sm text-gray-600">Promedio por Factura</p>
                    <p class="text-2xl font-bold text-green-600">${Utils.formatCurrency(report.total_purchases / report.invoice_count)}</p>
                </div>
            </div>
            
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead>
                        <tr class="border-b border-gray-200">
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Factura</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Fecha</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Proveedor</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Subtotal</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Total</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Items</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${report.invoices.map(invoice => `
                            <tr class="border-b border-gray-100 hover:bg-gray-50">
                                <td class="py-3 px-4 font-medium">${invoice.invoice_number}</td>
                                <td class="py-3 px-4">${new Date(invoice.invoice_date).toLocaleDateString()}</td>
                                <td class="py-3 px-4">${invoice.provider_name}</td>
                                <td class="py-3 px-4">${Utils.formatCurrency(invoice.subtotal)}</td>
                                <td class="py-3 px-4 font-semibold">${Utils.formatCurrency(invoice.total)}</td>
                                <td class="py-3 px-4">${invoice.item_count}</td>
                                <td class="py-3 px-4">
                                    <span class="px-2 py-1 text-xs font-semibold rounded-full ${invoice.status === 'processed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                                        ${invoice.status}
                                    </span>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        this.hideLoading();
    }

    renderRotationAnalysis(report) {
        const container = document.getElementById('reportData');
        
        container.innerHTML = `
            <div class="flex items-center justify-between mb-6">
                <h3 class="text-xl font-semibold text-gray-800">Análisis de Rotación (${report.period_days} días)</h3>
                <div class="flex space-x-2">
                    <button onclick="reportsManager.exportToExcel('rotation')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                        <i class="fas fa-file-excel mr-2"></i>Excel
                    </button>
                </div>
            </div>
            
            <div class="bg-yellow-50 rounded-lg p-4 mb-6">
                <p class="text-sm text-gray-600">Productos Analizados</p>
                <p class="text-2xl font-bold text-yellow-600">${report.products_analyzed}</p>
            </div>
            
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead>
                        <tr class="border-b border-gray-200">
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Producto</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Categoría</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Stock Actual</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Consumo</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Rotación</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Clasificación</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${report.products.map(product => `
                            <tr class="border-b border-gray-100 hover:bg-gray-50">
                                <td class="py-3 px-4 font-medium">${product.product_name}</td>
                                <td class="py-3 px-4">${product.category}</td>
                                <td class="py-3 px-4">${Utils.formatNumber(product.current_stock)}</td>
                                <td class="py-3 px-4">${Utils.formatNumber(product.total_out)}</td>
                                <td class="py-3 px-4 font-semibold">${product.rotation_rate}</td>
                                <td class="py-3 px-4">
                                    <span class="px-2 py-1 text-xs font-semibold rounded-full ${this.getRotationClass(product.rotation_classification)}">
                                        ${this.translateRotation(product.rotation_classification)}
                                    </span>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        this.hideLoading();
    }

    renderObsoleteProducts(report) {
        const container = document.getElementById('reportData');
        
        container.innerHTML = `
            <div class="flex items-center justify-between mb-6">
                <h3 class="text-xl font-semibold text-gray-800">Productos Obsoletos (${report.days_without_movement} días sin movimiento)</h3>
                <div class="flex space-x-2">
                    <button onclick="reportsManager.exportToExcel('obsolete')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                        <i class="fas fa-file-excel mr-2"></i>Excel
                    </button>
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div class="bg-gray-50 rounded-lg p-4">
                    <p class="text-sm text-gray-600">Productos Obsoletos</p>
                    <p class="text-2xl font-bold text-gray-600">${report.total_products}</p>
                </div>
                <div class="bg-red-50 rounded-lg p-4">
                    <p class="text-sm text-gray-600">Valor Atrapado</p>
                    <p class="text-2xl font-bold text-red-600">${Utils.formatCurrency(report.total_inventory_value)}</p>
                </div>
                <div class="bg-yellow-50 rounded-lg p-4">
                    <p class="text-sm text-gray-600">Promedio por Producto</p>
                    <p class="text-2xl font-bold text-yellow-600">${Utils.formatCurrency(report.total_inventory_value / report.total_products)}</p>
                </div>
            </div>
            
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead>
                        <tr class="border-b border-gray-200">
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Producto</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Categoría</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Stock</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Valor</th>
                            <th class="text-left py-3 px-4 font-medium text-gray-700">Último Movimiento</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${report.products.map(product => `
                            <tr class="border-b border-gray-100 hover:bg-gray-50">
                                <td class="py-3 px-4 font-medium">${product.product_name}</td>
                                <td class="py-3 px-4">${product.category}</td>
                                <td class="py-3 px-4">${Utils.formatNumber(product.current_stock)} ${product.unit}</td>
                                <td class="py-3 px-4 font-semibold text-red-600">${Utils.formatCurrency(product.total_value)}</td>
                                <td class="py-3 px-4">${product.last_movement_date}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        this.hideLoading();
    }

    renderChart(canvasId, type, data) {
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;

        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(ctx, {
            type: type,
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: [
                        '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
                        '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'
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

    getStockStatusClass(status) {
        switch (status) {
            case 'low': return 'bg-red-100 text-red-800';
            case 'ok': return 'bg-green-100 text-green-800';
            default: return 'bg-blue-100 text-blue-800';
        }
    }

    getRotationClass(classification) {
        switch (classification) {
            case 'high': return 'bg-green-100 text-green-800';
            case 'medium': return 'bg-yellow-100 text-yellow-800';
            case 'low': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }

    translateRotation(classification) {
        const translations = {
            high: 'Alta',
            medium: 'Media',
            low: 'Baja'
        };
        return translations[classification] || classification;
    }

    translateWasteType(type) {
        const translations = {
            preparation: 'Preparación',
            expired: 'Vencido',
            damaged: 'Dañado'
        };
        return translations[type] || type;
    }

    async exportToExcel(type) {
        if (!this.currentReport) {
            Utils.showNotification('No hay reporte para exportar', 'warning');
            return;
        }

        try {
            const hideLoading = Utils.showLoading('Exportando a Excel...');
            
            // Generate CSV content based on report type
            const csvContent = this.generateCSVContent(type);
            
            // Create and download file
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            Utils.downloadFile(blob, `${type}_${new Date().toISOString().split('T')[0]}.csv`);

            hideLoading();
            Utils.showNotification('Reporte exportado exitosamente', 'success');
        } catch (error) {
            console.error('Error exporting to Excel:', error);
            Utils.showNotification('Error al exportar', 'error');
        }
    }

    generateCSVContent(type) {
        // This would generate CSV content based on the current report
        // Implementation would depend on the specific report data
        return 'CSV content here';
    }

    async exportToPDF(type) {
        Utils.showNotification('Exportación a PDF no implementada', 'info');
    }

    showLoading() {
        document.getElementById('loadingState').style.display = 'flex';
        document.getElementById('reportData').style.display = 'none';
    }

    hideLoading() {
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('reportData').style.display = 'block';
    }

    clearFilters() {
        this.setDefaultDates();
        document.getElementById('reportCategory').value = '';
    }

    refreshData() {
        if (this.currentReport) {
            this.generateCurrentReport();
        }
    }
}

// Initialize reports manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (typeof authManager !== 'undefined' && authManager.isAuthenticated()) {
        window.reportsManager = new ReportsManager();
    }
});