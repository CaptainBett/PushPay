
    // API Configuration
    const API_BASE = '/api';

    
    // Theme toggle functionality
    const themeToggle = document.getElementById('themeToggle');
    const body = document.body;
    
    themeToggle.addEventListener('click', () => {
        body.classList.toggle('dark-mode');
        const icon = themeToggle.querySelector('i');
        if (body.classList.contains('dark-mode')) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    });
    
    // Tab functionality
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs and contents
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            tab.classList.add('active');
            const tabId = tab.getAttribute('data-tab');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
    
    // STK Push Form
    document.getElementById('stkForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const form = e.target;
        const loader = document.getElementById('stkLoader');
        const responseDiv = document.getElementById('stkResponse');
        const responseContent = document.getElementById('stkResponseContent');

        try {
            form.querySelector('button').disabled = true;
            loader.style.display = 'block';
            responseDiv.style.display = 'none';

            const formData = {
                phone: document.getElementById('phone').value,
                amount: document.getElementById('amount').value,
                account_ref: document.getElementById('account').value,
                description: document.getElementById('description').value
            };

            const res = await fetch(`${API_BASE}/stk-push`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(formData)
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Payment initiation failed');

            responseContent.textContent = JSON.stringify(data, null, 2);
            addTransaction({
                ...formData,
                status: 'pending',
                checkout_id: data.CheckoutRequestID,
                created_at: new Date().toISOString()
            });
            updateStats();
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            form.querySelector('button').disabled = false;
            loader.style.display = 'none';
            responseDiv.style.display = 'block';
        }
    });

    // Query Payment Form
    document.getElementById('queryForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const form = e.target;
        const loader = document.getElementById('queryLoader');
        const responseDiv = document.getElementById('queryResponse');
        const responseContent = document.getElementById('queryResponseContent');

        try {
            form.querySelector('button').disabled = true;
            loader.style.display = 'block';
            responseDiv.style.display = 'none';

            const checkoutId = document.getElementById('checkoutId').value;
            const res = await fetch(`${API_BASE}/query-payment`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ checkout_id: checkoutId })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Query failed');

            responseContent.textContent = JSON.stringify(data, null, 2);
            updateTransactionStatus(checkoutId, data.ResultCode === '0' ? 'completed' : 'failed');
            updateStats();
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            form.querySelector('button').disabled = false;
            loader.style.display = 'none';
            responseDiv.style.display = 'block';
        }
    });

    // Load initial transactions
    window.addEventListener('DOMContentLoaded', loadTransactions);

    async function loadTransactions() {
        try {
            const res = await fetch(`${API_BASE}/transactions`);
            const transactions = await res.json();
            transactions.forEach(addTransaction);
            updateStats();
        } catch (error) {
            console.error('Failed to load transactions:', error);
        }
    }

    function addTransaction(transaction) {
        const container = document.querySelector('.transaction-history');
        const transactionEl = document.createElement('div');
        transactionEl.className = 'transaction-item';
        transactionEl.innerHTML = `
            <div class="transaction-info">
                <div class="transaction-icon">
                    <i class="fas fa-${transaction.status === 'completed' ? 'check' : 
                                  transaction.status === 'failed' ? 'times' : 'spinner'}"></i>
                </div>
                <div class="transaction-details">
                    <h4>${transaction.account_ref}</h4>
                    <p>${transaction.description || 'Payment'}</p>
                    <small>${new Date(transaction.created_at).toLocaleString()}</small>
                </div>
            </div>
            <div>
                <div class="transaction-amount ${transaction.status}">
                    KES ${parseFloat(transaction.amount).toLocaleString()}
                </div>
                <span class="status-badge ${transaction.status}-bg">
                    ${transaction.status.charAt(0).toUpperCase() + transaction.status.slice(1)}
                </span>
            </div>
        `;
        container.prepend(transactionEl);
    }

    function updateTransactionStatus(checkoutId, newStatus) {
        document.querySelectorAll('.transaction-item').forEach(item => {
            const ref = item.querySelector('h4').textContent;
            const transactionId = item.dataset.id;
            if (transactionId === checkoutId) {
                item.querySelector('.transaction-amount').className = `transaction-amount ${newStatus}`;
                item.querySelector('.status-badge').className = `status-badge ${newStatus}-bg`;
                item.querySelector('.status-badge').textContent = newStatus.charAt(0).toUpperCase() + newStatus.slice(1);
            }
        });
    }

    async function updateStats() {
        try {
            const res = await fetch(`${API_BASE}/transactions`);
            const transactions = await res.json();
            
            const stats = {
                success: transactions.filter(t => t.status === 'completed').length,
                pending: transactions.filter(t => t.status === 'pending').length,
                failed: transactions.filter(t => t.status === 'failed').length
            };

            document.querySelectorAll('.stat-value').forEach(span => {
                const type = span.parentElement.querySelector('.stat-label').textContent.toLowerCase();
                span.textContent = stats[type];
            });
        } catch (error) {
            console.error('Failed to update stats:', error);
        }
    }