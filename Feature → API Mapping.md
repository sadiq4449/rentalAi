🧩 1. AUTH MODULE (EPIC 1)
🔹 Features → APIs
User Registration
→ POST /api/auth/register
User Login
→ POST /api/auth/login
Get Current User
→ GET /api/auth/me
Update Profile
→ PUT /api/users/profile
Verify User
→ POST /api/auth/verify
🏠 2. PROPERTY MODULE (EPIC 2)
🔹 Features → APIs
Add Property
→ POST /api/properties
Get All Properties
→ GET /api/properties
Get Single Property
→ GET /api/properties/{id}
Update Property
→ PUT /api/properties/{id}
Delete Property
→ DELETE /api/properties/{id}
Upload Images
→ POST /api/properties/{id}/images
🔍 3. SEARCH & FILTER (EPIC 3)
🔹 Features → APIs
Search Properties
→ GET /api/properties?location=&priceMin=&priceMax=
Filter Properties
→ GET /api/properties?bedrooms=&amenities=
Sort Properties
→ GET /api/properties?sort=price_asc
Recommended Properties
→ GET /api/properties/recommended
❤️ 4. FAVORITES MODULE
🔹 Features → APIs
Add to Favorites
→ POST /api/favorites/{propertyId}
Remove Favorite
→ DELETE /api/favorites/{propertyId}
Get Favorites
→ GET /api/favorites
💬 5. CHAT MODULE (EPIC 4)
🔹 Features → APIs

👉 REST (initial load)

Get Conversations
→ GET /api/chat
Get Messages
→ GET /api/chat/{userId}
Send Message (fallback REST)
→ POST /api/chat/send

👉 WebSocket (real-time)

/ws/chat/{userId}
📅 6. BOOKING MODULE (EPIC 5)
🔹 Features → APIs
Create Booking
→ POST /api/bookings
Get User Bookings
→ GET /api/bookings
Approve Booking
→ PUT /api/bookings/{id}/approve
Reject Booking
→ PUT /api/bookings/{id}/reject
💳 7. PAYMENT MODULE (EPIC 6)
🔹 Features → APIs
Initiate Payment
→ POST /api/payments/initiate
Verify Payment
→ POST /api/payments/verify
Payment History
→ GET /api/payments
🧾 8. AGREEMENT MODULE
🔹 Features → APIs
Generate Agreement
→ POST /api/agreements
Get Agreement
→ GET /api/agreements/{id}
Download PDF
→ GET /api/agreements/{id}/download
⭐ 9. REVIEW MODULE (EPIC 7)
🔹 Features → APIs
Add Review
→ POST /api/reviews
Get Reviews
→ GET /api/reviews/{userId}
🛡️ 10. ADMIN MODULE (EPIC 8)
🔹 Features → APIs
Get All Users
→ GET /api/admin/users
Ban User
→ PUT /api/admin/users/{id}/ban
Approve Listing
→ PUT /api/admin/properties/{id}/approve
Reject Listing
→ PUT /api/admin/properties/{id}/reject
🔔 11. NOTIFICATIONS MODULE
🔹 Features → APIs
Get Notifications
→ GET /api/notifications
Mark as Read
→ PUT /api/notifications/{id}/read
📊 12. ANALYTICS MODULE
🔹 Features → APIs
Owner Dashboard Stats
→ GET /api/analytics/owner
Property Views
→ GET /api/analytics/properties/{id}
🧠 FINAL STRUCTURE (SUPER CLEAN)
🔥 Total APIs:

👉 ~40+ endpoints

⚙️ 2 TYPES OF COMMUNICATION
1. REST APIs
CRUD operations
Data fetching
2. WebSockets
Chat
Notifications (future)