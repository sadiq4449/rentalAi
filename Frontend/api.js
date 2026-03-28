(function () {
    const API_BASE = 'http://127.0.0.1:8000';
    const TOKEN_KEY = 'rental_token';

    function getToken() {
        return localStorage.getItem(TOKEN_KEY);
    }

    function setToken(t) {
        if (t) localStorage.setItem(TOKEN_KEY, t);
        else localStorage.removeItem(TOKEN_KEY);
    }

    function clearToken() {
        localStorage.removeItem(TOKEN_KEY);
    }

    function detailMessage(data) {
        const d = data && data.detail;
        if (typeof d === 'string') return d;
        if (Array.isArray(d)) return d.map((x) => x.msg || JSON.stringify(x)).join('; ');
        if (d && typeof d === 'object') return JSON.stringify(d);
        return 'Request failed';
    }

    async function api(path, options) {
        const opts = options || {};
        const headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
        const token = getToken();
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const res = await fetch(API_BASE + path, Object.assign({}, opts, { headers: headers }));
        const text = await res.text();
        let data = {};
        if (text) {
            try {
                data = JSON.parse(text);
            } catch (_) {
                data = { detail: text };
            }
        }
        if (!res.ok) throw new Error(detailMessage(data));
        return data;
    }

    window.RentalAPI = {
        API_BASE: API_BASE,
        getToken: getToken,
        setToken: setToken,
        clearToken: clearToken,
        api: api,
        auth: {
            register: (body) => api('/api/auth/register', { method: 'POST', body: JSON.stringify(body) }),
            login: (body) => api('/api/auth/login', { method: 'POST', body: JSON.stringify(body) }),
            me: () => api('/api/auth/me'),
        },
        properties: {
            list: (q) => {
                const p = new URLSearchParams();
                if (q.location) p.set('location', q.location);
                if (q.price_min != null) p.set('price_min', String(q.price_min));
                if (q.price_max != null) p.set('price_max', String(q.price_max));
                if (q.bedrooms) p.set('bedrooms', q.bedrooms);
                if (q.property_type) p.set('property_type', q.property_type);
                if (q.sort) p.set('sort', q.sort);
                const s = p.toString();
                return api('/api/properties' + (s ? '?' + s : ''));
            },
            get: (id) => api('/api/properties/' + encodeURIComponent(id)),
            mine: () => api('/api/properties/mine'),
            create: (body) => api('/api/properties', { method: 'POST', body: JSON.stringify(body) }),
            update: (id, body) =>
                api('/api/properties/' + encodeURIComponent(id), { method: 'PUT', body: JSON.stringify(body) }),
            remove: (id) => api('/api/properties/' + encodeURIComponent(id), { method: 'DELETE' }),
        },
        favorites: {
            list: () => api('/api/favorites'),
            add: (propertyId) => api('/api/favorites/' + encodeURIComponent(propertyId), { method: 'POST' }),
            remove: (propertyId) =>
                api('/api/favorites/' + encodeURIComponent(propertyId), { method: 'DELETE' }),
        },
        chat: {
            conversations: () => api('/api/chat/conversations'),
            messages: (otherUserId) => api('/api/chat/messages/' + encodeURIComponent(otherUserId)),
            send: (body) => api('/api/chat/send', { method: 'POST', body: JSON.stringify(body) }),
        },
        bookings: {
            list: () => api('/api/bookings'),
            create: (body) => api('/api/bookings', { method: 'POST', body: JSON.stringify(body) }),
            approve: (id) => api('/api/bookings/' + encodeURIComponent(id) + '/approve', { method: 'PUT' }),
            reject: (id) => api('/api/bookings/' + encodeURIComponent(id) + '/reject', { method: 'PUT' }),
        },
        admin: {
            properties: () => api('/api/admin/properties'),
            approve: (id) =>
                api('/api/admin/properties/' + encodeURIComponent(id) + '/approve', { method: 'PUT' }),
            reject: (id) =>
                api('/api/admin/properties/' + encodeURIComponent(id) + '/reject', { method: 'PUT' }),
        },
    };
})();
