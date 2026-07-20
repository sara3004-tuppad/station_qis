"""
One-time setup script — run this locally to get a refresh token.

Steps:
1. Run: python get_refresh_token.py
2. It prints a URL and a code
3. Open the URL in your browser, enter the code, log in with your M365 account
4. Copy the refresh_token printed at the end
5. Paste it into .streamlit/secrets.toml as graph.refresh_token
6. Also add it to Streamlit Cloud Secrets

After this, the app will authenticate silently using the refresh token.
You only need to re-run this if the token expires (typically after 90 days of inactivity).
"""

import msal

TENANT_ID = "c7f044be-6021-48ac-9b54-7c77cc9d53d5"
CLIENT_ID = "0f06d221-934f-453e-bfe6-307580d65222"
SCOPES    = ["https://graph.microsoft.com/Files.ReadWrite"]

app = msal.PublicClientApplication(
    client_id=CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}",
)

flow = app.initiate_device_flow(scopes=SCOPES)
if "user_code" not in flow:
    raise RuntimeError(f"Failed to create device flow: {flow}")

print("\n" + "="*60)
print("STEP 1: Open this URL in your browser:")
print(f"  {flow['verification_uri']}")
print(f"\nSTEP 2: Enter this code: {flow['user_code']}")
print("="*60)
print("\nWaiting for you to log in...")

result = app.acquire_token_by_device_flow(flow)

if "refresh_token" in result:
    print("\n✅ Login successful!")
    print("\nAdd this to your .streamlit/secrets.toml under [graph]:")
    print(f'\nrefresh_token = "{result["refresh_token"]}"')
    print("\nAlso add it to Streamlit Cloud Secrets.")
else:
    print("\n❌ Failed:", result.get("error_description"))
