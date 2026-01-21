/**
 * Inventory Management JavaScript Module
 * Módulo JavaScript para Gestión de Inventario
 */

class InventoryManager {
    constructor() {
        this.products = [];
        this.categories = [];
        this.providers = [];
        this.filteredProducts = [];
        this.currentPage = 1;
        this.itemsPerPage = 12;
        this.currentView = 'grid';
        this.currentEditingId = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
    }

    setupEventListeners() {
        // Search and filters
        document.getElementById('searchInput').addEventListener('input',
            Utils.debounce(() => this.applyFilters(), 300));
        document.getElementById('categoryFilter').addEventListener('change', () => this.applyFilters());
        document.getElementById('stockFilter').addEventListener('change', () => this.applyFilters());
        document.getElementById('clearFilters').addEventListener('click', () => this.clearFilters());

        // View toggles
        document.getElementById('gridView').addEventListener('click', () => this.setView('grid'));
        document.getElementById('listView').addEventListener('click', () => this.setView('list'));

        // Pagination
        document.getElementById('prevPage').addEventListener('click', () => this.previousPage());
        document.getElementById('nextPage').addEventListener('click', () => this.nextPage());

        // Modal
        document.getElementById('addProductBtn').addEventListener('click', () => this.openModal());
        document.getElementById('closeModal').addEventListener('click', () => this.closeModal());
        document.getElementById('cancelBtn').addEventListener('click', () => this.closeModal());
        document.getElementById('productForm').addEventListener('submit', (e) => this.handleSubmit(e));

        // Provider Modal
        document.getElementById('addProviderBtn').addEventListener('click', () => this.openProviderModal());
        document.getElementById('closeProviderModal').addEventListener('click', () => this.closeProviderModal());
        document.getElementById('cancelProviderBtn').addEventListener('click', () => this.closeProviderModal());
        document.getElementById('providerForm').addEventListener('submit', (e) => this.handleProviderSubmit(e));

        // Export
        document.getElementById('exportBtn').addEventListener('click', () => this.exportProducts());

        // Close modal on outside click
        document.getElementById('productModal').addEventListener('click', (e) => {
            if (e.target.id === 'productModal') {
                this.closeModal();
            }
        });
    }

    async loadInitialData() {
        try {
            // Load products, categories, and providers in parallel
            await Promise.all([
                this.loadProducts(),
                this.loadCategories(),
                this.loadProviders(),
                this.loadStats()
            ]);

            this.populateSelects();
            this.applyFilters();

        } catch (error) {
            console.error('Error loading initial data:', error);
            Utils.showNotification('Error al cargar datos iniciales', 'error');
        }
    }

    async loadProducts() {
        try {
            const response = await authManager.authenticatedFetch('/api/products');
            const data = await response.json();
            this.products = data;
        } catch (error) {
            console.error('Error loading products:', error);
            throw error;
        }
    }

    async loadCategories() {
        try {
            const response = await authManager.authenticatedFetch('/api/products/categories/list');
            this.categories = await response.json();
        } catch (error) {
            console.error('Error loading categories:', error);
            // Fallback categories
            this.categories = [
                { id: 1, name: 'Carnes y Pescados', type: 'food' },
                { id: 2, name: 'Lácteos y Huevos', type: 'food' },
                { id: 3, name: 'Bebidas', type: 'beverage' },
                { id: 4, name: 'Limpieza', type: 'cleaning' }
            ];
        }
    }

    async loadProviders() {
        try {
            const response = await authManager.authenticatedFetch('/api/products/providers/list');
            this.providers = await response.json();
        } catch (error) {
            console.error('Error loading providers:', error);
            // Fallback providers
            this.providers = [
                { id: 1, name: 'Distribuidora Central' },
                { id: 2, name: 'Productores Frescos' },
                { id: 3, name: 'Bebidas Premium' }
            ];
        }
    }

    async loadStats() {
        try {
            const response = await authManager.authenticatedFetch('/api/products/stats');
            const stats = await response.json();
            this.renderStatsCards(stats);
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    populateSelects() {
        // Category select
        const categorySelect = document.getElementById('productCategory');
        const categoryFilter = document.getElementById('categoryFilter');

        categorySelect.innerHTML = '<option value="">Seleccionar categoría</option>';
        categoryFilter.innerHTML = '<option value="">Todas las categorías</option>';

        this.categories.forEach(category => {
            const option1 = document.createElement('option');
            option1.value = category.id;
            option1.textContent = category.name;
            categorySelect.appendChild(option1);

            const option2 = document.createElement('option');
            option2.value = category.id;
            option2.textContent = category.name;
            categoryFilter.appendChild(option2);
        });

        // Provider select
        const providerSelect = document.getElementById('productProvider');
        providerSelect.innerHTML = '<option value="">Seleccionar proveedor</option>';

        this.providers.forEach(provider => {
            const option = document.createElement('option');
            option.value = provider.id;
            option.textContent = provider.name;
            providerSelect.appendChild(option);
        });
    }

    renderStatsCards(stats) {
        const container = document.getElementById('statsCards');
        container.innerHTML = `
            <div class="bg-white rounded-xl shadow-sm p-6">
                <div class="flex items-center">
                    <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                        <i class="fas fa-boxes text-blue-600 text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Total Productos</p>
                        <p class="text-2xl font-bold text-gray-900">${stats.total_products || 0}</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-xl shadow-sm p-6">
                <div class="flex items-center">
                    <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                        <i class="fas fa-dollar-sign text-green-600 text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Valor Inventario</p>
                        <p class="text-2xl font-bold text-gray-900">${Utils.formatCurrency(stats.total_inventory_value || 0)}</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-xl shadow-sm p-6">
                <div class="flex items-center">
                    <div class="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                        <i class="fas fa-exclamation-triangle text-red-600 text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Stock Bajo</p>
                        <p class="text-2xl font-bold text-gray-900">${stats.low_stock_products || 0}</p>
                    </div>
                </div>
            </div>
        `;
    }

    applyFilters() {
        const search = document.getElementById('searchInput').value.toLowerCase();
        const categoryId = document.getElementById('categoryFilter').value;
        const stockStatus = document.getElementById('stockFilter').value;

        this.filteredProducts = this.products.filter(product => {
            // Search filter
            if (search && !product.name.toLowerCase().includes(search) &&
                !product.description?.toLowerCase().includes(search) &&
                !product.barcode?.toLowerCase().includes(search)) {
                return false;
            }

            // Category filter
            if (categoryId && product.category_id != categoryId) {
                return false;
            }

            // Stock status filter
            if (stockStatus) {
                const isLowStock = product.current_stock <= product.min_stock;
                if (stockStatus === 'low' && !isLowStock) {
                    return false;
                }
                if (stockStatus === 'ok' && isLowStock) {
                    return false;
                }
            }

            return true;
        });

        this.currentPage = 1;
        this.renderProducts();
        this.updatePagination();
    }

    clearFilters() {
        document.getElementById('searchInput').value = '';
        document.getElementById('categoryFilter').value = '';
        document.getElementById('stockFilter').value = '';
        this.applyFilters();
    }

    setView(view) {
        this.currentView = view;

        // Update buttons
        document.getElementById('gridView').className = view === 'grid' ?
            'px-3 py-2 bg-blue-600 text-white rounded-l-lg' :
            'px-3 py-2 text-gray-600 rounded-l-lg hover:bg-gray-50';

        document.getElementById('listView').className = view === 'list' ?
            'px-3 py-2 bg-blue-600 text-white rounded-r-lg' :
            'px-3 py-2 text-gray-600 rounded-r-lg hover:bg-gray-50';

        this.renderProducts();
    }

    renderProducts() {
        const container = document.getElementById('productsContainer');
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageProducts = this.filteredProducts.slice(startIndex, endIndex);

        if (this.currentView === 'grid') {
            container.className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6';
            this.renderGridView(container, pageProducts);
        } else {
            container.className = 'space-y-4';
            this.renderListView(container, pageProducts);
        }

        // Update product count
        document.getElementById('productCount').textContent = `${this.filteredProducts.length} productos`;
    }

    renderGridView(container, products) {
        container.innerHTML = '';

        products.forEach(product => {
            const stockStatus = this.getStockStatus(product);
            const card = document.createElement('div');
            card.className = `product-card bg-white rounded-xl shadow-sm p-6 border-l-4 ${stockStatus.class}`;

            card.innerHTML = `
                <div class="flex items-start justify-between mb-4">
                    <div class="flex-1">
                        <h4 class="font-semibold text-gray-800 mb-1">${product.name}</h4>
                        <p class="text-sm text-gray-600">${product.category_name || 'Sin categoría'}</p>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="inventoryManager.editProduct(${product.id})" class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="inventoryManager.deleteProduct(${product.id})" class="text-red-600 hover:text-red-800">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Stock Actual:</span>
                        <span class="font-medium">${Utils.formatNumber(product.current_stock)} ${product.unit}</span>
                    </div>
                    
                    <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Stock Mínimo:</span>
                        <span class="text-sm">${Utils.formatNumber(product.min_stock)} ${product.unit}</span>
                    </div>
                    
                    <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Precio Costo:</span>
                        <span class="font-medium">${Utils.formatCurrency(product.cost_price)}</span>
                    </div>
                    
                    <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Valor Total:</span>
                        <span class="font-semibold text-green-600">${Utils.formatCurrency(product.current_stock * product.cost_price)}</span>
                    </div>
                </div>
                
                <div class="mt-4 pt-4 border-t border-gray-100">
                    <div class="flex items-center justify-between">
                        <span class="px-2 py-1 text-xs font-semibold rounded-full ${stockStatus.labelClass}">
                            ${stockStatus.label}
                        </span>
                        <span class="text-xs text-gray-500">
                            ${product.provider_name || 'Sin proveedor'}
                        </span>
                    </div>
                </div>
            `;

            container.appendChild(card);
        });
    }

    renderListView(container, products) {
        container.innerHTML = '';

        const table = document.createElement('table');
        table.className = 'w-full';
        table.innerHTML = `
            <thead>
                <tr class="border-b border-gray-200">
                    <th class="text-left py-3 px-4 font-medium text-gray-700">Producto</th>
                    <th class="text-left py-3 px-4 font-medium text-gray-700">Categoría</th>
                    <th class="text-left py-3 px-4 font-medium text-gray-700">Stock</th>
                    <th class="text-left py-3 px-4 font-medium text-gray-700">Precio</th>
                    <th class="text-left py-3 px-4 font-medium text-gray-700">Valor</th>
                    <th class="text-left py-3 px-4 font-medium text-gray-700">Estado</th>
                    <th class="text-left py-3 px-4 font-medium text-gray-700">Acciones</th>
                </tr>
            </thead>
            <tbody id="listTableBody"></tbody>
        `;

        const tbody = table.querySelector('#listTableBody');

        products.forEach(product => {
            const stockStatus = this.getStockStatus(product);
            const row = document.createElement('tr');
            row.className = 'border-b border-gray-100 hover:bg-gray-50';

            row.innerHTML = `
                <td class="py-3 px-4">
                    <div class="font-medium text-gray-900">${product.name}</div>
                    <div class="text-sm text-gray-500">${product.barcode || 'Sin código'}</div>
                </td>
                <td class="py-3 px-4 text-gray-600">${product.category_name || 'Sin categoría'}</td>
                <td class="py-3 px-4">
                    <span class="font-medium">${Utils.formatNumber(product.current_stock)}</span>
                    <span class="text-sm text-gray-500">${product.unit}</span>
                </td>
                <td class="py-3 px-4">${Utils.formatCurrency(product.cost_price)}</td>
                <td class="py-3 px-4 font-semibold text-green-600">
                    ${Utils.formatCurrency(product.current_stock * product.cost_price)}
                </td>
                <td class="py-3 px-4">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full ${stockStatus.labelClass}">
                        ${stockStatus.label}
                    </span>
                </td>
                <td class="py-3 px-4">
                    <div class="flex space-x-2">
                        <button onclick="inventoryManager.editProduct(${product.id})" class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="inventoryManager.deleteProduct(${product.id})" class="text-red-600 hover:text-red-800">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;

            tbody.appendChild(row);
        });

        container.appendChild(table);
    }

    getStockStatus(product) {
        const current = product.current_stock;
        const minimum = product.min_stock || 0;

        if (current <= minimum) {
            return {
                class: 'stock-low',
                label: 'Bajo',
                labelClass: 'bg-red-100 text-red-800'
            };
        } else if (current <= minimum * 1.5) {
            return {
                class: 'stock-medium',
                label: 'Medio',
                labelClass: 'bg-yellow-100 text-yellow-800'
            };
        } else {
            return {
                class: 'stock-ok',
                label: 'Normal',
                labelClass: 'bg-green-100 text-green-800'
            };
        }
    }

    updatePagination() {
        const totalPages = Math.ceil(this.filteredProducts.length / this.itemsPerPage);
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = Math.min(startIndex + this.itemsPerPage, this.filteredProducts.length);

        // Update showing text
        document.getElementById('showingStart').textContent = this.filteredProducts.length > 0 ? startIndex + 1 : 0;
        document.getElementById('showingEnd').textContent = endIndex;
        document.getElementById('totalProducts').textContent = this.filteredProducts.length;

        // Update pagination buttons
        document.getElementById('prevPage').disabled = this.currentPage <= 1;
        document.getElementById('nextPage').disabled = this.currentPage >= totalPages;

        // Update page numbers
        this.renderPageNumbers(totalPages);
    }

    renderPageNumbers(totalPages) {
        const container = document.getElementById('pageNumbers');
        container.innerHTML = '';

        const maxVisible = 5;
        let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
        let end = Math.min(totalPages, start + maxVisible - 1);

        if (end - start < maxVisible - 1) {
            start = Math.max(1, end - maxVisible + 1);
        }

        for (let i = start; i <= end; i++) {
            const button = document.createElement('button');
            button.className = `px-3 py-2 rounded-lg ${i === this.currentPage ? 'bg-blue-600 text-white' : 'border border-gray-300 text-gray-600 hover:bg-gray-50'}`;
            button.textContent = i;
            button.addEventListener('click', () => this.goToPage(i));
            container.appendChild(button);
        }
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.renderProducts();
            this.updatePagination();
        }
    }

    nextPage() {
        const totalPages = Math.ceil(this.filteredProducts.length / this.itemsPerPage);
        if (this.currentPage < totalPages) {
            this.currentPage++;
            this.renderProducts();
            this.updatePagination();
        }
    }

    goToPage(page) {
        this.currentPage = page;
        this.renderProducts();
        this.updatePagination();
    }

    openModal(product = null) {
        const modal = document.getElementById('productModal');
        const title = document.getElementById('modalTitle');
        const form = document.getElementById('productForm');

        if (product) {
            title.textContent = 'Editar Producto';
            this.currentEditingId = product.id;
            this.populateForm(product);
        } else {
            title.textContent = 'Nuevo Producto';
            this.currentEditingId = null;
            form.reset();
        }

        modal.classList.add('active');
    }

    closeModal() {
        const modal = document.getElementById('productModal');
        modal.classList.remove('active');
        this.currentEditingId = null;
        document.getElementById('productForm').reset();
    }

    populateForm(product) {
        document.getElementById('productName').value = product.name;
        document.getElementById('productBarcode').value = product.barcode || '';
        document.getElementById('productDescription').value = product.description || '';
        document.getElementById('productCategory').value = product.category_id || '';
        document.getElementById('productProvider').value = product.provider_id || '';
        document.getElementById('productUnit').value = product.unit || '';
        document.getElementById('productCurrentStock').value = product.current_stock || 0;
        document.getElementById('productMinStock').value = product.min_stock || 0;
        document.getElementById('productMaxStock').value = product.max_stock || 0;
        document.getElementById('productCostPrice').value = product.cost_price || 0;
        document.getElementById('productSellingPrice').value = product.selling_price || 0;
    }

    async handleSubmit(e) {
        e.preventDefault();

        const formData = {
            name: document.getElementById('productName').value,
            barcode: document.getElementById('productBarcode').value || null,
            description: document.getElementById('productDescription').value || null,
            category_id: parseInt(document.getElementById('productCategory').value),
            provider_id: parseInt(document.getElementById('productProvider').value),
            unit: document.getElementById('productUnit').value,
            current_stock: parseFloat(document.getElementById('productCurrentStock').value),
            min_stock: parseFloat(document.getElementById('productMinStock').value) || 0,
            max_stock: parseFloat(document.getElementById('productMaxStock').value) || 100,
            cost_price: parseFloat(document.getElementById('productCostPrice').value),
            selling_price: parseFloat(document.getElementById('productSellingPrice').value) || 0
        };

        // Validation
        const validation = this.validateProduct(formData);
        if (!validation.isValid) {
            Utils.showNotification(validation.errors[0], 'error');
            return;
        }

        try {
            const hideLoading = Utils.showLoading('Guardando producto...');

            let response;
            if (this.currentEditingId) {
                // Update existing product
                response = await authManager.authenticatedFetch(`/api/products/${this.currentEditingId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });
            } else {
                // Create new product
                response = await authManager.authenticatedFetch('/api/products', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });
            }

            hideLoading();

            if (response.ok) {
                Utils.showNotification(
                    this.currentEditingId ? 'Producto actualizado exitosamente' : 'Producto creado exitosamente',
                    'success'
                );

                this.closeModal();
                await this.loadProducts();
                this.applyFilters();
                await this.loadStats();
            } else {
                const error = await response.json();
                Utils.showNotification(error.detail || 'Error al guardar producto', 'error');
            }
        } catch (error) {
            console.error('Error saving product:', error);
            Utils.showNotification('Error de conexión', 'error');
        }
    }

    validateProduct(data) {
        const errors = [];

        if (!data.name || data.name.trim().length < 2) {
            errors.push('El nombre debe tener al menos 2 caracteres');
        }

        if (!data.category_id) {
            errors.push('Debe seleccionar una categoría');
        }

        if (!data.provider_id) {
            errors.push('Debe seleccionar un proveedor');
        }

        if (!data.unit) {
            errors.push('Debe seleccionar una unidad de medida');
        }

        if (data.current_stock < 0) {
            errors.push('El stock actual no puede ser negativo');
        }

        if (data.min_stock < 0) {
            errors.push('El stock mínimo no puede ser negativo');
        }

        if (data.cost_price < 0) {
            errors.push('El precio de costo no puede ser negativo');
        }

        if (data.selling_price < 0) {
            errors.push('El precio de venta no puede ser negativo');
        }

        return {
            isValid: errors.length === 0,
            errors
        };
    }

    editProduct(productId) {
        const product = this.products.find(p => p.id === productId);
        if (product) {
            this.openModal(product);
        }
    }

    async deleteProduct(productId) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;

        const confirmed = await this.showConfirmDialog(
            'Eliminar Producto',
            `¿Está seguro de que desea eliminar el producto "${product.name}"?`
        );

        if (!confirmed) return;

        try {
            const hideLoading = Utils.showLoading('Eliminando producto...');

            const response = await authManager.authenticatedFetch(`/api/products/${productId}`, {
                method: 'DELETE'
            });

            hideLoading();

            if (response.ok) {
                Utils.showNotification('Producto eliminado exitosamente', 'success');
                await this.loadProducts();
                this.applyFilters();
                await this.loadStats();
            } else {
                const error = await response.json();
                Utils.showNotification(error.detail || 'Error al eliminar producto', 'error');
            }
        } catch (error) {
            console.error('Error deleting product:', error);
            Utils.showNotification('Error de conexión', 'error');
        }
    }

    async exportProducts() {
        try {
            const hideLoading = Utils.showLoading('Exportando productos...');

            const response = await authManager.authenticatedFetch('/api/products?limit=1000');
            const products = await response.json();

            // Create CSV content
            const headers = ['Nombre', 'Categoría', 'Proveedor', 'Unidad', 'Stock Actual', 'Stock Mínimo', 'Precio Costo', 'Precio Venta', 'Valor Total'];
            const csvContent = [
                headers.join(','),
                ...products.map(p => [
                    `"${p.name}"`,
                    `"${p.category_name || ''}"`,
                    `"${p.provider_name || ''}"`,
                    `"${p.unit}"`,
                    p.current_stock,
                    p.min_stock,
                    p.cost_price,
                    p.selling_price,
                    p.current_stock * p.cost_price
                ].join(','))
            ].join('\n');

            // Create and download file
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            Utils.downloadFile(blob, `inventario_${new Date().toISOString().split('T')[0]}.csv`);

            hideLoading();
            Utils.showNotification('Productos exportados exitosamente', 'success');
        } catch (error) {
            console.error('Error exporting products:', error);
            Utils.showNotification('Error al exportar productos', 'error');
        }
    }

    openProviderModal() {
        document.getElementById('providerModal').classList.add('active');
        document.getElementById('providerForm').reset();
    }

    closeProviderModal() {
        document.getElementById('providerModal').classList.remove('active');
        document.getElementById('providerForm').reset();
    }

    async handleProviderSubmit(e) {
        e.preventDefault();

        const formData = {
            name: document.getElementById('provName').value,
            contact_person: document.getElementById('provContact').value,
            phone: document.getElementById('provPhone').value,
            email: document.getElementById('provEmail').value,
            address: document.getElementById('provAddress').value || null,
            tax_id: document.getElementById('provTaxId').value || null
        };

        try {
            const hideLoading = Utils.showLoading('Guardando proveedor...');

            const response = await authManager.authenticatedFetch('/api/products/providers', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            hideLoading();

            if (response.ok) {
                Utils.showNotification('Proveedor creado exitosamente', 'success');
                this.closeProviderModal();

                // Refresh providers list
                await this.loadProviders();
                this.populateSelects();

            } else {
                const error = await response.json();
                Utils.showNotification(error.detail || 'Error al crear proveedor', 'error');
            }
        } catch (error) {
            console.error('Error creating provider:', error);
            Utils.showNotification('Error de conexión', 'error');
        }
    }

    showConfirmDialog(title, message) {
        return new Promise((resolve) => {
            const confirmed = confirm(`${title}\n\n${message}`);
            resolve(confirmed);
        });
    }
}

// Initialize inventory manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    if (typeof authManager !== 'undefined' && authManager.isAuthenticated()) {
        window.inventoryManager = new InventoryManager();
    }
});