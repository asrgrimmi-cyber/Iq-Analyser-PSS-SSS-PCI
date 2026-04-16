/* ═══════════════════════════════════════════════════════════
   IQ Analyzer — Application JavaScript
   Upload handling, progress polling, results rendering
   ═══════════════════════════════════════════════════════════ */

(function () {
    'use strict';

    // ── DOM Elements ──
    const uploadSection = document.getElementById('upload-section');
    const processingSection = document.getElementById('processing-section');
    const resultsSection = document.getElementById('results-section');
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const statusMsg = document.getElementById('status-msg');
    const paramsGrid = document.getElementById('params-grid');
    const plotsGrid = document.getElementById('plots-grid');
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxTitle = document.getElementById('lightbox-title');
    const lightboxClose = document.getElementById('lightbox-close');
    const newAnalysisBtn = document.getElementById('new-analysis-btn');
    const fileName = document.getElementById('file-name');

    // ── State ──
    let currentJobId = null;
    let pollTimer = null;

    // ══════════════════════════════════════
    // SECTION TRANSITIONS
    // ══════════════════════════════════════

    function showSection(section) {
        uploadSection.style.display = 'none';
        uploadSection.classList.remove('active');
        processingSection.style.display = 'none';
        processingSection.classList.remove('active');
        resultsSection.style.display = 'none';
        resultsSection.classList.remove('active');

        if (section === 'upload') {
            uploadSection.style.display = 'flex';
        } else if (section === 'processing') {
            processingSection.style.display = 'flex';
            processingSection.classList.add('active');
        } else if (section === 'results') {
            resultsSection.style.display = 'block';
            resultsSection.classList.add('active');
        }
    }

    // ══════════════════════════════════════
    // FILE UPLOAD — DRAG & DROP
    // ══════════════════════════════════════

    uploadZone.addEventListener('click', () => fileInput.click());

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadZone.classList.add('drag-over');
    });

    uploadZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) handleFile(files[0]);
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
    });

    // ══════════════════════════════════════
    // UPLOAD & PROCESSING
    // ══════════════════════════════════════

    function handleFile(file) {
        if (!file.name.endsWith('.bin')) {
            alert('Please select a .bin IQ file');
            return;
        }

        const progressBar = document.getElementById('progress-bar');
        const progressContainer = document.getElementById('progress-container');
        progressBar.style.width = '0%';
        
        fileName.textContent = file.name;
        showSection('processing');
        statusMsg.textContent = 'Uploading file...';

        const formData = new FormData();
        formData.append('file', file);

        // Use XMLHttpRequest for progress tracking
        const xhr = new XMLHttpRequest();
        
        // Tracking upload progress
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                // Map upload (0-100) to progress bar (0-50%)
                const displayPercent = percent / 2;
                progressBar.style.width = `${displayPercent}%`;
                statusMsg.textContent = `Uploading: ${percent}%`;
            }
        });

        xhr.onload = function() {
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
                if (data.error) {
                    alert('Upload error: ' + data.error);
                    showSection('upload');
                    return;
                }
                currentJobId = data.job_id;
                // Move bar to 50% once upload is done
                progressBar.style.width = '50%';
                statusMsg.textContent = 'Processing started — detecting PSS...';
                startPolling();
            } else {
                alert('Upload failed with status ' + xhr.status);
                showSection('upload');
            }
        };

        xhr.onerror = function() {
            console.error('Upload failed');
            alert('Upload failed. Check console.');
            showSection('upload');
        };

        xhr.open('POST', '/upload', true);
        xhr.send(formData);
    }

    function startPolling() {
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(pollStatus, 1500);
    }

    let fakeAnalysisProgress = 50;

    function pollStatus() {
        if (!currentJobId) return;

        fetch(`/status/${currentJobId}`)
            .then(res => res.json())
            .then(data => {
                const progressBar = document.getElementById('progress-bar');
                statusMsg.textContent = data.message || 'Processing...';

                // Simulate "Analysis" progress crawl from 50% up to 95%
                if (data.status === 'processing') {
                    if (fakeAnalysisProgress < 95) {
                        fakeAnalysisProgress += (95 - fakeAnalysisProgress) * 0.2;
                        progressBar.style.width = `${fakeAnalysisProgress}%`;
                    }
                }

                if (data.status === 'complete') {
                    clearInterval(pollTimer);
                    pollTimer = null;
                    progressBar.style.width = '100%';
                    fakeAnalysisProgress = 50; // reset
                    setTimeout(() => {
                        renderResults(data.results);
                        showSection('results');
                    }, 300);
                } else if (data.status === 'error') {
                    clearInterval(pollTimer);
                    pollTimer = null;
                    alert('Analysis failed: ' + data.message);
                    showSection('upload');
                }
            })
            .catch(err => {
                console.error('Poll error:', err);
            });
    }

    // ══════════════════════════════════════
    // RENDER RESULTS
    // ══════════════════════════════════════

    // Highlight keys — these get the accent treatment
    const HIGHLIGHT_KEYS = [
        'Detected PCI', 'Detected N_ID_2 (PSS)', 'Detected N_ID_1 (SSS)', 'Detected Subframe',
        'RSRP (dBFS)', 'RSRQ (dB)', 'SNR (dB)'
    ];

    function renderResults(results) {
        // ── Parameters ──
        paramsGrid.innerHTML = '';
        const params = results.parameters;

        for (const [key, value] of Object.entries(params)) {
            const card = document.createElement('div');
            card.className = 'param-card';
            if (HIGHLIGHT_KEYS.includes(key)) card.classList.add('highlight');

            const isLong = String(value).length > 12;

            card.innerHTML = `
                <div class="param-label">${escapeHtml(key)}</div>
                <div class="param-value ${isLong ? 'small' : ''}">${escapeHtml(String(value))}</div>
            `;
            paramsGrid.appendChild(card);
        }

        // ── Plots ──
        plotsGrid.innerHTML = '';
        const plots = results.plots;

        plots.forEach((plot, idx) => {
            const card = document.createElement('div');
            card.className = 'plot-card';
            card.innerHTML = `
                <div class="plot-card-header">
                    <span class="plot-card-title">${escapeHtml(plot.title)}</span>
                    <span class="plot-card-badge">Plot ${idx + 1}/${plots.length}</span>
                </div>
                <div class="plot-card-body">
                    <img src="${plot.path}" alt="${escapeHtml(plot.title)}" loading="lazy" />
                </div>
            `;

            card.addEventListener('click', () => openLightbox(plot.path, plot.title));
            plotsGrid.appendChild(card);
        });
    }

    // ══════════════════════════════════════
    // LIGHTBOX
    // ══════════════════════════════════════

    function openLightbox(src, title) {
        lightboxImg.src = src;
        lightboxTitle.textContent = title;
        lightbox.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeLightbox() {
        lightbox.classList.remove('active');
        document.body.style.overflow = '';
        lightboxImg.src = '';
    }

    lightboxClose.addEventListener('click', (e) => {
        e.stopPropagation();
        closeLightbox();
    });

    lightbox.addEventListener('click', closeLightbox);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeLightbox();
    });

    // ══════════════════════════════════════
    // NEW ANALYSIS
    // ══════════════════════════════════════

    newAnalysisBtn.addEventListener('click', () => {
        currentJobId = null;
        fileInput.value = '';
        showSection('upload');
    });

    // ══════════════════════════════════════
    // UTILITIES
    // ══════════════════════════════════════

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

})();
