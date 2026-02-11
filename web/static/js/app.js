/**
 * DABO Dashboard — Client-side JavaScript
 * All API calls, DOM updates, charts, and interactions.
 */

const DABO = {

    // ── State ────────────────────────────────────────────
    _projectId: null,
    _sheetsData: null,
    _reviewData: null,
    _rfiData: null,
    _scheduleData: null,
    _charts: {},

    // ── Project Selection ────────────────────────────────

    getProjectId() {
        if (this._projectId) return this._projectId;
        const sel = document.getElementById('projectSelect');
        if (sel && sel.value) {
            this._projectId = parseInt(sel.value);
            return this._projectId;
        }
        const saved = localStorage.getItem('dabo_project_id');
        if (saved) {
            this._projectId = parseInt(saved);
            if (sel) sel.value = saved;
            return this._projectId;
        }
        return null;
    },

    switchProject(val) {
        this._projectId = val ? parseInt(val) : null;
        localStorage.setItem('dabo_project_id', val || '');
        // Clear cached data
        this._sheetsData = null;
        this._reviewData = null;
        this._rfiData = null;
        this._scheduleData = null;
        // Reload current page
        window.location.reload();
    },

    requireProject(contentId, warningId) {
        const pid = this.getProjectId();
        const content = document.getElementById(contentId);
        const warning = document.getElementById(warningId);
        if (!pid) {
            if (content) content.style.display = 'none';
            if (warning) warning.style.display = 'block';
        } else {
            if (content) content.style.display = 'block';
            if (warning) warning.style.display = 'none';
        }
    },

    // ── API Helper ───────────────────────────────────────

    async api(url, options = {}) {
        const defaults = {
            headers: { 'Content-Type': 'application/json' },
        };
        const opts = { ...defaults, ...options };
        if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData)) {
            opts.body = JSON.stringify(opts.body);
        }
        if (opts.body instanceof FormData) {
            delete opts.headers['Content-Type'];
        }
        const resp = await fetch(url, opts);
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ error: resp.statusText }));
            throw new Error(err.error || resp.statusText);
        }
        const ct = resp.headers.get('Content-Type') || '';
        if (ct.includes('application/json')) return resp.json();
        return resp;
    },

    // ── Toast Notifications ──────────────────────────────

    toast(message, type = 'info') {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    },


    // ═══ PROJECTS PAGE ═══════════════════════════════════

    async createProject(event) {
        event.preventDefault();
        const form = event.target;
        const data = {
            name: form.name.value,
            building_type: form.building_type.value,
            square_feet: parseInt(form.square_feet.value),
            stories: parseInt(form.stories.value),
            notes: form.notes.value,
        };
        try {
            const result = await this.api('/api/projects', { method: 'POST', body: data });
            this.toast(`Project "${result.name}" created (ID #${result.id})`, 'success');
            form.reset();
            form.square_feet.value = '50000';
            form.stories.value = '2';
            this.loadProjects();
        } catch (e) {
            this.toast(e.message, 'error');
        }
        return false;
    },

    async loadProjects() {
        const container = document.getElementById('projectsList');
        if (!container) return;

        try {
            const projects = await this.api('/api/projects');
            if (!projects.length) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">&#128203;</div>
                        <div class="empty-title">No projects yet</div>
                        <div class="text-sm text-gray-500">Create your first project above to get started.</div>
                    </div>`;
                return;
            }

            container.innerHTML = projects.map(p => `
                <div class="project-card">
                    <div class="flex justify-between items-start mb-3">
                        <div>
                            <span class="text-lg font-bold text-navy">#${p.id} — ${this._esc(p.name)}</span>
                            ${p.notes ? `<p class="text-sm text-gray-500 mt-1">${this._esc(p.notes)}</p>` : ''}
                        </div>
                        <span class="text-xs text-gray-400">${p.created_at || ''}</span>
                    </div>
                    <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
                        <div class="text-center">
                            <div class="text-sm font-bold text-navy">${this._titleCase(p.building_type)}</div>
                            <div class="text-xs text-gray-400 uppercase">Type</div>
                        </div>
                        <div class="text-center">
                            <div class="text-sm font-bold text-navy">${(p.square_feet || 0).toLocaleString()}</div>
                            <div class="text-xs text-gray-400 uppercase">Square Feet</div>
                        </div>
                        <div class="text-center">
                            <div class="text-sm font-bold text-navy">${p.stories || 0}</div>
                            <div class="text-xs text-gray-400 uppercase">Stories</div>
                        </div>
                        <div class="text-center">
                            <div class="text-sm font-bold text-navy">${p.file_count || 0}</div>
                            <div class="text-xs text-gray-400 uppercase">Files</div>
                        </div>
                        <div class="text-center">
                            <div class="text-sm font-bold text-navy">${p.sheet_count || 0}</div>
                            <div class="text-xs text-gray-400 uppercase">Sheets</div>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            container.innerHTML = `<div class="alert-error">${e.message}</div>`;
        }
    },


    // ═══ INGESTION PAGE ══════════════════════════════════

    _selectedFiles: [],

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
    },

    handleDragLeave(e) {
        e.currentTarget.classList.remove('drag-over');
    },

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
        const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.pdf'));
        this._selectedFiles = files;
        this._showSelectedFiles();
    },

    handleFileSelect(e) {
        this._selectedFiles = Array.from(e.target.files);
        this._showSelectedFiles();
    },

    _showSelectedFiles() {
        const wrap = document.getElementById('selectedFiles');
        const list = document.getElementById('fileList');
        const count = document.getElementById('fileCount');

        if (!this._selectedFiles.length) {
            wrap.classList.add('hidden');
            return;
        }

        wrap.classList.remove('hidden');
        count.textContent = `${this._selectedFiles.length} file(s) selected`;
        list.innerHTML = this._selectedFiles.map(f => `
            <div class="file-row">
                <span class="text-gray-700">${this._esc(f.name)}</span>
                <span class="text-gray-400 text-xs">${(f.size / 1024 / 1024).toFixed(1)} MB</span>
            </div>
        `).join('');
    },

    async uploadFiles() {
        const pid = this.getProjectId();
        if (!pid || !this._selectedFiles.length) return;

        const btn = document.getElementById('uploadBtn');
        const progress = document.getElementById('uploadProgress');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const progressPct = document.getElementById('progressPct');

        btn.disabled = true;
        progress.classList.remove('hidden');

        const formData = new FormData();
        this._selectedFiles.forEach(f => formData.append('files', f));

        progressText.textContent = `Uploading ${this._selectedFiles.length} file(s)...`;
        progressFill.style.width = '30%';
        progressPct.textContent = '30%';

        try {
            const result = await this.api(`/api/projects/${pid}/upload`, {
                method: 'POST',
                body: formData,
            });

            progressFill.style.width = '100%';
            progressPct.textContent = '100%';
            progressText.textContent = 'Done!';

            this.toast(`Processed ${result.uploaded} file(s)`, 'success');
            this._selectedFiles = [];
            document.getElementById('selectedFiles').classList.add('hidden');

            setTimeout(() => {
                progress.classList.add('hidden');
                this.loadFileStatus();
            }, 1500);

        } catch (e) {
            this.toast(`Upload failed: ${e.message}`, 'error');
        }

        btn.disabled = false;
    },

    async loadFileStatus() {
        const pid = this.getProjectId();
        const container = document.getElementById('fileStatus');
        if (!pid || !container) return;

        try {
            const files = await this.api(`/api/projects/${pid}/files`);
            if (!files.length) {
                container.innerHTML = '<div class="text-gray-400 text-sm py-4">No files uploaded yet.</div>';
                return;
            }

            container.innerHTML = `
                <div class="text-sm font-semibold text-navy mb-3">${files.length} file(s)</div>
                ${files.map(f => `
                    <div class="file-row">
                        <span class="text-gray-700 font-medium">${this._esc(f.filename)}</span>
                        <div class="flex items-center gap-4">
                            <span class="text-gray-400 text-xs">${f.file_type || '—'}</span>
                            <span class="text-gray-400 text-xs">${f.page_count || 0} pages</span>
                            <span class="badge badge-${(f.status || 'pending').toLowerCase()}">${f.status || 'pending'}</span>
                        </div>
                    </div>
                `).join('')}
            `;
        } catch (e) {
            container.innerHTML = `<div class="alert-error">${e.message}</div>`;
        }
    },


    // ═══ SHEETS PAGE ═════════════════════════════════════

    _DISC_COLORS: {
        GEN: '#666666', CIV: '#8B4513', ARCH: '#1976D2',
        STR: '#D32F2F', MECH: '#388E3C', PLMB: '#0097A7',
        ELEC: '#F9A825', FP: '#E53935', FA: '#C62828',
        TECH: '#7B1FA2', FS: '#FF6F00', CONV: '#455A64',
    },

    // Demo drawing PDFs — UF Rinker Hall construction documents (public educational set)
    _DEMO_DRAWINGS: {
        // Architectural
        'A-101': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_006.pdf',
        'A-102': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_007.pdf',
        'A-103': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_008.pdf',
        'A-104': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_009.pdf',
        'A-201': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_014.pdf',
        'A-301': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_018.pdf',
        'A-401': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_022.pdf',
        'A-501': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_026.pdf',
        'A-601': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_030.pdf',
        'A-701': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_035.pdf',
        'A-801': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_040.pdf',
        'A-901': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_045.pdf',
        // Structural
        'S-101': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_050.pdf',
        'S-102': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_051.pdf',
        'S-103': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_052.pdf',
        'S-104': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_053.pdf',
        'S-105': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_054.pdf',
        'S-201': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_055.pdf',
        'S-301': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_057.pdf',
        'S-401': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_059.pdf',
        // Mechanical
        'M-101': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_060.pdf',
        'M-102': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_061.pdf',
        'M-103': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_062.pdf',
        'M-201': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_063.pdf',
        'M-301': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_064.pdf',
        'M-401': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_065.pdf',
        // Plumbing
        'P-101': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_069.pdf',
        'P-102': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_070.pdf',
        'P-201': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_071.pdf',
        'P-301': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_072.pdf',
        // Electrical
        'E-101': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_075.pdf',
        'E-102': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_076.pdf',
        'E-103': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_077.pdf',
        'E-201': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_078.pdf',
        'E-301': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_080.pdf',
        'E-401': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_082.pdf',
        'E-501': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_084.pdf',
        // Fire Protection
        'FP-101': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_087.pdf',
        'FP-102': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_088.pdf',
        'FP-201': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_089.pdf',
        // General / Cover
        'G-001': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_001.pdf',
        'G-002': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/Rinker_001.pdf',
        // Civil
        'C-101': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/DEST213524.pdf',
        'C-102': 'https://coremng.dcp.ufl.edu/rinkerhall/images/rinker/Drawings/DEST213525.pdf',
    },

    async loadSheets() {
        const pid = this.getProjectId();
        if (!pid) return;

        try {
            const data = await this.api(`/api/projects/${pid}/sheets`);
            this._sheetsData = data;

            // Update metrics
            const el = (id) => document.getElementById(id);
            el('totalSheets').textContent = data.total || 0;
            el('totalDiscs').textContent = Object.keys(data.disciplines || {}).length;
            el('avgConf').textContent = data.avg_confidence ? `${Math.round(data.avg_confidence * 100)}%` : '—';

            // Discipline badges
            const badgeContainer = el('discBadges');
            if (badgeContainer && data.disciplines) {
                badgeContainer.innerHTML = Object.entries(data.disciplines)
                    .sort((a, b) => b[1] - a[1])
                    .map(([disc, count]) => {
                        const color = this._DISC_COLORS[disc] || '#888';
                        return `<span class="disc-badge" style="background:${color}">${disc} &middot; ${count}</span>`;
                    }).join('');
            }

            // Chart
            this._buildDisciplineChart(data.disciplines);

            // Populate filter
            const filter = el('discFilter');
            if (filter && data.disciplines) {
                const existing = filter.value;
                filter.innerHTML = '<option value="">All Disciplines</option>';
                Object.keys(data.disciplines).sort().forEach(d => {
                    filter.innerHTML += `<option value="${d}">${d} (${data.disciplines[d]})</option>`;
                });
                if (existing) filter.value = existing;
            }

            // Table
            this._renderSheetsTable(data.sheets || []);

        } catch (e) {
            this.toast(`Failed to load sheets: ${e.message}`, 'error');
        }
    },

    _buildDisciplineChart(disciplines) {
        if (!disciplines) return;
        const canvas = document.getElementById('discChart');
        if (!canvas) return;

        if (this._charts.disc) this._charts.disc.destroy();

        const sorted = Object.entries(disciplines).sort((a, b) => b[1] - a[1]);
        const labels = sorted.map(e => e[0]);
        const values = sorted.map(e => e[1]);
        const colors = labels.map(l => this._DISC_COLORS[l] || '#888');

        this._charts.disc = new Chart(canvas, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Sheets',
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 } },
                    x: { grid: { display: false } },
                }
            }
        });
    },

    _renderSheetsTable(sheets) {
        const body = document.getElementById('sheetsBody');
        if (!body) return;

        body.innerHTML = sheets.map(s => {
            const conf = s.confidence || 0;
            const pct = Math.round(conf * 100);
            const color = this._DISC_COLORS[s.discipline] || '#888';
            const hasDrawing = this._DEMO_DRAWINGS[s.sheet_id];
            const viewBtn = hasDrawing
                ? `<button class="btn-sm btn-view" onclick="DABO.viewDrawing('${this._esc(s.sheet_id)}','${this._esc(s.sheet_name || '')}')">View</button>`
                : '<span class="text-gray-300 text-xs">—</span>';
            return `
                <tr>
                    <td class="font-mono font-semibold">${this._esc(s.sheet_id || '—')}</td>
                    <td>${this._esc(s.sheet_name || '—')}</td>
                    <td><span class="disc-badge" style="background:${color}">${s.discipline || '?'}</span></td>
                    <td>${s.page_number || '—'}</td>
                    <td>
                        <div class="conf-bar">
                            <div class="conf-track"><div class="conf-fill" style="width:${pct}%"></div></div>
                            <span class="conf-pct">${pct}%</span>
                        </div>
                    </td>
                    <td>${viewBtn}</td>
                </tr>`;
        }).join('');
    },

    viewDrawing(sheetId, sheetName) {
        const url = this._DEMO_DRAWINGS[sheetId];
        if (!url) return;

        // Create or reuse the modal
        let modal = document.getElementById('drawingModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'drawingModal';
            modal.className = 'drawing-modal';
            modal.innerHTML = `
                <div class="drawing-modal-content">
                    <div class="drawing-modal-header">
                        <span class="drawing-modal-title" id="drawingTitle"></span>
                        <button class="drawing-modal-close" onclick="DABO.closeDrawing()">&times;</button>
                    </div>
                    <iframe id="drawingFrame" class="drawing-frame"></iframe>
                </div>
            `;
            document.body.appendChild(modal);
        }

        document.getElementById('drawingTitle').textContent = `${sheetId} — ${sheetName}`;
        document.getElementById('drawingFrame').src = url;
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    },

    closeDrawing() {
        const modal = document.getElementById('drawingModal');
        if (modal) {
            modal.classList.remove('active');
            document.getElementById('drawingFrame').src = '';
            document.body.style.overflow = '';
        }
    },

    filterSheets() {
        if (!this._sheetsData) return;
        const filter = document.getElementById('discFilter').value;
        const sheets = filter
            ? this._sheetsData.sheets.filter(s => s.discipline === filter)
            : this._sheetsData.sheets;
        this._renderSheetsTable(sheets);
    },


    // ═══ PLAN REVIEW PAGE ════════════════════════════════

    _SEV_COLORS: {
        CRITICAL: '#DC2626', MAJOR: '#F97316', MINOR: '#EAB308', INFO: '#3B82F6',
    },

    async runReview() {
        const pid = this.getProjectId();
        if (!pid) return;

        const btn = document.getElementById('reviewBtn');
        const spinner = document.getElementById('reviewSpinner');
        btn.disabled = true;
        spinner.classList.remove('hidden');

        try {
            const data = await this.api(`/api/projects/${pid}/review`, { method: 'POST' });
            this._reviewData = data;

            document.getElementById('reviewSheets').textContent = data.sheets_analyzed || 0;
            document.getElementById('reviewConflicts').textContent = data.total_conflicts || 0;
            document.getElementById('reviewDiscs').textContent = data.disciplines || 0;

            document.getElementById('reviewResults').classList.remove('hidden');

            if (data.conflicts && data.conflicts.length) {
                document.getElementById('noConflicts').classList.add('hidden');
                this._buildSeverityChart(data.conflicts);
                this._renderConflicts(data.conflicts);
            } else {
                document.getElementById('noConflicts').classList.remove('hidden');
            }

            this.toast('Plan review complete', 'success');
        } catch (e) {
            this.toast(`Review failed: ${e.message}`, 'error');
        }

        btn.disabled = false;
        spinner.classList.add('hidden');
    },

    _buildSeverityChart(conflicts) {
        const canvas = document.getElementById('severityChart');
        if (!canvas) return;
        if (this._charts.severity) this._charts.severity.destroy();

        const counts = {};
        conflicts.forEach(c => {
            const sev = c.severity || 'INFO';
            counts[sev] = (counts[sev] || 0) + 1;
        });

        const labels = Object.keys(counts);
        const values = Object.values(counts);
        const colors = labels.map(l => this._SEV_COLORS[l] || '#888');

        this._charts.severity = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{ data: values, backgroundColor: colors, borderWidth: 0 }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
            }
        });
    },

    _renderConflicts(conflicts) {
        const container = document.getElementById('conflictList');
        if (!container) return;

        container.innerHTML = conflicts.map((c, i) => `
            <div class="conflict-card" id="conflict-${i}" onclick="DABO.toggleConflict(${i})">
                <div class="conflict-header">
                    <span class="badge badge-${(c.severity || 'info').toLowerCase()}">${c.severity || 'INFO'}</span>
                    <span>${this._esc(c.rule_id || '')} — ${this._esc(c.description || '')}</span>
                    <span class="conflict-chevron">&#9654;</span>
                </div>
                <div class="conflict-body">
                    <p><strong>Sheets:</strong> ${this._esc((c.sheets || []).join(', '))}</p>
                    <p><strong>Category:</strong> ${this._esc(c.category || 'N/A')}</p>
                    <p><strong>Details:</strong> ${this._esc(c.details || 'N/A')}</p>
                </div>
            </div>
        `).join('');
    },

    toggleConflict(idOrIndex) {
        // Support both numeric index and string element ID
        const elId = typeof idOrIndex === 'string' ? idOrIndex : `conflict-${idOrIndex}`;
        const el = document.getElementById(elId);
        if (el) el.classList.toggle('open');
    },


    // ═══ RFI PAGE ════════════════════════════════════════

    async generateRFIs() {
        const pid = this.getProjectId();
        if (!pid) return;

        if (!this._reviewData || !this._reviewData.conflicts || !this._reviewData.conflicts.length) {
            this.toast('No review results with conflicts. Run Plan Review first.', 'error');
            return;
        }

        const btn = document.getElementById('genRfiBtn');
        btn.disabled = true;

        try {
            const data = await this.api(`/api/projects/${pid}/rfis`, {
                method: 'POST',
                body: { conflicts: this._reviewData.conflicts },
            });
            this._rfiData = data.rfis || [];
            this._renderRFIs();
            this.toast(`Generated ${data.total} RFIs`, 'success');
        } catch (e) {
            this.toast(`RFI generation failed: ${e.message}`, 'error');
        }

        btn.disabled = false;
    },

    _renderRFIs() {
        const rfis = this._rfiData || [];
        const body = document.getElementById('rfiBody');
        const noRfis = document.getElementById('noRfis');
        const metrics = document.getElementById('rfiMetrics');
        const exportBtn = document.getElementById('exportRfiBtn');

        if (!rfis.length) {
            if (body) body.innerHTML = '';
            if (noRfis) noRfis.style.display = 'block';
            if (metrics) metrics.style.display = 'none';
            if (exportBtn) exportBtn.disabled = true;
            return;
        }

        if (noRfis) noRfis.style.display = 'none';
        if (metrics) metrics.style.display = 'grid';
        if (exportBtn) exportBtn.disabled = false;

        // Metrics
        document.getElementById('rfiTotal').textContent = rfis.length;
        document.getElementById('rfiCritical').textContent = rfis.filter(r => r.severity === 'CRITICAL').length;
        document.getElementById('rfiMajor').textContent = rfis.filter(r => r.severity === 'MAJOR').length;
        document.getElementById('rfiOpen').textContent = rfis.filter(r => r.status === 'Open').length;

        // Table
        body.innerHTML = rfis.map(r => `
            <tr>
                <td class="font-mono font-semibold">RFI-${String(r.number).padStart(3, '0')}</td>
                <td><span class="badge badge-${(r.severity || 'info').toLowerCase()}">${r.severity || 'INFO'}</span></td>
                <td>${this._esc(r.subject || '')}</td>
                <td>${this._esc(r.discipline || '')}</td>
                <td class="text-xs">${this._esc(r.sheets || '')}</td>
                <td><span class="badge badge-info">${r.status || 'Open'}</span></td>
            </tr>
        `).join('');
    },

    filterRFIs() {
        if (!this._rfiData) return;
        const filter = document.getElementById('rfiSevFilter').value;
        const body = document.getElementById('rfiBody');
        const rfis = filter ? this._rfiData.filter(r => r.severity === filter) : this._rfiData;

        body.innerHTML = rfis.map(r => `
            <tr>
                <td class="font-mono font-semibold">RFI-${String(r.number).padStart(3, '0')}</td>
                <td><span class="badge badge-${(r.severity || 'info').toLowerCase()}">${r.severity || 'INFO'}</span></td>
                <td>${this._esc(r.subject || '')}</td>
                <td>${this._esc(r.discipline || '')}</td>
                <td class="text-xs">${this._esc(r.sheets || '')}</td>
                <td><span class="badge badge-info">${r.status || 'Open'}</span></td>
            </tr>
        `).join('');
    },

    async exportRFIs() {
        const pid = this.getProjectId();
        if (!pid || !this._rfiData || !this._rfiData.length) return;

        try {
            const resp = await fetch(`/api/projects/${pid}/rfis/export`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rfis: this._rfiData }),
            });
            if (!resp.ok) throw new Error('Export failed');
            const blob = await resp.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'rfi_log.xlsx';
            a.click();
            URL.revokeObjectURL(url);
            this.toast('RFI Excel downloaded', 'success');
        } catch (e) {
            this.toast(`Export failed: ${e.message}`, 'error');
        }
    },


    // ═══ SCHEDULE PAGE ═══════════════════════════════════

    loadScheduleProjectInfo() {
        const pid = this.getProjectId();
        if (!pid) return;

        this.api(`/api/projects/${pid}`).then(p => {
            const el = (id) => document.getElementById(id);
            if (el('schedBuildType')) el('schedBuildType').textContent = this._titleCase(p.building_type);
            if (el('schedSF')) el('schedSF').textContent = `${(p.square_feet || 0).toLocaleString()} SF`;
        }).catch(() => {});
    },

    async generateSchedule() {
        const pid = this.getProjectId();
        if (!pid) return;

        const btn = document.getElementById('schedBtn');
        const spinner = document.getElementById('schedSpinner');
        btn.disabled = true;
        spinner.classList.remove('hidden');

        const startDate = document.getElementById('schedStartDate').value || '2026-04-01';

        try {
            const data = await this.api(`/api/projects/${pid}/schedule`, {
                method: 'POST',
                body: { start_date: startDate },
            });

            if (data.error) {
                this.toast(`Schedule error: ${data.error}`, 'error');
                return;
            }

            this._scheduleData = data;

            document.getElementById('schedActivities').textContent = data.total_activities || 0;
            document.getElementById('schedDuration').textContent = data.project_duration_days || 0;
            document.getElementById('schedCritical').textContent = data.critical_activities || 0;
            document.getElementById('schedMilestones').textContent = data.milestones || 0;

            document.getElementById('schedResults').classList.remove('hidden');

            // Gantt chart
            if (data.gantt_data && data.gantt_data.length) {
                this._buildGanttChart(data.gantt_data);
            }

            // Critical path
            const cpContainer = document.getElementById('criticalPath');
            if (cpContainer && data.critical_path) {
                cpContainer.innerHTML = data.critical_path.map(a =>
                    `<div class="flex items-center gap-2 text-sm">
                        <span class="w-2 h-2 bg-red-500 rounded-full flex-shrink-0"></span>
                        <span class="font-mono font-semibold text-navy">${this._esc(a.id)}</span>
                        <span class="text-gray-600">${this._esc(a.name)}</span>
                        <span class="text-gray-400">(${a.duration}d)</span>
                    </div>`
                ).join('');
            }

            // WBS
            const wbsEl = document.getElementById('wbsText');
            if (wbsEl && data.wbs_text) {
                wbsEl.textContent = data.wbs_text;
            }

            this.toast(`Schedule generated: ${data.total_activities} activities, ${data.project_duration_days} days`, 'success');

        } catch (e) {
            this.toast(`Schedule failed: ${e.message}`, 'error');
        }

        btn.disabled = false;
        spinner.classList.add('hidden');
    },

    _buildGanttChart(ganttData) {
        const container = document.getElementById('ganttContainer');
        if (!container) return;

        // Build a simple horizontal bar chart as Gantt
        const canvas = document.getElementById('ganttChart');
        if (!canvas) return;
        if (this._charts.gantt) this._charts.gantt.destroy();

        // Parse dates to offsets
        const allDates = ganttData.flatMap(d => [new Date(d.start), new Date(d.end)]);
        const minDate = new Date(Math.min(...allDates));

        const daysBetween = (a, b) => Math.max(1, Math.round((b - a) / 86400000));

        const labels = ganttData.map(d => d.task);
        const starts = ganttData.map(d => daysBetween(minDate, new Date(d.start)));
        const durations = ganttData.map(d => daysBetween(new Date(d.start), new Date(d.end)));
        const colors = ganttData.map(d => d.critical ? '#DC2626' : '#1976D2');

        // Set height based on data
        canvas.parentElement.style.height = `${Math.max(400, ganttData.length * 26)}px`;

        this._charts.gantt = new Chart(canvas, {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Offset',
                        data: starts,
                        backgroundColor: 'transparent',
                        borderWidth: 0,
                        barPercentage: 0.6,
                    },
                    {
                        label: 'Duration',
                        data: durations,
                        backgroundColor: colors,
                        borderRadius: 3,
                        barPercentage: 0.6,
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                if (ctx.datasetIndex === 0) return '';
                                const d = ganttData[ctx.dataIndex];
                                return `${d.start} → ${d.end} (${d.critical ? 'Critical' : d.float + 'd float'})`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        title: { display: true, text: 'Working Days' },
                        grid: { color: '#F0F2F5' },
                    },
                    y: {
                        stacked: true,
                        grid: { display: false },
                        ticks: { font: { size: 10 } },
                    }
                }
            }
        });
    },

    downloadScheduleExcel() {
        const pid = this.getProjectId();
        if (!pid || !this._scheduleData || !this._scheduleData.excel_path) {
            this.toast('No schedule generated yet', 'error');
            return;
        }
        // Find the filename from the path
        const parts = this._scheduleData.excel_path.replace(/\\/g, '/').split('/');
        const filename = parts[parts.length - 1];
        window.open(`/api/projects/${pid}/exports/${encodeURIComponent(filename)}`, '_blank');
    },


    // ═══ EXPORTS PAGE ════════════════════════════════════

    async loadExports() {
        const pid = this.getProjectId();
        const container = document.getElementById('exportsList');
        if (!pid || !container) return;

        try {
            const data = await this.api(`/api/projects/${pid}/exports`);

            if (!data.files || !data.files.length) {
                container.innerHTML = `
                    <div class="card">
                        <div class="empty-state">
                            <div class="empty-icon">&#128230;</div>
                            <div class="empty-title">No export files found</div>
                            <div class="text-sm text-gray-500 mt-2">
                                Generate outputs first:<br>
                                <strong>RFI Log:</strong> Run Plan Review then generate RFIs<br>
                                <strong>Schedule:</strong> Generate a CPM schedule
                            </div>
                        </div>
                    </div>`;
                return;
            }

            // Group by category
            const grouped = {};
            data.files.forEach(f => {
                if (!grouped[f.category]) grouped[f.category] = [];
                grouped[f.category].push(f);
            });

            container.innerHTML = Object.entries(grouped).map(([cat, files]) => `
                <div class="card">
                    <h2 class="section-title">${this._esc(cat)}</h2>
                    ${files.map(f => `
                        <div class="file-row">
                            <div>
                                <span class="font-medium text-gray-700">${this._esc(f.filename)}</span>
                                <span class="text-gray-400 text-xs ml-2">(${f.size_kb} KB)</span>
                            </div>
                            <a href="/api/projects/${pid}/exports/${encodeURIComponent(f.filename)}"
                               class="btn-primary text-xs py-1 px-3" style="text-decoration:none;">
                                Download
                            </a>
                        </div>
                    `).join('')}
                </div>
            `).join('');

        } catch (e) {
            container.innerHTML = `<div class="alert-error">${e.message}</div>`;
        }
    },

    async generateReport() {
        const pid = this.getProjectId();
        if (!pid) return;

        try {
            await this.api(`/api/projects/${pid}/report`, { method: 'POST' });
            this.toast('Report generated', 'success');
            this.loadExports();
        } catch (e) {
            this.toast(`Report failed: ${e.message}`, 'error');
        }
    },


    // ═══ FEEDBACK PAGE ═══════════════════════════════════

    switchFeedbackTab(tab) {
        ['conflict', 'rules', 'metrics'].forEach(t => {
            const el = document.getElementById(`feedback${this._titleCase(t)}`);
            const btn = document.getElementById(`tab${this._titleCase(t)}`);
            if (el) el.classList.toggle('hidden', t !== tab);
            if (btn) btn.classList.toggle('active', t === tab);
        });
    },

    async loadFeedbackData() {
        const pid = this.getProjectId();
        if (!pid) return;

        // Load metrics
        try {
            const m = await this.api(`/api/projects/${pid}/metrics`);
            document.getElementById('metricTotal').textContent = m.total_conflicts || 0;
            document.getElementById('metricTPR').textContent = `${Math.round((m.true_positive_rate || 0) * 100)}%`;
            document.getElementById('metricFPR').textContent = `${Math.round((m.false_positive_rate || 0) * 100)}%`;
            document.getElementById('metricSevChanges').textContent = m.severity_changes || 0;

            if (m.total_conflicts > 0) {
                document.getElementById('noMetrics').style.display = 'none';
                document.getElementById('metricsDetail').innerHTML = `
                    <p><strong>Accepted:</strong> ${m.accepted}</p>
                    <p><strong>False Positives:</strong> ${m.false_positives}</p>
                    <p><strong>Notes:</strong> ${m.notes}</p>
                `;
            }
        } catch (e) { /* ignore */ }

        // Load rules
        try {
            const rules = await this.api('/api/rules/all');
            const select = document.getElementById('ruleSelect');
            if (select && rules.rules) {
                select.innerHTML = rules.rules.map(r =>
                    `<option value="${r.rule_id}">${r.rule_id} — ${this._esc(r.name)}</option>`
                ).join('');
            }
        } catch (e) { /* ignore */ }

        // Load suppressed
        try {
            const sup = await this.api(`/api/rules/suppressed/${pid}`);
            const container = document.getElementById('suppressedRulesList');
            if (container && sup.suppressed && sup.suppressed.length) {
                container.innerHTML = sup.suppressed.map(r =>
                    `<div class="flex items-center justify-between py-1">
                        <code class="text-sm bg-gray-100 px-2 py-0.5 rounded">${r}</code>
                    </div>`
                ).join('');
            }
        } catch (e) { /* ignore */ }

        // Render conflict feedback if review data exists
        if (this._reviewData && this._reviewData.conflicts) {
            this._renderFeedbackConflicts(this._reviewData.conflicts);
        }
    },

    _renderFeedbackConflicts(conflicts) {
        const container = document.getElementById('feedbackConflictList');
        if (!container || !conflicts.length) return;

        container.innerHTML = conflicts.map((c, i) => `
            <div class="conflict-card mb-3" id="fb-conflict-${i}">
                <div class="conflict-header" onclick="DABO.toggleConflict('fb-conflict-${i}')">
                    <span class="badge badge-${(c.severity || 'info').toLowerCase()}">${c.severity || 'INFO'}</span>
                    <span>${this._esc(c.rule_id || '')} — ${this._esc(c.description || '')}</span>
                    <span class="conflict-chevron">&#9654;</span>
                </div>
                <div class="conflict-body">
                    <p class="mb-3"><strong>Sheets:</strong> ${this._esc((c.sheets || []).join(', '))}</p>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                            <label class="form-label">Assessment</label>
                            <select class="form-input text-sm" id="fb-action-${i}">
                                <option value="accepted">Accept (correct finding)</option>
                                <option value="false_positive">False Positive</option>
                                <option value="severity_change">Change Severity</option>
                                <option value="note">Add Note</option>
                            </select>
                        </div>
                        <div>
                            <label class="form-label">Note</label>
                            <input type="text" class="form-input text-sm" id="fb-note-${i}" placeholder="Optional note...">
                        </div>
                    </div>
                    <button class="btn-primary text-xs mt-3" onclick="DABO.submitFeedback(${i}, '${c.conflict_id || 'C-' + i}', '${c.severity || ''}')">
                        Submit Feedback
                    </button>
                </div>
            </div>
        `).join('');
    },

    async submitFeedback(idx, conflictId, severity) {
        const pid = this.getProjectId();
        if (!pid) return;

        const action = document.getElementById(`fb-action-${idx}`).value;
        const note = document.getElementById(`fb-note-${idx}`).value;

        try {
            await this.api(`/api/projects/${pid}/feedback`, {
                method: 'POST',
                body: {
                    conflict_id: conflictId,
                    action: action,
                    original_severity: severity,
                    user_note: note,
                },
            });
            this.toast('Feedback recorded!', 'success');
        } catch (e) {
            this.toast(`Feedback failed: ${e.message}`, 'error');
        }
    },

    async suppressRule() {
        const pid = this.getProjectId();
        const ruleId = document.getElementById('ruleSelect').value;
        const scope = document.getElementById('ruleScope').value;

        if (!ruleId) return;

        try {
            await this.api('/api/rules/suppress', {
                method: 'POST',
                body: {
                    rule_id: ruleId,
                    project_id: scope === 'project' ? pid : null,
                },
            });
            this.toast(`Rule ${ruleId} suppressed`, 'success');
            this.loadFeedbackData();
        } catch (e) {
            this.toast(`Failed: ${e.message}`, 'error');
        }
    },


    // ── Helpers ──────────────────────────────────────────

    _esc(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    },

    _titleCase(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    },
};
