from flask import Flask, request, jsonify
import requests, zipfile, io, json, os

app = Flask(__name__)

GODADDY_ZIP_URL = "https://inventory.auctions.godaddy.com/all_biddable_auctions.json.zip"
N8N_WEBHOOK_URL = "https://n8n.scrapifyapi.com/webhook/godaddy-auctions-render"

@app.route('/filter-domains', methods=['POST'])
def filter_domains():
    try:
        # Step 1: Download ZIP file
        response = requests.get(GODADDY_ZIP_URL)
        if response.status_code != 200:
            return jsonify({"error": "Failed to download ZIP file"}), 500

        # Step 2: Extract JSON
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            json_filename = z.namelist()[0]
            with z.open(json_filename) as f:
                full_data = json.load(f)

        all_domains = full_data.get("data", [])

        # Step 3: Get domains from POST body
        input_domains = request.json.get("domains", [])
        input_domains_set = set(domain.lower() for domain in input_domains)

        # Step 4: Filter matching domains
        matched = [
            domain for domain in all_domains
            if domain.get("domainName", "").lower() in input_domains_set
        ]

        # Step 5: Send matched data to n8n webhook
        if matched:
            try:
                webhook_response = requests.post(N8N_WEBHOOK_URL, json={"matched_domains": matched})
                webhook_response.raise_for_status()
            except Exception as webhook_err:
                print(f"[n8n webhook error] {webhook_err}")

        return jsonify(matched), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Required for Render: bind to 0.0.0.0 and use dynamic port
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
