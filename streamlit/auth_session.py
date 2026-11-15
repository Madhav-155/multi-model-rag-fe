"""Frontend login state and token lifecycle.

For the Streamlit server client, keep access tokens in server-side session
state. A future browser SPA should keep access tokens in memory and use a
Secure, HttpOnly refresh cookie with CSRF/origin protections.
"""
