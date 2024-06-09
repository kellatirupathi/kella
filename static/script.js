document.getElementById('uploadButton').addEventListener('click', () => {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (file && file.type === 'text/csv') {
        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload_csv', {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                antd.notification.error({
                    message: 'Error',
                    description: data.error,
                    duration: 1,
                });
            } else {
                displayCSVData(data);
                updateUploadCount(data.length); // Update the count of uploaded user IDs
            }
        })
        .catch(error => console.error('Error:', error));
    } else {
        antd.notification.warning({
            message: 'Warning',
            description: 'Please upload a valid CSV file.',
            duration: 1,
        });
    }
});

document.getElementById('searchButton').addEventListener('click', () => {
    triggerSearch();
});

document.getElementById('keywordInput').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault();
        triggerSearch();
    }
});

document.getElementById('saveButton').addEventListener('click', () => {
    saveResultsToGoogleSheet();
});

function triggerSearch() {
    const keywordInput = document.getElementById('keywordInput').value.trim();
    const keywords = keywordInput.split(',').map(kw => kw.trim()).filter(kw => kw !== "");
    const pdfData = Array.from(document.querySelectorAll('#dataTable tbody tr')).map(row => {
        return {
            user_id: row.cells[0].innerText,
            resume_link: row.cells[1].querySelector('a').href // Retrieve the actual link from the anchor tag
        };
    });

    if (keywords.length > 0 && pdfData.length > 0) {
        const estimatedTime = calculateEstimatedTime(pdfData.length); // Estimate the search time based on the number of PDFs
        startSearchTimer(estimatedTime); // Start the timer with the estimated time
        fetch('/search_keyword', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ keywords, data: pdfData }),
        })
        .then(response => response.json())
        .then(data => {
            stopSearchTimer(); // Stop the timer
            if (data.error) {
                antd.notification.error({
                    message: 'Error',
                    description: data.error,
                    duration: 1,
                });
            } else {
                displayMatchedResumes(data, keywordInput);
                updateSearchCount(data.length); // Update the count of matched user IDs
            }
        })
        .catch(error => {
            stopSearchTimer(); // Stop the timer on error
            console.error('Error:', error);
        });
    } else {
        antd.notification.warning({
            message: 'Warning',
            description: 'Please enter keywords and ensure there are resume links uploaded.',
            duration: 1,
        });
    }
}

function saveResultsToGoogleSheet() {
    const results = Array.from(document.querySelectorAll('#resultTable tbody tr')).map(row => {
        return {
            user_id: row.cells[2].innerText,
            resume_link: row.cells[1].querySelector('a').href, // Retrieve the actual link from the anchor tag
            checked: row.cells[0].querySelector('input[type="checkbox"]').checked,
            percentage: row.cells[3].innerText, // Get the percentage value
            matched_technologies: row.cells[4].innerText.split(', '), // Get the matched technologies
            existing_technologies: row.cells[5].innerText.split(', ')  // Get the existing technologies
        };
    });

    fetch('/save_results', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ results }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            antd.notification.error({
                message: 'Error',
                description: data.error,
                duration: 1,
            });
        } else {
            antd.notification.success({
                message: 'Success',
                description: 'Results saved to Google Spreadsheet.',
                duration: 1,
            });
        }
    })
    .catch(error => console.error('Error:', error));
}

function displayCSVData(data) {
    const tableBody = document.querySelector('#dataTable tbody');
    tableBody.innerHTML = '';  // Clear any existing rows

    data.forEach((row, index) => {
        const tr = document.createElement('tr');
        const tdUserId = document.createElement('td');
        const tdResumeLink = document.createElement('td');

        tdUserId.textContent = row.user_id;
        const link = document.createElement('a');
        link.href = row.resume_link;
        link.target = '_blank';
        link.textContent = `Resume${index + 1}`;
        link.addEventListener('click', (event) => {
            event.target.classList.add('red-link');
        });

        tdResumeLink.appendChild(link);

        tr.appendChild(tdUserId);
        tr.appendChild(tdResumeLink);
        tableBody.appendChild(tr);
    });
}

function displayMatchedResumes(data, keywords) {
    const resultBody = document.querySelector('#resultTable tbody');
    resultBody.innerHTML = '';  // Clear any existing rows

    if (data.length > 0) {
        data.forEach((entry, index) => {
            const tr = document.createElement('tr');
            const tdCheckbox = document.createElement('td');
            const tdLink = document.createElement('td');
            const tdUserId = document.createElement('td');
            const tdPercentage = document.createElement('td');
            const tdMatchedTechnologies = document.createElement('td'); // New column for matched technologies
            const tdExistingTechnologies = document.createElement('td'); // New column for existing technologies

            tdCheckbox.innerHTML = `<input type="checkbox" class="large-checkbox">`;

            const link = document.createElement('a');
            link.href = entry.resume_link;
            link.target = '_blank';
            link.textContent = `Resume${index + 1}`;
            link.addEventListener('click', (event) => {
                event.target.classList.add('red-link');
            });

            tdLink.appendChild(link);
            tdUserId.textContent = entry.user_id;
            tdPercentage.textContent = `${entry.percentage}%`;
            tdMatchedTechnologies.textContent = entry.matched_technologies.join(', '); // Display matched technologies
            tdExistingTechnologies.textContent = entry.existing_technologies.join(', '); // Display existing technologies

            tr.appendChild(tdCheckbox);
            tr.appendChild(tdLink);
            tr.appendChild(tdUserId);
            tr.appendChild(tdPercentage);
            tr.appendChild(tdMatchedTechnologies);
            tr.appendChild(tdExistingTechnologies);
            resultBody.appendChild(tr);
        });
    } else {
        const tr = document.createElement('tr');
        const tdNoMatch = document.createElement('td');
        tdNoMatch.setAttribute('colspan', '6'); // Updated colspan to 6
        tdNoMatch.className = 'center-message';
        tdNoMatch.textContent = `No matches found for keywords "${keywords}"`;
        tr.appendChild(tdNoMatch);
        resultBody.appendChild(tr);
    }
}

function updateUploadCount(count) {
    const uploadHeading = document.querySelector('#uploadHeading');
    uploadHeading.textContent = `Upload CSV File (${count} users)`;
}

function updateSearchCount(count) {
    const searchHeading = document.querySelector('#searchHeading');
    searchHeading.textContent = `Search Keyword in Resumes (${count} matches)`;
}

function calculateEstimatedTime(numberOfPdfs) {
    const timePerPdf = 2; // Estimate 2 seconds per PDF for processing
    return numberOfPdfs * timePerPdf;
}

function startSearchTimer(estimatedTime) {
    const resultBody = document.querySelector('#resultTable tbody');
    resultBody.innerHTML = `<tr><td colspan="6" class="center-message">Searching... <span id="timer">${estimatedTime}</span> seconds</td></tr>`; // Updated colspan to 6
    let timer = estimatedTime;
    window.searchTimer = setInterval(() => {
        timer--;
        if (timer <= 0) {
            clearInterval(window.searchTimer);
        }
        document.getElementById('timer').textContent = timer;
    }, 1000);
}

function stopSearchTimer() {
    clearInterval(window.searchTimer);
}
