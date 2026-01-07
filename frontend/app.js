// Configuration -->added to ensure the github repo was aligned
const API_BASE_URL = 'https://web-production-c1f93.up.railway.app';
const SOLANA_NETWORK = 'devnet';
// Payment Configuration
// Price in SOL (1 SOL ≈ $20-200 depending on market)
// Recommended: 0.001-0.01 SOL ($0.02-$2 USD)
const PAYMENT_AMOUNT = 0.001; // 0.001 SOL ≈ $0.02-0.20 USD
const RECEIVER_ADDRESS = 'YOUR_SOLANA_ADDRESS_HERE';

// CPP Constants
const CPP_NORMAL_AGE = 65;
const CPP_EARLY_REDUCTION_RATE = 0.006; // 0.6% per month
const CPP_LATE_INCREASE_RATE = 0.007;   // 0.7% per month

// State
let wallet = null;
let walletConnected = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    try {
        transformFormForBatchMode();
        setupModeToggle();
        setupEventListeners();
        checkWalletConnection();
        updateCPPCalculation();
        setupCalculateButton();
    updateCalculateButtons(); // Set initial button states
    } catch (error) {
        console.error('❌ Initialization error:', error);
        console.error('Stack:', error.stack);
    }
});

// Setup Event Listeners
function setupEventListeners() {
    document.getElementById('connectWallet').addEventListener('click', connectWallet);
    document.getElementById('disconnectWallet')?.addEventListener('click', disconnectWallet);
    document.getElementById('testCalculate').addEventListener('click', testCalculate);
    document.getElementById('retirementForm').addEventListener('submit', handleSubmit);
    
    // CPP dynamic calculation
    document.getElementById('cppStartAge').addEventListener('input', updateCPPCalculation);
    document.getElementById('cppMonthly').addEventListener('input', updateCPPCalculation);

    // Pension UI handlers
    document.getElementById('includePension').addEventListener('change', togglePensionFields);
    document.getElementById('pensionHasEndYear').addEventListener('change', togglePensionEndYear);

}

// Update CPP Calculation
function updateCPPCalculation() {
    // Check if elements exist (they were removed in UI cleanup)
    const cppAdjustedEl = document.getElementById('cppAdjusted');
    const cppAnnualEl = document.getElementById('cppAnnual');
    const cppAdjustmentEl = document.getElementById('cppAdjustment');
    
    if (!cppAdjustedEl || !cppAnnualEl || !cppAdjustmentEl) {
        return; // Elements don't exist, skip update
    }
    
    const startAge = parseInt(document.getElementById('cppStartAge').value);
    const baseAmount = parseFloat(document.getElementById('cppMonthly').value);
    
    let adjustedAmount = baseAmount;
    let adjustmentPercent = 0;
    
    if (startAge < CPP_NORMAL_AGE) {
        // Early: 0.6% reduction per month
        const monthsEarly = (CPP_NORMAL_AGE - startAge) * 12;
        adjustmentPercent = -(monthsEarly * CPP_EARLY_REDUCTION_RATE * 100);
        adjustedAmount = baseAmount * (1 - (monthsEarly * CPP_EARLY_REDUCTION_RATE));
    } else if (startAge > CPP_NORMAL_AGE) {
        // Late: 0.7% increase per month (max 60 months)
        const monthsLate = Math.min((startAge - CPP_NORMAL_AGE) * 12, 60);
        adjustmentPercent = monthsLate * CPP_LATE_INCREASE_RATE * 100;
        adjustedAmount = baseAmount * (1 + (monthsLate * CPP_LATE_INCREASE_RATE));
    }

    // Update display
    document.getElementById('cppAdjusted').textContent = 
        '$' + adjustedAmount.toLocaleString('en-CA', {maximumFractionDigits: 0});
    document.getElementById('cppAnnual').textContent = 
        '$' + (adjustedAmount * 12).toLocaleString('en-CA', {maximumFractionDigits: 0});
    document.getElementById('cppAdjustment').textContent = 
        (adjustmentPercent >= 0 ? '+' : '') + adjustmentPercent.toFixed(1) + '%';
}
// Toggle Pension Fields Visibility
function togglePensionFields() {
    const checkbox = document.getElementById('includePension');
    const fields = document.getElementById('pensionFields');
    
    if (checkbox.checked) {
        fields.classList.remove('hidden');
    } else {
        fields.classList.add('hidden');
    }
}

// Toggle Pension End Year Field
function togglePensionEndYear() {
    const checkbox = document.getElementById('pensionHasEndYear');
    const endYearField = document.getElementById('pensionEndYear');
    
    if (checkbox.checked) {
        endYearField.classList.remove('hidden');
        endYearField.required = true;
    } else {
        endYearField.classList.add('hidden');
        endYearField.required = false;
    }
}

// Wallet Functions
function checkWalletConnection() {
    if ('solana' in window) {
        const provider = window.solana;
        if (provider.isPhantom) {
            wallet = provider;
            provider.connect({ onlyIfTrusted: true })
                .then(({ publicKey }) => {
                    updateWalletUI(publicKey.toString());
                })
                .catch(() => {
                    console.log('Wallet not connected');
                });
        }
    } else {
        console.log('Phantom wallet not detected');
    }
}

async function connectWallet() {
    if (!wallet) {
        showError('Phantom wallet not detected. Please install it first.');
        window.open('https://phantom.app/', '_blank');
        return;
    }

    try {
        const resp = await wallet.connect();
        updateWalletUI(resp.publicKey.toString());
        showStatus('Wallet connected successfully!');
    } catch (err) {
        showError('Failed to connect wallet: ' + err.message);
    }
}

async function disconnectWallet() {
    if (wallet) {
        await wallet.disconnect();
        walletConnected = false;
        document.getElementById('connectWallet').classList.remove('hidden');
        document.getElementById('walletInfo').classList.add('hidden');
        showStatus('Wallet disconnected');
    }
}

function updateWalletUI(address) {
    walletConnected = true;
    const shortAddress = address.slice(0, 4) + '...' + address.slice(-4);
    document.getElementById('walletAddress').textContent = shortAddress;
    document.getElementById('connectWallet').classList.add('hidden');
    document.getElementById('walletInfo').classList.remove('hidden');
}

// Calculation Functions
async function testCalculate() {
    showStatus('Testing calculation (no payment)...');
    clearMessages();
    
    const data = getFormData();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/retirement/calculate`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `API error: ${response.status}`);
        }

        const result = await response.json();
        displayResults(result);
        showStatus('✅ Test calculation complete (no payment made)');
    } catch (error) {
        showError('Calculation failed: ' + error.message);
    }
}

async function handleSubmit(event) {
    event.preventDefault();
    
    if (!walletConnected) {
        showError('Please connect your wallet first');
        return;
    }

    showStatus('Processing payment...');
    clearMessages();

    try {
        await makePayment();
        const data = getFormData();
        
        const response = await fetch(`${API_BASE_URL}/api/v1/retirement/calculate`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `API error: ${response.status}`);
        }

        const result = await response.json();
        displayResults(result);
        showStatus('✅ Calculation complete! Payment received.');
    } catch (error) {
        showError('Transaction failed: ' + error.message);
    }
}

async function makePayment() {
    // Simulated payment for now
    return new Promise((resolve) => {
        setTimeout(() => {
            console.log('Payment simulated');
            resolve();
        }, 1000);
    });
}

function getFormData() {
    // Build the base data object
    const data = {
        current_age: parseInt(document.getElementById('currentAge').value),
        retirement_age: parseInt(document.getElementById('retirementAge').value),
        life_expectancy: parseInt(document.getElementById('lifeExpectancy').value),
        province: document.getElementById('province').value,
        real_estate_value: 0,  // Legacy field, not used with arrays
        rrsp_balance: parseFloat(document.getElementById('rrspBalance').value),
        tfsa_balance: parseFloat(document.getElementById('tfsaBalance').value),
        non_registered: parseFloat(document.getElementById('nonRegistered').value),
        monthly_contribution: parseFloat(document.getElementById('monthlyContribution').value),
        rrsp_real_return: parseFloat(document.getElementById('rrspRealReturn').value) / 100,
        tfsa_real_return: parseFloat(document.getElementById('tfsaRealReturn').value) / 100,
        non_reg_real_return: parseFloat(document.getElementById('nonRegRealReturn').value) / 100,
        // Real estate handled by getPropertiesData()
        cpp_monthly: parseFloat(document.getElementById('cppMonthly').value),
        cpp_start_age: parseInt(document.getElementById('cppStartAge').value),
        oas_start_age: parseInt(document.getElementById('oasStartAge').value),
        desired_annual_spending: parseFloat(document.getElementById('desiredSpending').value),
        has_spouse: false,
        tax_calculation_mode: 'accurate', // Always use accurate calculation
    };
    
    // Add pension data if checkbox is checked
    if (document.getElementById('includePension').checked) {
        const pensionData = {
            monthly_amount: parseFloat(document.getElementById('pensionMonthly').value),
            start_year: parseInt(document.getElementById('pensionStartYear').value),
            indexing_rate: parseFloat(document.getElementById('pensionIndexing').value) / 100  // Convert % to decimal
        };
        
        // Add end_year if specified
        if (document.getElementById('pensionHasEndYear').checked) {
            pensionData.end_year = parseInt(document.getElementById('pensionEndYear').value);
        }
        
        data.pension = pensionData;
    }
    
    // Now return the complete data object

    // ✅ Use pension/property arrays
    // Only include pensions if checkbox is checked
    if (document.getElementById('includePension')?.checked) {
        data.pensions = getPensionsData();
    } else {
        data.pensions = [];
    }
    // Additional income streams
    if (document.getElementById('includeAdditionalIncome')?.checked) {
        data.additional_income = getAdditionalIncomeData();
    } else {
        data.additional_income = [];
    }

    data.real_estate_holdings = getPropertiesData();
    
    return data;
}

// Display Functions
function displayResults(result) {
    document.getElementById('resultsSection').classList.remove('hidden');
    
    document.getElementById('yearsToRetirement').textContent = result.years_to_retirement;
    document.getElementById('finalBalance').textContent = 
        '$' + result.final_balance.toLocaleString('en-CA', {maximumFractionDigits: 0});
    document.getElementById('planStatus').textContent = result.success ? '✅ Viable' : '⚠️ At Risk';
    
    // Add "Money Runs Out" warning if plan fails
    // First, clear any existing red warning boxes
    const resultsSection = document.getElementById('resultsSection');
    const existingWarnings = resultsSection.querySelectorAll('.critical-warning-box');
    existingWarnings.forEach(w => w.remove());
    
    if (!result.success && result.warnings && result.warnings.length > 0) {
        const shortfallWarning = result.warnings.find(w => w.includes('Insufficient funds'));
        if (shortfallWarning) {
            const ageMatch = shortfallWarning.match(/age (\d+)/);
            if (ageMatch) {
                const criticalAge = ageMatch[1];
                const warningBox = document.createElement('div');
                warningBox.className = 'critical-warning-box';
                warningBox.style.cssText = 'background: #fee2e2; border: 2px solid #dc2626; padding: 16px; margin: 16px 0; border-radius: 8px;';
                warningBox.innerHTML = `<strong style="color: #991b1b; font-size: 18px;">⚠️ Money Runs Out at Age ${criticalAge}</strong><p style="margin: 8px 0 0; color: #7f1d1d;">Consider: reducing spending, working longer, or increasing savings.</p>`;
                resultsSection.insertBefore(warningBox, resultsSection.firstChild);
            }
        }
    }

    
    const recList = document.getElementById('recommendationsList');
    recList.innerHTML = '';
    result.recommendations.forEach(rec => {
        const li = document.createElement('li');
        li.textContent = rec;
        recList.appendChild(li);
    });
    
    const warningsSection = document.getElementById('warningsSection');
    if (result.warnings && result.warnings.length > 0) {
        warningsSection.classList.remove('hidden');
        const warnList = document.getElementById('warningsList');
        warnList.innerHTML = '';
        
        // Deduplicate repeated warnings - show only first occurrence of each type
        let firstInsufficientFundsAge = null;
        let firstTaxWarningAge = null;
        
        const dedupedWarnings = result.warnings.filter(warn => {
            // Deduplicate "Insufficient funds" warnings
            if (warn.includes('Insufficient funds')) {
                const ageMatch = warn.match(/age (\d+)/);
                if (ageMatch && firstInsufficientFundsAge === null) {
                    firstInsufficientFundsAge = ageMatch[1];
                    // Modify message to indicate it continues
                    const modifiedWarn = warn.replace(
                        /Insufficient funds.*$/,
                        `Insufficient funds starting at age ${ageMatch[1]} (continues through retirement)`
                    );
                    // Replace in the warnings array for display
                    const idx = result.warnings.indexOf(warn);
                    result.warnings[idx] = modifiedWarn;
                    return true; // Keep first occurrence with modified message
                }
                return false; // Skip subsequent insufficient funds warnings
            }
            
            // Deduplicate tax warnings (if any remain)
            if (warn.includes('Cannot cover tax')) {
                const ageMatch = warn.match(/age (\d+)/);
                if (ageMatch && firstTaxWarningAge === null) {
                    firstTaxWarningAge = ageMatch[1];
                    return true;
                }
                return false;
            }
            
            return true; // Keep all other warnings
        });
        
        dedupedWarnings.forEach(warn => {
            const li = document.createElement('li');
            li.textContent = warn;
            warnList.appendChild(li);
        });
    } else {
        warningsSection.classList.add('hidden');
    }
    
    drawChart(result.projections);
    
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });

    // Find retirement age projection
    const retirementProjection = result.projections.find(
        p => p.age === result.input_summary.retirement_age
    );

    if (retirementProjection) {
        document.getElementById('rrspValue').textContent = 
            '$' + retirementProjection.rrsp_rrif_balance.toLocaleString('en-CA', {maximumFractionDigits: 0});
        document.getElementById('tfsaValue').textContent = 
            '$' + retirementProjection.tfsa_balance.toLocaleString('en-CA', {maximumFractionDigits: 0});
        document.getElementById('nonRegValue').textContent = 
            '$' + retirementProjection.non_registered_balance.toLocaleString('en-CA', {maximumFractionDigits: 0});
        document.getElementById('totalValue').textContent = 
            '$' + retirementProjection.total_balance.toLocaleString('en-CA', {maximumFractionDigits: 0});
    }
}

function drawChart(projections) {
    const ctx = document.getElementById('balanceChart').getContext('2d');
    
    if (window.retirementChart) {
        window.retirementChart.destroy();
    }
    
    // Extract data for each account type
    const ages = projections.map(p => p.age);
    const taxesEstimated = projections.map(p => p.taxes_estimated);
    const rrspBalances = projections.map(p => p.rrsp_rrif_balance);
    const tfsaBalances = projections.map(p => p.tfsa_balance);
    const nonRegBalances = projections.map(p => p.non_registered_balance);
    const totalBalances = projections.map(p => p.total_balance);
    
    window.retirementChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ages,
            datasets: [
                {
                    label: 'RRSP/RRIF',
                    data: rrspBalances,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'TFSA',
                    data: tfsaBalances,
                    borderColor: '#764ba2',
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'Non-Registered',
                    data: nonRegBalances,
                    borderColor: '#f093fb',
                    backgroundColor: 'rgba(240, 147, 251, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false
                },                {
                    label: 'Taxes Paid (Annual)',
                    data: taxesEstimated,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    hidden: true,  // Hidden by default
                    yAxisID: 'y1'
                },

                {
                    label: 'Total',
                    data: totalBalances,
                    borderColor: '#4facfe',
                    backgroundColor: 'rgba(79, 172, 254, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + 
                                context.parsed.y.toLocaleString('en-CA', {maximumFractionDigits: 0});
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Age'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Balance ($)'
                    },
                    ticks: {
                        callback: function(value) {
                            if (value >= 1000000) {
                                return '$' + (value / 1000000).toFixed(1) + 'M';
                            } else if (value >= 1000) {
                                return '$' + (value / 1000).toFixed(0) + 'K';
                            }
                            return '$' + value;
                        }
                    }
                },
                y1: {
                    beginAtZero: true,
                    position: 'right',
                    display: 'auto',  // Hide when dataset is hidden
                    title: {
                        display: true,
                        text: 'Annual Taxes ($)',
                        color: '#ef4444'
                    },
                    ticks: {
                        callback: function(value) {
                            if (value >= 1000) {
                                return '$' + (value / 1000).toFixed(0) + 'K';
                            }
                            return '$' + value;
                        },
                        color: '#ef4444'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// Helper Functions
function showStatus(message) {
    const el = document.getElementById('statusMessage');
    el.textContent = message;
    el.classList.remove('hidden');
    setTimeout(() => el.classList.add('hidden'), 5000);
}

function showError(message) {
    const el = document.getElementById('errorMessage');
    el.textContent = message;
    el.classList.remove('hidden');
}

function clearMessages() {
    document.getElementById('statusMessage').classList.add('hidden');
    document.getElementById('errorMessage').classList.add('hidden');
}

// Calculate with Payment
async function calculateWithPayment() {
    if (!walletConnected) {
        showError('Please connect your Phantom wallet first');
        return;
    }

    showStatus('Processing payment...');
    clearMessages();

    try {
        // 1. Create payment transaction
        const transaction = await createPaymentTransaction();
        
        // 2. Request signature from user
        const { signature } = await wallet.signAndSendTransaction(transaction);
        showStatus('Payment sent! Verifying transaction...');

        // 3. Wait for confirmation
        await waitForConfirmation(signature);
        
        // 4. Send to backend for verification and calculation
        const data = getFormData();

        // Build URL with query parameters
        const url = new URL(`${API_BASE_URL}/api/v1/retirement/calculate-paid`);
        url.searchParams.append('payment_signature', signature);
        url.searchParams.append('wallet_address', wallet.publicKey.toString());

        const response = await fetch(url.toString(), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Payment verification failed: ${response.status}`);
        }

        const result = await response.json();
        displayResults(result);
        showStatus(`✅ Payment verified! Calculation complete (Tx: ${signature.slice(0, 8)}...)`);
    } catch (error) {
        console.error('Payment error:', error);
        showError('Payment failed: ' + error.message);
    }
}

// Create Solana payment transaction
async function createPaymentTransaction() {
    const Connection = window.solanaWeb3.Connection;
    const PublicKey = window.solanaWeb3.PublicKey;
    const Transaction = window.solanaWeb3.Transaction;
    const SystemProgram = window.solanaWeb3.SystemProgram;
    const LAMPORTS_PER_SOL = window.solanaWeb3.LAMPORTS_PER_SOL;

    // Connect to Solana
    const connection = new Connection('https://api.devnet.solana.com', 'confirmed');
    
    // Recipient address (your treasury wallet - CHANGE THIS!)
    const recipient = new PublicKey('4m5yJZMSYK2N6htdkwQ8t4dsmuRSxuZ2rDba51cFc25m');
    
    // Get recent blockhash
    const { blockhash } = await connection.getLatestBlockhash();
    
    // Create transfer instruction
    const transaction = new Transaction({
        recentBlockhash: blockhash,
        feePayer: wallet.publicKey,
    }).add(
        SystemProgram.transfer({
            fromPubkey: wallet.publicKey,
            toPubkey: recipient,
            lamports: PAYMENT_AMOUNT * LAMPORTS_PER_SOL,
        })
    );

    return transaction;
}

// Wait for transaction confirmation
async function waitForConfirmation(signature) {
    const Connection = window.solanaWeb3.Connection;
    const connection = new Connection('https://api.devnet.solana.com', 'confirmed');
    
    const confirmation = await connection.confirmTransaction(signature, 'confirmed');
    if (confirmation.value.err) {
        throw new Error('Transaction failed');
    }
    return confirmation;
}


// Mode Toggle Handler
let currentMode = 'free';

function setupModeToggle() {
    const freeModeRadio = document.getElementById('freeModeRadio');
    const batchModeRadio = document.getElementById('batchModeRadio');
    const freeModeLabel = document.getElementById('freeModeLabel');
    const batchModeLabel = document.getElementById('batchModeLabel');
    const form = document.getElementById('retirementForm');
    
    freeModeRadio.addEventListener('change', () => {
        if (freeModeRadio.checked) {
            switchToFreeMode();
        }
    });
    
    batchModeRadio.addEventListener('change', () => {
        if (batchModeRadio.checked) {
            switchToBatchMode();
        }
    });
    
}

// ===== BATCH MODE FUNCTIONS =====


// Update calculate button states based on mode
function updateCalculateButtons() {
    const isBatchMode = document.getElementById('batchModeRadio')?.checked;
    const paidButton = document.getElementById('calculateBtn');
    
    if (paidButton) {
        if (isBatchMode) {
            paidButton.disabled = false;
            paidButton.style.opacity = '1';
            paidButton.style.cursor = 'pointer';
            paidButton.title = 'Run batch analysis with payment';
        } else {
            paidButton.disabled = true;
            paidButton.style.opacity = '0.5';
            paidButton.style.cursor = 'not-allowed';
            paidButton.title = 'Switch to Batch mode to use paid calculation';
        }
    }
}

function switchToFreeMode() {
    currentMode = 'free';
    const freeModeLabel = document.getElementById('freeModeLabel');
    const batchModeLabel = document.getElementById('batchModeLabel');
    const form = document.getElementById('retirementForm');
    
    freeModeLabel.classList.add('active');
    batchModeLabel.classList.remove('active');
    form.classList.remove('batch-mode');
    
    // Hide batch controls, show original inputs
    document.querySelectorAll('.batch-controls').forEach(el => el.style.display = 'none');
    document.querySelectorAll('input[data-batch-field]').forEach(el => el.style.display = 'block');
    
}

function switchToBatchMode() {
    currentMode = 'batch';
    const freeModeLabel = document.getElementById('freeModeLabel');
    const batchModeLabel = document.getElementById('batchModeLabel');
    const form = document.getElementById('retirementForm');
    
    batchModeLabel.classList.add('active');
    freeModeLabel.classList.remove('active');
    form.classList.add('batch-mode');
    
    // Show batch controls, hide original inputs
    document.querySelectorAll('.batch-controls').forEach(el => el.style.display = 'block');
    document.querySelectorAll('input[data-batch-field]').forEach(el => el.style.display = 'none');
    
}

function transformFormForBatchMode() {
    const rangeFields = [
        { id: 'retirementAge', label: 'Retirement Age', defaultEnabled: false },
        { id: 'rrspBalance', label: 'RRSP Balance', defaultEnabled: true },
        { id: 'tfsaBalance', label: 'TFSA Balance', defaultEnabled: true },
        { id: 'nonRegistered', label: 'Non-Registered Balance', defaultEnabled: true },
        { id: 'desiredSpending', label: 'Annual Spending', defaultEnabled: true },
        { id: 'monthlyContribution', label: 'Monthly Savings', defaultEnabled: false },
        { id: 'rrspRealReturn', label: 'RRSP Real Return (%)', defaultEnabled: false },
        { id: 'tfsaRealReturn', label: 'TFSA Real Return (%)', defaultEnabled: false },
        { id: 'nonRegRealReturn', label: 'Non-Reg Real Return (%)', defaultEnabled: true },{ id: 'cppStartAge', label: 'CPP Start Age', defaultEnabled: false },
        { id: 'oasStartAge', label: 'OAS Start Age', defaultEnabled: false }
    ];

    rangeFields.forEach(field => {
        const originalInput = document.getElementById(field.id);
        if (!originalInput) {
            console.warn('Field not found:', field.id);
            return;
        }

        const container = originalInput.parentElement;
        
        // Create batch mode controls
        const batchControls = document.createElement('div');
        batchControls.className = 'batch-controls';
        batchControls.style.display = 'none';
        
        batchControls.innerHTML = `
            <div class="batch-range-header">
                <label class="batch-enable-label">
                    <input type="checkbox" class="batch-enable" data-field="${field.id}" ${field.defaultEnabled ? 'checked' : ''}>
                    <strong>Vary ${field.label}</strong>
                </label>
            </div>
            <div class="batch-range-inputs">
                <div class="range-input-group">
                    <label>Min</label>
                    <input type="number" class="batch-min" data-field="${field.id}" value="${originalInput.value}" step="any">
                </div>
                <div class="range-input-group">
                    <label>Max</label>
                    <input type="number" class="batch-max" data-field="${field.id}" value="${originalInput.value}" step="any">
                </div>
            </div>
        `;
        
        container.appendChild(batchControls);
        originalInput.setAttribute('data-batch-field', field.id);
    });
    
}

// Call setup on page load


// ===== BATCH SCENARIO COUNTER =====

function updateScenarioCount() {
    const enabledCheckboxes = document.querySelectorAll('.batch-enable:checked');
    const enabledCount = enabledCheckboxes.length;
    const scenarioCount = Math.pow(2, enabledCount);
    
    // Constants
    const SOL_PER_RUN = 0.00002;
    const SOL_USD_RATE = 150; // Approximate
    const WARN_THRESHOLD = 2000;
    const BLOCK_THRESHOLD = 4096;
    
    const totalCost = scenarioCount * SOL_PER_RUN;
    const estimatedUSD = totalCost * SOL_USD_RATE;
    const estimatedTime = (scenarioCount * 0.04).toFixed(1); // 40ms per scenario
    
    // Update or create the counter display
    let counterDiv = document.getElementById('batchScenarioCounter');
    if (!counterDiv) {
        counterDiv = document.createElement('div');
        counterDiv.id = 'batchScenarioCounter';
        counterDiv.className = 'batch-scenario-counter';
        
        // Insert after the mode toggle
        const modeToggle = document.querySelector('.mode-toggle-container');
        modeToggle.parentNode.insertBefore(counterDiv, modeToggle.nextSibling);
    }
    
    // Determine status
    let status = 'ok';
    let statusIcon = '✅';
    let statusText = '';
    
    if (scenarioCount > BLOCK_THRESHOLD) {
        status = 'blocked';
        statusIcon = '🚫';
        statusText = `Too many scenarios! Maximum is ${BLOCK_THRESHOLD.toLocaleString()}.`;
    } else if (scenarioCount > WARN_THRESHOLD) {
        status = 'warning';
        statusIcon = '⚠️';
        statusText = `Large batch - will take ~${Math.ceil(scenarioCount * 0.04 / 60)} minutes.`;
    }
    
    counterDiv.innerHTML = `
        <div class="counter-status ${status}">
            <div class="counter-main">
                <span class="counter-icon">${statusIcon}</span>
                <div class="counter-details">
                    <div class="counter-primary">
                        <strong>${scenarioCount.toLocaleString()}</strong> scenarios
                        <span class="counter-separator">|</span>
                        <strong>~${estimatedTime}s</strong>
                        <span class="counter-separator">|</span>
                        <strong>${totalCost.toFixed(5)} SOL</strong>
                        <span class="counter-secondary">(~$${estimatedUSD.toFixed(2)})</span>
                    </div>
                    ${statusText ? `<div class="counter-warning">${statusText}</div>` : ''}
                </div>
            </div>
            <div class="counter-info">
                ${enabledCount} field${enabledCount !== 1 ? 's' : ''} enabled (2^${enabledCount} = ${scenarioCount})
            </div>
        </div>
    `;
    
    // Show/hide based on mode
    if (currentMode === 'batch') {
        counterDiv.style.display = 'block';
    } else {
        counterDiv.style.display = 'none';
    }
    
    // Disable submit button if blocked
    const submitButton = document.querySelector('#calculateBtn, button[type="submit"]');
    if (submitButton && status === 'blocked') {
        submitButton.disabled = true;
        submitButton.title = 'Too many scenarios selected';
    } else if (submitButton) {
        submitButton.disabled = false;
        submitButton.title = '';
    }
    
    return { scenarioCount, status, enabledCount };
}

// Update the counter when checkboxes change
function setupBatchCounterListeners() {
    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('batch-enable')) {
            updateScenarioCount();
        }
    });
}

// Update switchToBatchMode to show counter
const originalSwitchToBatch = switchToBatchMode;
switchToBatchMode = function() {
    originalSwitchToBatch();
    updateScenarioCount();
    updateCalculateButtons(); // Enable paid button
};

// Update switchToFreeMode to hide counter
const originalSwitchToFree = switchToFreeMode;
switchToFreeMode = function() {
    originalSwitchToFree();
    const counterDiv = document.getElementById('batchScenarioCounter');
    if (counterDiv) {
        counterDiv.style.display = 'none';
        }
    updateCalculateButtons(); // Disable paid button
};

// Initialize counter listeners
setupBatchCounterListeners();


// ===== BATCH SUBMISSION FLOW =====

function getBatchInputData() {
    // Collect all enabled range fields
    const batchInput = {
        // Single-value fields
        current_age: parseInt(document.getElementById('currentAge').value),
        life_expectancy: parseInt(document.getElementById('lifeExpectancy').value),
        province: document.getElementById('province').value,
        real_estate_value: 0,  // Legacy field, not used with arrays
        // Pensions array
        // Pensions array (only if checkbox checked)
        pensions: document.getElementById('includePension')?.checked ? getPensionsData() : [],
        
        // Additional income streams (only if checkbox checked)
        additional_income: document.getElementById('includeAdditionalIncome')?.checked ? getAdditionalIncomeData() : [],
        
        // Range fields
        retirement_age: getRangeField('retirementAge'),
        rrsp_balance: getRangeField('rrspBalance'),
        tfsa_balance: getRangeField('tfsaBalance'),
        nonreg_balance: getRangeField('nonRegistered'),
        annual_spending: getRangeField('desiredSpending'),
        monthly_savings: getRangeField('monthlyContribution'),
        rrsp_real_return: getRangeField('rrspRealReturn', true), // Convert % to decimal
        tfsa_real_return: getRangeField('tfsaRealReturn', true),
        nonreg_real_return: getRangeField('nonRegRealReturn', true),
        real_estate_holdings: getPropertiesData(),
        real_estate_appreciation: getRangeField('realEstateRealReturn', true),
        real_estate_sale_age: getRangeField('realEstateSaleAge'),
        cpp_start_age: getRangeField('cppStartAge'),
        oas_start_age: getRangeField('oasStartAge')
    };
    
    return batchInput;
}

function getRangeField(fieldId, isPercentage = false) {
    const checkbox = document.querySelector(`.batch-enable[data-field="${fieldId}"]`);
    const minInput = document.querySelector(`.batch-min[data-field="${fieldId}"]`);
    const maxInput = document.querySelector(`.batch-max[data-field="${fieldId}"]`);
    
    const enabled = checkbox ? checkbox.checked : false;
    let minVal = parseFloat(minInput?.value || 0);
    let maxVal = parseFloat(maxInput?.value || minVal);
    
    // Convert percentage to decimal
    if (isPercentage) {
        minVal = minVal / 100;
        maxVal = maxVal / 100;
    }
    
    return {
        min: minVal,
        max: enabled ? maxVal : null,
        enabled: enabled
    };
}

async function estimateBatchCost() {
    // Logging moved after batchInput is defined
    try {
        const batchInput = getBatchInputData();
        // Payload logging removed for production
        
        const response = await fetch(`${API_BASE_URL}/api/v1/retirement/calculate-batch-estimate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(batchInput)
        });
        
        if (!response.ok) {
            const error = await response.json();
            console.error('❌ Backend error:', error);
            console.error('Status:', response.status, response.statusText);
            throw new Error(JSON.stringify(error));
        }
        
        return await response.json();
    } catch (error) {
        console.error('Estimation error:', error);
        throw error;
    }
}

async function submitBatchCalculation() {
    if (!wallet) {
        showStatus('Please connect your Phantom wallet first', 'error');
        return;
    }
    
    try {
        showStatus('📊 Estimating batch calculation...', 'info');
        
        // Step 1: Get estimate
        const estimate = await estimateBatchCost();
        
        if (!estimate.feasible) {
            showStatus(`❌ Too many scenarios: ${estimate.scenario_count}. Maximum is 4,096.`, 'error');
            return;
        }
        
        // Step 2: Confirm with user
        const costSOL = estimate.cost_sol.toFixed(5);
        const costUSD = estimate.cost_usd_estimate.toFixed(2);
        const timeEstimate = estimate.estimated_time_seconds.toFixed(1);
        
        const confirmed = confirm(
            `🎯 Batch Calculation Summary:\n\n` +
            `Scenarios: ${estimate.scenario_count.toLocaleString()}\n` +
            `Estimated Time: ~${timeEstimate}s\n` +
            `Cost: ${costSOL} SOL (~$${costUSD})\n\n` +
            `Proceed with payment?`
        );
        
        if (!confirmed) {
            showStatus('Batch calculation cancelled', 'info');
            return;
        }
        
        // Step 3: Create payment transaction
        showStatus('💰 Creating payment transaction...', 'info');
        
        const connection = new window.solanaWeb3.Connection(
            'https://api.devnet.solana.com',
            'confirmed'
        );
        
        const recipientPubkey = new window.solanaWeb3.PublicKey(
            '4m5yJZMSYK2N6htdkwQ8t4dsmuRSxuZ2rDba51cFc25m' // Treasury wallet
        );
        
        const lamports = Math.floor(estimate.cost_sol * 1000000000);
        
        const transaction = new window.solanaWeb3.Transaction().add(
            window.solanaWeb3.SystemProgram.transfer({
                fromPubkey: wallet.publicKey,
                toPubkey: recipientPubkey,
                lamports: lamports
            })
        );
        
        transaction.feePayer = wallet.publicKey;
        const { blockhash } = await connection.getLatestBlockhash();
        transaction.recentBlockhash = blockhash;
        
        // Step 4: Sign and send transaction
        showStatus('✍️ Please approve the transaction in Phantom...', 'info');
        
        const signed = await wallet.signAndSendTransaction(transaction);
        console.log('Transaction signature:', signed.signature);
        
        showStatus('⏳ Confirming transaction...', 'info');
        
        await connection.confirmTransaction(signed.signature, 'confirmed');
        
        console.log('✅ Payment confirmed');
        
        // Step 5: Submit batch calculation with payment proof
        showStatus('🔄 Processing batch calculation...', 'info');
        
        const batchInput = getBatchInputData();
        // Payload logging removed for production
        const url = new URL(`${API_BASE_URL}/api/v1/retirement/calculate-batch`);
        url.searchParams.append('payment_signature', signed.signature);
        url.searchParams.append('wallet_address', wallet.publicKey.toString());
        
        const batchResponse = await fetch(url.toString(), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(batchInput)
        });
        
        if (!batchResponse.ok) {
            const error = await batchResponse.json();
            throw new Error(error.detail || 'Batch calculation failed');
        }
        
        // Step 6: Download CSV
        const blob = await batchResponse.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `retirement_scenarios_${Date.now()}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);

        // Auto-scroll to show download buttons
        setTimeout(() => {
            window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
        }, 500);
        
        // Get or create batchResults container
        let batchResultsDiv = document.getElementById('batchResults');
        if (!batchResultsDiv) {
            // Create it if it doesn't exist
            batchResultsDiv = document.createElement('div');
            batchResultsDiv.id = 'batchResults';
            batchResultsDiv.style.cssText = 'margin-top: 20px;';
            
            // Insert after resultsSection or at end of form
            const resultsSection = document.getElementById('resultsSection') || 
                                   document.querySelector('.calculator-container') ||
                                   document.body;
            resultsSection.parentNode.insertBefore(batchResultsDiv, resultsSection.nextSibling);
        }
        
        // Clear previous results to prevent duplication
        batchResultsDiv.innerHTML = '';
        
        // Add template download buttons
        const templateDiv = document.createElement('div');
        templateDiv.style.cssText = 'margin: 20px 0; padding: 15px; background: #e8f5e9; border-radius: 8px; text-align: center;';
        templateDiv.innerHTML = `
            <p style="margin: 0 0 10px; font-weight: bold; color: #2e7d32;">📊 Analyze Your Results:</p>
            <a href="https://web-production-c1f93.up.railway.app/api/v1/templates/excel" 
               target="_blank" 
               style="display: inline-block; margin: 5px; padding: 10px 20px; background: #4caf50; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">
                📥 Download Excel Template
            </a>
            <a href="https://web-production-c1f93.up.railway.app/api/v1/templates/sheets-guide" 
               target="_blank" 
               style="display: inline-block; margin: 5px; padding: 10px 20px; background: #2196f3; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">
                📄 Google Sheets Guide
            </a>
        `;
        
        // Insert into batchResults container (cleared above)
        if (batchResultsDiv) {
            batchResultsDiv.appendChild(templateDiv);
            // Auto-scroll to show buttons
            templateDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        
        showStatus(
            `✅ Success! ${estimate.scenario_count} scenarios calculated.

` +
            `📊 CSV downloaded! Now analyze your results:
` +
            `📥 Excel Template: github.com/ZZCameron/retirement-planning-dapp/raw/master/templates/Retirement_Analysis_Template.xlsx
` +
            `📥 Google Sheets Guide: github.com/ZZCameron/retirement-planning-dapp/blob/master/templates/GOOGLE_SHEETS_GUIDE.md

` +
            `Transaction: ${signed.signature.substring(0, 20)}...` +
            `Transaction: ${signed.signature.substring(0, 20)}...`,
            'success'
        );
        
    } catch (error) {
        console.error('Batch calculation error:', error);
        showStatus(`❌ Error: ${error.message}`, 'error');
    }
}


// Update the calculate button to handle both modes
function setupCalculateButton() {
    const calculateBtn = document.getElementById('calculateBtn');
    
    if (!calculateBtn) {
        console.error('❌ Calculate button not found!');
        return;
    }
    
    // Remove any existing listeners by cloning the button
    const newBtn = calculateBtn.cloneNode(true);
    calculateBtn.parentNode.replaceChild(newBtn, calculateBtn);
    
    newBtn.addEventListener('click', async (e) => {
        e.preventDefault();

        
        if (currentMode === 'free') {
            // Use existing free calculation
            await testCalculate();
        } else {
            // Use batch calculation
            await submitBatchCalculation();
        }
    });
    

}

// Call this on page load




// ===== PENSION MANAGEMENT =====
let pensionCounter = 0;

function createPensionEntry(data = {}) {
    const id = pensionCounter++;
    const div = document.createElement('div');
    div.className = 'pension-entry';
    div.dataset.pensionId = id;
    
    div.innerHTML = `
        <div class="pension-header">
            <h4>Pension ${id + 1}</h4>
            ${id > 0 ? '<button type="button" class="btn-remove" onclick="removePension(' + id + ')">✖ Remove</button>' : ''}
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Monthly Amount ($)</label>
                <input type="number" class="pension-monthly" data-pension-id="${id}" 
                       min="0" step="100" value="${data.monthly || 1000}">
            </div>
            <div class="form-group">
                <label>Start Year</label>
                <input type="number" class="pension-start-year" data-pension-id="${id}" 
                       min="2024" max="2100" value="${data.startYear || 2034}">
            </div>
            <div class="form-group">
                <label>Annual Indexing (%)</label>
                <input type="number" class="pension-indexing" data-pension-id="${id}" 
                       min="-5" max="10" step="0.1" value="${data.indexing || 2.0}">
            </div>
        </div>
    `;
    
    return div;
}

function addPension(data = {}) {
    const container = document.getElementById('pensionsContainer');
    if (container) {
        container.appendChild(createPensionEntry(data));
    }
}

function removePension(id) {
    const entry = document.querySelector(`[data-pension-id="${id}"]`)?.closest('.pension-entry');
    if (entry) {
        entry.remove();
    }
}

function getPensionsData() {
    const pensions = [];
    document.querySelectorAll('.pension-entry').forEach(entry => {
        const id = entry.dataset.pensionId;
        const monthlyEl = document.querySelector(`.pension-monthly[data-pension-id="${id}"]`);
        const startYearEl = document.querySelector(`.pension-start-year[data-pension-id="${id}"]`);
        const indexingEl = document.querySelector(`.pension-indexing[data-pension-id="${id}"]`);
        
        pensions.push({
            monthly_amount: parseFloat(monthlyEl?.value || 0),
            start_year: parseInt(startYearEl?.value || new Date().getFullYear()),
            indexing_rate: parseFloat(indexingEl?.value || 0) / 100
        });
    });
    
    return pensions;
}

// ===== ADDITIONAL INCOME FUNCTIONS =====

let additionalIncomeIdCounter = 0;

function createAdditionalIncomeEntry(data = {}) {
    const id = additionalIncomeIdCounter++;
    const monthly = data.monthly || 500;
    const startYear = data.startYear || 2034;
    const indexing = data.indexing || 0;
    const hasEndYear = data.endYear !== undefined && data.endYear !== null;
    const endYear = data.endYear || 2044;
    
    return `
        <div class="income-entry" data-income-id="${id}" style="background: #f0f8ff; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #2196f3;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <strong>Income Stream #${id + 1}</strong>
                <button type="button" onclick="removeAdditionalIncome(${id})" class="btn btn-danger btn-sm">Remove</button>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div>
                    <label>Monthly Amount ($)</label>
                    <input type="number" class="income-monthly" data-income-id="${id}" value="${monthly}" min="0" step="100" required>
                </div>
                <div>
                    <label>Start Year</label>
                    <input type="number" class="income-start-year" data-income-id="${id}" value="${startYear}" min="2024" max="2100" required>
                </div>
                <div>
                    <label>Annual Indexing (%)</label>
                    <input type="number" class="income-indexing" data-income-id="${id}" value="${indexing}" min="-10" max="10" step="0.1">
                    <small style="color: #666;">Positive for growth, negative for declining income, 0 for fixed</small>
                </div>
                <div>
                    <label style="display: flex; align-items: center; gap: 5px;">
                        <input type="checkbox" class="income-has-end-year" data-income-id="${id}" ${hasEndYear ? 'checked' : ''} 
                               onchange="toggleIncomeEndYear(${id})">
                        <span>Income ends in specific year?</span>
                    </label>
                    <input type="number" class="income-end-year" data-income-id="${id}" value="${endYear}" 
                           min="2024" max="2100" ${!hasEndYear ? 'disabled' : ''} 
                           style="margin-top: 5px; ${!hasEndYear ? 'opacity: 0.5;' : ''}">
                </div>
            </div>
        </div>
    `;
}

function addAdditionalIncome(data) {
    const container = document.getElementById('additionalIncomeContainer');
    if (container) {
        container.insertAdjacentHTML('beforeend', createAdditionalIncomeEntry(data));
    }
}

function removeAdditionalIncome(id) {
    const entry = document.querySelector(`.income-entry[data-income-id="${id}"]`);
    if (entry) {
        entry.remove();
    }
}

function toggleIncomeEndYear(id) {
    const checkbox = document.querySelector(`.income-has-end-year[data-income-id="${id}"]`);
    const endYearInput = document.querySelector(`.income-end-year[data-income-id="${id}"]`);
    
    if (checkbox && endYearInput) {
        endYearInput.disabled = !checkbox.checked;
        endYearInput.style.opacity = checkbox.checked ? '1' : '0.5';
    }
}

function getAdditionalIncomeData() {
    const incomes = [];
    document.querySelectorAll('.income-entry').forEach(entry => {
        const id = entry.dataset.incomeId;
        const monthlyEl = document.querySelector(`.income-monthly[data-income-id="${id}"]`);
        const startYearEl = document.querySelector(`.income-start-year[data-income-id="${id}"]`);
        const indexingEl = document.querySelector(`.income-indexing[data-income-id="${id}"]`);
        const hasEndYearEl = document.querySelector(`.income-has-end-year[data-income-id="${id}"]`);
        const endYearEl = document.querySelector(`.income-end-year[data-income-id="${id}"]`);
        
        if (monthlyEl && startYearEl) {
            const income = {
                monthly_amount: parseFloat(monthlyEl.value) || 0,
                start_year: parseInt(startYearEl.value) || 2034,
                indexing_rate: parseFloat(indexingEl.value) / 100 || 0
            };
            
            if (hasEndYearEl && hasEndYearEl.checked && endYearEl) {
                income.end_year = parseInt(endYearEl.value);
            }
            
            incomes.push(income);
        }
    });
    
    return incomes;
}



        const indexingEl = document.querySelector(`.pension-indexing[data-pension-id="${id}"]`);
        
        if (monthlyEl && startYearEl && indexingEl) {
            const monthly = parseFloat(monthlyEl.value);
            const startYear = parseInt(startYearEl.value);
            const indexing = parseFloat(indexingEl.value) / 100;
            
            pensions.push({
                monthly_amount: monthly,
                start_year: startYear,
                annual_indexing: indexing
            });
        }
    });
    return pensions;
}

// ===== PROPERTY MANAGEMENT =====
let propertyCounter = 0;

function createPropertyEntry(data = {}) {
    const id = propertyCounter++;
    const div = document.createElement('div');
    div.className = 'property-entry';
    div.dataset.propertyId = id;
    
    div.innerHTML = `
        <div class="property-header">
            <h4>Property ${id + 1}</h4>
            <button type="button" class="btn-remove" onclick="removeProperty(${id})">✖ Remove</button>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Property Type</label>
                <select class="property-type" data-property-id="${id}">
                    <option value="primary_residence" ${data.type === 'primary_residence' ? 'selected' : ''}>Primary Residence</option>
                    <option value="cottage" ${data.type === 'cottage' ? 'selected' : ''}>Cottage/Vacation</option>
                    <option value="rental" ${data.type === 'rental' ? 'selected' : ''}>Rental Property</option>
                    <option value="investment" ${data.type === 'investment' ? 'selected' : ''}>Investment Property</option>
                </select>
            </div>
            <div class="form-group">
                <label>Current Value ($)</label>
                <input type="number" class="property-value" data-property-id="${id}" 
                       min="0" step="10000" value="${data.value || 500000}">
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Real Return (%/year)</label>
                <input type="number" class="property-return" data-property-id="${id}" 
                       min="-10" max="15" step="0.1" value="${data.return || 2.0}">
            </div>
            <div class="form-group">
                <label>Sale Age (0 = never sell)</label>
                <input type="number" class="property-sale-age" data-property-id="${id}" 
                       min="0" max="150" value="${data.saleAge || 75}">
            </div>
        </div>
    `;
    
    return div;
}

function addProperty(data = {}) {
    const container = document.getElementById('propertiesContainer');
    if (container) {
        container.appendChild(createPropertyEntry(data));
    }
}

function removeProperty(id) {
    const entry = document.querySelector(`.property-entry[data-property-id="${id}"]`);
    if (entry) {
        entry.remove();
    }
}


// ===== INITIALIZATION =====
document.getElementById('addPensionBtn')?.addEventListener('click', () => addPension());
document.getElementById('addAdditionalIncomeBtn')?.addEventListener('click', () => addAdditionalIncome());

// Additional Income checkbox toggle
document.getElementById('includeAdditionalIncome')?.addEventListener('change', function() {
    const container = document.getElementById('additionalIncomeContainer');
    const button = document.getElementById('addAdditionalIncomeBtn');
    
    if (this.checked) {
        button.style.display = 'block';
        // Add first income stream if none exist
        if (document.querySelectorAll('.income-entry').length === 0) {
            addAdditionalIncome({ monthly: 1000, startYear: 2034, indexing: 0 });
        }
    } else {
        button.style.display = 'none';
        // Clear all income entries when unchecked
        container.innerHTML = '';
    }
});
document.getElementById('addPropertyBtn')?.addEventListener('click', () => addProperty());

function getPropertiesData() {
    const properties = [];
    document.querySelectorAll('.property-entry').forEach(entry => {
        const id = entry.dataset.propertyId;
        const typeEl = document.querySelector(`.property-type[data-property-id="${id}"]`);
        const valueEl = document.querySelector(`.property-value[data-property-id="${id}"]`);
        const returnEl = document.querySelector(`.property-return[data-property-id="${id}"]`);
        const saleAgeEl = document.querySelector(`.property-sale-age[data-property-id="${id}"]`);
        
        if (typeEl && valueEl && returnEl && saleAgeEl) {
            const type = typeEl.value;
            const value = parseFloat(valueEl.value);
            const returnRate = parseFloat(returnEl.value) / 100;
            const saleAge = parseInt(saleAgeEl.value);
            
            if (value > 0) {
                properties.push({
                    property_type: type,
                    value: value,
                    real_return: returnRate,
                    sale_age: saleAge
                });
            }
        }
    });
    return properties;
}


// Removed: Auto-add pension on page load (users add manually via button)
