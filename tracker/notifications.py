import os
import requests


def send_line_alert(product, new_price):
    """Sends a push message via LINE Messaging API."""
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    # Retrieve line_user_id dynamically from product owner's profile
    line_user_id = getattr(product.user.profile, "line_user_id", None)

    if not token or not line_user_id:
        print(f"Skipping LINE alert: No LINE User ID found for {product.user}")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    payload = {
        "to": line_user_id,
        "messages": [
            {
                "type": "text",
                "text": (
                    f"🚨 Price Drop Alert!\n\n"
                    f"📦 {product.name}\n"
                    f"💰 Current Price: ${new_price}\n"
                    f"🎯 Target Price: ${product.target_price}\n\n"
                    f"🔗 {product.url}"
                ),
            }
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to send LINE notification: {e}")
