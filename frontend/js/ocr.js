/**
 * OCR Processing JavaScript Module
 * Módulo JavaScript para Procesamiento OCR de Facturas
 */

class OCRManager {
    constructor() {
        this.currentFile = null;
        this.ocrResult = null;
        this.extractedItems = [];
        this.providers = [];
        this.products = [];
        this.matchingItems = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.setupDragAndDrop();
    }

    setupEventListeners() {
        // File input
        document.getElementById('fileInput').addEventListener('change', (e) => this.handleFileSelect(e));
        document.getElementById('dropZone').addEventListener('click', () => document.getElementById('fileInput').click());

        // OCR actions
        document.getElementById('discardBtn').addEventListener('click', () => this.discardResults());
        document.getElementById('saveInvoiceBtn').addEventListener('click', () => this.saveInvoice());

        // Invoice filters
        document.getElementById('searchInvoices').addEventListener('input', 
            Utils.debounce(() => this.loadInvoices(), 300));
        document.getElementById('filterStatus').addEventListener('change', () => this.loadInvoices());

        // Modal
        document.getElementById('closeMatchingModal').addEventListener('click', () => this.closeMatchingModal());
        document.getElementById('cancelMatching').addEventListener('click', () => this.closeMatchingModal());
        document.getElementById('confirmMatching').addEventListener('click', () => this.confirmMatching());
    }

    setupDragAndDrop() {
        const dropZone = document.getElementById('dropZone');

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => this.highlight(), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => this.unhighlight(), false);
        });

        dropZone.addEventListener('drop', (e) => this.handleDrop(e), false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    highlight() {
        document.getElementById('dropZone').classList.add('dragover');
    }

    unhighlight() {
        document.getElementById('dropZone').classList.remove('dragover');
    }

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        if (e.target.files.length > 0) {
            this.processFile(e.target.files[0]);
        }
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadProviders(),
                this.loadProducts(),
                this.loadInvoices()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    async loadProviders() {
        try {
            const response = await authManager.authenticatedFetch('/api/products/providers/list');
            this.providers = await response.json();
        } catch (error) {
            console.error('Error loading providers:', error);
            this.providers = [];
        }
    }

    async loadProducts() {
        try {
            const response = await authManager.authenticatedFetch('/api/products?limit=1000');
            this.products = await response.json();
        } catch (error) {
            console.error('Error loading products:', error);
            this.products = [];
        }
    }

    async loadInvoices() {
        try {
            const search = document.getElementById('searchInvoices').value;
            const status = document.getElementById('filterStatus').value;
            
            let url = '/api/invoices?limit=50';
            if (search) url += `&search=${encodeURIComponent(search)}`;
            if (status) url += `&status=${status}`;
            
            const response = await authManager.authenticatedFetch(url);
            const invoices = await response.json();
            this.renderInvoices(invoices);
        } catch (error) {
            console.error('Error loading invoices:', error);
        }
    }

    async processFile(file) {
        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
        if (!allowedTypes.includes(file.type)) {
            Utils.showNotification('Tipo de archivo no soportado. Use JPG, PNG o PDF.', 'error');
            return;
        }

        // Check file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            Utils.showNotification('El archivo es demasiado grande. Máximo 10MB.', 'error');
            return;
        }

        this.currentFile = file;
        this.showProcessing();

        try {
            // First, try server-side OCR
            const serverResult = await this.processWithServer(file);
            
            if (serverResult && serverResult.success) {
                this.handleOCRResult(serverResult);
            } else {
                // Fallback to client-side OCR
                const clientResult = await this.processWithClient(file);
                this.handleOCRResult(clientResult);
            }
        } catch (error) {
            console.error('OCR processing error:', error);
            Utils.showNotification('Error al procesar la factura', 'error');
            this.hideProcessing();
        }
    }

    async processWithServer(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await authManager.authenticatedFetch('/api/invoices/ocr/process', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Server OCR error:', error);
        }

        return null;
    }

    async processWithClient(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = async (e) => {
                try {
                    // Update progress
                    this.updateProgress(20, 'Cargando imagen...');

                    // Perform OCR with Tesseract.js
                    const result = await Tesseract.recognize(
                        e.target.result,
                        'spa',
                        {
                            logger: (m) => {
                                if (m.status === 'recognizing text') {
                                    const progress = 20 + (m.progress * 60);
                                    this.updateProgress(progress, 'Procesando texto...');
                                }
                            }
                        }
                    );

                    this.updateProgress(90, 'Analizando factura...');

                    // Parse the text
                    const parsedData = this.parseInvoiceText(result.data.text);
                    
                    this.updateProgress(100, 'Completado');

                    resolve({
                        success: true,
                        ...parsedData,
                        confidence: result.data.confidence,
                        raw_text: result.data.text
                    });
                } catch (error) {
                    reject(error);
                }
            };

            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsDataURL(file);
        });
    }

    parseInvoiceText(text) {
        const lines = text.split('\n').filter(line => line.trim());
        
        // Extract invoice number
        const invoiceNumberMatch = text.match(/(?:factura|número|n[°º]\s*factura|nro\.?\s*factura)[\s:]*([A-Z0-9\-]+)/i);
        const invoiceNumber = invoiceNumberMatch ? invoiceNumberMatch[1] : '';

        // Extract date
        const dateMatch = text.match(/(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})/);
        const invoiceDate = dateMatch ? this.normalizeDate(dateMatch[1]) : '';

        // Extract provider (first line that looks like a company name)
        const providerMatch = lines.find(line => 
            line.length > 5 && line.length < 50 && 
            !line.match(/\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}/) &&
            !line.match(/total|subtotal|iva|factura/i)
        );
        const provider = providerMatch || '';

        // Extract amounts
        const amounts = text.match(/\d+[,.]?\d{0,2}/g) || [];
        const numericAmounts = amounts.map(a => parseFloat(a.replace(',', '.'))).filter(a => a > 0);
        
        let subtotal = 0, total = 0;
        if (numericAmounts.length >= 2) {
            subtotal = Math.min(...numericAmounts);
            total = Math.max(...numericAmounts);
        } else if (numericAmounts.length === 1) {
            total = numericAmounts[0];
            subtotal = total;
        }

        // Extract items (lines with product names and quantities)
        const items = this.extractItems(lines);

        return {
            invoice_number: invoiceNumber,
            invoice_date: invoiceDate,
            provider_name: provider,
            subtotal: subtotal,
            total: total,
            items: items
        };
    }

    extractItems(lines) {
        const items = [];
        
        for (const line of lines) {
            // Try to match product lines with quantities and prices
            const match = line.match(/(.{5,40})\s+(\d+(?:[,.]\d{1,3})?)\s+.*?\$(\d+[,.]?\d{0,2})/i);
            
            if (match) {
                const [, name, quantity, price] = match;
                const qty = parseFloat(quantity.replace(',', '.'));
                const unitPrice = parseFloat(price.replace(',', '.'));
                
                if (qty > 0 && unitPrice > 0) {
                    items.push({
                        product_name: name.trim(),
                        quantity: qty,
                        unit_price: unitPrice,
                        total_price: qty * unitPrice
                    });
                }
            }
        }

        return items.slice(0, 20); // Limit to 20 items
    }

    normalizeDate(dateStr) {
        try {
            // Try different Spanish date formats
            const formats = ['%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y', '%m-%d-%Y'];
            
            // Simple date normalization
            const parts = dateStr.split(/[\/\-]/);
            if (parts.length === 3) {
                const [d, m, y] = parts.map(p => parseInt(p));
                const year = y < 100 ? 2000 + y : y;
                const month = m - 1; // JavaScript months are 0-based
                const day = d;
                
                const date = new Date(year, month, day);
                return date.toISOString().split('T')[0];
            }
        } catch (error) {
            console.error('Date normalization error:', error);
        }
        
        return new Date().toISOString().split('T')[0]; // Default to today
    }

    handleOCRResult(result) {
        this.ocrResult = result;
        this.extractedItems = result.items || [];

        // Populate invoice form
        document.getElementById('invoiceNumber').value = result.invidence_number || '';
        document.getElementById('invoiceDate').value = result.invoice_date || new Date().toISOString().split('T')[0];
        document.getElementById('invoiceProvider').value = result.provider_name || '';
        document.getElementById('invoiceSubtotal').value = result.subtotal || 0;
        document.getElementById('invoiceTotal').value = result.total || 0;

        // Update confidence badge
        const confidenceBadge = document.getElementById('confidenceBadge');
        const confidence = result.confidence || 0;
        confidenceBadge.textContent = `${Math.round(confidence * 100)}%`;
        confidenceBadge.className = `px-2 py-1 text-xs font-semibold rounded-full ${
            confidence > 0.8 ? 'bg-green-100 text-green-800 confidence-high' :
            confidence > 0.6 ? 'bg-yellow-100 text-yellow-800 confidence-medium' :
            'bg-red-100 text-red-800 confidence-low'
        }`;

        // Render extracted items
        this.renderExtractedItems();

        // Show results
        document.getElementById('ocrResults').style.display = 'block';
        this.hideProcessing();

        // Auto-match products
        this.matchProducts();
    }

    renderExtractedItems() {
        const container = document.getElementById('extractedItems');
        container.innerHTML = '';

        this.extractedItems.forEach((item, index) => {
            const itemElement = document.createElement('div');
            itemElement.className = 'invoice-item p-3 border border-gray-200 rounded-lg';
            
            itemElement.innerHTML = `
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <input type="text" value="${item.product_name}" 
                               class="w-full font-medium text-gray-800 border-none bg-transparent focus:outline-none"
                               onchange="ocrManager.updateItem(${index}, 'product_name', this.value)">
                    </div>
                    <div class="flex items-center space-x-2 ml-4">
                        <input type="number" value="${item.quantity}" step="0.01"
                               class="w-20 px-2 py-1 border border-gray-300 rounded text-center"
                               onchange="ocrManager.updateItem(${index}, 'quantity', this.value)">
                        <span class="text-sm text-gray-500">x</span>
                        <input type="number" value="${item.unit_price}" step="0.01"
                               class="w-20 px-2 py-1 border border-gray-300 rounded text-center"
                               onchange="ocrManager.updateItem(${index}, 'unit_price', this.value)">
                        <span class="text-sm text-gray-500">=</span>
                        <span class="font-medium">${Utils.formatCurrency(item.total_price)}</span>
                    </div>
                    <button onclick="ocrManager.removeItem(${index})" class="ml-2 text-red-600 hover:text-red-800">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="mt-2">
                    <select id="productMatch_${index}" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                        <option value="">-- Seleccionar producto existente --</option>
                    </select>
                </div>
            `;

            container.appendChild(itemElement);
        });
    }

    updateItem(index, field, value) {
        if (this.extractedItems[index]) {
            this.extractedItems[index][field] = field === 'quantity' || field === 'unit_price' ? 
                parseFloat(value) || 0 : value;
            
            // Recalculate total if quantity or price changed
            if (field === 'quantity' || field === 'unit_price') {
                const item = this.extractedItems[index];
                item.total_price = item.quantity * item.unit_price;
                this.renderExtractedItems();
            }
        }
    }

    removeItem(index) {
        this.extractedItems.splice(index, 1);
        this.renderExtractedItems();
    }

    matchProducts() {
        this.extractedItems.forEach((item, index) => {
            const select = document.getElementById(`productMatch_${index}`);
            
            // Clear existing options
            select.innerHTML = '<option value="">-- Seleccionar producto existente --</option>';
            
            // Find matching products
            const matches = this.products.filter(product => 
                product.name.toLowerCase().includes(item.product_name.toLowerCase().substr(0, 10)) ||
                item.product_name.toLowerCase().includes(product.name.toLowerCase().substr(0, 10))
            ).slice(0, 5);

            matches.forEach(product => {
                const option = document.createElement('option');
                option.value = product.id;
                option.textContent = `${product.name} (${product.category_name})`;
                select.appendChild(option);
            });

            // Auto-select if perfect match
            if (matches.length === 1) {
                select.value = matches[0].id;
            }
        });
    }

    async saveInvoice() {
        // Validate required fields
        const invoiceNumber = document.getElementById('invoiceNumber').value;
        const invoiceDate = document.getElementById('invoiceDate').value;
        const providerName = document.getElementById('invoiceProvider').value;
        const total = parseFloat(document.getElementById('invoiceTotal').value) || 0;

        if (!invoiceNumber || !invoiceDate || this.extractedItems.length === 0) {
            Utils.showNotification('Por favor complete todos los campos requeridos', 'error');
            return;
        }

        // Check for unmatched items
        const unmatchedItems = this.extractedItems.filter((_, index) => {
            const select = document.getElementById(`productMatch_${index}`);
            return !select.value;
        });

        if (unmatchedItems.length > 0) {
            this.showMatchingModal();
            return;
        }

        // Prepare invoice data
        const invoiceData = {
            invoice_number: invoiceNumber,
            invoice_date: invoiceDate,
            provider_id: this.findOrCreateProvider(providerName),
            subtotal: parseFloat(document.getElementById('invoiceSubtotal').value) || total,
            tax: 0,
            total: total,
            ocr_text: this.ocrResult.raw_text || '',
            ocr_confidence: this.ocrResult.confidence || 0,
            items: this.extractedItems.map((item, index) => ({
                product_id: document.getElementById(`productMatch_${index}`).value,
                product_name: item.product_name,
                quantity: item.quantity,
                unit_price: item.unit_price,
                total_price: item.total_price
            }))
        };

        try {
            const hideLoading = Utils.showLoading('Guardando factura...');

            const response = await authManager.authenticatedFetch('/api/invoices', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(invoiceData)
            });

            hideLoading();

            if (response.ok) {
                const result = await response.json();
                Utils.showNotification('Factura guardada exitosamente', 'success');
                
                // Clear form and reload invoices
                this.discardResults();
                await this.loadInvoices();
            } else {
                const error = await response.json();
                Utils.showNotification(error.detail || 'Error al guardar factura', 'error');
            }
        } catch (error) {
            console.error('Error saving invoice:', error);
            Utils.showNotification('Error de conexión', 'error');
        }
    }

    findOrCreateProvider(providerName) {
        // Try to find existing provider
        const existing = this.providers.find(p => 
            p.name.toLowerCase().includes(providerName.toLowerCase()) ||
            providerName.toLowerCase().includes(p.name.toLowerCase())
        );

        if (existing) {
            return existing.id;
        }

        // Return first provider as fallback
        return this.providers.length > 0 ? this.providers[0].id : 1;
    }

    showMatchingModal() {
        this.matchingItems = this.extractedItems.filter((_, index) => {
            const select = document.getElementById(`productMatch_${index}`);
            return !select.value;
        });

        const container = document.getElementById('matchingItems');
        container.innerHTML = '';

        this.matchingItems.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'border border-gray-200 rounded-lg p-4';
            div.innerHTML = `
                <div class="flex items-center justify-between mb-3">
                    <span class="font-medium">${item.product_name}</span>
                    <span class="text-sm text-gray-500">${item.quantity} x ${Utils.formatCurrency(item.unit_price)}</span>
                </div>
                <div class="space-y-2">
                    <label class="block text-sm text-gray-600">Opciones:</label>
                    <select id="matchSelect_${index}" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                        <option value="new">Crear nuevo producto</option>
                        ${this.products.map(p => 
                            `<option value="${p.id}">${p.name} (${p.category_name})</option>`
                        ).join('')}
                    </select>
                </div>
            `;
            container.appendChild(div);
        });

        document.getElementById('matchingModal').style.display = 'flex';
    }

    closeMatchingModal() {
        document.getElementById('matchingModal').style.display = 'none';
    }

    confirmMatching() {
        // Update the product matches
        this.matchingItems.forEach((item, index) => {
            const select = document.getElementById(`matchSelect_${index}`);
            const originalIndex = this.extractedItems.indexOf(item);
            
            if (select.value !== 'new') {
                document.getElementById(`productMatch_${originalIndex}`).value = select.value;
            }
        });

        this.closeMatchingModal();
        this.saveInvoice(); // Retry saving
    }

    discardResults() {
        this.currentFile = null;
        this.ocrResult = null;
        this.extractedItems = [];
        
        document.getElementById('ocrResults').style.display = 'none';
        document.getElementById('fileInput').value = '';
    }

    renderInvoices(invoices) {
        const tbody = document.getElementById('invoicesTable');
        tbody.innerHTML = '';

        if (invoices.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-8 text-gray-500">
                        <i class="fas fa-file-invoice text-4xl mb-4"></i>
                        <p>No hay facturas procesadas aún</p>
                    </td>
                </tr>
            `;
            return;
        }

        invoices.forEach(invoice => {
            const row = document.createElement('tr');
            row.className = 'border-b border-gray-100 hover:bg-gray-50';
            
            const statusColors = {
                pending: 'bg-yellow-100 text-yellow-800',
                processed: 'bg-green-100 text-green-800',
                failed: 'bg-red-100 text-red-800'
            };

            row.innerHTML = `
                <td class="py-3 px-4 font-medium">${invoice.invoice_number}</td>
                <td class="py-3 px-4">${new Date(invoice.invoice_date).toLocaleDateString()}</td>
                <td class="py-3 px-4">${invoice.provider_name}</td>
                <td class="py-3 px-4 font-semibold">${Utils.formatCurrency(invoice.total)}</td>
                <td class="py-3 px-4">${invoice.item_count}</td>
                <td class="py-3 px-4">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full ${statusColors[invoice.status] || statusColors.pending}">
                        ${invoice.status}
                    </span>
                </td>
                <td class="py-3 px-4">
                    <button onclick="ocrManager.viewInvoiceDetails(${invoice.id})" class="text-blue-600 hover:text-blue-800 mr-2">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button onclick="ocrManager.downloadInvoice(${invoice.id})" class="text-green-600 hover:text-green-800">
                        <i class="fas fa-download"></i>
                    </button>
                </td>
            `;

            tbody.appendChild(row);
        });
    }

    async viewInvoiceDetails(invoiceId) {
        try {
            const response = await authManager.authenticatedFetch(`/api/invoices/${invoiceId}`);
            const invoice = await response.json();
            
            // Show invoice details in a modal or new page
            console.log('Invoice details:', invoice);
            // Implementation would show a detailed view
            
        } catch (error) {
            console.error('Error loading invoice details:', error);
            Utils.showNotification('Error al cargar detalles de la factura', 'error');
        }
    }

    async downloadInvoice(invoiceId) {
        // Implementation for downloading invoice PDF
        Utils.showNotification('Función no implementada', 'info');
    }

    showProcessing() {
        document.getElementById('uploadContent').style.display = 'none';
        document.getElementById('processingContent').style.display = 'block';
        this.updateProgress(0, 'Iniciando...');
    }

    hideProcessing() {
        document.getElementById('uploadContent').style.display = 'block';
        document.getElementById('processingContent').style.display = 'none';
        this.updateProgress(0, '');
    }

    updateProgress(percent, status) {
        document.getElementById('progressBar').style.width = `${percent}%`;
        document.getElementById('progressText').textContent = `${Math.round(percent)}% - ${status}`;
    }
}

// Initialize OCR manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (typeof authManager !== 'undefined' && authManager.isAuthenticated()) {
        window.ocrManager = new OCRManager();
    }
});