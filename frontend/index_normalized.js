// index_normalized.js: Fetch and display normalization-based results

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('experiment-form');
    const resultsTableBody = document.querySelector('#results-table tbody');
    const normalizationDetails = document.getElementById('normalization-details');

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        // Collect parameters from form (adapt as needed)
        const params = {};
        Array.from(form.elements).forEach(el => {
            if (el.name) params[el.name] = el.value;
        });
        // Indicate normalization scoring
        params['use_normalization'] = true;
        fetchResults(params);
    });

    function fetchResults(params) {
        fetch('/api/experiment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        })
        .then(response => response.json())
        .then(data => {
            renderResults(data.results, data.normalization);
        })
        .catch(err => {
            resultsTableBody.innerHTML = '<tr><td colspan="8">Error fetching results</td></tr>';
        });
    }

    function renderResults(results, normalization) {
        resultsTableBody.innerHTML = '';
        results.forEach((sol, idx) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${sol.name || idx + 1}</td>
                <td>${sol.cost}</td>
                <td>${sol.latency}</td>
                <td>${sol.reliability}</td>
                <td>${sol.norm_cost.toFixed(3)}</td>
                <td>${sol.norm_latency.toFixed(3)}</td>
                <td>${sol.norm_reliability.toFixed(3)}</td>
                <td>${sol.score.toFixed(3)}</td>
            `;
            resultsTableBody.appendChild(row);
        });
        // Show normalization details
        normalizationDetails.innerHTML = `
            <h3>Normalization Details</h3>
            <p>Min/Max values used for normalization:</p>
            <ul>
                <li>Cost: min=${normalization.cost_min}, max=${normalization.cost_max}</li>
                <li>Latency: min=${normalization.latency_min}, max=${normalization.latency_max}</li>
                <li>Reliability: min=${normalization.reliability_min}, max=${normalization.reliability_max}</li>
            </ul>
            <p>Weights: cost=${normalization.weights.cost}, latency=${normalization.weights.latency}, reliability=${normalization.weights.reliability}</p>
            <p>Score formula: <code>score = cost_weight * (1 - norm_cost) + latency_weight * (1 - norm_latency) + reliability_weight * norm_reliability</code></p>
        `;
    }
});
