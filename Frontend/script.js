/**
 * RentHome — Tier 1 prototype (API-backed)
 */
const PLACEHOLDER_IMG =
    'data:image/svg+xml,' +
    encodeURIComponent(
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"><rect fill="%23e2e8f0" width="100%" height="100%"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%2364748b" font-family="sans-serif" font-size="24">No image</text></svg>'
    );

const state = {
    currentUser: null,
    darkMode: localStorage.getItem('darkMode') === 'true',
    propertiesList: [],
    favoriteIds: new Set(),
    uploadedImages: [],
    currentPropertyDetail: null,
    chatReceiverId: null,
    chatPropertyId: null,
    conversations: [],
};

function initials(name) {
    if (!name) return '?';
    const p = name.trim().split(/\s+/);
    return (p[0][0] + (p[1] ? p[1][0] : '')).toUpperCase();
}

let currentFilters = {
    priceMin: 0,
    priceMax: 5000,
    bedrooms: null,
    types: [],
    amenities: [],
};

function showToast(message, type) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast ' + (type || 'info');
    const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
    toast.innerHTML = '<span style="font-weight:bold">' + icon + '</span><span>' + message + '</span>';
    container.appendChild(toast);
    setTimeout(function () {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(function () {
            toast.remove();
        }, 300);
    }, 3200);
}

function initDarkMode() {
    if (state.darkMode) document.documentElement.setAttribute('data-theme', 'dark');
}

function toggleDarkMode() {
    state.darkMode = !state.darkMode;
    if (state.darkMode) document.documentElement.setAttribute('data-theme', 'dark');
    else document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('darkMode', state.darkMode);
    showToast(state.darkMode ? 'Dark mode enabled' : 'Light mode enabled', 'info');
}

async function refreshSession() {
    if (!RentalAPI.getToken()) {
        state.currentUser = null;
        updateAuthUi();
        return;
    }
    try {
        state.currentUser = await RentalAPI.auth.me();
    } catch (e) {
        RentalAPI.clearToken();
        state.currentUser = null;
    }
    updateAuthUi();
    await refreshFavoritesSet();
}

function updateNavForRole() {
    const seekerDesktop = document.getElementById('navSeekerLink');
    const ownerDesktop = document.getElementById('navOwnerLink');
    const seekerMobile = document.getElementById('mobileNavSeekerLink');
    const ownerMobile = document.getElementById('mobileNavOwnerLink');
    function show(el, on) {
        if (!el) return;
        el.style.display = on ? '' : 'none';
    }
    if (!state.currentUser) {
        show(seekerDesktop, false);
        show(ownerDesktop, false);
        show(seekerMobile, false);
        show(ownerMobile, false);
        return;
    }
    const r = state.currentUser.role;
    if (r === 'admin') {
        show(seekerDesktop, true);
        show(ownerDesktop, true);
        show(seekerMobile, true);
        show(ownerMobile, true);
    } else if (r === 'seeker') {
        show(seekerDesktop, true);
        show(ownerDesktop, false);
        show(seekerMobile, true);
        show(ownerMobile, false);
    } else if (r === 'owner') {
        show(seekerDesktop, false);
        show(ownerDesktop, true);
        show(seekerMobile, false);
        show(ownerMobile, true);
    } else {
        show(seekerDesktop, false);
        show(ownerDesktop, false);
        show(seekerMobile, false);
        show(ownerMobile, false);
    }
}

function updateAuthUi() {
    const guest = document.getElementById('guestNav');
    const userNav = document.getElementById('userNav');
    const nameEl = document.getElementById('userNameDisplay');
    const adminLink = document.getElementById('navAdminLink');
    if (state.currentUser) {
        if (guest) guest.style.display = 'none';
        if (userNav) userNav.style.display = 'flex';
        if (nameEl) nameEl.textContent = state.currentUser.name;
        if (adminLink) adminLink.style.display = state.currentUser.role === 'admin' ? 'inline' : 'none';
    } else {
        if (guest) guest.style.display = 'flex';
        if (userNav) userNav.style.display = 'none';
        if (adminLink) adminLink.style.display = 'none';
    }
    if (state.currentUser) {
        const oa = document.getElementById('ownerAvatar');
        const on = document.getElementById('ownerName');
        const sa = document.getElementById('seekerAvatar');
        const sn = document.getElementById('seekerName');
        if (oa) oa.textContent = initials(state.currentUser.name);
        if (on) on.textContent = state.currentUser.name;
        if (sa) sa.textContent = initials(state.currentUser.name);
        if (sn) sn.textContent = state.currentUser.name;
    }
    updateNavForRole();
}

async function refreshFavoritesSet() {
    state.favoriteIds = new Set();
    if (!state.currentUser) {
        updateFavCount();
        return;
    }
    try {
        const list = await RentalAPI.favorites.list();
        list.forEach(function (p) {
            state.favoriteIds.add(p.id);
        });
    } catch (_) {}
    updateFavCount();
}

function updateFavCount() {
    const badge = document.getElementById('favCount');
    if (badge) badge.textContent = state.favoriteIds.size;
    const fc = document.getElementById('favoritesCount');
    if (fc) fc.textContent = '(' + state.favoriteIds.size + ')';
}

function propImage(p) {
    if (p.images && p.images.length) return p.images[0];
    return PLACEHOLDER_IMG;
}

function navigateTo(page) {
    if (page === 'admin-panel' && (!state.currentUser || state.currentUser.role !== 'admin')) {
        showToast('Admin access only. Sign in as admin@local.test', 'error');
        return;
    }
    if (page === 'owner-dashboard' && state.currentUser && state.currentUser.role === 'seeker') {
        showToast('Owner portal is only for property owners.', 'info');
        return;
    }
    if (page === 'seeker-dashboard' && state.currentUser && state.currentUser.role === 'owner') {
        showToast('My Rentals is for seekers. Use Owner Portal to manage listings.', 'info');
        return;
    }
    document.querySelectorAll('.page').forEach(function (p) {
        p.classList.remove('active');
    });
    const target = document.getElementById(page);
    if (target) target.classList.add('active');

    document.querySelectorAll('.nav-link').forEach(function (link) {
        link.classList.remove('active');
        var oc = link.getAttribute('onclick') || '';
        if (oc.indexOf("'" + page + "'") !== -1) link.classList.add('active');
    });

    var mm = document.getElementById('mobileMenu');
    if (mm) mm.classList.remove('active');
    window.scrollTo(0, 0);

    if (page === 'home') loadHome();
    else if (page === 'favorites') renderFavoritesPage();
    else if (page === 'owner-dashboard') {
        loadOwnerDashboard();
        initCharts();
    } else if (page === 'seeker-dashboard') loadSeekerBookings();
    else if (page === 'admin-panel') loadAdminListings();
}

function toggleMobileMenu() {
    var m = document.getElementById('mobileMenu');
    if (m) m.classList.toggle('active');
}

function applyLocalFilters(list) {
    return list.filter(function (p) {
        if (currentFilters.types.length && currentFilters.types.indexOf(p.property_type) === -1) return false;
        if (currentFilters.amenities.length) {
            var am = p.amenities || [];
            for (var i = 0; i < currentFilters.amenities.length; i++) {
                if (am.indexOf(currentFilters.amenities[i]) === -1) return false;
            }
        }
        return true;
    });
}

async function loadHome() {
    var skeleton = document.getElementById('skeletonGrid');
    var grid = document.getElementById('propertyGrid');
    if (skeleton) skeleton.style.display = 'grid';
    if (grid) grid.style.display = 'none';
    try {
        var q = buildFilterQuery();
        var raw = await RentalAPI.properties.list(q);
        state.propertiesList = applyLocalFilters(raw);
    } catch (e) {
        showToast(e.message || 'Failed to load properties', 'error');
        state.propertiesList = [];
    }
    if (skeleton) skeleton.style.display = 'none';
    if (grid) grid.style.display = 'grid';
    renderProperties(state.propertiesList);
}

function buildFilterQuery() {
    var loc = (document.getElementById('searchLocation') && document.getElementById('searchLocation').value) || '';
    var sortEl = document.getElementById('sortProperties');
    var sort = sortEl ? sortEl.value : 'newest';
    var q = { location: loc.trim() || undefined, sort: sort };
    var pm = document.getElementById('priceMin');
    var px = document.getElementById('priceMax');
    if (pm && px) {
        q.price_min = parseInt(pm.value, 10) || 0;
        q.price_max = parseInt(px.value, 10) || 5000;
    }
    var spr = document.getElementById('searchPrice');
    if (spr && spr.value) {
        if (spr.value === '3000+') {
            q.price_min = 3000;
            q.price_max = 10000000;
        } else {
            var parts = spr.value.split('-');
            q.price_min = parseInt(parts[0], 10) || 0;
            q.price_max = parseInt(parts[1], 10) || 5000;
        }
    }
    var st = document.getElementById('searchType');
    if (st && st.value) q.property_type = st.value;
    if (currentFilters.bedrooms && currentFilters.bedrooms !== 'any') q.bedrooms = currentFilters.bedrooms;
    return q;
}

function filterProperties() {
    loadHome();
}

function sortProperties() {
    loadHome();
}

function resetFilters() {
    var sl = document.getElementById('searchLocation');
    var sp = document.getElementById('searchPrice');
    var st = document.getElementById('searchType');
    var pm = document.getElementById('priceMin');
    var px = document.getElementById('priceMax');
    if (sl) sl.value = '';
    if (sp) sp.value = '';
    if (st) st.value = '';
    if (pm) pm.value = 0;
    if (px) px.value = 5000;
    var d1 = document.getElementById('priceMinDisplay');
    var d2 = document.getElementById('priceMaxDisplay');
    if (d1) d1.textContent = '0';
    if (d2) d2.textContent = '5,000';
    document.querySelectorAll('.bedroom-btn').forEach(function (b) {
        b.classList.remove('active');
    });
    document.querySelectorAll('.type-filter, .amenity-filter').forEach(function (cb) {
        cb.checked = false;
    });
    currentFilters = {
        priceMin: 0,
        priceMax: 5000,
        bedrooms: null,
        types: [],
        amenities: [],
    };
    loadHome();
    showToast('Filters reset', 'info');
}

function renderProperties(list) {
    var grid = document.getElementById('propertyGrid');
    var count = document.getElementById('propertyCount');
    var noResults = document.getElementById('noResults');
    if (!grid) return;
    if (count) count.textContent = '(' + list.length + ')';
    if (!list.length) {
        grid.style.display = 'none';
        if (noResults) noResults.style.display = 'block';
        return;
    }
    grid.style.display = 'grid';
    if (noResults) noResults.style.display = 'none';
    grid.innerHTML = list.map(createPropertyCard).join('');
}

function createPropertyCard(p) {
    var isFav = state.favoriteIds.has(p.id);
    var feat = p.listing_status === 'approved';
    return (
        '<div class="property-card" onclick="showPropertyDetails(\'' +
        p.id +
        "')\">" +
        '<div class="property-image">' +
        '<img src="' +
        propImage(p) +
        '" alt="" loading="lazy">' +
        '<button type="button" class="favorite-btn ' +
        (isFav ? 'active' : '') +
        '" onclick="event.stopPropagation();toggleFavorite(\'' +
        p.id +
        "')\">" +
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="' +
        (isFav ? 'currentColor' : 'none') +
        '" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>' +
        '</button>' +
        (feat ? '<span class="property-badge">Listed</span>' : '') +
        '</div>' +
        '<div class="property-info">' +
        '<div class="property-header">' +
        '<h3 class="property-title">' +
        escapeHtml(p.title) +
        '</h3>' +
        '<span class="property-price">$' +
        Number(p.price).toLocaleString() +
        '/mo</span></div>' +
        '<div class="property-location"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>' +
        escapeHtml(p.location) +
        '</div>' +
        '<div class="property-features">' +
        '<span class="property-feature"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg> ' +
        p.bedrooms +
        ' Beds</span>' +
        '<span class="property-feature"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12a8 8 0 0 1 8-8 8 8 0 0 1 8 8 8 8 0 0 1-8 8 8 8 0 0 1-8-8z"/></svg> ' +
        p.bathrooms +
        ' Baths</span>' +
        '</div></div></div>'
    );
}

function escapeHtml(s) {
    if (!s) return '';
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

async function toggleFavorite(propertyId) {
    if (!state.currentUser) {
        showToast('Sign in to save favorites', 'info');
        showAuthModal('login');
        return;
    }
    try {
        if (state.favoriteIds.has(propertyId)) {
            await RentalAPI.favorites.remove(propertyId);
            state.favoriteIds.delete(propertyId);
            showToast('Removed from favorites', 'info');
        } else {
            await RentalAPI.favorites.add(propertyId);
            state.favoriteIds.add(propertyId);
            showToast('Saved to favorites', 'success');
        }
    } catch (e) {
        showToast(e.message || 'Favorite failed', 'error');
    }
    updateFavCount();
    renderProperties(state.propertiesList);
    var fg = document.getElementById('favoritesGrid');
    if (fg && document.getElementById('favorites') && document.getElementById('favorites').classList.contains('active')) {
        renderFavoritesPage();
    }
}

async function showPropertyDetails(propertyId) {
    var container = document.getElementById('propertyDetailsContainer');
    if (!container) return;
    container.innerHTML = '<p style="padding:2rem">Loading…</p>';
    navigateTo('property-details');
    try {
        var p = await RentalAPI.properties.get(propertyId);
        state.currentPropertyDetail = p;
        var imgs = p.images && p.images.length ? p.images : [PLACEHOLDER_IMG];
        var rest = imgs.slice(1, 3);
        container.innerHTML =
            '<div class="property-gallery">' +
            '<div class="gallery-main"><img src="' +
            imgs[0] +
            '" alt=""></div>' +
            rest
                .map(function (img) {
                    return '<div class="gallery-thumb"><img src="' + img + '" alt=""></div>';
                })
                .join('') +
            '</div>' +
            '<div class="property-details-grid">' +
            '<div class="property-details-main">' +
            '<h1>' +
            escapeHtml(p.title) +
            '</h1>' +
            '<div class="property-details-location"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg> ' +
            escapeHtml(p.location) +
            '</div>' +
            '<div class="property-highlights">' +
            '<div class="highlight-item"><div class="highlight-info"><span class="highlight-value">' +
            p.bedrooms +
            '</span><span class="highlight-label">Bedrooms</span></div></div>' +
            '<div class="highlight-item"><div class="highlight-info"><span class="highlight-value">' +
            p.bathrooms +
            '</span><span class="highlight-label">Bathrooms</span></div></div>' +
            '</div>' +
            '<h3 class="section-title">About</h3>' +
            '<p class="property-description">' +
            escapeHtml(p.description || '') +
            '</p>' +
            '</div>' +
            '<div class="property-sidebar">' +
            '<div class="contact-card">' +
            '<div class="contact-price">$' +
            Number(p.price).toLocaleString() +
            '/mo</div>' +
            '<p style="font-size:0.875rem;color:var(--text-secondary);margin-bottom:1rem">Status: ' +
            escapeHtml(p.listing_status) +
            '</p>' +
            '<div class="contact-buttons">' +
            '<button type="button" class="btn btn-primary" onclick="openChatFromProperty()">Message owner</button>' +
            '<button type="button" class="btn btn-outline" onclick="openBookingForCurrentProperty()">Request visit</button>' +
            '</div></div></div></div>';
    } catch (e) {
        container.innerHTML = '<p style="padding:2rem">Could not load property.</p>';
        showToast(e.message || 'Error', 'error');
    }
}

function openChatFromProperty() {
    var p = state.currentPropertyDetail;
    if (!p || !state.currentUser) {
        showAuthModal('login');
        return;
    }
    if (state.currentUser.id === p.owner_id) {
        showToast('This is your listing', 'info');
        return;
    }
    state.chatReceiverId = p.owner_id;
    state.chatPropertyId = p.id;
    var chatName = document.getElementById('chatUserName');
    var chatAvatar = document.getElementById('chatAvatar');
    if (chatName) chatName.textContent = 'Property owner';
    if (chatAvatar) chatAvatar.textContent = 'OW';
    var modal = document.getElementById('chatModal');
    if (modal) modal.classList.add('active');
    loadChatMessages();
}

function openBookingForCurrentProperty() {
    var p = state.currentPropertyDetail;
    if (!p || !state.currentUser) {
        showAuthModal('login');
        return;
    }
    if (state.currentUser.role !== 'seeker' && state.currentUser.role !== 'admin') {
        showToast('Only seekers can request visits', 'info');
        return;
    }
    if (p.listing_status !== 'approved') {
        showToast('This listing is not bookable yet', 'info');
        return;
    }
    var hid = document.getElementById('bookingPropertyId');
    if (hid) hid.value = p.id;
    var modal = document.getElementById('bookingModal');
    if (modal) modal.classList.add('active');
}

async function loadChatMessages() {
    if (!state.chatReceiverId) return;
    var body = document.getElementById('chatBody');
    if (!body) return;
    body.innerHTML = '';
    try {
        var msgs = await RentalAPI.chat.messages(state.chatReceiverId);
        msgs.forEach(function (m) {
            var mine = m.sender_id === state.currentUser.id;
            var t = m.created_at ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
            body.insertAdjacentHTML(
                'beforeend',
                '<div class="chat-message ' +
                    (mine ? 'sent' : 'received') +
                    '"><p>' +
                    escapeHtml(m.body) +
                    '</p><span class="message-time">' +
                    t +
                    '</span></div>'
            );
        });
        body.scrollTop = body.scrollHeight;
    } catch (e) {
        showToast(e.message || 'Failed to load messages', 'error');
    }
}

async function sendMessage() {
    var input = document.getElementById('chatInput');
    if (!input || !state.chatReceiverId || !state.currentUser) return;
    var message = input.value.trim();
    if (!message) return;
    try {
        await RentalAPI.chat.send({
            receiver_id: state.chatReceiverId,
            body: message,
            property_id: state.chatPropertyId || null,
        });
        input.value = '';
        await loadChatMessages();
    } catch (e) {
        showToast(e.message || 'Send failed', 'error');
    }
}

function handleChatKeypress(e) {
    if (e.key === 'Enter') sendMessage();
}

function closeChat() {
    var modal = document.getElementById('chatModal');
    if (modal) modal.classList.remove('active');
    state.chatReceiverId = null;
    state.chatPropertyId = null;
}

function closeBookingModal() {
    var modal = document.getElementById('bookingModal');
    if (modal) modal.classList.remove('active');
}

async function submitBooking(e) {
    e.preventDefault();
    var pid = document.getElementById('bookingPropertyId');
    var d = document.getElementById('bookingDate');
    var t = document.getElementById('bookingTime');
    var n = document.getElementById('bookingNotes');
    if (!pid || !d || !t) return;
    try {
        await RentalAPI.bookings.create({
            property_id: pid.value,
            visit_date: d.value,
            visit_time: t.value,
            notes: (n && n.value) || '',
        });
        showToast('Visit request sent', 'success');
        closeBookingModal();
    } catch (err) {
        showToast(err.message || 'Booking failed', 'error');
    }
}

async function renderFavoritesPage() {
    var grid = document.getElementById('favoritesGrid');
    var empty = document.getElementById('emptyFavorites');
    if (!grid) return;
    if (!state.currentUser) {
        grid.innerHTML = '';
        if (empty) empty.style.display = 'block';
        return;
    }
    try {
        var list = await RentalAPI.favorites.list();
        if (!list.length) {
            grid.innerHTML = '';
            if (empty) empty.style.display = 'block';
            return;
        }
        if (empty) empty.style.display = 'none';
        grid.innerHTML = list.map(createPropertyCard).join('');
    } catch (e) {
        showToast(e.message || 'Failed to load favorites', 'error');
    }
}

function showAuthModal(type) {
    var modal = document.getElementById('authModal');
    if (modal) modal.classList.add('active');
    document.querySelectorAll('.auth-tab').forEach(function (tab) {
        tab.classList.toggle('active', tab.dataset.tab === type);
    });
    document.querySelectorAll('.auth-form').forEach(function (form) {
        form.classList.remove('active');
    });
    var f = document.getElementById(type === 'login' ? 'loginForm' : 'signupForm');
    if (f) f.classList.add('active');
}

function closeAuthModal() {
    var modal = document.getElementById('authModal');
    if (modal) modal.classList.remove('active');
}

async function handleLogin(e) {
    e.preventDefault();
    var em = document.getElementById('loginEmail');
    var pw = document.getElementById('loginPassword');
    try {
        var res = await RentalAPI.auth.login({ email: em.value.trim(), password: pw.value });
        RentalAPI.setToken(res.access_token);
        await refreshSession();
        showToast('Welcome back', 'success');
        closeAuthModal();
        loadHome();
    } catch (err) {
        showToast(err.message || 'Login failed', 'error');
    }
}

async function handleSignup(e) {
    e.preventDefault();
    var name = document.getElementById('signupName').value.trim();
    var email = document.getElementById('signupEmail').value.trim();
    var password = document.getElementById('signupPassword').value;
    var role = document.querySelector('input[name="role"]:checked');
    try {
        var res = await RentalAPI.auth.register({
            name: name,
            email: email,
            password: password,
            role: role ? role.value : 'seeker',
        });
        RentalAPI.setToken(res.access_token);
        await refreshSession();
        showToast('Account created', 'success');
        closeAuthModal();
        loadHome();
    } catch (err) {
        showToast(err.message || 'Sign up failed', 'error');
    }
}

function logout() {
    RentalAPI.clearToken();
    state.currentUser = null;
    updateAuthUi();
    state.favoriteIds = new Set();
    updateFavCount();
    showToast('Signed out', 'info');
    navigateTo('home');
}

function showOwnerSection(section) {
    document.querySelectorAll('#owner-dashboard .dashboard-section').forEach(function (s) {
        s.classList.remove('active');
    });
    var el = document.getElementById('section-' + section);
    if (el) el.classList.add('active');
    document.querySelectorAll('#owner-dashboard .sidebar-nav-item').forEach(function (btn) {
        btn.classList.toggle('active', btn.dataset.section === section);
    });
    if (section === 'bookings') loadOwnerBookings();
    if (section === 'messages') loadOwnerConversations();
}

function showSeekerSection() {}

async function loadOwnerDashboard() {
    await loadOwnerProperties();
}

async function loadOwnerProperties() {
    var grid = document.getElementById('ownerPropertiesGrid');
    if (!grid) return;
    if (!state.currentUser || (state.currentUser.role !== 'owner' && state.currentUser.role !== 'admin')) {
        grid.innerHTML = '<p>Sign in as a property owner to manage listings.</p>';
        return;
    }
    try {
        var list = await RentalAPI.properties.mine();
        grid.innerHTML = list
            .map(function (p) {
                return (
                    '<div class="owner-property-card">' +
                    '<div class="property-image"><img src="' +
                    propImage(p) +
                    '" alt=""><span class="property-status ' +
                    (p.listing_status === 'approved' ? 'active' : 'pending') +
                    '">' +
                    escapeHtml(p.listing_status) +
                    '</span></div>' +
                    '<div class="property-info"><div class="property-header"><h3 class="property-title">' +
                    escapeHtml(p.title) +
                    '</h3><span class="property-price">$' +
                    Number(p.price).toLocaleString() +
                    '/mo</span></div>' +
                    '<div class="property-location">' +
                    escapeHtml(p.location) +
                    '</div></div>' +
                    '<div class="owner-property-actions">' +
                    '<button type="button" class="btn btn-ghost" onclick="startEditProperty(\'' +
                    p.id +
                    "')\">Edit</button>" +
                    '<button type="button" class="btn btn-danger" onclick="deleteOwnerProperty(\'' +
                    p.id +
                    "')\">Delete</button>" +
                    '</div></div>'
                );
            })
            .join('');
    } catch (e) {
        grid.innerHTML = '<p>Could not load properties.</p>';
        showToast(e.message || 'Error', 'error');
    }
}

function resetPropertyForm() {
    var form = document.getElementById('addPropertyForm');
    if (form) form.reset();
    var eid = document.getElementById('editPropertyId');
    if (eid) eid.value = '';
    var title = document.getElementById('propertyFormTitle');
    if (title) title.textContent = 'Add New Property';
    state.uploadedImages = [];
    var ipg = document.getElementById('imagePreviewGrid');
    if (ipg) ipg.innerHTML = '';
}

async function startEditProperty(id) {
    try {
        var p = await RentalAPI.properties.get(id);
        var eid = document.getElementById('editPropertyId');
        if (eid) eid.value = p.id;
        var title = document.getElementById('propertyFormTitle');
        if (title) title.textContent = 'Edit Property';
        document.getElementById('propTitle').value = p.title;
        document.getElementById('propPrice').value = p.price;
        document.getElementById('propLocation').value = p.location;
        document.getElementById('propType').value = p.property_type;
        document.getElementById('propBedrooms').value = String(Math.min(p.bedrooms, 5));
        document.getElementById('propBathrooms').value = String(Math.min(p.bathrooms, 4));
        document.getElementById('propDescription').value = p.description || '';
        state.uploadedImages = p.images || [];
        document.querySelectorAll('.amenity-checkbox input').forEach(function (cb) {
            cb.checked = (p.amenities || []).indexOf(cb.value) !== -1;
        });
        renderImagePreviews();
        showOwnerSection('add-property');
    } catch (e) {
        showToast(e.message || 'Error', 'error');
    }
}

async function deleteOwnerProperty(id) {
    if (!confirm('Delete this property?')) return;
    try {
        await RentalAPI.properties.remove(id);
        showToast('Deleted', 'info');
        await loadOwnerProperties();
        loadHome();
    } catch (e) {
        showToast(e.message || 'Delete failed', 'error');
    }
}

async function handleAddProperty(e) {
    e.preventDefault();
    var amenities = Array.from(document.querySelectorAll('.amenity-checkbox input:checked')).map(function (x) {
        return x.value;
    });
    var body = {
        title: document.getElementById('propTitle').value.trim(),
        price: parseFloat(document.getElementById('propPrice').value),
        location: document.getElementById('propLocation').value.trim(),
        property_type: document.getElementById('propType').value,
        bedrooms: parseInt(document.getElementById('propBedrooms').value, 10) || 0,
        bathrooms: parseInt(document.getElementById('propBathrooms').value, 10) || 0,
        description: (document.getElementById('propDescription') && document.getElementById('propDescription').value) || '',
        amenities: amenities,
        images: state.uploadedImages.length ? state.uploadedImages : [],
    };
    var eid = document.getElementById('editPropertyId');
    try {
        if (eid && eid.value) {
            await RentalAPI.properties.update(eid.value, body);
            showToast('Property updated', 'success');
        } else {
            await RentalAPI.properties.create(body);
            showToast('Property submitted (pending admin approval)', 'success');
        }
        resetPropertyForm();
        showOwnerSection('my-properties');
        await loadOwnerProperties();
        loadHome();
    } catch (err) {
        showToast(err.message || 'Save failed', 'error');
    }
}

function handleImageUpload(ev) {
    var files = ev.target.files;
    if (!files) return;
    Array.from(files).forEach(function (file) {
        var reader = new FileReader();
        reader.onload = function (e) {
            state.uploadedImages.push(e.target.result);
            renderImagePreviews();
        };
        reader.readAsDataURL(file);
    });
}

function renderImagePreviews() {
    var previewGrid = document.getElementById('imagePreviewGrid');
    if (!previewGrid) return;
    previewGrid.innerHTML = state.uploadedImages
        .map(function (img, index) {
            return (
                '<div class="image-preview"><img src="' +
                img +
                '" alt=""><button type="button" class="remove-image" onclick="removeImage(' +
                index +
                ')">×</button></div>'
            );
        })
        .join('');
}

function removeImage(index) {
    state.uploadedImages.splice(index, 1);
    renderImagePreviews();
}

async function loadOwnerBookings() {
    var tbody = document.getElementById('ownerBookingsBody');
    if (!tbody || !state.currentUser) return;
    try {
        var rows = await RentalAPI.bookings.list();
        tbody.innerHTML = rows
            .map(function (b) {
                return (
                    '<tr><td>' +
                    escapeHtml(b.property_title || b.property_id) +
                    '</td><td>' +
                    escapeHtml(b.seeker_name || b.seeker_id) +
                    '</td><td>' +
                    escapeHtml(String(b.visit_date)) +
                    '</td><td>' +
                    escapeHtml(b.visit_time) +
                    '</td><td><span class="status-badge ' +
                    (b.status === 'approved' ? 'active' : b.status === 'rejected' ? 'pending' : 'pending') +
                    '">' +
                    escapeHtml(b.status) +
                    '</span></td><td>' +
                    (b.status === 'pending'
                        ? '<button type="button" class="btn btn-sm btn-success" onclick="approveBooking(\'' +
                          b.id +
                          "')\">Approve</button> <button type=\"button\" class=\"btn btn-sm btn-danger\" onclick=\"rejectBooking('" +
                          b.id +
                          "')\">Reject</button>"
                        : '—') +
                    '</td></tr>'
                );
            })
            .join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="6">Could not load bookings.</td></tr>';
    }
}

async function approveBooking(id) {
    try {
        await RentalAPI.bookings.approve(id);
        showToast('Approved', 'success');
        loadOwnerBookings();
    } catch (e) {
        showToast(e.message || 'Error', 'error');
    }
}

async function rejectBooking(id) {
    try {
        await RentalAPI.bookings.reject(id);
        showToast('Rejected', 'info');
        loadOwnerBookings();
    } catch (e) {
        showToast(e.message || 'Error', 'error');
    }
}

async function loadSeekerBookings() {
    var tbody = document.getElementById('seekerBookingsBody');
    if (!tbody) return;
    if (!state.currentUser) {
        tbody.innerHTML = '<tr><td colspan="4">Sign in to see your requests.</td></tr>';
        return;
    }
    try {
        var rows = await RentalAPI.bookings.list();
        tbody.innerHTML = rows
            .map(function (b) {
                return (
                    '<tr><td>' +
                    escapeHtml(b.property_title || '') +
                    '</td><td>' +
                    escapeHtml(String(b.visit_date)) +
                    '</td><td>' +
                    escapeHtml(b.visit_time) +
                    '</td><td><span class="status-badge pending">' +
                    escapeHtml(b.status) +
                    '</span></td></tr>'
                );
            })
            .join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="4">Could not load.</td></tr>';
    }
}

async function loadOwnerConversations() {
    var list = document.getElementById('ownerChatList');
    if (!list) return;
    try {
        var convos = await RentalAPI.chat.conversations();
        state.conversations = convos;
        if (!convos.length) {
            list.innerHTML = '<p style="padding:1rem;color:var(--text-secondary)">No conversations yet.</p>';
            return;
        }
        list.innerHTML = convos
            .map(function (c) {
                return (
                    '<div class="chat-list-item" onclick="openChatWith(\'' +
                    c.user_id +
                    '\')">' +
                    '<div class="chat-avatar">' +
                    initials(c.name) +
                    '</div>' +
                    '<div class="chat-info"><h4>' +
                    escapeHtml(c.name) +
                    '</h4><p>' +
                    escapeHtml(c.last_message || '') +
                    '</p></div></div>'
                );
            })
            .join('');
    } catch (e) {
        list.innerHTML = '<p>Could not load conversations.</p>';
    }
}

function openChatWith(userId) {
    var c = (state.conversations || []).find(function (x) {
        return x.user_id === userId;
    });
    var name = c ? c.name : 'User';
    state.chatReceiverId = userId;
    state.chatPropertyId = null;
    var chatName = document.getElementById('chatUserName');
    var chatAvatar = document.getElementById('chatAvatar');
    if (chatName) chatName.textContent = name;
    if (chatAvatar) chatAvatar.textContent = initials(name);
    var modal = document.getElementById('chatModal');
    if (modal) modal.classList.add('active');
    loadChatMessages();
}

function showAdminSection(section) {
    document.querySelectorAll('#admin-panel .dashboard-section').forEach(function (s) {
        s.classList.remove('active');
    });
    var el = document.getElementById('admin-section-' + section);
    if (el) el.classList.add('active');
    document.querySelectorAll('#admin-panel .sidebar-nav-item').forEach(function (btn) {
        btn.classList.toggle('active', btn.dataset.adminSection === section);
    });
    if (section === 'listings') loadAdminListings();
}

async function loadAdminListings() {
    var tbody = document.getElementById('adminListingsTable');
    if (!tbody) return;
    try {
        var props = await RentalAPI.admin.properties();
        tbody.innerHTML = props
            .map(function (p) {
                return (
                    '<tr><td><div class="user-cell"><img src="' +
                    propImage(p) +
                    '" alt="" style="width:48px;height:48px;object-fit:cover;border-radius:8px"><div><div class="user-name">' +
                    escapeHtml(p.title) +
                    '</div><div class="user-email">' +
                    escapeHtml(p.location) +
                    '</div></div></div></td>' +
                    '<td>' +
                    escapeHtml(p.owner_id) +
                    '</td>' +
                    '<td>$' +
                    Number(p.price).toLocaleString() +
                    '</td>' +
                    '<td>' +
                    escapeHtml(p.location) +
                    '</td>' +
                    '<td><span class="status-badge ' +
                    (p.listing_status === 'approved' ? 'active' : 'pending') +
                    '">' +
                    escapeHtml(p.listing_status) +
                    '</span></td>' +
                    '<td>' +
                    (p.listing_status === 'pending'
                        ? '<button type="button" class="btn btn-sm btn-success" onclick="adminApprove(\'' +
                          p.id +
                          "')\">Approve</button> <button type=\"button\" class=\"btn btn-sm btn-danger\" onclick=\"adminReject('" +
                          p.id +
                          "')\">Reject</button>"
                        : '—') +
                    '</td></tr>'
                );
            })
            .join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="6">Could not load (admin only).</td></tr>';
        showToast(e.message || 'Error', 'error');
    }
}

async function adminApprove(id) {
    try {
        await RentalAPI.admin.approve(id);
        showToast('Listing approved', 'success');
        loadAdminListings();
        loadHome();
    } catch (e) {
        showToast(e.message || 'Error', 'error');
    }
}

async function adminReject(id) {
    try {
        await RentalAPI.admin.reject(id);
        showToast('Listing rejected', 'info');
        loadAdminListings();
    } catch (e) {
        showToast(e.message || 'Error', 'error');
    }
}

function initCharts() {}

document.addEventListener('DOMContentLoaded', function () {
    initDarkMode();
    refreshSession().then(function () {
        loadHome();
    });

    var priceMin = document.getElementById('priceMin');
    var priceMax = document.getElementById('priceMax');
    if (priceMin) {
        priceMin.addEventListener('input', function (e) {
            currentFilters.priceMin = parseInt(e.target.value, 10);
            var display = document.getElementById('priceMinDisplay');
            if (display) display.textContent = currentFilters.priceMin.toLocaleString();
            filterProperties();
        });
    }
    if (priceMax) {
        priceMax.addEventListener('input', function (e) {
            currentFilters.priceMax = parseInt(e.target.value, 10);
            var display = document.getElementById('priceMaxDisplay');
            if (display) display.textContent = currentFilters.priceMax.toLocaleString();
            filterProperties();
        });
    }

    document.querySelectorAll('.bedroom-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.bedroom-btn').forEach(function (b) {
                b.classList.remove('active');
            });
            btn.classList.add('active');
            currentFilters.bedrooms = btn.dataset.value;
            filterProperties();
        });
    });

    document.querySelectorAll('.type-filter').forEach(function (cb) {
        cb.addEventListener('change', function () {
            currentFilters.types = Array.from(document.querySelectorAll('.type-filter:checked')).map(function (x) {
                return x.value;
            });
            filterProperties();
        });
    });

    document.querySelectorAll('.amenity-filter').forEach(function (cb) {
        cb.addEventListener('change', function () {
            currentFilters.amenities = Array.from(document.querySelectorAll('.amenity-filter:checked')).map(function (x) {
                return x.value;
            });
            filterProperties();
        });
    });

    document.querySelectorAll('.auth-tab').forEach(function (tab) {
        tab.addEventListener('click', function () {
            document.querySelectorAll('.auth-tab').forEach(function (t) {
                t.classList.remove('active');
            });
            tab.classList.add('active');
            document.querySelectorAll('.auth-form').forEach(function (f) {
                f.classList.remove('active');
            });
            document.getElementById(tab.dataset.tab + 'Form').classList.add('active');
        });
    });

    setTimeout(function () {
        var skeleton = document.getElementById('skeletonGrid');
        var grid = document.getElementById('propertyGrid');
        if (skeleton) skeleton.style.display = 'none';
        if (grid) grid.style.display = 'grid';
    }, 400);
});

window.onclick = function (event) {
    if (event.target.classList && event.target.classList.contains('modal-overlay')) {
        event.target.classList.remove('active');
    }
    if (event.target.classList && event.target.classList.contains('chat-modal')) {
        event.target.classList.remove('active');
    }
};
