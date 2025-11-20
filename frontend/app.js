// Configuration -->added to ensure the github repo was aligned
const API_BASE_URL = 'http://localhost:8000';
const SOLANA_NETWORK = 'devnet';
const PAYMENT_AMOUNT = 0.01;
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
    console.log('Retirement Planning Calculator loaded');
    setupEventListeners();
    checkWalletConnection();
    updateCPPCalculation(); // Initial calculation
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
            console.log('Phantom wallet detected');
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
    return {
        current_age: parseInt(document.getElementById('currentAge').value),
        retirement_age: parseInt(document.getElementById('retirementAge').value),
        life_expectancy: parseInt(document.getElementById('lifeExpectancy').value),
        province: document.getElementById('province').value,
        rrsp_balance: parseFloat(document.getElementById('rrspBalance').value),
        tfsa_balance: parseFloat(document.getElementById('tfsaBalance').value),
        non_registered: parseFloat(document.getElementById('nonRegistered').value),
        monthly_contribution: parseFloat(document.getElementById('monthlyContribution').value),
        expected_return: parseFloat(document.getElementById('expectedReturn').value) / 100,
        expected_inflation: parseFloat(document.getElementById('expectedInflation').value) / 100,
        cpp_monthly: parseFloat(document.getElementById('cppMonthly').value),
        cpp_start_age: parseInt(document.getElementById('cppStartAge').value),
        oas_start_age: parseInt(document.getElementById('oasStartAge').value),
        desired_annual_spending: parseFloat(document.getElementById('desiredSpending').value),
        has_spouse: false,
    };

    // Add pension data if checkbox is checked (NEW!)
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
    
    return data;
}

// Display Functions
function displayResults(result) {
    document.getElementById('resultsSection').classList.remove('hidden');
    
    document.getElementById('yearsToRetirement').textContent = result.years_to_retirement;
    document.getElementById('finalBalance').textContent = 
        '$' + result.final_balance.toLocaleString('en-CA', {maximumFractionDigits: 0});
    document.getElementById('planStatus').textContent = result.success ? '✅ Viable' : '⚠️ At Risk';
    
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
        result.warnings.forEach(warn => {
            const li = document.createElement('li');
            li.textContent = warn;
            warnList.appendChild(li);
        });
    } else {
        warningsSection.classList.add('hidden');
    }
    
    drawChart(result.projections);
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

function drawChart(projections) {
    const ctx = document.getElementById('balanceChart').getContext('2d');
    
    if (window.retirementChart) {
        window.retirementChart.destroy();
    }
    
    const ages = projections.map(p => p.age);
    const balances = projections.map(p => p.total_balance);
    
    window.retirementChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ages,
            datasets: [{
                label: 'Total Balance',
                data: balances,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {display: false},
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return '$' + context.parsed.y.toLocaleString('en-CA', {maximumFractionDigits: 0});
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + (value / 1000) + 'K';
                        }
                    }
                }
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
